"""
services/analisi_competitiva.py — BIOLavaTU LaundryPro

Analisi competitiva avanzata per lavanderie self-service.
Stima:
  - Capacità installata concorrenza (macchine × cicli × giorni)
  - Dimensione mercato reale in €/mese
  - Quota mercato aggredibile
  - Indice saturazione con formula famiglie/lavanderie (Fabrizio method)
  - Punti deboli concorrenza (prezzo, orari, servizi, pulizia)
"""

from typing import Dict, List, Optional

# ─── BENCHMARK MACCHINE PER TIPO LAVANDERIA ──────────────────────────────────
# Basati su survey settore IT + analisi mercato BIOLavaTU
CONFIGURAZIONE_TIPO = {
    'piccola':   {'lavatrici': 4,  'asciugatrici': 3,  'label': 'Piccola (4L+3A)'},
    'media':     {'lavatrici': 6,  'asciugatrici': 4,  'label': 'Media (6L+4A)'},
    'grande':    {'lavatrici': 10, 'asciugatrici': 7,  'label': 'Grande (10L+7A)'},
    'hub':       {'lavatrici': 16, 'asciugatrici': 12, 'label': 'Hub (16L+12A)'},
}

# Cicli medi/giorno per macchina (14h operative, 65% occupazione media)
CICLI_LAVATRICE_GIORNO   = 8   # 45min/ciclo → max 18, media reale ~8
CICLI_ASCIUGATRICE_GIORNO = 20  # 16min/ciclo → max 52, media reale ~20

# Ticket medio per ciclo
TICKET_LAVAGGIO = 8.0   # €/ciclo medio (mix piccola/media/grande)
TICKET_ASCIUGA  = 2.5   # €/ciclo asciugatura (3×8min a €1 = €3, media più bassa)

# Giorni apertura anno
GIORNI_ANNO = 365

# ─── STIMA CONFIGURAZIONE DA NOME/RATING ─────────────────────────────────────
def stima_config(nome: str, rating: float, n_recensioni: int) -> str:
    """
    Stima la dimensione di una lavanderia dal nome e dal numero di recensioni.
    Più recensioni = più traffico = più macchine.
    """
    n = nome.lower()
    if any(k in n for k in ('hub', 'center', 'grande', 'maxi', 'super')):
        return 'grande'
    if n_recensioni and n_recensioni > 300:
        return 'grande'
    if n_recensioni and n_recensioni > 120:
        return 'media'
    if n_recensioni and n_recensioni > 40:
        return 'media'
    return 'piccola'


# ─── CALCOLO CAPACITÀ INSTALLATA CONCORRENZA ─────────────────────────────────
def calcola_capacita_concorrenza(competitors: List[Dict]) -> Dict:
    """
    Per ogni concorrente stima:
    - Configurazione macchine (piccola/media/grande)
    - Capacità massima teorica (cicli/mese)
    - Fatturato stimato a piena occupazione
    - Fatturato stimato reale (65% occupazione media)
    Restituisce totali aggregati + dettaglio per competitor.
    """
    dettaglio = []
    tot_lavatrici   = 0
    tot_asciugatrici = 0
    tot_capex_stimato = 0

    for c in competitors:
        tipo = c.get('tipo_lavanderia', 'self_service')
        if tipo not in ('self_service', 'tradizionale'):
            continue  # escludi industriali

        nome       = c.get('nome', '')
        rating     = float(c.get('rating') or 3.5)
        n_rec      = int(c.get('user_ratings_total') or c.get('n_recensioni') or 0)
        dist_m     = int(c.get('distanza_m') or c.get('dist_m') or 999)

        config_key = stima_config(nome, rating, n_rec)
        config     = CONFIGURAZIONE_TIPO[config_key]
        n_lav      = config['lavatrici']
        n_asc      = config['asciugatrici']

        # Capacità massima teorica/mese
        cap_lav_max = n_lav * 18 * 30   # 18 cicli/giorno max
        cap_asc_max = n_asc * 52 * 30

        # Occupazione stimata da rating e recensioni
        # Alto rating + molte recens = lavanderia che lavora bene → ~70% occ
        # Basso rating o poche recens → 40-55% occ
        if rating >= 4.2 and n_rec > 100:
            occ_stimata = 0.70
        elif rating >= 3.8:
            occ_stimata = 0.58
        elif rating >= 3.0:
            occ_stimata = 0.45
        else:
            occ_stimata = 0.35  # basso rating → pochi clienti

        # Cicli/mese stimati reali
        cicli_lav_reale = n_lav * CICLI_LAVATRICE_GIORNO * 30
        cicli_asc_reale = n_asc * CICLI_ASCIUGATRICE_GIORNO * 30

        # Fatturato stimato
        fatturato_max   = (cap_lav_max * TICKET_LAVAGGIO +
                           cap_asc_max * TICKET_ASCIUGA)
        fatturato_reale = (cicli_lav_reale * occ_stimata * TICKET_LAVAGGIO +
                           cicli_asc_reale * occ_stimata * TICKET_ASCIUGA)

        tot_lavatrici    += n_lav
        tot_asciugatrici += n_asc

        # Capex stimato (valore macchine installate)
        capex_stim = n_lav * 9000 + n_asc * 6500
        tot_capex_stimato += capex_stim

        # Fattore distanza per impatto sulla nostra quota
        if dist_m <= 300:   impatto = 'Diretto'
        elif dist_m <= 600: impatto = 'Alto'
        elif dist_m <= 1000: impatto = 'Medio'
        else:               impatto = 'Basso'

        dettaglio.append({
            'nome':             nome,
            'distanza_m':       dist_m,
            'tipo':             tipo,
            'config_label':     config['label'],
            'n_lavatrici':      n_lav,
            'n_asciugatrici':   n_asc,
            'rating':           rating,
            'n_recensioni':     n_rec,
            'occupazione_stim': occ_stimata,
            'fatturato_reale':  round(fatturato_reale),
            'fatturato_max':    round(fatturato_max),
            'impatto_su_ns':    impatto,
            'capex_stimato':    capex_stim,
        })

    # Mercato totale stimato
    mercato_totale = sum(d['fatturato_reale'] for d in dettaglio)
    capacita_totale_cicli = (
        tot_lavatrici * CICLI_LAVATRICE_GIORNO * 30 +
        tot_asciugatrici * CICLI_ASCIUGATRICE_GIORNO * 30
    )

    return {
        'dettaglio':            dettaglio,
        'tot_lavatrici':        tot_lavatrici,
        'tot_asciugatrici':     tot_asciugatrici,
        'tot_capex_stimato':    tot_capex_stimato,
        'mercato_totale_mese':  round(mercato_totale),
        'capacita_cicli_mese':  capacita_totale_cicli,
        'n_competitors_analizzati': len(dettaglio),
    }


# ─── INDICE FAMIGLIE / LAVANDERIE (Fabrizio Method) ──────────────────────────
def calcola_indice_famiglie_lavanderie(
    pop_5min: int,
    pop_10min: int,
    n_lav_500m: int,
    n_lav_1km: int,
    densita_famiglie: float = 2.3,   # media italiana: 2.3 persone/famiglia
) -> Dict:
    """
    Il KPI più predittivo per lavanderie self-service.
    Formula: famiglie entro 5min ÷ lavanderie concorrenti entro 10min

    Interpretazione:
    > 1500 famiglie/lavanderia → mercato largamente sotto-servito
    800-1500 → opportunità
    400-800  → mercato competitivo ma fattibile
    < 400    → zona satura, sconsigliato
    """
    famiglie_5min  = int(pop_5min  / densita_famiglie)
    famiglie_10min = int(pop_10min / densita_famiglie)

    n_totale_lav = max(1, n_lav_500m + n_lav_1km)  # evita divisione per zero

    indice = famiglie_5min / n_totale_lav

    if   indice > 1500: label = 'Mercato sotto-servito'; colore = '#10b981'; score = 10
    elif indice > 1000: label = 'Opportunità alta';      colore = '#34d399'; score = 8
    elif indice > 600:  label = 'Opportunità buona';     colore = '#84cc16'; score = 6
    elif indice > 400:  label = 'Competitivo';           colore = '#f59e0b'; score = 4
    elif indice > 200:  label = 'Saturo';                colore = '#ef4444'; score = 2
    else:               label = 'Insostenibile';         colore = '#991b1b'; score = 1

    return {
        'famiglie_5min':     famiglie_5min,
        'famiglie_10min':    famiglie_10min,
        'n_lavanderie_area': n_totale_lav,
        'indice':            round(indice),
        'label':             label,
        'colore':            colore,
        'score':             score,
        'interpretazione':   (
            f'{famiglie_5min:,} famiglie entro 5min'
            f' ÷ {n_totale_lav} lavanderie entro 10min'
            f' = {int(indice):,} famiglie per lavanderia'
        ),
    }


# ─── ANALISI PUNTI DEBOLI CONCORRENZA ────────────────────────────────────────
def analizza_punti_deboli(competitors: List[Dict]) -> Dict:
    """
    Identifica i punti deboli della concorrenza per trovare
    il vantaggio competitivo BIOLavaTU.
    """
    if not competitors:
        return {'opportunita': ['Nessun concorrente — mercato libero'], 'score_opportunity': 10}

    ratings = [float(c.get('rating') or 0) for c in competitors if c.get('rating')]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0

    opportunita = []
    rischi = []

    # Rating basso = clienti insoddisfatti = opportunità
    if avg_rating < 3.5:
        opportunita.append(f'⭐ Rating concorrenti basso ({avg_rating:.1f}/5) — clienti insoddisfatti')
    elif avg_rating < 4.0:
        opportunita.append(f'⭐ Rating medio ({avg_rating:.1f}/5) — margine miglioramento')
    else:
        rischi.append(f'⚠️ Concorrenti ben valutati ({avg_rating:.1f}/5) — clienti fidelizzati')

    # Numero recensioni = stima clientela attiva
    total_rec = sum(int(c.get('user_ratings_total') or 0) for c in competitors)
    if total_rec > 500:
        opportunita.append(f'📊 Mercato attivo confermato ({total_rec:,} recensioni totali)')

    # Analisi nomi per identificare punti deboli
    nomi_tutti = ' '.join(c.get('nome', '').lower() for c in competitors)
    if not any(k in nomi_tutti for k in ('biolavatu', 'bio')):
        opportunita.append('🌱 Nessun competitor eco-posizionato — BIOLavaTU unico brand green')
    if not any(k in nomi_tutti for k in ('24', 'notturno', 'h24')):
        opportunita.append('🌙 Nessun competitor H24 — apertura notturna differenziante')

    # Score opportunity (0-10)
    score = min(10, len(opportunita) * 2 + (1 if avg_rating < 3.8 else 0))

    return {
        'avg_rating_concorrenti': round(avg_rating, 1),
        'total_recensioni':       total_rec,
        'opportunita':            opportunita,
        'rischi':                 rischi,
        'score_opportunity':      score,
    }


# ─── STIMA TRAFFICO VEICOLARE DA GOOGLE PLACES ───────────────────────────────
def stima_traffico_veicolare(
    n_stazioni_metro: int,
    n_fermate_bus: int,
    n_parcheggi: int,
    n_strade_principali: int,   # proxy da Google Roads / Places
    recensioni_zona: int,
) -> Dict:
    """
    Stima il traffico veicolare e pedonale dalla combinazione
    di indicatori Google Maps.
    Nota: Google non fornisce contatori traffico direttamente —
    usiamo proxy validati da ricerca settoriale.
    """
    # Score passaggio pedonale (0-100)
    score_pedonale = min(100,
        n_stazioni_metro * 25 +
        n_fermate_bus * 8 +
        min(recensioni_zona // 100, 40)
    )

    # Score accessibilità auto (0-100)
    score_auto = min(100,
        n_parcheggi * 15 +
        n_strade_principali * 10 +
        (20 if n_stazioni_metro > 0 else 0)
    )

    score_totale = int(score_pedonale * 0.60 + score_auto * 0.40)

    if   score_totale >= 80: label = 'Eccellente';  colore = '#10b981'
    elif score_totale >= 60: label = 'Buona';       colore = '#34d399'
    elif score_totale >= 40: label = 'Discreta';    colore = '#f59e0b'
    elif score_totale >= 20: label = 'Limitata';    colore = '#ef4444'
    else:                    label = 'Scarsa';      colore = '#991b1b'

    # Stima auto/giorno (approssimativa, solo orientativa)
    auto_stima = (
        n_stazioni_metro * 800 +
        n_fermate_bus * 200 +
        n_strade_principali * 2000 +
        min(recensioni_zona // 5, 3000)
    )

    pedoni_stima = (
        n_stazioni_metro * 1500 +
        n_fermate_bus * 400 +
        min(recensioni_zona // 3, 5000)
    )

    return {
        'score_pedonale':   score_pedonale,
        'score_auto':       score_auto,
        'score_totale':     score_totale,
        'label':            label,
        'colore':           colore,
        'auto_giorno_stim': auto_stima,
        'pedoni_ora_stim':  pedoni_stima // 14,  # distribuiti su 14h
        'n_fermate_metro':  n_stazioni_metro,
        'n_fermate_bus':    n_fermate_bus,
        'n_parcheggi':      n_parcheggi,
        'nota':             (
            'Stima orientativa da indicatori Google Maps. '
            'Per dati precisi: contatori comunali o sopralluogo diretto.'
        ),
    }


# ─── SCORING PONDERATO TOTALE (metodo Fabrizio) ──────────────────────────────
def calcola_score_ponderato(
    pop_5min: int,
    n_turismo: int,
    n_lav_competitori: int,
    score_traffico: int,
    n_parcheggi: int,
    n_mezzi_pubblici: int,
    reddito_medio: float,
    densita: float,
    indice_famiglie_lav: int,
) -> Dict:
    """
    Score composito a 7 dimensioni con pesi calibrati su Fabrizio method.
    Pesi:
      20% — Residenti entro 5min
      20% — Turisti/B&B/strutture ricettive
      20% — Concorrenza (inverso: più concorrenti = score minore)
      15% — Traffico pedonale/veicolare
       5% — Parcheggi
      10% — Mezzi pubblici
      10% — Indice famiglie/lavanderie
    """
    items = []

    # 1. Residenti 5min (peso 20%)
    if   pop_5min > 8000: s1 = 10
    elif pop_5min > 5000: s1 = 8
    elif pop_5min > 3000: s1 = 6
    elif pop_5min > 1500: s1 = 4
    elif pop_5min > 500:  s1 = 2
    else:                  s1 = 1
    items.append(('Residenti 5 min', s1, 20, pop_5min, f'{pop_5min:,} ab.'))

    # 2. Turismo/B&B (peso 20%)
    if   n_turismo > 20: s2 = 10
    elif n_turismo > 10: s2 = 8
    elif n_turismo > 5:  s2 = 6
    elif n_turismo > 2:  s2 = 4
    elif n_turismo > 0:  s2 = 2
    else:                 s2 = 0
    items.append(('Turismo/B&B/Hotel', s2, 20, n_turismo, f'{n_turismo} strutture'))

    # 3. Concorrenza — inverso (peso 20%)
    if   n_lav_competitori == 0: s3 = 10
    elif n_lav_competitori == 1: s3 = 7
    elif n_lav_competitori == 2: s3 = 5
    elif n_lav_competitori == 3: s3 = 3
    elif n_lav_competitori == 4: s3 = 2
    else:                         s3 = 1
    items.append(('Concorrenza (inverso)', s3, 20, n_lav_competitori,
                  f'{n_lav_competitori} lavanderie entro 1km'))

    # 4. Traffico (peso 15%)
    s4 = min(10, score_traffico // 10)
    items.append(('Visibilità/Traffico', s4, 15, score_traffico, f'Score {score_traffico}/100'))

    # 5. Parcheggi (peso 5%)
    if   n_parcheggi >= 3: s5 = 10
    elif n_parcheggi == 2: s5 = 7
    elif n_parcheggi == 1: s5 = 4
    else:                   s5 = 1
    items.append(('Parcheggi vicini', s5, 5, n_parcheggi, f'{n_parcheggi} parcheggi'))

    # 6. Mezzi pubblici (peso 10%)
    if   n_mezzi_pubblici >= 5: s6 = 10
    elif n_mezzi_pubblici >= 3: s6 = 7
    elif n_mezzi_pubblici >= 1: s6 = 4
    else:                        s6 = 1
    items.append(('Mezzi pubblici', s6, 10, n_mezzi_pubblici, f'{n_mezzi_pubblici} fermate'))

    # 7. Indice famiglie/lavanderie (peso 10%)
    if   indice_famiglie_lav > 1500: s7 = 10
    elif indice_famiglie_lav > 1000: s7 = 8
    elif indice_famiglie_lav > 600:  s7 = 6
    elif indice_famiglie_lav > 400:  s7 = 4
    elif indice_famiglie_lav > 200:  s7 = 2
    else:                             s7 = 1
    items.append(('Famiglie/Lavanderie', s7, 10, indice_famiglie_lav,
                  f'{indice_famiglie_lav:,} fam/lav'))

    # Calcolo score ponderato
    score_100 = sum(s * w for (_, s, w, _, _) in items)  # già pesato su 100

    if   score_100 >= 80: label = 'Eccellente'; colore = '#10b981'
    elif score_100 >= 65: label = 'Ottimo';     colore = '#34d399'
    elif score_100 >= 50: label = 'Buono';      colore = '#84cc16'
    elif score_100 >= 35: label = 'Discreto';   colore = '#f59e0b'
    elif score_100 >= 20: label = 'Scarso';     colore = '#ef4444'
    else:                  label = 'Critico';   colore = '#991b1b'

    # Normalizza a 0-10 per compatibilità con lo score esistente
    score_10 = round(score_100 / 10, 1)

    return {
        'score_100':   score_100,
        'score_10':    score_10,
        'label':       label,
        'colore':      colore,
        'breakdown':   [
            {
                'parametro': nome,
                'score':     s,
                'peso':      w,
                'score_pesato': round(s * w / 10, 1),
                'valore_raw':   vraw,
                'descrizione':  desc,
                'colore': '#10b981' if s >= 7 else '#f59e0b' if s >= 4 else '#ef4444',
            }
            for (nome, s, w, vraw, desc) in items
        ],
    }
