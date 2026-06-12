"""
services/investitore.py — BIOLavaTU LaundryPro Platform

Motore di analisi VERSIONE INVESTITORE.
Combina 3 livelli di dati per portare il margine di errore a ±8-10%:

  LIVELLO 1 — Automatico (API Google + ISTAT): 51 variabili
  LIVELLO 2 — Sopralluogo campo (obbligatorio): 9 variabili
  LIVELLO 3 — Validazione incrociata AI (3 metodi convergenti)

BENCHMARK CALIBRATI SU DATI REALI BIOLAVATU:
  Via della Giuliana Roma → monopolio   → €18.000/mese → occ 57.9%
  Via Candia Roma         → 4 conc 500m → €8.000/mese  → occ 25.7%

OUTPUT:
  - Score investitore 0-100
  - Confidenza % con etichetta Alta/Media/Bassa
  - Raccomandazione: Procedi / Approfondisci / Sconsigliato
  - 3 stime incasso convergenti con delta
  - Red flag espliciti
  - Sensitivity analysis
"""

import math
from typing import Dict, List, Optional, Tuple

# ─── BENCHMARK REALI ─────────────────────────────────────────────────────────
BENCHMARKS = [
    {
        'nome':         'Via della Giuliana, Roma',
        'tipo':         'monopolio_grande_citta',
        'incasso':      18000,
        'n_lavatrici':  6,
        'n_asciugatrici': 4,
        'concorrenti_500m': 0,
        'concorrenti_1km':  0,
        'densita':      6500,
        'reddito':      22000,
        'occupazione':  0.579,
        'tipo_zona':    'residenziale_denso',
        'note':         'Benchmark principale — zona semi-monopolio Roma centro',
    },
    {
        'nome':         'Via Candia, Roma',
        'tipo':         'zona_satura_grande_citta',
        'incasso':      8000,
        'n_lavatrici':  6,
        'n_asciugatrici': 4,
        'concorrenti_500m': 4,
        'concorrenti_1km':  9,
        'densita':      7000,
        'reddito':      23800,
        'occupazione':  0.257,
        'tipo_zona':    'residenziale_turistico',
        'note':         'Zona satura Prati Roma — alta concorrenza',
    },
]

# ─── SOGLIE OSSERVAZIONI MINIME OBBLIGATORIE ─────────────────────────────────
MIN_OSSERVAZIONI_TRAFFICO   = 4   # fasce orarie minime
MIN_OSSERVAZIONI_CONCORRENTE = 2  # visite minime per competitor

# ─── FASCE ORARIE SOPRALLUOGO ─────────────────────────────────────────────────
FASCE_ORARIE = [
    {'id': 'lun_mattina',   'label': 'Lunedì mattina',    'orario': '9:00-10:00',  'peso': 1.0},
    {'id': 'lun_pranzo',    'label': 'Lunedì pranzo',     'orario': '12:30-13:30', 'peso': 0.8},
    {'id': 'lun_sera',      'label': 'Lunedì sera',       'orario': '18:00-19:00', 'peso': 1.2},
    {'id': 'sab_mattina',   'label': 'Sabato mattina',    'orario': '10:00-11:00', 'peso': 1.5},
    {'id': 'sab_pomeriggio','label': 'Sabato pomeriggio', 'orario': '15:00-16:00', 'peso': 1.3},
    {'id': 'fer_random',    'label': 'Feriale casuale',   'orario': 'libero',      'peso': 1.0},
]

# ─── SCHEDA RILEVAZIONE CONCORRENTE ──────────────────────────────────────────
SCHEDA_CONCORRENTE = {
    'campi_obbligatori': [
        'nome', 'indirizzo', 'n_lavatrici', 'n_asciugatrici',
        'prezzo_lavaggio', 'orario_apertura', 'orario_chiusura',
    ],
    'campi_rilevazione': [
        # Per ogni visita: {data, ora, lav_occupate, asc_occupate}
        'visite',
    ],
    'campi_qualita': [
        'pulizia_1_5',        # 1=sporco 5=impeccabile
        'funzionamento_1_5',  # 1=guaste spesso 5=sempre ok
        'assistenza_1_5',     # 1=nessuna 5=personale presente
        'app_pagamento',      # bool
        'tessera_fedelta',    # bool
        'h24',                # bool
        'eco_posizionato',    # bool
        'note_punti_deboli',  # testo libero
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# METODO 1 — STIMA DA CAPACITÀ MACCHINE × OCCUPAZIONE ZONA
# (già in preventivo.py — qui lo reimplementiamo con benchmark estesi)
# ═══════════════════════════════════════════════════════════════════════════════

def _occ_da_concorrenza(c500: int, c1km: int) -> float:
    """Occupazione base calibrata — aggiornata con media italiana reale.
    Benchmark: Via Candia (25.7%) e Via Giuliana (57.9% top performer Roma).
    Media italiana monopolio: 45% (più rappresentativa fuori Roma/Milano).
    """
    if   c500 >= 5: return 0.10
    elif c500 == 4: return 0.257   # Via Candia ✅
    elif c500 == 3: return 0.32
    elif c500 == 2: return 0.42
    elif c500 == 1: return 0.52
    elif c1km >= 4: return 0.55
    elif c1km >= 2: return 0.58
    elif c1km == 1: return 0.60
    else:           return 0.45   # media italiana reale (non top performer)


def stima_metodo1_capacita(
    n_std: int, n_med: int, n_grd: int, n_asc: int,
    t_std: float, t_med: float, t_grd: float, t_asc: float,
    concorrenti_500m: int, concorrenti_1km: int,
    densita: float, recensioni_zona: int, reddito_medio: float,
    gdo_500m: int, mult_attractor: float,
    visibilita_vetrina: int = 5,
    pedoni_ora_campo: int = 0,
    scenario: str = 'realistico',
) -> Dict:
    giorni = 30
    mult = {'pessimistico': 0.70, 'realistico': 1.00, 'ottimistico': 1.30}.get(scenario, 1.0)

    occ_base = _occ_da_concorrenza(concorrenti_500m, concorrenti_1km)

    # ── Fattore dimensione città ──────────────────────────────────────────────
    # Da kwargs opzionali — default 1.0 se non disponibile
    pop_comune   = kwargs.get('pop_comune', 0) if kwargs else 0
    tipo_zona_s  = (kwargs.get('tipo_zona', '') or '').lower() if kwargs else ''
    if   pop_comune >= 500000: f_citta = 1.00
    elif pop_comune >= 200000: f_citta = 0.88
    elif pop_comune >= 100000: f_citta = 0.78
    elif pop_comune >= 50000:  f_citta = 0.68
    elif pop_comune > 0:        f_citta = 0.58
    else:                       f_citta = 0.75  # default medio se non disponibile

    # ── Stagionalità ──────────────────────────────────────────────────────────
    import datetime as _dt
    mese = _dt.date.today().month
    _stag = {
        'turistica':    {1:0.45,2:0.45,3:0.65,4:0.80,5:0.90,
                         6:1.20,7:1.80,8:1.80,9:1.10,10:0.80,11:0.55,12:0.45},
        'universitaria':{1:1.15,2:1.20,3:1.20,4:1.15,5:1.10,
                         6:0.70,7:0.55,8:0.50,9:0.80,10:1.15,11:1.20,12:1.00},
        'residenziale': {1:0.95,2:0.95,3:1.00,4:1.00,5:1.05,
                         6:1.00,7:0.90,8:0.85,9:1.00,10:1.05,11:1.05,12:0.95},
    }
    f_stagionalita = _stag.get(tipo_zona_s, _stag['residenziale']).get(mese, 1.0)

    # Correzioni additive (max ±20%)
    corr = 0.0
    if   densita > 6000: corr += 0.04
    elif densita > 4000: corr += 0.02
    elif densita > 2000: corr += 0.00
    elif densita > 800:  corr -= 0.04
    else:                corr -= 0.10

    if   recensioni_zona > 150000: corr += 0.04
    elif recensioni_zona > 80000:  corr += 0.02
    elif recensioni_zona > 30000:  corr += 0.00
    elif recensioni_zona > 8000:   corr -= 0.02
    elif recensioni_zona > 2000:   corr -= 0.05
    else:                           corr -= 0.10

    if gdo_500m >= 2: corr += 0.02
    elif gdo_500m == 1: corr += 0.01

    if   reddito_medio > 40000: corr -= 0.06
    elif reddito_medio > 30000: corr -= 0.03
    elif reddito_medio < 13000: corr -= 0.04

    # Visibilità vetrina (campo)
    if visibilita_vetrina >= 8:   corr += 0.04
    elif visibilita_vetrina >= 6: corr += 0.02
    elif visibilita_vetrina <= 3: corr -= 0.05

    # Traffico pedonale campo (se disponibile sovrascrive proxy Google)
    if pedoni_ora_campo > 0:
        if   pedoni_ora_campo > 800: corr += 0.05
        elif pedoni_ora_campo > 400: corr += 0.02
        elif pedoni_ora_campo < 100: corr -= 0.06

    corr += min((mult_attractor - 1.0) * 0.10, 0.08)
    corr  = max(-0.20, min(0.20, corr))

    occ = min(0.82, occ_base * (1.0 + corr) * f_citta * f_stagionalita * mult)

    incasso_lav = (n_std * 18 * t_std + n_med * 18 * t_med + n_grd * 18 * t_grd) * occ * giorni
    incasso_asc = n_asc * 52 * t_asc * occ * giorni
    incasso = incasso_lav + incasso_asc

    return {
        'metodo':       'Capacità macchine × occupazione zona',
        'incasso':      round(incasso),
        'occupazione':  round(occ * 100, 1),
        'occ_base':     round(occ_base * 100, 1),
        'correzione':   round(corr * 100, 1),
        'dettaglio':    f"{n_std+n_med+n_grd}L+{n_asc}A × {occ*100:.1f}% occ × 30gg",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# METODO 2 — STIMA DA MERCATO CONCORRENZA (capacità installata zona)
# Formula: mercato totale zona × quota aggredibile
# ═══════════════════════════════════════════════════════════════════════════════

def stima_metodo2_mercato(
    concorrenti_campo: List[Dict],
    concorrenti_api: List[Dict],
    n_lavatrici_ns: int,
    n_asciugatrici_ns: int,
    t_lav_medio: float,
    t_asc: float,
    concorrenti_500m: int,
) -> Dict:
    """
    Stima l'incasso da quota di mercato aggredibile.
    Se abbiamo i dati campo (macchine occupate), usa quelli.
    Altrimenti usa la stima da API (rating/recensioni).
    """
    # Usa dati campo se disponibili, altrimenti API
    competitors = concorrenti_campo if concorrenti_campo else concorrenti_api

    mercato_totale = 0
    dettaglio_conc = []

    for c in competitors:
        n_lav = int(c.get('n_lavatrici') or c.get('n_lav_stimato', 6))
        n_asc = int(c.get('n_asciugatrici') or c.get('n_asc_stimato', 4))

        # Occupazione: usa media visite campo se disponibile
        visite = c.get('visite', [])
        if visite:
            occ_rilevata = sum(
                (v.get('lav_occupate', 0) / max(1, n_lav) +
                 v.get('asc_occupate', 0) / max(1, n_asc)) / 2
                for v in visite
            ) / len(visite)
            fonte = 'campo'
        else:
            # Stima da rating
            rating = float(c.get('rating') or 3.5)
            n_rec  = int(c.get('user_ratings_total') or c.get('n_recensioni', 0))
            if rating >= 4.2 and n_rec > 100: occ_rilevata = 0.68
            elif rating >= 3.8:               occ_rilevata = 0.55
            elif rating >= 3.0:               occ_rilevata = 0.42
            else:                              occ_rilevata = 0.32
            fonte = 'api'

        fat_c = (n_lav * 18 * t_lav_medio + n_asc * 52 * t_asc) * occ_rilevata * 30
        mercato_totale += fat_c
        dettaglio_conc.append({
            'nome':         c.get('nome', '—'),
            'fatturato':    round(fat_c),
            'occupazione':  round(occ_rilevata * 100, 1),
            'fonte':        fonte,
        })

    if mercato_totale == 0:
        return {'metodo': 'Quota mercato', 'incasso': 0, 'affidabile': False,
                'nota': 'Nessun concorrente rilevato — impossibile stimare mercato'}

    # Quota ns in base alla concorrenza
    n_tot = len(competitors) + 1  # +1 = noi
    if   concorrenti_500m == 0: quota = 1 / n_tot * 1.20  # vantaggio first-mover
    elif concorrenti_500m <= 2: quota = 1 / n_tot * 1.10
    else:                        quota = 1 / n_tot

    # Ns macchine vs media competitor
    cap_ns    = n_lavatrici_ns * 18 * 30 + n_asciugatrici_ns * 52 * 30
    cap_media = mercato_totale / len(competitors) if competitors else 1
    adj_cap   = min(1.3, max(0.7, cap_ns / (cap_media * 0.8) if cap_media > 0 else 1))

    incasso = mercato_totale * quota * adj_cap

    return {
        'metodo':         'Quota mercato concorrenti',
        'incasso':        round(incasso),
        'mercato_totale': round(mercato_totale),
        'quota_pct':      round(quota * 100, 1),
        'n_competitors':  len(competitors),
        'dettaglio':      dettaglio_conc,
        'affidabile':     len(concorrenti_campo) > 0,
        'nota':           f"Mercato zona €{mercato_totale:,.0f}/mese ÷ {n_tot} operatori × adj capacità",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# METODO 3 — STIMA DA TRAFFICO PEDONALE CAMPO
# Formula: pedoni_ora × ore_apertura × tasso_conversione × spesa_media × 30
# ═══════════════════════════════════════════════════════════════════════════════

def stima_metodo3_traffico(
    osservazioni_traffico: List[Dict],
    t_lav_medio: float,
    t_asc: float,
    perc_asciugatura: float,
    concorrenti_500m: int,
) -> Dict:
    """
    Stima da traffico pedonale rilevato sul campo.
    osservazioni_traffico: lista di {fascia_id, pedoni_15min, direzione, data}
    """
    if not osservazioni_traffico:
        return {'metodo': 'Traffico pedonale campo', 'incasso': 0,
                'affidabile': False, 'nota': 'Nessuna osservazione campo disponibile'}

    # Media pedoni per fascia (moltiplica ×4 per avere pedoni/ora)
    totale_peso = sum(
        obs.get('pedoni_15min', 0) * 4 *
        next((f['peso'] for f in FASCE_ORARIE if f['id'] == obs.get('fascia_id')), 1.0)
        for obs in osservazioni_traffico
    )
    n_obs = len(osservazioni_traffico)
    pedoni_ora_pesata = totale_peso / n_obs if n_obs > 0 else 0

    # Ore apertura effettiva
    ore_apertura = 13  # 8:00-21:00

    # Tasso conversione: % pedoni che entrano nella lavanderia
    # Calibrato: lavanderia media capta 0.8-1.5% del traffico pedonale
    # Con alta concorrenza si abbassa, con bassa si alza
    if   concorrenti_500m == 0: tasso_conv = 0.013
    elif concorrenti_500m == 1: tasso_conv = 0.010
    elif concorrenti_500m == 2: tasso_conv = 0.008
    elif concorrenti_500m == 3: tasso_conv = 0.006
    else:                        tasso_conv = 0.004

    clienti_giorno = pedoni_ora_pesata * ore_apertura * tasso_conv
    spesa_media    = t_lav_medio + (perc_asciugatura / 100) * t_asc
    incasso        = clienti_giorno * spesa_media * 30

    return {
        'metodo':           'Traffico pedonale campo',
        'incasso':          round(incasso),
        'pedoni_ora':       round(pedoni_ora_pesata),
        'clienti_giorno':   round(clienti_giorno, 1),
        'tasso_conv':       round(tasso_conv * 100, 2),
        'n_osservazioni':   n_obs,
        'affidabile':       n_obs >= MIN_OSSERVAZIONI_TRAFFICO,
        'nota': f"{round(pedoni_ora_pesata)} ped/h × {ore_apertura}h × {tasso_conv*100:.2f}% conv × €{spesa_media:.1f}",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERGENZA 3 METODI — CUORE DEL SISTEMA
# ═══════════════════════════════════════════════════════════════════════════════

def valida_convergenza(
    m1: Dict, m2: Dict, m3: Dict
) -> Dict:
    """
    Verifica se i 3 metodi convergono.
    Convergenza = tutti entro ±20% dalla media.
    Se divergono > 20% → identifica l'outlier e segnala.
    """
    stime = []
    if m1.get('incasso', 0) > 0:
        stime.append(('M1-Capacità', m1['incasso'], True))
    if m2.get('incasso', 0) > 0 and m2.get('affidabile', True):
        stime.append(('M2-Mercato', m2['incasso'], m2.get('affidabile', False)))
    if m3.get('incasso', 0) > 0 and m3.get('affidabile', False):
        stime.append(('M3-Traffico', m3['incasso'], m3.get('affidabile', False)))

    if not stime:
        return {'converge': False, 'media': 0, 'delta_max': 0, 'affidabilita': 0}

    valori  = [s[1] for s in stime]
    media   = sum(valori) / len(valori)
    delta_max = max(abs(v - media) / media * 100 for v in valori) if media > 0 else 0

    # Identifica outlier (diverge >30% dalla media)
    outliers = [s[0] for s in stime if abs(s[1] - media) / media * 100 > 30] if media > 0 else []

    # Stima finale: media ponderata (campo vale di più)
    pesi = []
    for nome, val, aff in stime:
        if 'Traffico' in nome and aff: pesi.append((val, 3.0))   # campo = peso 3
        elif 'Mercato' in nome and aff: pesi.append((val, 2.5))  # campo = peso 2.5
        elif 'Capacità' in nome: pesi.append((val, 2.0))         # sempre disponibile
        else: pesi.append((val, 1.0))
    stima_finale = sum(v * p for v, p in pesi) / sum(p for _, p in pesi)

    # Affidabilità (0-100)
    if   delta_max < 8:  aff = 95
    elif delta_max < 15: aff = 82
    elif delta_max < 25: aff = 65
    elif delta_max < 35: aff = 45
    else:                aff = 25

    # Bonus se tutti e 3 i metodi disponibili con dati campo
    if len(stime) == 3 and all(s[2] for s in stime):
        aff = min(98, aff + 10)

    return {
        'converge':      delta_max < 25,
        'media':         round(media),
        'stima_finale':  round(stima_finale),
        'delta_max':     round(delta_max, 1),
        'n_metodi':      len(stime),
        'outliers':      outliers,
        'affidabilita':  aff,
        'stime':         [{'nome': s[0], 'valore': s[1], 'campo': s[2]} for s in stime],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# RED FLAG — ANOMALIE CHE BLOCCANO O AVVERTONO
# ═══════════════════════════════════════════════════════════════════════════════

def calcola_red_flags(
    convergenza: Dict,
    sopralluogo: Dict,
    concorrenti_campo: List[Dict],
    score_automatico: float,
    pop_5min: int,
    concorrenti_500m: int,
    visibilita_vetrina: int,
    cantieri_previsti: bool,
    reddito_medio: float,
) -> List[Dict]:
    flags = []

    # ── CRITICI (bloccano il documento) ──────────────────────────────────────
    if convergenza.get('delta_max', 100) > 40 and convergenza.get('n_metodi', 0) >= 2:
        flags.append({
            'livello': 'CRITICO',
            'codice':  'DIVERGENZA_STIME',
            'titolo':  'Stime divergenti oltre il 40%',
            'dettaglio': f"I {convergenza['n_metodi']} metodi di stima divergono di {convergenza['delta_max']:.0f}%. "
                         f"Raccogliere più dati di campo prima di procedere.",
            'azione':  'Aggiungere almeno 3 osservazioni traffico e 2 visite per concorrente',
            'blocca':  True,
        })

    if pop_5min < 1000:
        flags.append({
            'livello': 'CRITICO',
            'codice':  'BACINO_INSUFFICIENTE',
            'titolo':  'Bacino demografico insufficiente',
            'dettaglio': f"Solo {pop_5min:,} abitanti entro 5 minuti a piedi. "
                         "Sotto 1.000 abitanti la lavanderia non è sostenibile.",
            'azione':  'Valutare zona diversa',
            'blocca':  True,
        })

    if concorrenti_500m >= 5:
        flags.append({
            'livello': 'CRITICO',
            'codice':  'SATURAZIONE_CRITICA',
            'titolo':  f'{concorrenti_500m} concorrenti diretti entro 500m',
            'dettaglio': "Zona insostenibile. Con 5+ lavanderie a 500m la quota di mercato "
                         "stimata è <10% del teorico.",
            'azione':  'Zona sconsigliata — cercare alternativa',
            'blocca':  True,
        })

    # ── WARNINGS (richiedono verifica) ────────────────────────────────────────
    n_obs = len(sopralluogo.get('osservazioni', []))
    if n_obs < MIN_OSSERVAZIONI_TRAFFICO:
        flags.append({
            'livello': 'WARNING',
            'codice':  'SOPRALLUOGO_INCOMPLETO',
            'titolo':  f'Sopralluogo traffico incompleto ({n_obs}/{MIN_OSSERVAZIONI_TRAFFICO} fasce)',
            'dettaglio': "Raccogliere almeno 4 fasce orarie per una stima affidabile del traffico.",
            'azione':  'Completare sopralluogo fasce mancanti',
            'blocca':  False,
        })

    conc_con_visite = [c for c in concorrenti_campo if len(c.get('visite', [])) >= MIN_OSSERVAZIONI_CONCORRENTE]
    if concorrenti_500m > 0 and len(conc_con_visite) == 0:
        flags.append({
            'livello': 'WARNING',
            'codice':  'CONCORRENTI_NON_ANALIZZATI',
            'titolo':  'Nessun concorrente analizzato sul campo',
            'dettaglio': f"Ci sono {concorrenti_500m} concorrenti entro 500m ma nessuno "
                         "è stato visitato per rilevare l'occupazione reale.",
            'azione':  'Effettuare almeno 2 visite per ogni concorrente diretto',
            'blocca':  False,
        })

    if visibilita_vetrina > 0 and visibilita_vetrina <= 3:
        flags.append({
            'livello': 'WARNING',
            'codice':  'VISIBILITA_BASSA',
            'titolo':  f'Visibilità vetrina bassa ({visibilita_vetrina}/10)',
            'dettaglio': "Locale difficilmente visibile dalla strada. "
                         "Riduce il traffico di passaggio del 30-40%.",
            'azione':  'Valutare segnaletica esterna potenziata o alternativa locale',
            'blocca':  False,
        })

    if cantieri_previsti:
        flags.append({
            'livello': 'WARNING',
            'codice':  'CANTIERI',
            'titolo':  'Cantieri o lavori stradali previsti',
            'dettaglio': "Cantieri nelle vicinanze possono ridurre il traffico pedonale "
                         "fino al 50% per la durata dei lavori.",
            'azione':  'Verificare durata cantieri e impatto su accesso al locale',
            'blocca':  False,
        })

    if reddito_medio > 38000:
        flags.append({
            'livello': 'INFO',
            'codice':  'REDDITO_ALTO',
            'titolo':  f'Reddito medio zona elevato (€{reddito_medio:,.0f})',
            'dettaglio': "Zona ad alto reddito: alta probabilità di lavatrice domestica. "
                         "La domanda si concentra su B&B, affitti brevi e monolocali.",
            'azione':  'Verificare % affittuari e presenza B&B nella zona',
            'blocca':  False,
        })

    return flags


# ═══════════════════════════════════════════════════════════════════════════════
# SENSITIVITY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def sensitivity_analysis(
    incasso_base: float,
    costi_fissi: float,
    capex: float,
) -> Dict:
    """
    Mostra cosa succede se l'occupazione è diversa dal previsto.
    Fondamentale per l'investitore.
    """
    scenari = []
    for delta_pct, label in [
        (-20, 'Scenario pessimistico -20%'),
        (-10, 'Cautela -10%'),
        (0,   'Realistico (base)'),
        (+10, 'Ottimistico +10%'),
        (+20, 'Ottimistico forte +20%'),
    ]:
        inc = incasso_base * (1 + delta_pct / 100)
        utile = inc - costi_fissi
        payback = (capex * 1.22 / utile / 12) if utile > 0 else 999
        scenari.append({
            'label':    label,
            'delta':    delta_pct,
            'incasso':  round(inc),
            'utile':    round(utile),
            'payback':  round(payback, 1) if payback < 999 else None,
            'viable':   utile > 0,
        })

    # Break-even occupazione
    if incasso_base > 0:
        be_occ = costi_fissi / incasso_base * 100
    else:
        be_occ = 100

    return {
        'scenari':      scenari,
        'be_occupazione_pct': round(be_occ, 1),
        'note': f"Break-even operativo a {be_occ:.0f}% dell'occupazione stimata",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE INVESTITORE (0-100) + RACCOMANDAZIONE
# ═══════════════════════════════════════════════════════════════════════════════

def calcola_score_investitore(
    score_automatico: float,           # score zona 0-100 da API
    convergenza: Dict,
    red_flags: List[Dict],
    sopralluogo_completo: bool,
    n_concorrenti_analizzati: int,
    visibilita_vetrina: int,
    indice_famiglie_lav: int,
    payback_mesi: float,
) -> Dict:
    score = 0

    # ── 1. Score zona automatico (peso 25%) ───────────────────────────────────
    score += (score_automatico / 100) * 25

    # ── 2. Convergenza stime (peso 20%) ───────────────────────────────────────
    score += (convergenza.get('affidabilita', 0) / 100) * 20

    # ── 3. Sopralluogo qualità (peso 20%) ─────────────────────────────────────
    sop_score = 0
    if sopralluogo_completo:      sop_score += 12
    if n_concorrenti_analizzati >= 2: sop_score += 8
    score += sop_score

    # ── 4. Visibilità vetrina (peso 10%) ──────────────────────────────────────
    score += (visibilita_vetrina / 10) * 10

    # ── 5. Indice famiglie/lavanderie (peso 15%) ──────────────────────────────
    if   indice_famiglie_lav > 1500: score += 15
    elif indice_famiglie_lav > 1000: score += 12
    elif indice_famiglie_lav > 600:  score += 8
    elif indice_famiglie_lav > 400:  score += 5
    else:                             score += 2

    # ── 6. Payback (peso 10%) ─────────────────────────────────────────────────
    if   payback_mesi > 0 and payback_mesi <= 18:  score += 10
    elif payback_mesi <= 30:  score += 7
    elif payback_mesi <= 48:  score += 4
    elif payback_mesi <= 72:  score += 2

    # ── Penalità red flags ────────────────────────────────────────────────────
    for f in red_flags:
        if f['livello'] == 'CRITICO':  score -= 25
        elif f['livello'] == 'WARNING': score -= 8

    score = max(0, min(100, score))

    # Raccomandazione
    critici = [f for f in red_flags if f['livello'] == 'CRITICO' and f.get('blocca')]
    if critici or score < 30:
        rac = 'Sconsigliato'
        rac_colore = '#ef4444'
        rac_icon   = '🔴'
    elif score < 55:
        rac = 'Approfondire'
        rac_colore = '#f59e0b'
        rac_icon   = '🟡'
    elif score < 72:
        rac = 'Fattibile'
        rac_colore = '#84cc16'
        rac_icon   = '🟢'
    else:
        rac = 'Procedi'
        rac_colore = '#10b981'
        rac_icon   = '✅'

    # Confidenza
    if   convergenza.get('affidabilita', 0) >= 80 and sopralluogo_completo: conf = 'Alta'
    elif convergenza.get('affidabilita', 0) >= 55: conf = 'Media'
    else:                                            conf = 'Bassa'

    conf_colore = {'Alta': '#10b981', 'Media': '#f59e0b', 'Bassa': '#ef4444'}[conf]

    return {
        'score':           round(score, 1),
        'raccomandazione': rac,
        'rac_colore':      rac_colore,
        'rac_icon':        rac_icon,
        'confidenza':      conf,
        'conf_colore':     conf_colore,
        'conf_pct':        convergenza.get('affidabilita', 0),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNZIONE PRINCIPALE — ANALISI COMPLETA INVESTITORE
# ═══════════════════════════════════════════════════════════════════════════════

def analisi_completa_investitore(
    # Dati pratica
    pratica_id: int,
    # Macchine
    n_std: int, n_med: int, n_grd: int, n_asc: int,
    t_std: float, t_med: float, t_grd: float, t_asc: float,
    perc_asciugatura: float,
    capex: float,
    costi_fissi_mese: float,
    # Zona (API)
    concorrenti_500m: int, concorrenti_1km: int,
    densita: float, recensioni_zona: int,
    reddito_medio: float, gdo_500m: int,
    mult_attractor: float,
    score_automatico: float,
    pop_5min: int, pop_10min: int,
    indice_famiglie_lav: int,
    # Sopralluogo campo
    sopralluogo: Dict,              # {osservazioni: [...], completato: bool}
    concorrenti_campo: List[Dict],  # lista concorrenti con visite
    concorrenti_api: List[Dict],    # lista da Google Maps
    # Qualità locale
    visibilita_vetrina: int,
    cantieri_previsti: bool,
    scenario: str = 'realistico',
) -> Dict:

    t_lav_medio = (
        (n_std * t_std + n_med * t_med + n_grd * t_grd) /
        max(1, n_std + n_med + n_grd)
    )

    # ── 3 METODI DI STIMA ─────────────────────────────────────────────────────
    osservazioni = sopralluogo.get('osservazioni', [])
    pedoni_ora = 0
    if osservazioni:
        pedoni_ora = int(sum(o.get('pedoni_15min', 0) * 4 for o in osservazioni) / len(osservazioni))

    m1 = stima_metodo1_capacita(
        n_std, n_med, n_grd, n_asc,
        t_std, t_med, t_grd, t_asc,
        concorrenti_500m, concorrenti_1km,
        densita, recensioni_zona, reddito_medio,
        gdo_500m, mult_attractor,
        visibilita_vetrina, pedoni_ora, scenario,
    )
    m2 = stima_metodo2_mercato(
        concorrenti_campo, concorrenti_api,
        n_std + n_med + n_grd, n_asc,
        t_lav_medio, t_asc, concorrenti_500m,
    )
    m3 = stima_metodo3_traffico(
        osservazioni, t_lav_medio, t_asc, perc_asciugatura, concorrenti_500m,
    )

    # ── CONVERGENZA ───────────────────────────────────────────────────────────
    conv = valida_convergenza(m1, m2, m3)
    incasso_finale = conv['stima_finale'] if conv['stima_finale'] > 0 else m1['incasso']

    # ── RED FLAGS ─────────────────────────────────────────────────────────────
    flags = calcola_red_flags(
        conv, sopralluogo, concorrenti_campo,
        score_automatico, pop_5min,
        concorrenti_500m, visibilita_vetrina,
        cantieri_previsti, reddito_medio,
    )

    # ── SENSITIVITY ───────────────────────────────────────────────────────────
    sensitivity = sensitivity_analysis(incasso_finale, costi_fissi_mese, capex)

    # ── PAYBACK ───────────────────────────────────────────────────────────────
    utile_mese = incasso_finale - costi_fissi_mese
    payback_mesi = (capex * 1.22 / utile_mese / 12) if utile_mese > 0 else 999

    # ── SCORE FINALE ──────────────────────────────────────────────────────────
    n_conc_analizzati = len([c for c in concorrenti_campo
                              if len(c.get('visite', [])) >= MIN_OSSERVAZIONI_CONCORRENTE])
    score_inv = calcola_score_investitore(
        score_automatico, conv, flags,
        sopralluogo.get('completato', False),
        n_conc_analizzati, visibilita_vetrina,
        indice_famiglie_lav, payback_mesi,
    )

    # ── BENCHMARK COMPARISON ──────────────────────────────────────────────────
    benchmark_match = None
    for b in BENCHMARKS:
        if abs(b['concorrenti_500m'] - concorrenti_500m) <= 1:
            benchmark_match = b
            break

    return {
        # Risultati principali
        'incasso_finale':    incasso_finale,
        'utile_mese':        round(utile_mese),
        'payback_mesi':      round(payback_mesi, 1) if payback_mesi < 999 else None,

        # 3 metodi
        'metodo1':   m1,
        'metodo2':   m2,
        'metodo3':   m3,
        'convergenza': conv,

        # Score e raccomandazione
        'score_investitore':  score_inv['score'],
        'raccomandazione':    score_inv['raccomandazione'],
        'rac_colore':         score_inv['rac_colore'],
        'rac_icon':           score_inv['rac_icon'],
        'confidenza':         score_inv['confidenza'],
        'conf_colore':        score_inv['conf_colore'],
        'conf_pct':           score_inv['conf_pct'],

        # Red flags
        'red_flags':          flags,
        'n_critici':          len([f for f in flags if f['livello'] == 'CRITICO']),
        'n_warning':          len([f for f in flags if f['livello'] == 'WARNING']),
        'blocca_documento':   any(f.get('blocca') for f in flags),

        # Sensitivity
        'sensitivity':        sensitivity,

        # Benchmark
        'benchmark':          benchmark_match,

        # Meta
        'pratica_id':         pratica_id,
        'n_metodi_usati':     conv['n_metodi'],
        'dati_campo':         len(osservazioni) > 0 or len(concorrenti_campo) > 0,
    }
