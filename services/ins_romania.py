"""
services/ins_romania.py — BIOLavaTU LaundryPro
Dati demografici Romania per judet (contee) e principali città.
Fonte: INS Romania (Institutul Național de Statistică) — Recensământul 2021
+ stime Google Maps proxy dove INS non disponibile.

Struttura identica a services/istat.py per compatibilità con il motore esistente.
Valuta: RON (leu rumeno). Cambio EUR/RON aggiornato automaticamente via API.
"""

# Tasso cambio EUR/RON di riferimento (aggiornato periodicamente)
EUR_RON_RATE = 4.97  # Banca Națională a României — giugno 2026

# ─── DATI JUDET (contee) INS 2021 ────────────────────────────────────────────
# eta_media: anni
# reddito_medio: RON/anno (salario mediu net)
# densita: ab/km²
# perc_stranieri: % popolazione straniera
# pop_totale: popolazione residente

JUDET_DATA = {
    # MUNTENIA + ILFOV
    'B':  {'nome': 'București',        'eta_media': 39.8, 'reddito_medio': 52800, 'densita': 8247, 'perc_stranieri': 4.2,  'pop_totale': 1803425},
    'IF': {'nome': 'Ilfov',            'eta_media': 38.2, 'reddito_medio': 42000, 'densita': 352,  'perc_stranieri': 2.8,  'pop_totale': 388738},
    'PH': {'nome': 'Prahova',          'eta_media': 42.1, 'reddito_medio': 34200, 'densita': 179,  'perc_stranieri': 0.8,  'pop_totale': 762886},
    'DB': {'nome': 'Dâmbovița',        'eta_media': 41.8, 'reddito_medio': 31800, 'densita': 172,  'perc_stranieri': 0.4,  'pop_totale': 494597},
    'AG': {'nome': 'Argeș',            'eta_media': 42.4, 'reddito_medio': 33600, 'densita': 115,  'perc_stranieri': 0.5,  'pop_totale': 597175},
    'CL': {'nome': 'Călărași',         'eta_media': 43.2, 'reddito_medio': 26400, 'densita': 72,   'perc_stranieri': 0.3,  'pop_totale': 282800},
    'GR': {'nome': 'Giurgiu',          'eta_media': 43.8, 'reddito_medio': 25800, 'densita': 96,   'perc_stranieri': 0.2,  'pop_totale': 253000},
    'IL': {'nome': 'Ialomița',         'eta_media': 43.5, 'reddito_medio': 26100, 'densita': 57,   'perc_stranieri': 0.3,  'pop_totale': 261000},
    'TL': {'nome': 'Teleorman',        'eta_media': 45.1, 'reddito_medio': 24600, 'densita': 66,   'perc_stranieri': 0.2,  'pop_totale': 330000},
    # MOLDOVA
    'IS': {'nome': 'Iași',             'eta_media': 38.6, 'reddito_medio': 31200, 'densita': 166,  'perc_stranieri': 2.1,  'pop_totale': 772348},
    'BC': {'nome': 'Bacău',            'eta_media': 41.2, 'reddito_medio': 28800, 'densita': 101,  'perc_stranieri': 0.5,  'pop_totale': 616000},
    'BT': {'nome': 'Botoșani',         'eta_media': 41.8, 'reddito_medio': 24600, 'densita': 94,   'perc_stranieri': 0.3,  'pop_totale': 412000},
    'NT': {'nome': 'Neamț',            'eta_media': 42.4, 'reddito_medio': 26400, 'densita': 92,   'perc_stranieri': 0.4,  'pop_totale': 448000},
    'SV': {'nome': 'Suceava',          'eta_media': 40.2, 'reddito_medio': 27600, 'densita': 76,   'perc_stranieri': 0.6,  'pop_totale': 634000},
    'VS': {'nome': 'Vaslui',           'eta_media': 41.6, 'reddito_medio': 22800, 'densita': 71,   'perc_stranieri': 0.2,  'pop_totale': 388000},
    'VN': {'nome': 'Vrancea',          'eta_media': 42.8, 'reddito_medio': 26400, 'densita': 75,   'perc_stranieri': 0.3,  'pop_totale': 320000},
    'GL': {'nome': 'Galați',           'eta_media': 41.4, 'reddito_medio': 28800, 'densita': 144,  'perc_stranieri': 0.8,  'pop_totale': 536000},
    'BR': {'nome': 'Brăila',           'eta_media': 43.6, 'reddito_medio': 27600, 'densita': 85,   'perc_stranieri': 0.4,  'pop_totale': 291000},
    # DOBROGEA
    'CT': {'nome': 'Constanța',        'eta_media': 41.2, 'reddito_medio': 34800, 'densita': 101,  'perc_stranieri': 1.8,  'pop_totale': 684000},
    'TL2': {'nome': 'Tulcea',          'eta_media': 43.8, 'reddito_medio': 27600, 'densita': 30,   'perc_stranieri': 0.6,  'pop_totale': 210000},
    # OLTENIA
    'DJ': {'nome': 'Dolj',             'eta_media': 43.2, 'reddito_medio': 28800, 'densita': 98,   'perc_stranieri': 0.4,  'pop_totale': 616000},
    'GJ': {'nome': 'Gorj',             'eta_media': 43.8, 'reddito_medio': 30000, 'densita': 67,   'perc_stranieri': 0.3,  'pop_totale': 322000},
    'MH': {'nome': 'Mehedinți',        'eta_media': 45.2, 'reddito_medio': 25200, 'densita': 60,   'perc_stranieri': 0.2,  'pop_totale': 252000},
    'OT': {'nome': 'Olt',              'eta_media': 44.1, 'reddito_medio': 25800, 'densita': 78,   'perc_stranieri': 0.2,  'pop_totale': 396000},
    'VL': {'nome': 'Vâlcea',           'eta_media': 43.4, 'reddito_medio': 28200, 'densita': 71,   'perc_stranieri': 0.3,  'pop_totale': 360000},
    # BANAT + VEST
    'TM': {'nome': 'Timiș',            'eta_media': 41.8, 'reddito_medio': 43200, 'densita': 87,   'perc_stranieri': 3.8,  'pop_totale': 696000},
    'AR': {'nome': 'Arad',             'eta_media': 42.4, 'reddito_medio': 36000, 'densita': 64,   'perc_stranieri': 1.2,  'pop_totale': 436000},
    'CS': {'nome': 'Caraș-Severin',    'eta_media': 44.8, 'reddito_medio': 28800, 'densita': 31,   'perc_stranieri': 0.5,  'pop_totale': 268000},
    'HD': {'nome': 'Hunedoara',        'eta_media': 44.2, 'reddito_medio': 31200, 'densita': 57,   'perc_stranieri': 0.6,  'pop_totale': 404000},
    # TRANSILVANIA
    'CJ': {'nome': 'Cluj',             'eta_media': 40.4, 'reddito_medio': 46800, 'densita': 119,  'perc_stranieri': 3.2,  'pop_totale': 691000},
    'BV': {'nome': 'Brașov',           'eta_media': 41.6, 'reddito_medio': 40800, 'densita': 114,  'perc_stranieri': 2.4,  'pop_totale': 623000},
    'SB': {'nome': 'Sibiu',            'eta_media': 41.8, 'reddito_medio': 38400, 'densita': 79,   'perc_stranieri': 2.8,  'pop_totale': 397000},
    'MS': {'nome': 'Mureș',            'eta_media': 42.2, 'reddito_medio': 32400, 'densita': 82,   'perc_stranieri': 0.8,  'pop_totale': 526000},
    'AB': {'nome': 'Alba',             'eta_media': 42.8, 'reddito_medio': 32400, 'densita': 57,   'perc_stranieri': 0.6,  'pop_totale': 323000},
    'HR': {'nome': 'Harghita',         'eta_media': 42.6, 'reddito_medio': 28800, 'densita': 46,   'perc_stranieri': 0.4,  'pop_totale': 299000},
    'CV': {'nome': 'Covasna',          'eta_media': 42.4, 'reddito_medio': 29400, 'densita': 56,   'perc_stranieri': 0.3,  'pop_totale': 194000},
    # NORD-VEST
    'BH': {'nome': 'Bihor',            'eta_media': 41.8, 'reddito_medio': 34800, 'densita': 80,   'perc_stranieri': 1.2,  'pop_totale': 580000},
    'BN': {'nome': 'Bistrița-Năsăud',  'eta_media': 41.2, 'reddito_medio': 28200, 'densita': 58,   'perc_stranieri': 0.4,  'pop_totale': 280000},
    'CJ2': {'nome': 'Sălaj',           'eta_media': 43.2, 'reddito_medio': 26400, 'densita': 57,   'perc_stranieri': 0.3,  'pop_totale': 216000},
    'SM': {'nome': 'Satu Mare',        'eta_media': 41.6, 'reddito_medio': 28800, 'densita': 78,   'perc_stranieri': 0.8,  'pop_totale': 338000},
    'MM': {'nome': 'Maramureș',        'eta_media': 41.4, 'reddito_medio': 28200, 'densita': 79,   'perc_stranieri': 0.5,  'pop_totale': 456000},
}

# ─── BENCHMARK REALI (da aggiornare con dati BIOLavaTU Romania) ──────────────
# Al momento non disponibili — usiamo stime conservative
# Struttura identica a benchmark Italia per compatibilità con services/investitore.py
BENCHMARKS_RO = [
    {
        'nome':              'București sector 2 (stima)',
        'tipo':              'monopolio_grande_citta',
        'incasso_ron':       28000,   # RON/mese stimato (~€5.600)
        'incasso_eur':       5635,
        'n_lavatrici':       6,
        'n_asciugatrici':    4,
        'concorrenti_500m':  0,
        'concorrenti_1km':   1,
        'densita':           8247,
        'reddito_ron':       52800,
        'occupazione':       0.45,    # base conservativa — da aggiornare
        'tipo_zona':         'residenziale',
        'note':              'Stima — nessun dato reale disponibile. Da calibrare.',
        'calibrato':         False,
    },
]

# ─── TARIFFE MEDIE ROMANIA (Google Maps + survey mercato 2024) ───────────────
TARIFFE_DEFAULT_RO = {
    'lavaggio_std_ron':   20.0,   # RON (~€4) — lavatrice 8kg
    'lavaggio_med_ron':   25.0,   # RON (~€5) — lavatrice 13kg
    'lavaggio_grd_ron':   35.0,   # RON (~€7) — lavatrice 23kg
    'asciugatura_ron':     5.0,   # RON (~€1) / ciclo
}

# ─── OCCUPAZIONE BASE — calibrazione conservativa per Romania ─────────────────
# In attesa di benchmark reali, usiamo coefficienti più bassi dell'Italia:
# - Mercato meno maturo
# - Abitudine culturale diversa (più lavaggio in casa)
# - Prezzi più bassi = volumi necessariamente maggiori per pareggio
OCC_BASE_RO = {
    # (concorrenti_500m, concorrenti_1km): occupazione_base
    (5, 0):  0.08,   # zona satura
    (4, 0):  0.20,   # alta concorrenza
    (3, 0):  0.28,
    (2, 0):  0.35,
    (1, 0):  0.42,
    (0, 4):  0.48,
    (0, 2):  0.52,
    (0, 1):  0.55,
    (0, 0):  0.45,   # monopolio — conservativo Romania
}

# ─── FATTORE CITTÀ ROMANIA ────────────────────────────────────────────────────
def get_f_citta_ro(pop_comune: int) -> float:
    """Fattore correttivo dimensione città per mercato rumeno."""
    if   pop_comune >= 1000000: return 1.00  # București
    elif pop_comune >= 300000:  return 0.85  # Cluj, Timișoara, Iași
    elif pop_comune >= 150000:  return 0.75  # Brașov, Constanța, Galați
    elif pop_comune >= 50000:   return 0.65  # città medie
    elif pop_comune >= 20000:   return 0.55  # comuni grandi
    else:                        return 0.45  # piccoli comuni

# ─── FUNZIONE PRINCIPALE (compatibile con get_demographic_data ISTAT) ─────────
def get_demographic_data_ro(judet_cod: str, oras: str = '') -> dict:
    """
    Ritorna dati demografici per un judet rumeno.
    Compatibile con la struttura di get_demographic_data() di istat.py.
    """
    # Cerca per codice judet
    data = JUDET_DATA.get(judet_cod.upper())

    # Fallback: cerca per nome città
    if not data and oras:
        oras_lower = oras.lower()
        for cod, d in JUDET_DATA.items():
            if oras_lower in d['nome'].lower() or d['nome'].lower() in oras_lower:
                data = d
                break

    # Default Romania se non trovato
    if not data:
        data = {
            'nome':            oras or 'Romania',
            'eta_media':       42.0,
            'reddito_medio':   30000,  # RON/anno (media nazionale)
            'densita':         85,
            'perc_stranieri':  0.8,
            'pop_totale':      0,
        }

    return {
        'eta_media':       data['eta_media'],
        'reddito_medio':   data['reddito_medio'],      # RON/anno
        'reddito_eur':     round(data['reddito_medio'] / EUR_RON_RATE),
        'densita':         data['densita'],
        'perc_stranieri':  data['perc_stranieri'],
        'pop_totale':      data.get('pop_totale', 0),
        'paese':           'RO',
        'valuta':          'RON',
        'fonte':           'INS Romania — Recensământul 2021',
    }

def converti_ron_eur(importo_ron: float) -> float:
    return round(importo_ron / EUR_RON_RATE, 2)

def converti_eur_ron(importo_eur: float) -> float:
    return round(importo_eur * EUR_RON_RATE, 2)

def get_market_assessment_ro(reddito_ron: float, densita: float) -> dict:
    """Valutazione mercato rumeno — equivalente di get_market_assessment ISTAT."""
    reddito_eur = converti_ron_eur(reddito_ron)

    if   reddito_ron > 48000: mercato = 'premium'
    elif reddito_ron > 36000: mercato = 'medio-alto'
    elif reddito_ron > 24000: mercato = 'medio'
    else:                      mercato = 'popolare'

    if   densita > 2000: tipo_area = 'urbano_denso'
    elif densita > 500:  tipo_area = 'urbano'
    elif densita > 100:  tipo_area = 'semi_urbano'
    else:                tipo_area = 'rurale'

    return {
        'tipo_mercato':  mercato,
        'tipo_area':     tipo_area,
        'reddito_eur':   reddito_eur,
        'potenziale':    'alto' if reddito_ron > 36000 and densita > 500 else
                         'medio' if reddito_ron > 24000 else 'basso',
    }
