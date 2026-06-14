"""
routes/polonia.py — BIOLavaTU LaundryPro — Mercato Polonia
ISOLATO: zero import da geo.py, preventivo.py, investitore.py, istat.py, romania.py, albania.py.
"""
import os, json, math
import requests
from flask import (Blueprint, render_template, request, jsonify,
                   redirect, url_for, session)
from flask_login import login_required, current_user
from app import db
from models.pratica import Pratica
from models.cliente import Cliente
from models.settings import Settings
from services.normativa_polonia import NORMATIVA_PL
from services.ins_polonia import (
    get_demographic_data_pl, get_market_assessment_pl, get_f_miasto_pl,
    get_cambio_pln_live, converti_pln_eur, converti_eur_pln,
    get_densita_urbana_pl,
    calcola_potenziale_lavaggi_pl, calcola_incasso_da_lavaggi_pl,
    calcola_affitto_max_pl, calcola_costi_operativi_pl, calcola_saturazione_pl,
    TARIFFE_DEFAULT_PL, EUR_PLN_RATE, OCC_BASE_PL,
)

TR = {
    'it': {
        'nuovo': 'Nuova pratica', 'pratiche': 'Pratiche Polonia',
        'avanti': 'Avanti', 'indietro': 'Indietro',
        'analizza_zona': 'Analizza zona', 'genera_ai': 'Genera Analisi AI',
        'salva': 'Salva pratica', 'cliente': 'Cliente', 'sede': 'Sede',
        'zona': 'Zona', 'macchine': 'Macchine', 'business_plan': 'Business Plan',
        'riepilogo': 'Riepilogo',
    },
    'pl': {
        'nuovo': 'Nowa sprawa', 'pratiche': 'Sprawy Polska',
        'avanti': 'Dalej', 'indietro': 'Wstecz',
        'analizza_zona': 'Analizuj strefe', 'genera_ai': 'Generuj analize AI',
        'salva': 'Zapisz sprawe', 'cliente': 'Klient', 'sede': 'Siedziba',
        'zona': 'Strefa', 'macchine': 'Maszyny', 'business_plan': 'Biznesplan',
        'riepilogo': 'Podsumowanie',
    },
}

def _get_lingua():
    return session.get('lingua_pl', 'it')

pl_bp = Blueprint('polonia', __name__, url_prefix='/pl')
GMAPS_KEY  = os.environ.get('GMAPS_KEY', '')
PLACES_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'

def walking_radius(minutes): return minutes * 80

def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(math.radians(lng2-lng1)/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def gmaps_nearby(lat, lng, radius, place_type, keyword=None):
    params = {'location': f'{lat},{lng}', 'radius': radius, 'type': place_type,
              'key': GMAPS_KEY, 'language': 'it'}
    if keyword: params['keyword'] = keyword
    try:
        return requests.get(PLACES_URL, params=params, timeout=10).json().get('results', [])
    except: return []

def place_to_poi(place, lat_c, lng_c, categoria, colore, icon):
    try:
        plat = place['geometry']['location']['lat']
        plng = place['geometry']['location']['lng']
    except (KeyError, TypeError): return None
    return {'lat': plat, 'lng': plng, 'nome': place.get('name',''),
            'categoria': categoria, 'colore': colore, 'icon': icon,
            'distanza_m': int(haversine(lat_c, lng_c, plat, plng)),
            'rating': place.get('rating'), 'vicinity': place.get('vicinity','')}

def _check_pl():
    return current_user.role in ('owner','admin','segreteria') or \
           getattr(current_user, 'market', 'IT') == 'PL'

def _cambio():
    return get_cambio_pln_live()

# ── Dashboard ─────────────────────────────────────────────────────────────────
@pl_bp.route('/')
@login_required
def dashboard():
    if not _check_pl(): return redirect(url_for('dashboard.index'))
    pratiche = Pratica.query.filter_by(market='PL').order_by(Pratica.created.desc()).limit(20).all()
    ling = _get_lingua()
    return render_template('polonia/dashboard_pl.html',
        pratiche=pratiche, cambio_pln=_cambio(), lingua=ling, tr=TR.get(ling, TR['it']))

@pl_bp.route('/pratiche')
@login_required
def pratiche():
    if not _check_pl(): return redirect(url_for('dashboard.index'))
    pratiche = Pratica.query.filter_by(market='PL').order_by(Pratica.created.desc()).all()
    return render_template('polonia/pratiche_pl.html', pratiche=pratiche, cambio_pln=_cambio())

# ── Wizard ────────────────────────────────────────────────────────────────────
@pl_bp.route('/preventivo/nuovo', methods=['GET'])
@login_required
def nuovo_preventivo():
    if not _check_pl(): return redirect(url_for('dashboard.index'))
    ling = _get_lingua()
    return render_template('polonia/preventivo_pl.html',
        pratica=None, cambio_pln=_cambio(), tariffe=TARIFFE_DEFAULT_PL,
        settings=Settings.query.first(), lingua=ling, tr=TR.get(ling, TR['it']))

@pl_bp.route('/preventivo/<int:id>')
@login_required
def modifica_preventivo(id):
    if not _check_pl(): return redirect(url_for('dashboard.index'))
    p = Pratica.query.get_or_404(id)
    ling = _get_lingua()
    return render_template('polonia/preventivo_pl.html',
        pratica=p, cambio_pln=_cambio(), tariffe=TARIFFE_DEFAULT_PL,
        settings=Settings.query.first(), lingua=ling, tr=TR.get(ling, TR['it']))

# ── API Geocodifica ───────────────────────────────────────────────────────────
@pl_bp.route('/api/geocode')
@login_required
def geocode_pl():
    indirizzo = request.args.get('indirizzo','')
    citta     = request.args.get('citta','')
    woje      = request.args.get('woje','')
    if not GMAPS_KEY or not citta:
        return jsonify({'error': 'Parametri mancanti'}), 400
    addr = ', '.join(p for p in [indirizzo, citta, woje, 'Polska'] if p)
    try:
        r = requests.get('https://maps.googleapis.com/maps/api/geocode/json',
            params={'address': addr, 'key': GMAPS_KEY, 'region': 'pl', 'language': 'pl'},
            timeout=8).json()
        if r.get('status') != 'OK' or not r.get('results'):
            return jsonify({'error': f"Geocode: {r.get('status')}"}), 400
        loc  = r['results'][0]['geometry']['location']
        lat  = float(loc['lat']); lng = float(loc['lng'])
        demo = get_demographic_data_pl(woje, citta)
        ass  = get_market_assessment_pl(demo['reddito_medio'], demo['densita'])
        return jsonify({'lat': lat, 'lng': lng,
            'indirizzo_fmt': r['results'][0].get('formatted_address', addr),
            'reddito_medio': demo['reddito_medio'], 'reddito_eur': demo['reddito_eur'],
            'densita': demo['densita'], 'eta_media': demo['eta_media'],
            'potenziale': ass['potenziale'], 'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── API Zona-analisi ──────────────────────────────────────────────────────────
@pl_bp.route('/api/zona-analisi')
@login_required
def zona_analisi_pl():
    try:
        lat   = float(request.args.get('lat', 0) or 0)
        lng   = float(request.args.get('lng', 0) or 0)
        citta = request.args.get('citta','')
        woje  = request.args.get('provincia','')

        if (not lat or not lng) and citta and GMAPS_KEY:
            r = requests.get('https://maps.googleapis.com/maps/api/geocode/json',
                params={'address': citta+', Polska', 'key': GMAPS_KEY, 'region': 'pl'},
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
        raw_tram  = gmaps_nearby(lat, lng, r5,  'light_rail_station')
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

        add(raw_sup,    'supermarkety', '#22c55e', 'S')
        add(raw_conv,   'supermarkety', '#16a34a', 'S')
        add(raw_farm,   'apteki',       '#ec4899', 'F')
        add(raw_bar,    'bary',         '#f59e0b', 'B')
        add(raw_cafe,   'bary',         '#d97706', 'C')
        add(raw_rest,   'restauracje',  '#f97316', 'R')
        add(raw_bank,   'banki',        '#06b6d4', '$')
        add(raw_atm,    'banki',        '#0891b2', '$')
        add(raw_park,   'parkingi',     '#64748b', 'P')
        add(raw_bus,    'transport',    '#7c3aed', 'T')
        add(raw_tram,   'transport',    '#8b5cf6', 'T')
        add(raw_scol,   'edukacja',     '#0ea5e9', 'U')
        add(raw_scuola, 'edukacja',     '#0284c7', 'U')
        add(raw_osp,    'szpitale',     '#ef4444', 'H')
        add(raw_hotel,  'hotele',       '#a855f7', 'L')
        add(raw_gym,    'inne',         '#14b8a6', 'G')

        conc500 = 0; conc1k = 0; comp_det = []
        for c in (raw_lav or []):
            if not c: continue
            clat = float(c.get('geometry',{}).get('location',{}).get('lat', lat))
            clng = float(c.get('geometry',{}).get('location',{}).get('lng', lng))
            dist = int(haversine(lat, lng, clat, clng))
            if dist <= 500:  conc500 += 1
            if dist <= 1000: conc1k  += 1
            col = '#ef4444' if dist<=300 else '#f97316' if dist<=600 else '#22c55e'
            comp_det.append({'nome': c.get('name',''), 'distanza_m': dist,
                'rating': c.get('rating'), 'lat': clat, 'lng': clng, 'cerchio_colore': col})

        gdo_500m = len([p for p in (raw_sup or [])+(raw_conv or [])
            if p and int(haversine(lat, lng,
                float(p.get('geometry',{}).get('location',{}).get('lat', lat)),
                float(p.get('geometry',{}).get('location',{}).get('lng', lng)))) <= 500])

        mult = 1.0
        for p in (raw_scol or []):
            if p: mult = min(1.6, mult + 0.20)
        for p in (raw_osp or []):
            if p: mult = min(1.6, mult + 0.12)
        for p in (raw_hotel or []):
            if p: mult = min(1.6, mult + 0.08)

        demo = get_demographic_data_pl(woje, citta)
        den_urbana = get_densita_urbana_pl(woje, len(pois))
        pop3  = int(den_urbana * math.pi * 0.240**2)
        pop5  = int(den_urbana * math.pi * 0.400**2)
        pop10 = int(den_urbana * math.pi * 0.800**2)

        ass = get_market_assessment_pl(demo['reddito_medio'], den_urbana)
        sc  = ass['score']
        sc += (20 - conc500*4) if conc500 <= 5 else 0
        if gdo_500m >= 2: sc += 8
        elif gdo_500m == 1: sc += 4
        sc = min(100, max(0, sc))

        if   sc >= 70: slabel, scol2 = 'Doskonaly', '#10b981'
        elif sc >= 55: slabel, scol2 = 'Dobry',     '#3b82f6'
        elif sc >= 35: slabel, scol2 = 'Sredni',    '#f59e0b'
        else:          slabel, scol2 = 'Slaby',     '#ef4444'

        return jsonify({
            'lat': lat, 'lng': lng,
            'pop_3min': pop3, 'pop_5min': pop5, 'pop_10min': pop10,
            'concorrenti_500m': conc500, 'concorrenti_1km': conc1k,
            'competitors_detail': comp_det, 'pois': pois, 'mult_attractor': mult,
            'score': sc, 'score_zona': sc, 'score_label': slabel, 'score_colore': scol2,
            'demografici': {'densita': den_urbana, 'reddito_medio': demo['reddito_medio'],
                'eta_media': demo['eta_media'], 'perc_stranieri': demo['perc_stranieri'],
                'reddito_eur': demo['reddito_eur']},
            'segnali_reali': {'gdo_500m': gdo_500m},
            'ins_data': {
                'perc_affittuari':      demo.get('perc_affittuari', 14),
                'perc_senza_lavatrice': demo.get('perc_senza_lavatrice', 5),
                'perc_appartamenti':    demo.get('perc_appartamenti', 60),
                'mq_medi':              demo.get('mq_medi', 72),
                'studenti_uni_1000':    demo.get('studenti_uni_1000', 40),
                'tasso_disoccupazione': demo.get('tasso_disoccupazione', 5.2),
                'eta_media':            demo.get('eta_media', 42),
                'reddito_medio':        demo.get('reddito_medio', 64000),
            },
            'paese': 'PL',
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'tb': traceback.format_exc()[-400:]}), 500

# ── API Business Plan ─────────────────────────────────────────────────────────
@pl_bp.route('/api/calcola-bp', methods=['POST'])
@login_required
def calcola_bp_pl():
    d = request.json or {}
    cambio = _cambio()
    n_std = int(d.get('n_std',0)); n_med = int(d.get('n_med',0))
    n_grd = int(d.get('n_grd',0)); n_asc = int(d.get('n_asc',0))
    t_std = float(d.get('t_std') or TARIFFE_DEFAULT_PL['lavaggio_std_pln'])
    t_med = float(d.get('t_med') or TARIFFE_DEFAULT_PL['lavaggio_med_pln'])
    t_grd = float(d.get('t_grd') or TARIFFE_DEFAULT_PL['lavaggio_grd_pln'])
    t_asc = float(d.get('t_asc') or TARIFFE_DEFAULT_PL['asciugatura_pln'])
    c500  = int(d.get('concorrenti_500m',0)); c1k = int(d.get('concorrenti_1km',0))
    den   = float(d.get('densita', 4000)); red = float(d.get('reddito_medio', 64000))
    gdo   = int(d.get('gdo_500m',0)); mult = float(d.get('mult_attractor',1.0))
    popc  = float(d.get('pop_comune',0)); sc_n = d.get('scenario','realistico')

    if   c500 >= 5: ob = 0.08
    elif c500 == 4: ob = 0.20
    elif c500 == 3: ob = 0.28
    elif c500 == 2: ob = 0.35
    elif c500 == 1: ob = 0.42
    elif c1k  >= 4: ob = 0.48
    elif c1k  >= 2: ob = 0.52
    elif c1k  == 1: ob = 0.55
    else:            ob = OCC_BASE_PL

    corr = 0.0
    if den > 4000: corr += 0.04
    elif den < 500: corr -= 0.06
    if gdo >= 2: corr += 0.02
    if red > 90000: corr -= 0.02
    elif red < 45000: corr -= 0.04
    corr += min((mult-1.0)*0.10, 0.08)
    corr = max(-0.20, min(0.20, corr))

    fc  = get_f_miasto_pl(int(popc))
    msc = {'pessimistico':0.70,'realistico':1.00,'ottimistico':1.30}.get(sc_n, 1.0)
    occ = min(0.75, ob*(1+corr)*fc*msc)

    inc_pln = ((n_std*18*t_std + n_med*18*t_med + n_grd*18*t_grd) + n_asc*52*t_asc)*occ*30
    aff_pln = float(d.get('affitto_pln', 3000))
    cos_pln = aff_pln + inc_pln*0.28 + 400
    uti_pln = inc_pln - cos_pln
    cap_pln = float(d.get('capex_pln', 0))
    pb = (cap_pln*1.23/uti_pln/12) if uti_pln > 0 else 999

    return jsonify({
        'incasso_pln': round(inc_pln), 'incasso_eur': round(converti_pln_eur(inc_pln)),
        'costi_pln':   round(cos_pln), 'utile_pln':   round(uti_pln),
        'utile_eur':   round(converti_pln_eur(uti_pln)),
        'capex_pln':   round(cap_pln), 'tva_pln':     round(cap_pln*0.23),
        'occupazione_pct': round(occ*100,1), 'f_miasto': round(fc,2),
        'cambio_pln': cambio, 'payback_anni': round(pb,1) if pb<999 else None,
        'scenario': sc_n, 'valuta': 'PLN',
    })

# ── API Analisi AI ────────────────────────────────────────────────────────────
@pl_bp.route('/api/analisi-ai', methods=['POST'])
@login_required
def analisi_ai_pl():
    import traceback
    try:
        d = request.json or {}
        api_key = os.environ.get('ANTHROPIC_API_KEY','')
        if not api_key: return jsonify({'errore':'ANTHROPIC_API_KEY non configurata'}), 200
        cambio = _cambio()
        inc = float(d.get('incasso_pln',0) or 0)
        cos = float(d.get('costi_pln',  0) or 0)
        cap = float(d.get('capex_pln',  0) or 0)
        red = float(d.get('reddito_medio',64000) or 64000)
        prompt = (
            "Sei un analista specializzato nel mercato delle lavanderie self-service in Polonia. "
            "Produci un'analisi obiettiva della zona. Scrivi prima in ITALIANO, poi in POLACCO (Polski).\n\n"
            f"LOKALIZACJA: {d.get('indirizzo','')}, {d.get('citta','')}, Polska\n"
            f"Populacja 5 min: {int(d.get('pop_5min',0)):,} osob\n"
            f"Gestosc: {int(d.get('densita',0)):,} os/km2\n"
            f"Srednie wynagrodzenie: {int(red):,} PLN/rok ({int(red/cambio):,} EUR/rok)\n"
            f"Konkurencja self-service 500m: {d.get('concorrenti_500m',0)}\n"
            f"Przychody szacowane: {inc:,.0f} PLN/mies\n"
            f"Koszty: {cos:,.0f} PLN/mies | Zysk: {inc-cos:,.0f} PLN/mies\n"
            f"Inwestycja: {cap:,.0f} PLN + VAT 23%\n\n"
            "Analisi in 4 sezioni (max 350 parole):\n"
            "1. BACINO DEMOGRAFICO / BASEN DEMOGRAFICZNY\n"
            "2. CONCORRENZA / KONKURENCJA\n"
            "3. PROIEZIONE ECONOMICA / PROJEKCJA EKONOMICZNA\n"
            "4. FATTORI DI RISCHIO / CZYNNIKI RYZYKA"
        )
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(model='claude-sonnet-4-6', max_tokens=1200,
            messages=[{'role':'user','content':prompt}])
        return jsonify({'analisi': msg.content[0].text.strip(), 'mercato': 'PL'})
    except Exception as e:
        return jsonify({'errore': str(e), 'detail': traceback.format_exc()[-400:]}), 200

# ── API Cambio ────────────────────────────────────────────────────────────────
@pl_bp.route('/api/cambio')
@login_required
def cambio_live():
    rate = _cambio()
    return jsonify({'eur_pln': rate, 'pln_eur': round(1/rate, 6)})

# ── API Demografici ───────────────────────────────────────────────────────────
@pl_bp.route('/api/demografici')
@login_required
def demografici():
    woje   = request.args.get('woje','')
    miasto = request.args.get('miasto','')
    demo   = get_demographic_data_pl(woje, miasto)
    ass    = get_market_assessment_pl(demo['reddito_medio'], demo['densita'])
    return jsonify({**demo, **ass})

# ── Normativa ─────────────────────────────────────────────────────────────────
@pl_bp.route('/normativa')
@pl_bp.route('/normativa/<int:pratica_id>')
@login_required
def normativa(pratica_id=None):
    if not _check_pl(): return redirect(url_for('dashboard.index'))
    import datetime
    lingua = request.args.get('lingua', _get_lingua())
    norm   = NORMATIVA_PL.get(lingua, NORMATIVA_PL['it'])
    p = None; cliente_nome = ''; citta = ''
    if pratica_id:
        p = Pratica.query.get_or_404(pratica_id)
        cliente_nome = p.cliente.nome if p.cliente else ''
        citta        = p.citta or ''
    return render_template('polonia/normativa_pl.html',
        norm=norm, lingua=lingua, cliente_nome=cliente_nome, citta=citta,
        pratica_id=pratica_id, cambio_pln=_cambio(),
        data_oggi=datetime.date.today().strftime('%d/%m/%Y'))

# ── Lingua ────────────────────────────────────────────────────────────────────
@pl_bp.route('/lingua/<lang>')
@login_required
def set_lingua(lang):
    if lang in ('it','pl'): session['lingua_pl'] = lang
    return redirect(request.referrer or url_for('polonia.dashboard'))

# ── Salva pratica ─────────────────────────────────────────────────────────────
@pl_bp.route('/preventivo/nuovo', methods=['POST'])
@login_required
def salva_nuovo():
    if not _check_pl(): return redirect(url_for('dashboard.index'))
    import datetime
    d = request.form; cambio = float(d.get('cambio_pln') or _cambio())
    c = Cliente(nome=d.get('cliente_nome','').strip(), azienda=d.get('cliente_azienda',''),
                email=d.get('cliente_email',''), telefono=d.get('cliente_tel',''))
    db.session.add(c); db.session.flush()
    count  = Pratica.query.filter_by(market='PL').count() + 1
    numero = f"PL-{datetime.date.today().year}-{count:04d}"
    p = Pratica(
        numero=numero, cliente_id=c.id, agente_id=current_user.id,
        market='PL', stato='bozza',
        indirizzo=d.get('indirizzo',''), citta=d.get('citta',''),
        cap=d.get('cap',''), provincia=d.get('woje_cod',''),
        mq=int(d.get('mq') or 60),
        lat=float(d.get('lat') or 0) or None, lng=float(d.get('lng') or 0) or None,
        affitto_mese=float(d.get('affitto_pln') or 0),
        pop_3min=int(d.get('pop_3min') or 0), pop_5min=int(d.get('pop_5min') or 0),
        pop_10min=int(d.get('pop_10min') or 0),
        score_zona=float(d.get('score_zona') or 0),
        concorrenti_500m=int(d.get('concorrenti_500m') or 0),
        concorrenti_1km=int(d.get('concorrenti_1km') or 0),
        tariffa_lavaggio_std=float(d.get('t_std') or 20),
        tariffa_lavaggio_med=float(d.get('t_med') or 26),
        tariffa_lavaggio_grd=float(d.get('t_grd') or 36),
        tariffa_asciugatura=float(d.get('t_asc') or 10),
        capex=float(d.get('capex_pln') or 0),
        incasso_mese=float(d.get('incasso_eur') or 0),
        costi_mese=float(d.get('costi_eur') or 0),
        utile_mese=float(d.get('utile_eur') or 0),
        cambio_ron=cambio, valuta='PLN',
    )
    db.session.add(p); db.session.commit()
    return redirect(url_for('polonia.modifica_preventivo', id=p.id))
