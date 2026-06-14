"""
services/ins_polonia.py — BIOLavaTU LaundryPro
Dati demografici Polonia per województwo (voivodato) + motore analisi.
ISOLATO — zero dipendenze da file italiani, rumeni o albanesi.
"""

EUR_PLN_RATE = 4.28  # 1 EUR = ~4.28 PLN (zloty polacchi)

# ── Dati per Województwo (GUS 2023) ──────────────────────────────────────────
# densita_urbana = densità centro città principale (molto più alta della media voivodato)
WOJE_DATA = {
    'MZ': {'nome': 'Mazowieckie',       'pop': 5548000,  'eta_media': 41.2, 'reddito_medio': 92400,  'densita_judet': 153,  'densita_urbana': 7800, 'perc_stranieri': 4.2, 'citta': 'Warszawa'},
    'SL': {'nome': 'Śląskie',           'pop': 4411000,  'eta_media': 43.1, 'reddito_medio': 72000,  'densita_judet': 358,  'densita_urbana': 5200, 'perc_stranieri': 1.8, 'citta': 'Katowice'},
    'WP': {'nome': 'Wielkopolskie',     'pop': 3524000,  'eta_media': 40.8, 'reddito_medio': 70800,  'densita_judet': 116,  'densita_urbana': 5400, 'perc_stranieri': 1.4, 'citta': 'Poznań'},
    'MP': {'nome': 'Małopolskie',       'pop': 3462000,  'eta_media': 40.2, 'reddito_medio': 68400,  'densita_judet': 228,  'densita_urbana': 5800, 'perc_stranieri': 2.1, 'citta': 'Kraków'},
    'DL': {'nome': 'Dolnośląskie',      'pop': 2889000,  'eta_media': 42.4, 'reddito_medio': 74400,  'densita_judet': 145,  'densita_urbana': 5600, 'perc_stranieri': 2.8, 'citta': 'Wrocław'},
    'LZ': {'nome': 'Łódzkie',          'pop': 2410000,  'eta_media': 43.8, 'reddito_medio': 65200,  'densita_judet': 132,  'densita_urbana': 5200, 'perc_stranieri': 1.2, 'citta': 'Łódź'},
    'PK': {'nome': 'Podkarpackie',      'pop': 2127000,  'eta_media': 40.6, 'reddito_medio': 55200,  'densita_judet': 119,  'densita_urbana': 3800, 'perc_stranieri': 0.8, 'citta': 'Rzeszów'},
    'PM': {'nome': 'Pomorskie',         'pop': 2371000,  'eta_media': 40.1, 'reddito_medio': 73200,  'densita_judet': 129,  'densita_urbana': 5400, 'perc_stranieri': 1.6, 'citta': 'Gdańsk'},
    'LB': {'nome': 'Lubelskie',         'pop': 2071000,  'eta_media': 41.8, 'reddito_medio': 57600,  'densita_judet': 82,   'densita_urbana': 4200, 'perc_stranieri': 0.9, 'citta': 'Lublin'},
    'KP': {'nome': 'Kujawsko-Pomorskie','pop': 2058000,  'eta_media': 42.2, 'reddito_medio': 63600,  'densita_judet': 115,  'densita_urbana': 4400, 'perc_stranieri': 0.7, 'citta': 'Bydgoszcz'},
    'PD': {'nome': 'Podlaskie',         'pop': 1175000,  'eta_media': 42.6, 'reddito_medio': 58800,  'densita_judet': 58,   'densita_urbana': 4000, 'perc_stranieri': 0.6, 'citta': 'Białystok'},
    'ZP': {'nome': 'Zachodniopomorskie','pop': 1694000,  'eta_media': 42.8, 'reddito_medio': 65600,  'densita_judet': 74,   'densita_urbana': 4600, 'perc_stranieri': 1.1, 'citta': 'Szczecin'},
    'WM': {'nome': 'Warmińsko-Mazurskie','pop':1421000,  'eta_media': 41.8, 'reddito_medio': 57200,  'densita_judet': 59,   'densita_urbana': 3800, 'perc_stranieri': 0.5, 'citta': 'Olsztyn'},
    'LU': {'nome': 'Lubuskie',          'pop': 1011000,  'eta_media': 42.4, 'reddito_medio': 63200,  'densita_judet': 73,   'densita_urbana': 3600, 'perc_stranieri': 0.9, 'citta': 'Zielona Góra'},
    'OP': {'nome': 'Opolskie',          'pop': 966000,   'eta_media': 43.6, 'reddito_medio': 64800,  'densita_judet': 103,  'densita_urbana': 3400, 'perc_stranieri': 0.8, 'citta': 'Opole'},
    'SK': {'nome': 'Świętokrzyskie',    'pop': 1207000,  'eta_media': 43.2, 'reddito_medio': 56000,  'densita_judet': 97,   'densita_urbana': 3600, 'perc_stranieri': 0.5, 'citta': 'Kielce'},
},

# ── Dati abitativi per Województwo (GUS 2023 + stime) ────────────────────────
ABITATIVI = {
    'MZ': {'perc_affittuari': 22, 'perc_appartamenti': 68, 'mq_medi': 72, 'perc_senza_lavatrice': 3,  'studenti_uni_1000': 95,  'tasso_disoccupazione': 2.8},
    'MP': {'perc_affittuari': 20, 'perc_appartamenti': 65, 'mq_medi': 70, 'perc_senza_lavatrice': 4,  'studenti_uni_1000': 110, 'tasso_disoccupazione': 2.4},
    'DL': {'perc_affittuari': 18, 'perc_appartamenti': 64, 'mq_medi': 71, 'perc_senza_lavatrice': 4,  'studenti_uni_1000': 85,  'tasso_disoccupazione': 3.2},
    'SL': {'perc_affittuari': 15, 'perc_appartamenti': 70, 'mq_medi': 68, 'perc_senza_lavatrice': 3,  'studenti_uni_1000': 60,  'tasso_disoccupazione': 3.8},
    'WP': {'perc_affittuari': 16, 'perc_appartamenti': 63, 'mq_medi': 73, 'perc_senza_lavatrice': 3,  'studenti_uni_1000': 75,  'tasso_disoccupazione': 2.6},
    'PM': {'perc_affittuari': 19, 'perc_appartamenti': 62, 'mq_medi': 74, 'perc_senza_lavatrice': 3,  'studenti_uni_1000': 80,  'tasso_disoccupazione': 2.9},
    'LZ': {'perc_affittuari': 14, 'perc_appartamenti': 66, 'mq_medi': 69, 'perc_senza_lavatrice': 4,  'studenti_uni_1000': 70,  'tasso_disoccupazione': 4.2},
    '_default': {'perc_affittuari': 14, 'perc_appartamenti': 60, 'mq_medi': 72, 'perc_senza_lavatrice': 5, 'studenti_uni_1000': 40, 'tasso_disoccupazione': 5.2},
}

# ── Tariffe default Polonia ───────────────────────────────────────────────────
TARIFFE_DEFAULT_PL = {
    'lavaggio_std_pln': 20.0,   # ~4.70 EUR per 6kg
    'lavaggio_med_pln': 26.0,   # ~6.10 EUR per 9kg
    'lavaggio_grd_pln': 36.0,   # ~8.40 EUR per 15kg
    'asciugatura_pln':  10.0,   # ~2.30 EUR/ciclo
}

OCC_BASE_PL  = 0.42
EUR_PLN_RATE = 4.28


# ── Funzioni dati ─────────────────────────────────────────────────────────────

def get_demographic_data_pl(woje_cod: str, miasto: str = '') -> dict:
    data = WOJE_DATA.get(woje_cod.upper() if woje_cod else '')
    if not data and miasto:
        for cod, d in WOJE_DATA.items():
            if miasto.lower() in d['nome'].lower() or d['nome'].lower() in miasto.lower() \
               or miasto.lower() in d.get('citta','').lower():
                data = d
                break
    if not data:
        data = {
            'nome': miasto or 'Polska', 'pop': 0, 'eta_media': 42.0,
            'reddito_medio': 64000, 'densita_judet': 100, 'densita_urbana': 4000,
            'perc_stranieri': 1.2, 'citta': miasto or '',
        }
    abit = ABITATIVI.get(woje_cod.upper() if woje_cod else '', ABITATIVI['_default'])
    return {
        'eta_media':             data['eta_media'],
        'reddito_medio':         data['reddito_medio'],         # PLN/anno
        'reddito_eur':           round(data['reddito_medio'] / EUR_PLN_RATE),
        'densita':               data.get('densita_urbana', data['densita_judet']),
        'perc_stranieri':        data['perc_stranieri'],
        'pop_totale':            data['pop'],
        'perc_affittuari':       abit['perc_affittuari'],
        'perc_appartamenti':     abit['perc_appartamenti'],
        'mq_medi':               abit['mq_medi'],
        'perc_senza_lavatrice':  abit['perc_senza_lavatrice'],
        'studenti_uni_1000':     abit['studenti_uni_1000'],
        'tasso_disoccupazione':  abit['tasso_disoccupazione'],
        'paese': 'PL', 'valuta': 'PLN', 'fonte': 'GUS Polonia 2023',
    }


def get_densita_urbana_pl(woje_cod: str, n_poi_zona: int = 0) -> float:
    d = WOJE_DATA.get(woje_cod.upper() if woje_cod else {})
    base = d.get('densita_urbana', 4000) if d else 4000
    if   n_poi_zona >= 30: factor = 1.00
    elif n_poi_zona >= 15: factor = 0.75
    elif n_poi_zona >= 5:  factor = 0.50
    else:                  factor = 0.30
    return base * factor


def get_market_assessment_pl(reddito_pln: float, densita: float) -> dict:
    score = 0
    if   densita > 4000: score += 30
    elif densita > 2000: score += 22
    elif densita > 500:  score += 14
    elif densita > 100:  score += 8
    else:                score += 2
    if   reddito_pln > 90000: score += 25
    elif reddito_pln > 70000: score += 20
    elif reddito_pln > 55000: score += 14
    elif reddito_pln > 40000: score += 8
    else:                      score += 3
    if densita > 3000: score += 20
    elif densita > 1000: score += 14
    elif densita > 200: score += 7
    score = min(100, score)
    potenziale = ('alto' if reddito_pln > 70000 and densita > 1000 else
                  'medio' if reddito_pln > 50000 else 'basso')
    if   score >= 70: label, colore = 'Doskonały', '#10b981'
    elif score >= 55: label, colore = 'Dobry',     '#3b82f6'
    elif score >= 35: label, colore = 'Średni',    '#f59e0b'
    else:             label, colore = 'Słaby',     '#ef4444'
    return {'score': score, 'label': label, 'colore': colore,
            'potenziale': potenziale, 'paese': 'PL'}


def get_f_miasto_pl(pop: int) -> float:
    if   pop >= 1000000: return 1.00
    elif pop >= 500000:  return 0.92
    elif pop >= 200000:  return 0.82
    elif pop >= 100000:  return 0.72
    elif pop >= 50000:   return 0.62
    elif pop >= 20000:   return 0.52
    else:                return 0.42


def calcola_potenziale_lavaggi_pl(
    pop_5min: int,
    perc_affittuari: float,
    perc_senza_lavatrice: float,
    studenti_uni_1000: float,
    perc_stranieri: float,
    n_hotel_bb: int,
    frequenza_lavaggi_mese: float = 2.2,
) -> dict:
    famiglie_5min = pop_5min // 2.6  # media 2.6 persone/famiglia Polonia

    seg_senza_lav  = famiglie_5min * (perc_senza_lavatrice / 100)
    seg_affittuari = famiglie_5min * (perc_affittuari / 100) * 0.12
    studenti_zona  = pop_5min * (studenti_uni_1000 / 1000) * 0.3
    seg_studenti   = studenti_zona * 0.45
    seg_immigrati  = pop_5min * (perc_stranieri / 100) * 0.30
    seg_pro        = n_hotel_bb * 9

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


def calcola_incasso_da_lavaggi_pl(
    lavaggi_quota: int,
    t_lav_medio_pln: float,
    perc_asciugatura: float = 50,
    t_asc_pln: float = 10.0,
) -> float:
    return round(lavaggi_quota * t_lav_medio_pln +
                 lavaggi_quota * (perc_asciugatura / 100) * t_asc_pln)


def calcola_affitto_max_pl(fatturato_pln: float) -> dict:
    return {
        'affitto_max_10pct': round(fatturato_pln * 0.10),
        'affitto_max_12pct': round(fatturato_pln * 0.12),
        'regola': '10-12% del fatturato previsto',
    }


def calcola_costi_operativi_pl(
    n_lavatrici: int,
    n_asciugatrici: int,
    cicli_giorno_lav: float = 6,
    cicli_giorno_asc: float = 8,
    costi_override: dict = None,
) -> dict:
    COSTI_DEFAULT = {
        'kwh_pln': 0.92,          # PLN/kWh (~0.21 EUR)
        'mc_acqua_pln': 8.50,     # PLN/mc
        'mc_fognatura_pln': 6.20,
        'internet_pln': 80.0,     # PLN/mese (~19 EUR)
        'assicurazione_pln': 200.0,
    }
    c = {**COSTI_DEFAULT, **(costi_override or {})}
    giorni = 30

    kwh_lav = n_lavatrici * cicli_giorno_lav * 1.2 * giorni
    kwh_asc = n_asciugatrici * cicli_giorno_asc * 3.5 * giorni
    costo_energia = (kwh_lav + kwh_asc) * c['kwh_pln']

    mc_acqua = n_lavatrici * cicli_giorno_lav * 0.065 * giorni
    costo_acqua = mc_acqua * (c['mc_acqua_pln'] + c['mc_fognatura_pln'])

    totale = costo_energia + costo_acqua + c['internet_pln'] + c['assicurazione_pln']

    return {
        'energia_pln':       round(costo_energia),
        'acqua_pln':         round(costo_acqua),
        'internet_pln':      round(c['internet_pln']),
        'assicurazione_pln': round(c['assicurazione_pln']),
        'totale_utenze_pln': round(totale),
        'totale_utenze_eur': round(totale / EUR_PLN_RATE),
        'kwh_mese':          round(kwh_lav + kwh_asc),
        'mc_acqua_mese':     round(mc_acqua, 1),
    }


def calcola_saturazione_pl(pop_5min: int, n_lavatrici_zona: int) -> dict:
    if n_lavatrici_zona == 0:
        return {'indice': 99999, 'label': 'Monopol', 'colore': '#10b981', 'n_lavatrici_zona': 0}
    indice = pop_5min // n_lavatrici_zona
    if   indice > 6000: label, colore = 'Optymalny',    '#10b981'
    elif indice > 3000: label, colore = 'Konkurencyjny','#3b82f6'
    elif indice > 1500: label, colore = 'Nasycony',     '#f59e0b'
    else:               label, colore = 'Bardzo nasycony','#ef4444'
    return {'indice': indice, 'label': label, 'colore': colore, 'n_lavatrici_zona': n_lavatrici_zona}


def converti_pln_eur(pln: float) -> float:
    return round(pln / EUR_PLN_RATE, 2)

def converti_eur_pln(eur: float) -> float:
    return round(eur * EUR_PLN_RATE, 2)

def get_cambio_pln_live() -> float:
    try:
        import urllib.request as _ur, json as _j
        with _ur.urlopen(_ur.Request('https://api.frankfurter.app/latest?from=EUR&to=PLN'), timeout=3) as r:
            return float(_j.loads(r.read())['rates']['PLN'])
    except Exception:
        return EUR_PLN_RATE
