from flask import Blueprint, request, jsonify
from flask_login import login_required
import requests
import json
import math

geo_bp = Blueprint('geo', __name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org"


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def walking_radius(minutes):
    return minutes * 80


@geo_bp.route('/api/geocode')
@login_required
def geocode():
    address = request.args.get('address', '')
    if not address:
        return jsonify({'error': 'Indirizzo mancante'}), 400
    try:
        r = requests.get(
            f"{NOMINATIM_URL}/search",
            params={'q': address, 'format': 'json', 'limit': 1, 'countrycodes': 'it'},
            headers={'User-Agent': 'BIOLavaTU/1.0'},
            timeout=10
        )
        data = r.json()
        if data:
            return jsonify({'lat': float(data[0]['lat']), 'lon': float(data[0]['lon']), 'display': data[0]['display_name']})
        return jsonify({'error': 'Indirizzo non trovato'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@geo_bp.route('/api/zona-analisi')
@login_required
def zona_analisi():
    lat = float(request.args.get('lat', 0))
    lng = float(request.args.get('lng', 0))
    if not lat or not lng:
        return jsonify({'error': 'Coordinate mancanti'}), 400

    r3 = walking_radius(3)    # 240m
    r5 = walking_radius(5)    # 400m
    r10 = walking_radius(10)  # 800m
    r15 = walking_radius(15)  # 1200m
    r1km = 1000               # esatto 1km

    # Query Overpass estesa
    query = f"""
    [out:json][timeout:45];
    (
      node["shop"="supermarket"](around:{r10},{lat},{lng});
      node["shop"="convenience"](around:{r5},{lat},{lng});
      node["shop"="mall"](around:{r10},{lat},{lng});
      node["shop"="department_store"](around:{r10},{lat},{lng});
      node["amenity"="bank"](around:{r5},{lat},{lng});
      node["amenity"="post_office"](around:{r5},{lat},{lng});
      node["amenity"="pharmacy"](around:{r5},{lat},{lng});
      node["amenity"="cafe"](around:{r5},{lat},{lng});
      node["amenity"="restaurant"](around:{r5},{lat},{lng});
      node["amenity"="fast_food"](around:{r5},{lat},{lng});
      node["amenity"="bar"](around:{r5},{lat},{lng});
      node["amenity"="school"](around:{r5},{lat},{lng});
      node["amenity"="university"](around:{r10},{lat},{lng});
      node["amenity"="gym"](around:{r5},{lat},{lng});
      node["leisure"="fitness_centre"](around:{r5},{lat},{lng});
      node["amenity"="hospital"](around:{r10},{lat},{lng});
      node["amenity"="marketplace"](around:{r5},{lat},{lng});
      node["public_transport"="stop_position"](around:{r5},{lat},{lng});
      node["highway"="bus_stop"](around:{r5},{lat},{lng});
      node["railway"="station"](around:{r10},{lat},{lng});
      node["railway"="subway_entrance"](around:{r5},{lat},{lng});
      node["shop"="laundry"](around:{r15},{lat},{lng});
      node["shop"="dry_cleaning"](around:{r15},{lat},{lng});
      node["amenity"="laundry"](around:{r15},{lat},{lng});
    );
    out body;
    """

    pois = []
    competitors_500m = 0
    competitors_1km = 0
    servizi_400m = 0
    alta_affluenza = []  # cluster ad alta affluenza

    # Contatori per categoria
    contatori = {
        'supermercato': 0, 'ristorante': 0, 'bar_cafe': 0,
        'farmacia': 0, 'trasporti': 0, 'istruzione': 0,
        'competitor': 0, 'altro': 0
    }

    try:
        r = requests.post(OVERPASS_URL, data={'data': query}, timeout=45)
        elements = r.json().get('elements', [])

        for el in elements:
            tags = el.get('tags', {})
            elat = el.get('lat', 0)
            elng = el.get('lon', 0)
            if not elat or not elng:
                continue
            dist = haversine(lat, lng, elat, elng)
            shop = tags.get('shop', '')
            amenity = tags.get('amenity', '')
            leisure = tags.get('leisure', '')
            public_transport = tags.get('public_transport', '')
            highway = tags.get('highway', '')
            railway = tags.get('railway', '')
            nome = tags.get('name', 'N/D')

            # Classificazione dettagliata
            if shop in ('laundry', 'dry_cleaning') or amenity == 'laundry':
                tipo = 'competitor'
                colore = 'rosso'
                icona = '🔴'
                affluenza = 'alta'
                contatori['competitor'] += 1
                if dist <= 500:
                    competitors_500m += 1
                if dist <= 1000:
                    competitors_1km += 1

            elif shop in ('supermarket', 'mall', 'department_store'):
                tipo = 'supermercato'
                colore = 'verde'
                icona = '🟢'
                affluenza = 'molto_alta'
                contatori['supermercato'] += 1
                if dist <= 400:
                    servizi_400m += 1
                alta_affluenza.append({'lat': elat, 'lng': elng, 'nome': nome, 'tipo': tipo})

            elif shop == 'convenience':
                tipo = 'negozio'
                colore = 'verde'
                icona = '🟢'
                affluenza = 'media'
                contatori['supermercato'] += 1
                if dist <= 400:
                    servizi_400m += 1

            elif amenity in ('restaurant', 'fast_food'):
                tipo = 'ristorante'
                colore = 'arancio'
                icona = '🟠'
                affluenza = 'alta'
                contatori['ristorante'] += 1
                if dist <= 400:
                    servizi_400m += 1
                    alta_affluenza.append({'lat': elat, 'lng': elng, 'nome': nome, 'tipo': tipo})

            elif amenity in ('cafe', 'bar'):
                tipo = 'bar/caffè'
                colore = 'arancio'
                icona = '🟠'
                affluenza = 'alta'
                contatori['bar_cafe'] += 1
                if dist <= 400:
                    servizi_400m += 1

            elif amenity == 'pharmacy':
                tipo = 'farmacia'
                colore = 'verde_chiaro'
                icona = '💚'
                affluenza = 'alta'
                contatori['farmacia'] += 1
                if dist <= 400:
                    servizi_400m += 1

            elif amenity in ('bank', 'post_office'):
                tipo = 'banca/posta'
                colore = 'blu'
                icona = '🔵'
                affluenza = 'media'
                if dist <= 400:
                    servizi_400m += 1
                contatori['altro'] += 1

            elif amenity in ('school', 'university'):
                tipo = 'istruzione'
                colore = 'viola'
                icona = '🟣'
                affluenza = 'alta'
                contatori['istruzione'] += 1
                if dist <= 400:
                    servizi_400m += 1
                alta_affluenza.append({'lat': elat, 'lng': elng, 'nome': nome, 'tipo': tipo})

            elif amenity in ('gym',) or leisure == 'fitness_centre':
                tipo = 'palestra'
                colore = 'viola'
                icona = '🟣'
                affluenza = 'alta'
                contatori['istruzione'] += 1
                if dist <= 400:
                    servizi_400m += 1

            elif amenity == 'hospital':
                tipo = 'ospedale'
                colore = 'rosso_chiaro'
                icona = '🔴'
                affluenza = 'molto_alta'
                alta_affluenza.append({'lat': elat, 'lng': elng, 'nome': nome, 'tipo': tipo})
                contatori['altro'] += 1

            elif amenity == 'marketplace':
                tipo = 'mercato'
                colore = 'giallo'
                icona = '🟡'
                affluenza = 'molto_alta'
                alta_affluenza.append({'lat': elat, 'lng': elng, 'nome': nome, 'tipo': tipo})
                contatori['altro'] += 1

            elif highway == 'bus_stop' or public_transport == 'stop_position':
                tipo = 'fermata bus'
                colore = 'azzurro'
                icona = '🔵'
                affluenza = 'alta'
                contatori['trasporti'] += 1
                if dist <= 400:
                    servizi_400m += 1

            elif railway in ('station', 'subway_entrance'):
                tipo = 'stazione'
                colore = 'azzurro'
                icona = '🔵'
                affluenza = 'molto_alta'
                contatori['trasporti'] += 1
                alta_affluenza.append({'lat': elat, 'lng': elng, 'nome': nome, 'tipo': tipo})

            else:
                continue

            pois.append({
                'nome': nome,
                'tipo': tipo,
                'colore': colore,
                'icona': icona,
                'affluenza': affluenza,
                'lat': elat,
                'lng': elng,
                'dist': round(dist),
            })

    except Exception as e:
        print(f"[GEO] Overpass error: {e}")

    # Stima popolazione
    pop_3min = _stima_pop(r3)
    pop_5min = _stima_pop(r5)
    pop_10min = _stima_pop(r10)
    pop_1km = _stima_pop(r1km)

    # Traffico pedonale stimato
    traffico = _stima_traffico(contatori['trasporti'], contatori['ristorante'] + contatori['bar_cafe'], pop_5min)

    # Score zona
    score = _calcola_score(pop_5min, competitors_500m, servizi_400m, contatori['trasporti'])
    label = _score_label(score)

    return jsonify({
        'lat': lat,
        'lng': lng,
        'pop_3min': pop_3min,
        'pop_5min': pop_5min,
        'pop_10min': pop_10min,
        'pop_1km': pop_1km,
        'competitors_500m': competitors_500m,
        'competitors_1km': competitors_1km,
        'servizi_400m': servizi_400m,
        'score': round(score, 1),
        'label': label,
        'traffico': traffico,
        'pois': pois,
        'alta_affluenza': alta_affluenza[:20],
        'contatori': contatori,
        'r3': r3,
        'r5': r5,
        'r10': r10,
        'r1km': r1km,
    })


def _stima_pop(raggio_m):
    area_km2 = math.pi * (raggio_m / 1000) ** 2
    return int(area_km2 * 2500)


def _stima_traffico(trasporti, food, pop):
    if trasporti >= 3 and food >= 5 and pop > 5000:
        return 'Molto alto'
    elif trasporti >= 2 or food >= 3 or pop > 3000:
        return 'Alto'
    elif trasporti >= 1 or food >= 1 or pop > 1500:
        return 'Medio'
    return 'Basso'


def _calcola_score(pop_5min, concorrenti_500m, servizi_400m, trasporti):
    score = 0
    if pop_5min > 8000:
        score += 40
    elif pop_5min > 5000:
        score += 30
    elif pop_5min > 3000:
        score += 20
    else:
        score += 10
    score += min(servizi_400m * 3, 30)
    score += min(trasporti * 5, 15)
    score -= min(concorrenti_500m * 10, 20)
    return max(0, min(100, score))


def _score_label(score):
    if score >= 75:
        return 'Eccellente'
    elif score >= 55:
        return 'Ottima'
    elif score >= 35:
        return 'Buona'
    elif score >= 20:
        return 'Discreta'
    return 'Scarsa'


@geo_bp.route('/api/dati-demografici')
@login_required
def dati_demografici():
    """Restituisce dati demografici ISTAT per città/provincia."""
    citta = request.args.get('citta', '')
    provincia = request.args.get('provincia', '')
    lat = float(request.args.get('lat', 0) or 0)
    lng = float(request.args.get('lng', 0) or 0)
    concorrenti = int(request.args.get('concorrenti', 0) or 0)

    from services.istat import get_demographic_data, get_market_assessment
    demo = get_demographic_data(citta, provincia)
    market = get_market_assessment(
        demo['eta_media'], demo['reddito_medio'],
        demo['densita'], concorrenti
    )
    return jsonify({**demo, 'market': market})


@geo_bp.route('/api/esplora-zona')
@login_required
def esplora_zona():
    """
    Data una città, trova le zone migliori per aprire una lavanderia.
    Divide la città in una griglia e valuta ogni cella.
    """
    citta = request.args.get('citta', '')
    if not citta:
        return jsonify({'error': 'Città mancante'}), 400

    # Geocodifica la città
    try:
        r = requests.get(
            f"{NOMINATIM_URL}/search",
            params={'q': citta + ', Italia', 'format': 'json', 'limit': 1},
            headers={'User-Agent': 'BIOLavaTU/1.0'},
            timeout=10
        )
        data = r.json()
        if not data:
            return jsonify({'error': 'Città non trovata'}), 404
        centro_lat = float(data[0]['lat'])
        centro_lng = float(data[0]['lon'])
        display = data[0]['display_name']
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Griglia 3x3 attorno al centro (ogni cella ~600m)
    step = 0.005  # ~550m
    punti = []
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            punti.append((centro_lat + dy * step, centro_lng + dx * step))

    # Per ogni punto, query Overpass leggera (solo laundries e supermercati)
    risultati = []
    query_base = """
    [out:json][timeout:20];
    (
      node["shop"~"laundry|dry_cleaning"](around:600,{lat},{lng});
      node["amenity"="laundry"](around:600,{lat},{lng});
      node["shop"~"supermarket|mall"](around:400,{lat},{lng});
      node["amenity"~"restaurant|cafe|fast_food"](around:400,{lat},{lng});
      node["highway"="bus_stop"](around:400,{lat},{lng});
      node["railway"~"station|subway_entrance"](around:600,{lat},{lng});
    );
    out body;
    """

    for plat, plng in punti:
        try:
            r = requests.post(OVERPASS_URL,
                data={'data': query_base.format(lat=plat, lng=plng)},
                timeout=20)
            elements = r.json().get('elements', [])
            lavanderie = sum(1 for e in elements if
                e.get('tags', {}).get('shop') in ('laundry', 'dry_cleaning') or
                e.get('tags', {}).get('amenity') == 'laundry')
            supermercati = sum(1 for e in elements if
                e.get('tags', {}).get('shop') in ('supermarket', 'mall'))
            food = sum(1 for e in elements if
                e.get('tags', {}).get('amenity') in ('restaurant', 'cafe', 'fast_food'))
            trasporti = sum(1 for e in elements if
                e.get('tags', {}).get('highway') == 'bus_stop' or
                e.get('tags', {}).get('railway') in ('station', 'subway_entrance'))
            pop_est = _stima_pop(600)
            score = _calcola_score(pop_est, lavanderie, supermercati + food, trasporti)
            risultati.append({
                'lat': plat, 'lng': plng,
                'score': round(score, 1),
                'label': _score_label(score),
                'lavanderie': lavanderie,
                'supermercati': supermercati,
                'food': food,
                'trasporti': trasporti,
            })
        except Exception:
            risultati.append({'lat': plat, 'lng': plng, 'score': 0, 'label': 'N/D',
                'lavanderie': 0, 'supermercati': 0, 'food': 0, 'trasporti': 0})

    # Ordina per score
    risultati.sort(key=lambda x: x['score'], reverse=True)

    from services.istat import get_demographic_data
    demo = get_demographic_data(citta)

    return jsonify({
        'citta': citta,
        'display': display,
        'centro_lat': centro_lat,
        'centro_lng': centro_lng,
        'zone': risultati,
        'demo': demo,
        'migliore': risultati[0] if risultati else None,
    })
