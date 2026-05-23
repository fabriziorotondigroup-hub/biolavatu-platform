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
    """Raggio in metri per camminata a ~80m/min"""
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

    r3 = walking_radius(3)   # 240m
    r5 = walking_radius(5)   # 400m
    r10 = walking_radius(10) # 800m

    # Query Overpass per POI
    query = f"""
    [out:json][timeout:30];
    (
      node["shop"="supermarket"](around:{r5},{lat},{lng});
      node["shop"="convenience"](around:{r5},{lat},{lng});
      node["amenity"="bank"](around:{r5},{lat},{lng});
      node["amenity"="post_office"](around:{r5},{lat},{lng});
      node["amenity"="pharmacy"](around:{r5},{lat},{lng});
      node["amenity"="cafe"](around:{r5},{lat},{lng});
      node["amenity"="restaurant"](around:{r5},{lat},{lng});
      node["amenity"="school"](around:{r5},{lat},{lng});
      node["amenity"="gym"](around:{r5},{lat},{lng});
      node["shop"="laundry"](around:1000,{lat},{lng});
      node["shop"="dry_cleaning"](around:1000,{lat},{lng});
      node["amenity"="laundry"](around:1000,{lat},{lng});
    );
    out body;
    """

    pois = []
    competitors_500m = 0
    competitors_1km = 0
    servizi_400m = 0

    try:
        r = requests.post(OVERPASS_URL, data={'data': query}, timeout=30)
        elements = r.json().get('elements', [])

        for el in elements:
            tags = el.get('tags', {})
            elat = el.get('lat', 0)
            elng = el.get('lon', 0)
            dist = haversine(lat, lng, elat, elng)

            # Classifica
            shop = tags.get('shop', '')
            amenity = tags.get('amenity', '')
            nome = tags.get('name', 'N/D')

            if shop in ('laundry', 'dry_cleaning') or amenity == 'laundry':
                tipo = 'competitor'
                colore = 'rosso'
                if dist <= 500:
                    competitors_500m += 1
                if dist <= 1000:
                    competitors_1km += 1
            elif shop in ('supermarket', 'convenience'):
                tipo = 'supermercato'
                colore = 'verde'
                if dist <= 400:
                    servizi_400m += 1
            elif amenity in ('bank', 'post_office'):
                tipo = amenity
                colore = 'blu'
                if dist <= 400:
                    servizi_400m += 1
            elif amenity == 'pharmacy':
                tipo = 'farmacia'
                colore = 'verde'
                if dist <= 400:
                    servizi_400m += 1
            elif amenity in ('cafe', 'restaurant'):
                tipo = amenity
                colore = 'arancio'
                if dist <= 400:
                    servizi_400m += 1
            elif amenity in ('school', 'gym'):
                tipo = amenity
                colore = 'viola'
                if dist <= 400:
                    servizi_400m += 1
            else:
                continue

            pois.append({
                'nome': nome,
                'tipo': tipo,
                'colore': colore,
                'lat': elat,
                'lng': elng,
                'dist': round(dist),
            })

    except Exception as e:
        print(f"[GEO] Overpass error: {e}")

    # Stima popolazione (basata su raggio)
    pop_3min = _stima_pop(r3)
    pop_5min = _stima_pop(r5)
    pop_10min = _stima_pop(r10)

    # Score zona
    score = _calcola_score(pop_5min, competitors_500m, servizi_400m)
    label = _score_label(score)

    return jsonify({
        'lat': lat,
        'lng': lng,
        'pop_3min': pop_3min,
        'pop_5min': pop_5min,
        'pop_10min': pop_10min,
        'competitors_500m': competitors_500m,
        'competitors_1km': competitors_1km,
        'servizi_400m': servizi_400m,
        'score': round(score, 1),
        'label': label,
        'pois': pois,
        'r3': r3,
        'r5': r5,
        'r10': r10,
    })


def _stima_pop(raggio_m):
    """Stima popolazione media italiana: ~2500 ab/km²"""
    area_km2 = math.pi * (raggio_m / 1000) ** 2
    return int(area_km2 * 2500)


def _calcola_score(pop_5min, concorrenti_500m, servizi_400m):
    score = 0
    # Popolazione (max 40 punti)
    if pop_5min > 8000:
        score += 40
    elif pop_5min > 5000:
        score += 30
    elif pop_5min > 3000:
        score += 20
    else:
        score += 10
    # Servizi (max 30 punti)
    score += min(servizi_400m * 3, 30)
    # Concorrenza (max -20 penalità)
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
