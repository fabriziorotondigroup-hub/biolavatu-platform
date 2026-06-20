from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.pratica import Pratica
from models.cliente import Cliente
from models.macchina import Macchina
from models.settings import Settings
from models.user import User
from app import db
import json
import os
import datetime
from werkzeug.utils import secure_filename

preventivo_bp = Blueprint('preventivo', __name__)

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def genera_numero():
    """Genera numero progressivo univoco per anno — immune a eliminazioni."""
    anno = datetime.datetime.now().year
    prefisso = f'BIO-{anno}-'
    ultima = (db.session.query(Pratica.numero)
              .filter(Pratica.numero.like(f'{prefisso}%'))
              .order_by(Pratica.numero.desc()).first())
    n = 1
    if ultima:
        try:
            n = int(ultima[0].replace(prefisso, '')) + 1
        except Exception:
            n = 1
    candidato = f'{prefisso}{n:04d}'
    while db.session.query(Pratica.id).filter_by(numero=candidato).first():
        n += 1
        candidato = f'{prefisso}{n:04d}'
    return candidato


def _build_bp_avanzato_json(data):
    """Raccoglie tutti i campi del BP avanzato dal form e li serializza in JSON."""
    import json as _json
    fields = [
        # Piano Investimenti
        'inv_formazione','inv_fattibilita','inv_commercialista','inv_notaio',
        'inv_burocratico','inv_allacciamento','inv_marchio','inv_promozione_av',
        'inv_inaugurazione','inv_franchising','inv_murarie','inv_insegne',
        'inv_impianti_idr','inv_illuminazione','inv_climatiz','inv_stereo',
        'inv_antifurto','inv_arredo','inv_vetrofanie','inv_gettoniere',
        'inv_scaldacqua','inv_dispenser_det','inv_cambia_monete','inv_telefono',
        'inv_computer','inv_software','inv_stampante','inv_altre_attr','inv_altri',
        'inv_anni_mac','inv_perc_fin','inv_tasso','inv_anni_fin','pc_cauzione',
        # Conto Economico — Ricavi
        'ce_cic_lav_p','ce_tar_lav_p','ce_cic_lav_m','ce_tar_lav_m',
        'ce_cic_lav_g','ce_tar_lav_g','ce_cic_asc_p','ce_tar_asc_p',
        'ce_cic_asc_g','ce_tar_asc_g','ce_cic_det','ce_tar_det',
        'ce_cic_caffe','ce_tar_caffe',
        # Costi Variabili
        'ce_perc_energia','ce_perc_det_cv',
        # Costi Fissi mensili
        'ce_cf_affitto_m','ce_cf_riscald','ce_cf_dipendenti','ce_cf_comm',
        'ce_cf_promo','ce_cf_manut','ce_cf_energia_el_m','ce_cf_telefono_m',
        'ce_cf_postali','ce_cf_assic','ce_cf_pulizia_m','ce_cf_guardia',
        'ce_cf_tari','ce_cf_cciaa','ce_cf_associaz','ce_cf_altri_amm',
        'ce_cf_leasing','ce_cf_interessi','ce_cf_cancel','ce_cf_altro',
        # Modalità
        'bp_mode',
    ]
    result = {}
    for f in fields:
        val = data.get(f)
        if val is not None and val != '':
            try: result[f] = float(val)
            except (ValueError, TypeError): result[f] = val
    return _json.dumps(result) if result else None


@preventivo_bp.route('/preventivo/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo():
    # Agenti di mercati esteri non accedono al wizard IT
    # Owner, admin e segreteria passano SEMPRE senza controllo market
    _ruoli_liberi = ('owner', 'admin', 'segreteria')
    _market_utente = getattr(current_user, 'market', 'IT') or 'IT'
    if current_user.role not in _ruoli_liberi and _market_utente != 'IT':
        return redirect(url_for('dashboard.index'))
    macchine = Macchina.query.filter_by(attiva=True).order_by(Macchina.categoria, Macchina.nome).all()
    clienti = Cliente.query.order_by(Cliente.nome).all()
    settings = Settings.query.first()
    return render_template('preventivo.html',
        macchine=macchine,
        clienti=clienti,
        settings=settings,
        pratica=None,
    )


@preventivo_bp.route('/preventivo/salva', methods=['POST'])
@login_required
def salva():
    data = request.form
    settings = Settings.query.first()

    # Cliente
    cliente_id = data.get('cliente_id')
    if not cliente_id:
        # Crea nuovo cliente al volo
        c = Cliente(
            nome=data.get('cliente_nome', 'Cliente'),
            email=data.get('cliente_email', ''),
            telefono=data.get('cliente_tel', ''),
            azienda=data.get('cliente_azienda', ''),
        )
        db.session.add(c)
        db.session.flush()
        cliente_id = c.id

    # Macchine selezionate
    macchine_raw = data.get('macchine_json', '[]')
    try:
        macchine_sel = json.loads(macchine_raw)
    except Exception:
        macchine_sel = []

    # Calcola capex
    capex = sum(float(m.get('prezzo_effettivo') or m.get('prezzo',0)) * int(m.get('qty',1)) for m in macchine_sel)

    # Business plan
    incasso = float(data.get('incasso_mese', 0) or 0)
    costi = float(data.get('costi_mese', 0) or 0)
    utile = incasso - costi
    payback = (capex * 1.22 / utile / 12) if utile > 0 else 0

    # Geocoding server-side se lat/lng mancanti dal frontend
    _save_lat = float(data.get('lat', 0) or 0)
    _save_lng = float(data.get('lng', 0) or 0)
    if (not _save_lat or not _save_lng):
        _gmaps_key = os.environ.get('GMAPS_KEY', '')
        _citta = data.get('citta', '')
        _indirizzo = data.get('indirizzo', '')
        if _gmaps_key and (_citta or _indirizzo):
            import urllib.parse as _upl, urllib.request as _ugr
            for _ga in [
                f"{_indirizzo}, {_citta}, Italia" if _indirizzo and _citta else None,
                f"{_citta}, Italia" if _citta else None,
            ]:
                if not _ga: continue
                try:
                    _gurl = ("https://maps.googleapis.com/maps/api/geocode/json?address="
                             + _upl.quote_plus(_ga) + "&key=" + _gmaps_key)
                    _greq = _ugr.Request(_gurl, headers={"User-Agent": "BIOLavaTU"})
                    with _ugr.urlopen(_greq, timeout=6) as _gr:
                        _gd = __import__('json').loads(_gr.read())
                    if _gd.get('results'):
                        _loc = _gd['results'][0]['geometry']['location']
                        _save_lat = float(_loc['lat'])
                        _save_lng = float(_loc['lng'])
                        break
                except Exception:
                    continue

    p = Pratica(
        numero=genera_numero(),
        stato='bozza',
        fattibilita=int(data.get('fattibilita', 50)),
        cliente_id=int(cliente_id),
        agente_id=current_user.id,
        # Sede
        indirizzo=data.get('indirizzo', ''),
        citta=data.get('citta', ''),
        cap=data.get('cap', ''),
        provincia=data.get('provincia', ''),
        lat=_save_lat,
        lng=_save_lng,
        mq=int(data.get('mq', 60) or 60),
        # Zona
        pop_3min=int(data.get('pop_3min', 0) or 0),
        pop_5min=int(data.get('pop_5min', 0) or 0),
        pop_10min=int(data.get('pop_10min', 0) or 0),
        concorrenti_500m=int(data.get('concorrenti_500m', 0) or 0),
        concorrenti_1km=int(data.get('concorrenti_1km', 0) or 0),
        servizi_400m=int(data.get('servizi_400m', 0) or 0),
        score_zona=float(data.get('score_zona', 0) or 0),
        score_label=data.get('score_label', ''),
        traffico_pedonale=data.get('traffico_pedonale', 'medio'),
        pois_raw=data.get('pois_raw', ''),
        # Macchine
        macchine_json=macchine_raw,
        capex=capex,
        # Business plan
        tariffa_lavaggio_std=float(data.get('tariffa_lavaggio_std', 6) or 6),
        tariffa_lavaggio_med=float(data.get('tariffa_lavaggio_med', 8) or 8),
        tariffa_lavaggio_grd=float(data.get('tariffa_lavaggio_grd', 10) or 10),
        tariffa_asciugatura=float(data.get('tariffa_asciugatura', 3.5) or 3.5),
        affitto_mese=float(data.get('affitto_mese', 0) or 0),
        incasso_mese=incasso,
        costi_mese=costi,
        utile_mese=utile,
        payback_mesi=round(payback, 1),
        scenario=data.get('scenario', 'realistico'),
        # AI
        ai_zona=data.get('ai_zona', ''),
        ai_bp=data.get('ai_bp', ''),
        note_interne=data.get('note_interne', ''),
        # Business Plan Avanzato — tutti i campi salvati come JSON
        bp_avanzato_json=_build_bp_avanzato_json(data),
    )

    db.session.add(p)
    db.session.commit()

    # Upload foto sede
    if 'foto_sede' in request.files:
        f = request.files['foto_sede']
        if f and f.filename and allowed_file(f.filename):
            from flask import current_app
            fn = secure_filename(f'sede_{p.id}_{f.filename}')
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fn))
            p.foto_sede = fn
            db.session.commit()

    # [ADD-ON COMMERCIALE] Salva Risk Score Investimento (se calcolato dal frontend)
    try:
        _risk_score_in = data.get('risk_score', '')
        if _risk_score_in:
            p.risk_score = int(float(_risk_score_in))
            p.risk_label = data.get('risk_label', '')
            p.risk_assessment_json = data.get('risk_assessment_json', '')
            db.session.commit()
    except Exception:
        pass

    # [ADD-ON COMMERCIALE] Scarica e salva mappa statica con concorrenti per il PDF
    try:
        if p.lat and p.lng:
            _gmaps_key2 = os.environ.get('GMAPS_KEY', '')
            if _gmaps_key2:
                import urllib.parse as _upl2, urllib.request as _ugr2
                _markers = f"color:0x1B4F72|label:S|{p.lat},{p.lng}"
                try:
                    _pois_list = json.loads(p.pois_raw) if p.pois_raw else []
                except Exception:
                    _pois_list = []
                _conc_markers = ''
                for _poi in _pois_list[:8]:
                    if _poi.get('categoria') == 'concorrente' and _poi.get('lat') and _poi.get('lng'):
                        _conc_markers += f"&markers=color:0xC0392B|{_poi['lat']},{_poi['lng']}"
                _static_url = (
                    "https://maps.googleapis.com/maps/api/staticmap?"
                    f"center={p.lat},{p.lng}&zoom=15&size=900x500&scale=2"
                    f"&markers={_upl2.quote(_markers)}"
                    f"{_conc_markers}"
                    f"&key={_gmaps_key2}"
                )
                from flask import current_app
                _map_fn  = secure_filename(f'mappa_{p.id}.png')
                _map_path = os.path.join(current_app.config['UPLOAD_FOLDER'], _map_fn)
                _mreq = _ugr2.Request(_static_url, headers={"User-Agent": "BIOLavaTU"})
                with _ugr2.urlopen(_mreq, timeout=10) as _mresp:
                    with open(_map_path, 'wb') as _mf:
                        _mf.write(_mresp.read())
                p.foto_mappa = _map_path
                db.session.commit()
    except Exception:
        pass

    flash(f'Preventivo {p.numero} creato con successo!', 'success')
    return redirect(url_for('pratiche.dettaglio', id=p.id))


@preventivo_bp.route('/preventivo/<int:id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica(id):
    p = Pratica.query.get_or_404(id)
    macchine = Macchina.query.filter_by(attiva=True).order_by(Macchina.categoria, Macchina.nome).all()
    clienti = Cliente.query.order_by(Cliente.nome).all()
    settings = Settings.query.first()
    return render_template('preventivo.html',
        macchine=macchine,
        clienti=clienti,
        settings=settings,
        pratica=p,
    )


@preventivo_bp.route('/api/calcola-bp', methods=['POST'])
@login_required
def calcola_bp():
    """
    Business Plan — modello domanda reale × tariffe utente.
    INCASSO = clienti/giorno (zona) × spesa/visita (tariffe) × 26
    COSTI = variabili (cicli reali) + fissi + capitale
    """
    data     = request.json
    s        = Settings.query.first()
    macchine = data.get('macchine', [])
    scenario = data.get('scenario', 'realistico')
    mult        = {'pessimistico': 0.60, 'realistico': 1.00, 'ottimistico': 1.25}.get(scenario, 1.0)
    # 365 giorni/anno ÷ 12 = 30.4 → arrotondato 30 (conservativo)
    giorni_mese = float(data.get('giorni_mese', 30) or 30)
    ore_apertura= float(data.get('ore_apertura', 13) or 13)  # 12-14h/giorno

    # ── TARIFFE DALL'UTENTE ──────────────────────────────────────────────────
    t_std  = float(data.get('tariffa_lavaggio_std', 6.0) or 6.0)
    t_med  = float(data.get('tariffa_lavaggio_med', 8.0) or 8.0)
    t_grd  = float(data.get('tariffa_lavaggio_grd', 10.0) or 10.0)
    t_asc  = float(data.get('tariffa_asciugatura',  3.5) or 3.5)
    p_asc  = float(data.get('perc_asciugatura', 65) or 65) / 100.0

    # ── ANALISI MACCHINE ─────────────────────────────────────────────────────
    capex = kw_tot = 0.0
    n_std = n_med = n_grd = n_asc = 0
    gas_mc = 0.0; has_gas = False

    for m in macchine:
        qty = int(m.get('qty', 1))
        pr  = float(m.get('prezzo_effettivo') or m.get('prezzo', 0))
        kw  = float(m.get('kw', 0))
        kg  = float(m.get('capacita_kg', 0))
        nom = m.get('nome', '').lower()
        cat = m.get('categoria', '').lower()
        cb  = m.get('combustibile', 'elettrico')
        mc  = float(m.get('mc_ciclo', 0))
        capex  += pr * qty
        kw_tot += kw * qty
        asc = 'asciug' in nom or 'asciug' in cat
        if asc:
            n_asc += qty
            if cb == 'gas': has_gas = True; gas_mc = mc
        else:
            if kg <= 9:    n_std += qty
            elif kg <= 13: n_med += qty
            else:          n_grd += qty

    n_lav = max(1, n_std + n_med + n_grd)
    t_avg_lav  = (n_std*t_std + n_med*t_med + n_grd*t_grd) / n_lav
    spesa_cli  = t_avg_lav + (p_asc * t_asc)

    # ══════════════════════════════════════════════════════════════════════════
    # INCASSO — metodo capacità macchine × occupazione zona (benchmark reali)
    # ══════════════════════════════════════════════════════════════════════════
    # Benchmark calibrati su dati reali BIOLavaTU:
    #   Via della Giuliana Roma  → monopolio   → €18.000/mese → occ 65%
    #   Via Candia Roma          → 4 conc 500m → €8.000/mese  → occ 25%
    #
    # Formula: incasso = Σ(macchine × cicli_max × occ% × tariffa) × 30
    # L'occupazione% dipende dallo score zona (concorrenza + densità + traffico)
    # ══════════════════════════════════════════════════════════════════════════

    c500  = int(data.get('concorrenti_500m', 0) or 0)
    c1k   = int(data.get('concorrenti_1km', 0) or 0)
    den   = float(data.get('densita', 2000) or 2000)
    rec   = float(data.get('recensioni_zona', 0) or 0)
    gdo   = int(data.get('gdo_500m', 0) or 0)
    red   = float(data.get('reddito_medio', 21000) or 21000)
    pop5  = float(data.get('pop_5min', 0) or 0)
    pop10 = float(data.get('pop_10min', 0) or 0)
    mult_attr = float(data.get('mult_attractor', 1.0) or 1.0)

    # ── 1. OCCUPAZIONE BASE da concorrenza ────────────────────────────────────
    # CALIBRAZIONE AGGIORNATA:
    #   Via Candia Roma:    4 conc 500m → 25% → €8.000/mese  ✅ benchmark reale
    #   Via Giuliana Roma:  monopolio   → 57.9% → €18.000/mese ✅ top performer Roma
    #   Media italiana monopolio: 45% (più rappresentativa fuori Roma/Milano)
    #   57.9% usato solo come scenario ottimistico (x1.30 del realistico)
    if   c500 >= 5: occ_base = 0.10   # zona satura
    elif c500 == 4: occ_base = 0.25   # Via Candia → €8k ✅
    elif c500 == 3: occ_base = 0.32
    elif c500 == 2: occ_base = 0.42
    elif c500 == 1: occ_base = 0.52
    elif c1k  >= 4: occ_base = 0.55
    elif c1k  >= 2: occ_base = 0.58
    elif c1k  == 1: occ_base = 0.60
    else:           occ_base = 0.45   # monopolio → media italiana reale (non top performer)

    # ── 2. CORREZIONE ZONA (additiva, max ±20% sull'occupazione base) ─────────
    # I fattori zonali correggono l'occupazione base di piccole percentuali.
    # Calibrati su 2 benchmark reali:
    #   Via Candia:    4 conc 500m → occ_base 25.7% → incasso €8.000 ✅
    #   Via Giuliana:  monopolio   → occ_base 57.9% → incasso €18.000 ✅

    corr = 0.0

    # Densità residenti
    if   den > 6000: corr += 0.04
    elif den > 4000: corr += 0.02
    elif den > 2000: corr += 0.00
    elif den > 800:  corr -= 0.04
    else:            corr -= 0.10

    # Traffico reale (recensioni Google zona)
    if   rec > 150000: corr += 0.04   # zona vivace come Via Candia
    elif rec > 80000:  corr += 0.02
    elif rec > 30000:  corr += 0.00
    elif rec > 8000:   corr -= 0.02
    elif rec > 2000:   corr -= 0.05
    else:              corr -= 0.10

    # GDO (sinergia percorso spesa)
    if gdo >= 2: corr += 0.02
    elif gdo == 1: corr += 0.01

    # Reddito (penalizza redditi molto alti: lavatrice di casa)
    if   red > 40000: corr -= 0.06
    elif red > 30000: corr -= 0.03
    elif red < 13000: corr -= 0.04

    # Attractor points (università, ospedali ecc.)
    corr += min((mult_attr - 1.0) * 0.10, 0.08)  # max +8%

    # ── FATTORE DIMENSIONE CITTÀ ──────────────────────────────────────────────
    # Le città grandi hanno cultura self-service più consolidata,
    # maggiore densità e più turismo rispetto alle città medie/piccole.
    # Moltiplicatore applicato DOPO le correzioni additive.
    pop_comune = float(data.get('pop_comune', 0) or 0)
    if   pop_comune >= 500000:  f_citta = 1.00   # Roma, Milano, Napoli, Torino
    elif pop_comune >= 200000:  f_citta = 0.88   # Bologna, Firenze, Palermo, Bari
    elif pop_comune >= 100000:  f_citta = 0.78   # Bergamo, Brescia, Padova, Taranto
    elif pop_comune >= 50000:   f_citta = 0.68   # città medie
    elif pop_comune >= 20000:   f_citta = 0.58   # comuni grandi
    else:                        f_citta = 0.50   # comuni piccoli / borghi

    # Se pop_comune non disponibile, stima dalla densità e pop_10min
    if pop_comune == 0:
        pop_est = float(data.get('pop_10min', 0) or 0) * 3.5  # stima grossolana
        if   pop_est >= 500000: f_citta = 1.00
        elif pop_est >= 200000: f_citta = 0.88
        elif pop_est >= 100000: f_citta = 0.78
        elif pop_est >= 50000:  f_citta = 0.68
        else:                    f_citta = 0.60  # default conservativo

    # Correzione totale clamped a [-20%, +20%]
    corr = max(-0.20, min(0.20, corr))

    # ── 3. STAGIONALITÀ PER TIPO DI ZONA ─────────────────────────────────────
    # Moltiplicatore mensile in base al tipo di zona e al mese corrente.
    # Fondamentale per valutare la tenuta finanziaria nei mesi morti.
    import datetime as _dt
    mese_corrente = _dt.date.today().month
    tipo_zona = (data.get('tipo_zona') or '').lower()

    # Profili stagionali per tipo di zona
    _stagionalita = {
        # Zona turistica estiva: picco luglio-agosto, crollo invernale
        'turistica': {1:0.45, 2:0.45, 3:0.65, 4:0.80, 5:0.90,
                      6:1.20, 7:1.80, 8:1.80, 9:1.10, 10:0.80, 11:0.55, 12:0.45},
        # Zona universitaria: picco ott-maggio, crollo estate
        'universitaria': {1:1.15, 2:1.20, 3:1.20, 4:1.15, 5:1.10,
                          6:0.70, 7:0.55, 8:0.50, 9:0.80, 10:1.15, 11:1.20, 12:1.00},
        # Zona residenziale pura: stabile tutto l'anno
        'residenziale': {1:0.95, 2:0.95, 3:1.00, 4:1.00, 5:1.05,
                         6:1.00, 7:0.90, 8:0.85, 9:1.00, 10:1.05, 11:1.05, 12:0.95},
        # Zona mista/commerciale: leggera variazione
        'mista': {1:0.95, 2:0.95, 3:1.00, 4:1.05, 5:1.05,
                  6:1.00, 7:0.90, 8:0.85, 9:1.00, 10:1.05, 11:1.05, 12:0.95},
    }
    # Default residenziale se non specificato
    _profilo = _stagionalita.get(tipo_zona, _stagionalita['residenziale'])
    f_stagionalita = _profilo.get(mese_corrente, 1.0)

    # ── 4. OCCUPAZIONE FINALE ─────────────────────────────────────────────────
    occ_finale = min(0.82, occ_base * (1.0 + corr) * f_citta * f_stagionalita * mult)
    # cap a 82%: picchi stagionali possono superare 80% in zone turistiche luglio-agosto

    # ── 4. INCASSO DA CAPACITÀ MACCHINE ───────────────────────────────────────
    # Cicli max/giorno: 14h operative
    CICLI_MAX_LAV = 18   # 14h ÷ 45min = 18.6 → 18
    CICLI_MAX_ASC = 52   # 14h ÷ 16min = 52.5 → 52

    incasso_lav = (
        n_std * CICLI_MAX_LAV * t_std +
        n_med * CICLI_MAX_LAV * t_med +
        n_grd * CICLI_MAX_LAV * t_grd
    ) * occ_finale * giorni_mese

    incasso_asc = n_asc * CICLI_MAX_ASC * t_asc * occ_finale * giorni_mese

    incasso = incasso_lav + incasso_asc

    # ── 5. CLIENTI/GIORNO (ricavati dall'incasso per reportistica) ───────────
    clienti = (incasso / giorni_mese / spesa_cli) if spesa_cli > 0 else 0

    # Salva dettaglio occupazione per il report
    _occ_detail = {
        'occ_base':        round(occ_base * 100, 1),
        'correzione_zona': round(corr * 100, 1),
        'f_citta':         round(f_citta, 2),
        'f_stagionalita':  round(f_stagionalita, 2),
        'tipo_zona':       tipo_zona or 'residenziale',
        'mese':            mese_corrente,
        'occ_finale':      round(occ_finale * 100, 1),
    }

    # ── COSTI VARIABILI (proporzionali ai cicli reali) ───────────────────────
    kwh_c  = float(data.get('kwh_cost')        or (s.kwh_cost      if s else 0.28))
    gas_c  = float(data.get('gas_mc_cost')     or (s.gas_mc_cost   if s else 1.20))
    acq_c  = float(data.get('acqua_mc_cost')   or (s.acqua_mc_cost if s else 2.50))
    sca_c  = float(data.get('scarico_mc_cost') or (s.scarico_mc_cost if s else 1.80))

    # Energia: kW × ore_uso_reale (non 8h fisse)
    # Ore uso = cicli × durata_ciclo (45 min lav, 40 min asc)
    c_lav = clienti        # cicli lavaggio/giorno (da domanda zona)
    c_asc = clienti * p_asc # cicli asciugatura/giorno
    kw_lav = kw_tot * (n_lav / max(1, n_lav + n_asc))
    kw_asc = kw_tot * (n_asc  / max(1, n_lav + n_asc))
    # Energia = uso macchine (cicli reali) + standby (ore apertura × consumi fissi)
    # Standby: solo illuminazione + sistemi controllo (NON le macchine in standby caldo)
    kw_standby_illum = 0.3  # illuminazione LED + sistema controllo pagamento
    cv_energia = (
        (kw_lav * c_lav * 0.75 + kw_asc * c_asc * 0.67)  # uso macchine proporzionale ai cicli
        + kw_standby_illum * ore_apertura                  # illuminazione fissa
    ) * giorni_mese * kwh_c

    # Gas asciugatura (solo se asciugatrici a gas)
    cv_gas  = gas_mc * c_asc * giorni_mese * gas_c if has_gas else 0.0

    # Acqua e scarico: ~55L per ciclo lavaggio
    mc_acq  = c_lav * 0.055 * giorni_mese
    cv_acq  = mc_acq * acq_c
    cv_sca  = mc_acq * sca_c

    # Detergenti: grammi/ciclo × costo/kg × cicli_mese
    cv_det  = 0.0
    if s and c_lav > 0:
        cm = c_lav * giorni_mese
        cv_det = (
            (s.det1_grammi_ciclo/1000)*s.det1_costo_kg*cm +
            (s.det2_grammi_ciclo/1000)*s.det2_costo_kg*cm +
            (s.det3_grammi_ciclo/1000)*s.det3_costo_kg*cm
        )

    tot_variabili = cv_energia + cv_gas + cv_acq + cv_sca + cv_det

    # ── COSTI FISSI ──────────────────────────────────────────────────────────
    affitto  = float(data.get('affitto_mese', 0) or 0)
    comm     = float(data.get('commercialista') or (s.commercialista if s else 150))
    cciaa    = float(data.get('cciaa')           or (s.cciaa          if s else 50))
    assic    = float(data.get('assicurazione')   or (s.assicurazione  if s else 100))
    manut    = float(data.get('manutenzione')    or (s.manutenzione   if s else 200))
    lavoro   = float(data.get('costo_lavoro', 0) or 0)

    tot_fissi = affitto + comm + cciaa + assic + manut + lavoro

    # ── COSTI CAPITALE ───────────────────────────────────────────────────────
    anni_amm = float(data.get('anni_ammortamento', 10) or 10)
    ammort   = capex / anni_amm / 12

    pf  = float(data.get('perc_finanziato', 0) or 0) / 100.0
    ti  = float(data.get('tasso_interesse', 6.0) or 6.0) / 100.0
    ap  = float(data.get('anni_prestito', 7) or 7)
    cf  = capex * 1.22 * pf
    if cf > 0 and ap > 0:
        r = ti/12; n = ap*12
        rata = cf * (r*(1+r)**n) / ((1+r)**n - 1)
    else:
        rata = 0.0

    tot_capitale = ammort + rata

    # ── RISULTATI ────────────────────────────────────────────────────────────
    tot_costi  = tot_variabili + tot_fissi + tot_capitale
    ebitda     = incasso - tot_variabili - tot_fissi
    utile      = incasso - tot_costi
    capex_iva  = round(capex * 1.22, 2)
    payback    = (capex_iva / utile / 12) if utile > 0 else 0
    be_clienti = round((tot_fissi + tot_capitale) / (spesa_cli * giorni_mese), 1) if spesa_cli > 0 else 0

    return jsonify({
        'capex':          round(capex, 2),
        'capex_iva':      capex_iva,
        'occupazione_pct': _occ_detail['occ_finale'],
        'occ_detail':      _occ_detail,
        'incasso_mese':   round(incasso, 2),
        'costi_mese':     round(tot_costi, 2),
        'ebitda':         round(ebitda, 2),
        'utile_mese':     round(utile, 2),
        'payback_anni':   round(payback, 1),
        'payback_mesi':   round(payback * 12, 0),
        'clienti_giorno': round(clienti, 1),
        'spesa_cliente':  round(spesa_cli, 2),
        'tariffa_media':  round(t_avg_lav, 2),
        'be_clienti':     be_clienti,
        'giorni_mese':    giorni_mese,
        'ore_apertura':   ore_apertura,
        'dettaglio': {
            'variabili':     round(tot_variabili, 2),
            'energia':       round(cv_energia, 2),
            'gas':           round(cv_gas, 2),
            'acqua':         round(cv_acq + cv_sca, 2),
            'detergenti':    round(cv_det, 2),
            'fissi':         round(tot_fissi, 2),
            'affitto':       round(affitto, 2),
            'lavoro':        round(lavoro, 2),
            'commercialista':round(comm, 2),
            'cciaa':         round(cciaa, 2),
            'assicurazione': round(assic, 2),
            'manutenzione':  round(manut, 2),
            'capitale':      round(tot_capitale, 2),
            'ammortamento':  round(ammort, 2),
            'finanziamento': round(rata, 2),
        }
    })


@preventivo_bp.route('/api/analisi-ai', methods=['POST'])
@login_required
def analisi_ai():
    """Genera analisi AI della zona"""
    import anthropic
    import os

    data = request.json

    # Istanziazione robusta: compatibile con anthropic >=0.18 e >=0.40
    # Evita il bug "unexpected keyword argument 'proxies'" delle versioni intermedie
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'errore': 'ANTHROPIC_API_KEY non configurata'}), 500
    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=60.0, max_retries=1)
    except Exception as e:
        return jsonify({'errore': f'Errore init client: {str(e)}'}), 500

    # Costruisce contesto completo per l'analisi
    mac_list = data.get('macchine', [])
    mac_txt = '; '.join(
        f"{m.get('qty',1)}x {m.get('nome','')} {m.get('capacita_kg','')}kg"
        for m in mac_list if int(m.get('qty',0)) > 0
    ) or 'N/D'

    cap      = float(data.get('capex', 0) or 0)
    inc      = float(data.get('incasso_mese', 0) or 0)
    cos      = float(data.get('costi_mese', 0) or 0)
    uti      = float(data.get('utile_mese', 0) or 0)
    pay      = float(data.get('payback_anni', 0) or 0)
    cli_g    = float(data.get('clienti_giorno', 0) or 0)
    spe      = float(data.get('spesa_cliente', 0) or 0)
    be_cli   = float(data.get('be_clienti', 0) or 0)
    t_std    = float(data.get('tariffa_lavaggio_std', 6) or 6)
    t_med    = float(data.get('tariffa_lavaggio_med', 8) or 8)
    t_grd    = float(data.get('tariffa_lavaggio_grd', 10) or 10)
    t_asc    = float(data.get('tariffa_asciugatura', 3.5) or 3.5)
    p_asc    = float(data.get('perc_asciugatura', 65) or 65)
    aff      = float(data.get('affitto_mese', 0) or 0)
    det      = data.get('dettaglio_costi', {}) or {}
    giorni_mese = float(data.get('giorni_mese', 30) or 30)

    # Costruisce lista POI attractor per il prompt
    attractor_txt = ''
    for ap in data.get('attractor_points', []):
        nome = ap.get('nome', '')
        tipo = ap.get('tipo', '').replace('_', ' ')
        dist = ap.get('distanza_m', 0)
        if nome:
            attractor_txt += f"  • {nome} ({tipo}, {dist}m)\n"
    if not attractor_txt:
        attractor_txt = '  Nessun generatore di domanda strutturale rilevato nel raggio'

    # [ADD-ON COMMERCIALE] Vocazione turistica + vulnerabilità concorrenza per il prompt AI
    _vt_ai  = data.get('vocazione_turistica') or {}
    _itz_ai = data.get('intensita_turistica_zona') or {}
    _vz_ai  = data.get('vulnerabilita_zona') or {}

    if _vt_ai.get('in_top50_istat'):
        turismo_txt = (
            f"Comune in posizione #{_vt_ai.get('posizione_classifica','N/D')} nella classifica "
            f"nazionale Istat per presenze turistiche, con {int(_vt_ai.get('presenze_2024',0) or 0):,} "
            f"pernottamenti registrati nel 2024 ({_vt_ai.get('quota_pct_nazionale','N/D')}% del totale Italia)."
        )
        if _itz_ai.get('n_strutture_turismo_zona') is not None:
            turismo_txt += (
                f"\nNella zona specifica analizzata: {_itz_ai.get('n_strutture_turismo_zona')} "
                f"strutture turistiche (hotel/B&B/case vacanza) rilevate, densità locale "
                f"'{_itz_ai.get('densita_locale_label','N/D')}', indice combinato comune+zona: "
                f"{_itz_ai.get('indice_combinato','N/D')}/100."
            )
    elif _itz_ai.get('n_strutture_turismo_zona', 0) > 0:
        turismo_txt = (
            f"Comune fuori dalla Top50 nazionale Istat per volume turistico, ma nella zona "
            f"specifica risultano {_itz_ai.get('n_strutture_turismo_zona')} strutture turistiche "
            f"(hotel/B&B/case vacanza) rilevate — densità locale '{_itz_ai.get('densita_locale_label','N/D')}'."
        )
    else:
        turismo_txt = 'Nessun dato significativo di vocazione turistica rilevato per questa zona/comune.'

    if _vz_ai.get('media_vulnerabilita') is not None:
        vulnerabilita_txt = (
            f"Vulnerabilità media dei concorrenti rilevati: {_vz_ai.get('media_vulnerabilita')}/100 "
            f"({_vz_ai.get('n_concorrenti_deboli',0)} concorrenti con segnali di debolezza — rating basso "
            f"o poche recensioni — su {_vz_ai.get('n_concorrenti_valutati',0)} valutati; "
            f"{_vz_ai.get('n_concorrenti_solidi',0)} concorrenti ben radicati)."
        )
    else:
        vulnerabilita_txt = 'Dato insufficiente per calcolare la vulnerabilità media dei concorrenti.'

    # Lista concorrenti
    conc_list = data.get('competitors_detail', [])
    conc_txt = ''
    for c in conc_list[:8]:
        conc_txt += f"  • {c.get('nome','')} — {c.get('distanza_m',0)}m — Rating: {c.get('rating','N/D')} — {c.get('tipo_label','lavanderia')} — {c.get('vicinity','')}\n"
    if not conc_txt:
        conc_txt = '  Nessun concorrente diretto rilevato nel raggio analizzato'

    prompt = f"""Sei un analista di mercato specializzato nel settore retail e lavanderie self-service.
Il tuo compito è produrre una LETTURA OGGETTIVA della zona — solo dati, fatti, misurazioni.
NON dare raccomandazioni, NON dire se aprire o non aprire, NON esprimere giudizi di valore.
Limitati a descrivere ciò che i dati mostrano, come farebbe un report di analisi territoriale professionale.

═══ DATI LOCATION ═══
Indirizzo: {data.get('indirizzo','N/D')}, {data.get('citta','N/D')}
Superficie locale: {data.get('mq',60)} mq

═══ BACINO DEMOGRAFICO ═══
Popolazione raggiungibile:
  • 3 minuti a piedi (~240m): {int(data.get('pop_3min',0) or 0):,} abitanti
  • 5 minuti a piedi (~400m): {int(data.get('pop_5min',0) or 0):,} abitanti
  • 10 minuti a piedi (~800m): {int(data.get('pop_10min',0) or 0):,} abitanti
Densità abitativa: {int(data.get('densita',0) or 0):,} ab/km²
Età media zona: {float(data.get('eta_media',46) or 46):.0f} anni
Reddito medio dichiarato: €{int(data.get('reddito_medio',0) or 0):,}/anno (fonte MEF)

═══ FLUSSI E PASSAGGIO PEDONALE ═══
Indicatore traffico reale (recensioni Google entro 400m): {int(data.get('recensioni_zona',0) or 0):,}
  [Metodo: somma delle recensioni di tutti i locali commerciali entro 400m —
   stesso indicatore usato da Lidl/Eurospin/McDonald's per site selection]
Catene GDO entro 500m: {data.get('gdo_500m',0)} ({data.get('gdo_nomi','nessuna') if data.get('gdo_nomi') else 'nessuna specificata'})
Score zona complessivo: {data.get('score_zona',0)}/100

═══ CONCORRENZA DIRETTA E INDIRETTA ═══
Self-service entro 500m: {data.get('concorrenti_500m',0)}
Lavanderie totali entro 1km: {data.get('concorrenti_1km',0)}
Dettaglio operatori rilevati:
{conc_txt}

═══ GENERATORI DI DOMANDA (Attractor Points) ═══
Strutture che generano domanda strutturale per lavanderie self-service
(personale su turni, residenti senza lavatrice, utenti fissi):
{attractor_txt}

═══ VOCAZIONE TURISTICA (dati Istat 2024 + rilevazione zona) ═══
{turismo_txt}

═══ VULNERABILITÀ CONCORRENZA ═══
{vulnerabilita_txt}

═══ STRUTTURA ECONOMICA ═══
Configurazione macchine: {mac_txt}
Investimento: €{cap:,.0f} + IVA 22% = €{cap*1.22:,.0f}
Stima clienti/giorno dalla zona: {cli_g:.1f}
Incasso mensile stimato (scenario realistico): €{inc:,.0f}
Costi mensili totali: €{cos:,.0f}
Margine mensile stimato: €{uti:,.0f}
Break-even: {be_cli:.0f} clienti/giorno

═══ STRUTTURA DELL'ANALISI (obbligatoria) ═══

## 1. LETTURA DEL BACINO
Descrivi numericamente il bacino demografico. Riporta la popolazione per fascia di distanza,
la densità, il profilo reddituale. Confronta con benchmark nazionali se pertinente.
Non usare aggettivi valutativi. Solo dati e misurazioni.

## 2. ANALISI DEL PASSAGGIO PEDONALE
Leggi l'indicatore traffico ({int(data.get('recensioni_zona',0) or 0):,} recensioni entro 400m).
Interpreta cosa significa in termini di flusso giornaliero stimato.
Cita la presenza di GDO e cosa implica per il traffico di spesa.
Descrivi il tipo di zona (residenziale, commerciale, misto, industriale) dai dati disponibili.

## 3. MAPPA DELLA CONCORRENZA
Elenca e analizza i concorrenti rilevati: distanza, posizionamento, rating.
Calcola la densità operatori per abitante (operatori per 1.000 ab.).
Descrivi la distribuzione geografica della concorrenza rispetto alla sede.

## 4. GENERATORI DI DOMANDA STRUTTURALE
Elenca e descrivi gli attractor points trovati nel raggio.
Per ognuno indica: tipo di struttura, distanza, impatto atteso sui flussi
(es. ospedale = personale su turni, caserma = reclute, università = studenti fuori sede).
Quantifica dove possibile il numero di persone coinvolte.

## 4.5 TURISMO E VULNERABILITÀ CONCORRENZA
Riporta il dato di vocazione turistica del comune e della zona specifica (dati Istat 2024).
Se rilevante, spiega l'impatto di hotel/B&B/case vacanza sulla domanda potenziale
(turisti con bagagli minimi che necessitano lavaggio durante il soggiorno, gestori
di strutture ricettive che lavano biancheria con regolarità — domanda B2B ricorrente).
Riporta il dato di vulnerabilità media della concorrenza: spiega se i concorrenti rilevati
mostrano segnali di debolezza (rating basso, poche recensioni) o solidità (ben radicati).
Solo dati e misurazioni, nessuna raccomandazione.

## 5. LETTURA ECONOMICA
Riporta i numeri del business plan senza commentarli in termini di fattibilità.
Mostra: incasso stimato, costi fissi e variabili, margine, break-even.
Indica a quanti clienti/giorno corrisponde il break-even rispetto alla stima zona.
Mostra i tre scenari (pessimistico/realistico/ottimistico) con i valori assoluti.

## 5.5 CONFRONTO CON LA CONCORRENZA DIRETTA
Identifica tra i concorrenti rilevati quello più vicino e quello con rating/recensioni
più alti (anche se non coincidono). Confrontali esplicitamente: distanza, rating,
numero recensioni. Indica se il concorrente più vicino è vulnerabile (rating basso
o poche recensioni) o solido. Confronto fattuale, non giudizio sull'apertura.

## 5.6 OPPORTUNITA DI DIFFERENZIAZIONE
Sulla base dei dati concorrenza (rating, numero recensioni, distanza) e del profilo
di zona (presenza universitaria, turistica, demografica), identifica concretamente:
- quali servizi tipicamente assenti in lavanderie self-service con rating/recensioni
  basse potrebbero mancare ai concorrenti rilevati (es. pagamento app/contactless,
  capacita di carico extra-large per piumoni/tappeti, asciugatura rapida, orari 24/7,
  pulizia/igiene percepita) — deducendolo dal rating, non inventando dati specifici
  sul singolo concorrente che non sono stati forniti;
- quale segmento di clientela rilevato in zona (studenti, turisti/B&B, residenti
  senza lavatrice, professionisti) e oggi probabilmente sotto-servito dai concorrenti
  esistenti, in base a distanza e numerosità;
- 2-3 azioni concrete per intercettare clienti che oggi vanno dal concorrente più
  vicino o più numeroso (es. convenzione con una struttura specifica gia citata nel
  report, fascia oraria scoperta, servizio assente plausibile).
Resta sui dati gia raccolti in questo report (concorrenti, attractor points, profilo
zona): non inventare informazioni sui concorrenti che non sono state fornite.

## 6. VALUTAZIONE TARIFFE PROPOSTE
Confronta le tariffe inserite nel business plan con il contesto demografico rilevato
(reddito medio zona, presenza studentesca/turistica). Indica se le tariffe appaiono
in linea, sopra o sotto la sensibilità al prezzo tipica del profilo di zona descritto,
motivando con i dati già riportati sopra, senza inventare nuovi dati.

## 7. SENSIBILITA DEL RISK SCORE
Sulla base dei dati raccolti (payback, concorrenza, turismo/studenti), indica una o
due leve concrete che, se attivate, cambierebbero il quadro di rischio in modo
significativo (es. tariffa dedicata a un segmento specifico, orari estesi,
convenzione con una struttura nelle vicinanze). Resta su leve plausibili dai dati
disponibili, non generiche.

## 8. RACCOMANDAZIONE OPERATIVA
Questa e l'unica sezione con giudizio esplicito del documento. In 3-4 punti elenco,
indica azioni concrete per questa zona, basate sui dati sopra riportati (target di
clientela da privilegiare, leva competitiva contro il concorrente piu vicino,
eventuali accordi B2B da valutare). Ogni punto deve derivare da un dato specifico
gia citato in questo report, niente generico applicabile a qualsiasi zona.

Tono: dalle sezioni 1 a 7, report analitico, asciutto, numeri precisi, zero
aggettivi valutativi, zero raccomandazioni. Nelle sezioni 5.6 e 8 e ammesso un
tono diretto e consulenziale.
Rispondi in italiano. Usa intestazioni Markdown (##). Sii conciso ma completo."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3200,
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({'testo': message.content[0].text})
    except Exception as e:
        return jsonify({'errore': str(e)}), 500



@preventivo_bp.route('/api/genera-lettera', methods=['POST'])
@login_required
def genera_lettera():
    """Genera lettera di presentazione AI e la salva in DB"""
    import anthropic, os, json

    data      = request.json
    pratica_id = data.get('pratica_id')
    if not pratica_id:
        return jsonify({'errore': 'pratica_id mancante'}), 400

    p = Pratica.query.get_or_404(pratica_id)

    # Se già generata, ritorna quella salvata
    if p.lettera_presentazione and len(p.lettera_presentazione.strip()) > 100:
        return jsonify({'lettera': p.lettera_presentazione, 'cached': True})

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'errore': 'ANTHROPIC_API_KEY non configurata'}), 500

    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=60.0, max_retries=1)
    except Exception as e:
        return jsonify({'errore': f'Errore init client: {str(e)}'}), 500

    c        = p.cliente
    macchine = p.get_macchine()
    mac_txt  = '; '.join(
        f"{m.get('qty',1)}x {m.get('nome','')} {m.get('capacita_kg','')}kg"
        for m in macchine if int(m.get('qty', 0)) > 0
    ) or 'configurazione personalizzata'
    sc       = float(p.score_zona or 0)
    sc_t     = p.score_label or ('Ottima' if sc >= 8 else 'Buona' if sc >= 6 else 'Da valutare')
    cap_str  = f"€ {int(p.capex or 0):,}".replace(',', '.')
    inc_str  = f"€ {int(p.incasso_mese or 0):,}".replace(',', '.')
    pay_str  = f"{p.payback_mesi:.1f} mesi" if p.payback_mesi and p.payback_mesi < 999 else 'stimato'

    prompt = f"""Sei il responsabile commerciale senior di BIOLavaTU by Rotondi Group Srl,
azienda italiana leader nelle lavanderie self-service ecocompatibili dal 1972.

Scrivi una lettera di presentazione professionale e personalizzata per il seguente progetto:

DATI PROGETTO:
- Cliente: {c.nome if c else 'Gentile Cliente'}
- Città / Sede: {p.citta or 'N/D'}, {p.indirizzo or ''}
- Zona analizzata: Score {sc}/10 — {sc_t}
- Macchine proposte: {mac_txt}
- Investimento totale: {cap_str}
- Incasso mensile stimato: {inc_str}
- Payback stimato: {pay_str}

FORMATO RICHIESTO:
- Inizia con "Gentile {c.nome if c else 'Cliente'},"
- 4-5 paragrafi fluidi, tono professionale ma caldo
- Fai riferimento specifico alla città/zona e alle macchine scelte
- Sottolinea il valore dell'esclusiva tecnologica IPSO/Wascomat e del supporto Rotondi Group
- Chiudi con formula di saluto formale e "Rotondi Group Srl — BIOLavaTU"
- NO elenchi puntati, SOLO testo narrativo scorrevole
- Lunghezza: circa 300-350 parole
- Scrivi in italiano"""

    try:
        message = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=800,
            messages=[{'role': 'user', 'content': prompt}]
        )
        lettera_text = message.content[0].text.strip()
        # Salva in DB
        p.lettera_presentazione = lettera_text
        from app import db
        db.session.commit()
        return jsonify({'lettera': lettera_text, 'cached': False})
    except Exception as e:
        return jsonify({'errore': str(e)}), 500


