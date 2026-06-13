"""
routes/romania.py — BIOLavaTU LaundryPro
Blueprint per il mercato Romania.
Struttura separata dall'Italia ma usa gli stessi motori di calcolo.
Lingua: IT + RO (doppia)
Valuta: RON + EUR con cambio automatico
"""
import os, json
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

ro_bp = Blueprint('romania', __name__, url_prefix='/ro')


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
