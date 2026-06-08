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


@preventivo_bp.route('/preventivo/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo():
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

    # ── CLIENTI/GIORNO DALLA ZONA ────────────────────────────────────────────
    pop5  = float(data.get('pop_5min', 0) or 0)
    pop10 = float(data.get('pop_10min', 0) or 0)
    c500  = int(data.get('concorrenti_500m', 0) or 0)
    c1k   = int(data.get('concorrenti_1km', 0) or 0)
    red   = float(data.get('reddito_medio', 21000) or 21000)
    den   = float(data.get('densita', 2000) or 2000)
    rec   = float(data.get('recensioni_zona', 0) or 0)
    gdo   = int(data.get('gdo_500m', 0) or 0)

    bacino = pop5 * 0.60 + max(0, pop10 - pop5) * 0.25
    if   den > 5000: tasso = 0.018 * 1.35
    elif den > 3000: tasso = 0.018 * 1.25
    elif den > 1500: tasso = 0.018 * 1.12
    elif den >  500: tasso = 0.018
    elif den >  200: tasso = 0.018 * 0.82
    else:            tasso = 0.018 * 0.60

    if 15000 <= red <= 24000:   mr = 1.00
    elif red > 35000:           mr = 0.65
    elif red > 24000:           mr = 0.80
    elif red > 11000:           mr = 0.90
    else:                       mr = 0.80

    if   rec > 8000: mt = 1.25
    elif rec > 4000: mt = 1.15
    elif rec > 1500: mt = 1.05
    elif rec >  400: mt = 0.92
    else:            mt = 0.75

    mg = 1.18 if gdo>=3 else 1.10 if gdo==2 else 1.04 if gdo==1 else 1.00

    if   c500 >= 5: share = 0.08
    elif c500 == 4: share = 0.12
    elif c500 == 3: share = 0.18
    elif c500 == 2: share = 0.25
    elif c500 == 1: share = 0.40
    elif c1k  >= 4: share = 0.55
    elif c1k  >= 2: share = 0.70
    elif c1k  == 1: share = 0.82
    else:           share = 1.00

    clienti = max(0, bacino * tasso * mr * mt * mg * share * mult)

    # ── INCASSO ──────────────────────────────────────────────────────────────
    incasso = clienti * spesa_cli * giorni_mese

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
        client = anthropic.Anthropic(api_key=api_key)
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

## 5. LETTURA ECONOMICA
Riporta i numeri del business plan senza commentarli in termini di fattibilità.
Mostra: incasso stimato, costi fissi e variabili, margine, break-even.
Indica a quanti clienti/giorno corrisponde il break-even rispetto alla stima zona.
Mostra i tre scenari (pessimistico/realistico/ottimistico) con i valori assoluti.

Tono: report analitico, asciutto, numeri precisi, zero aggettivi valutativi,
zero raccomandazioni, zero conclusioni su apertura/non apertura.
Rispondi in italiano. Usa intestazioni Markdown (##). Sii conciso ma completo."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({'testo': message.content[0].text})
    except Exception as e:
        return jsonify({'errore': str(e)}), 500


