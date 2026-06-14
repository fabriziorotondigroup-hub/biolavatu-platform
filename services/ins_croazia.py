"""
services/ins_croazia.py — BIOLavaTU LaundryPro
Dati demografici Croazia per županija (contea) + motore analisi.
ISOLATO — zero dipendenze da altri mercati.
"""

EUR_HRK_RATE = 1.0  # Croazia usa EUR dal 01/01/2023

ZUPANIJA_DATA = {
    'GZ': {'nome': 'Grad Zagreb',         'pop': 806341,  'eta_media': 41.8, 'reddito_medio': 22800, 'densita_urbana': 6200, 'perc_stranieri': 3.2, 'citta': 'Zagreb'},
    'ZG': {'nome': 'Zagrebačka',          'pop': 317606,  'eta_media': 42.4, 'reddito_medio': 17400, 'densita_urbana': 3200, 'perc_stranieri': 1.1, 'citta': 'Velika Gorica'},
    'ST': {'nome': 'Splitsko-dalmatinska','pop': 454798,  'eta_media': 42.6, 'reddito_medio': 17800, 'densita_urbana': 4800, 'perc_stranieri': 2.8, 'citta': 'Split'},
    'RI': {'nome': 'Primorsko-goranska',  'pop': 264412,  'eta_media': 44.2, 'reddito_medio': 19200, 'densita_urbana': 4200, 'perc_stranieri': 2.4, 'citta': 'Rijeka'},
    'OS': {'nome': 'Osječko-baranjska',   'pop': 267783,  'eta_media': 43.8, 'reddito_medio': 14800, 'densita_urbana': 3400, 'perc_stranieri': 0.8, 'citta': 'Osijek'},
    'ZD': {'nome': 'Zadarska',            'pop': 170017,  'eta_media': 41.2, 'reddito_medio': 16200, 'densita_urbana': 3800, 'perc_stranieri': 2.1, 'citta': 'Zadar'},
    'SI': {'nome': 'Sisačko-moslavačka', 'pop': 152950,  'eta_media': 45.2, 'reddito_medio': 13600, 'densita_urbana': 2600, 'perc_stranieri': 0.5, 'citta': 'Sisak'},
    'KA': {'nome': 'Karlovačka',          'pop': 111541,  'eta_media': 45.8, 'reddito_medio': 14200, 'densita_urbana': 2400, 'perc_stranieri': 0.6, 'citta': 'Karlovac'},
    'VA': {'nome': 'Varaždinska',         'pop': 167225,  'eta_media': 43.6, 'reddito_medio': 16800, 'densita_urbana': 3200, 'perc_stranieri': 0.7, 'citta': 'Varaždin'},
    'DU': {'nome': 'Dubrovačko-neretvanska','pop': 122568,'eta_media': 42.8, 'reddito_medio': 18600, 'densita_urbana': 3600, 'perc_stranieri': 3.8, 'citta': 'Dubrovnik'},
    'IS': {'nome': 'Istarska',            'pop': 208055,  'eta_media': 43.4, 'reddito_medio': 20400, 'densita_urbana': 3800, 'perc_stranieri': 4.2, 'citta': 'Pula'},
    'SB': {'nome': 'Šibensko-kninska',    'pop': 104059,  'eta_media': 45.2, 'reddito_medio': 14800, 'densita_urbana': 2800, 'perc_stranieri': 1.2, 'citta': 'Šibenik'},
    'BB': {'nome': 'Bjelovarsko-bilogorska','pop': 101190,'eta_media': 46.2, 'reddito_medio': 13200, 'densita_urbana': 2200, 'perc_stranieri': 0.4, 'citta': 'Bjelovar'},
    'KK': {'nome': 'Koprivničko-križevačka','pop': 108622,'eta_media': 44.8, 'reddito_medio': 16400, 'densita_urbana': 2600, 'perc_stranieri': 0.5, 'citta': 'Koprivnica'},
    'MZ': {'nome': 'Međimurska',          'pop': 113804,  'eta_media': 41.8, 'reddito_medio': 17200, 'densita_urbana': 3000, 'perc_stranieri': 0.9, 'citta': 'Čakovec'},
    'VK': {'nome': 'Virovitičko-podravska','pop': 77175,  'eta_media': 47.2, 'reddito_medio': 12800, 'densita_urbana': 2000, 'perc_stranieri': 0.3, 'citta': 'Virovitica'},
    'PZ': {'nome': 'Požeško-slavonska',   'pop': 68688,   'eta_media': 46.8, 'reddito_medio': 13000, 'densita_urbana': 2000, 'perc_stranieri': 0.4, 'citta': 'Požega'},
    'BR': {'nome': 'Brodsko-posavska',    'pop': 143975,  'eta_media': 43.8, 'reddito_medio': 13400, 'densita_urbana': 2400, 'perc_stranieri': 0.4, 'citta': 'Slavonski Brod'},
    'VU': {'nome': 'Vukovarsko-srijemska','pop': 161882,  'eta_media': 43.2, 'reddito_medio': 13000, 'densita_urbana': 2200, 'perc_stranieri': 0.5, 'citta': 'Vukovar'},
    'LI': {'nome': 'Ličko-senjska',       'pop': 46006,   'eta_media': 48.2, 'reddito_medio': 14000, 'densita_urbana': 1800, 'perc_stranieri': 0.4, 'citta': 'Gospić'},
}

ABITATIVI = {
    'GZ': {'perc_affittuari': 28, 'perc_appartamenti': 72, 'mq_medi': 68, 'perc_senza_lavatrice': 5,  'studenti_uni_1000': 88,  'tasso_disoccupazione': 4.2},
    'ST': {'perc_affittuari': 22, 'perc_appartamenti': 65, 'mq_medi': 72, 'perc_senza_lavatrice': 6,  'studenti_uni_1000': 55,  'tasso_disoccupazione': 8.4},
    'RI': {'perc_affittuari': 20, 'perc_appartamenti': 68, 'mq_medi': 70, 'perc_senza_lavatrice': 5,  'studenti_uni_1000': 42,  'tasso_disoccupazione': 6.2},
    'IS': {'perc_affittuari': 18, 'perc_appartamenti': 58, 'mq_medi': 74, 'perc_senza_lavatrice': 5,  'studenti_uni_1000': 28,  'tasso_disoccupazione': 5.8},
    'DU': {'perc_affittuari': 24, 'perc_appartamenti': 60, 'mq_medi': 70, 'perc_senza_lavatrice': 6,  'studenti_uni_1000': 22,  'tasso_disoccupazione': 7.2},
    'OS': {'perc_affittuari': 16, 'perc_appartamenti': 62, 'mq_medi': 74, 'perc_senza_lavatrice': 7,  'studenti_uni_1000': 48,  'tasso_disoccupazione': 12.4},
    '_default': {'perc_affittuari': 16, 'perc_appartamenti': 58, 'mq_medi': 72, 'perc_senza_lavatrice': 7, 'studenti_uni_1000': 25, 'tasso_disoccupazione': 8.5},
}

TARIFFE_DEFAULT_HR = {
    'lavaggio_std_eur': 4.5,
    'lavaggio_med_eur': 6.0,
    'lavaggio_grd_eur': 8.5,
    'asciugatura_eur':  2.5,
}

OCC_BASE_HR  = 0.40
EUR_HRK_RATE = 1.0  # già in EUR


def get_demographic_data_hr(zupanija_cod: str, grad: str = '') -> dict:
    data = ZUPANIJA_DATA.get(zupanija_cod.upper() if zupanija_cod else '')
    if not data and grad:
        for cod, d in ZUPANIJA_DATA.items():
            if grad.lower() in d['nome'].lower() or d['nome'].lower() in grad.lower() \
               or grad.lower() in d.get('citta', '').lower():
                data = d; break
    if not data:
        data = {'nome': grad or 'Hrvatska', 'pop': 0, 'eta_media': 43.0,
                'reddito_medio': 16000, 'densita_urbana': 2800, 'perc_stranieri': 1.5, 'citta': grad or ''}
    abit = ABITATIVI.get(zupanija_cod.upper() if zupanija_cod else '', ABITATIVI['_default'])
    return {
        'eta_media':             data['eta_media'],
        'reddito_medio':         data['reddito_medio'],   # EUR/anno (già in EUR)
        'reddito_eur':           data['reddito_medio'],
        'densita':               data.get('densita_urbana', 2800),
        'perc_stranieri':        data['perc_stranieri'],
        'pop_totale':            data['pop'],
        'perc_affittuari':       abit['perc_affittuari'],
        'perc_appartamenti':     abit['perc_appartamenti'],
        'mq_medi':               abit['mq_medi'],
        'perc_senza_lavatrice':  abit['perc_senza_lavatrice'],
        'studenti_uni_1000':     abit['studenti_uni_1000'],
        'tasso_disoccupazione':  abit['tasso_disoccupazione'],
        'paese': 'HR', 'valuta': 'EUR', 'fonte': 'DZS Croazia 2023',
    }


def get_densita_urbana_hr(zupanija_cod: str, n_poi_zona: int = 0) -> float:
    d = ZUPANIJA_DATA.get(zupanija_cod.upper() if zupanija_cod else {})
    base = d.get('densita_urbana', 2800) if d else 2800
    if   n_poi_zona >= 30: factor = 1.00
    elif n_poi_zona >= 15: factor = 0.75
    elif n_poi_zona >= 5:  factor = 0.50
    else:                  factor = 0.30
    return base * factor


def get_market_assessment_hr(reddito_eur: float, densita: float) -> dict:
    score = 0
    if   densita > 4000: score += 30
    elif densita > 2000: score += 22
    elif densita > 500:  score += 14
    else:                score += 5
    if   reddito_eur > 20000: score += 25
    elif reddito_eur > 16000: score += 18
    elif reddito_eur > 12000: score += 11
    else:                      score += 5
    if densita > 3000: score += 20
    elif densita > 1000: score += 12
    score = min(100, score)
    potenziale = ('alto' if reddito_eur > 18000 and densita > 2000 else
                  'medio' if reddito_eur > 14000 else 'basso')
    if   score >= 70: label, colore = 'Izvrsno',  '#10b981'
    elif score >= 55: label, colore = 'Dobro',    '#3b82f6'
    elif score >= 35: label, colore = 'Srednje',  '#f59e0b'
    else:             label, colore = 'Slabo',    '#ef4444'
    return {'score': score, 'label': label, 'colore': colore, 'potenziale': potenziale, 'paese': 'HR'}


def get_f_grad_hr(pop: int) -> float:
    if   pop >= 500000: return 1.00
    elif pop >= 200000: return 0.88
    elif pop >= 100000: return 0.78
    elif pop >= 50000:  return 0.68
    elif pop >= 20000:  return 0.58
    else:               return 0.48


def calcola_potenziale_lavaggi_hr(pop_5min, perc_affittuari, perc_senza_lavatrice,
                                   studenti_uni_1000, perc_stranieri, n_hotel_bb,
                                   frequenza_lavaggi_mese=2.4):
    famiglie = pop_5min // 2.7
    seg_senza_lav  = famiglie * (perc_senza_lavatrice / 100)
    seg_affittuari = famiglie * (perc_affittuari / 100) * 0.14
    seg_studenti   = pop_5min * (studenti_uni_1000 / 1000) * 0.3 * 0.42
    seg_immigrati  = pop_5min * (perc_stranieri / 100) * 0.28
    seg_pro        = n_hotel_bb * 10  # Croazia forte turismo
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


def calcola_costi_operativi_hr(n_lavatrici, n_asciugatrici, cicli_giorno_lav=6, cicli_giorno_asc=8, costi_override=None):
    C = {'kwh_eur': 0.18, 'mc_acqua_eur': 3.20, 'mc_fognatura_eur': 2.40, 'internet_eur': 25.0, 'assicurazione_eur': 60.0}
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


def converti_eur_eur(v): return round(v, 2)  # già in EUR

def get_cambio_hr_live() -> float:
    return 1.0  # Croazia è in Eurozona dal 2023
