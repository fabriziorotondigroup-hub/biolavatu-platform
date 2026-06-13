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
import os as _os
from services.istat import get_demographic_data, get_market_assessment
from services.ins_romania import get_demographic_data_ro, get_market_assessment_ro, EUR_RON_RATE
from services.domanda import calcola_stima_clienti, calcola_domanda_avanzata
from services.analisi_competitiva import (
    calcola_capacita_concorrenza,
    calcola_indice_famiglie_lavanderie,
    analizza_punti_deboli,
    stima_traffico_veicolare,
    calcola_score_ponderato,
)

def ricerca_info_struttura_militare(nome: str, citta: str) -> dict:
    """
    Usa Claude con web search per trovare info su scuole/caserme militari:
    durata corsi, numero allievi, operatività, presenza lavanderia interna.
    Restituisce dict con: durata_mesi, n_allievi, ha_lavanderia_interna, note, mult_suggerito
    """
    try:
        import anthropic, httpx
        try:
            client = anthropic.Anthropic(
                api_key=_os.environ.get('ANTHROPIC_API_KEY'),
                http_client=httpx.Client()
            )
        except TypeError:
            client = anthropic.Anthropic(api_key=_os.environ.get('ANTHROPIC_API_KEY'))

        prompt = f"""Cerca informazioni su questa struttura militare italiana: "{nome}" a {citta}.

Devo sapere:
1. Durata dei corsi/addestramento (mesi)
2. Numero approssimativo di allievi/personale presenti
3. Se ha lavanderia interna (gli allievi non escono per lavare)
4. Periodicità dei corsi (quante sessioni all'anno)

Rispondi SOLO in questo formato JSON, senza altro testo:
{{
  "durata_mesi": <numero o null se non trovato>,
  "n_allievi_stimati": <numero o null>,
  "ha_lavanderia_interna": <true/false/null>,
  "sessioni_anno": <numero o null>,
  "tipo": "<scuola_formazione|base_operativa|centro_addestramento|accademia>",
  "fonte": "<breve descrizione della fonte>",
  "note": "<max 100 caratteri di note>"
}}"""

        msg = client.messages.create(
            model='claude-sonnet-4-5',
            max_tokens=400,
            tools=[{'type': 'web_search_20250305', 'name': 'web_search'}],
            messages=[{'role': 'user', 'content': prompt}]
        )

        # Estrae il testo dalla risposta
        testo = ''
        for block in msg.content:
            if hasattr(block, 'text'):
                testo += block.text

        # Parsa il JSON
        import re, json as _json
        m = re.search(r'\{[^{}]+\}', testo, re.DOTALL)
        if m:
            info = _json.loads(m.group())
        else:
            info = {}

        # Calcola moltiplicatore suggerito
        durata = info.get('durata_mesi')
        ha_lav = info.get('ha_lavanderia_interna')

        durata_mesi = info.get('durata_mesi')
        if ha_lav:
            mult_caserma = 0.08  # preferiscono self esterna: più pulita, no attesa
            lav_txt = ' | ha lavanderia interna (riduzione parziale — preferiscono self esterna)'
        elif durata_mesi and durata_mesi >= 24:
            mult_caserma = 0.22
        elif durata_mesi and durata_mesi >= 12:
            mult_caserma = 0.18
        elif durata_mesi and durata_mesi >= 6:
            mult_caserma = 0.12
        elif durata_mesi:
            mult_caserma = 0.08
        else:
            mult_caserma = 0.10

        info['mult_suggerito'] = mult_caserma
        info['ricerca_ok'] = True
        return info

    except Exception as e:
        return {
            'durata_mesi': None,
            'mult_suggerito': 0.10,
            'ricerca_ok': False,
            'note': f'Ricerca non disponibile: {str(e)[:50]}',
        }



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
    try:
        plat = place['geometry']['location']['lat']
        plng = place['geometry']['location']['lng']
    except (KeyError, TypeError):
        return None  # risultato malformato
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
        import traceback
        print(f'[GEO ERROR] {type(e).__name__}: {e}')
        traceback.print_exc()
        return jsonify({'error': str(e), 'tipo': type(e).__name__}), 500


# ── ANALISI ZONA ──────────────────────────────────────────────────────────────

@geo_bp.route('/api/zona-analisi')
@login_required
def zona_analisi():
    try:
        lat      = float(request.args.get('lat', 0))
        lng      = float(request.args.get('lng', 0))
        citta    = request.args.get('citta', '')
        provincia = request.args.get('provincia', '')
        # Per Romania: se lat/lng mancanti ma market=RO, geocodifica automaticamente
        _market_check = request.args.get('market','').upper()
        if (not lat or not lng) and _market_check == 'RO':
            # Geocodifica l'indirizzo internamente
            _citta_ro  = request.args.get('citta', '')
            _prov_ro   = request.args.get('provincia', '')
            _addr_ro   = request.args.get('indirizzo', _citta_ro + ', Romania')
            _gmk = os.environ.get('GMAPS_KEY','')
            if _gmk and _citta_ro:
                import requests as _req
                _gr = _req.get(
                    'https://maps.googleapis.com/maps/api/geocode/json',
                    params={'address': _addr_ro, 'key': _gmk, 'region': 'ro'},
                    timeout=5
                ).json()
                if _gr.get('status') == 'OK' and _gr.get('results'):
                    _loc = _gr['results'][0]['geometry']['location']
                    lat  = float(_loc['lat'])
                    lng  = float(_loc['lng'])
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
        # Raccogliamo anche uffici/aziende come proxy zona lavorativa
        raw_uffici       = gmaps_nearby(lat, lng, r5,  'establishment',
                                        keyword='ufficio azienda sede legale')

        # ── NUOVI: parcheggi, metro, bus, strade principali ───────────────────
        raw_parcheggi    = gmaps_nearby(lat, lng, r5, 'parking')
        raw_metro        = gmaps_nearby(lat, lng, r5, 'subway_station')
        raw_bus          = gmaps_nearby(lat, lng, r5, 'bus_station')
        raw_fermate_bus  = gmaps_nearby(lat, lng, r5, 'transit_station',
                                        keyword='fermata autobus')
        # Strade ad alto traffico: proxy da punti di interesse su arterie principali
        raw_strade_princ = gmaps_nearby(lat, lng, r5, 'point_of_interest',
                                        keyword='viale corso piazza strada principale')
        # Residenze/condomini per stima famiglie
        raw_residenze    = gmaps_nearby(lat, lng, r5, 'point_of_interest',
                                        keyword='condominio residence appartamenti affitto')

        # Contatori per classificazione tipo zona (usati da modello domanda avanzato)
        _n_rist  = len(raw_ristoranti)
        _n_bar   = len(raw_bar_cafe)
        _n_farm  = len(raw_farmacie)
        _n_trasp = len(raw_trasporti)

        # ── ATTRACTOR POINTS — generatori ad alto consumo lavanderia ─────────────
        # Università: studenti fuori sede, senza lavatrice, uso quotidiano
        raw_universita   = gmaps_nearby(lat, lng, r15, 'university')
        # Caserme e scuole militari: Google Maps non ha tipo 'military'
        # Si usa point_of_interest + keyword separate per massimizzare i risultati
        raw_caserme_base  = gmaps_nearby(lat, lng, r15, 'point_of_interest',
                                         keyword='caserma esercito carabinieri polizia guardia finanza')
        raw_caserme_scuole = gmaps_nearby(lat, lng, r15, 'point_of_interest',
                                          keyword='scuola militare accademia militare istituto militare')
        # Unisci deduplicando per place_id
        _caserme_viste = set()
        raw_caserme = []
        for _lst in [raw_caserme_base, raw_caserme_scuole]:
            for _p in _lst:
                _pid = _p.get('place_id', _p.get('name', ''))
                if _pid not in _caserme_viste:
                    _caserme_viste.add(_pid)
                    raw_caserme.append(_p)
        # Vigili del fuoco: turni 24/7, divise lavate spesso, personale fisso 365gg
        raw_vvf          = gmaps_nearby(lat, lng, r15, 'fire_station')
        # Ospedali e cliniche: personale + visitatori + degenti
        raw_ospedali     = gmaps_nearby(lat, lng, r15, 'hospital')
        # Case di riposo, RSA, case di cura: residenti permanenti senza lavatrice
        raw_case_cura_1  = gmaps_nearby(lat, lng, r15, 'nursing_home')
        raw_case_cura_2  = gmaps_nearby(lat, lng, r15, 'point_of_interest',
                                        keyword='casa di riposo RSA residenza anziani casa di cura')
        # Deduplicazione case di cura
        _cure_viste = set()
        raw_case_cura = []
        for _lst in [raw_case_cura_1, raw_case_cura_2]:
            for _p in _lst:
                _pid = _p.get('place_id', _p.get('name', ''))
                if _pid not in _cure_viste:
                    _cure_viste.add(_pid)
                    raw_case_cura.append(_p)
        # Stazioni ferroviarie: pendolari, turisti, transito
        raw_stazioni     = gmaps_nearby(lat, lng, r10, 'train_station')

        # ── TURISMO: hotel, B&B, affittacamere, ostelli ─────────────────────────────
        raw_hotel      = gmaps_nearby(lat, lng, r10, 'lodging')
        raw_bnb        = gmaps_nearby(lat, lng, r10, 'point_of_interest',
                                      keyword='bed and breakfast affittacamere casa vacanze')
        # Deduplicazione turismo
        _tur_visti = set()
        raw_turismo = []
        for _lst in [raw_hotel, raw_bnb]:
            for _p in (_lst or []):
                _pid = _p.get('place_id', _p.get('name', ''))
                if _pid not in _tur_visti:
                    _tur_visti.add(_pid)
                    raw_turismo.append(_p)

        # ── AFFITTI BREVI / TURISMO RESIDENZIALE ────────────────────────────
        # Cerca segnali di affitti brevi/Airbnb nella zona
        raw_affitti_1 = gmaps_nearby(lat, lng, r10, 'point_of_interest',
                                     keyword='affittacamere casa vacanze appartamento turistico airbnb')
        raw_affitti_2 = gmaps_nearby(lat, lng, r10, 'lodging',
                                     keyword='bed and breakfast ostello agriturismo')
        _aff_visti = set()
        raw_affitti = []
        for _lst in [raw_affitti_1, raw_affitti_2]:
            for _p in (_lst or []):
                _pid = _p.get('place_id', _p.get('name', ''))
                if _pid not in _aff_visti:
                    _aff_visti.add(_pid)
                    raw_affitti.append(_p)

        # ── PET SHOP / VETERINARI / TOELETTATURA ──────────────────────────────
        raw_pet_1 = gmaps_nearby(lat, lng, r5, 'pet_store')
        raw_pet_2 = gmaps_nearby(lat, lng, r5, 'veterinary_care')
        raw_pet_3 = gmaps_nearby(lat, lng, r5, 'point_of_interest',
                                  keyword='toelettatura animali pet shop negozio animali')
        # Deduplicazione pet
        _pet_visti = set()
        raw_pet = []
        for _lst in [raw_pet_1, raw_pet_2, raw_pet_3]:
            for _p in (_lst or []):
                _pid = _p.get('place_id', _p.get('name', ''))
                if _pid not in _pet_visti:
                    _pet_visti.add(_pid)
                    raw_pet.append(_p)

        # ── FORNI / PANIFICI / PASTICCERIE ────────────────────────────────────
        raw_forni = gmaps_nearby(lat, lng, r5, 'bakery')

        # ── PARRUCCHIERI / BARBIERI ────────────────────────────────────────────────────
        raw_parrucchieri = gmaps_nearby(lat, lng, r5, 'hair_care')

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

        # Nuovi contatori
        n_parcheggi      = 0
        n_fermate_metro  = 0
        n_fermate_bus_tot = 0
        n_strade_princ   = 0
        n_residenze      = 0

        # Volume recensioni entro 400m (proxy traffico pedonale reale)
        recensioni_zona = 0
        # Catene GDO entro 500m (validazione zona)
        gdo_trovate = []

        def add_pois(places, categoria, colore, icon, max_serv=None):
            nonlocal servizi_400m, recensioni_zona
            for p in (places or []):
                poi = place_to_poi(p, lat, lng, categoria, colore, icon)
                if poi is None:
                    continue  # salta risultati malformati di Google
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

        add_pois(raw_supermercati, 'supermercato',  '#10b981', '🛒',  400)
        add_pois(raw_convenience,  'supermercato',  '#10b981', '🏪',  400)
        add_pois(raw_farmacie,     'farmacia',      '#3b82f6', '💊',  400)
        add_pois(raw_bar_cafe,     'bar_cafe',      '#f59e0b', '☕',  400)
        add_pois(raw_ristoranti,   'ristorante',    '#ef4444', '🍽️', 400)
        add_pois(raw_scuole,       'istruzione',    '#8b5cf6', '🎓',  400)
        add_pois(raw_trasporti,    'trasporti',     '#06b6d4', '🚌',  400)
        add_pois(raw_palestre,     'altro',         '#ec4899', '💪',  400)
        add_pois(raw_ospedali,     'ospedale',      '#0891b2', '🏥', 1500)
        add_pois(raw_case_cura,    'casa_cura',     '#7c3aed', '🏠', 1500)
        add_pois(raw_turismo,      'turismo',       '#0891b2', '🛏️', 500)

        # ── NUOVI POI: parcheggi, metro, bus ──────────────────────────────────────
        for p in (raw_parcheggi or []):
            poi = place_to_poi(p, lat, lng, 'altro', '#64748b', '🅿️')
            if poi and poi['distanza_m'] <= r5:
                pois.append(poi)
                n_parcheggi += 1

        _bus_visti = set()
        for p in (raw_metro or []):
            pid = p.get('place_id', p.get('name',''))
            if pid not in _bus_visti:
                _bus_visti.add(pid)
                poi = place_to_poi(p, lat, lng, 'trasporti', '#6d28d9', '🚇')
                if poi and poi['distanza_m'] <= r5:
                    pois.append(poi)
                    n_fermate_metro += 1

        for p in (list(raw_bus or []) + list(raw_fermate_bus or [])):
            pid = p.get('place_id', p.get('name',''))
            if pid not in _bus_visti:
                _bus_visti.add(pid)
                poi = place_to_poi(p, lat, lng, 'trasporti', '#0284c7', '🚌')
                if poi and poi['distanza_m'] <= r5:
                    pois.append(poi)
                    n_fermate_bus_tot += 1

        _strade_viste = set()
        for p in (raw_strade_princ or []):
            pid = p.get('place_id', p.get('name',''))
            if pid not in _strade_viste:
                _strade_viste.add(pid)
                n_strade_princ += 1

        # Stima famiglie da residenze trovate + densità
        n_residenze = len(raw_residenze or [])

        # ── ANALISI ATTRACTOR POINTS ──────────────────────────────────────────────
        attractor_points = []
        n_universita = 0
        n_caserme    = 0
        n_ospedali   = 0
        n_stazioni   = 0
        n_vvf        = 0
        n_case_cura  = 0
        n_turismo    = 0
        n_parrucchieri = 0
        n_forni = 0
        n_pet = 0
        n_affitti = 0
        affitti_latlng = []  # per cerchi densità

        for p in raw_universita:
            poi = place_to_poi(p, lat, lng, 'istruzione', '#7c3aed', '🎓')
            if poi is None: continue
            poi['tipo_attractor'] = 'universita'
            poi['nota'] = 'Studenti fuori sede — alto uso lavanderia'
            pois.append(poi)
            if poi['distanza_m'] <= r15:
                n_universita += 1
                attractor_points.append({
                    'tipo': 'universita', 'nome': poi['nome'],
                    'lat': poi['lat'], 'lng': poi['lng'],
                    'distanza_m': poi['distanza_m'], 'icon': '🎓',
                    'impatto': 'Alto — studenti senza lavatrice',
                    'mult_caserma': None, 'durata_mesi': None,
                    'n_allievi': None, 'ha_lavanderia_interna': None,
                    'note_ricerca': None, 'ricerca_ai_ok': None,
                    'verifica_richiesta': False,
                })

        for p in raw_caserme:
            poi = place_to_poi(p, lat, lng, 'altro', '#1e40af', '🪖')
            if poi is None: continue
            nome = poi.get('nome', '').lower()
            # Filtra solo risultati pertinenti
            if not any(k in nome for k in ('caserma','militar','polizi','carabin','eserc',
                                            'guardia','finanz','aeronautic','marina','esercit')):
                continue
            pois.append(poi)
            if poi['distanza_m'] > r15:
                continue
            n_caserme += 1

            # Classifica tipo struttura militare per stimare impatto reale
            # NB: la durata corso NON è rilevabile automaticamente — va verificata sul posto
            if any(k in nome for k in ('scuola','accademia','istituto','centro addestramento')):
                tipo_mil = 'scuola_militare'
                poi['tipo_attractor'] = 'scuola_militare'

                # Ricerca automatica durata corsi e operatività
                info_mil = ricerca_info_struttura_militare(poi['nome'], citta)
                mult_caserma = info_mil.get('mult_suggerito', 0.10)
                durata_mesi  = info_mil.get('durata_mesi')
                n_allievi    = info_mil.get('n_allievi_stimati')
                ha_lav       = info_mil.get('ha_lavanderia_interna')
                note_mil     = info_mil.get('note', '')
                ricerca_ok   = info_mil.get('ricerca_ok', False)

                # Costruisce nota descrittiva
                if durata_mesi:
                    dur_txt = f'{durata_mesi} mesi'
                else:
                    dur_txt = 'durata non trovata'
                lav_txt = ' | ⚠️ ha lavanderia interna' if ha_lav else ''
                poi['nota'] = (
                    f'Scuola militare — corso: {dur_txt}'
                    f'{" | ~"+str(n_allievi)+" allievi" if n_allievi else ""}'
                    f'{lav_txt}'
                )
                poi['info_militare'] = info_mil

                if ha_lav:
                    impatto_nota = '✅ Ha lavanderia interna ma riduzione solo parziale — gli allievi preferiscono self esterna (più pulita, no attesa, prezzi simili)'
                elif durata_mesi and durata_mesi >= 24:
                    impatto_nota = f'Alto — corso {dur_txt}, allievi con abitudini stabili (come universitari)'
                elif durata_mesi and durata_mesi >= 12:
                    impatto_nota = f'Medio-alto — corso {dur_txt}'
                elif durata_mesi and durata_mesi >= 6:
                    impatto_nota = f'Medio — corso {dur_txt}, si orienta nella zona'
                elif durata_mesi:
                    impatto_nota = f'Basso — corso {dur_txt}, troppo breve per creare abitudini'
                else:
                    impatto_nota = 'Da verificare — durata corso non trovata (applicato moltiplicatore conservativo 10%)'
            else:
                tipo_mil = 'base_operativa'
                poi['tipo_attractor'] = 'caserma'
                poi['nota'] = 'Base operativa — personale di stanza, abitudini fisse'
                mult_caserma = 0.20
                impatto_nota = 'Medio-alto — militari stabili con abitudini regolari'

            poi['mult_caserma']    = mult_caserma
            poi['tipo_militare']   = tipo_mil
            poi['durata_corso_mesi'] = None  # da verificare sul posto

            attractor_points.append({
                'tipo':              tipo_mil,
                'nome':              poi['nome'],
                'lat':               poi['lat'],
                'lng':               poi['lng'],
                'distanza_m':        poi['distanza_m'],
                'icon':              '🪖',
                'impatto':           impatto_nota,
                'mult_caserma':      mult_caserma,
                'durata_mesi':       durata_mesi if tipo_mil == 'scuola_militare' else None,
                'n_allievi':         n_allievi if tipo_mil == 'scuola_militare' else None,
                'ha_lavanderia_interna': ha_lav if tipo_mil == 'scuola_militare' else False,
                'note_ricerca':      note_mil if tipo_mil == 'scuola_militare' else None,
                'ricerca_ai_ok':     ricerca_ok if tipo_mil == 'scuola_militare' else None,
                'verifica_richiesta': tipo_mil == 'scuola_militare' and not ricerca_ok,
            })

        for p in raw_ospedali:
            poi = place_to_poi(p, lat, lng, 'altro', '#0891b2', '🏥')
            if poi is None: continue
            poi['tipo_attractor'] = 'ospedale'
            poi['nota'] = 'Personale sanitario + visitatori'
            pois.append(poi)
            if poi['distanza_m'] <= r15:
                n_ospedali += 1
                attractor_points.append({
                    'tipo': 'ospedale', 'nome': poi['nome'],
                    'lat': poi['lat'], 'lng': poi['lng'],
                    'distanza_m': poi['distanza_m'], 'icon': '🏥',
                    'impatto': 'Medio-alto — personale sanitario + familiari degenti',
                    'mult_caserma': None, 'durata_mesi': None,
                    'n_allievi': None, 'ha_lavanderia_interna': None,
                    'note_ricerca': 'Ospedale: personale su turni usa lavanderia esterna regolarmente',
                    'ricerca_ai_ok': True,
                    'verifica_richiesta': False,
                })

        for p in raw_stazioni:
            poi = place_to_poi(p, lat, lng, 'trasporti', '#0284c7', '🚂')
            if poi is None: continue
            poi['tipo_attractor'] = 'stazione'
            poi['nota'] = 'Nodo di transito — utenti pendolari'
            pois.append(poi)
            if poi['distanza_m'] <= r10:
                n_stazioni += 1
                attractor_points.append({
                    'tipo': 'stazione', 'nome': poi['nome'],
                    'lat': poi['lat'], 'lng': poi['lng'],
                    'distanza_m': poi['distanza_m'], 'icon': '🚂',
                    'impatto': 'Medio — pendolari e turisti di passaggio',
                    'mult_caserma': None, 'durata_mesi': None,
                    'n_allievi': None, 'ha_lavanderia_interna': None,
                    'note_ricerca': None, 'ricerca_ai_ok': None,
                    'verifica_richiesta': False,
                })

        for p in raw_vvf:
            poi = place_to_poi(p, lat, lng, 'altro', '#dc2626', '🚒')
            if poi is None: continue
            poi['tipo_attractor'] = 'vvf'
            poi['nota'] = 'Vigili del fuoco — turni 24/7, divise lavate frequentemente, personale fisso'
            pois.append(poi)
            if poi['distanza_m'] <= r15:
                n_vvf += 1
                attractor_points.append({
                    'tipo': 'vvf', 'nome': poi['nome'],
                    'lat': poi['lat'], 'lng': poi['lng'],
                    'distanza_m': poi['distanza_m'], 'icon': '🚒',
                    'impatto': 'Medio — personale fisso 365gg, divise su turni, usano self-service esterna',
                    'mult_caserma': None, 'durata_mesi': None,
                    'n_allievi': None, 'ha_lavanderia_interna': None,
                    'note_ricerca': 'Personale permanente su turni — lavaggio divise e indumenti regolare',
                    'ricerca_ai_ok': True,
                    'verifica_richiesta': False,
                })

        # Moltiplicatore attractor: somma ponderata per distanza e tipo
        mult_attractor = 1.0
        for ap in attractor_points:
            d = ap['distanza_m']
            peso = 1.0 if d <= 400 else 0.7 if d <= 800 else 0.4
            if ap['tipo'] == 'universita': mult_attractor += 0.25 * peso
            elif ap['tipo'] in ('caserma','scuola_militare','base_operativa'):
                mc = ap.get('mult_caserma', 0.10)
                mult_attractor += mc * peso
            elif ap['tipo'] == 'ospedale': mult_attractor += 0.12 * peso
            elif ap['tipo'] == 'stazione': mult_attractor += 0.08 * peso
            elif ap['tipo'] == 'vvf':      mult_attractor += 0.10 * peso
        mult_attractor = min(mult_attractor, 2.0)  # cap a ×2.0

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
            if poi is None: continue
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

        # ── DATI DEMOGRAFICI — auto-detect IT / RO ───────────────────────────────
        _indirizzo_raw = request.args.get('indirizzo', '').lower()
        _market_param  = request.args.get('market', '').upper()
        # IMPORTANTE: il codice provincia da solo NON basta per distinguere IT/RO
        # (IS=Isernia/Iași, CT=Catania/Constanța, AG=Agrigento/Argeș, SV=Savona/Suceava)
        # Usiamo SOLO market=RO o 'romania' nell'indirizzo come segnali affidabili
        _is_romania = (
            _market_param == 'RO' or
            'romania' in _indirizzo_raw or
            'românia' in _indirizzo_raw or
            ', ro,' in _indirizzo_raw or
            _indirizzo_raw.endswith(', ro') or
            _indirizzo_raw.endswith(', romania')
        )
        _paese = 'RO' if _is_romania else 'IT'  # default sicuro

        if _is_romania:
            demo          = get_demographic_data_ro(provincia, citta)
            eta_media     = demo.get('eta_media', 42.0)
            reddito_medio = demo.get('reddito_medio', 30000)  # RON/anno
            densita_istat = demo.get('densita', 200)
        else:
            demo          = get_demographic_data(citta, provincia)
            eta_media     = demo.get('eta_media', 46.4)
            reddito_medio = demo.get('reddito_medio', 19800)  # EUR/anno
            densita_istat = demo.get('densita', 200)

        # ── DENSITÀ REALE da Google Maps (proxy da POI nel raggio) ───────────────
        # Contiamo i luoghi unici entro 400m come proxy di urbanizzazione reale
        # Benchmark: centro città = 50+ POI in 400m → densità >3000
        #            periferia     = 15-30 POI → densità 800-2000
        #            zona rurale   = <10 POI → densità <500
        def _safe_dist(p):
            try:
                return haversine(lat, lng,
                                 p['geometry']['location']['lat'],
                                 p['geometry']['location']['lng'])
            except (KeyError, TypeError):
                return 9999
        _poi_400m = sum(1 for p in (
            raw_supermercati + raw_bar_cafe + raw_ristoranti +
            raw_farmacie + raw_scuole + raw_trasporti + raw_palestre
        ) if _safe_dist(p) <= 400)

        # Stima densità reale dal numero di POI entro 400m
        if   _poi_400m >= 60: densita_reale = 7000
        elif _poi_400m >= 40: densita_reale = 5000
        elif _poi_400m >= 25: densita_reale = 3500
        elif _poi_400m >= 15: densita_reale = 2000
        elif _poi_400m >= 8:  densita_reale = 1000
        elif _poi_400m >= 3:  densita_reale = 500
        else:                  densita_reale = 150

        # Usa il massimo tra ISTAT e stima reale (evita di sottostimare centri urbani)
        # ma non moltiplicare più di 4× per sicurezza
        densita = max(densita_istat, min(densita_reale, densita_istat * 4))

        # ── POPOLAZIONE STIMATA (anticipata per usarla nell'assessment) ────────────
        area_3min  = math.pi * (r3  ** 2) / 1_000_000
        area_5min  = math.pi * (r5  ** 2) / 1_000_000
        area_10min = math.pi * (r10 ** 2) / 1_000_000
        pop_3min   = int(densita * area_3min)
        pop_5min   = int(densita * area_5min)
        pop_10min  = int(densita * area_10min)

        if _paese == 'RO':
            assessment = get_market_assessment_ro(reddito_medio, densita)
        else:
            assessment = get_market_assessment(
                eta_media, reddito_medio, densita,
                concorrenti_1km, recensioni_zona, gdo_500m
            )
        # ── PENALITÀ SCORE se bacino demografico insufficiente ────────────────────
        _score_raw = assessment['score']
        _pop_bacino = pop_3min
        if   _pop_bacino < 200:  _score_raw = min(_score_raw, 25)
        elif _pop_bacino < 500:  _score_raw = min(_score_raw, 40)
        elif _pop_bacino < 1000: _score_raw = min(_score_raw, 55)
        elif _pop_bacino < 2000: _score_raw = min(_score_raw, 70)
        # Penalità concorrenza estrema
        if concorrenti_500m >= 3: _score_raw = min(_score_raw, 50)
        if concorrenti_500m >= 5: _score_raw = min(_score_raw, 30)
        assessment = dict(assessment)
        assessment['score'] = _score_raw
        # Ricalcola label
        if   _score_raw >= 80: assessment['label'] = 'Eccellente'
        elif _score_raw >= 65: assessment['label'] = 'Buono'
        elif _score_raw >= 45: assessment['label'] = 'Discreto'
        elif _score_raw >= 25: assessment['label'] = 'Scarso'
        else:                   assessment['label'] = 'Critico'

        # ── CASE DI RIPOSO / RSA / CASE DI CURA ────────────────────────────────────
        for p in raw_case_cura:
            poi = place_to_poi(p, lat, lng, 'casa_cura', '#7c3aed', '🏠')
            if poi is None: continue
            poi['tipo_attractor'] = 'casa_cura'
            poi['nota'] = 'Residenti permanenti — alta necessità lavanderia'
            # Evita duplicati (già aggiunti da add_pois)
            if not any(x.get('nome') == poi['nome'] and x.get('tipo') == 'casa_cura' for x in pois):
                pois.append(poi)
            if poi['distanza_m'] <= r15:
                n_case_cura += 1
                attractor_points.append({
                    'tipo': 'casa_cura', 'nome': poi['nome'],
                    'lat': poi.get('lat', 0), 'lng': poi.get('lng', 0),
                    'distanza_m': poi['distanza_m'], 'icon': '🏠',
                    'impatto': 'Alto — residenti permanenti senza lavatrice, uso quotidiano',
                    'mult_caserma': None, 'durata_mesi': None,
                    'n_allievi': None, 'ha_lavanderia_interna': None,
                    'note_ricerca': 'RSA/casa di cura: residenti permanenti, uso sistematico lavanderia',
                    'ricerca_ai_ok': True,
                    'verifica_richiesta': False,
                })

        # ── STIMA CLIENTI ─────────────────────────────────────────────────────────
        stima = calcola_stima_clienti(
            pop_3min=pop_3min,
            pop_5min=pop_5min, pop_10min=pop_10min,
            densita=densita, concorrenti_500m=concorrenti_500m,
            concorrenti_1km=concorrenti_1km, servizi_400m=servizi_400m,
            reddito_medio=reddito_medio,
            recensioni_zona=recensioni_zona, gdo_500m=gdo_500m,
            mult_attractor=mult_attractor,
            attractor_points=attractor_points,
            n_ristoranti=_n_rist, n_bar=_n_bar,
        )

        # ── ANALISI AVANZATA (nuovo modulo) ───────────────────────────────────
        # Capacità installata concorrenza
        _comp_analisi = calcola_capacita_concorrenza(competitors_detail)

        # Indice famiglie/lavanderie (KPI principale Fabrizio method)
        _indice_fam_lav = calcola_indice_famiglie_lavanderie(
            pop_5min=pop_5min,
            pop_10min=pop_10min,
            n_lav_500m=concorrenti_500m,
            n_lav_1km=concorrenti_1km,
        )

        # Analisi punti deboli concorrenza
        _punti_deboli = analizza_punti_deboli(competitors_detail)

        # Traffico veicolare/pedonale stimato
        _traffico = stima_traffico_veicolare(
            n_stazioni_metro=n_fermate_metro,
            n_fermate_bus=n_fermate_bus_tot,
            n_parcheggi=n_parcheggi,
            n_strade_principali=n_strade_princ,
            recensioni_zona=recensioni_zona,
        )

        # Score ponderato 7 dimensioni
        _score_pond = calcola_score_ponderato(
            pop_5min=pop_5min,
            n_turismo=n_turismo,
            n_lav_competitori=concorrenti_1km,
            score_traffico=_traffico['score_totale'],
            n_parcheggi=n_parcheggi,
            n_mezzi_pubblici=n_fermate_metro + n_fermate_bus_tot,
            reddito_medio=reddito_medio,
            densita=densita,
            indice_famiglie_lav=_indice_fam_lav['indice'],
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
            'confidenza': {
                'score': stima.get('confidenza_score', 0),
                'label': stima.get('confidenza_label', 'N/D'),
                'col':   stima.get('confidenza_col', '#64748b'),
            },
            'tipo_zona':          stima.get('tipo_zona', 'misto'),
            'zona_turistica':     n_affitti >= 5,  # 5+ strutture = zona ad alta densita turistica
            'attractor_points':   attractor_points,
            'mult_attractor':     round(mult_attractor, 2),
            'n_universita':       n_universita,
            'n_caserme':          n_caserme,
            'n_ospedali':         n_ospedali,
            'n_stazioni':         n_stazioni,
            'n_vvf':              n_vvf,
            'n_case_cura':        n_case_cura,
            'n_turismo':          n_turismo,
            'n_parrucchieri':     n_parrucchieri,
            'n_forni':            n_forni,
            'n_pet':              n_pet,
            'n_affitti':          n_affitti,
            'affitti_latlng':     affitti_latlng,
            'verifica_richiesta': any(
                ap.get('verifica_richiesta') for ap in attractor_points
            ),
            # ── NUOVI CAMPI ANALISI AVANZATA ──────────────────────────────────
            'mobilita': {
                'n_parcheggi':       n_parcheggi,
                'n_fermate_metro':   n_fermate_metro,
                'n_fermate_bus':     n_fermate_bus_tot,
                'n_strade_princ':    n_strade_princ,
            },
            'traffico_analisi':   _traffico,
            'indice_famiglie_lav': _indice_fam_lav,
            'concorrenza_avanzata': {
                **_comp_analisi,
                'punti_deboli': _punti_deboli,
            },
            'score_ponderato':    _score_pond,
        })

    except Exception as _err:
        import traceback as _tb2
        _tb2.print_exc()
        print(f"[ZONA 500] {type(_err).__name__}: {_err}")
        return jsonify({"error": str(_err), "tipo": type(_err).__name__}), 500


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
            r10 = walking_radius(10)
            pop_10min_z = int(densita * math.pi * (r10 ** 2) / 1_000_000)
            stima = calcola_stima_clienti(
                pop_5min=pop_stimata,
                pop_10min=pop_10min_z,
                mult_attractor=1.0,
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
            r10 = walking_radius(10)
            pop_10min_z = int(densita * math.pi * (r10 ** 2) / 1_000_000)
            stima = calcola_stima_clienti(
                pop_5min=pop_stimata,
                pop_10min=pop_10min_z,
                densita=densita, concorrenti_500m=n_conc, concorrenti_1km=n_conc,
                servizi_400m=len(raw_bar)+len(raw_rest)+len(raw_sup),
                reddito_medio=reddito_medio, recensioni_zona=rec_zona, gdo_500m=gdo_z,
                mult_attractor=1.0,
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
            r10 = walking_radius(10)
            pop_10min_z = int(densita * math.pi * (r10 ** 2) / 1_000_000)
            stima = calcola_stima_clienti(
                pop_5min=pop_stimata,
                pop_10min=pop_10min_z,
                mult_attractor=1.0,
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


# ── GEOCODIFICA ROMANIA ───────────────────────────────────────────────────────

@geo_bp.route('/api/geocode-ro')
@login_required
def geocode_ro():
    """Geocodifica un indirizzo rumeno via Google Maps e ritorna lat/lng + analisi zona."""
    import requests as _req
    indirizzo = request.args.get('indirizzo', '')
    citta     = request.args.get('citta', '')
    judet     = request.args.get('judet', '')

    gmaps_key = os.environ.get('GMAPS_KEY', '')
    if not gmaps_key:
        return jsonify({'error': 'GMAPS_KEY non configurata'}), 500

    # Costruisci stringa indirizzo completa per Romania
    addr_parts = [p for p in [indirizzo, citta, judet, 'România'] if p]
    addr_str   = ', '.join(addr_parts)

    # Geocodifica
    try:
        resp = _req.get(
            'https://maps.googleapis.com/maps/api/geocode/json',
            params={'address': addr_str, 'key': gmaps_key,
                    'region': 'ro', 'language': 'ro'},
            timeout=8
        )
        geo = resp.json()
        if geo.get('status') != 'OK' or not geo.get('results'):
            return jsonify({'error': f'Geocode fallito: {geo.get("status")}'}), 400

        location = geo['results'][0]['geometry']['location']
        lat = location['lat']
        lng = location['lng']

        # Dati INS per il județ
        demo = get_demographic_data_ro(judet, citta)

        return jsonify({
            'lat':           float(lat),
            'lng':           float(lng),
            'indirizzo_fmt': geo['results'][0].get('formatted_address', addr_str),
            'reddito_medio': float(demo['reddito_medio']),
            'densita':       float(demo['densita']),
            'eta_media':     float(demo['eta_media']),
            'perc_stranieri':float(demo['perc_stranieri']),
            'reddito_eur':   float(demo.get('reddito_eur', demo['reddito_medio']/4.97)),
            'potenziale':    get_market_assessment_ro(
                demo['reddito_medio'], demo['densita'])['potenziale'],
            'paese':         'RO',
            'market':        'RO',
            'ok':            True,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
