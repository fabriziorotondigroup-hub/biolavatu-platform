"""
routes/romania.py — BIOLavaTU LaundryPro — Mercato Romania
ISOLATO: zero import da geo.py, preventivo.py, investitore.py, istat.py.
"""
import os, json, math
import requests as _req
from flask import (Blueprint, render_template, request, jsonify,
                   redirect, url_for, session, flash)
from flask_login import login_required, current_user
from app import db
from models.pratica import Pratica
from models.cliente import Cliente
from models.settings import Settings
from services.ins_romania import (
    get_demographic_data_ro, get_market_assessment_ro, get_f_citta_ro,
    get_cambio_ron_live, converti_ron_eur, converti_eur_ron,
    TARIFFE_DEFAULT_RO, EUR_RON_RATE, OCC_BASE_RO,
)


# ── Dizionario traduzioni IT / RO ────────────────────────────────────────────
TR = {
    'it': {
        'dashboard':        'Dashboard',
        'nuovo':            'Nuova pratica',
        'pratiche':         'Pratiche Romania',
        'venditori':        'Venditori Romania',
        'nuovo_venditore':  'Nuovo Venditore RO',
        'cliente':          'Cliente',
        'sede':             'Sede',
        'zona':             'Zona',
        'macchine':         'Macchine',
        'business_plan':    'Business Plan',
        'riepilogo':        'Riepilogo',
        'salva':            'Salva pratica',
        'avanti':           'Avanti →',
        'indietro':         '← Indietro',
        'analizza_zona':    'Analizza zona',
        'genera_ai':        'Genera Analisi AI',
        'incasari':         'Incasari lunare',
        'profit':           'Profit net',
        'investitie':       'Investimento',
        'ocupare':          'Occupazione',
        'curs':             '1 EUR =',
        'ron':              'RON',
        'nome':             'Nome',
        'email':            'Email',
        'telefon':          'Telefono',
        'oras':             'Città',
        'judet':            'Judet / Provincia',
        'suprafata':        'Superficie (mq)',
        'chirie':           'Affitto mensile (RON)',
        'tip_zona':         'Tipo zona',
        'strada':           'Via e numero civico',
        'pesimist':         'Pessimistico',
        'realist':          'Realistico',
        'optimist':         'Ottimistico',
        'populatie':        'Popolazione raggiungibile',
        'scor_zona':        'Score zona',
        'concurenta':       'Concorrenza',
        'conc_500':         'Self-service 500m',
        'conc_1km':         'Tutte 1km',
        'rol':              'Ruolo',
        'activ':            'Attivo',
        'creat':            'Creato',
        'actiuni':          'Azioni',
    },
    'ro': {
        'dashboard':        'Panou de control',
        'nuovo':            'Dosar nou',
        'pratiche':         'Dosare Romania',
        'venditori':        'Agenti Romania',
        'nuovo_venditore':  'Agent nou RO',
        'cliente':          'Client',
        'sede':             'Sediu',
        'zona':             'Zona',
        'macchine':         'Utilaje',
        'business_plan':    'Plan de afaceri',
        'riepilogo':        'Rezumat',
        'salva':            'Salveaza dosarul',
        'avanti':           'Inainte →',
        'indietro':         '← Inapoi',
        'analizza_zona':    'Analizeaza zona',
        'genera_ai':        'Genereaza Analiza AI',
        'incasari':         'Incasari lunare',
        'profit':           'Profit net',
        'investitie':       'Investitie',
        'ocupare':          'Ocupare',
        'curs':             '1 EUR =',
        'ron':              'RON',
        'nome':             'Nume',
        'email':            'Email',
        'telefon':          'Telefon',
        'oras':             'Oras',
        'judet':            'Judet',
        'suprafata':        'Suprafata (mp)',
        'chirie':           'Chirie lunara (RON)',
        'tip_zona':         'Tip zona',
        'strada':           'Strada si numar',
        'pesimist':         'Pesimist',
        'realist':          'Realist',
        'optimist':         'Optimist',
        'populatie':        'Populatie accesibila',
        'scor_zona':        'Scor zona',
        'concurenta':       'Concurenta',
        'conc_500':         'Spalatorii 500m',
        'conc_1km':         'Total 1km',
        'rol':              'Rol',
        'activ':            'Activ',
        'creat':            'Creat',
        'actiuni':          'Actiuni',
    }
}

def _tr(key, lingua='it'):
    return TR.get(lingua, TR['it']).get(key, key)

def _get_lingua():
    from flask import session
    return session.get('lingua', 'it')

ro_bp = Blueprint('romania', __name__, url_prefix='/ro')
GMAPS_KEY = os.environ.get('GMAPS_KEY', '')


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


# ── Accesso ───────────────────────────────────────────────────────────────────
def _check_ro():
    return current_user.role in ('owner','admin','segreteria') or \
           getattr(current_user,'market','IT') == 'RO'

def _cambio():
    return get_cambio_ron_live()

# ── Dashboard ─────────────────────────────────────────────────────────────────
@ro_bp.route('/')
@login_required
def dashboard():
    if not _check_ro(): return redirect(url_for('dashboard.index'))
    pratiche = Pratica.query.filter_by(market='RO').order_by(Pratica.created.desc()).limit(20).all()
    ling = _get_lingua()
    return render_template('romania/dashboard_ro.html',
        pratiche=pratiche, cambio_ron=_cambio(),
        lingua=ling, tr=TR.get(ling, TR['it']))

@ro_bp.route('/pratiche')
@login_required
def pratiche():
    if not _check_ro(): return redirect(url_for('dashboard.index'))
    pratiche = Pratica.query.filter_by(market='RO').order_by(Pratica.created.desc()).all()
    return render_template('romania/pratiche_ro.html',
        pratiche=pratiche, cambio_ron=_cambio())

# ── Wizard ────────────────────────────────────────────────────────────────────
@ro_bp.route('/preventivo/nuovo', methods=['GET'])
@login_required
def nuovo_preventivo():
    if not _check_ro(): return redirect(url_for('dashboard.index'))
    ling = _get_lingua()
    return render_template('romania/preventivo_ro.html',
        pratica=None, cambio_ron=_cambio(),
        tariffe=TARIFFE_DEFAULT_RO, settings=Settings.query.first(),
        lingua=ling, tr=TR.get(ling, TR['it']))

@ro_bp.route('/preventivo/<int:id>')
@login_required
def modifica_preventivo(id):
    if not _check_ro(): return redirect(url_for('dashboard.index'))
    p = Pratica.query.get_or_404(id)
    ling = _get_lingua()
    return render_template('romania/preventivo_ro.html',
        pratica=p, cambio_ron=_cambio(),
        tariffe=TARIFFE_DEFAULT_RO, settings=Settings.query.first(),
        lingua=ling, tr=TR.get(ling, TR['it']))

# ── API Geocodifica ───────────────────────────────────────────────────────────
@ro_bp.route('/api/geocode')
@login_required
def geocode_ro():
    indirizzo = request.args.get('indirizzo','')
    citta     = request.args.get('citta','')
    judet     = request.args.get('judet','')
    if not GMAPS_KEY or not citta:
        return jsonify({'error':'Parametri mancanti'}), 400
    addr = ', '.join(p for p in [indirizzo, citta, judet, 'Romania'] if p)
    try:
        r = _req.get('https://maps.googleapis.com/maps/api/geocode/json',
            params={'address':addr,'key':GMAPS_KEY,'region':'ro','language':'ro'},
            timeout=8).json()
        if r.get('status') != 'OK' or not r.get('results'):
            return jsonify({'error': f"Geocode: {r.get('status')}"}), 400
        loc  = r['results'][0]['geometry']['location']
        lat  = float(loc['lat']); lng = float(loc['lng'])
        demo = get_demographic_data_ro(judet, citta)
        ass  = get_market_assessment_ro(demo['reddito_medio'], demo['densita'])
        return jsonify({'lat':lat,'lng':lng,
            'indirizzo_fmt': r['results'][0].get('formatted_address', addr),
            'reddito_medio': demo['reddito_medio'],
            'reddito_eur':   demo['reddito_eur'],
            'densita':       demo['densita'],
            'eta_media':     demo['eta_media'],
            'potenziale':    ass['potenziale'],
            'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── API Zona-analisi Romania ──────────────────────────────────────────────────
@ro_bp.route('/api/zona-analisi')
@login_required
def zona_analisi_ro():
    try:
        lat      = float(request.args.get('lat',0) or 0)
        lng      = float(request.args.get('lng',0) or 0)
        citta    = request.args.get('citta','')
        judet    = request.args.get('provincia','')

        if (not lat or not lng) and citta and GMAPS_KEY:
            r = _req.get('https://maps.googleapis.com/maps/api/geocode/json',
                params={'address': citta+', Romania','key':GMAPS_KEY,'region':'ro'},
                timeout=5).json()
            if r.get('status') == 'OK' and r.get('results'):
                loc = r['results'][0]['geometry']['location']
                lat, lng = float(loc['lat']), float(loc['lng'])

        if not lat or not lng:
            return jsonify({'error':'Coordinate mancanti'}), 400

        r3 = walking_radius(3); r5 = walking_radius(5); r10 = walking_radius(10)

        raw_sup  = gmaps_nearby(lat, lng, r10, 'supermarket')
        raw_conv = gmaps_nearby(lat, lng, r5,  'convenience_store')
        raw_farm = gmaps_nearby(lat, lng, r5,  'pharmacy')
        raw_bar  = gmaps_nearby(lat, lng, r5,  'bar')
        raw_rest = gmaps_nearby(lat, lng, r5,  'restaurant')
        raw_park = gmaps_nearby(lat, lng, r5,  'parking')
        raw_metro= gmaps_nearby(lat, lng, r5,  'subway_station')
        raw_bus  = gmaps_nearby(lat, lng, r5,  'bus_station')
        raw_scol = gmaps_nearby(lat, lng, r10, 'university')
        raw_osp  = gmaps_nearby(lat, lng, r10, 'hospital')
        raw_lav  = gmaps_nearby(lat, lng, r10, 'laundry')

        pois = []
        def add(places, cat, col, icon):
            for p in (places or []):
                poi = place_to_poi(p, lat, lng, cat, col, icon)
                if poi: pois.append(poi)

        add(raw_sup,  'supermercati','#22c55e','🛒')
        add(raw_farm, 'farmacie',    '#ec4899','💊')
        add(raw_bar,  'bar',         '#f59e0b','☕')
        add(raw_rest, 'ristoranti',  '#f97316','🍽️')
        add(raw_park, 'parcheggi',   '#64748b','🅿️')
        add(raw_metro,'trasporti',   '#6d28d9','🚇')
        add(raw_bus,  'trasporti',   '#7c3aed','🚌')
        add(raw_scol, 'istruzione',  '#0ea5e9','🎓')
        add(raw_osp,  'ospedali',    '#ef4444','🏥')

        conc500 = 0; conc1k = 0; comp_det = []
        for c in (raw_lav or []):
            if not c: continue
            clat = float(c.get('geometry',{}).get('location',{}).get('lat', lat))
            clng = float(c.get('geometry',{}).get('location',{}).get('lng', lng))
            dist = int(haversine(lat, lng, clat, clng) * 1000)
            if dist <= 500:  conc500 += 1
            if dist <= 1000: conc1k  += 1
            col  = '#ef4444' if dist<=300 else '#f97316' if dist<=600 else '#22c55e'
            sat  = 'alta' if dist<=300 else 'media' if dist<=600 else 'bassa'
            comp_det.append({'nome':c.get('name',''),'distanza_m':dist,
                'rating':c.get('rating'),'lat':clat,'lng':clng,
                'raggio_copertura':300,'cerchio_colore':col,'saturazione':sat})

        gdo_500m = len([p for p in (raw_sup or [])+(raw_conv or []) if p and
            int(haversine(lat, lng,
                float(p.get('geometry',{}).get('location',{}).get('lat',lat)),
                float(p.get('geometry',{}).get('location',{}).get('lng',lng)))*1000) <= 500])

        tutti = (raw_bar or []) + (raw_rest or []) + (raw_sup or [])
        recen = sum(int(p.get('user_ratings_total',0) or 0) for p in tutti if p)

        mult = 1.0
        for p in (raw_scol or []):
            if p: mult = min(1.6, mult + 0.20)
        for p in (raw_osp or []):
            if p: mult = min(1.6, mult + 0.12)

        demo = get_demographic_data_ro(judet, citta)
        den  = float(demo['densita'])
        pop3  = int(den * math.pi * 0.240**2)
        pop5  = int(den * math.pi * 0.400**2)
        pop10 = int(den * math.pi * 0.800**2)

        ass = get_market_assessment_ro(demo['reddito_medio'], den)
        sc  = ass['score']
        sc += (20 - conc500*4) if conc500 <= 5 else 0
        if gdo_500m >= 2: sc += 8
        elif gdo_500m == 1: sc += 4
        sc = min(100, max(0, sc))

        if   sc >= 70: slabel, scol2 = 'Excelent','#10b981'
        elif sc >= 55: slabel, scol2 = 'Bun',     '#3b82f6'
        elif sc >= 35: slabel, scol2 = 'Mediu',   '#f59e0b'
        else:          slabel, scol2 = 'Slab',    '#ef4444'

        fam5  = pop5 // 3
        idx_f = fam5 // max(1, conc1k)

        return jsonify({
            'lat':lat,'lng':lng,
            'pop_3min':pop3,'pop_5min':pop5,'pop_10min':pop10,
            'concorrenti_500m':conc500,'concorrenti_1km':conc1k,
            'competitors_detail':comp_det,
            'pois':pois,'attractor_points':[],'mult_attractor':mult,
            'score':sc,'score_zona':sc,'score_label':slabel,'score_colore':scol2,
            'demografici':{'densita':den,'reddito_medio':demo['reddito_medio'],
                'eta_media':demo['eta_media'],'perc_stranieri':demo['perc_stranieri'],
                'reddito_eur':demo['reddito_eur']},
            'segnali_reali':{'recensioni_zona':recen,'gdo_500m':gdo_500m},
            'mobilita':{'n_metro':len(raw_metro or []),'n_bus':len(raw_bus or []),
                'n_parcheggi':len(raw_park or [])},
            'indice_famiglie_lav':{'indice':idx_f,'famiglie':fam5},
            'paese':'RO',
        })
    except Exception as e:
        import traceback
        print(f"[zona_ro] {traceback.format_exc()}")
        return jsonify({'error':str(e)}), 500

# ── API Business Plan ─────────────────────────────────────────────────────────
@ro_bp.route('/api/calcola-bp', methods=['POST'])
@login_required
def calcola_bp_ro():
    d = request.json or {}
    cambio = _cambio()
    n_std = int(d.get('n_std',0)); n_med = int(d.get('n_med',0))
    n_grd = int(d.get('n_grd',0)); n_asc = int(d.get('n_asc',0))
    t_std = float(d.get('t_std') or TARIFFE_DEFAULT_RO['lavaggio_std_ron'])
    t_med = float(d.get('t_med') or TARIFFE_DEFAULT_RO['lavaggio_med_ron'])
    t_grd = float(d.get('t_grd') or TARIFFE_DEFAULT_RO['lavaggio_grd_ron'])
    t_asc = float(d.get('t_asc') or TARIFFE_DEFAULT_RO['asciugatura_ron'])
    c500  = int(d.get('concorrenti_500m',0)); c1k = int(d.get('concorrenti_1km',0))
    den   = float(d.get('densita',500)); red = float(d.get('reddito_medio',30000))
    gdo   = int(d.get('gdo_500m',0));   rec = float(d.get('recensioni_zona',0))
    mult  = float(d.get('mult_attractor',1.0))
    popc  = float(d.get('pop_comune',0))
    sc_n  = d.get('scenario','realistico')

    if   c500 >= 5: ob = 0.08
    elif c500 == 4: ob = 0.20
    elif c500 == 3: ob = 0.28
    elif c500 == 2: ob = 0.35
    elif c500 == 1: ob = 0.42
    elif c1k  >= 4: ob = 0.48
    elif c1k  >= 2: ob = 0.52
    elif c1k  == 1: ob = 0.55
    else:            ob = OCC_BASE_RO

    corr = 0.0
    if den > 3000: corr += 0.04
    elif den < 200: corr -= 0.08
    if rec > 80000: corr += 0.04
    elif rec < 5000: corr -= 0.06
    if gdo >= 2: corr += 0.02
    if red > 60000: corr -= 0.04
    elif red < 18000: corr -= 0.05
    corr += min((mult-1.0)*0.10, 0.08)
    corr = max(-0.20, min(0.20, corr))

    fc  = get_f_citta_ro(int(popc))
    msc = {'pessimistico':0.70,'realistico':1.00,'ottimistico':1.30}.get(sc_n, 1.0)
    occ = min(0.75, ob*(1+corr)*fc*msc)

    inc_ron = ((n_std*18*t_std + n_med*18*t_med + n_grd*18*t_grd) + n_asc*52*t_asc) * occ * 30
    aff_ron = float(d.get('affitto_ron', 3000))
    cos_ron = aff_ron + inc_ron*0.28 + 1300
    uti_ron = inc_ron - cos_ron
    cap_ron = float(d.get('capex_ron', 0))
    pb = (cap_ron*1.19/uti_ron/12) if uti_ron > 0 else 999

    return jsonify({
        'incasso_ron':round(inc_ron),'incasso_eur':round(converti_ron_eur(inc_ron)),
        'costi_ron':round(cos_ron),'utile_ron':round(uti_ron),
        'utile_eur':round(converti_ron_eur(uti_ron)),
        'capex_ron':round(cap_ron),'tva_ron':round(cap_ron*0.19),
        'occupazione_pct':round(occ*100,1),'f_citta':round(fc,2),
        'cambio_ron':cambio,'payback_anni':round(pb,1) if pb<999 else None,
        'scenario':sc_n,'valuta':'RON',
    })

# ── API Analisi AI Romania ────────────────────────────────────────────────────
@ro_bp.route('/api/analisi-ai', methods=['POST'])
@login_required
def analisi_ai_ro():
    import anthropic as _anth
    d = request.json or {}
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'errore':'ANTHROPIC_API_KEY non configurata'}), 500
    cambio = _cambio()
    inc = float(d.get('incasso_ron',0) or 0)
    cos = float(d.get('costi_ron',0) or 0)
    cap = float(d.get('capex_ron',0) or 0)
    prompt = (
        "Sei un analista di piata din Romania specializat in spalatorii self-service. "
        "Produce o analiza obiectiva - doar date si fapte. "
        "Scrie in ITALIANA poi ROMANA.\n\n"
        f"LOCATIE: {d.get('indirizzo','')}, {d.get('citta','')}, Romania\n"
        f"Pop 5 min: {int(d.get('pop_5min',0)):,} ab | "
        f"Densitate: {int(d.get('densita',0)):,} loc/km2\n"
        f"Salariu: {int(d.get('reddito_medio',0)):,} RON/an "
        f"(EUR {int(d.get('reddito_medio',0)/cambio):,}/an)\n"
        f"Concurenta: {d.get('concorrenti_500m',0)} spalatorii 500m\n"
        f"Incasari stimate: {inc:,.0f} RON/luna | Costuri: {cos:,.0f} RON\n"
        f"Profit: {inc-cos:,.0f} RON/luna | Investitie: {cap:,.0f} RON + TVA 19%\n\n"
        "Analiza in 4 sectiuni (max 400 cuvinte):\n"
        "1. BACIN DEMOGRAFIC / BACINO DEMOGRAFICO\n"
        "2. CONCURENTA / CONCORRENZA\n"
        "3. PROIECTIE ECONOMICA / PROIEZIONE ECONOMICA\n"
        "4. FACTORI DE RISC / FATTORI DI RISCHIO"
    )
    try:
        msg = _anth.Anthropic(api_key=api_key).messages.create(
            model='claude-sonnet-4-5', max_tokens=1200,
            messages=[{'role':'user','content':prompt}])
        return jsonify({'analisi':msg.content[0].text.strip(),'mercato':'RO'})
    except Exception as e:
        import traceback
        return jsonify({'errore':str(e),'detail':traceback.format_exc()[:300]}), 500

# ── API Cambio ────────────────────────────────────────────────────────────────
@ro_bp.route('/api/cambio')
@login_required
def cambio_live():
    rate = _cambio()
    return jsonify({'eur_ron':rate,'ron_eur':round(1/rate,6)})

# ── API Demografici ───────────────────────────────────────────────────────────
@ro_bp.route('/api/demografici')
@login_required
def demografici():
    judet = request.args.get('judet',''); oras = request.args.get('oras','')
    demo  = get_demographic_data_ro(judet, oras)
    ass   = get_market_assessment_ro(demo['reddito_medio'], demo['densita'])
    return jsonify({**demo, **ass})

# ── Salva pratica ─────────────────────────────────────────────────────────────
@ro_bp.route('/preventivo/nuovo', methods=['POST'])
@login_required
def salva_nuovo():
    if not _check_ro(): return redirect(url_for('dashboard.index'))
    import datetime
    d = request.form; cambio = float(d.get('cambio_ron') or _cambio())
    c = Cliente(nome=d.get('cliente_nome','').strip(),
                azienda=d.get('cliente_azienda',''),
                email=d.get('cliente_email',''),
                telefono=d.get('cliente_tel',''))
    db.session.add(c); db.session.flush()
    count  = Pratica.query.filter_by(market='RO').count() + 1
    numero = f"RO-{datetime.date.today().year}-{count:04d}"
    p = Pratica(
        numero=numero, cliente_id=c.id, agente_id=current_user.id,
        market='RO', stato='bozza',
        indirizzo=d.get('indirizzo',''), citta=d.get('citta',''),
        cap=d.get('cap',''), provincia=d.get('judet_cod',''),
        mq=int(d.get('mq') or 60),
        lat=float(d.get('lat') or 0) or None,
        lng=float(d.get('lng') or 0) or None,
        affitto_mese=float(d.get('affitto_ron') or 0),
        pop_3min=int(d.get('pop_3min') or 0),
        pop_5min=int(d.get('pop_5min') or 0),
        pop_10min=int(d.get('pop_10min') or 0),
        score_zona=float(d.get('score_zona') or 0),
        concorrenti_500m=int(d.get('concorrenti_500m') or 0),
        concorrenti_1km=int(d.get('concorrenti_1km') or 0),
        tariffa_lavaggio_std=float(d.get('t_std') or 20),
        tariffa_lavaggio_med=float(d.get('t_med') or 25),
        tariffa_lavaggio_grd=float(d.get('t_grd') or 35),
        tariffa_asciugatura=float(d.get('t_asc') or 5),
        capex=float(d.get('capex_ron') or 0),
        incasso_mese=float(d.get('incasso_eur') or 0),
        costi_mese=float(d.get('costi_eur') or 0),
        utile_mese=float(d.get('utile_eur') or 0),
    )
    db.session.add(p); db.session.commit()
    return redirect(url_for('romania.modifica_preventivo', id=p.id))

# ── Lingua ────────────────────────────────────────────────────────────────────
@ro_bp.route('/lingua/<lang>')
@login_required
def set_lingua(lang):
    if lang in ('it','ro'): session['lingua'] = lang
    return redirect(request.referrer or url_for('romania.dashboard'))


# ── Venditori Romania ─────────────────────────────────────────────────────────

@ro_bp.route('/venditori')
@login_required
def venditori():
    if not _check_ro(): return redirect(url_for('dashboard.index'))
    if not current_user.can_manage_venditori:
        flash('Accesso negato.', 'error')
        return redirect(url_for('romania.dashboard'))
    ling = _get_lingua()
    agenti = User.query.filter(
        User.market == 'RO',
        User.role.in_(('sales', 'sales_ro', 'admin'))
    ).order_by(User.created.desc()).all()
    return render_template('romania/venditori_ro.html',
        agenti=agenti, lingua=ling, tr=TR.get(ling, TR['it']),
        cambio_ron=_cambio())


@ro_bp.route('/venditori/nuovo', methods=['POST'])
@login_required
def nuovo_venditore_ro():
    if not current_user.can_manage_venditori:
        return redirect(url_for('romania.dashboard'))
    from werkzeug.security import generate_password_hash
    email = request.form.get('email', '').strip()
    if not email or User.query.filter_by(email=email).first():
        flash('Email non valida o già registrata.', 'error')
        return redirect(url_for('romania.venditori'))
    u = User(
        nome    = request.form.get('nome', '').strip(),
        email   = email,
        role    = request.form.get('role', 'sales_ro'),
        market  = 'RO',
        lingua  = request.form.get('lingua', 'ro'),
        attivo  = True,
    )
    u.set_password(request.form.get('password', 'Romania2026!'))
    db.session.add(u)
    db.session.commit()
    flash(f'Agente {u.nome} creato.', 'success')
    return redirect(url_for('romania.venditori'))


@ro_bp.route('/venditori/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_venditore_ro(id):
    if not current_user.can_manage_venditori:
        return jsonify({'error': 'Accesso negato'}), 403
    u = User.query.get_or_404(id)
    u.attivo = not u.attivo
    db.session.commit()
    return jsonify({'attivo': u.attivo, 'nome': u.nome})


@ro_bp.route('/venditori/<int:id>/elimina', methods=['POST'])
@login_required
def elimina_venditore_ro(id):
    if not current_user.is_owner:
        return jsonify({'error': 'Solo il proprietario può eliminare agenti'}), 403
    u = User.query.get_or_404(id)
    if u.is_owner:
        return jsonify({'error': 'Non puoi eliminare il proprietario'}), 403
    db.session.delete(u)
    db.session.commit()
    flash(f'Agente eliminato.', 'success')
    return redirect(url_for('romania.venditori'))

