"""
routes/investitore.py — BIOLavaTU LaundryPro Platform
API endpoints versione investitore.
"""
import os, json
from flask import Blueprint, request, jsonify, abort, send_file
from flask_login import login_required, current_user
from app import db
from models.pratica import Pratica
from models.settings import Settings
from services.investitore import (
    analisi_completa_investitore,
    FASCE_ORARIE, SCHEDA_CONCORRENTE,
    MIN_OSSERVAZIONI_TRAFFICO, MIN_OSSERVAZIONI_CONCORRENTE,
)

inv_bp = Blueprint('investitore', __name__)


def _check_pratica(id):
    p = Pratica.query.get_or_404(id)
    if current_user.role not in ('owner', 'admin') and p.agente_id != current_user.id:
        abort(403)
    return p


# ── INFO FASCE E SCHEDE ───────────────────────────────────────────────────────

@inv_bp.route('/api/investitore/fasce-orarie')
@login_required
def fasce_orarie():
    return jsonify({
        'fasce':          FASCE_ORARIE,
        'min_richieste':  MIN_OSSERVAZIONI_TRAFFICO,
        'scheda_concorrente': SCHEDA_CONCORRENTE,
        'min_visite_concorrente': MIN_OSSERVAZIONI_CONCORRENTE,
    })


# ── SALVA SOPRALLUOGO TRAFFICO ────────────────────────────────────────────────

@inv_bp.route('/api/investitore/<int:id>/sopralluogo', methods=['POST'])
@login_required
def salva_sopralluogo(id):
    p = _check_pratica(id)
    data = request.json or {}

    sop = p.get_sopralluogo()
    osservazioni = sop.get('osservazioni', [])

    nuova = {
        'fascia_id':      data.get('fascia_id'),
        'data':           data.get('data'),
        'ora':            data.get('ora'),
        'pedoni_15min':   int(data.get('pedoni_15min', 0)),
        'direzione':      data.get('direzione', 'entrambe'),
        'note':           data.get('note', ''),
        'operatore':      current_user.email,
    }

    # Sostituisce se stessa fascia già presente
    existing = next((i for i, o in enumerate(osservazioni)
                     if o.get('fascia_id') == nuova['fascia_id']), None)
    if existing is not None:
        osservazioni[existing] = nuova
    else:
        osservazioni.append(nuova)

    completato = len(osservazioni) >= MIN_OSSERVAZIONI_TRAFFICO
    sop['osservazioni'] = osservazioni
    sop['completato']   = completato

    p.sopralluogo_json         = json.dumps(sop)
    p.sopralluogo_completato   = completato
    db.session.commit()

    return jsonify({
        'ok':           True,
        'n_osservazioni': len(osservazioni),
        'completato':   completato,
        'mancanti':     max(0, MIN_OSSERVAZIONI_TRAFFICO - len(osservazioni)),
        'fasce_inserite': [o['fascia_id'] for o in osservazioni],
    })


@inv_bp.route('/api/investitore/<int:id>/sopralluogo', methods=['GET'])
@login_required
def get_sopralluogo(id):
    p = _check_pratica(id)
    sop = p.get_sopralluogo()
    return jsonify({
        'sopralluogo':    sop,
        'completato':     p.sopralluogo_completato or False,
        'n_osservazioni': len(sop.get('osservazioni', [])),
        'mancanti':       max(0, MIN_OSSERVAZIONI_TRAFFICO - len(sop.get('osservazioni', []))),
        'fasce_orarie':   FASCE_ORARIE,
    })


# ── SALVA CONCORRENTE CAMPO ───────────────────────────────────────────────────

@inv_bp.route('/api/investitore/<int:id>/concorrente', methods=['POST'])
@login_required
def salva_concorrente(id):
    p = _check_pratica(id)
    data = request.json or {}

    concorrenti = p.get_concorrenza_campo()

    # Aggiorna se stesso nome, altrimenti aggiunge
    nome = data.get('nome', '').strip()
    idx  = next((i for i, c in enumerate(concorrenti)
                 if c.get('nome', '').lower() == nome.lower()), None)

    conc = {
        'nome':            nome,
        'indirizzo':       data.get('indirizzo', ''),
        'distanza_m':      int(data.get('distanza_m', 0)),
        'n_lavatrici':     int(data.get('n_lavatrici', 0)),
        'n_asciugatrici':  int(data.get('n_asciugatrici', 0)),
        'prezzo_lavaggio': float(data.get('prezzo_lavaggio', 0)),
        'prezzo_asciugatura': float(data.get('prezzo_asciugatura', 0)),
        'orario_apertura': data.get('orario_apertura', ''),
        'orario_chiusura': data.get('orario_chiusura', ''),
        'h24':             bool(data.get('h24', False)),
        'app_pagamento':   bool(data.get('app_pagamento', False)),
        'tessera_fedelta': bool(data.get('tessera_fedelta', False)),
        'eco_posizionato': bool(data.get('eco_posizionato', False)),
        'pulizia_1_5':     int(data.get('pulizia_1_5', 3)),
        'funzionamento_1_5': int(data.get('funzionamento_1_5', 3)),
        'assistenza_1_5':  int(data.get('assistenza_1_5', 3)),
        'note_punti_deboli': data.get('note_punti_deboli', ''),
        'visite':          data.get('visite', []),
        'operatore':       current_user.email,
    }

    if idx is not None:
        # Mantieni visite esistenti se non sostituite
        if not data.get('visite') and concorrenti[idx].get('visite'):
            conc['visite'] = concorrenti[idx]['visite']
        concorrenti[idx] = conc
    else:
        concorrenti.append(conc)

    p.concorrenza_campo_json = json.dumps(concorrenti)
    db.session.commit()

    n_analizzati = len([c for c in concorrenti
                        if len(c.get('visite', [])) >= MIN_OSSERVAZIONI_CONCORRENTE])
    return jsonify({
        'ok':             True,
        'n_concorrenti':  len(concorrenti),
        'n_analizzati':   n_analizzati,
    })


@inv_bp.route('/api/investitore/<int:id>/concorrente/<nome>/visita', methods=['POST'])
@login_required
def aggiungi_visita(id, nome):
    p = _check_pratica(id)
    data = request.json or {}

    concorrenti = p.get_concorrenza_campo()
    idx = next((i for i, c in enumerate(concorrenti)
                if c.get('nome', '').lower() == nome.lower()), None)
    if idx is None:
        return jsonify({'errore': 'Concorrente non trovato'}), 404

    visita = {
        'data':           data.get('data'),
        'ora':            data.get('ora'),
        'lav_occupate':   int(data.get('lav_occupate', 0)),
        'asc_occupate':   int(data.get('asc_occupate', 0)),
        'note':           data.get('note', ''),
        'operatore':      current_user.email,
    }
    concorrenti[idx].setdefault('visite', []).append(visita)

    n_visite = len(concorrenti[idx]['visite'])
    n_lav = concorrenti[idx].get('n_lavatrici', 1)
    n_asc = concorrenti[idx].get('n_asciugatrici', 1)
    occ_media = sum(
        (v.get('lav_occupate', 0) / max(1, n_lav) +
         v.get('asc_occupate', 0) / max(1, n_asc)) / 2
        for v in concorrenti[idx]['visite']
    ) / n_visite if n_visite > 0 else 0

    p.concorrenza_campo_json = json.dumps(concorrenti)
    db.session.commit()

    return jsonify({
        'ok':           True,
        'n_visite':     n_visite,
        'occ_media':    round(occ_media * 100, 1),
        'sufficiente':  n_visite >= MIN_OSSERVAZIONI_CONCORRENTE,
    })


# ── ANALISI COMPLETA ──────────────────────────────────────────────────────────

@inv_bp.route('/api/investitore/<int:id>/analisi', methods=['POST'])
@login_required
def esegui_analisi(id):
    p = _check_pratica(id)
    s = Settings.query.first()
    data = request.json or {}

    # Macchine
    macchine = p.get_macchine()
    n_std = n_med = n_grd = n_asc = 0
    for m in macchine:
        qty = int(m.get('qty', 0))
        kg  = float(m.get('capacita_kg', 0))
        nom = m.get('nome', '').lower()
        if 'asciug' in nom or 'asciug' in m.get('categoria', '').lower():
            n_asc += qty
        else:
            if kg <= 9:    n_std += qty
            elif kg <= 13: n_med += qty
            else:          n_grd += qty

    t_std = float(p.tariffa_lavaggio_std or 6)
    t_med = float(p.tariffa_lavaggio_med or 8)
    t_grd = float(p.tariffa_lavaggio_grd or 10)
    t_asc = float(p.tariffa_asciugatura or 1)

    # Zona
    geo = {}
    if p.geo_raw:
        try: geo = json.loads(p.geo_raw)
        except: pass

    concorrenti_api = p.get_competitors()
    zona_info = {}
    if p.zona_info_raw:
        try: zona_info = json.loads(p.zona_info_raw)
        except: pass

    # Analisi
    risultato = analisi_completa_investitore(
        pratica_id=p.id,
        n_std=n_std, n_med=n_med, n_grd=n_grd, n_asc=n_asc,
        t_std=t_std, t_med=t_med, t_grd=t_grd, t_asc=t_asc,
        perc_asciugatura=float(data.get('perc_asciugatura', 65)),
        capex=float(p.capex or 0),
        costi_fissi_mese=float(p.costi_mese or 0),
        concorrenti_500m=p.concorrenti_500m or 0,
        concorrenti_1km=p.concorrenti_1km or 0,
        densita=float(zona_info.get('densita', 3000)),
        recensioni_zona=int(geo.get('segnali_reali', {}).get('recensioni_zona', 0)),
        reddito_medio=float(zona_info.get('reddito_medio', 21000)),
        gdo_500m=int(geo.get('segnali_reali', {}).get('gdo_500m', 0)),
        mult_attractor=float(geo.get('mult_attractor', 1.0)),
        score_automatico=float(p.score_zona or 50),
        pop_5min=p.pop_5min or 0,
        pop_10min=p.pop_10min or 0,
        indice_famiglie_lav=int(geo.get('indice_famiglie_lav', {}).get('indice', 0)),
        sopralluogo=p.get_sopralluogo(),
        concorrenti_campo=p.get_concorrenza_campo(),
        concorrenti_api=concorrenti_api,
        visibilita_vetrina=p.visibilita_vetrina or 0,
        cantieri_previsti=p.cantieri_previsti or False,
        scenario=data.get('scenario', 'realistico'),
    )

    # Salva nel DB
    p.score_investitore       = risultato['score_investitore']
    p.confidenza_pct          = risultato['conf_pct']
    p.confidenza_label        = risultato['confidenza']
    p.raccomandazione         = risultato['raccomandazione']
    p.incasso_mese            = risultato['incasso_finale']
    p.utile_mese              = risultato['utile_mese']
    p.payback_mesi            = risultato.get('payback_mesi') or 0
    p.analisi_investitore_json = json.dumps(risultato)
    db.session.commit()

    return jsonify(risultato)


# ── STATO COMPLETAMENTO ───────────────────────────────────────────────────────

@inv_bp.route('/api/investitore/<int:id>/stato')
@login_required
def stato_completamento(id):
    p = _check_pratica(id)
    sop = p.get_sopralluogo()
    conc_campo = p.get_concorrenza_campo()

    n_obs      = len(sop.get('osservazioni', []))
    n_conc     = len(conc_campo)
    n_analizzati = len([c for c in conc_campo
                        if len(c.get('visite', [])) >= MIN_OSSERVAZIONI_CONCORRENTE])

    step_a_ok = n_obs >= MIN_OSSERVAZIONI_TRAFFICO
    step_b_ok = (p.concorrenti_500m == 0) or (n_analizzati >= min(2, p.concorrenti_500m))
    step_c_ok = (p.visibilita_vetrina or 0) > 0

    completato = step_a_ok and step_b_ok and step_c_ok

    return jsonify({
        'completato':     completato,
        'step_a':         {'ok': step_a_ok, 'n': n_obs, 'min': MIN_OSSERVAZIONI_TRAFFICO,
                           'label': 'Traffico pedonale'},
        'step_b':         {'ok': step_b_ok, 'n': n_analizzati,
                           'min': min(2, p.concorrenti_500m or 0),
                           'label': 'Analisi concorrenti'},
        'step_c':         {'ok': step_c_ok, 'label': 'Qualità locale'},
        'score':          p.score_investitore or 0,
        'raccomandazione': p.raccomandazione or '—',
        'confidenza':     p.confidenza_label or '—',
    })


# ── AGGIORNA QUALITÀ LOCALE ───────────────────────────────────────────────────

@inv_bp.route('/api/investitore/<int:id>/locale', methods=['POST'])
@login_required
def aggiorna_locale(id):
    p = _check_pratica(id)
    data = request.json or {}

    p.visibilita_vetrina  = int(data.get('visibilita_vetrina', 0))
    p.parcheggio_diretto  = bool(data.get('parcheggio_diretto', False))
    p.n_posti_parcheggio  = int(data.get('n_posti_parcheggio', 0))
    p.distanza_arteria_m  = int(data.get('distanza_arteria_m', 0))
    p.lato_soleggiato     = bool(data.get('lato_soleggiato', True))
    p.cantieri_previsti   = bool(data.get('cantieri_previsti', False))
    p.note_sopralluogo    = data.get('note_sopralluogo', '')
    p.tipo_pratica        = 'investitore'
    db.session.commit()

    return jsonify({'ok': True})

# ── PDF CAMPO ─────────────────────────────────────────────────────────────────

@inv_bp.route('/api/investitore/pdf-campo')
@login_required
def pdf_campo_generico():
    """PDF scheda sopralluogo senza pratica specifica"""
    from services.pdf_campo import build_pdf_campo
    from models.settings import Settings
    s = Settings.query.first()
    buf = build_pdf_campo(pratica=None, settings=s)
    return send_file(
        buf, mimetype='application/pdf',
        as_attachment=False,
        download_name='BIOLavaTU_Scheda_Sopralluogo.pdf'
    )


@inv_bp.route('/api/investitore/<int:id>/pdf-campo')
@login_required
def pdf_campo_pratica(id):
    """PDF scheda sopralluogo pre-compilato con dati pratica"""
    from services.pdf_campo import build_pdf_campo
    from models.settings import Settings
    p = _check_pratica(id)
    s = Settings.query.first()
    buf = build_pdf_campo(pratica=p, settings=s)
    nome = f"BIOLavaTU_Sopralluogo_{p.numero}.pdf"
    return send_file(
        buf, mimetype='application/pdf',
        as_attachment=False,
        download_name=nome
    )
