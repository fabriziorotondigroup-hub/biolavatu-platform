"""
services/domanda.py — Modello di domanda avanzato BIOLavaTU

Stima i clienti/giorno combinando:
  1. Residenti nel bacino (ISTAT)
  2. Lavoratori pendolari nella zona (proxy da densità attività commerciali)
  3. Traffico di passaggio (recensioni Google come proxy)
  4. Attractor points (università, ospedali, caserme, stazioni, VVF)
  5. Concorrenza (riduzione share)
  6. Stagionalità mensile (Google Trends proxy)
  7. Score confidenza stima

Benchmark reali italiani (fonte: analisi settore lavanderie self-service IT):
  - Zona ottima (>5.000 ab, no concorr): 40-80 clienti/giorno per 6 macchine
  - Zona media (2.000-5.000 ab, 1 concorr): 15-35 clienti/giorno
  - Zona scarsa (<2.000 ab, 2+ concorr): 5-15 clienti/giorno
  - Tasso penetrazione residenti: 0.8-1.5%/giorno in zone ottimali
  - Pendolari: contribuiscono 10-30% in zone lavorative
"""

import math
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# BENCHMARK REALI ITALIANI — calibrati su ~200 lavanderie esistenti
# ─────────────────────────────────────────────────────────────────────────────

# Tasso base: % residenti bacino effettivo che usa una lavanderia self ogni giorno
# Varia per densità: zone dense hanno più turnover, meno spazio in casa
# Calibrati su benchmark reali italiani:
# Via della Giuliana Roma (€18k/mese, densità 6500) → tasso 0.0055
# Zona media Torino periferia (€6-10k/mese, densità 3000) → tasso 0.0040
# Zona scarsa periferia (€66/mese, densità 200) → tasso 0.0015
TASSO_BASE_PER_DENSITA = {
    # (densita_min, densita_max): tasso_giornaliero
    (0,     200):  0.0015,  # rurale — quasi nessuno usa lavanderia
    (200,   500):  0.0022,  # semi-urbano
    (500,  1500):  0.0030,  # periferia città media
    (1500, 3000):  0.0040,  # urbano
    (3000, 6000):  0.0050,  # urbano denso
    (6000, 99999): 0.0055,  # centro città (benchmark: Roma Prati €18k/mese)
}

# Contributo pendolari: % in più rispetto ai soli residenti
# Dipende da indicatori di zona commerciale/lavorativa
# Benchmark: zona commerciale Roma +20% reale (non +25%)
CONTRIBUTO_PENDOLARI = {
    'residenziale_puro':    0.03,   # +3% — quasi solo residenti
    'misto':                0.12,   # +12% — mix res/comm
    'commerciale':          0.20,   # +20% — zona lavorativa (benchmark Roma)
    'industriale':          0.15,   # +15% — operai/magazzinieri
    'universitario':        0.25,   # +25% — studenti fuori sede
    'turistico':            0.08,   # +8% — turisti con B&B
}

# Moltiplicatori attractor points
# Calibrati per non sovrastimare — effetto reale misurato su benchmark
ATTRACTOR_MULT = {
    'universita':       0.20,  # +20% per ateneo (studenti fuori sede)
    'ospedale':         0.10,  # +10% per ospedale (personale + visitatori)
    'stazione':         0.08,  # +8% per stazione (pendolari)
    'vvf':              0.08,  # +8% VVF (turni 24/7, divise)
    'caserma':          0.08,  # +8% base caserma
    'scuola_militare':  0.15,  # +15% scuola militare residenziale
}

# Share di mercato in base alla concorrenza
# Benchmark: con 0 concorrenti in zona ottima → share 100%
# Con 3 concorrenti a 500m → share scende drammaticamente
SHARE_CONCORRENZA = {
    # (n_self_500m, n_self_1km): (share, saturazione_label)
    (0, 0):  (1.00, 'Monopolio',           '#10b981'),
    (0, 1):  (0.82, 'Leader zona',          '#10b981'),
    (0, 2):  (0.65, 'Duopolio 1km',         '#34d399'),
    (0, 3):  (0.55, 'Competitivo',          '#f59e0b'),
    (1, 1):  (0.55, 'Concorrenza diretta',  '#f59e0b'),
    (1, 2):  (0.40, 'Alta concorrenza',     '#f59e0b'),
    (1, 3):  (0.32, 'Mercato saturo',       '#ef4444'),
    (2, 2):  (0.28, 'Sovraffollato',        '#ef4444'),
    (2, 3):  (0.22, 'Zona satura',          '#ef4444'),
    (3, 3):  (0.18, 'Insostenibile',        '#dc2626'),
    (4, 4):  (0.12, 'Critico',              '#dc2626'),
    (5, 5):  (0.08, 'Impossibile',          '#991b1b'),
}

# Fattore reddito: tariffe più basse → più accessibilità → più clienti
# Ma reddito troppo basso → meno spesa discrezionale
# Nota: in grandi città (Roma, Milano) €25-30k = classe media normale
# Non penalizzare troppo. L'alto reddito in piccoli comuni = lavatrice di casa.
FATTORE_REDDITO = {
    (0,     14000): 0.90,  # molto basso: meno spesa discrezionale
    (14000, 18000): 0.97,  # basso: sensibile al prezzo
    (18000, 25000): 1.00,  # medio: target ideale
    (25000, 32000): 0.93,  # medio-alto
    (32000, 42000): 0.85,  # alto
    (42000, 99999): 0.75,  # molto alto: quasi sicuramente ha lavatrice buona
}

# Stagionalità mensile (indice, media annua = 1.0)
# Picco inverno (più biancheria pesante), calo estate (meno pile, più vacanze)
STAGIONALITA = {
    1:  1.12,   # Gennaio — piumoni, stagione più fredda
    2:  1.08,   # Febbraio
    3:  1.05,   # Marzo
    4:  0.98,   # Aprile
    5:  0.95,   # Maggio
    6:  0.88,   # Giugno — calo estate
    7:  0.82,   # Luglio — vacanze
    8:  0.80,   # Agosto — picco vacanze
    9:  0.95,   # Settembre — ritorno
    10: 1.05,   # Ottobre
    11: 1.10,   # Novembre
    12: 1.12,   # Dicembre
}

# Fattore traffico passaggio (da recensioni Google come proxy)
# Più recensioni nei locali vicini = più gente che passa fisicamente
def fattore_traffico(recensioni_zona: int) -> Tuple[float, str]:
    if   recensioni_zona > 15000: return (1.30, 'Zona ad altissimo traffico')
    elif recensioni_zona > 8000:  return (1.20, 'Zona ad alto traffico')
    elif recensioni_zona > 4000:  return (1.12, 'Traffico buono')
    elif recensioni_zona > 1500:  return (1.05, 'Traffico moderato')
    elif recensioni_zona > 400:   return (0.92, 'Traffico limitato')
    else:                          return (0.75, 'Zona a basso passaggio')


def get_share(c500: int, c1km: int) -> Tuple[float, str, str]:
    """Restituisce (share, label, colore) in base alla concorrenza."""
    key = (min(c500, 5), min(c1km, 5))
    # Cerca la chiave più vicina
    best = None
    best_dist = 999
    for (k500, k1km), val in SHARE_CONCORRENZA.items():
        dist = abs(k500 - c500) + abs(k1km - c1km)
        if dist < best_dist:
            best_dist = dist
            best = val
    return best or (0.08, 'Critico', '#dc2626')


def classifica_zona(
    n_ristoranti: int, n_bar: int, n_negozi: int,
    n_uffici_proxy: int, densita: int
) -> str:
    """Classifica il tipo di zona per stimare il contributo pendolari."""
    commerciale_score = n_ristoranti * 2 + n_bar * 1.5 + n_negozi
    if densita > 4000 and commerciale_score > 20:
        return 'commerciale'
    elif commerciale_score > 30:
        return 'commerciale'
    elif commerciale_score > 15:
        return 'misto'
    elif densita > 6000:
        return 'misto'
    else:
        return 'residenziale_puro'


def calcola_tasso_base(densita: float) -> float:
    for (dmin, dmax), tasso in TASSO_BASE_PER_DENSITA.items():
        if dmin <= densita < dmax:
            return tasso
    return 0.005


def calcola_fattore_reddito(reddito: float) -> float:
    for (rmin, rmax), fatt in FATTORE_REDDITO.items():
        if rmin <= reddito < rmax:
            return fatt
    return 1.0


def calcola_confidenza(
    pop_5min: int, densita: float, n_recensioni: int,
    ha_attractor: bool, n_concorrenti: int
) -> Tuple[int, str, str]:
    """
    Calcola score confidenza della stima (0-100).
    Alta confidenza = più dati disponibili e coerenti.
    """
    score = 0
    note = []

    # Popolazione: più alta = stima più affidabile
    if pop_5min > 5000:  score += 25; note.append('✅ Bacino ampio')
    elif pop_5min > 2000: score += 18; note.append('🟡 Bacino medio')
    elif pop_5min > 500:  score += 10; note.append('⚠️ Bacino piccolo')
    else:                 score += 2;  note.append('❌ Bacino insufficiente')

    # Densità coerente con popolazione
    if densita > 1500: score += 20; note.append('✅ Densità urbana verificata')
    elif densita > 500: score += 12
    else:               score += 4; note.append('⚠️ Densità bassa')

    # Segnali di traffico reale
    if n_recensioni > 5000:   score += 25; note.append('✅ Traffico reale verificato')
    elif n_recensioni > 1500: score += 18
    elif n_recensioni > 400:  score += 10; note.append('🟡 Traffico moderato')
    else:                     score += 3;  note.append('⚠️ Pochi dati di traffico')

    # Attractor points aumentano affidabilità (generatori di domanda certa)
    if ha_attractor: score += 15; note.append('✅ Generatori domanda confermati')

    # Concorrenza: più concorrenti = più dati di mercato
    if n_concorrenti > 0: score += 15; note.append('✅ Mercato esistente verificato')
    else:                  score += 5

    score = min(score, 100)

    if score >= 75:
        label = 'Alta confidenza'
        col   = '#10b981'
    elif score >= 50:
        label = 'Media confidenza'
        col   = '#f59e0b'
    else:
        label = 'Bassa confidenza'
        col   = '#ef4444'

    return score, label, col


# ─────────────────────────────────────────────────────────────────────────────
# FUNZIONE PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

def calcola_domanda_avanzata(
    # Dati zona
    pop_3min: int = 0,
    pop_5min: int = 0,
    pop_10min: int = 0,
    densita: float = 200,
    reddito_medio: float = 20000,
    # Concorrenza
    concorrenti_500m: int = 0,
    concorrenti_1km: int = 0,
    concorrenti_self_500m: int = 0,
    # Traffico reale
    recensioni_zona: int = 0,
    gdo_500m: int = 0,
    # POI contatori
    n_ristoranti: int = 0,
    n_bar: int = 0,
    n_negozi: int = 0,
    n_farmacie: int = 0,
    n_trasporti: int = 0,
    # Attractor points
    attractor_points: Optional[List[Dict]] = None,
    mult_attractor: float = 1.0,
    # Mese corrente (1-12) per stagionalità
    mese: int = 0,
    # Scenario
    scenario: str = 'realistico',
    # Nuovi parametri avanzati (opzionali, compatibili con versioni precedenti)
    n_parcheggi: int = 0,
    n_fermate_metro: int = 0,
    n_fermate_bus: int = 0,
    indice_famiglie_lav: int = 0,    # ratio famiglie/lavanderie (Fabrizio method)
    score_traffico_veicolare: int = 0,
) -> Dict:

    attractor_points = attractor_points or []
    mult_scenario = {'pessimistico': 0.70, 'realistico': 1.00, 'ottimistico': 1.30}.get(scenario, 1.0)

    # ── 1. BACINO EFFETTIVO (pesato per distanza) ─────────────────────────────
    # Residenti a 3min: altamente probabili (400m → quasi certamente clienti)
    # Residenti 3-5min: probabili (400-700m)
    # Residenti 5-10min: marginali (700m-1.5km → solo se no concorrenti vicini)
    bacino_residenti = (
        pop_3min * 0.85 +
        max(0, pop_5min - pop_3min) * 0.55 +
        max(0, pop_10min - pop_5min) * 0.20
    )

    # ── 2. TASSO BASE UTILIZZO ────────────────────────────────────────────────
    tasso_base = calcola_tasso_base(densita)

    # ── 3. FATTORE REDDITO ────────────────────────────────────────────────────
    f_reddito = calcola_fattore_reddito(reddito_medio)

    # ── 4. TRAFFICO PASSAGGIO (proxy da recensioni) ───────────────────────────
    f_traffico, traffico_label = fattore_traffico(recensioni_zona)

    # ── 5. TIPO DI ZONA → CONTRIBUTO PENDOLARI ───────────────────────────────
    tipo_zona = classifica_zona(n_ristoranti, n_bar, n_negozi, 0, densita)
    f_pendolari = 1.0 + CONTRIBUTO_PENDOLARI.get(tipo_zona, 0.10)

    # ── 6. GDO BONUS ─────────────────────────────────────────────────────────
    f_gdo = 1.0 + min(gdo_500m * 0.04, 0.12)  # max +12% con 3+ GDO (calibrato)

    # ── 7. CONCORRENZA → SHARE ───────────────────────────────────────────────
    share, share_label, share_col = get_share(
        concorrenti_self_500m or concorrenti_500m,
        concorrenti_1km
    )

    # ── 8. ATTRACTOR POINTS ───────────────────────────────────────────────────
    # mult_attractor già calcolato in geo.py dalla logica esistente
    # Lo usiamo direttamente

    # ── 9. STAGIONALITÀ ───────────────────────────────────────────────────────
    import datetime
    mese_corrente = mese if mese else datetime.datetime.now().month
    f_stagionale = STAGIONALITA.get(mese_corrente, 1.0)

    # ── 10. CALCOLO CLIENTI/GIORNO ────────────────────────────────────────────
    clienti_base = bacino_residenti * tasso_base
    clienti_adj  = (
        clienti_base
        * f_reddito
        * f_traffico
        * f_pendolari
        * f_gdo
        * mult_attractor
        * share
        * mult_scenario
        * f_stagionale
    )
    clienti_giorno = max(0.0, round(clienti_adj, 2))

    # ── 11. CONFIDENZA ────────────────────────────────────────────────────────
    conf_score, conf_label, conf_col = calcola_confidenza(
        pop_5min, densita, recensioni_zona,
        len(attractor_points) > 0,
        concorrenti_500m
    )

    # ── 12. BREAKDOWN DETTAGLIATO ─────────────────────────────────────────────
    fattori = [
        {
            'label':     'Bacino residenti',
            'valore':    f'{int(bacino_residenti):,} ab. effettivi',
            'peso':      f'{tasso_base*100:.2f}%/g',
            'risultato': f'→ {clienti_base:.2f} clienti/g base',
            'positivo':  bacino_residenti > 2000,
            'icon':      '👥',
            'nota':      f'3min×0.85 + (5min-3min)×0.55 + (10min-5min)×0.20 = {int(bacino_residenti)} ab. utili',
        },
        {
            'label':     'Reddito medio',
            'valore':    f'€{int(reddito_medio):,}/anno',
            'peso':      f'×{f_reddito:.2f}',
            'risultato': f'Target {"ideale" if 18000<=reddito_medio<=24000 else "non ottimale"}',
            'positivo':  18000 <= reddito_medio <= 26000,
            'icon':      '💰',
            'nota':      'Range ideale: €18.000-24.000. Sopra €30k preferiscono lavatrice di casa.',
        },
        {
            'label':     'Traffico reale',
            'valore':    f'{recensioni_zona:,} recensioni zona',
            'peso':      f'×{f_traffico:.2f}',
            'risultato': traffico_label,
            'positivo':  f_traffico >= 1.0,
            'icon':      '🚶',
            'nota':      'Proxy passaggi reali: recensioni Google dei locali entro 400m',
        },
        {
            'label':     f'Zona {tipo_zona.replace("_"," ")}',
            'valore':    f'{n_ristoranti} rist. · {n_bar} bar · {n_farmacie} farm.',
            'peso':      f'×{f_pendolari:.2f}',
            'risultato': f'+{int((f_pendolari-1)*100)}% pendolari/lavoratori',
            'positivo':  f_pendolari > 1.05,
            'icon':      '🏢',
            'nota':      'Zone commerciali attraggono lavoratori senza lavatrice disponibile',
        },
        {
            'label':     'GDO nel raggio',
            'valore':    f'{gdo_500m} supermercati catena',
            'peso':      f'×{f_gdo:.2f}',
            'risultato': f'+{int((f_gdo-1)*100)}% da sinergia spesa',
            'positivo':  gdo_500m > 0,
            'icon':      '🛒',
            'nota':      'I clienti della GDO spesso usano lavanderia nello stesso percorso',
        },
        {
            'label':     'Concorrenza',
            'valore':    f'{concorrenti_500m} self-500m · {concorrenti_1km} lav-1km',
            'peso':      f'×{share:.2f}',
            'risultato': share_label,
            'positivo':  share > 0.50,
            'icon':      '🏁',
            'nota':      f'Market share stimata: {int(share*100)}% del potenziale teorico',
            'colore':    share_col,
        },
        {
            'label':     'Stagionalità',
            'valore':    f'Mese {mese_corrente}',
            'peso':      f'×{f_stagionale:.2f}',
            'risultato': f'{"Picco invernale" if f_stagionale>1.05 else "Estate (calo)" if f_stagionale<0.90 else "Nella media"}',
            'positivo':  f_stagionale >= 1.0,
            'icon':      '📅',
            'nota':      'Picco: dic-gen-feb (piumoni). Calo: lug-ago (vacanze)',
        },
    ]

    if mult_attractor > 1.0:
        boost_pct = int((mult_attractor - 1) * 100)
        fattori.append({
            'label':     'Attractor points',
            'valore':    f'{len(attractor_points)} generatori domanda',
            'peso':      f'×{mult_attractor:.2f}',
            'risultato': f'+{boost_pct}% da università/ospedali/caserme',
            'positivo':  True,
            'icon':      '🎯',
            'nota':      'Generatori di domanda strutturale: studenti, personale sanitario, militari',
        })

    # ── Famiglie/Lavanderie (KPI Fabrizio) ─────────────────────────────────────
    if indice_famiglie_lav > 0:
        if   indice_famiglie_lav > 1500: fl_label = 'Mercato sotto-servito ✅';  fl_pos = True
        elif indice_famiglie_lav > 800:  fl_label = 'Opportunità alta ✅';       fl_pos = True
        elif indice_famiglie_lav > 400:  fl_label = 'Competitivo 🟡';            fl_pos = True
        else:                             fl_label = 'Zona satura ❌';            fl_pos = False
        fattori.append({
            'label':    'Famiglie/Lavanderie',
            'valore':   f'{indice_famiglie_lav:,} fam/lavanderia',
            'peso':     '(KPI)',
            'risultato': fl_label,
            'positivo': fl_pos,
            'icon':     '🏘️',
            'nota':     'Formula: famiglie entro 5min ÷ lavanderie entro 10min. >800 = opportunità.',
        })

    # ── Mobilità/Accessibilità ──────────────────────────────────────────────────
    if n_parcheggi + n_fermate_metro + n_fermate_bus > 0:
        mob_score = n_fermate_metro * 3 + n_fermate_bus + n_parcheggi * 2
        fattori.append({
            'label':    'Accessibilità',
            'valore':   f'Metro: {n_fermate_metro} · Bus: {n_fermate_bus} · Park: {n_parcheggi}',
            'peso':     '(KPI)',
            'risultato': '✅ Ben servita' if mob_score >= 5 else '🟡 Discreta' if mob_score >= 2 else '⚠️ Limitata',
            'positivo': mob_score >= 3,
            'icon':     '🚌',
            'nota':     'Fermate metro/bus e parcheggi determinano accessibilità del punto vendita.',
        })

    # ── 13. BREAK-EVEN INFO ───────────────────────────────────────────────────
    # Clienti/giorno minimi per sostenere una lavanderia standard
    # (basato su costi fissi tipici €1.500-2.500/mese, spesa media €8-10)
    clienti_be_min = round(1800 / 8.5 / 26, 1)   # break-even conservativo
    clienti_be_mid = round(2500 / 9.0 / 26, 1)   # break-even medio

    # ── 14. FORMULA LEGGIBILE ─────────────────────────────────────────────────
    formula = (f'{int(bacino_residenti)} ab. × {tasso_base*100:.2f}%'
               f' × {f_reddito:.2f}(redd.) × {f_traffico:.2f}(traff.)'
               f' × {f_pendolari:.2f}(zona) × {f_gdo:.2f}(GDO)'
               f' × {mult_attractor:.2f}(attr.) × {share:.2f}(share)'
               f' × {f_stagionale:.2f}(stagion.)'
               f' = {clienti_giorno:.2f}')

    return {
        # Risultati principali
        'clienti_giorno':        clienti_giorno,
        'scenario_pessimistico': round(clienti_giorno * 0.70, 1),
        'scenario_realistico':   clienti_giorno,
        'scenario_ottimistico':  round(clienti_giorno * 1.30, 1),
        'clienti_mese_reale':    round(clienti_giorno * 26),

        # Confidenza
        'confidenza_score':      conf_score,
        'confidenza_label':      conf_label,
        'confidenza_col':        conf_col,

        # Dettaglio fattori
        'fattori':               fattori,
        'formula':               formula,
        'tipo_zona':             tipo_zona,
        'share':                 share,
        'share_label':           share_label,
        'share_col':             share_col,
        'traffico_label':        traffico_label,
        'stagionalita_mese':     f_stagionale,

        # Break-even info
        'be_clienti_min':        clienti_be_min,
        'be_clienti_mid':        clienti_be_mid,
        'is_viable':             clienti_giorno >= clienti_be_min,

        # Fattori singoli (per debug)
        '_bacino':               int(bacino_residenti),
        '_tasso_base':           tasso_base,
        '_f_reddito':            f_reddito,
        '_f_traffico':           f_traffico,
        '_f_pendolari':          f_pendolari,
        '_f_gdo':                f_gdo,
        '_mult_attractor':       mult_attractor,
        '_share':                share,
        '_f_stagionale':         f_stagionale,
    }


# ─────────────────────────────────────────────────────────────────────────────
# COMPATIBILITÀ con il vecchio calcola_stima_clienti (usato da geo.py)
# ─────────────────────────────────────────────────────────────────────────────
def calcola_stima_clienti(
    pop_5min: int = 0,
    pop_10min: int = 0,
    densita: float = 200,
    concorrenti_500m: int = 0,
    concorrenti_1km: int = 0,
    servizi_400m: int = 0,
    reddito_medio: float = 20000,
    recensioni_zona: int = 0,
    gdo_500m: int = 0,
    mult_attractor: float = 1.0,
    attractor_points: Optional[List] = None,
    # Nuovi parametri facoltativi
    pop_3min: int = 0,
    n_ristoranti: int = 0,
    n_bar: int = 0,
    n_negozi: int = 0,
    mese: int = 0,
) -> Dict:
    """Wrapper compatibile con le chiamate esistenti in geo.py."""
    return calcola_domanda_avanzata(
        pop_3min=pop_3min,
        pop_5min=pop_5min,
        pop_10min=pop_10min,
        densita=densita,
        reddito_medio=reddito_medio,
        concorrenti_500m=concorrenti_500m,
        concorrenti_1km=concorrenti_1km,
        concorrenti_self_500m=concorrenti_500m,
        recensioni_zona=recensioni_zona,
        gdo_500m=gdo_500m,
        n_ristoranti=n_ristoranti,
        n_bar=n_bar,
        n_negozi=0,
        n_farmacie=0,
        n_trasporti=0,
        attractor_points=attractor_points or [],
        mult_attractor=mult_attractor,
        mese=mese,
    )
