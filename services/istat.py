"""
Dati demografici ISTAT per province e principali città italiane.
Fonte: ISTAT Censimento 2021 + MEF dichiarazioni redditi 2022.
eta_media: anni, reddito_medio: €/anno, densita: ab/km²
"""

PROVINCE_DATA = {
    # Nord-Ovest
    '001': {'nome': 'Torino',                'eta_media': 46.2, 'reddito_medio': 22800, 'densita': 337, 'perc_stranieri': 15.2},
    '002': {'nome': 'Vercelli',              'eta_media': 47.1, 'reddito_medio': 20100, 'densita': 72, 'perc_stranieri': 11.8},
    '003': {'nome': 'Novara',                'eta_media': 46.8, 'reddito_medio': 21400, 'densita': 174, 'perc_stranieri': 13.4},
    '004': {'nome': 'Cuneo',                 'eta_media': 46.5, 'reddito_medio': 21200, 'densita': 82, 'perc_stranieri': 11.9},
    '005': {'nome': 'Asti',                  'eta_media': 47.3, 'reddito_medio': 19800, 'densita': 116, 'perc_stranieri': 11.2},
    '006': {'nome': 'Alessandria',           'eta_media': 47.8, 'reddito_medio': 20600, 'densita': 120, 'perc_stranieri': 11.5},
    '096': {'nome': 'Biella',                'eta_media': 48.1, 'reddito_medio': 20200, 'densita': 151, 'perc_stranieri': 9.8},
    '103': {'nome': 'Verbano-Cusio-Ossola',  'eta_media': 47.2, 'reddito_medio': 19900, 'densita': 72, 'perc_stranieri': 10.1},
    '007': {'nome': 'Aosta',                 'eta_media': 46.1, 'reddito_medio': 22600, 'densita': 39, 'perc_stranieri': 8.9},
    '008': {'nome': 'Imperia',               'eta_media': 48.5, 'reddito_medio': 19600, 'densita': 162, 'perc_stranieri': 7.2},
    '009': {'nome': 'Savona',                'eta_media': 48.9, 'reddito_medio': 20800, 'densita': 174, 'perc_stranieri': 8.1},
    '010': {'nome': 'Genova',                'eta_media': 48.2, 'reddito_medio': 22400, 'densita': 486, 'perc_stranieri': 9.4},
    '011': {'nome': 'La Spezia',             'eta_media': 47.6, 'reddito_medio': 20200, 'densita': 232, 'perc_stranieri': 7.8},
    '012': {'nome': 'Varese',                'eta_media': 45.8, 'reddito_medio': 23200, 'densita': 711, 'perc_stranieri': 16.8},
    '013': {'nome': 'Como',                  'eta_media': 45.4, 'reddito_medio': 23800, 'densita': 492, 'perc_stranieri': 15.9},
    '014': {'nome': 'Sondrio',               'eta_media': 46.8, 'reddito_medio': 20100, 'densita': 57, 'perc_stranieri': 8.2},
    '015': {'nome': 'Milano',                'eta_media': 44.1, 'reddito_medio': 28600, 'densita': 2063, 'perc_stranieri': 19.8},
    '016': {'nome': 'Bergamo',               'eta_media': 44.8, 'reddito_medio': 23400, 'densita': 413, 'perc_stranieri': 16.4},
    '017': {'nome': 'Brescia',               'eta_media': 44.9, 'reddito_medio': 22800, 'densita': 291, 'perc_stranieri': 15.2},
    '018': {'nome': 'Pavia',                 'eta_media': 46.9, 'reddito_medio': 21200, 'densita': 184, 'perc_stranieri': 13.1},
    '019': {'nome': 'Cremona',               'eta_media': 46.7, 'reddito_medio': 21800, 'densita': 156, 'perc_stranieri': 14.8},
    '020': {'nome': 'Mantova',               'eta_media': 46.4, 'reddito_medio': 22100, 'densita': 173, 'perc_stranieri': 12.9},
    '097': {'nome': 'Lecco',                 'eta_media': 45.6, 'reddito_medio': 23100, 'densita': 313, 'perc_stranieri': 11.8},
    '098': {'nome': 'Lodi',                  'eta_media': 45.2, 'reddito_medio': 22400, 'densita': 256, 'perc_stranieri': 11.2},
    '108': {'nome': 'Monza e della Brianza', 'eta_media': 44.6, 'reddito_medio': 24800, 'densita': 2081, 'perc_stranieri': 3.2},
    # Nord-Est
    '021': {'nome': 'Bolzano',               'eta_media': 43.8, 'reddito_medio': 24200, 'densita': 72, 'perc_stranieri': 16.2},
    '022': {'nome': 'Trento',                'eta_media': 44.6, 'reddito_medio': 23400, 'densita': 87, 'perc_stranieri': 13.4},
    '023': {'nome': 'Verona',                'eta_media': 45.2, 'reddito_medio': 23600, 'densita': 312, 'perc_stranieri': 14.6},
    '024': {'nome': 'Vicenza',               'eta_media': 45.1, 'reddito_medio': 23800, 'densita': 329, 'perc_stranieri': 16.1},
    '025': {'nome': 'Belluno',               'eta_media': 47.4, 'reddito_medio': 21200, 'densita': 55, 'perc_stranieri': 13.8},
    '026': {'nome': 'Treviso',               'eta_media': 45.0, 'reddito_medio': 23200, 'densita': 349, 'perc_stranieri': 11.4},
    '027': {'nome': 'Venezia',               'eta_media': 46.1, 'reddito_medio': 22400, 'densita': 268, 'perc_stranieri': 13.2},
    '028': {'nome': 'Padova',                'eta_media': 45.3, 'reddito_medio': 23100, 'densita': 429, 'perc_stranieri': 15.4},
    '029': {'nome': 'Rovigo',                'eta_media': 47.6, 'reddito_medio': 19800, 'densita': 130, 'perc_stranieri': 12.8},
    '030': {'nome': 'Udine',                 'eta_media': 47.2, 'reddito_medio': 21400, 'densita': 89, 'perc_stranieri': 11.6},
    '031': {'nome': 'Gorizia',               'eta_media': 48.1, 'reddito_medio': 20800, 'densita': 182, 'perc_stranieri': 13.9},
    '032': {'nome': 'Trieste',               'eta_media': 48.4, 'reddito_medio': 22100, 'densita': 1023, 'perc_stranieri': 12.3},
    '093': {'nome': 'Pordenone',             'eta_media': 46.4, 'reddito_medio': 21800, 'densita': 163, 'perc_stranieri': 2.8},
    '033': {'nome': 'Piacenza',              'eta_media': 46.8, 'reddito_medio': 21600, 'densita': 102, 'perc_stranieri': 10.8},
    '034': {'nome': 'Parma',                 'eta_media': 45.8, 'reddito_medio': 23200, 'densita': 133, 'perc_stranieri': 13.2},
    '035': {'nome': 'Reggio Emilia',         'eta_media': 44.6, 'reddito_medio': 23400, 'densita': 261, 'perc_stranieri': 12.1},
    '036': {'nome': 'Modena',                'eta_media': 45.2, 'reddito_medio': 23800, 'densita': 270, 'perc_stranieri': 8.4},
    '037': {'nome': 'Bologna',               'eta_media': 46.1, 'reddito_medio': 24600, 'densita': 274, 'perc_stranieri': 7.2},
    '038': {'nome': 'Ferrara',               'eta_media': 48.2, 'reddito_medio': 20400, 'densita': 131, 'perc_stranieri': 11.8},
    '039': {'nome': 'Ravenna',               'eta_media': 47.1, 'reddito_medio': 22100, 'densita': 163, 'perc_stranieri': 9.6},
    '040': {'nome': 'Forlì-Cesena',          'eta_media': 46.8, 'reddito_medio': 21800, 'densita': 179, 'perc_stranieri': 8.9},
    '099': {'nome': 'Rimini',                'eta_media': 45.6, 'reddito_medio': 21200, 'densita': 484, 'perc_stranieri': 12.8},
    # Centro
    '041': {'nome': 'Massa-Carrara',         'eta_media': 47.8, 'reddito_medio': 19600, 'densita': 153, 'perc_stranieri': 7.8},
    '042': {'nome': 'Lucca',                 'eta_media': 47.2, 'reddito_medio': 20800, 'densita': 193, 'perc_stranieri': 8.2},
    '043': {'nome': 'Pistoia',               'eta_media': 46.8, 'reddito_medio': 20400, 'densita': 274, 'perc_stranieri': 14.2},
    '044': {'nome': 'Firenze',               'eta_media': 46.4, 'reddito_medio': 24200, 'densita': 385, 'perc_stranieri': 13.8},
    '045': {'nome': 'Livorno',               'eta_media': 47.6, 'reddito_medio': 20600, 'densita': 214, 'perc_stranieri': 15.1},
    '046': {'nome': 'Pisa',                  'eta_media': 46.1, 'reddito_medio': 21400, 'densita': 168, 'perc_stranieri': 12.4},
    '047': {'nome': 'Arezzo',                'eta_media': 47.1, 'reddito_medio': 20200, 'densita': 103, 'perc_stranieri': 13.6},
    '048': {'nome': 'Siena',                 'eta_media': 47.4, 'reddito_medio': 21800, 'densita': 67, 'perc_stranieri': 12.8},
    '049': {'nome': 'Grosseto',              'eta_media': 48.2, 'reddito_medio': 19400, 'densita': 57, 'perc_stranieri': 11.9},
    '050': {'nome': 'Prato',                 'eta_media': 44.2, 'reddito_medio': 21600, 'densita': 733, 'perc_stranieri': 13.2},
    '052': {'nome': 'Perugia',               'eta_media': 46.8, 'reddito_medio': 20100, 'densita': 104, 'perc_stranieri': 12.1},
    '053': {'nome': 'Terni',                 'eta_media': 47.6, 'reddito_medio': 19800, 'densita': 111, 'perc_stranieri': 10.4},
    '054': {'nome': 'Pesaro e Urbino',       'eta_media': 47.2, 'reddito_medio': 20400, 'densita': 137, 'perc_stranieri': 9.8},
    '055': {'nome': 'Ancona',                'eta_media': 47.1, 'reddito_medio': 21200, 'densita': 234, 'perc_stranieri': 11.2},
    '056': {'nome': 'Macerata',              'eta_media': 47.4, 'reddito_medio': 19800, 'densita': 98, 'perc_stranieri': 13.4},
    '057': {'nome': 'Ascoli Piceno',         'eta_media': 47.8, 'reddito_medio': 19200, 'densita': 116, 'perc_stranieri': 11.8},
    '109': {'nome': 'Fermo',                 'eta_media': 47.2, 'reddito_medio': 19400, 'densita': 175, 'perc_stranieri': 3.6},
    '058': {'nome': 'Roma',                  'eta_media': 44.8, 'reddito_medio': 23400, 'densita': 832, 'perc_stranieri': 16.4},
    '059': {'nome': 'Rieti',                 'eta_media': 47.8, 'reddito_medio': 17800, 'densita': 54, 'perc_stranieri': 11.6},
    '060': {'nome': 'Roma',                  'eta_media': 44.8, 'reddito_medio': 23400, 'densita': 832, 'perc_stranieri': 10.2},
    '061': {'nome': 'Latina',                'eta_media': 45.6, 'reddito_medio': 18600, 'densita': 185, 'perc_stranieri': 7.8},
    '062': {'nome': 'Frosinone',             'eta_media': 46.8, 'reddito_medio': 17400, 'densita': 137, 'perc_stranieri': 9.4},
    '063': {'nome': "L'Aquila",              'eta_media': 47.6, 'reddito_medio': 17800, 'densita': 56, 'perc_stranieri': 8.6},
    '064': {'nome': 'Teramo',                'eta_media': 46.8, 'reddito_medio': 18200, 'densita': 129, 'perc_stranieri': 7.2},
    '065': {'nome': 'Pescara',               'eta_media': 46.1, 'reddito_medio': 19200, 'densita': 389, 'perc_stranieri': 5.8},
    '066': {'nome': 'Chieti',                'eta_media': 46.8, 'reddito_medio': 18400, 'densita': 136, 'perc_stranieri': 6.4},
    '067': {'nome': 'Campobasso',            'eta_media': 47.8, 'reddito_medio': 16800, 'densita': 61, 'perc_stranieri': 4.8},
    '094': {'nome': 'Isernia',               'eta_media': 48.2, 'reddito_medio': 15800, 'densita': 50, 'perc_stranieri': 5.4},
    # Sud
    '068': {'nome': 'Caserta',               'eta_media': 42.8, 'reddito_medio': 14800, 'densita': 453, 'perc_stranieri': 5.2},
    '069': {'nome': 'Benevento',             'eta_media': 46.2, 'reddito_medio': 15200, 'densita': 122, 'perc_stranieri': 4.6},
    '070': {'nome': 'Napoli',                'eta_media': 41.2, 'reddito_medio': 14200, 'densita': 2634, 'perc_stranieri': 3.8},
    '071': {'nome': 'Avellino',              'eta_media': 46.4, 'reddito_medio': 15400, 'densita': 135, 'perc_stranieri': 4.2},
    '072': {'nome': 'Salerno',               'eta_media': 44.2, 'reddito_medio': 15800, 'densita': 188, 'perc_stranieri': 3.6},
    '073': {'nome': 'Foggia',                'eta_media': 43.8, 'reddito_medio': 13800, 'densita': 102, 'perc_stranieri': 3.2},
    '074': {'nome': 'Bari',                  'eta_media': 43.2, 'reddito_medio': 16800, 'densita': 333, 'perc_stranieri': 4.8},
    '075': {'nome': 'Taranto',               'eta_media': 44.6, 'reddito_medio': 14400, 'densita': 193, 'perc_stranieri': 3.8},
    '076': {'nome': 'Brindisi',              'eta_media': 45.1, 'reddito_medio': 14200, 'densita': 175, 'perc_stranieri': 5.2},
    '077': {'nome': 'Lecce',                 'eta_media': 45.4, 'reddito_medio': 14600, 'densita': 265, 'perc_stranieri': 4.6},
    '110': {'nome': 'Barletta-Andria-Trani', 'eta_media': 43.4, 'reddito_medio': 13600, 'densita': 291, 'perc_stranieri': 4.1},
    '078': {'nome': 'Potenza',               'eta_media': 46.8, 'reddito_medio': 15200, 'densita': 57, 'perc_stranieri': 3.4},
    '079': {'nome': 'Matera',                'eta_media': 46.4, 'reddito_medio': 15600, 'densita': 54, 'perc_stranieri': 4.1},
    '080': {'nome': 'Cosenza',               'eta_media': 44.8, 'reddito_medio': 13200, 'densita': 129, 'perc_stranieri': 3.8},
    '081': {'nome': 'Catanzaro',             'eta_media': 45.2, 'reddito_medio': 13600, 'densita': 172, 'perc_stranieri': 2.9},
    '082': {'nome': 'Reggio Calabria',       'eta_media': 44.6, 'reddito_medio': 12800, 'densita': 178, 'perc_stranieri': 2.6},
    '083': {'nome': 'Crotone',               'eta_media': 43.8, 'reddito_medio': 11800, 'densita': 122, 'perc_stranieri': 3.2},
    '084': {'nome': 'Vibo Valentia',         'eta_media': 44.2, 'reddito_medio': 11400, 'densita': 148, 'perc_stranieri': 2.8},
    # Sicilia
    '085': {'nome': 'Trapani',               'eta_media': 44.2, 'reddito_medio': 12400, 'densita': 193, 'perc_stranieri': 3.6},
    '086': {'nome': 'Palermo',               'eta_media': 43.1, 'reddito_medio': 13200, 'densita': 405, 'perc_stranieri': 4.2},
    '087': {'nome': 'Messina',               'eta_media': 45.2, 'reddito_medio': 13600, 'densita': 196, 'perc_stranieri': 3.8},
    '088': {'nome': 'Agrigento',             'eta_media': 44.6, 'reddito_medio': 11800, 'densita': 160, 'perc_stranieri': 4.1},
    '089': {'nome': 'Caltanissetta',         'eta_media': 44.8, 'reddito_medio': 12200, 'densita': 132, 'perc_stranieri': 3.4},
    '090': {'nome': 'Enna',                  'eta_media': 46.2, 'reddito_medio': 11600, 'densita': 67, 'perc_stranieri': 5.8},
    '091': {'nome': 'Catania',               'eta_media': 42.8, 'reddito_medio': 14200, 'densita': 469, 'perc_stranieri': 4.2},
    '092': {'nome': 'Ragusa',                'eta_media': 43.4, 'reddito_medio': 14800, 'densita': 191, 'perc_stranieri': 3.6},
    '093': {'nome': 'Siracusa',              'eta_media': 44.1, 'reddito_medio': 13400, 'densita': 187, 'perc_stranieri': 2.8},
    # Sardegna
    '095': {'nome': 'Sassari',               'eta_media': 46.2, 'reddito_medio': 16200, 'densita': 50, 'perc_stranieri': 4.8},
    '096': {'nome': 'Nuoro',                 'eta_media': 47.1, 'reddito_medio': 14800, 'densita': 27, 'perc_stranieri': 9.8},
    '097': {'nome': 'Oristano',              'eta_media': 48.4, 'reddito_medio': 15200, 'densita': 43, 'perc_stranieri': 11.8},
    '092': {'nome': 'Cagliari',              'eta_media': 46.1, 'reddito_medio': 17800, 'densita': 263, 'perc_stranieri': 3.6},
    '111': {'nome': 'Sud Sardegna',          'eta_media': 47.2, 'reddito_medio': 14600, 'densita': 37, 'perc_stranieri': 3.8},
}

CITTA_DATA = {
    'milano':          {'eta_media': 43.8, 'reddito_medio': 29400, 'densita': 7200,  'note': 'Alta densità, ottimo per self-service'},
    'roma':            {'eta_media': 44.2, 'reddito_medio': 23800, 'densita': 2200,  'note': 'Grande mercato, concorrenza media'},
    'napoli':          {'eta_media': 40.8, 'reddito_medio': 13800, 'densita': 8182,  'note': 'Altissima densità, reddito basso'},
    'torino':          {'eta_media': 46.1, 'reddito_medio': 22400, 'densita': 6800,  'note': 'Buon mercato, popolazione anziana'},
    'palermo':         {'eta_media': 42.8, 'reddito_medio': 12800, 'densita': 4200,  'note': 'Alta densità, attenzione al reddito'},
    'genova':          {'eta_media': 48.6, 'reddito_medio': 22100, 'densita': 2400,  'note': 'Popolazione anziana, alta fidelizzazione'},
    'bologna':         {'eta_media': 46.8, 'reddito_medio': 25200, 'densita': 2800,  'note': 'Ottimo potere acquisto, studenti'},
    'firenze':         {'eta_media': 47.1, 'reddito_medio': 24800, 'densita': 3500,  'note': 'Turismo + residenti, ottimo mix'},
    'bari':            {'eta_media': 43.4, 'reddito_medio': 16400, 'densita': 2900,  'note': 'Mercato in crescita'},
    'catania':         {'eta_media': 42.6, 'reddito_medio': 13800, 'densita': 2800,  'note': 'Giovane, alta densità'},
    'venezia':         {'eta_media': 47.2, 'reddito_medio': 22800, 'densita': 620,   'note': 'Terraferma ottima, centro storico difficile'},
    'verona':          {'eta_media': 45.4, 'reddito_medio': 23600, 'densita': 1100,  'note': 'Buon reddito, turismo'},
    'padova':          {'eta_media': 45.1, 'reddito_medio': 23200, 'densita': 2200,  'note': 'Università, alta domanda studentesca'},
    'trieste':         {'eta_media': 49.2, 'reddito_medio': 22400, 'densita': 2400,  'note': 'Popolazione anziana, alta fidelizzazione'},
    'brescia':         {'eta_media': 44.6, 'reddito_medio': 22800, 'densita': 1800,  'note': 'Industria, lavoratori, buona domanda'},
    'taranto':         {'eta_media': 44.2, 'reddito_medio': 14200, 'densita': 1400,  'note': 'Mercato in sviluppo'},
    'prato':           {'eta_media': 43.8, 'reddito_medio': 21200, 'densita': 2100,  'note': 'Alta densità, buon mercato'},
    'reggio calabria': {'eta_media': 44.4, 'reddito_medio': 12600, 'densita': 1600,  'note': 'Mercato da sviluppare'},
    'modena':          {'eta_media': 45.4, 'reddito_medio': 24200, 'densita': 870,   'note': 'Alto reddito, industriale'},
    'reggio emilia':   {'eta_media': 44.8, 'reddito_medio': 23800, 'densita': 820,   'note': 'Ottimo mercato'},
    'perugia':         {'eta_media': 46.4, 'reddito_medio': 19800, 'densita': 430,   'note': 'Università, studenti'},
    'livorno':         {'eta_media': 47.8, 'reddito_medio': 20200, 'densita': 1100,  'note': 'Porto, lavoratori'},
    'cagliari':        {'eta_media': 46.2, 'reddito_medio': 18200, 'densita': 1900,  'note': 'Capoluogo, buon mercato'},
    'sassari':         {'eta_media': 45.8, 'reddito_medio': 15800, 'densita': 530,   'note': 'Secondo centro sardo'},
    'foggia':          {'eta_media': 43.4, 'reddito_medio': 13400, 'densita': 490,   'note': 'Mercato giovane'},
    'salerno':         {'eta_media': 43.8, 'reddito_medio': 15600, 'densita': 2900,  'note': 'Buona densità, turismo'},
    'ferrara':         {'eta_media': 48.4, 'reddito_medio': 20400, 'densita': 430,   'note': 'Universitaria, anziani'},
    'ravenna':         {'eta_media': 47.2, 'reddito_medio': 21800, 'densita': 540,   'note': 'Porto, industria'},
    'rimini':          {'eta_media': 45.8, 'reddito_medio': 21400, 'densita': 1600,  'note': 'Turismo, stagionale'},
    'lecce':           {'eta_media': 45.6, 'reddito_medio': 14400, 'densita': 1100,  'note': 'Università, turismo'},
}


def get_demographic_data(citta: str, provincia: str = None) -> dict:
    citta_key = citta.lower().strip() if citta else ''
    for prefix in ['comune di ', 'città di ', 'provincia di ']:
        if citta_key.startswith(prefix):
            citta_key = citta_key[len(prefix):]

    if citta_key in CITTA_DATA:
        d = CITTA_DATA[citta_key].copy()
        d['fonte'] = 'città'
        d['citta'] = citta
        return d

    for key, val in CITTA_DATA.items():
        if key in citta_key or citta_key in key:
            d = val.copy()
            d['fonte'] = 'città (parziale)'
            d['citta'] = citta
            return d

    if provincia:
        prov_key = provincia.upper().strip()[:2]
        SIGLE = {
            'TO': '001', 'VC': '002', 'NO': '003', 'CN': '004', 'AT': '005',
            'AL': '006', 'BI': '096', 'VB': '103', 'AO': '007', 'IM': '008',
            'SV': '009', 'GE': '010', 'SP': '011', 'VA': '012', 'CO': '013',
            'SO': '014', 'MI': '015', 'BG': '016', 'BS': '017', 'PV': '018',
            'CR': '019', 'MN': '020', 'LC': '097', 'LO': '098', 'MB': '108',
            'BZ': '021', 'TN': '022', 'VR': '023', 'VI': '024', 'BL': '025',
            'TV': '026', 'VE': '027', 'PD': '028', 'RO': '029', 'UD': '030',
            'GO': '031', 'TS': '032', 'PN': '093', 'PC': '033', 'PR': '034',
            'RE': '035', 'MO': '036', 'BO': '037', 'FE': '038', 'RA': '039',
            'FC': '040', 'RN': '099', 'MS': '041', 'LU': '042', 'PT': '043',
            'FI': '044', 'LI': '045', 'PI': '046', 'AR': '047', 'SI': '048',
            'GR': '049', 'PO': '050', 'PG': '052', 'TR': '053', 'PU': '054',
            'AN': '055', 'MC': '056', 'AP': '057', 'FM': '109', 'VT': '058',
            'RI': '059', 'RM': '060', 'LT': '061', 'FR': '062', 'AQ': '063',
            'TE': '064', 'PE': '065', 'CH': '066', 'CB': '067', 'IS': '094',
            'CE': '068', 'BN': '069', 'NA': '070', 'AV': '071', 'SA': '072',
            'FG': '073', 'BA': '074', 'TA': '075', 'BR': '076', 'LE': '077',
            'BT': '110', 'PZ': '078', 'MT': '079', 'CS': '080', 'CZ': '081',
            'RC': '082', 'KR': '083', 'VV': '084', 'TP': '085', 'PA': '086',
            'ME': '087', 'AG': '088', 'CL': '089', 'EN': '090', 'CT': '091',
            'RG': '092', 'SR': '093', 'SS': '095', 'NU': '096', 'OR': '097',
            'CA': '092', 'SU': '111',
        }
        codice = SIGLE.get(prov_key)
        if codice and codice in PROVINCE_DATA:
            d = PROVINCE_DATA[codice].copy()
            d['fonte'] = 'provincia'
            d['citta'] = citta
            return d

    return {
        'eta_media': 46.4,
        'reddito_medio': 19800,
        'densita': 200,
        'perc_stranieri': 8.0,
        'note': 'Dati medi nazionali (zona non trovata)',
        'fonte': 'nazionale',
        'citta': citta or 'N/D',
    }


def calcola_stima_clienti(pop_5min: int, pop_10min: int, densita: float,
                           concorrenti_500m: int, concorrenti_1km: int,
                           servizi_400m: int, reddito_medio: float,
                           recensioni_zona: int, gdo_500m: int,
                           mult_attractor: float = 1.0,
                           perc_stranieri: float = 8.0) -> dict:
    """
    Modello pesato stima clienti/giorno — valori conservativi realistici.

    Tasso base 1.8% (media italiana reale lavanderie self-service attive).
    Penalità concorrenza più severa: zona satura = quota residuale bassa.
    Segnali reali:
    - recensioni_zona: proxy traffico pedonale reale (metodo Lidl/Eurospin)
    - gdo_500m: validazione zona da catene GDO
    """
    # Bacino pesato (popolazione)
    pop_secondario = max(0, pop_10min - pop_5min)
    bacino = pop_5min * 0.60 + pop_secondario * 0.25

    # Tasso base realistico: ~1.8% della pop nel bacino visita/giorno
    # (dato medio italiano su lavanderie self-service operative)
    tasso_base = 0.018

    # Moltiplicatore densità
    if densita > 3000:
        mult_densita = 1.30
    elif densita > 1500:
        mult_densita = 1.15
    elif densita > 500:
        mult_densita = 1.00
    elif densita > 200:
        mult_densita = 0.85
    else:
        mult_densita = 0.65  # zona industriale/suburbana con villette

    # Moltiplicatore reddito
    if 16000 <= reddito_medio <= 26000:
        mult_reddito = 1.00   # target ideale
    elif reddito_medio > 35000:
        mult_reddito = 0.70   # reddito alto → stireria/lavatrice propria
    elif reddito_medio > 26000:
        mult_reddito = 0.85
    else:
        mult_reddito = 0.88   # reddito basso → abitudinari self-service

    # Moltiplicatore traffico reale (recensioni Google zona 400m)
    if recensioni_zona > 5000:
        mult_traffico = 1.20
    elif recensioni_zona > 2000:
        mult_traffico = 1.10
    elif recensioni_zona > 800:
        mult_traffico = 1.00
    elif recensioni_zona > 200:
        mult_traffico = 0.90
    else:
        mult_traffico = 0.75  # zona morta, poco passaggio reale

    # Moltiplicatore validazione GDO
    if gdo_500m >= 3:
        mult_gdo = 1.15
    elif gdo_500m == 2:
        mult_gdo = 1.08
    elif gdo_500m == 1:
        mult_gdo = 1.03
    else:
        mult_gdo = 1.00

    # Quota mercato — penalità concorrenza più severa
    # I clienti sono abitudinari: chi usa già una lavanderia tende a non cambiare
    if concorrenti_500m >= 4:
        share = 0.10   # zona ipersatura
    elif concorrenti_500m == 3:
        share = 0.15
    elif concorrenti_500m == 2:
        share = 0.22
    elif concorrenti_500m == 1:
        share = 0.40   # un concorrente diretto già radicato
    elif concorrenti_1km >= 4:
        share = 0.55
    elif concorrenti_1km >= 2:
        share = 0.70
    elif concorrenti_1km >= 1:
        share = 0.80
    else:
        share = 1.00   # zona vergine, nessun concorrente

    clienti_lordi = bacino * tasso_base * mult_densita * mult_reddito * mult_traffico * mult_gdo
    clienti_base  = max(0, round(clienti_lordi * share))
    clienti_netti = max(0, round(clienti_lordi * share * mult_attractor))

    fattori = [
        {'label': 'Bacino popolazione',    'valore': f'{int(bacino):,} ab.',         'peso': f'×{tasso_base}',       'icon': '👥', 'positivo': bacino > 5000},
        {'label': 'Densità abitativa',     'valore': f'{int(densita):,} ab/km²',     'peso': f'×{mult_densita:.2f}', 'icon': '🏙️', 'positivo': densita > 500},
        {'label': 'Fascia reddito',        'valore': f'€{int(reddito_medio):,}/anno','peso': f'×{mult_reddito:.2f}', 'icon': '💰', 'positivo': 16000 <= reddito_medio <= 26000},
        {'label': 'Traffico reale (rec.)', 'valore': f'{recensioni_zona:,} rec.',    'peso': f'×{mult_traffico:.2f}','icon': '⭐', 'positivo': recensioni_zona > 800},
        {'label': 'Validazione GDO',       'valore': f'{gdo_500m} catene vicine',    'peso': f'×{mult_gdo:.2f}',    'icon': '🛒', 'positivo': gdo_500m > 0},
        {'label': 'Quota mercato',         'valore': f'{int(share*100)}%',           'peso': f'×{share:.2f}',       'icon': '🥊', 'positivo': share > 0.6},
    ]

    if mult_attractor > 1.01:
        fattori.append({
            'label':     'Attractor points',
            'valore':    f'×{mult_attractor:.2f}',
            'peso':      f'×{mult_attractor:.2f}',
            'risultato': f'→ {clienti_netti} clienti/giorno (da {clienti_base} base)',
            'icon':      '🎓',
            'positivo':  True,
            'nota': (
                f'Università, caserme o ospedali vicini generano domanda aggiuntiva '
                f'non rilevata dai dati ISTAT residenti. '
                f'Boost applicato: +{int((mult_attractor-1)*100)}% sui clienti base.'
            ),
        })

    return {
        'clienti_giorno': clienti_netti,
        'scenario_pessimistico': round(clienti_netti * 0.60),
        'scenario_realistico':   clienti_netti,
        'scenario_ottimistico':  round(clienti_netti * 1.25),
        'clienti_mese_reale':    clienti_netti * 26,
        'fattori': fattori,
        'bacino_pesato': int(bacino),
    }


def get_market_assessment(eta_media: float, reddito_medio: float, densita: float,
                           concorrenti: int, recensioni_zona: int = 0,
                           gdo_500m: int = 0) -> dict:
    """Score zona 0-100."""
    score = 0
    notes = []

    # Densità (peso 30)
    if densita > 2000:
        score += 30; notes.append('✅ Densità altissima — mercato eccellente')
    elif densita > 800:
        score += 25; notes.append('✅ Alta densità — ottimo potenziale')
    elif densita > 300:
        score += 18; notes.append('ℹ️ Densità media — mercato buono')
    elif densita > 100:
        score += 12; notes.append('⚠️ Bassa densità — mercato limitato')
    else:
        score += 6;  notes.append('❌ Densità molto bassa — mercato difficile')

    # Età media (peso 15)
    if 38 <= eta_media <= 50:
        score += 15; notes.append('✅ Fascia d\'età ideale per il self-service')
    elif eta_media > 50:
        score += 10; notes.append('ℹ️ Popolazione anziana — alta fidelizzazione')
    else:
        score += 8;  notes.append('ℹ️ Popolazione giovane — abitudini diverse')

    # Reddito (peso 15)
    if 16000 <= reddito_medio <= 26000:
        score += 15; notes.append('✅ Reddito medio — target ideale laundromat')
    elif reddito_medio > 26000:
        score += 8;  notes.append('ℹ️ Reddito alto — preferisce lavanderia a domicilio')
    else:
        score += 6;  notes.append('⚠️ Reddito basso — sensibile al prezzo')

    # Traffico reale — recensioni Google (peso 20)
    if recensioni_zona > 5000:
        score += 20; notes.append('✅ Zona ad altissimo traffico (volume rec. Google)')
    elif recensioni_zona > 2000:
        score += 16; notes.append('✅ Zona ad alto traffico (volume rec. Google)')
    elif recensioni_zona > 800:
        score += 11; notes.append('ℹ️ Traffico pedonale medio')
    elif recensioni_zona > 200:
        score += 6;  notes.append('⚠️ Traffico pedonale basso')
    else:
        score += 2;  notes.append('❌ Zona poco frequentata')

    # Validazione GDO (peso 10)
    if gdo_500m >= 2:
        score += 10; notes.append('✅ Più catene GDO vicine — zona già validata')
    elif gdo_500m == 1:
        score += 7;  notes.append('✅ Catena GDO vicina — zona validata')
    else:
        score += 0;  notes.append('ℹ️ Nessuna GDO entro 500m')

    # Concorrenza (peso 10)
    if concorrenti == 0:
        score += 10; notes.append('✅ Nessun concorrente — blue ocean')
    elif concorrenti == 1:
        score += 6;  notes.append('ℹ️ Un concorrente — mercato condivisibile')
    elif concorrenti <= 3:
        score += 2;  notes.append('⚠️ Concorrenza presente')
    else:
        score += 0;  notes.append('❌ Alta concorrenza — mercato saturo')

    if score >= 75:
        label, colore = 'Eccellente', '#10b981'
    elif score >= 55:
        label, colore = 'Buono', '#3b82f6'
    elif score >= 35:
        label, colore = 'Discreto', '#f59e0b'
    else:
        label, colore = 'Scarso', '#ef4444'

    return {'score': score, 'label': label, 'colore': colore, 'note': notes}


# ── DATI OMI CANONI COMMERCIALI ───────────────────────────────────────────────
# Fonte: Agenzia delle Entrate — OMI (Osservatorio Mercato Immobiliare)
# Fascia canone annuo locazione commerciale €/mq per zona centrale/semicentrale.
# I valori sono range (min, max) per zona CENTRALE della città.
# Zone periferiche: applicare moltiplicatore 0.55-0.70.
# Aggiornamento: 2° semestre 2023.

OMI_CANONI = {
    # (canone_min_anno, canone_max_anno) in €/mq — zona centrale
    'milano':          (180, 420),
    'roma':            (130, 320),
    'napoli':          (80,  200),
    'torino':          (90,  200),
    'firenze':         (110, 260),
    'bologna':         (100, 220),
    'venezia':         (100, 240),
    'genova':          (70,  160),
    'palermo':         (60,  140),
    'bari':            (65,  150),
    'catania':         (55,  130),
    'verona':          (85,  190),
    'padova':          (80,  180),
    'brescia':         (80,  175),
    'trieste':         (75,  165),
    'modena':          (80,  170),
    'reggio emilia':   (75,  165),
    'prato':           (70,  155),
    'parma':           (80,  175),
    'perugia':         (60,  140),
    'livorno':         (60,  135),
    'cagliari':        (65,  145),
    'sassari':         (50,  115),
    'salerno':         (60,  135),
    'foggia':          (50,  115),
    'rimini':          (75,  165),
    'ravenna':         (65,  145),
    'ferrara':         (60,  135),
    'lecce':           (55,  125),
    'taranto':         (50,  115),
    'reggio calabria': (45,  105),
    # Fallback per province non elencate: applica fattore sul reddito medio
}

# Moltiplicatori zona (rispetto al centro)
OMI_ZONA_MULT = {
    'centrale':      1.00,
    'semicentrale':  0.72,
    'periferica':    0.55,
    'suburbana':     0.42,
}


def get_canone_stimato(citta: str, mq: int, zona: str = 'semicentrale') -> dict:
    """
    Restituisce stima canone mensile per locale commerciale.
    zona: 'centrale' | 'semicentrale' | 'periferica' | 'suburbana'
    """
    citta_key = (citta or '').lower().strip()
    for prefix in ['comune di ', 'città di ']:
        if citta_key.startswith(prefix):
            citta_key = citta_key[len(prefix):]

    # Cerca corrispondenza esatta o parziale
    range_anno = None
    for key, val in OMI_CANONI.items():
        if key == citta_key or key in citta_key or citta_key in key:
            range_anno = val
            break

    # Fallback: stima da reddito medio provinciale
    if not range_anno:
        demo = get_demographic_data(citta)
        reddito = demo.get('reddito_medio', 19800)
        # Approssimazione: canone commerciale ~0.4-0.9% del reddito medio per mq
        base_min = round(reddito * 0.004)
        base_max = round(reddito * 0.009)
        range_anno = (base_min, base_max)
        fonte = 'stima da reddito medio'
    else:
        fonte = 'dati OMI Agenzia Entrate'

    mult = OMI_ZONA_MULT.get(zona, 0.72)
    mq = max(20, mq or 60)

    canone_mq_min = round(range_anno[0] * mult)
    canone_mq_max = round(range_anno[1] * mult)

    canone_anno_min = round(canone_mq_min * mq)
    canone_anno_max = round(canone_mq_max * mq)

    canone_mese_min = round(canone_anno_min / 12)
    canone_mese_max = round(canone_anno_max / 12)

    return {
        'canone_mese_min': canone_mese_min,
        'canone_mese_max': canone_mese_max,
        'canone_mese_mid': round((canone_mese_min + canone_mese_max) / 2),
        'canone_mq_anno_min': canone_mq_min,
        'canone_mq_anno_max': canone_mq_max,
        'mq': mq,
        'zona': zona,
        'citta': citta,
        'fonte': fonte,
    }
