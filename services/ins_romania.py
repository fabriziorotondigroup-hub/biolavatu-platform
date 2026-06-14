"""
services/ins_romania.py — BIOLavaTU LaundryPro
Dati demografici Romania per judet (INS 2021) + motore analisi 11 parametri.
ISOLATO — zero dipendenze da file italiani.
"""

EUR_RON_RATE = 4.97

# ── Dati judet INS 2021 ───────────────────────────────────────────────────────
JUDET_DATA = {
    'B':  {'nome':'Bucuresti',        'pop':1803425,'eta_media':39.8,'reddito_medio':52800,'densita_judet':8247,'perc_stranieri':4.2},
    'IF': {'nome':'Ilfov',            'pop':388738, 'eta_media':38.2,'reddito_medio':42000,'densita_judet':352, 'perc_stranieri':2.8},
    'CJ': {'nome':'Cluj',             'pop':691000, 'eta_media':40.4,'reddito_medio':46800,'densita_judet':119, 'perc_stranieri':3.2},
    'TM': {'nome':'Timis',            'pop':696000, 'eta_media':41.8,'reddito_medio':43200,'densita_judet':87,  'perc_stranieri':3.8},
    'IS': {'nome':'Iasi',             'pop':772348, 'eta_media':38.6,'reddito_medio':31200,'densita_judet':166, 'perc_stranieri':2.1},
    'CT': {'nome':'Constanta',        'pop':684000, 'eta_media':41.2,'reddito_medio':34800,'densita_judet':101, 'perc_stranieri':1.8},
    'BV': {'nome':'Brasov',           'pop':623000, 'eta_media':41.6,'reddito_medio':40800,'densita_judet':114, 'perc_stranieri':2.4},
    'PH': {'nome':'Prahova',          'pop':762886, 'eta_media':42.1,'reddito_medio':34200,'densita_judet':179, 'perc_stranieri':0.8},
    'AG': {'nome':'Arges',            'pop':597175, 'eta_media':42.4,'reddito_medio':33600,'densita_judet':115, 'perc_stranieri':0.5},
    'BC': {'nome':'Bacau',            'pop':616000, 'eta_media':41.2,'reddito_medio':28800,'densita_judet':101, 'perc_stranieri':0.5},
    'BH': {'nome':'Bihor',            'pop':580000, 'eta_media':41.8,'reddito_medio':34800,'densita_judet':80,  'perc_stranieri':1.2},
    'SB': {'nome':'Sibiu',            'pop':397000, 'eta_media':41.8,'reddito_medio':38400,'densita_judet':79,  'perc_stranieri':2.8},
    'DJ': {'nome':'Dolj',             'pop':616000, 'eta_media':43.2,'reddito_medio':28800,'densita_judet':98,  'perc_stranieri':0.4},
    'GL': {'nome':'Galati',           'pop':536000, 'eta_media':41.4,'reddito_medio':28800,'densita_judet':144, 'perc_stranieri':0.8},
    'MM': {'nome':'Maramures',        'pop':456000, 'eta_media':41.4,'reddito_medio':28200,'densita_judet':79,  'perc_stranieri':0.5},
    'NT': {'nome':'Neamt',            'pop':448000, 'eta_media':42.4,'reddito_medio':26400,'densita_judet':92,  'perc_stranieri':0.4},
    'SV': {'nome':'Suceava',          'pop':634000, 'eta_media':40.2,'reddito_medio':27600,'densita_judet':76,  'perc_stranieri':0.6},
    'VS': {'nome':'Vaslui',           'pop':388000, 'eta_media':41.6,'reddito_medio':22800,'densita_judet':71,  'perc_stranieri':0.2},
    'AR': {'nome':'Arad',             'pop':436000, 'eta_media':42.4,'reddito_medio':36000,'densita_judet':64,  'perc_stranieri':1.2},
    'MS': {'nome':'Mures',            'pop':526000, 'eta_media':42.2,'reddito_medio':32400,'densita_judet':82,  'perc_stranieri':0.8},
    'HD': {'nome':'Hunedoara',        'pop':404000, 'eta_media':44.2,'reddito_medio':31200,'densita_judet':57,  'perc_stranieri':0.6},
    'AB': {'nome':'Alba',             'pop':323000, 'eta_media':42.8,'reddito_medio':32400,'densita_judet':57,  'perc_stranieri':0.6},
    'BN': {'nome':'Bistrita-Nasaud',  'pop':280000, 'eta_media':41.2,'reddito_medio':28200,'densita_judet':58,  'perc_stranieri':0.4},
    'SM': {'nome':'Satu Mare',        'pop':338000, 'eta_media':41.6,'reddito_medio':28800,'densita_judet':78,  'perc_stranieri':0.8},
    'VL': {'nome':'Valcea',           'pop':348000, 'eta_media':43.2,'reddito_medio':28800,'densita_judet':73,  'perc_stranieri':0.3},
}

# ── Densità urbana città principale (molto più alta della media judet) ────────
DENSITA_URBANA_RO = {
    'B':8500,'IF':3800,'CJ':6800,'TM':5200,'IS':6200,'CT':4800,'BV':6500,
    'PH':4200,'AG':4500,'BC':4000,'BH':4200,'SB':4800,'DJ':4500,'GL':5200,
    'MM':3800,'NT':3500,'SV':3200,'VS':2800,'AR':3600,'MS':4000,'HD':3200,
    'AB':3000,'BN':2800,'SM':3400,'VL':3200,
}

# ── Dati abitativi per judet (INS 2021 + stime) ───────────────────────────────
# perc_affittuari: % famiglie che affittano
# perc_appartamenti: % abitazioni in condominio/palazzo
# mq_medi: superficie media appartamento in mq
# perc_senza_lavatrice: % famiglie senza lavatrice (stimato)
# studenti_uni_1000: studenti universitari per 1000 abitanti
# tasso_disoccupazione: %
ABITATIVI = {
    'B':  {'perc_affittuari':38,'perc_appartamenti':92,'mq_medi':52,'perc_senza_lavatrice':12,'studenti_uni_1000':85,'tasso_disoccupazione':2.8},
    'CJ': {'perc_affittuari':42,'perc_appartamenti':78,'mq_medi':55,'perc_senza_lavatrice':10,'studenti_uni_1000':120,'tasso_disoccupazione':2.2},
    'TM': {'perc_affittuari':35,'perc_appartamenti':75,'mq_medi':57,'perc_senza_lavatrice':9, 'studenti_uni_1000':65, 'tasso_disoccupazione':2.5},
    'IS': {'perc_affittuari':40,'perc_appartamenti':72,'mq_medi':50,'perc_senza_lavatrice':14,'studenti_uni_1000':110,'tasso_disoccupazione':3.8},
    'CT': {'perc_affittuari':30,'perc_appartamenti':68,'mq_medi':54,'perc_senza_lavatrice':11,'studenti_uni_1000':45, 'tasso_disoccupazione':4.2},
    'BV': {'perc_affittuari':32,'perc_appartamenti':70,'mq_medi':56,'perc_senza_lavatrice':10,'studenti_uni_1000':55, 'tasso_disoccupazione':3.1},
    'SB': {'perc_affittuari':28,'perc_appartamenti':65,'mq_medi':58,'perc_senza_lavatrice':9, 'studenti_uni_1000':40, 'tasso_disoccupazione':2.8},
    'IF': {'perc_affittuari':35,'perc_appartamenti':60,'mq_medi':62,'perc_senza_lavatrice':8, 'studenti_uni_1000':15, 'tasso_disoccupazione':2.1},
    '_default': {'perc_affittuari':22,'perc_appartamenti':55,'mq_medi':62,'perc_senza_lavatrice':15,'studenti_uni_1000':25,'tasso_disoccupazione':5.5},
}

# ── Costi utenze default Romania ──────────────────────────────────────────────
COSTI_UTENZE_DEFAULT_RO = {
    'kwh_ron':         0.95,   # RON/kWh energia elettrica
    'mc_acqua_ron':    4.20,   # RON/mc acqua
    'mc_fognatura_ron':2.80,   # RON/mc fognatura
    'mc_gas_ron':      2.10,   # RON/mc gas
    'internet_ron':   60.0,    # RON/mese
    'assicurazione_ron':150.0, # RON/mese
}

# ── Prezzi lavaggio default Romania ──────────────────────────────────────────
PREZZI_DEFAULT_RO = {
    'lav_8kg_ron':    20.0,
    'lav_12kg_ron':   25.0,
    'lav_18kg_ron':   35.0,
    'asc_10min_ron':   5.0,
    'detersivo_ron':   3.0,
}

TARIFFE_DEFAULT_RO = {
    'lavaggio_std_ron': 20.0,
    'lavaggio_med_ron': 25.0,
    'lavaggio_grd_ron': 35.0,
    'asciugatura_ron':   5.0,
}

OCC_BASE_RO  = 0.45
EUR_RON_RATE = 4.97


# ── Funzioni dati ─────────────────────────────────────────────────────────────

def get_demographic_data_ro(judet_cod: str, oras: str = '') -> dict:
    data = JUDET_DATA.get(judet_cod.upper() if judet_cod else '')
    if not data and oras:
        for cod, d in JUDET_DATA.items():
            if oras.lower() in d['nome'].lower() or d['nome'].lower() in oras.lower():
                data = d; break
    if not data:
        data = {'nome':oras or 'Romania','pop':0,'eta_media':42.0,
                'reddito_medio':30000,'densita_judet':85,'perc_stranieri':0.8}
    abit = ABITATIVI.get(judet_cod.upper() if judet_cod else '', ABITATIVI['_default'])
    return {
        'eta_media':          data['eta_media'],
        'reddito_medio':      data['reddito_medio'],
        'reddito_eur':        round(data['reddito_medio'] / EUR_RON_RATE),
        'densita':            data['densita_judet'],
        'perc_stranieri':     data['perc_stranieri'],
        'pop_totale':         data['pop'],
        'perc_affittuari':    abit['perc_affittuari'],
        'perc_appartamenti':  abit['perc_appartamenti'],
        'mq_medi':            abit['mq_medi'],
        'perc_senza_lavatrice': abit['perc_senza_lavatrice'],
        'studenti_uni_1000':  abit['studenti_uni_1000'],
        'tasso_disoccupazione': abit['tasso_disoccupazione'],
        'paese': 'RO', 'valuta': 'RON', 'fonte': 'INS Romania 2021',
    }


def get_densita_urbana_ro(judet_cod: str, n_poi_zona: int = 0) -> float:
    base = DENSITA_URBANA_RO.get(judet_cod.upper() if judet_cod else '', 3000)
    if   n_poi_zona >= 30: factor = 1.00
    elif n_poi_zona >= 15: factor = 0.75
    elif n_poi_zona >= 5:  factor = 0.50
    else:                  factor = 0.30
    return base * factor


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


# ── MOTORE ANALISI 11 PARAMETRI ───────────────────────────────────────────────

def calcola_potenziale_lavaggi_ro(
    pop_5min: int,
    perc_affittuari: float,
    perc_senza_lavatrice: float,
    studenti_uni_1000: float,
    perc_stranieri: float,
    n_hotel_bb: int,
    frequenza_lavaggi_mese: float = 2.5,
) -> dict:
    """
    Formula lavaggi/mese basata sui parametri reali della zona.
    Segmenti clienti:
    - Residenti senza lavatrice
    - Affittuari (alta mobilità)
    - Studenti universitari
    - Immigrati (spesso senza lavatrice)
    - Clienti professionali (B&B, hotel)
    """
    famiglie_5min = pop_5min // 2.8  # media 2.8 persone/famiglia Romania

    # Segmento 1: residenti senza lavatrice
    seg_senza_lav = famiglie_5min * (perc_senza_lavatrice / 100)

    # Segmento 2: affittuari (più propensi a usare lavanderie)
    seg_affittuari = famiglie_5min * (perc_affittuari / 100) * 0.15  # 15% degli affittuari

    # Segmento 3: studenti
    studenti_zona = pop_5min * (studenti_uni_1000 / 1000) * 0.3  # 30% nella zona pedonale
    seg_studenti  = studenti_zona * 0.40  # 40% usano lavanderie

    # Segmento 4: immigrati (alta propensione)
    seg_immigrati = pop_5min * (perc_stranieri / 100) * 0.25

    # Segmento 5: clienti professionali (B&B, hotel)
    seg_pro = n_hotel_bb * 8  # stima 8 lavaggi/mese per struttura

    clienti_totali = seg_senza_lav + seg_affittuari + seg_studenti + seg_immigrati + seg_pro
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


def calcola_saturazione_ro(pop_5min: int, n_lavatrici_zona: int) -> dict:
    """
    Indice saturazione = abitanti / lavatrici self-service nella zona.
    < 3000 ab/lavatrice = zona satura
    3000-6000 = zona competitiva
    > 6000 = zona interessante
    """
    if n_lavatrici_zona == 0:
        indice = 99999
        label  = 'Monopolio'
        colore = '#10b981'
    else:
        indice = pop_5min // n_lavatrici_zona
        if   indice > 6000: label, colore = 'Ottimale',    '#10b981'
        elif indice > 3000: label, colore = 'Competitiva', '#3b82f6'
        elif indice > 1500: label, colore = 'Satura',      '#f59e0b'
        else:               label, colore = 'Molto satura','#ef4444'
    return {'indice': indice, 'label': label, 'colore': colore,
            'n_lavatrici_zona': n_lavatrici_zona}


def calcola_incasso_da_lavaggi_ro(
    lavaggi_quota: int,
    t_lav_medio_ron: float,
    perc_asciugatura: float = 60,
    t_asc_ron: float = 5.0,
) -> float:
    """Incasso mensile da quota lavaggi."""
    incasso_lav = lavaggi_quota * t_lav_medio_ron
    incasso_asc = lavaggi_quota * (perc_asciugatura / 100) * t_asc_ron
    return round(incasso_lav + incasso_asc)


def calcola_affitto_max_ro(fatturato_ron: float) -> dict:
    """Affitto massimo sostenibile = 10-12% del fatturato."""
    return {
        'affitto_max_10pct': round(fatturato_ron * 0.10),
        'affitto_max_12pct': round(fatturato_ron * 0.12),
        'regola': '10-12% del fatturato previsto',
    }


def calcola_costi_operativi_ro(
    n_lavatrici: int,
    n_asciugatrici: int,
    cicli_giorno_lav: float = 6,
    cicli_giorno_asc: float = 8,
    costi_override: dict = None,
) -> dict:
    """Stima costi operativi mensili in RON."""
    c = {**COSTI_UTENZE_DEFAULT_RO, **(costi_override or {})}
    giorni = 30

    # Consumo energia (kWh)
    kwh_lav = n_lavatrici * cicli_giorno_lav * 1.2 * giorni       # 1.2 kWh/ciclo lavatrice
    kwh_asc = n_asciugatrici * cicli_giorno_asc * 3.5 * giorni    # 3.5 kWh/ciclo asciugatrice
    costo_energia = (kwh_lav + kwh_asc) * c['kwh_ron']

    # Consumo acqua (mc)
    mc_acqua = n_lavatrici * cicli_giorno_lav * 0.065 * giorni    # 65 litri/ciclo
    costo_acqua = mc_acqua * (c['mc_acqua_ron'] + c['mc_fognatura_ron'])

    # Gas (se presente)
    mc_gas = n_lavatrici * cicli_giorno_lav * 0.02 * giorni
    costo_gas = mc_gas * c['mc_gas_ron']

    totale_utenze = costo_energia + costo_acqua + costo_gas + \
                    c['internet_ron'] + c['assicurazione_ron']

    return {
        'energia_ron':    round(costo_energia),
        'acqua_ron':      round(costo_acqua),
        'gas_ron':        round(costo_gas),
        'internet_ron':   round(c['internet_ron']),
        'assicurazione_ron': round(c['assicurazione_ron']),
        'totale_utenze_ron': round(totale_utenze),
        'kwh_mese':       round(kwh_lav + kwh_asc),
        'mc_acqua_mese':  round(mc_acqua, 1),
    }


# ── Utilities ─────────────────────────────────────────────────────────────────

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
