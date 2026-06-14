"""
services/ins_romania.py — BIOLavaTU LaundryPro
Dati demografici Romania per judet (INS 2021).
ISOLATO — zero dipendenze da file italiani.
"""
EUR_RON_RATE = 4.97

# Densità urbana per città principale di ogni judet (loc/km²)
# Molto più alta della densità judet — usata per calcolo popolazione isocrone
DENSITA_URBANA_RO = {
    'B':  8500,  # Bucuresti centro
    'CJ': 6800,  # Cluj-Napoca
    'TM': 5200,  # Timisoara
    'IS': 6200,  # Iasi
    'CT': 4800,  # Constanta
    'BV': 6500,  # Brasov
    'PH': 4200,  # Ploiesti
    'IF': 3800,  # Ilfov area
    'AG': 4500,  # Pitesti
    'BC': 4000,  # Bacau
    'BH': 4200,  # Oradea
    'SB': 4800,  # Sibiu
    'DJ': 4500,  # Craiova
    'GL': 5200,  # Galati
    'MM': 3800,  # Baia Mare
    'NT': 3500,  # Piatra Neamt
    'SV': 3200,  # Suceava
    'VS': 2800,  # Vaslui
    'AR': 3600,  # Arad
    'MS': 4000,  # Targu Mures
    'HD': 3200,  # Deva
    'AB': 3000,  # Alba Iulia
    'BN': 2800,  # Bistrita
    'SM': 3400,  # Satu Mare
    'VL': 3200,  # Ramnicu Valcea
}


def get_densita_urbana_ro(judet_cod: str, n_poi_zona: int = 0) -> float:
    """
    Stima densità urbana reale basata su:
    1. Densità urbana città principale del judet (molto più alta della media judet)
    2. Boost se ci sono molti POI vicini (proxy densità urbana reale)
    """
    base = DENSITA_URBANA_RO.get(judet_cod.upper() if judet_cod else '', 3000)
    # Se ci sono molti POI → siamo in zona densa → usiamo densità piena
    # Se pochi POI → periferia → riduciamo
    if n_poi_zona >= 30:   factor = 1.0   # centro città
    elif n_poi_zona >= 15: factor = 0.75  # zona semi-centrale
    elif n_poi_zona >= 5:  factor = 0.50  # periferia
    else:                   factor = 0.30  # zona rurale/suburbana
    return base * factor

JUDET_DATA = {
    'B':  {'nome':'Bucuresti',        'eta_media':39.8,'reddito_medio':52800,'densita':8247,'perc_stranieri':4.2,'pop_totale':1803425},
    'IF': {'nome':'Ilfov',            'eta_media':38.2,'reddito_medio':42000,'densita':352, 'perc_stranieri':2.8,'pop_totale':388738},
    'CJ': {'nome':'Cluj',             'eta_media':40.4,'reddito_medio':46800,'densita':119, 'perc_stranieri':3.2,'pop_totale':691000},
    'TM': {'nome':'Timis',            'eta_media':41.8,'reddito_medio':43200,'densita':87,  'perc_stranieri':3.8,'pop_totale':696000},
    'IS': {'nome':'Iasi',             'eta_media':38.6,'reddito_medio':31200,'densita':166, 'perc_stranieri':2.1,'pop_totale':772348},
    'CT': {'nome':'Constanta',        'eta_media':41.2,'reddito_medio':34800,'densita':101, 'perc_stranieri':1.8,'pop_totale':684000},
    'BV': {'nome':'Brasov',           'eta_media':41.6,'reddito_medio':40800,'densita':114, 'perc_stranieri':2.4,'pop_totale':623000},
    'PH': {'nome':'Prahova',          'eta_media':42.1,'reddito_medio':34200,'densita':179, 'perc_stranieri':0.8,'pop_totale':762886},
    'AG': {'nome':'Arges',            'eta_media':42.4,'reddito_medio':33600,'densita':115, 'perc_stranieri':0.5,'pop_totale':597175},
    'BC': {'nome':'Bacau',            'eta_media':41.2,'reddito_medio':28800,'densita':101, 'perc_stranieri':0.5,'pop_totale':616000},
    'BH': {'nome':'Bihor',            'eta_media':41.8,'reddito_medio':34800,'densita':80,  'perc_stranieri':1.2,'pop_totale':580000},
    'SB': {'nome':'Sibiu',            'eta_media':41.8,'reddito_medio':38400,'densita':79,  'perc_stranieri':2.8,'pop_totale':397000},
    'DJ': {'nome':'Dolj',             'eta_media':43.2,'reddito_medio':28800,'densita':98,  'perc_stranieri':0.4,'pop_totale':616000},
    'GL': {'nome':'Galati',           'eta_media':41.4,'reddito_medio':28800,'densita':144, 'perc_stranieri':0.8,'pop_totale':536000},
    'MM': {'nome':'Maramures',        'eta_media':41.4,'reddito_medio':28200,'densita':79,  'perc_stranieri':0.5,'pop_totale':456000},
    'NT': {'nome':'Neamt',            'eta_media':42.4,'reddito_medio':26400,'densita':92,  'perc_stranieri':0.4,'pop_totale':448000},
    'SV': {'nome':'Suceava',          'eta_media':40.2,'reddito_medio':27600,'densita':76,  'perc_stranieri':0.6,'pop_totale':634000},
    'VS': {'nome':'Vaslui',           'eta_media':41.6,'reddito_medio':22800,'densita':71,  'perc_stranieri':0.2,'pop_totale':388000},
    'AR': {'nome':'Arad',             'eta_media':42.4,'reddito_medio':36000,'densita':64,  'perc_stranieri':1.2,'pop_totale':436000},
    'MS': {'nome':'Mures',            'eta_media':42.2,'reddito_medio':32400,'densita':82,  'perc_stranieri':0.8,'pop_totale':526000},
    'HD': {'nome':'Hunedoara',        'eta_media':44.2,'reddito_medio':31200,'densita':57,  'perc_stranieri':0.6,'pop_totale':404000},
    'AB': {'nome':'Alba',             'eta_media':42.8,'reddito_medio':32400,'densita':57,  'perc_stranieri':0.6,'pop_totale':323000},
    'BN': {'nome':'Bistrita-Nasaud',  'eta_media':41.2,'reddito_medio':28200,'densita':58,  'perc_stranieri':0.4,'pop_totale':280000},
    'SM': {'nome':'Satu Mare',        'eta_media':41.6,'reddito_medio':28800,'densita':78,  'perc_stranieri':0.8,'pop_totale':338000},
    'VL': {'nome':'Valcea',           'eta_media':43.2,'reddito_medio':28800,'densita':73,  'perc_stranieri':0.3,'pop_totale':348000},
}

TARIFFE_DEFAULT_RO = {
    'lavaggio_std_ron': 20.0,
    'lavaggio_med_ron': 25.0,
    'lavaggio_grd_ron': 35.0,
    'asciugatura_ron':   5.0,
}

OCC_BASE_RO = 0.45


def get_demographic_data_ro(judet_cod: str, oras: str = '') -> dict:
    data = JUDET_DATA.get(judet_cod.upper() if judet_cod else '')
    if not data and oras:
        for cod, d in JUDET_DATA.items():
            if oras.lower() in d['nome'].lower() or d['nome'].lower() in oras.lower():
                data = d; break
    if not data:
        data = {'nome': oras or 'Romania','eta_media':42.0,'reddito_medio':30000,
                'densita':85,'perc_stranieri':0.8,'pop_totale':0}
    return {
        'eta_media':      data['eta_media'],
        'reddito_medio':  data['reddito_medio'],
        'reddito_eur':    round(data['reddito_medio'] / EUR_RON_RATE),
        'densita':        data['densita'],
        'perc_stranieri': data['perc_stranieri'],
        'pop_totale':     data.get('pop_totale', 0),
        'paese': 'RO', 'valuta': 'RON', 'fonte': 'INS Romania 2021',
    }


def get_market_assessment_ro(reddito_ron: float, densita: float) -> dict:
    score = 0
    if   densita > 3000: score += 30
    elif densita > 1000: score += 22
    elif densita > 300:  score += 14
    elif densita > 80:   score += 8
    else:                score += 2

    if   reddito_ron > 48000: score += 25
    elif reddito_ron > 36000: score += 20
    elif reddito_ron > 24000: score += 14
    elif reddito_ron > 18000: score += 8
    else:                      score += 3

    if densita > 2000: score += 20
    elif densita > 500: score += 14
    elif densita > 100: score += 7

    score = min(100, score)
    potenziale = ('alto' if reddito_ron > 36000 and densita > 500 else
                  'medio' if reddito_ron > 24000 else 'basso')
    if   score >= 70: label, colore = 'Excelent', '#10b981'
    elif score >= 55: label, colore = 'Bun',      '#3b82f6'
    elif score >= 35: label, colore = 'Mediu',    '#f59e0b'
    else:             label, colore = 'Slab',     '#ef4444'
    return {'score':score,'label':label,'colore':colore,'potenziale':potenziale,'paese':'RO'}


def get_f_citta_ro(pop: int) -> float:
    if   pop >= 1000000: return 1.00
    elif pop >= 300000:  return 0.85
    elif pop >= 150000:  return 0.75
    elif pop >= 50000:   return 0.65
    elif pop >= 20000:   return 0.55
    else:                return 0.45


def converti_ron_eur(ron: float) -> float:
    return round(ron / EUR_RON_RATE, 2)


def converti_eur_ron(eur: float) -> float:
    return round(eur * EUR_RON_RATE, 2)


def get_cambio_ron_live() -> float:
    try:
        import urllib.request as _ur, json as _j
        req = _ur.Request('https://api.frankfurter.app/latest?from=EUR&to=RON')
        with _ur.urlopen(req, timeout=3) as r:
            return float(_j.loads(r.read())['rates']['RON'])
    except Exception:
        return EUR_RON_RATE
