"""
routes/albania.py — BIOLavaTU LaundryPro — Mercato Albania
ISOLATO: zero import da geo.py, preventivo.py, investitore.py, istat.py, romania.py.
"""
import os, json, math
import requests
from flask import (Blueprint, render_template, request, jsonify,
                   redirect, url_for, session, flash)
from flask_login import login_required, current_user
from app import db
from models.pratica import Pratica
from models.cliente import Cliente
from models.settings import Settings
from services.normativa_albania import NORMATIVA_AL
from services.ins_albania import (
    get_demographic_data_al, get_market_assessment_al, get_f_qyteti_al,
    get_cambio_all_live, converti_all_eur, converti_eur_all,
    get_densita_urbana_al,
    calcola_potenziale_lavaggi_al, calcola_incasso_da_lavaggi_al,
    calcola_affitto_max_al, calcola_costi_operativi_al, calcola_saturazione_al,
    TARIFFE_DEFAULT_AL, EUR_ALL_RATE, OCC_BASE_AL,
)

# ── Traduzioni IT / AL ────────────────────────────────────────────────────────
TR = {
    'it': {
        'dashboard':      'Dashboard',
        'nuovo':          'Nuova pratica',
        'pratiche':       'Pratiche Albania',
        'venditori':      'Venditori Albania',
        'cliente':        'Cliente',
        'sede':           'Sede',
        'zona':           'Zona',
        'macchine':       'Macchine',
        'business_plan':  'Business Plan',
        'riepilogo':      'Riepilogo',
        'salva':          'Salva pratica',
        'avanti':         'Avanti',
        'indietro':       'Indietro',
        'analizza_zona':  'Analizza zona',
        'genera_ai':      'Genera Analisi AI',
        'incasari':       'Incasso mensile',
        'profit':         'Utile netto',
        'investitie':     'Investimento',
        'ocupare':        'Occupazione',
        'all':            'ALL',
        'nome':           'Nome',
        'email':          'Email',
        'telefon':        'Telefono',
        'qyteti':         'Citta',
        'qark':           'Qark / Regione',
        'suprafata':      'Superficie (mq)',
        'qira':           'Affitto mensile (ALL)',
        'tip_zona':       'Tipo zona',
        'rruga':          'Via e numero civico',
        'pesimist':       'Pessimistico',
        'realist':        'Realistico',
        'optimist':       'Ottimistico',
        'populata':       'Popolazione raggiungibile',
        'score_zona':     'Score zona',
        'konkurenca':     'Concorrenza',
        'conc_500':       'Self-service 500m',
        'conc_1km':       'Tutte 1km',
    },
    'al': {
        'dashboard':      'Paneli kryesor',
        'nuovo':          'Dosar i ri',
        'pratiche':       'Dosaret Shqiperi',
        'venditori':      'Agjentet Shqiperi',
        'cliente':        'Klient',
        'sede':           'Selia',
        'zona':           'Zona',
        'macchine':       'Makinerite',
        'business_plan':  'Plani i biznesit',
        'riepilogo':      'Permbledhje',
        'salva':          'Ruaj dosarin',
        'avanti':         'Perpara',
        'indietro':       'Mbrapa',
        'analizza_zona':  'Analizo zonen',
        'genera_ai':      'Gjenero Analizen AI',
        'incasari':       'Te ardhura mujore',
        'profit':         'Fitim neto',
        'investitie':     'Investimi',
        'ocupare':        'Zenia',
        'all':            'ALL',
        'nome':           'Emer',
        'email':          'Email',
        'telefon':        'Telefon',
        'qyteti':         'Qyteti',
        'qark':           'Qark',
        'suprafata':      'Siperfaqe (m2)',
        'qira':           'Qira mujore (ALL)',
        'tip_zona':       'Lloji i zones',
        'rruga':          'Rruga dhe numri',
        'pesimist':       'Pesimist',
        'realist':        'Realist',
        'optimist':       'Optimist',
        'populata':       'Popullata e arritshme',
        'score_zona':     'Score zone',
        'konkurenca':     'Konkurenca',
        'conc_500':       'Lavanderite 500m',
        'conc_1km':       'Gjithsej 1km',
    },
}

def _tr(key, lingua='it'):
    return TR.get(lingua, TR['it']).get(key, key)

def _get_lingua():
    return session.get('lingua_al', 'it')

al_bp = Blueprint('albania', __name__, url_prefix='/al')
GMAPS_KEY  = os.environ.get('GMAPS_KEY', '')
PLACES_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'


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

def place_to_poi(place, lat_c, lng_c, categoria, colore, icon):
    try:
        plat = place['geometry']['location']['lat']
        plng = place['geometry']['location']['lng']
    except (KeyError, TypeError):
        return None
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

def _check_al():
    return current_user.role in ('owner', 'admin', 'segreteria') or \
           getattr(current_user, 'market', 'IT') == 'AL'

def _cambio():
    return get_cambio_all_live()

# ── Dashboard ─────────────────────────────────────────────────────────────────
@al_bp.route('/')
@login_required
def dashboard():
    if not _check_al(): return redirect(url_for('dashboard.index'))
    pratiche = Pratica.query.filter_by(market='AL').order_by(Pratica.created.desc()).limit(20).all()
    ling = _get_lingua()
    return render_template('albania/dashboard_al.html',
        pratiche=pratiche, cambio_all=_cambio(),
        lingua=ling, tr=TR.get(ling, TR['it']))

@al_bp.route('/pratiche')
@login_required
def pratiche():
    if not _check_al(): return redirect(url_for('dashboard.index'))
    pratiche = Pratica.query.filter_by(market='AL').order_by(Pratica.created.desc()).all()
    return render_template('albania/pratiche_al.html',
        pratiche=pratiche, cambio_all=_cambio())

# ── Wizard ────────────────────────────────────────────────────────────────────
@al_bp.route('/preventivo/nuovo', methods=['GET'])
@login_required
def nuovo_preventivo():
    if not _check_al(): return redirect(url_for('dashboard.index'))
    ling = _get_lingua()
    return render_template('albania/preventivo_al.html',
        pratica=None, cambio_all=_cambio(),
        tariffe=TARIFFE_DEFAULT_AL, settings=Settings.query.first(),
        lingua=ling, tr=TR.get(ling, TR['it']))

@al_bp.route('/preventivo/<int:id>')
@login_required
def modifica_preventivo(id):
    if not _check_al(): return redirect(url_for('dashboard.index'))
    p = Pratica.query.get_or_404(id)
    ling = _get_lingua()
    return render_template('albania/preventivo_al.html',
        pratica=p, cambio_all=_cambio(),
        tariffe=TARIFFE_DEFAULT_AL, settings=Settings.query.first(),
        lingua=ling, tr=TR.get(ling, TR['it']))

# ── API Geocodifica ───────────────────────────────────────────────────────────
@al_bp.route('/api/geocode')
@login_required
def geocode_al():
    indirizzo = request.args.get('indirizzo', '')
    citta     = request.args.get('citta', '')
    qark      = request.args.get('qark', '')
    if not GMAPS_KEY or not citta:
        return jsonify({'error': 'Parametri mancanti'}), 400
    addr = ', '.join(p for p in [indirizzo, citta, qark, 'Shqiperia'] if p)
    try:
        r = requests.get('https://maps.googleapis.com/maps/api/geocode/json',
            params={'address': addr, 'key': GMAPS_KEY, 'region': 'al', 'language': 'sq'},
            timeout=8).json()
        if r.get('status') != 'OK' or not r.get('results'):
            return jsonify({'error': f"Geocode: {r.get('status')}"}), 400
        loc  = r['results'][0]['geometry']['location']
        lat  = float(loc['lat']); lng = float(loc['lng'])
        demo = get_demographic_data_al(qark, citta)
        ass  = get_market_assessment_al(demo['reddito_medio'], demo['densita'])
        return jsonify({
            'lat': lat, 'lng': lng,
            'indirizzo_fmt': r['results'][0].get('formatted_address', addr),
            'reddito_medio': demo['reddito_medio'],
            'reddito_eur':   demo['reddito_eur'],
            'densita':       demo['densita'],
            'eta_media':     demo['eta_media'],
            'potenziale':    ass['potenziale'],
            'ok': True,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── API Zona-analisi ──────────────────────────────────────────────────────────
@al_bp.route('/api/zona-analisi')
@login_required
def zona_analisi_al():
    try:
        lat    = float(request.args.get('lat', 0) or 0)
        lng    = float(request.args.get('lng', 0) or 0)
        citta  = request.args.get('citta', '')
        qark   = request.args.get('provincia', '')

        if (not lat or not lng) and citta and GMAPS_KEY:
            r = requests.get('https://maps.googleapis.com/maps/api/geocode/json',
                params={'address': citta + ', Albania', 'key': GMAPS_KEY, 'region': 'al'},
                timeout=5).json()
            if r.get('status') == 'OK' and r.get('results'):
                loc = r['results'][0]['geometry']['location']
                lat, lng = float(loc['lat']), float(loc['lng'])

        if not lat or not lng:
            return jsonify({'error': 'Coordinate mancanti'}), 400

        r3 = walking_radius(3); r5 = walking_radius(5); r10 = walking_radius(10)

        raw_sup   = gmaps_nearby(lat, lng, r10, 'supermarket')
        raw_conv  = gmaps_nearby(lat, lng, r5,  'convenience_store')
        raw_farm  = gmaps_nearby(lat, lng, r5,  'pharmacy')
        raw_bar   = gmaps_nearby(lat, lng, r5,  'bar')
        raw_cafe  = gmaps_nearby(lat, lng, r5,  'cafe')
        raw_rest  = gmaps_nearby(lat, lng, r5,  'restaurant')
        raw_bank  = gmaps_nearby(lat, lng, r5,  'bank')
        raw_atm   = gmaps_nearby(lat, lng, r5,  'atm')
        raw_park  = gmaps_nearby(lat, lng, r5,  'parking')
        raw_bus   = gmaps_nearby(lat, lng, r5,  'bus_station')
        raw_scol  = gmaps_nearby(lat, lng, r10, 'university')
        raw_scuola= gmaps_nearby(lat, lng, r10, 'school')
        raw_osp   = gmaps_nearby(lat, lng, r10, 'hospital')
        raw_hotel = gmaps_nearby(lat, lng, r10, 'lodging')
        raw_gym   = gmaps_nearby(lat, lng, r5,  'gym')
        raw_lav   = gmaps_nearby(lat, lng, r10, 'laundry')

        pois = []
        def add(places, cat, col, icon):
            for p in (places or []):
                poi = place_to_poi(p, lat, lng, cat, col, icon)
                if poi: pois.append(poi)

        add(raw_sup,    'supermarkete',  '#22c55e', 'S')
        add(raw_conv,   'supermarkete',  '#16a34a', 'S')
        add(raw_farm,   'farmaci',       '#ec4899', 'F')
        add(raw_bar,    'bar',           '#f59e0b', 'B')
        add(raw_cafe,   'bar',           '#d97706', 'C')
        add(raw_rest,   'restorante',    '#f97316', 'R')
        add(raw_bank,   'banka',         '#06b6d4', '$')
        add(raw_atm,    'banka',         '#0891b2', '$')
        add(raw_park,   'parking',       '#64748b', 'P')
        add(raw_bus,    'transport',     '#7c3aed', 'T')
        add(raw_scol,   'arsim',         '#0ea5e9', 'U')
        add(raw_scuola, 'arsim',         '#0284c7', 'U')
        add(raw_osp,    'spitale',       '#ef4444', 'H')
        add(raw_hotel,  'hotele',        '#a855f7', 'L')
        add(raw_gym,    'tjeter',        '#14b8a6', 'G')

        conc500 = 0; conc1k = 0; comp_det = []
        for c in (raw_lav or []):
            if not c: continue
            clat = float(c.get('geometry', {}).get('location', {}).get('lat', lat))
            clng = float(c.get('geometry', {}).get('location', {}).get('lng', lng))
            dist = int(haversine(lat, lng, clat, clng))
            if dist <= 500:  conc500 += 1
            if dist <= 1000: conc1k  += 1
            col = '#ef4444' if dist <= 300 else '#f97316' if dist <= 600 else '#22c55e'
            comp_det.append({'nome': c.get('name', ''), 'distanza_m': dist,
                'rating': c.get('rating'), 'lat': clat, 'lng': clng,
                'cerchio_colore': col})

        gdo_500m = len([p for p in (raw_sup or []) + (raw_conv or [])
            if p and int(haversine(lat, lng,
                float(p.get('geometry', {}).get('location', {}).get('lat', lat)),
                float(p.get('geometry', {}).get('location', {}).get('lng', lng)))) <= 500])

        mult = 1.0
        for p in (raw_scol or []):
            if p: mult = min(1.6, mult + 0.20)
        for p in (raw_osp or []):
            if p: mult = min(1.6, mult + 0.12)
        for p in (raw_hotel or []):
            if p: mult = min(1.6, mult + 0.08)

        demo = get_demographic_data_al(qark, citta)
        n_poi_totali = len(pois)
        den_urbana = get_densita_urbana_al(qark, n_poi_totali)
        pop3  = int(den_urbana * math.pi * 0.240**2)
        pop5  = int(den_urbana * math.pi * 0.400**2)
        pop10 = int(den_urbana * math.pi * 0.800**2)

        ass = get_market_assessment_al(demo['reddito_medio'], den_urbana)
        sc  = ass['score']
        sc += (20 - conc500 * 4) if conc500 <= 5 else 0
        if gdo_500m >= 2: sc += 8
        elif gdo_500m == 1: sc += 4
        sc = min(100, max(0, sc))

        if   sc >= 70: slabel, scol2 = 'Shkelqyer', '#10b981'
        elif sc >= 55: slabel, scol2 = 'I mire',    '#3b82f6'
        elif sc >= 35: slabel, scol2 = 'Mesatar',   '#f59e0b'
        else:          slabel, scol2 = 'I dobet',   '#ef4444'

        return jsonify({
            'lat': lat, 'lng': lng,
            'pop_3min': pop3, 'pop_5min': pop5, 'pop_10min': pop10,
            'concorrenti_500m': conc500, 'concorrenti_1km': conc1k,
            'competitors_detail': comp_det,
            'pois': pois, 'mult_attractor': mult,
            'score': sc, 'score_zona': sc, 'score_label': slabel, 'score_colore': scol2,
            'demografici': {
                'densita': den_urbana, 'reddito_medio': demo['reddito_medio'],
                'eta_media': demo['eta_media'], 'perc_stranieri': demo['perc_stranieri'],
                'reddito_eur': demo['reddito_eur'],
            },
            'segnali_reali': {'gdo_500m': gdo_500m},
            'ins_data': {
                'perc_affittuari':       demo.get('perc_affittuari', 28),
                'perc_senza_lavatrice':  demo.get('perc_senza_lavatrice', 25),
                'perc_appartamenti':     demo.get('perc_appartamenti', 55),
                'mq_medi':               demo.get('mq_medi', 85),
                'studenti_uni_1000':     demo.get('studenti_uni_1000', 20),
                'tasso_disoccupazione':  demo.get('tasso_disoccupazione', 15.0),
                'eta_media':             demo.get('eta_media', 35),
                'reddito_medio':         demo.get('reddito_medio', 420000),
            },
            'paese': 'AL',
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'tb': traceback.format_exc()[-400:]}), 500

# ── API Business Plan ─────────────────────────────────────────────────────────
@al_bp.route('/api/calcola-bp', methods=['POST'])
@login_required
def calcola_bp_al():
    d = request.json or {}
    cambio = _cambio()
    n_std = int(d.get('n_std', 0)); n_med = int(d.get('n_med', 0))
    n_grd = int(d.get('n_grd', 0)); n_asc = int(d.get('n_asc', 0))
    t_std = float(d.get('t_std') or TARIFFE_DEFAULT_AL['lavaggio_std_all'])
    t_med = float(d.get('t_med') or TARIFFE_DEFAULT_AL['lavaggio_med_all'])
    t_grd = float(d.get('t_grd') or TARIFFE_DEFAULT_AL['lavaggio_grd_all'])
    t_asc = float(d.get('t_asc') or TARIFFE_DEFAULT_AL['asciugatura_all'])
    c500  = int(d.get('concorrenti_500m', 0)); c1k = int(d.get('concorrenti_1km', 0))
    den   = float(d.get('densita', 2500)); red = float(d.get('reddito_medio', 420000))
    gdo   = int(d.get('gdo_500m', 0)); mult = float(d.get('mult_attractor', 1.0))
    popc  = float(d.get('pop_comune', 0))
    sc_n  = d.get('scenario', 'realistico')

    if   c500 >= 5: ob = 0.08
    elif c500 == 4: ob = 0.20
    elif c500 == 3: ob = 0.28
    elif c500 == 2: ob = 0.35
    elif c500 == 1: ob = 0.42
    elif c1k  >= 4: ob = 0.48
    elif c1k  >= 2: ob = 0.52
    elif c1k  == 1: ob = 0.55
    else:            ob = OCC_BASE_AL

    corr = 0.0
    if den > 3000: corr += 0.04
    elif den < 200: corr -= 0.08
    if gdo >= 2: corr += 0.02
    if red > 800000: corr -= 0.04
    elif red < 280000: corr -= 0.05
    corr += min((mult - 1.0) * 0.10, 0.08)
    corr = max(-0.20, min(0.20, corr))

    fc  = get_f_qyteti_al(int(popc))
    msc = {'pessimistico': 0.70, 'realistico': 1.00, 'ottimistico': 1.30}.get(sc_n, 1.0)
    occ = min(0.75, ob * (1 + corr) * fc * msc)

    inc_all = ((n_std * 18 * t_std + n_med * 18 * t_med + n_grd * 18 * t_grd)
               + n_asc * 52 * t_asc) * occ * 30
    aff_all = float(d.get('affitto_all', 80000))
    cos_all = aff_all + inc_all * 0.28 + 15000
    uti_all = inc_all - cos_all
    cap_all = float(d.get('capex_all', 0))
    pb = (cap_all * 1.20 / uti_all / 12) if uti_all > 0 else 999

    return jsonify({
        'incasso_all':    round(inc_all),
        'incasso_eur':    round(converti_all_eur(inc_all)),
        'costi_all':      round(cos_all),
        'utile_all':      round(uti_all),
        'utile_eur':      round(converti_all_eur(uti_all)),
        'capex_all':      round(cap_all),
        'tva_all':        round(cap_all * 0.20),
        'occupazione_pct': round(occ * 100, 1),
        'f_qyteti':       round(fc, 2),
        'cambio_all':     cambio,
        'payback_anni':   round(pb, 1) if pb < 999 else None,
        'scenario':       sc_n,
        'valuta':         'ALL',
    })

# ── API Analisi AI ────────────────────────────────────────────────────────────
@al_bp.route('/api/analisi-ai', methods=['POST'])
@login_required
def analisi_ai_al():
    import traceback
    try:
        d       = request.json or {}
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        if not api_key:
            return jsonify({'errore': 'ANTHROPIC_API_KEY non configurata'}), 200
        cambio = _cambio()
        inc = float(d.get('incasso_all', 0) or 0)
        cos = float(d.get('costi_all',   0) or 0)
        cap = float(d.get('capex_all',   0) or 0)
        red = float(d.get('reddito_medio', 420000) or 420000)
        prompt = (
            "Sei un analista specializzato nel mercato delle lavanderie self-service in Albania. "
            "Produci un'analisi obiettiva della zona basata solo su dati e fatti. "
            "Scrivi prima in ITALIANO, poi in ALBANESE (Shqip).\n\n"
            f"LOKACIONI: {d.get('indirizzo', '')}, {d.get('citta', '')}, Shqiperia\n"
            f"Popullata 5 min: {int(d.get('pop_5min', 0)):,} banore\n"
            f"Densiteti: {int(d.get('densita', 0)):,} banore/km2\n"
            f"Te ardhura mesatare: {int(red):,} ALL/vit ({int(red/cambio):,} EUR/vit)\n"
            f"Konkurence self-service 500m: {d.get('concorrenti_500m', 0)}\n"
            f"Incasso stimato: {inc:,.0f} ALL/mese\n"
            f"Costi: {cos:,.0f} ALL/mese | Utile: {inc-cos:,.0f} ALL/mese\n"
            f"Investimento: {cap:,.0f} ALL + IVA 20%\n\n"
            "Analisi in 4 sezioni (max 350 parole totali):\n"
            "1. BACINO DEMOGRAFICO / PELLAZGU DEMOGRAFIK\n"
            "2. CONCORRENZA / KONKURENCA\n"
            "3. PROIEZIONE ECONOMICA / PROJEKSIONI EKONOMIK\n"
            "4. FATTORI DI RISCHIO / FAKTORET E RISKUT"
        )
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=1200,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return jsonify({'analisi': msg.content[0].text.strip(), 'mercato': 'AL'})
    except Exception as e:
        return jsonify({'errore': str(e), 'detail': traceback.format_exc()[-400:]}), 200

# ── API Cambio ────────────────────────────────────────────────────────────────
@al_bp.route('/api/cambio')
@login_required
def cambio_live():
    rate = _cambio()
    return jsonify({'eur_all': rate, 'all_eur': round(1 / rate, 6)})

# ── API Demografici ───────────────────────────────────────────────────────────
@al_bp.route('/api/demografici')
@login_required
def demografici():
    qark  = request.args.get('qark', '')
    qyteti = request.args.get('qyteti', '')
    demo  = get_demographic_data_al(qark, qyteti)
    ass   = get_market_assessment_al(demo['reddito_medio'], demo['densita'])
    return jsonify({**demo, **ass})

# ── Normativa Albania ─────────────────────────────────────────────────────────
@al_bp.route('/normativa')
@al_bp.route('/normativa/<int:pratica_id>')
@login_required
def normativa(pratica_id=None):
    if not _check_al(): return redirect(url_for('dashboard.index'))
    import datetime
    lingua = request.args.get('lingua', _get_lingua())
    norm   = NORMATIVA_AL.get(lingua, NORMATIVA_AL['it'])
    p = None; cliente_nome = ''; citta = ''
    if pratica_id:
        p = Pratica.query.get_or_404(pratica_id)
        cliente_nome = p.cliente.nome if p.cliente else ''
        citta        = p.citta or ''
    return render_template('albania/normativa_al.html',
        norm=norm, lingua=lingua,
        cliente_nome=cliente_nome, citta=citta,
        pratica_id=pratica_id, cambio_all=_cambio(),
        data_oggi=datetime.date.today().strftime('%d/%m/%Y'))

# ── Lingua ────────────────────────────────────────────────────────────────────
@al_bp.route('/lingua/<lang>')
@login_required
def set_lingua(lang):
    if lang in ('it', 'al'): session['lingua_al'] = lang
    return redirect(request.referrer or url_for('albania.dashboard'))

# ── Salva pratica ─────────────────────────────────────────────────────────────
@al_bp.route('/preventivo/nuovo', methods=['POST'])
@login_required
def salva_nuovo():
    if not _check_al(): return redirect(url_for('dashboard.index'))
    import datetime
    d = request.form
    cambio = float(d.get('cambio_all') or _cambio())
    c = Cliente(
        nome=d.get('cliente_nome', '').strip(),
        azienda=d.get('cliente_azienda', ''),
        email=d.get('cliente_email', ''),
        telefono=d.get('cliente_tel', '')
    )
    db.session.add(c); db.session.flush()
    count  = Pratica.query.filter_by(market='AL').count() + 1
    numero = f"AL-{datetime.date.today().year}-{count:04d}"
    p = Pratica(
        numero=numero, cliente_id=c.id, agente_id=current_user.id,
        market='AL', stato='bozza',
        indirizzo=d.get('indirizzo', ''), citta=d.get('citta', ''),
        cap=d.get('cap', ''), provincia=d.get('qark_cod', ''),
        mq=int(d.get('mq') or 60),
        lat=float(d.get('lat') or 0) or None,
        lng=float(d.get('lng') or 0) or None,
        affitto_mese=float(d.get('affitto_all') or 0),
        pop_3min=int(d.get('pop_3min') or 0),
        pop_5min=int(d.get('pop_5min') or 0),
        pop_10min=int(d.get('pop_10min') or 0),
        score_zona=float(d.get('score_zona') or 0),
        concorrenti_500m=int(d.get('concorrenti_500m') or 0),
        concorrenti_1km=int(d.get('concorrenti_1km') or 0),
        tariffa_lavaggio_std=float(d.get('t_std') or 600),
        tariffa_lavaggio_med=float(d.get('t_med') or 800),
        tariffa_lavaggio_grd=float(d.get('t_grd') or 1200),
        tariffa_asciugatura=float(d.get('t_asc') or 300),
        capex=float(d.get('capex_all') or 0),
        incasso_mese=float(d.get('incasso_eur') or 0),
        costi_mese=float(d.get('costi_eur') or 0),
        utile_mese=float(d.get('utile_eur') or 0),
        cambio_ron=cambio,
        valuta='ALL',
    )
    db.session.add(p); db.session.commit()
    return redirect(url_for('albania.modifica_preventivo', id=p.id))
