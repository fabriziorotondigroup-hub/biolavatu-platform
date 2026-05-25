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
    raw_lavanderie   = gmaps_nearby(lat, lng, r15, 'laundry')

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
    for p in raw_lavanderie:
        poi = place_to_poi(p, lat, lng, 'competitor', '#dc2626', '🏁')
        pois.append(poi)
        contatori['competitor'] += 1
        dist = poi['distanza_m']
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
    area_5min  = math.pi * (r5  ** 2) / 1_000_000
    area_10min = math.pi * (r10 ** 2) / 1_000_000
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
        'servizi_400m':       servizi_400m,
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


# ── ESPLORA ZONA (griglia per tab "Esplora" step 2) ──────────────────────────

@geo_bp.route('/api/esplora-zona')
@login_required
def esplora_zona():
    lat      = float(request.args.get('lat', 0))
    lng      = float(request.args.get('lng', 0))
    citta    = request.args.get('citta', '')
    provincia = request.args.get('provincia', '')
    if not lat or not lng:
        return jsonify({'error': 'Coordinate mancanti'}), 400

    demo          = get_demographic_data(citta, provincia)
    eta_media     = demo.get('eta_media', 46.4)
    reddito_medio = demo.get('reddito_medio', 19800)
    densita       = demo.get('densita', 200)

    step = 0.006
    zone = []
    for di in range(-2, 3):
        for dj in range(-2, 3):
            zlat = lat + di * step
            zlng = lng + dj * step

            conc_raw  = gmaps_nearby(zlat, zlng, 800, 'laundry')
            n_conc    = len(conc_raw)
            store_raw = gmaps_nearby(zlat, zlng, 400, 'store')
            rec_zona  = sum(p.get('user_ratings_total', 0) or 0 for p in store_raw)
            gdo_z     = sum(1 for p in store_raw if is_gdo(p.get('name', '')))

            a = get_market_assessment(eta_media, reddito_medio, densita,
                                      n_conc, rec_zona, gdo_z)
            zone.append({
                'lat': zlat, 'lng': zlng,
                'score':       a['score'],
                'label':       a['label'],
                'colore':      a['colore'],
                'concorrenti': n_conc,
                'recensioni':  rec_zona,
                'gdo':         gdo_z,
            })

    zone.sort(key=lambda z: z['score'], reverse=True)
    return jsonify({
        'zone': zone,
        'centro_lat': lat,
        'centro_lng': lng,
        'demo': {
            'eta_media': eta_media,
            'reddito_medio': reddito_medio,
            'densita': int(densita),
            'note': '',
            'fonte': 'ISTAT Censimento 2021',
        }
    })
