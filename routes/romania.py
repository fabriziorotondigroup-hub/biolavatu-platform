"""
routes/romania.py — BIOLavaTU LaundryPro
Blueprint per il mercato Romania.
Struttura separata dall'Italia ma usa gli stessi motori di calcolo.
Lingua: IT + RO (doppia)
Valuta: RON + EUR con cambio automatico
"""
import os, json, math
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from app import db
from models.pratica import Pratica
from models.cliente import Cliente
from models.settings import Settings
from services.ins_romania import (
    get_demographic_data_ro, get_market_assessment_ro,
    converti_ron_eur, converti_eur_ron,
    TARIFFE_DEFAULT_RO, EUR_RON_RATE, OCC_BASE_RO, get_f_citta_ro
)
from services.i18n import t, get_all
from services.domanda import calcola_stima_clienti
from services.analisi_competitiva import (
    calcola_score_ponderato, calcola_capacita_concorrenza, analizza_punti_deboli
)

ro_bp = Blueprint('romania', __name__, url_prefix='/ro')


# ── Helper copiati da geo.py (isolato) ──────────────────────────────────────

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

@geo_bp.route('/api/geocode')
@login_required



def _check_ro_access():
    """Verifica che l'utente abbia accesso al mercato Romania."""
    if current_user.role in ('owner', 'admin'):
        return True
    if getattr(current_user, 'market', 'IT') == 'RO':
        return True
    return False


def _get_lingua():
    """Lingua corrente dalla sessione o dal profilo utente."""
    return session.get('lingua', getattr(current_user, 'lingua', 'it'))


def _cambio_ron_live():
    """Ottieni cambio EUR/RON live (con fallback al valore fisso)."""
    try:
        import urllib.request
        url = "https://api.frankfurter.app/latest?from=EUR&to=RON"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'BIOLavaTU/1.0')
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
            return float(data['rates']['RON'])
    except Exception:
        return EUR_RON_RATE  # fallback


# ── DASHBOARD ROMANIA ────────────────────────────────────────────────────────

@ro_bp.route('/')
@login_required
def dashboard():
    if not _check_ro_access():
        return redirect(url_for('dashboard.index'))

    lingua = _get_lingua()
    pratiche = Pratica.query.filter_by(market='RO').order_by(
        Pratica.created.desc()).limit(20).all()

    cambio = _cambio_ron_live()
    return render_template('romania/dashboard.html',
        pratiche=pratiche,
        lingua=lingua,
        tr=get_all(lingua),
        cambio_ron=cambio,
        market='RO',
    )


# ── NUOVO PREVENTIVO ROMANIA ─────────────────────────────────────────────────

@ro_bp.route('/preventivo/nuovo')
@login_required
def nuovo_preventivo():
    if not _check_ro_access():
        return redirect(url_for('dashboard.index'))

    lingua   = _get_lingua()
    cambio   = _cambio_ron_live()
    settings = Settings.query.first()

    return render_template('romania/preventivo_ro.html',
        pratica=None,
        lingua=lingua,
        tr=get_all(lingua),
        cambio_ron=cambio,
        tariffe=TARIFFE_DEFAULT_RO,
        market='RO',
        settings=settings,
    )


@ro_bp.route('/preventivo/<int:id>')
@login_required
def modifica_preventivo(id):
    if not _check_ro_access():
        return redirect(url_for('dashboard.index'))

    p        = Pratica.query.get_or_404(id)
    lingua   = _get_lingua()
    cambio   = _cambio_ron_live()
    settings = Settings.query.first()

    return render_template('romania/preventivo_ro.html',
        pratica=p,
        lingua=lingua,
        tr=get_all(lingua),
        cambio_ron=cambio,
        tariffe=TARIFFE_DEFAULT_RO,
        market='RO',
        settings=settings,
    )


# ── API CAMBIO LIVE ───────────────────────────────────────────────────────────

@ro_bp.route('/api/cambio')
@login_required
def get_cambio():
    cambio = _cambio_ron_live()
    return jsonify({
        'eur_ron':    cambio,
        'ron_eur':    round(1 / cambio, 6),
        'fonte':      'frankfurter.app (BCE)',
        'fallback':   cambio == EUR_RON_RATE,
    })


# ── API DATI DEMOGRAFICI JUDET ────────────────────────────────────────────────

@ro_bp.route('/api/demografici')
@login_required
def demografici_judet():
    judet = request.args.get('judet', '')
    oras  = request.args.get('oras', '')
    data  = get_demographic_data_ro(judet, oras)
    assessment = get_market_assessment_ro(
        data['reddito_medio'], data['densita'])
    return jsonify({**data, **assessment})


# ── API CALCOLO BUSINESS PLAN ROMANIA ────────────────────────────────────────

@ro_bp.route('/api/calcola-bp-ro', methods=['POST'])
@login_required
def calcola_bp_ro():
    data = request.json or {}
    cambio = _cambio_ron_live()

    # Macchine
    n_std = int(data.get('n_std', 0))
    n_med = int(data.get('n_med', 0))
    n_grd = int(data.get('n_grd', 0))
    n_asc = int(data.get('n_asc', 0))

    # Tariffe in RON
    t_std = float(data.get('t_std') or TARIFFE_DEFAULT_RO['lavaggio_std_ron'])
    t_med = float(data.get('t_med') or TARIFFE_DEFAULT_RO['lavaggio_med_ron'])
    t_grd = float(data.get('t_grd') or TARIFFE_DEFAULT_RO['lavaggio_grd_ron'])
    t_asc = float(data.get('t_asc') or TARIFFE_DEFAULT_RO['asciugatura_ron'])

    # Concorrenza
    c500 = int(data.get('concorrenti_500m', 0))
    c1k  = int(data.get('concorrenti_1km',  0))

    # Occupazione base Romania (più conservativa dell'Italia)
    if   c500 >= 5: occ_base = 0.08
    elif c500 == 4: occ_base = 0.20
    elif c500 == 3: occ_base = 0.28
    elif c500 == 2: occ_base = 0.35
    elif c500 == 1: occ_base = 0.42
    elif c1k  >= 4: occ_base = 0.48
    elif c1k  >= 2: occ_base = 0.52
    elif c1k  == 1: occ_base = 0.55
    else:            occ_base = 0.45

    # Correzioni zona
    den   = float(data.get('densita', 500))
    rec   = float(data.get('recensioni_zona', 0))
    red   = float(data.get('reddito_medio', 30000))  # RON
    gdo   = int(data.get('gdo_500m', 0))
    mult  = float(data.get('mult_attractor', 1.0))
    pop_c = float(data.get('pop_comune', 0))

    corr = 0.0
    if   den > 3000: corr += 0.04
    elif den > 1500: corr += 0.02
    elif den < 200:  corr -= 0.08

    if   rec > 80000:  corr += 0.04
    elif rec > 30000:  corr += 0.02
    elif rec < 5000:   corr -= 0.06

    if gdo >= 2: corr += 0.02
    elif gdo == 1: corr += 0.01

    # Romania: penalizza meno per alto reddito (mercato emergente)
    if   red > 60000: corr -= 0.04
    elif red < 18000: corr -= 0.05

    corr += min((mult - 1.0) * 0.10, 0.08)

    # Fattore città Romania
    f_citta = get_f_citta_ro(int(pop_c))

    # Scenario
    mult_sc = {'pessimistico': 0.70, 'realistico': 1.00, 'ottimistico': 1.30}.get(
        data.get('scenario', 'realistico'), 1.0)

    corr = max(-0.20, min(0.20, corr))
    occ  = min(0.75, occ_base * (1.0 + corr) * f_citta * mult_sc)

    # Incasso in RON
    CICLI_LAV = 18
    CICLI_ASC = 52
    giorni = 30

    incasso_lav_ron = (
        n_std * CICLI_LAV * t_std +
        n_med * CICLI_LAV * t_med +
        n_grd * CICLI_LAV * t_grd
    ) * occ * giorni
    incasso_asc_ron = n_asc * CICLI_ASC * t_asc * occ * giorni
    incasso_ron     = incasso_lav_ron + incasso_asc_ron
    incasso_eur     = converti_ron_eur(incasso_ron)

    # TVA Romania 19% (non 22% Italia)
    capex_ron = float(data.get('capex_ron', 0))
    capex_eur = converti_ron_eur(capex_ron)
    tva       = capex_ron * 0.19

    # Costi fissi stimati in RON
    affitto_ron    = float(data.get('affitto_ron', 3000))
    costi_fisi_ron = (
        affitto_ron +
        incasso_ron * 0.18 +   # energia ~18%
        incasso_ron * 0.06 +   # acqua ~6%
        incasso_ron * 0.04 +   # detergenti ~4%
        800 +                   # assicurazione RON/mese
        500                     # manutenzione RON/mese
    )
    utile_ron = incasso_ron - costi_fisi_ron
    utile_eur = converti_ron_eur(utile_ron)

    payback = (capex_ron * 1.19 / utile_ron / 12) if utile_ron > 0 else 999

    return jsonify({
        # RON
        'incasso_ron':      round(incasso_ron),
        'costi_ron':        round(costi_fisi_ron),
        'utile_ron':        round(utile_ron),
        'capex_ron':        round(capex_ron),
        'tva_ron':          round(tva),
        # EUR
        'incasso_eur':      round(incasso_eur),
        'utile_eur':        round(utile_eur),
        'capex_eur':        round(capex_eur),
        # Comune
        'occupazione_pct':  round(occ * 100, 1),
        'occ_base_pct':     round(occ_base * 100, 1),
        'f_citta':          round(f_citta, 2),
        'cambio_ron':       cambio,
        'payback_anni':     round(payback, 1) if payback < 999 else None,
        'scenario':         data.get('scenario', 'realistico'),
        'market':           'RO',
        'valuta':           'RON',
        'iva_pct':          19,
    })


# ── SWITCH LINGUA ─────────────────────────────────────────────────────────────

@ro_bp.route('/lingua/<lang>')
@login_required
def set_lingua(lang):
    if lang in ('it', 'ro'):
        session['lingua'] = lang
        if hasattr(current_user, 'lingua'):
            current_user.lingua = lang
            db.session.commit()
    return redirect(request.referrer or url_for('romania.dashboard'))


# ── LISTA PRATICHE ROMANIA ────────────────────────────────────────────────────

@ro_bp.route('/pratiche')
@login_required
def pratiche():
    if not _check_ro_access():
        return redirect(url_for('dashboard.index'))

    lingua   = _get_lingua()
    pratiche = Pratica.query.filter_by(market='RO').order_by(
        Pratica.created.desc()).all()
    cambio   = _cambio_ron_live()

    return render_template('romania/pratiche_ro.html',
        pratiche=pratiche,
        lingua=lingua,
        tr=get_all(lingua),
        cambio_ron=cambio,
        market='RO',
    )

# ── SALVA PREVENTIVO ROMANIA ─────────────────────────────────────────────────

@ro_bp.route('/preventivo/nuovo', methods=['POST'])
@login_required
def salva_nuovo():
    if not _check_ro_access():
        return redirect(url_for('dashboard.index'))

    from models.cliente import Cliente
    import datetime

    data = request.form
    cambio = float(data.get('cambio_ron') or _cambio_ron_live())

    # Cliente
    cliente = Cliente(
        nome      = data.get('cliente_nome','').strip(),
        azienda   = data.get('cliente_azienda',''),
        email     = data.get('cliente_email',''),
        telefono  = data.get('cliente_tel',''),
        piva      = data.get('cliente_piva',''),
    )
    db.session.add(cliente)
    db.session.flush()

    # Numero pratica Romania
    count = Pratica.query.filter_by(market='RO').count() + 1
    numero = f"RO-{datetime.date.today().year}-{count:04d}"

    p = Pratica(
        numero           = numero,
        cliente_id       = cliente.id,
        agente_id        = current_user.id,
        market           = 'RO',
        valuta           = 'RON',
        cambio_ron       = cambio,
        judet_cod        = data.get('judet_cod',''),
        indirizzo        = data.get('indirizzo',''),
        citta            = data.get('citta',''),
        cap              = data.get('cap',''),
        provincia        = data.get('provincia',''),
        mq               = int(data.get('mq') or 60),
        affitto_mese     = float(data.get('affitto_ron') or 0),
        tipo_zona        = data.get('tipo_zona','residenziale'),
        lat              = float(data.get('lat') or 0) or None,
        lng              = float(data.get('lng') or 0) or None,
        pop_3min         = int(data.get('pop_3min') or 0),
        pop_5min         = int(data.get('pop_5min') or 0),
        pop_10min        = int(data.get('pop_10min') or 0),
        score_zona       = float(data.get('score_zona') or 0),
        concorrenti_500m = int(data.get('concorrenti_500m') or 0),
        concorrenti_1km  = int(data.get('concorrenti_1km') or 0),

        tariffa_lavaggio_std = float(data.get('tariffa_lavaggio_std') or 20),
        tariffa_lavaggio_med = float(data.get('tariffa_lavaggio_med') or 25),
        tariffa_lavaggio_grd = float(data.get('tariffa_lavaggio_grd') or 35),
        tariffa_asciugatura  = float(data.get('tariffa_asciugatura') or 5),
        capex            = float(data.get('capex') or 0),
        incasso_mese     = float(data.get('incasso_mese') or 0),
        costi_mese       = float(data.get('costi_mese') or 0),
        utile_mese       = float(data.get('utile_mese') or 0),
    )
    db.session.add(p)
    db.session.commit()

    return redirect(url_for('romania.modifica_preventivo', id=p.id))

# ── ANALISI AI ZONA ROMANIA ───────────────────────────────────────────────────

@ro_bp.route('/api/analisi-ai-ro', methods=['POST'])
@login_required
def analisi_ai_ro():
    """Genera analisi AI della zona per il mercato Romania.
    Prompt bilingue IT/RO, valori in RON, calibrato per mercato rumeno.
    """
    import anthropic as _anth
    import os as _os

    data    = request.json or {}
    api_key = _os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'errore': 'ANTHROPIC_API_KEY non configurata'}), 500

    try:
        client = _anth.Anthropic(api_key=api_key)
    except Exception as e:
        return jsonify({'errore': f'Errore init client: {str(e)}'}), 500

    lingua = data.get('lingua', 'it')
    cambio = float(data.get('cambio_ron', 4.97) or 4.97)

    # Dati finanziari in RON
    inc_ron = float(data.get('incasso_mese_ron', 0) or 0)
    inc_eur = round(inc_ron / cambio)
    cos_ron = float(data.get('costi_mese_ron', 0) or 0)
    uti_ron = round(inc_ron - cos_ron)
    cap_ron = float(data.get('capex_ron', 0) or 0)
    cap_eur = round(cap_ron / cambio)

    attractor_txt = ''
    for ap in data.get('attractor_points', []):
        nome = ap.get('nome', '')
        tipo = ap.get('tipo', '').replace('_', ' ')
        dist = ap.get('distanza_m', 0)
        if nome:
            attractor_txt += f'  • {nome} ({tipo}, {dist}m)\n'
    if not attractor_txt:
        attractor_txt = '  Niciun generator de cerere structural detectat / Nessun generatore rilevato'

    conc_txt = ''
    for c in data.get('competitors_detail', [])[:8]:
        conc_txt += f"  • {c.get('nome','')} — {c.get('distanza_m',0)}m — Rating: {c.get('rating','N/D')}\n"
    if not conc_txt:
        conc_txt = '  Niciun concurent detectat / Nessun concorrente rilevato'

    prompt = f"""Esti un analist de piata specializat in sectorul spalatoriilor self-service din Romania.
Produceti o ANALIZA OBIECTIVA a zonei - doar date, fapte, masuratori.
NU dati recomandari, NU spuneti daca sa deschideti sau nu, NU exprimati judecati de valoare.
Scrieti in {"ROMANA si ITALIANA" if lingua == 'ro' else "ITALIANA e RUMENO"} - intai romana, apoi italiana.

=== DATE LOCATIE ===
Adresa: {data.get('indirizzo','N/D')}, {data.get('citta','N/D')}, Romania
Suprafata local: {data.get('mq',60)} mp

=== BAZIN DEMOGRAFIC ===
Populatie accesibila:
  - 3 minute pe jos (~240m): {int(data.get('pop_3min',0) or 0):,} locuitori
  - 5 minute pe jos (~400m): {int(data.get('pop_5min',0) or 0):,} locuitori
  - 10 minute pe jos (~800m): {int(data.get('pop_10min',0) or 0):,} locuitori
Densitate: {int(data.get('densita',0) or 0):,} loc/km2
Salariu mediu net judet: {int(data.get('reddito_medio',0) or 0):,} RON/an (sursa: INS Romania 2021)
Echivalent EUR: circa EUR{int((data.get('reddito_medio',0) or 0)/cambio):,}/an (curs {cambio:.2f} RON/EUR)

=== TRAFIC SI VIZIBILITATE ===
Indicator trafic real (recenzii Google in 400m): {int(data.get('recensioni_zona',0) or 0):,}
Magazine alimentare (GDO) in 500m: {data.get('gdo_500m',0)}
Scor zona: {data.get('score_zona',0)}/100

=== CONCURENTA ===
Spalatorii self-service in 500m: {data.get('concorrenti_500m',0)}
Total spalatorii in 1km: {data.get('concorrenti_1km',0)}
Detaliu operatori detectati:
{conc_txt}

=== GENERATORI DE CERERE (Attractor Points) ===
{attractor_txt}

=== STRUCTURA ECONOMICA ===
Investitie estimata: {int(cap_ron):,} RON + TVA 19% = {int(cap_ron*1.19):,} RON (~ EUR{cap_eur:,})
Incasari lunare estimate: {int(inc_ron):,} RON (~ EUR{inc_eur:,}/luna)
Costuri lunare: {int(cos_ron):,} RON
Profit net estimat: {int(uti_ron):,} RON/luna

=== STRUCTURA ANALIZEI (obligatorie) ===

## 1. BAZIN DEMOGRAFIC / BACINO DEMOGRAFICO
Descrie numeric bazinul. Compara cu media nationala romana.

## 2. TRAFIC SI ZONA / TRAFFICO E ZONA
Interpreteaza indicatorul de trafic. Descrie tipul de zona.

## 3. CONCURENTA / CONCORRENZA
Analizeaza operatorii detectati. Calculeaza densitatea (operatori/1000 loc).

## 4. GENERATORI DE CERERE / GENERATORI DI DOMANDA
Descrie factorii structurali care genereaza cerere constanta.

## 5. PROIECTIE ECONOMICA / PROIEZIONE ECONOMICA
Comenteaza cifrele financiare in context romanesc.
Compara cu piata italiana (Italia: EUR8.000-18.000/luna; Romania: estimat proportional cu salariile).

Fii concis si precis. Max 600 cuvinte total.
"""

    try:
        msg = client.messages.create(
            model='claude-sonnet-4-5',
            max_tokens=1200,
            messages=[{'role': 'user', 'content': prompt}]
        )
        testo = msg.content[0].text.strip()
        return jsonify({'analisi': testo, 'lingua': lingua, 'mercato': 'RO'})
    except Exception as e:
        import traceback
        err_detail = traceback.format_exc()
        print(f"[analisi_ai_ro] ERRORE: {err_detail}")
        return jsonify({'errore': str(e), 'detail': err_detail[:500]}), 500


# ── ZONA ANALISI ROMANIA (copia isolata da geo.py) ──────────────────────────
@ro_bp.route('/api/zona-analisi-ro')
@login_required
def zona_analisi_ro():
    try:
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

        # ── DATI DEMOGRAFICI ──────────────────────────────────────────────────────
        demo          = get_demographic_data_ro(provincia, citta)
        eta_media     = demo.get('eta_media', 42.0)
        reddito_medio = demo.get('reddito_medio', 30000)  # RON
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

        assessment = get_market_assessment_ro(reddito_medio, densita_istat)
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
        'zona_turistica':     n_affitti >= 5,  # 5+ strutture = zona ad alta densità turistica
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
