"""
services/ins_slovenia.py — BIOLavaTU LaundryPro
Dati demografici Slovenia per statistična regija (regione statistica) + motore analisi.
ISOLATO — zero dipendenze da altri mercati.
"""

EUR_SIT_RATE = 1.0  # Slovenia usa EUR dal 2007

REGIJA_DATA = {
    'OS': {'nome': 'Osrednjeslovenska', 'pop': 557332, 'eta_media': 42.2, 'reddito_medio': 28400, 'densita_urbana': 6800, 'perc_stranieri': 8.2, 'citta': 'Ljubljana'},
    'PO': {'nome': 'Podravska',         'pop': 323159, 'eta_media': 43.8, 'reddito_medio': 21600, 'densita_urbana': 4200, 'perc_stranieri': 5.4, 'citta': 'Maribor'},
    'SA': {'nome': 'Savinjska',         'pop': 261022, 'eta_media': 43.4, 'reddito_medio': 22800, 'densita_urbana': 3800, 'perc_stranieri': 4.8, 'citta': 'Celje'},
    'GO': {'nome': 'Gorenjska',         'pop': 209147, 'eta_media': 42.6, 'reddito_medio': 24600, 'densita_urbana': 4400, 'perc_stranieri': 5.6, 'citta': 'Kranj'},
    'DO': {'nome': 'Dolenjska',         'pop': 145018, 'eta_media': 43.8, 'reddito_medio': 21200, 'densita_urbana': 3200, 'perc_stranieri': 4.2, 'citta': 'Novo Mesto'},
    'KO': {'nome': 'Koroška',           'pop': 71908,  'eta_media': 44.2, 'reddito_medio': 20400, 'densita_urbana': 2600, 'perc_stranieri': 2.8, 'citta': 'Slovenj Gradec'},
    'PR': {'nome': 'Primorsko-notranjska','pop': 52816, 'eta_media': 43.6, 'reddito_medio': 22000, 'densita_urbana': 2400, 'perc_stranieri': 3.2, 'citta': 'Postojna'},
    'GO2':{'nome': 'Goriška',           'pop': 118008, 'eta_media': 44.4, 'reddito_medio': 23200, 'densita_urbana': 3400, 'perc_stranieri': 4.4, 'citta': 'Nova Gorica'},
    'OB': {'nome': 'Obalno-kraška',     'pop': 115623, 'eta_media': 43.2, 'reddito_medio': 25600, 'densita_urbana': 4000, 'perc_stranieri': 6.8, 'citta': 'Koper'},
    'ZA': {'nome': 'Zasavska',          'pop': 41016,  'eta_media': 44.8, 'reddito_medio': 20000, 'densita_urbana': 2800, 'perc_stranieri': 3.6, 'citta': 'Trbovlje'},
    'PD': {'nome': 'Posavska',          'pop': 75568,  'eta_media': 44.2, 'reddito_medio': 20800, 'densita_urbana': 2600, 'perc_stranieri': 3.0, 'citta': 'Brežice'},
    'JV': {'nome': 'Jugovzhodna Slovenija','pop': 145018,'eta_media': 43.6,'reddito_medio': 21600,'densita_urbana': 3000, 'perc_stranieri': 3.8, 'citta': 'Kočevje'},
}

ABITATIVI = {
    'OS': {'perc_affittuari': 24, 'perc_appartamenti': 65, 'mq_medi': 78, 'perc_senza_lavatrice': 3,  'studenti_uni_1000': 92,  'tasso_disoccupazione': 3.8},
    'PO': {'perc_affittuari': 18, 'perc_appartamenti': 60, 'mq_medi': 82, 'perc_senza_lavatrice': 4,  'studenti_uni_1000': 55,  'tasso_disoccupazione': 6.2},
    'SA': {'perc_affittuari': 16, 'perc_appartamenti': 58, 'mq_medi': 84, 'perc_senza_lavatrice': 4,  'studenti_uni_1000': 42,  'tasso_disoccupazione': 5.8},
    'GO': {'perc_affittuari': 18, 'perc_appartamenti': 58, 'mq_medi': 80, 'perc_senza_lavatrice': 3,  'studenti_uni_1000': 38,  'tasso_disoccupazione': 4.4},
    'OB': {'perc_affittuari': 22, 'perc_appartamenti': 62, 'mq_medi': 76, 'perc_senza_lavatrice': 4,  'studenti_uni_1000': 32,  'tasso_disoccupazione': 4.8},
    '_default': {'perc_affittuari': 15, 'perc_appartamenti': 55, 'mq_medi': 82, 'perc_senza_lavatrice': 4, 'studenti_uni_1000': 28, 'tasso_disoccupazione': 5.5},
}

TARIFFE_DEFAULT_SI = {
    'lavaggio_std_eur': 5.0,
    'lavaggio_med_eur': 7.0,
    'lavaggio_grd_eur': 9.5,
    'asciugatura_eur':  3.0,
}

OCC_BASE_SI  = 0.42
EUR_SIT_RATE = 1.0  # già EUR


def get_demographic_data_si(regija_cod: str, mesto: str = '') -> dict:
    data = REGIJA_DATA.get(regija_cod.upper() if regija_cod else '')
    if not data and mesto:
        for cod, d in REGIJA_DATA.items():
            if mesto.lower() in d['nome'].lower() or d['nome'].lower() in mesto.lower() \
               or mesto.lower() in d.get('citta', '').lower():
                data = d; break
    if not data:
        data = {'nome': mesto or 'Slovenija', 'pop': 0, 'eta_media': 43.0,
                'reddito_medio': 22000, 'densita_urbana': 3200, 'perc_stranieri': 4.5, 'citta': mesto or ''}
    abit = ABITATIVI.get(regija_cod.upper() if regija_cod else '', ABITATIVI['_default'])
    return {
        'eta_media':             data['eta_media'],
        'reddito_medio':         data['reddito_medio'],   # EUR/anno
        'reddito_eur':           data['reddito_medio'],
        'densita':               data.get('densita_urbana', 3200),
        'perc_stranieri':        data['perc_stranieri'],
        'pop_totale':            data['pop'],
        'perc_affittuari':       abit['perc_affittuari'],
        'perc_appartamenti':     abit['perc_appartamenti'],
        'mq_medi':               abit['mq_medi'],
        'perc_senza_lavatrice':  abit['perc_senza_lavatrice'],
        'studenti_uni_1000':     abit['studenti_uni_1000'],
        'tasso_disoccupazione':  abit['tasso_disoccupazione'],
        'paese': 'SI', 'valuta': 'EUR', 'fonte': 'SURS Slovenia 2023',
    }


def get_densita_urbana_si(regija_cod: str, n_poi_zona: int = 0) -> float:
    d = REGIJA_DATA.get(regija_cod.upper() if regija_cod else {})
    base = d.get('densita_urbana', 3200) if d else 3200
    if   n_poi_zona >= 30: factor = 1.00
    elif n_poi_zona >= 15: factor = 0.75
    elif n_poi_zona >= 5:  factor = 0.50
    else:                  factor = 0.30
    return base * factor


def get_market_assessment_si(reddito_eur: float, densita: float) -> dict:
    score = 0
    if   densita > 5000: score += 30
    elif densita > 3000: score += 24
    elif densita > 1000: score += 16
    else:                score += 6
    if   reddito_eur > 26000: score += 25
    elif reddito_eur > 22000: score += 20
    elif reddito_eur > 18000: score += 14
    else:                      score += 7
    if densita > 3000: score += 20
    elif densita > 1000: score += 12
    score = min(100, score)
    potenziale = ('alto' if reddito_eur > 23000 and densita > 2000 else
                  'medio' if reddito_eur > 18000 else 'basso')
    if   score >= 70: label, colore = 'Odlično',  '#10b981'
    elif score >= 55: label, colore = 'Dobro',    '#3b82f6'
    elif score >= 35: label, colore = 'Srednje',  '#f59e0b'
    else:             label, colore = 'Slabo',    '#ef4444'
    return {'score': score, 'label': label, 'colore': colore, 'potenziale': potenziale, 'paese': 'SI'}


def get_f_mesto_si(pop: int) -> float:
    if   pop >= 300000: return 1.00
    elif pop >= 100000: return 0.88
    elif pop >= 50000:  return 0.78
    elif pop >= 20000:  return 0.68
    elif pop >= 10000:  return 0.58
    else:               return 0.48


def calcola_potenziale_lavaggi_si(pop_5min, perc_affittuari, perc_senza_lavatrice,
                                   studenti_uni_1000, perc_stranieri, n_hotel_bb,
                                   frequenza_lavaggi_mese=2.3):
    famiglie = pop_5min // 2.5  # Slovenia media 2.5 persone/famiglia
    seg_senza_lav  = famiglie * (perc_senza_lavatrice / 100)
    seg_affittuari = famiglie * (perc_affittuari / 100) * 0.13
    seg_studenti   = pop_5min * (studenti_uni_1000 / 1000) * 0.3 * 0.44
    seg_immigrati  = pop_5min * (perc_stranieri / 100) * 0.32
    seg_pro        = n_hotel_bb * 9
    clienti        = seg_senza_lav + seg_affittuari + seg_studenti + seg_immigrati + seg_pro
    lavaggi        = clienti * frequenza_lavaggi_mese
    return {
        'clienti_totali_stimati': round(clienti),
        'lavaggi_mese_teorici':   round(lavaggi),
        'segmenti': {'senza_lavatrice': round(seg_senza_lav), 'affittuari': round(seg_affittuari),
                     'studenti': round(seg_studenti), 'immigrati': round(seg_immigrati), 'professionali': round(seg_pro)},
        'quota_10pct': round(lavaggi * 0.10),
        'quota_20pct': round(lavaggi * 0.20),
        'quota_30pct': round(lavaggi * 0.30),
    }


def calcola_costi_operativi_si(n_lavatrici, n_asciugatrici, cicli_giorno_lav=6, cicli_giorno_asc=8, costi_override=None):
    C = {'kwh_eur': 0.22, 'mc_acqua_eur': 2.80, 'mc_fognatura_eur': 2.10, 'internet_eur': 30.0, 'assicurazione_eur': 70.0}
    if costi_override: C.update(costi_override)
    giorni = 30
    kwh_lav = n_lavatrici * cicli_giorno_lav * 1.2 * giorni
    kwh_asc = n_asciugatrici * cicli_giorno_asc * 3.5 * giorni
    costo_e = (kwh_lav + kwh_asc) * C['kwh_eur']
    mc_acq  = n_lavatrici * cicli_giorno_lav * 0.065 * giorni
    costo_a = mc_acq * (C['mc_acqua_eur'] + C['mc_fognatura_eur'])
    tot     = costo_e + costo_a + C['internet_eur'] + C['assicurazione_eur']
    return {'energia_eur': round(costo_e), 'acqua_eur': round(costo_a),
            'internet_eur': round(C['internet_eur']), 'assicurazione_eur': round(C['assicurazione_eur']),
            'totale_utenze_eur': round(tot), 'kwh_mese': round(kwh_lav + kwh_asc), 'mc_acqua_mese': round(mc_acq, 1)}


def get_cambio_si_live() -> float:
    return 1.0  # Slovenia è in Eurozona dal 2007


# ── Alias e costanti per compatibilità route ─────────────────────────────────
EUR_SIT_RATE = 1.0   # Slovenia usa EUR dal 2007
OCC_BASE_SI  = 0.42

def converti_eur_eur(v: float) -> float:
    return round(v, 2)  # già in EUR

def calcola_incasso_da_lavaggi_si(
    lavaggi_quota: int,
    t_lav_medio_eur: float,
    perc_asciugatura: float = 50,
    t_asc_eur: float = 3.0,
) -> float:
    return round(lavaggi_quota * t_lav_medio_eur +
                 lavaggi_quota * (perc_asciugatura / 100) * t_asc_eur)

def calcola_affitto_max_si(fatturato_eur: float) -> dict:
    return {
        'affitto_max_10pct': round(fatturato_eur * 0.10),
        'affitto_max_12pct': round(fatturato_eur * 0.12),
        'regola': '10-12% del fatturato previsto',
    }

def calcola_saturazione_si(pop_5min: int, n_lavatrici_zona: int) -> dict:
    if n_lavatrici_zona == 0:
        return {'indice': 99999, 'label': 'Monopol', 'colore': '#10b981', 'n_lavatrici_zona': 0}
    indice = pop_5min // n_lavatrici_zona
    if   indice > 6000: label, colore = 'Optimalno',   '#10b981'
    elif indice > 3000: label, colore = 'Konkurencno', '#3b82f6'
    elif indice > 1500: label, colore = 'Nasiceno',    '#f59e0b'
    else:               label, colore = 'Prenasiceno', '#ef4444'
    return {'indice': indice, 'label': label, 'colore': colore, 'n_lavatrici_zona': n_lavatrici_zona}
