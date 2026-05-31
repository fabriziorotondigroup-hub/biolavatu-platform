"""
Geo routes — BIOLavaTU LaundryPro
Google Maps Platform: geocoding, Places Nearby Search.

Segnali reali di traffico:
  - recensioni_zona: somma recensioni Google di tutti i locali entro 400m
    (proxy traffico pedonale, stesso approccio di Lidl/Eurospin per site selection)
  - gdo_500m: catene GDO (Lidl, Eurospin, Conad, Esselunga, Penny, Carrefour,
    Decathlon, Coop, Pam) entro 500m — validazione indiretta della zona
Heatmap concorrenti: cerchi verde/arancio/rosso per saturazione.
"""
import os, math, requests
from flask import Blueprint, jsonify, request
from flask_login import login_required
from services.istat import (get_demographic_data, get_market_assessment,
                             calcola_stima_clienti)

geo_bp = Blueprint('geo', __name__)

GMAPS_KEY   = os.environ.get('GMAPS_KEY', '')
PLACES_URL  = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
GEOCODE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'

# Keyword usate per riconoscere catene GDO nella risposta Google
GDO_KEYWORDS = {
    'lidl', 'eurospin', 'conad', 'esselunga', 'penny', 'carrefour',
    'decathlon', 'coop', 'pam', 'aldi', 'in\'s', 'simply', 'despar',
    'interspar', 'spar', 'iper', 'ipercoop', 'tigros',
}


def walking_radius(minutes: int) -> int:
    return minutes * 80


def haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def gmaps_nearby(lat, lng, radius, place_type, keyword=None):
    params = {
        'location': f'{lat},{lng}',
        'radius': radius,
        'type': place_type,
        'key': GMAPS_KEY,
        'language': 'it',
    }
    if keyword:
        params['keyword'] = keyword
    try:
        r = requests.get(PLACES_URL, params=params, timeout=10)
        return r.json().get('results', [])
    except Exception:
        return []


def is_gdo(place_name: str) -> bool:
    name_lower = place_name.lower()
    return any(kw in name_lower for kw in GDO_KEYWORDS)


def place_to_poi(place, lat_c, lng_c, categoria, colore, icon):
    plat = place['geometry']['location']['lat']
    plng = place['geometry']['location']['lng']
    dist = int(haversine(lat_c, lng_c, plat, plng))
    return {
        'lat': plat, 'lng': plng,
        'nome': place.get('name', ''),
        'categoria': categoria,
        'colore': colore,
        'icon': icon,
        'distanza_m': dist,
        'rating': place.get('rating'),
        'user_ratings_total': place.get('user_ratings_total', 0),
        'open_now': place.get('opening_hours', {}).get('open_now'),
        'vicinity': place.get('vicinity', ''),
    }


# ── GEOCODING ─────────────────────────────────────────────────────────────────

@geo_bp.route('/api/geocode')
@login_required
def geocode():
    address = request.args.get('address', '')
    if not address:
        return jsonify({'error': 'Indirizzo mancante'}), 400
    try:
        r = requests.get(GEOCODE_URL, params={
            'address': address + ', Italia',
            'key': GMAPS_KEY, 'language': 'it', 'region': 'it',
        }, timeout=10)
        data = r.json()
        if data.get('status') == 'OK' and data['results']:
            res = data['results'][0]
            loc = res['geometry']['location']
            comp = {c['types'][0]: c['long_name']
                    for c in res.get('address_components', []) if c['types']}
            return jsonify({
                'lat': loc['lat'], 'lng': loc['lng'],
                'formatted': res.get('formatted_address', address),
                'citta':     comp.get('locality') or comp.get('administrative_area_level_3', ''),
                'provincia': comp.get('administrative_area_level_2', ''),
                'cap':       comp.get('postal_code', ''),
            })
        return jsonify({'error': 'Indirizzo non trovato'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ANALISI ZONA ──────────────────────────────────────────────────────────────

@geo_bp.route('/api/zona-analisi')
@login_required
def zona_analisi():
    lat      = float(request.args.get('lat', 0))
    lng      = float(request.args.get('lng', 0))
    citta    = request.args.get('citta', '')
    provincia = request.args.get('provincia', '')
    if not lat or not lng:
        return jsonify({'error': 'Coordinate mancanti'}), 400

    r3  = walking_radius(3)   # 240m
    r5  = walking_radius(5)   # 400m
    r10 = walking_radius(10)  # 800m
    r15 = walking_radius(15)  # 1200m

    # ── CHIAMATE GOOGLE PLACES (una per categoria) ────────────────────────────
    raw_supermercati = gmaps_nearby(lat, lng, r10, 'supermarket')
    raw_convenience  = gmaps_nearby(lat, lng, r5,  'convenience_store')
    raw_farmacie     = gmaps_nearby(lat, lng, r5,  'pharmacy')
    raw_bar_cafe     = gmaps_nearby(lat, lng, r5,  'cafe')
    raw_ristoranti   = gmaps_nearby(lat, lng, r5,  'restaurant')
    raw_scuole       = gmaps_nearby(lat, lng, r5,  'school')
    raw_trasporti    = gmaps_nearby(lat, lng, r5,  'transit_station')
    raw_palestre     = gmaps_nearby(lat, lng, r5,  'gym')

    # ── CONCORRENTI: 3 chiamate separate per tipo ─────────────────────────────
    # 1) Self-service / coin laundry (competitor diretto)
    raw_self_service = gmaps_nearby(lat, lng, r15, 'laundry', keyword='self service lavanderia automatica gettoni')
    # 2) Lavanderia tradizionale / tintoria / stireria (competitor parziale)
    raw_tradizionale = gmaps_nearby(lat, lng, r15, 'laundry', keyword='tintoria lavasecco stireria')
    # 3) Lavanderia industriale / professionale (non competitor diretto)
    raw_industriale  = gmaps_nearby(lat, lng, r15, 'laundry', keyword='lavanderia industriale professionale biancheria')

    # Classificazione per nome: se una lavanderia appare in più ricerche, vince il tipo più specifico
    def classifica_lavanderia(nome: str) -> str:
        n = nome.lower()
        if any(k in n for k in ('self', 'gettoni', 'automatica', 'coin', 'lavomatic', 'speed queen', 'lava e asciuga')):
            return 'self_service'
        if any(k in n for k in ('tintoria', 'lavasecco', 'stireria', 'pulitura', 'pulito')):
            return 'tradizionale'
        if any(k in n for k in ('industriale', 'professionale', 'biancheria', 'alberghiera', 'hotel', 'noleggio')):
            return 'industriale'
        return 'self_service'  # default: trattala come competitor diretto

    # Unisci tutti i risultati lavanderie deduplicando per place_id
    lavanderie_viste = set()
    raw_lavanderie_classified = []
    for tipo, raw in [('self_service', raw_self_service),
                      ('tradizionale', raw_tradizionale),
                      ('industriale',  raw_industriale)]:
        for p in raw:
            pid = p.get('place_id', p.get('name', ''))
            if pid not in lavanderie_viste:
                lavanderie_viste.add(pid)
                # Riclassifica per nome per maggiore precisione
                tipo_reale = classifica_lavanderia(p.get('name', ''))
                raw_lavanderie_classified.append((p, tipo_reale))

    # ── POI + SEGNALI REALI ───────────────────────────────────────────────────
    pois = []
    contatori = {
        'supermercato': 0, 'ristorante': 0, 'bar_cafe': 0,
        'farmacia': 0, 'trasporti': 0, 'istruzione': 0,
        'competitor': 0, 'altro': 0,
    }
    servizi_400m     = 0
    concorrenti_500m = 0
    concorrenti_1km  = 0
    alta_affluenza   = []
    competitors_detail = []

    # Volume recensioni entro 400m (proxy traffico pedonale reale)
    recensioni_zona = 0
    # Catene GDO entro 500m (validazione zona)
    gdo_trovate = []

    def add_pois(places, categoria, colore, icon, max_serv=None):
        nonlocal servizi_400m, recensioni_zona
        for p in places:
            poi = place_to_poi(p, lat, lng, categoria, colore, icon)
            pois.append(poi)
            if max_serv and poi['distanza_m'] <= max_serv:
                servizi_400m += 1
                # Accumula recensioni per proxy traffico
                recensioni_zona += poi.get('user_ratings_total', 0) or 0
            contatori[categoria] = contatori.get(categoria, 0) + 1
            if categoria in ('supermercato', 'trasporti') and poi['distanza_m'] <= r5:
                alta_affluenza.append({'lat': poi['lat'], 'lng': poi['lng'],
                                       'nome': poi['nome'], 'tipo': categoria})
            # Rileva GDO
            if categoria == 'supermercato' and poi['distanza_m'] <= 500 and is_gdo(poi['nome']):
                gdo_trovate.append({'nome': poi['nome'], 'distanza_m': poi['distanza_m']})

    add_pois(raw_supermercati, 'supermercato', '#10b981', '🛒', 400)
    add_pois(raw_convenience,  'supermercato', '#10b981', '🏪', 400)
    add_pois(raw_farmacie,     'farmacia',     '#3b82f6', '💊', 400)
    add_pois(raw_bar_cafe,     'bar_cafe',     '#f59e0b', '☕', 400)
    add_pois(raw_ristoranti,   'ristorante',   '#ef4444', '🍽️', 400)
    add_pois(raw_scuole,       'istruzione',   '#8b5cf6', '🎓', 400)
    add_pois(raw_trasporti,    'trasporti',    '#06b6d4', '🚌', 400)
    add_pois(raw_palestre,     'altro',        '#ec4899', '💪', 400)

    # Aggiungi anche recensioni bar e ristoranti al conteggio traffico
    for p in raw_bar_cafe + raw_ristoranti:
        recensioni_zona += (p.get('user_ratings_total', 0) or 0)

    # Deduplicazione GDO
    gdo_nomi_visti = set()
    gdo_unici = []
    for g in gdo_trovate:
        key = g['nome'].lower()[:8]
        if key not in gdo_nomi_visti:
            gdo_nomi_visti.add(key)
            gdo_unici.append(g)
    gdo_500m = len(gdo_unici)

    # ── CONCORRENTI + HEATMAP ─────────────────────────────────────────────────
    concorrenti_per_tipo = {'self_service': 0, 'tradizionale': 0, 'industriale': 0}

    # Icone e colori per tipo
    TIPO_CONFIG = {
        'self_service': {'icon': '🪙', 'colore': '#dc2626', 'label': 'Self-service'},
        'tradizionale': {'icon': '👔', 'colore': '#f59e0b', 'label': 'Tradizionale/Tintoria'},
        'industriale':  {'icon': '🏭', 'colore': '#8b5cf6', 'label': 'Industriale'},
    }

    for p, tipo in raw_lavanderie_classified:
        cfg = TIPO_CONFIG[tipo]
        poi = place_to_poi(p, lat, lng, 'competitor', cfg['colore'], cfg['icon'])
        poi['tipo_lavanderia'] = tipo
        poi['tipo_label'] = cfg['label']
        pois.append(poi)
        contatori['competitor'] += 1
        concorrenti_per_tipo[tipo] += 1
        dist = poi['distanza_m']

        # Solo self-service e tradizionali contano come competitor per i contatori principali
        if tipo in ('self_service', 'tradizionale'):
            if dist <= 500:  concorrenti_500m += 1
            if dist <= 1000: concorrenti_1km  += 1

        if dist < 400:
            sat, cerchio_col, cerchio_fill = 'alta',  '#dc2626', 'rgba(220,38,38,0.18)'
        elif dist < 700:
            sat, cerchio_col, cerchio_fill = 'media', '#f59e0b', 'rgba(245,158,11,0.15)'
        else:
            sat, cerchio_col, cerchio_fill = 'bassa', '#10b981', 'rgba(16,185,129,0.12)'

        competitors_detail.append({
            'lat': poi['lat'], 'lng': poi['lng'],
            'nome': poi['nome'],
            'tipo_lavanderia': tipo,
            'tipo_label': cfg['label'],
            'distanza_m': int(dist),
            'rating': poi.get('rating'),
            'vicinity': poi.get('vicinity', ''),
            'raggio_copertura': 400,
            'saturazione': sat,
            'cerchio_colore': cerchio_col,
            'cerchio_fill':   cerchio_fill,
        })

    # ── DATI DEMOGRAFICI ──────────────────────────────────────────────────────
    demo          = get_demographic_data(citta, provincia)
    eta_media     = demo.get('eta_media', 46.4)
    reddito_medio = demo.get('reddito_medio', 19800)
    densita       = demo.get('densita', 200)

    assessment = get_market_assessment(
        eta_media, reddito_medio, densita,
        concorrenti_1km, recensioni_zona, gdo_500m
    )

    # ── POPOLAZIONE STIMATA ───────────────────────────────────────────────────
    area_3min  = math.pi * (r3  ** 2) / 1_000_000
    area_5min  = math.pi * (r5  ** 2) / 1_000_000
    area_10min = math.pi * (r10 ** 2) / 1_000_000
    pop_3min   = int(densita * area_3min)
    pop_5min   = int(densita * area_5min)
    pop_10min  = int(densita * area_10min)

    # ── STIMA CLIENTI ─────────────────────────────────────────────────────────
    stima = calcola_stima_clienti(
        pop_5min=pop_5min, pop_10min=pop_10min,
        densita=densita, concorrenti_500m=concorrenti_500m,
        concorrenti_1km=concorrenti_1km, servizi_400m=servizi_400m,
        reddito_medio=reddito_medio,
        recensioni_zona=recensioni_zona, gdo_500m=gdo_500m,
    )

    return jsonify({
        'pois':               pois,
        'competitors_detail': competitors_detail,
        'alta_affluenza':     alta_affluenza,
        'contatori':          contatori,
        'concorrenti_500m':   concorrenti_500m,
        'concorrenti_1km':    concorrenti_1km,
        'concorrenti_per_tipo': concorrenti_per_tipo,
        'servizi_400m':       servizi_400m,
        'pop_3min':           pop_3min,
        'pop_5min':           pop_5min,
        'pop_10min':          pop_10min,
        'score':              assessment['score'],
        'score_label':        assessment['label'],
        'score_colore':       assessment['colore'],
        'score_note':         assessment['note'],
        'segnali_reali': {
            'recensioni_zona': recensioni_zona,
            'gdo_500m':        gdo_500m,
            'gdo_lista':       gdo_unici,
        },
        'demografici': {
            'eta_media':     eta_media,
            'reddito_medio': reddito_medio,
            'densita':       int(densita),
            'fonte':         demo.get('fonte', 'N/D'),
            'citta':         demo.get('citta', citta),
        },
        'stima_clienti': stima,
    })


# ── CANONE STIMATO OMI ───────────────────────────────────────────────────────

@geo_bp.route('/api/canone-stimato')
@login_required
def canone_stimato():
    from services.istat import get_canone_stimato
    citta = request.args.get('citta', '')
    mq    = int(request.args.get('mq', 60) or 60)
    zona  = request.args.get('zona', 'semicentrale')
    return jsonify(get_canone_stimato(citta, mq, zona))


# ── DATI DEMOGRAFICI (endpoint separato, usato da esplora-zona) ───────────────

@geo_bp.route('/api/dati-demografici')
@login_required
def dati_demografici():
    citta    = request.args.get('citta', '')
    provincia = request.args.get('provincia', '')
    return jsonify(get_demographic_data(citta, provincia))


# ── ESPLORA CITTÀ (Scenario B — quartieri predefiniti) ───────────────────────

# Quartieri principali per densità residenziale — aggiornabili
QUARTIERI_CITTA = {
    'roma': [
        'Roma Prati', 'Roma Trastevere', 'Roma Ostiense', 'Roma EUR',
        'Roma Pigneto', 'Roma Centocelle', 'Roma Tiburtino', 'Roma Prenestino',
        'Roma Nomentano', 'Roma Flaminio', 'Roma Trionfale', 'Roma Monteverde',
        'Roma Garbatella', 'Roma Testaccio', 'Roma San Giovanni',
        'Roma Tuscolano', 'Roma Appio Latino', 'Roma Portuense',
        'Roma Aurelio', 'Roma Trieste', 'Roma Salario', 'Roma Parioli',
    ],
    'milano': [
        'Milano Navigli', 'Milano Isola', 'Milano NoLo', 'Milano Lambrate',
        'Milano Bovisa', 'Milano Lorenteggio', 'Milano Porta Romana',
        'Milano Città Studi', 'Milano Loreto', 'Milano Affori',
        'Milano Brera', 'Milano Porta Venezia', 'Milano Bicocca',
        'Milano Famagosta', 'Milano Turro',
    ],
    'napoli': [
        'Napoli Chiaia', 'Napoli Vomero', 'Napoli Fuorigrotta',
        'Napoli Posillipo', 'Napoli Bagnoli', 'Napoli Secondigliano',
        'Napoli Ponticelli', 'Napoli San Giovanni a Teduccio',
        'Napoli Centro Storico', 'Napoli Mergellina',
        'Napoli Pianura', 'Napoli Chiaiano',
    ],
    'torino': [
        'Torino Crocetta', 'Torino San Salvario', 'Torino Lingotto',
        'Torino Mirafiori', 'Torino Borgo Po', 'Torino Aurora',
        'Torino Barriera di Milano', 'Torino Pozzo Strada',
        'Torino Parella', 'Torino Madonna di Campagna',
    ],
    'firenze': [
        'Firenze Oltrarno', 'Firenze Campo di Marte', 'Firenze Rifredi',
        'Firenze Isolotto', 'Firenze Gavinana', 'Firenze Novoli',
        'Firenze Le Cure', 'Firenze Coverciano',
    ],
    'bologna': [
        'Bologna Bolognina', 'Bologna San Donato', 'Bologna Mazzini',
        'Bologna Porto Saragozza', 'Bologna Savena',
        'Bologna Borgo Panigale', 'Bologna Navile',
    ],
    'genova': [
        'Genova Marassi', 'Genova Sestri Ponente', 'Genova Sampierdarena',
        'Genova Rivarolo', 'Genova Molassana', 'Genova Voltri',
        'Genova Nervi', 'Genova Cornigliano',
    ],
    'palermo': [
        'Palermo Noce', 'Palermo Brancaccio', 'Palermo Zisa',
        'Palermo Calatafimi', 'Palermo Oreto', 'Palermo Uditore',
        'Palermo Palagonia', 'Palermo Villagrazia',
    ],
    'catania': [
        'Catania Librino', 'Catania San Giovanni Galermo', 'Catania Nesima',
        'Catania Cibali', 'Catania Barriera', 'Catania Ognina',
    ],
    'verona': [
        'Verona Golosine', 'Verona Borgo Trento', 'Verona Santa Lucia',
        'Verona Borgo Roma', 'Verona Quinzano', 'Verona Montorio',
    ],
    'venezia': [
        'Mestre Centro', 'Mestre Marghera', 'Mestre Favaro',
        'Mestre Zelarino', 'Venezia Lido', 'Mestre Chirignago',
    ],
    'padova': [
        'Padova Arcella', 'Padova Pontevigodarzere', 'Padova Voltabarozzo',
        'Padova Guizza', 'Padova Camin', 'Padova Montà',
    ],
    'trieste': [
        'Trieste Rozzol', 'Trieste Roiano', 'Trieste Valmaura',
        'Trieste Chiarbola', 'Trieste Servola', 'Trieste Opicina',
    ],
    'bari': [
        'Bari Japigia', 'Bari San Paolo', 'Bari Madonnella',
        'Bari Carrassi', 'Bari Poggiofranco', 'Bari Libertà',
    ],
    'catanzaro': [
        'Catanzaro Lido', 'Catanzaro Nord', 'Catanzaro Sud',
        'Catanzaro Est', 'Catanzaro Ovest',
    ],
}


@geo_bp.route('/api/esplora-citta')
@login_required
def esplora_citta():
    """Scenario B: analizza i quartieri principali di una città"""
    citta_input = request.args.get('citta', '').lower().strip()
    provincia   = request.args.get('provincia', '')

    # Trova la lista quartieri per la città richiesta
    quartieri = None
    for key, lista in QUARTIERI_CITTA.items():
        if key in citta_input or citta_input in key:
            quartieri = lista
            break

    if not quartieri:
        # Fallback: genera una griglia più ampia attorno al centro città
        # Geocodifica prima la città
        try:
            r = requests.get(GEOCODE_URL, params={
                'address': citta_input + ', Italia',
                'key': GMAPS_KEY, 'language': 'it', 'region': 'it',
            }, timeout=10)
            data = r.json()
            if data.get('status') == 'OK' and data['results']:
                loc = data['results'][0]['geometry']['location']
                clat, clng = loc['lat'], loc['lng']
                # Griglia 4×4 con step più ampio per città non in lista
                quartieri_gen = []
                for di in range(-2, 3):
                    for dj in range(-2, 3):
                        if abs(di) + abs(dj) <= 3:  # evita angoli troppo lontani
                            quartieri_gen.append(
                                f'{citta_input.title()} zona {di},{dj}'
                            )
                # Usa geocodifica diretta con coordinate
                return _analizza_quartieri_coords(
                    clat, clng, citta_input, provincia, step=0.012
                )
        except Exception:
            pass
        return jsonify({'error': f'Città "{citta_input}" non in archivio. Prova con un quartiere specifico.'}), 400

    demo          = get_demographic_data(citta_input.title(), provincia)
    eta_media     = demo.get('eta_media', 46.4)
    reddito_medio = demo.get('reddito_medio', 19800)
    densita       = demo.get('densita', 200)

    zone = []
    for q in quartieri:
        try:
            r = requests.get(GEOCODE_URL, params={
                'address': q + ', Italia',
                'key': GMAPS_KEY, 'language': 'it', 'region': 'it',
            }, timeout=8)
            data = r.json()
            if data.get('status') != 'OK' or not data['results']:
                continue
            loc  = data['results'][0]['geometry']['location']
            zlat, zlng = loc['lat'], loc['lng']

            raw_self = gmaps_nearby(zlat, zlng, 800, 'laundry',
                                    keyword='self service automatica gettoni')
            raw_trad = gmaps_nearby(zlat, zlng, 800, 'laundry',
                                    keyword='tintoria lavasecco')
            visti = set(); n_self = 0; n_trad = 0
            for p in raw_self:
                pid = p.get('place_id', p.get('name',''))
                if pid not in visti: visti.add(pid); n_self += 1
            for p in raw_trad:
                pid = p.get('place_id', p.get('name',''))
                if pid not in visti: visti.add(pid); n_trad += 1
            n_conc = n_self + n_trad

            raw_bar  = gmaps_nearby(zlat, zlng, 400, 'cafe')
            raw_rest = gmaps_nearby(zlat, zlng, 400, 'restaurant')
            raw_sup  = gmaps_nearby(zlat, zlng, 400, 'supermarket')
            rec_zona = sum(p.get('user_ratings_total', 0) or 0
                           for p in raw_bar + raw_rest + raw_sup)
            gdo_z    = sum(1 for p in raw_sup if is_gdo(p.get('name', '')))

            r5 = walking_radius(5)
            pop_stimata = int(densita * math.pi * (r5**2) / 1_000_000)

            a = get_market_assessment(eta_media, reddito_medio, densita,
                                      n_conc, rec_zona, gdo_z)

            from services.istat import calcola_stima_clienti
            stima = calcola_stima_clienti(
                pop_5min=pop_stimata,
                pop_10min=int(densita * math.pi * (walking_radius(10)**2) / 1_000_000),
                densita=densita,
                concorrenti_500m=n_conc,
                concorrenti_1km=n_conc,
                servizi_400m=len(raw_bar)+len(raw_rest)+len(raw_sup),
                reddito_medio=reddito_medio,
                recensioni_zona=rec_zona,
                gdo_500m=gdo_z,
            )

            zone.append({
                'lat': zlat, 'lng': zlng,
                'nome': q,
                'score': a['score'], 'label': a['label'], 'colore': a['colore'],
                'concorrenti': n_conc, 'self_service': n_self, 'tradizionali': n_trad,
                'recensioni': rec_zona, 'gdo': gdo_z,
                'pop_5min': pop_stimata,
                'clienti_giorno': stima.get('scenario_realistico', 0),
                'clienti_pess':   stima.get('scenario_pessimistico', 0),
                'clienti_ott':    stima.get('scenario_ottimistico', 0),
            })
        except Exception:
            continue

    if not zone:
        return jsonify({'error': 'Nessuna zona analizzata. Riprova.'}), 500

    zone.sort(key=lambda z: z['score'], reverse=True)
    centro = zone[0] if zone else {'lat': 41.9, 'lng': 12.5}

    return jsonify({
        'zone': zone,
        'centro_lat': centro['lat'],
        'centro_lng': centro['lng'],
        'totale_quartieri': len(quartieri),
        'analizzati': len(zone),
        'demo': {
            'eta_media': eta_media,
            'reddito_medio': reddito_medio,
            'densita': int(densita),
            'fonte': 'ISTAT Censimento 2021',
        }
    })


def _analizza_quartieri_coords(clat, clng, citta, provincia, step=0.012):
    """Fallback: griglia attorno al centro per città non in lista"""
    demo = get_demographic_data(citta.title(), provincia)
    eta_media = demo.get('eta_media', 46.4)
    reddito_medio = demo.get('reddito_medio', 19800)
    densita = demo.get('densita', 200)
    zone = []
    for di in range(-2, 3):
        for dj in range(-2, 3):
            if abs(di) + abs(dj) > 3: continue
            zlat = clat + di * step
            zlng = clng + dj * step
            raw_self = gmaps_nearby(zlat, zlng, 800, 'laundry',
                                    keyword='self service automatica')
            raw_trad = gmaps_nearby(zlat, zlng, 800, 'laundry',
                                    keyword='tintoria lavasecco')
            visti = set(); n_self = 0; n_trad = 0
            for p in raw_self + raw_trad:
                pid = p.get('place_id', p.get('name',''))
                if pid not in visti:
                    visti.add(pid)
                    if p in raw_self: n_self += 1
                    else: n_trad += 1
            n_conc = n_self + n_trad
            raw_bar  = gmaps_nearby(zlat, zlng, 400, 'cafe')
            raw_rest = gmaps_nearby(zlat, zlng, 400, 'restaurant')
            raw_sup  = gmaps_nearby(zlat, zlng, 400, 'supermarket')
            rec_zona = sum(p.get('user_ratings_total', 0) or 0
                           for p in raw_bar + raw_rest + raw_sup)
            gdo_z = sum(1 for p in raw_sup if is_gdo(p.get('name', '')))
            r5 = walking_radius(5)
            pop_stimata = int(densita * math.pi * (r5**2) / 1_000_000)
            a = get_market_assessment(eta_media, reddito_medio, densita,
                                      n_conc, rec_zona, gdo_z)
            from services.istat import calcola_stima_clienti
            stima = calcola_stima_clienti(
                pop_5min=pop_stimata,
                pop_10min=int(densita * math.pi * (walking_radius(10)**2) / 1_000_000),
                densita=densita, concorrenti_500m=n_conc, concorrenti_1km=n_conc,
                servizi_400m=len(raw_bar)+len(raw_rest)+len(raw_sup),
                reddito_medio=reddito_medio, recensioni_zona=rec_zona, gdo_500m=gdo_z,
            )
            zone.append({
                'lat': zlat, 'lng': zlng, 'nome': f'{citta.title()} zona',
                'score': a['score'], 'label': a['label'], 'colore': a['colore'],
                'concorrenti': n_conc, 'self_service': n_self, 'tradizionali': n_trad,
                'recensioni': rec_zona, 'gdo': gdo_z, 'pop_5min': pop_stimata,
                'clienti_giorno': stima.get('scenario_realistico', 0),
                'clienti_pess': stima.get('scenario_pessimistico', 0),
                'clienti_ott': stima.get('scenario_ottimistico', 0),
            })
    zone.sort(key=lambda z: z['score'], reverse=True)
    centro = zone[0] if zone else {'lat': clat, 'lng': clng}
    from flask import jsonify as _j
    return _j({
        'zone': zone, 'centro_lat': centro['lat'], 'centro_lng': centro['lng'],
        'totale_quartieri': len(zone), 'analizzati': len(zone),
        'demo': {'eta_media': eta_media, 'reddito_medio': reddito_medio,
                 'densita': int(densita), 'fonte': 'ISTAT Censimento 2021'}
    })


# ── ESPLORA ZONA (Scenario A — griglia 3x3 attorno a punto specifico) ────────

@geo_bp.route('/api/esplora-zona')
@login_required
def esplora_zona():
    lat       = float(request.args.get('lat', 0))
    lng       = float(request.args.get('lng', 0))
    citta     = request.args.get('citta', '')
    provincia = request.args.get('provincia', '')
    if not lat or not lng:
        return jsonify({'error': 'Coordinate mancanti'}), 400

    demo          = get_demographic_data(citta, provincia)
    eta_media     = demo.get('eta_media', 46.4)
    reddito_medio = demo.get('reddito_medio', 19800)
    densita       = demo.get('densita', 200)

    # Griglia 3×3 centrata sull'indirizzo — passo ~700m
    # 9 zone invece di 25: più veloce, meno chiamate API, risultati più leggibili
    step = 0.008   # ~700m per grado a latitudini italiane
    zone = []
    for di in range(-1, 2):
        for dj in range(-1, 2):
            zlat = lat + di * step
            zlng = lng + dj * step

            # Concorrenti: 3 keyword separate per classificare i tipi
            raw_self    = gmaps_nearby(zlat, zlng, 800, 'laundry',
                                       keyword='self service automatica gettoni')
            raw_trad    = gmaps_nearby(zlat, zlng, 800, 'laundry',
                                       keyword='tintoria lavasecco stireria')
            # Deduplicazione per place_id
            visti = set()
            n_self = 0; n_trad = 0
            for p in raw_self:
                pid = p.get('place_id', p.get('name',''))
                if pid not in visti:
                    visti.add(pid); n_self += 1
            for p in raw_trad:
                pid = p.get('place_id', p.get('name',''))
                if pid not in visti:
                    visti.add(pid); n_trad += 1
            n_conc = n_self + n_trad   # totale competitor (escluse industriali)

            # Traffico reale: usa bar, ristoranti, negozi (più affidabile di 'store')
            raw_bar  = gmaps_nearby(zlat, zlng, 400, 'cafe')
            raw_rest = gmaps_nearby(zlat, zlng, 400, 'restaurant')
            raw_sup  = gmaps_nearby(zlat, zlng, 400, 'supermarket')
            rec_zona = sum(p.get('user_ratings_total', 0) or 0
                           for p in raw_bar + raw_rest + raw_sup)
            gdo_z    = sum(1 for p in raw_sup if is_gdo(p.get('name', '')))

            # Stima popolazione nel raggio 5min (~400m)
            r5 = walking_radius(5)
            area_5min = math.pi * (r5 ** 2) / 1_000_000
            pop_stimata = int(densita * area_5min)

            a = get_market_assessment(eta_media, reddito_medio, densita,
                                      n_conc, rec_zona, gdo_z)

            # Stima clienti/giorno per questa zona specifica
            from services.istat import calcola_stima_clienti
            stima = calcola_stima_clienti(
                pop_5min=pop_stimata,
                pop_10min=int(densita * math.pi * (walking_radius(10)**2) / 1_000_000),
                densita=densita,
                concorrenti_500m=n_conc,
                concorrenti_1km=n_conc,
                servizi_400m=len(raw_bar)+len(raw_rest)+len(raw_sup),
                reddito_medio=reddito_medio,
                recensioni_zona=rec_zona,
                gdo_500m=gdo_z,
            )

            zone.append({
                'lat':          zlat,
                'lng':          zlng,
                'score':        a['score'],
                'label':        a['label'],
                'colore':       a['colore'],
                'concorrenti':  n_conc,
                'self_service': n_self,
                'tradizionali': n_trad,
                'recensioni':   rec_zona,
                'gdo':          gdo_z,
                'pop_5min':     pop_stimata,
                'clienti_giorno': stima.get('scenario_realistico', 0),
                'clienti_pess':   stima.get('scenario_pessimistico', 0),
                'clienti_ott':    stima.get('scenario_ottimistico', 0),
            })

    zone.sort(key=lambda z: z['score'], reverse=True)
    return jsonify({
        'zone': zone,
        'centro_lat': lat,
        'centro_lng': lng,
        'demo': {
            'eta_media':     eta_media,
            'reddito_medio': reddito_medio,
            'densita':       int(densita),
            'note':          '',
            'fonte':         'ISTAT Censimento 2021',
        }
    })
