"""
Dati demografici ISTAT per comune italiano.
Fonte: ISTAT Censimento 2021 + MEF dichiarazioni redditi 2022.
Dati aggregati per provincia/regione come fallback.
"""

# Dati per codice ISTAT provincia (prime 3 cifre del codice comune)
# eta_media: anni, reddito_medio: €/anno, densita: ab/km²
PROVINCE_DATA = {
    # Nord-Ovest
    '001': {'nome': 'Torino', 'eta_media': 46.2, 'reddito_medio': 22800, 'densita': 337},
    '002': {'nome': 'Vercelli', 'eta_media': 47.1, 'reddito_medio': 20100, 'densita': 72},
    '003': {'nome': 'Novara', 'eta_media': 46.8, 'reddito_medio': 21400, 'densita': 174},
    '004': {'nome': 'Cuneo', 'eta_media': 46.5, 'reddito_medio': 21200, 'densita': 82},
    '005': {'nome': 'Asti', 'eta_media': 47.3, 'reddito_medio': 19800, 'densita': 116},
    '006': {'nome': 'Alessandria', 'eta_media': 47.8, 'reddito_medio': 20600, 'densita': 120},
    '096': {'nome': 'Biella', 'eta_media': 48.1, 'reddito_medio': 20200, 'densita': 151},
    '103': {'nome': 'Verbano-Cusio-Ossola', 'eta_media': 47.2, 'reddito_medio': 19900, 'densita': 72},
    '007': {'nome': 'Aosta', 'eta_media': 46.1, 'reddito_medio': 22600, 'densita': 39},
    '008': {'nome': 'Imperia', 'eta_media': 48.5, 'reddito_medio': 19600, 'densita': 162},
    '009': {'nome': 'Savona', 'eta_media': 48.9, 'reddito_medio': 20800, 'densita': 174},
    '010': {'nome': 'Genova', 'eta_media': 48.2, 'reddito_medio': 22400, 'densita': 486},
    '011': {'nome': 'La Spezia', 'eta_media': 47.6, 'reddito_medio': 20200, 'densita': 232},
    '012': {'nome': 'Varese', 'eta_media': 45.8, 'reddito_medio': 23200, 'densita': 711},
    '013': {'nome': 'Como', 'eta_media': 45.4, 'reddito_medio': 23800, 'densita': 492},
    '014': {'nome': 'Sondrio', 'eta_media': 46.8, 'reddito_medio': 20100, 'densita': 57},
    '015': {'nome': 'Milano', 'eta_media': 44.1, 'reddito_medio': 28600, 'densita': 2063},
    '016': {'nome': 'Bergamo', 'eta_media': 44.8, 'reddito_medio': 23400, 'densita': 413},
    '017': {'nome': 'Brescia', 'eta_media': 44.9, 'reddito_medio': 22800, 'densita': 291},
    '018': {'nome': 'Pavia', 'eta_media': 46.9, 'reddito_medio': 21200, 'densita': 184},
    '019': {'nome': 'Cremona', 'eta_media': 46.7, 'reddito_medio': 21800, 'densita': 156},
    '020': {'nome': 'Mantova', 'eta_media': 46.4, 'reddito_medio': 22100, 'densita': 173},
    '097': {'nome': 'Lecco', 'eta_media': 45.6, 'reddito_medio': 23100, 'densita': 313},
    '098': {'nome': 'Lodi', 'eta_media': 45.2, 'reddito_medio': 22400, 'densita': 256},
    '108': {'nome': 'Monza e della Brianza', 'eta_media': 44.6, 'reddito_medio': 24800, 'densita': 2081},
    # Nord-Est
    '021': {'nome': 'Bolzano', 'eta_media': 43.8, 'reddito_medio': 24200, 'densita': 72},
    '022': {'nome': 'Trento', 'eta_media': 44.6, 'reddito_medio': 23400, 'densita': 87},
    '023': {'nome': 'Verona', 'eta_media': 45.2, 'reddito_medio': 23600, 'densita': 312},
    '024': {'nome': 'Vicenza', 'eta_media': 45.1, 'reddito_medio': 23800, 'densita': 329},
    '025': {'nome': 'Belluno', 'eta_media': 47.4, 'reddito_medio': 21200, 'densita': 55},
    '026': {'nome': 'Treviso', 'eta_media': 45.0, 'reddito_medio': 23200, 'densita': 349},
    '027': {'nome': 'Venezia', 'eta_media': 46.1, 'reddito_medio': 22400, 'densita': 268},
    '028': {'nome': 'Padova', 'eta_media': 45.3, 'reddito_medio': 23100, 'densita': 429},
    '029': {'nome': 'Rovigo', 'eta_media': 47.6, 'reddito_medio': 19800, 'densita': 130},
    '030': {'nome': 'Udine', 'eta_media': 47.2, 'reddito_medio': 21400, 'densita': 89},
    '031': {'nome': 'Gorizia', 'eta_media': 48.1, 'reddito_medio': 20800, 'densita': 182},
    '032': {'nome': 'Trieste', 'eta_media': 48.4, 'reddito_medio': 22100, 'densita': 1023},
    '093': {'nome': 'Pordenone', 'eta_media': 46.4, 'reddito_medio': 21800, 'densita': 163},
    '033': {'nome': 'Piacenza', 'eta_media': 46.8, 'reddito_medio': 21600, 'densita': 102},
    '034': {'nome': 'Parma', 'eta_media': 45.8, 'reddito_medio': 23200, 'densita': 133},
    '035': {'nome': 'Reggio Emilia', 'eta_media': 44.6, 'reddito_medio': 23400, 'densita': 261},
    '036': {'nome': 'Modena', 'eta_media': 45.2, 'reddito_medio': 23800, 'densita': 270},
    '037': {'nome': 'Bologna', 'eta_media': 46.1, 'reddito_medio': 24600, 'densita': 274},
    '038': {'nome': 'Ferrara', 'eta_media': 48.2, 'reddito_medio': 20400, 'densita': 131},
    '039': {'nome': 'Ravenna', 'eta_media': 47.1, 'reddito_medio': 22100, 'densita': 163},
    '040': {'nome': 'Forlì-Cesena', 'eta_media': 46.8, 'reddito_medio': 21800, 'densita': 179},
    '099': {'nome': 'Rimini', 'eta_media': 45.6, 'reddito_medio': 21200, 'densita': 484},
    # Centro
    '041': {'nome': 'Massa-Carrara', 'eta_media': 47.8, 'reddito_medio': 19600, 'densita': 153},
    '042': {'nome': 'Lucca', 'eta_media': 47.2, 'reddito_medio': 20800, 'densita': 193},
    '043': {'nome': 'Pistoia', 'eta_media': 46.8, 'reddito_medio': 20400, 'densita': 274},
    '044': {'nome': 'Firenze', 'eta_media': 46.4, 'reddito_medio': 24200, 'densita': 385},
    '045': {'nome': 'Livorno', 'eta_media': 47.6, 'reddito_medio': 20600, 'densita': 214},
    '046': {'nome': 'Pisa', 'eta_media': 46.1, 'reddito_medio': 21400, 'densita': 168},
    '047': {'nome': 'Arezzo', 'eta_media': 47.1, 'reddito_medio': 20200, 'densita': 103},
    '048': {'nome': 'Siena', 'eta_media': 47.4, 'reddito_medio': 21800, 'densita': 67},
    '049': {'nome': 'Grosseto', 'eta_media': 48.2, 'reddito_medio': 19400, 'densita': 57},
    '050': {'nome': 'Prato', 'eta_media': 44.2, 'reddito_medio': 21600, 'densita': 733},
    '051': {'nome': 'Massa', 'eta_media': 47.1, 'reddito_medio': 19200, 'densita': 153},
    '052': {'nome': 'Perugia', 'eta_media': 46.8, 'reddito_medio': 20100, 'densita': 104},
    '053': {'nome': 'Terni', 'eta_media': 47.6, 'reddito_medio': 19800, 'densita': 111},
    '054': {'nome': 'Pesaro e Urbino', 'eta_media': 47.2, 'reddito_medio': 20400, 'densita': 137},
    '055': {'nome': 'Ancona', 'eta_media': 47.1, 'reddito_medio': 21200, 'densita': 234},
    '056': {'nome': 'Macerata', 'eta_media': 47.4, 'reddito_medio': 19800, 'densita': 98},
    '057': {'nome': 'Ascoli Piceno', 'eta_media': 47.8, 'reddito_medio': 19200, 'densita': 116},
    '109': {'nome': 'Fermo', 'eta_media': 47.2, 'reddito_medio': 19400, 'densita': 175},
    '058': {'nome': 'Viterbo', 'eta_media': 47.4, 'reddito_medio': 18800, 'densita': 89},
    '059': {'nome': 'Rieti', 'eta_media': 47.8, 'reddito_medio': 17800, 'densita': 54},
    '058': {'nome': 'Roma', 'eta_media': 44.8, 'reddito_medio': 23400, 'densita': 832},
    '060': {'nome': 'Roma', 'eta_media': 44.8, 'reddito_medio': 23400, 'densita': 832},
    '061': {'nome': 'Latina', 'eta_media': 45.6, 'reddito_medio': 18600, 'densita': 185},
    '062': {'nome': 'Frosinone', 'eta_media': 46.8, 'reddito_medio': 17400, 'densita': 137},
    '063': {'nome': "L'Aquila", 'eta_media': 47.6, 'reddito_medio': 17800, 'densita': 56},
    '064': {'nome': 'Teramo', 'eta_media': 46.8, 'reddito_medio': 18200, 'densita': 129},
    '065': {'nome': 'Pescara', 'eta_media': 46.1, 'reddito_medio': 19200, 'densita': 389},
    '066': {'nome': 'Chieti', 'eta_media': 46.8, 'reddito_medio': 18400, 'densita': 136},
    '067': {'nome': 'Campobasso', 'eta_media': 47.8, 'reddito_medio': 16800, 'densita': 61},
    '094': {'nome': 'Isernia', 'eta_media': 48.2, 'reddito_medio': 15800, 'densita': 50},
    # Sud
    '068': {'nome': 'Caserta', 'eta_media': 42.8, 'reddito_medio': 14800, 'densita': 453},
    '069': {'nome': 'Benevento', 'eta_media': 46.2, 'reddito_medio': 15200, 'densita': 122},
    '070': {'nome': 'Napoli', 'eta_media': 41.2, 'reddito_medio': 14200, 'densita': 2634},
    '071': {'nome': 'Avellino', 'eta_media': 46.4, 'reddito_medio': 15400, 'densita': 135},
    '072': {'nome': 'Salerno', 'eta_media': 44.2, 'reddito_medio': 15800, 'densita': 188},
    '073': {'nome': 'Foggia', 'eta_media': 43.8, 'reddito_medio': 13800, 'densita': 102},
    '074': {'nome': 'Bari', 'eta_media': 43.2, 'reddito_medio': 16800, 'densita': 333},
    '075': {'nome': 'Taranto', 'eta_media': 44.6, 'reddito_medio': 14400, 'densita': 193},
    '076': {'nome': 'Brindisi', 'eta_media': 45.1, 'reddito_medio': 14200, 'densita': 175},
    '077': {'nome': 'Lecce', 'eta_media': 45.4, 'reddito_medio': 14600, 'densita': 265},
    '110': {'nome': 'Barletta-Andria-Trani', 'eta_media': 43.4, 'reddito_medio': 13600, 'densita': 291},
    '078': {'nome': 'Potenza', 'eta_media': 46.8, 'reddito_medio': 15200, 'densita': 57},
    '079': {'nome': 'Matera', 'eta_media': 46.4, 'reddito_medio': 15600, 'densita': 54},
    '080': {'nome': 'Cosenza', 'eta_media': 44.8, 'reddito_medio': 13200, 'densita': 129},
    '081': {'nome': 'Catanzaro', 'eta_media': 45.2, 'reddito_medio': 13600, 'densita': 172},
    '082': {'nome': 'Reggio Calabria', 'eta_media': 44.6, 'reddito_medio': 12800, 'densita': 178},
    '083': {'nome': 'Crotone', 'eta_media': 43.8, 'reddito_medio': 11800, 'densita': 122},
    '084': {'nome': 'Vibo Valentia', 'eta_media': 44.2, 'reddito_medio': 11400, 'densita': 148},
    # Sicilia
    '085': {'nome': 'Trapani', 'eta_media': 44.2, 'reddito_medio': 12400, 'densita': 193},
    '086': {'nome': 'Palermo', 'eta_media': 43.1, 'reddito_medio': 13200, 'densita': 405},
    '087': {'nome': 'Messina', 'eta_media': 45.2, 'reddito_medio': 13600, 'densita': 196},
    '088': {'nome': 'Agrigento', 'eta_media': 44.6, 'reddito_medio': 11800, 'densita': 160},
    '089': {'nome': 'Caltanissetta', 'eta_media': 44.8, 'reddito_medio': 12200, 'densita': 132},
    '090': {'nome': 'Enna', 'eta_media': 46.2, 'reddito_medio': 11600, 'densita': 67},
    '091': {'nome': 'Catania', 'eta_media': 42.8, 'reddito_medio': 14200, 'densita': 469},
    '092': {'nome': 'Ragusa', 'eta_media': 43.4, 'reddito_medio': 14800, 'densita': 191},
    '093': {'nome': 'Siracusa', 'eta_media': 44.1, 'reddito_medio': 13400, 'densita': 187},
    # Sardegna
    '095': {'nome': 'Sassari', 'eta_media': 46.2, 'reddito_medio': 16200, 'densita': 50},
    '096': {'nome': 'Nuoro', 'eta_media': 47.1, 'reddito_medio': 14800, 'densita': 27},
    '097': {'nome': 'Oristano', 'eta_media': 48.4, 'reddito_medio': 15200, 'densita': 43},
    '092': {'nome': 'Cagliari', 'eta_media': 46.1, 'reddito_medio': 17800, 'densita': 263},
    '111': {'nome': 'Sud Sardegna', 'eta_media': 47.2, 'reddito_medio': 14600, 'densita': 37},
}

# Dati specifici per le principali città (più precisi)
CITTA_DATA = {
    'milano': {'eta_media': 43.8, 'reddito_medio': 29400, 'densita': 7200, 'note': 'Alta densità, ottimo per self-service'},
    'roma': {'eta_media': 44.2, 'reddito_medio': 23800, 'densita': 2200, 'note': 'Grande mercato, concorrenza media'},
    'napoli': {'eta_media': 40.8, 'reddito_medio': 13800, 'densita': 8182, 'note': 'Altissima densità, reddito basso'},
    'torino': {'eta_media': 46.1, 'reddito_medio': 22400, 'densita': 6800, 'note': 'Buon mercato, popolazione anziana'},
    'palermo': {'eta_media': 42.8, 'reddito_medio': 12800, 'densita': 4200, 'note': 'Alta densità, attenzione al reddito'},
    'genova': {'eta_media': 48.6, 'reddito_medio': 22100, 'densita': 2400, 'note': 'Popolazione anziana, alta fidelizzazione'},
    'bologna': {'eta_media': 46.8, 'reddito_medio': 25200, 'densita': 2800, 'note': 'Ottimo potere acquisto, studenti'},
    'firenze': {'eta_media': 47.1, 'reddito_medio': 24800, 'densita': 3500, 'note': 'Turismo + residenti, ottimo mix'},
    'bari': {'eta_media': 43.4, 'reddito_medio': 16400, 'densita': 2900, 'note': 'Mercato in crescita'},
    'catania': {'eta_media': 42.6, 'reddito_medio': 13800, 'densita': 2800, 'note': 'Giovane, alta densità'},
    'venezia': {'eta_media': 47.2, 'reddito_medio': 22800, 'densita': 620, 'note': 'Terraferma ottima, centro storico difficile'},
    'verona': {'eta_media': 45.4, 'reddito_medio': 23600, 'densita': 1100, 'note': 'Buon reddito, turismo'},
    'padova': {'eta_media': 45.1, 'reddito_medio': 23200, 'densita': 2200, 'note': 'Università, alta domanda studentesca'},
    'trieste': {'eta_media': 49.2, 'reddito_medio': 22400, 'densita': 2400, 'note': 'Popolazione anziana, alta fidelizzazione'},
    'brescia': {'eta_media': 44.6, 'reddito_medio': 22800, 'densita': 1800, 'note': 'Industria, lavoratori, buona domanda'},
    'taranto': {'eta_media': 44.2, 'reddito_medio': 14200, 'densita': 1400, 'note': 'Mercato in sviluppo'},
    'prato': {'eta_media': 43.8, 'reddito_medio': 21200, 'densita': 2100, 'note': 'Alta immigrazione, ottimo per laundromat'},
    'reggio calabria': {'eta_media': 44.4, 'reddito_medio': 12600, 'densita': 1600, 'note': 'Mercato da sviluppare'},
    'modena': {'eta_media': 45.4, 'reddito_medio': 24200, 'densita': 870, 'note': 'Alto reddito, industriale'},
    'reggio emilia': {'eta_media': 44.8, 'reddito_medio': 23800, 'densita': 820, 'note': 'Ottimo mercato, immigrazione'},
    'perugia': {'eta_media': 46.4, 'reddito_medio': 19800, 'densita': 430, 'note': 'Università, studenti'},
    'livorno': {'eta_media': 47.8, 'reddito_medio': 20200, 'densita': 1100, 'note': 'Porto, lavoratori'},
    'cagliari': {'eta_media': 46.2, 'reddito_medio': 18200, 'densita': 1900, 'note': 'Capoluogo, buon mercato'},
    'sassari': {'eta_media': 45.8, 'reddito_medio': 15800, 'densita': 530, 'note': 'Secondo centro sardo'},
    'foggia': {'eta_media': 43.4, 'reddito_medio': 13400, 'densita': 490, 'note': 'Mercato giovane'},
    'salerno': {'eta_media': 43.8, 'reddito_medio': 15600, 'densita': 2900, 'note': 'Buona densità, turismo'},
    'ferrara': {'eta_media': 48.4, 'reddito_medio': 20400, 'densita': 430, 'note': 'Universitaria, anziani'},
    'ravenna': {'eta_media': 47.2, 'reddito_medio': 21800, 'densita': 540, 'note': 'Porto, industria'},
    'rimini': {'eta_media': 45.8, 'reddito_medio': 21400, 'densita': 1600, 'note': 'Turismo, stagionale'},
    'lecce': {'eta_media': 45.6, 'reddito_medio': 14400, 'densita': 1100, 'note': 'Università, turismo'},
}


def get_demographic_data(citta: str, provincia: str = None) -> dict:
    """
    Restituisce dati demografici per una città/provincia italiana.
    Cerca prima per città, poi per provincia, poi usa media nazionale.
    """
    # Cerca per città (lowercase, strip)
    citta_key = citta.lower().strip() if citta else ''
    
    # Rimuovi "di", "del", "della" ecc
    for prefix in ['comune di ', 'città di ', 'provincia di ']:
        if citta_key.startswith(prefix):
            citta_key = citta_key[len(prefix):]
    
    if citta_key in CITTA_DATA:
        d = CITTA_DATA[citta_key].copy()
        d['fonte'] = 'città'
        d['citta'] = citta
        return d
    
    # Cerca parziale
    for key, val in CITTA_DATA.items():
        if key in citta_key or citta_key in key:
            d = val.copy()
            d['fonte'] = 'città (parziale)'
            d['citta'] = citta
            return d
    
    # Cerca per provincia
    if provincia:
        prov_key = provincia.upper().strip()[:2]
        # Mappa sigle → codici
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
    
    # Fallback: media nazionale
    return {
        'eta_media': 46.4,
        'reddito_medio': 19800,
        'densita': 200,
        'note': 'Dati medi nazionali (zona non trovata)',
        'fonte': 'nazionale',
        'citta': citta or 'N/D',
    }


def get_market_assessment(eta_media: float, reddito_medio: float, densita: float, concorrenti: int) -> dict:
    """Valuta il potenziale di mercato per una lavanderia self-service."""
    score = 0
    notes = []

    # Densità popolazione
    if densita > 2000:
        score += 30
        notes.append('✅ Densità molto alta — mercato eccellente')
    elif densita > 800:
        score += 22
        notes.append('✅ Buona densità urbana')
    elif densita > 300:
        score += 14
        notes.append('⚠️ Densità media — valutare con attenzione')
    else:
        score += 6
        notes.append('❌ Bassa densità — mercato limitato')

    # Età media (target ideale: 35-50 anni)
    if 38 <= eta_media <= 50:
        score += 25
        notes.append('✅ Fascia d\'età ideale per il self-service')
    elif eta_media > 50:
        score += 18
        notes.append('ℹ️ Popolazione anziana — alta fidelizzazione')
    else:
        score += 15
        notes.append('ℹ️ Popolazione giovane — abitudini diverse')

    # Reddito medio (fascia media è il target)
    if 16000 <= reddito_medio <= 26000:
        score += 25
        notes.append('✅ Reddito medio — target ideale laundromat')
    elif reddito_medio > 26000:
        score += 15
        notes.append('ℹ️ Reddito alto — preferisce lavanderia a domicilio')
    else:
        score += 10
        notes.append('⚠️ Reddito basso — sensibile al prezzo')

    # Concorrenza
    if concorrenti == 0:
        score += 20
        notes.append('✅ Nessun concorrente diretto — blue ocean')
    elif concorrenti == 1:
        score += 12
        notes.append('ℹ️ Un concorrente — mercato condivisibile')
    elif concorrenti <= 3:
        score += 5
        notes.append('⚠️ Concorrenza presente — differenziazione necessaria')
    else:
        score += 0
        notes.append('❌ Alta concorrenza — mercato saturo')

    # Label
    if score >= 75:
        label = 'Eccellente'
        colore = '#10b981'
    elif score >= 55:
        label = 'Buono'
        colore = '#3b82f6'
    elif score >= 35:
        label = 'Discreto'
        colore = '#f59e0b'
    else:
        label = 'Scarso'
        colore = '#ef4444'

    return {
        'score': score,
        'label': label,
        'colore': colore,
        'note': notes,
    }

