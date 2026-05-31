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
    from sqlalchemy import func
    anno = datetime.datetime.now().year
    count = db.session.query(func.count(Pratica.id)).scalar() or 0
    return f"BIO-{anno}-{count+1:04d}"


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
    capex = sum(float(m.get('prezzo', 0)) * int(m.get('qty', 1)) for m in macchine_sel)

    # Business plan
    incasso = float(data.get('incasso_mese', 0) or 0)
    costi = float(data.get('costi_mese', 0) or 0)
    utile = incasso - costi
    payback = (capex / utile / 12) if utile > 0 else 0

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
    Business Plan — modello domanda reale.
    L'incasso si calcola dai CLIENTI REALI della zona (pop × tasso × moltiplicatori),
    NON dalla capacità teorica delle macchine. Le macchine devono soddisfare la domanda,
    non il contrario.
    """
    data = request.json
    settings = Settings.query.first()

    macchine  = data.get('macchine', [])
    scenario  = data.get('scenario', 'realistico')
    mult_scen = {'pessimistico': 0.60, 'realistico': 1.00, 'ottimistico': 1.25}.get(scenario, 1.0)

    # ── 1. DOMANDA REALE DALLA ZONA ──────────────────────────────────────────
    pop_5min         = float(data.get('pop_5min', 0) or 0)
    pop_10min        = float(data.get('pop_10min', 0) or 0)
    concorrenti_500m = int(data.get('concorrenti_500m', 0) or 0)
    concorrenti_1km  = int(data.get('concorrenti_1km', 0) or 0)
    reddito_medio    = float(data.get('reddito_medio', 21000) or 21000)
    densita          = float(data.get('densita', 2000) or 2000)
    eta_media        = float(data.get('eta_media', 44) or 44)
    recensioni_zona  = float(data.get('recensioni_zona', 0) or 0)
    gdo_500m         = int(data.get('gdo_500m', 0) or 0)

    # Bacino pesato
    bacino = pop_5min * 0.60 + max(0, pop_10min - pop_5min) * 0.25

    # Tasso base per densità
    if densita > 5000:   tasso = 0.018 * 1.35
    elif densita > 3000: tasso = 0.018 * 1.25
    elif densita > 1500: tasso = 0.018 * 1.12
    elif densita > 500:  tasso = 0.018
    elif densita > 200:  tasso = 0.018 * 0.82
    else:                tasso = 0.018 * 0.60

    # Moltiplicatore reddito
    if 15000 <= reddito_medio <= 24000: mr = 1.00
    elif reddito_medio > 35000:         mr = 0.65
    elif reddito_medio > 24000:         mr = 0.80
    elif reddito_medio > 11000:         mr = 0.90
    else:                               mr = 0.80

    # Moltiplicatore traffico
    if recensioni_zona > 8000:   mt = 1.25
    elif recensioni_zona > 4000: mt = 1.15
    elif recensioni_zona > 1500: mt = 1.05
    elif recensioni_zona > 400:  mt = 0.92
    else:                        mt = 0.75

    # Validazione GDO
    mg = 1.18 if gdo_500m >= 3 else 1.10 if gdo_500m == 2 else 1.04 if gdo_500m == 1 else 1.00

    # Accessibilità locale
    vis  = float(data.get('accessib_visibilita', 0.5) or 0.5)
    park = float(data.get('accessib_parcheggio', 0.5) or 0.5)
    piano= float(data.get('accessib_piano', 1.0) or 1.0)
    h24  = float(data.get('accessib_h24', 0.0) or 0.0)
    ma   = 0.70 + (vis * 0.15 + park * 0.15 + piano * 0.10 + h24 * 0.10)

    # Quota di mercato (penalità concorrenza)
    if concorrenti_500m >= 5:   share = 0.08
    elif concorrenti_500m == 4: share = 0.12
    elif concorrenti_500m == 3: share = 0.18
    elif concorrenti_500m == 2: share = 0.25
    elif concorrenti_500m == 1: share = 0.40
    elif concorrenti_1km >= 4:  share = 0.55
    elif concorrenti_1km >= 2:  share = 0.70
    elif concorrenti_1km == 1:  share = 0.82
    else:                       share = 1.00

    # Clienti/giorno reali
    clienti_giorno = max(0, bacino * tasso * mr * mt * mg * ma * share * mult_scen)

    # Cicli/mese da domanda (non da capacità macchine)
    cicli_lavaggio_mese  = clienti_giorno * 26          # 1 ciclo/cliente/giorno
    cicli_asciugatura_mese = cicli_lavaggio_mese * 0.65  # 65% lava anche asciuga

    # ── 2. CAPEX E INCASSO ───────────────────────────────────────────────────
    capex = 0
    kw_totale = 0
    incasso_lavaggio = 0
    incasso_asciugatura = 0
    cicli_giorno_tot = 0
    gas_mc_giorno = 0

    n_lav = sum(int(m.get('qty', 1)) for m in macchine
                if float(m.get('tariffa', 0)) > 0
                and 'asciug' not in m.get('nome', '').lower()
                and 'asciug' not in m.get('categoria', '').lower())
    n_asc = sum(int(m.get('qty', 1)) for m in macchine
                if float(m.get('tariffa', 0)) > 0
                and ('asciug' in m.get('nome', '').lower()
                     or 'asciug' in m.get('categoria', '').lower()))

    for m in macchine:
        qty    = int(m.get('qty', 1))
        prezzo = float(m.get('prezzo_effettivo', 0) or m.get('prezzo', 0))
        kw     = float(m.get('kw', 0))
        tariffa= float(m.get('tariffa', 0))
        comb   = m.get('combustibile', 'elettrico')
        mc_ciclo = float(m.get('mc_ciclo', 0))
        nome   = m.get('nome', '').lower()
        cat    = m.get('categoria', '').lower()

        capex     += prezzo * qty
        kw_totale += kw * qty

        if tariffa > 0:
            is_asc = 'asciug' in nome or 'asciug' in cat
            if is_asc:
                # Cicli asciugatura distribuiti sulle macchine disponibili
                cicli_mac = (cicli_asciugatura_mese / n_asc * qty) if n_asc > 0 else 0
                incasso_asciugatura += tariffa * cicli_mac
                cicli_giorno_tot    += (cicli_mac / 26)
                if comb == 'gas':
                    gas_mc_giorno += mc_ciclo * (cicli_mac / 26)
            else:
                # Cicli lavaggio distribuiti sulle macchine disponibili
                cicli_mac = (cicli_lavaggio_mese / n_lav * qty) if n_lav > 0 else 0
                incasso_lavaggio += tariffa * cicli_mac
                cicli_giorno_tot += (cicli_mac / 26)
                if comb == 'gas':
                    gas_mc_giorno += mc_ciclo * (cicli_mac / 26)

    incasso = incasso_lavaggio + incasso_asciugatura

    # ── 3. COSTI ─────────────────────────────────────────────────────────────
    kwh_cost     = float(data.get('kwh_cost')        or (settings.kwh_cost      if settings else 0.28))
    gas_cost     = float(data.get('gas_mc_cost')     or (settings.gas_mc_cost   if settings else 1.20))
    acqua_cost   = float(data.get('acqua_mc_cost')   or (settings.acqua_mc_cost if settings else 2.50))
    scarico_cost = float(data.get('scarico_mc_cost') or (settings.scarico_mc_cost if settings else 1.80))

    ore_uso       = max(1.0, cicli_giorno_tot * 1.2)
    costo_energia = kw_totale * ore_uso * 26 * kwh_cost
    costo_gas     = gas_mc_giorno * 26 * gas_cost
    acqua_mc      = cicli_giorno_tot * 0.055 * 26
    costo_acqua   = acqua_mc * acqua_cost
    costo_scarico = acqua_mc * scarico_cost

    affitto        = float(data.get('affitto_mese', 0) or 0)
    commercialista = float(data.get('commercialista') or (settings.commercialista if settings else 150))
    cciaa          = float(data.get('cciaa')           or (settings.cciaa          if settings else 50))
    assicurazione  = float(data.get('assicurazione')   or (settings.assicurazione  if settings else 100))
    manutenzione   = float(data.get('manutenzione')    or (settings.manutenzione   if settings else 200))
    costo_lavoro   = float(data.get('costo_lavoro', 480) or 480)

    anni_amm     = float(data.get('anni_ammortamento', 10) or 10)
    ammortamento = capex / anni_amm / 12

    perc_fin   = float(data.get('perc_finanziato', 0) or 0) / 100.0
    tasso_int  = float(data.get('tasso_interesse', 6.0) or 6.0) / 100.0
    anni_prest = float(data.get('anni_prestito', 7) or 7)
    cap_fin    = capex * 1.22 * perc_fin
    if cap_fin > 0 and anni_prest > 0:
        r = tasso_int / 12
        n = anni_prest * 12
        rata = cap_fin * (r * (1+r)**n) / ((1+r)**n - 1)
    else:
        rata = 0

    det1 = det2 = det3 = 0.0
    if settings and cicli_giorno_tot > 0:
        det1 = (settings.det1_grammi_ciclo/1000)*settings.det1_costo_kg*cicli_giorno_tot*26
        det2 = (settings.det2_grammi_ciclo/1000)*settings.det2_costo_kg*cicli_giorno_tot*26
        det3 = (settings.det3_grammi_ciclo/1000)*settings.det3_costo_kg*cicli_giorno_tot*26

    costi_totali = (costo_energia + costo_gas + costo_acqua + costo_scarico +
                    affitto + commercialista + cciaa + assicurazione + manutenzione +
                    costo_lavoro + ammortamento + rata + det1 + det2 + det3)

    utile     = incasso - costi_totali
    capex_iva = round(capex * 1.22, 2)
    payback   = (capex_iva / utile / 12) if utile > 0 else 0

    return jsonify({
        'capex':               round(capex, 2),
        'capex_iva':           capex_iva,
        'incasso_mese':        round(incasso, 2),
        'incasso_lavaggio':    round(incasso_lavaggio, 2),
        'incasso_asciugatura': round(incasso_asciugatura, 2),
        'costi_mese':          round(costi_totali, 2),
        'utile_mese':          round(utile, 2),
        'payback_anni':        round(payback, 1),
        'payback_mesi':        round(payback * 12, 0),
        'cicli_giorno':        round(clienti_giorno, 1),
        'dettaglio': {
            'energia':        round(costo_energia, 2),
            'gas':            round(costo_gas, 2),
            'acqua':          round(costo_acqua, 2),
            'scarico':        round(costo_scarico, 2),
            'affitto':        round(affitto, 2),
            'lavoro':         round(costo_lavoro, 2),
            'ammortamento':   round(ammortamento, 2),
            'finanziamento':  round(rata, 2),
            'commercialista': round(commercialista, 2),
            'cciaa':          round(cciaa, 2),
            'assicurazione':  round(assicurazione, 2),
            'manutenzione':   round(manutenzione, 2),
            'det1':           round(det1, 2),
            'det2':           round(det2, 2),
            'det3':           round(det3, 2),
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

    prompt = f"""Sei un esperto di laundromats (lavanderie self-service) in Italia.

Analizza questa zona per aprire una lavanderia self-service:
- Indirizzo: {data.get('indirizzo', 'N/D')}
- Città: {data.get('citta', 'N/D')}
- Popolazione nel raggio 5 min a piedi: {int(data.get('pop_5min', 0) or 0):,} abitanti
- Popolazione nel raggio 10 min a piedi: {int(data.get('pop_10min', 0) or 0):,} abitanti
- Concorrenti entro 500m: {data.get('concorrenti_500m', 0)}
- Concorrenti entro 1km: {data.get('concorrenti_1km', 0)}
- Servizi nelle vicinanze (400m): {data.get('servizi_400m', 0)} attività
- Score zona: {data.get('score_zona', 0)}/100 ({data.get('score_label', '')})
- Superficie locale: {data.get('mq', 60)} mq
- Stima clienti/giorno (modello pesato): {data.get('stima_clienti', 'N/D')}
- Recensioni Google nella zona (proxy traffico reale): {data.get('recensioni_zona', 'N/D')}
- Catene GDO entro 500m (Lidl/Eurospin/Conad ecc.): {data.get('gdo_500m', 'N/D')}

Fornisci:
1. Analisi della zona (3-4 righe)
2. Punti di forza (2-3 punti)
3. Rischi e criticità (2-3 punti)
4. Raccomandazione finale (1-2 righe)

Sii diretto, pratico e professionale. Rispondi in italiano."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({'testo': message.content[0].text})
    except Exception as e:
        return jsonify({'errore': str(e)}), 500
