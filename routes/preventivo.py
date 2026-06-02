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
        lat=float(data.get('lat', 0) or 0),
        lng=float(data.get('lng', 0) or 0),
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
        tariffa_lavaggio_std=float(data.get('tariffa_lavaggio_std', 4) or 4),
        tariffa_lavaggio_med=float(data.get('tariffa_lavaggio_med', 5) or 5),
        tariffa_lavaggio_grd=float(data.get('tariffa_lavaggio_grd', 7) or 7),
        tariffa_asciugatura=float(data.get('tariffa_asciugatura', 3) or 3),
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
    t_std  = float(data.get('tariffa_lavaggio_std', 4.0) or 4.0)
    t_med  = float(data.get('tariffa_lavaggio_med', 5.0) or 5.0)
    t_grd  = float(data.get('tariffa_lavaggio_grd', 7.0) or 7.0)
    t_asc  = float(data.get('tariffa_asciugatura',  3.0) or 3.0)
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
    # Energia = uso macchine (cicli × durata) + standby (ore apertura × 0.5kW illuminaz.)
    kw_standby = 0.5 + (max(1, n_lav + n_asc) * 0.05)  # illuminazione + controlli
    cv_energia = (
        (kw_lav * c_lav * 0.75 + kw_asc * c_asc * 0.67)  # uso macchine
        + kw_standby * ore_apertura                        # standby/illuminazione
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
    import httpx
    import os

    data = request.json

    # Istanziazione robusta: compatibile con anthropic >=0.18 e >=0.40
    # Evita il bug "unexpected keyword argument 'proxies'" delle versioni intermedie
    try:
        http_client = httpx.Client()
        client = anthropic.Anthropic(
            api_key=os.environ.get('ANTHROPIC_API_KEY'),
            http_client=http_client,
        )
    except TypeError:
        # Fallback per versioni molto vecchie
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

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
    t_std    = float(data.get('tariffa_lavaggio_std', 4) or 4)
    t_med    = float(data.get('tariffa_lavaggio_med', 5) or 5)
    t_grd    = float(data.get('tariffa_lavaggio_grd', 7) or 7)
    t_asc    = float(data.get('tariffa_asciugatura', 3) or 3)
    p_asc    = float(data.get('perc_asciugatura', 65) or 65)
    aff      = float(data.get('affitto_mese', 0) or 0)
    det      = data.get('dettaglio_costi', {}) or {}

    prompt = f"""Sei un consulente senior specializzato in apertura di lavanderie self-service in Italia.
Devi produrre un'analisi professionale, strutturata e onesta — come farebbe un consulente Bocconi/McKinsey.

═══ LOCATION ═══
Indirizzo: {data.get('indirizzo','N/D')}, {data.get('citta','N/D')} | Superficie: {data.get('mq',60)} mq
Popolazione: 5min={int(data.get('pop_5min',0) or 0):,} ab. | 10min={int(data.get('pop_10min',0) or 0):,} ab.
Densità: {int(data.get('densita',0) or 0):,} ab/km² | Reddito medio: €{int(data.get('reddito_medio',0) or 0):,}/anno
Concorrenti self-service 500m: {data.get('concorrenti_500m',0)} | Lavanderie 1km: {data.get('concorrenti_1km',0)}
Score zona: {data.get('score_zona',0)}/100 ({data.get('score_label','')}) | Traffico: {int(data.get('recensioni_zona',0) or 0):,} rec. | GDO 500m: {data.get('gdo_500m',0)}

═══ INVESTIMENTO ═══
Macchine: {mac_txt}
CAPEX: €{cap:,.0f} | CAPEX+IVA 22%: €{cap*1.22:,.0f}
Ammortamento: €{float(det.get('ammortamento',cap/120) or 0):,.0f}/mese (10 anni) | Rata fin.: €{float(det.get('finanziamento',0) or 0):,.0f}/mese

═══ TARIFFE IMPOSTATE ═══
Lav. piccola (≤9kg): €{t_std} | Lav. media (10-13kg): €{t_med} | Lav. grande (≥14kg): €{t_grd}
Asciugatura: €{t_asc}/ciclo | Clienti che asciugano: {p_asc:.0f}%
→ Spesa media per visita: €{spe:.2f} (lav. + quota asciugatura)

═══ BUSINESS PLAN — SCENARIO REALISTICO ═══
Clienti stimati: {cli_g:.1f}/giorno → {cli_g*26:.0f}/mese
Ricavi mensili: €{inc:,.0f}
  di cui costi variabili: €{float(det.get('variabili',0) or 0):,.0f} (energia €{float(det.get('energia',0) or 0):,.0f} | acqua €{float(det.get('acqua',0) or 0):,.0f} | deterg. €{float(det.get('detergenti',0) or 0):,.0f})
  di cui costi fissi: €{float(det.get('fissi',0) or 0):,.0f} (affitto €{aff:,.0f} | manut/assic/comm €{float(det.get('manutenzione',0) or 0)+float(det.get('assicurazione',0) or 0)+float(det.get('commercialista',0) or 0):,.0f})
  di cui capitale: €{float(det.get('capitale',0) or 0):,.0f} (ammort. + fin.)
Totale costi: €{cos:,.0f}
EBITDA: €{float(data.get('ebitda',inc-cos) or 0):,.0f}/mese
Utile netto mensile: €{uti:,.0f}
Payback: {pay:.1f} anni (su CAPEX+IVA)
Break-even: {be_cli:.0f} clienti/giorno per coprire costi fissi e capitale

Scenario pessimistico (×0.60): ricavi €{inc*0.60:,.0f} | utile €{(inc*0.60-cos):,.0f}
Scenario ottimistico (×1.25): ricavi €{inc*1.25:,.0f} | utile €{(inc*1.25-cos):,.0f}

═══ ANALISI RICHIESTA (struttura obbligatoria) ═══

## 1. SINTESI LOCATION
3-4 righe. Cita i numeri. Valuta potenziale demografico vs pressione competitiva.

## 2. PUNTI DI FORZA
2-4 punti concreti con dato a supporto.

## 3. RISCHI E CRITICITÀ
2-4 rischi concreti. Se i numeri sono negativi, dillo chiaramente.

## 4. ANALISI ECONOMICA
- La spesa media di €{spe:.2f}/visita è realistica per questa zona e queste tariffe?
- Con {cli_g:.0f} clienti/giorno, i ricavi di €{inc:,.0f}/mese coprono i costi di €{cos:,.0f}/mese?
- Il break-even di {be_cli:.0f} clienti/giorno è raggiungibile in questa zona con questa concorrenza?
- Da quando l'attività diventa profittevole? (mese stimato dall'apertura)
- Confronto tra i 3 scenari.

## 5. RACCOMANDAZIONE
Scegli UNA e motiva in 3 righe:
✅ CONSIGLIATO
⚠️ CONSIGLIATO CON RISERVE — specificare condizioni
❌ SCONSIGLIATO — specificare cosa cercare di diverso

Tono: professionale, diretto, numeri precisi. NON essere ottimista per compiacere. Rispondi in italiano."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({'testo': message.content[0].text})
    except Exception as e:
        return jsonify({'errore': str(e)}), 500
