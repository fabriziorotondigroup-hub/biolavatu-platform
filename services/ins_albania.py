"""
services/ins_albania.py — BIOLavaTU LaundryPro
Dati demografici Albania per qark (regione) + motore analisi.
ISOLATO — zero dipendenze da file italiani o rumeni.
"""

EUR_ALL_RATE = 98.5  # 1 EUR = ~98.5 ALL (Lek albanesi)

# ── Dati per Qark (INSTAT 2023) ───────────────────────────────────────────────
# densita_urbana = densità centro città (molto più alta della media qark)
QARK_DATA = {
    'TI': {'nome': 'Tiranë',      'pop': 930631, 'eta_media': 33.2, 'reddito_medio': 720000, 'densita_judet': 278,  'densita_urbana': 5200, 'perc_stranieri': 2.1},
    'DR': {'nome': 'Durrës',      'pop': 370007, 'eta_media': 34.5, 'reddito_medio': 600000, 'densita_judet': 326,  'densita_urbana': 4200, 'perc_stranieri': 1.2},
    'VL': {'nome': 'Vlorë',       'pop': 190000, 'eta_media': 35.8, 'reddito_medio': 480000, 'densita_judet': 72,   'densita_urbana': 3800, 'perc_stranieri': 1.8},
    'SH': {'nome': 'Shkodër',     'pop': 210000, 'eta_media': 35.2, 'reddito_medio': 420000, 'densita_judet': 68,   'densita_urbana': 3200, 'perc_stranieri': 0.8},
    'EL': {'nome': 'Elbasan',     'pop': 300000, 'eta_media': 35.6, 'reddito_medio': 420000, 'densita_judet': 132,  'densita_urbana': 3500, 'perc_stranieri': 0.6},
    'KO': {'nome': 'Korçë',       'pop': 210000, 'eta_media': 37.1, 'reddito_medio': 400000, 'densita_judet': 56,   'densita_urbana': 3000, 'perc_stranieri': 0.9},
    'FK': {'nome': 'Fier',        'pop': 300000, 'eta_media': 34.8, 'reddito_medio': 400000, 'densita_judet': 194,  'densita_urbana': 3200, 'perc_stranieri': 0.5},
    'GJ': {'nome': 'Gjirokastër', 'pop': 75000,  'eta_media': 38.2, 'reddito_medio': 360000, 'densita_judet': 27,   'densita_urbana': 2600, 'perc_stranieri': 1.2},
    'BE': {'nome': 'Berat',       'pop': 130000, 'eta_media': 36.4, 'reddito_medio': 360000, 'densita_judet': 87,   'densita_urbana': 2800, 'perc_stranieri': 0.5},
    'DI': {'nome': 'Dibër',       'pop': 130000, 'eta_media': 32.4, 'reddito_medio': 320000, 'densita_judet': 48,   'densita_urbana': 2200, 'perc_stranieri': 0.3},
    'LE': {'nome': 'Lezhë',       'pop': 135000, 'eta_media': 33.8, 'reddito_medio': 360000, 'densita_judet': 79,   'densita_urbana': 2400, 'perc_stranieri': 0.4},
    'KU': {'nome': 'Kukës',       'pop': 80000,  'eta_media': 31.2, 'reddito_medio': 280000, 'densita_judet': 34,   'densita_urbana': 1800, 'perc_stranieri': 0.2},
}

# ── Dati abitativi per Qark (INSTAT 2023 + stime) ────────────────────────────
ABITATIVI = {
    'TI': {'perc_affittuari': 45, 'perc_appartamenti': 72, 'mq_medi': 78, 'perc_senza_lavatrice': 18, 'studenti_uni_1000': 95,  'tasso_disoccupazione': 11.2},
    'DR': {'perc_affittuari': 38, 'perc_appartamenti': 65, 'mq_medi': 82, 'perc_senza_lavatrice': 22, 'studenti_uni_1000': 35,  'tasso_disoccupazione': 13.5},
    'VL': {'perc_affittuari': 30, 'perc_appartamenti': 58, 'mq_medi': 85, 'perc_senza_lavatrice': 20, 'studenti_uni_1000': 28,  'tasso_disoccupazione': 14.2},
    'SH': {'perc_affittuari': 28, 'perc_appartamenti': 52, 'mq_medi': 88, 'perc_senza_lavatrice': 25, 'studenti_uni_1000': 22,  'tasso_disoccupazione': 15.8},
    'EL': {'perc_affittuari': 32, 'perc_appartamenti': 55, 'mq_medi': 84, 'perc_senza_lavatrice': 24, 'studenti_uni_1000': 30,  'tasso_disoccupazione': 16.4},
    'KO': {'perc_affittuari': 25, 'perc_appartamenti': 48, 'mq_medi': 90, 'perc_senza_lavatrice': 28, 'studenti_uni_1000': 20,  'tasso_disoccupazione': 17.2},
    'FK': {'perc_affittuari': 30, 'perc_appartamenti': 52, 'mq_medi': 86, 'perc_senza_lavatrice': 26, 'studenti_uni_1000': 18,  'tasso_disoccupazione': 15.5},
    'GJ': {'perc_affittuari': 22, 'perc_appartamenti': 45, 'mq_medi': 92, 'perc_senza_lavatrice': 30, 'studenti_uni_1000': 15,  'tasso_disoccupazione': 18.5},
    'BE': {'perc_affittuari': 24, 'perc_appartamenti': 48, 'mq_medi': 90, 'perc_senza_lavatrice': 28, 'studenti_uni_1000': 15,  'tasso_disoccupazione': 17.8},
    '_default': {'perc_affittuari': 28, 'perc_appartamenti': 55, 'mq_medi': 85, 'perc_senza_lavatrice': 25, 'studenti_uni_1000': 20, 'tasso_disoccupazione': 15.0},
}

# ── Tariffe default Albania ───────────────────────────────────────────────────
TARIFFE_DEFAULT_AL = {
    'lavaggio_std_all': 600.0,   # ~6 EUR per 6kg
    'lavaggio_med_all': 800.0,   # ~8 EUR per 9kg
    'lavaggio_grd_all': 1200.0,  # ~12 EUR per 15kg
    'asciugatura_all':  300.0,   # ~3 EUR/ciclo
}

OCC_BASE_AL  = 0.40
EUR_ALL_RATE = 98.5


# ── Funzioni dati ─────────────────────────────────────────────────────────────

def get_demographic_data_al(qark_cod: str, qyteti: str = '') -> dict:
    data = QARK_DATA.get(qark_cod.upper() if qark_cod else '')
    if not data and qyteti:
        for cod, d in QARK_DATA.items():
            if qyteti.lower() in d['nome'].lower() or d['nome'].lower() in qyteti.lower():
                data = d
                break
    if not data:
        data = {
            'nome': qyteti or 'Shqipëri', 'pop': 0, 'eta_media': 35.0,
            'reddito_medio': 420000, 'densita_judet': 90, 'densita_urbana': 2500,
            'perc_stranieri': 0.8,
        }
    abit = ABITATIVI.get(qark_cod.upper() if qark_cod else '', ABITATIVI['_default'])
    return {
        'eta_media':             data['eta_media'],
        'reddito_medio':         data['reddito_medio'],         # in ALL/anno
        'reddito_eur':           round(data['reddito_medio'] / EUR_ALL_RATE),
        'densita':               data.get('densita_urbana', data['densita_judet']),
        'perc_stranieri':        data['perc_stranieri'],
        'pop_totale':            data['pop'],
        'perc_affittuari':       abit['perc_affittuari'],
        'perc_appartamenti':     abit['perc_appartamenti'],
        'mq_medi':               abit['mq_medi'],
        'perc_senza_lavatrice':  abit['perc_senza_lavatrice'],
        'studenti_uni_1000':     abit['studenti_uni_1000'],
        'tasso_disoccupazione':  abit['tasso_disoccupazione'],
        'paese': 'AL', 'valuta': 'ALL', 'fonte': 'INSTAT Albania 2023',
    }


def get_densita_urbana_al(qark_cod: str, n_poi_zona: int = 0) -> float:
    base = QARK_DATA.get(qark_cod.upper() if qark_cod else {}, {}).get('densita_urbana', 2500)
    if   n_poi_zona >= 30: factor = 1.00
    elif n_poi_zona >= 15: factor = 0.75
    elif n_poi_zona >= 5:  factor = 0.50
    else:                  factor = 0.30
    return base * factor


def get_market_assessment_al(reddito_all: float, densita: float) -> dict:
    score = 0
    if   densita > 3000: score += 30
    elif densita > 1000: score += 22
    elif densita > 300:  score += 14
    elif densita > 80:   score += 8
    else:                score += 2
    if   reddito_all > 800000: score += 25
    elif reddito_all > 600000: score += 20
    elif reddito_all > 400000: score += 14
    elif reddito_all > 280000: score += 8
    else:                       score += 3
    if densita > 2000: score += 20
    elif densita > 500: score += 14
    elif densita > 100: score += 7
    score = min(100, score)
    potenziale = ('alto' if reddito_all > 600000 and densita > 500 else
                  'medio' if reddito_all > 400000 else 'basso')
    if   score >= 70: label, colore = 'Shkelqyer', '#10b981'
    elif score >= 55: label, colore = 'I mire',    '#3b82f6'
    elif score >= 35: label, colore = 'Mesatar',   '#f59e0b'
    else:             label, colore = 'I dobet',   '#ef4444'
    return {'score': score, 'label': label, 'colore': colore,
            'potenziale': potenziale, 'paese': 'AL'}


def get_f_qyteti_al(pop: int) -> float:
    if   pop >= 500000: return 1.00
    elif pop >= 200000: return 0.85
    elif pop >= 100000: return 0.75
    elif pop >= 50000:  return 0.65
    elif pop >= 20000:  return 0.55
    else:               return 0.45


def calcola_potenziale_lavaggi_al(
    pop_5min: int,
    perc_affittuari: float,
    perc_senza_lavatrice: float,
    studenti_uni_1000: float,
    perc_stranieri: float,
    n_hotel_bb: int,
    frequenza_lavaggi_mese: float = 2.5,
) -> dict:
    famiglie_5min = pop_5min // 3.2  # media 3.2 persone/famiglia Albania

    seg_senza_lav  = famiglie_5min * (perc_senza_lavatrice / 100)
    seg_affittuari = famiglie_5min * (perc_affittuari / 100) * 0.15
    studenti_zona  = pop_5min * (studenti_uni_1000 / 1000) * 0.3
    seg_studenti   = studenti_zona * 0.40
    seg_immigrati  = pop_5min * (perc_stranieri / 100) * 0.25
    seg_pro        = n_hotel_bb * 8

    clienti_totali  = seg_senza_lav + seg_affittuari + seg_studenti + seg_immigrati + seg_pro
    lavaggi_teorici = clienti_totali * frequenza_lavaggi_mese

    return {
        'clienti_totali_stimati': round(clienti_totali),
        'lavaggi_mese_teorici':   round(lavaggi_teorici),
        'segmenti': {
            'senza_lavatrice': round(seg_senza_lav),
            'affittuari':      round(seg_affittuari),
            'studenti':        round(seg_studenti),
            'immigrati':       round(seg_immigrati),
            'professionali':   round(seg_pro),
        },
        'quota_10pct': round(lavaggi_teorici * 0.10),
        'quota_20pct': round(lavaggi_teorici * 0.20),
        'quota_30pct': round(lavaggi_teorici * 0.30),
    }


def calcola_incasso_da_lavaggi_al(
    lavaggi_quota: int,
    t_lav_medio_all: float,
    perc_asciugatura: float = 55,
    t_asc_all: float = 300.0,
) -> float:
    incasso_lav = lavaggi_quota * t_lav_medio_all
    incasso_asc = lavaggi_quota * (perc_asciugatura / 100) * t_asc_all
    return round(incasso_lav + incasso_asc)


def calcola_affitto_max_al(fatturato_all: float) -> dict:
    return {
        'affitto_max_10pct': round(fatturato_all * 0.10),
        'affitto_max_12pct': round(fatturato_all * 0.12),
        'regola': '10-12% del fatturato previsto',
    }


def calcola_costi_operativi_al(
    n_lavatrici: int,
    n_asciugatrici: int,
    cicli_giorno_lav: float = 6,
    cicli_giorno_asc: float = 8,
    costi_override: dict = None,
) -> dict:
    COSTI_DEFAULT = {
        'kwh_all': 14.0,         # ALL/kWh (~0.14 EUR)
        'mc_acqua_all': 80.0,    # ALL/mc
        'mc_fognatura_all': 50.0,
        'internet_all': 2500.0,  # ALL/mese (~25 EUR)
        'assicurazione_all': 5000.0,
    }
    c = {**COSTI_DEFAULT, **(costi_override or {})}
    giorni = 30

    kwh_lav = n_lavatrici * cicli_giorno_lav * 1.2 * giorni
    kwh_asc = n_asciugatrici * cicli_giorno_asc * 3.5 * giorni
    costo_energia = (kwh_lav + kwh_asc) * c['kwh_all']

    mc_acqua = n_lavatrici * cicli_giorno_lav * 0.065 * giorni
    costo_acqua = mc_acqua * (c['mc_acqua_all'] + c['mc_fognatura_all'])

    totale_utenze = costo_energia + costo_acqua + c['internet_all'] + c['assicurazione_all']

    return {
        'energia_all':     round(costo_energia),
        'acqua_all':       round(costo_acqua),
        'internet_all':    round(c['internet_all']),
        'assicurazione_all': round(c['assicurazione_all']),
        'totale_utenze_all': round(totale_utenze),
        'totale_utenze_eur': round(totale_utenze / EUR_ALL_RATE),
        'kwh_mese':        round(kwh_lav + kwh_asc),
        'mc_acqua_mese':   round(mc_acqua, 1),
    }


def calcola_saturazione_al(pop_5min: int, n_lavatrici_zona: int) -> dict:
    if n_lavatrici_zona == 0:
        indice = 99999
        label  = 'Monopoli'
        colore = '#10b981'
    else:
        indice = pop_5min // n_lavatrici_zona
        if   indice > 6000: label, colore = 'Optimale',   '#10b981'
        elif indice > 3000: label, colore = 'Competitive','#3b82f6'
        elif indice > 1500: label, colore = 'E ngoptur',  '#f59e0b'
        else:               label, colore = 'Shume e ngoptur', '#ef4444'
    return {'indice': indice, 'label': label, 'colore': colore,
            'n_lavatrici_zona': n_lavatrici_zona}


# ── Utilities ─────────────────────────────────────────────────────────────────

def converti_all_eur(al: float) -> float:
    return round(al / EUR_ALL_RATE, 2)

def converti_eur_all(eur: float) -> float:
    return round(eur * EUR_ALL_RATE, 2)

def get_cambio_all_live() -> float:
    try:
        import urllib.request as _ur, json as _j
        req = _ur.Request('https://api.frankfurter.app/latest?from=EUR&to=ALL')
        with _ur.urlopen(req, timeout=3) as r:
            return float(_j.loads(r.read())['rates']['ALL'])
    except Exception:
        return EUR_ALL_RATE
