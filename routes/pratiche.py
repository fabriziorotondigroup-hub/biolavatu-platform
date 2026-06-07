from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from models.pratica import Pratica
from models.cliente import Cliente
from models.settings import Settings
from app import db
import json, io, datetime

pratiche_bp = Blueprint('pratiche', __name__)

STATI = ['bozza', 'inviato', 'trattativa', 'firmato', 'perso']


@pratiche_bp.route('/pratiche')
@login_required
def index():
    stato = request.args.get('stato', '')
    q = request.args.get('q', '')
    query = Pratica.query
    if not current_user.is_admin:
        query = query.filter_by(agente_id=current_user.id)
    if stato:
        query = query.filter_by(stato=stato)
    if q:
        query = query.join(Cliente).filter(
            Cliente.nome.ilike(f'%{q}%') |
            Cliente.azienda.ilike(f'%{q}%') |
            Pratica.numero.ilike(f'%{q}%')
        )
    pratiche = query.order_by(Pratica.created.desc()).all()
    return render_template('pratiche.html', pratiche=pratiche, stato=stato, q=q, stati=STATI)


@pratiche_bp.route('/pratiche/<int:id>')
@login_required
def dettaglio(id):
    p = Pratica.query.get_or_404(id)
    return render_template('pratica_dettaglio.html', pratica=p)


@pratiche_bp.route('/pratiche/<int:id>/stato', methods=['POST'])
@login_required
def aggiorna_stato(id):
    p = Pratica.query.get_or_404(id)
    nuovo_stato = request.form.get('stato')
    if nuovo_stato in STATI:
        p.stato = nuovo_stato
        db.session.commit()
        flash(f'Stato aggiornato: {nuovo_stato}', 'success')
    return redirect(url_for('pratiche.dettaglio', id=id))


@pratiche_bp.route('/pratiche/<int:id>/fattibilita', methods=['POST'])
@login_required
def aggiorna_fattibilita(id):
    p = Pratica.query.get_or_404(id)
    val = int(request.form.get('fattibilita', 50))
    p.fattibilita = max(0, min(100, val))
    db.session.commit()
    return jsonify({'ok': True, 'fattibilita': p.fattibilita})


@pratiche_bp.route('/pratiche/<int:id>/elimina', methods=['POST'])
@login_required
def elimina(id):
    p = Pratica.query.get_or_404(id)
    if not current_user.is_admin and p.agente_id != current_user.id:
        flash('Non autorizzato.', 'error')
        return redirect(url_for('pratiche.index'))
    db.session.delete(p)
    db.session.commit()
    flash('Pratica eliminata.', 'success')
    return redirect(url_for('pratiche.index'))



def _render_ai_text(testo, story, st, body, h2, BSCURO, VERDE, ROSSO, ARANCIO, Spacer, Paragraph):
    """Renderizza testo AI nel PDF con formattazione corretta."""
    from reportlab.lib import colors as _colors
    righe = testo.split('\n')
    for riga in righe:
        r = riga.strip()
        if not r:
            story.append(Spacer(1, 4))
            continue
        if r.startswith('---'):
            story.append(Spacer(1, 6))
            continue
        if r.startswith('##') or r.startswith('#'):
            titolo = r.lstrip('#').strip()
            col = BSCURO
            if any(k in titolo.upper() for k in ['FORZA', 'POSITIV']):
                col = VERDE
            elif any(k in titolo.upper() for k in ['RISCHIO', 'CRITICA', 'SCONSIG']):
                col = ROSSO
            elif any(k in titolo.upper() for k in ['ECONOMICA', 'PIANO', 'BUSINESS']):
                col = _colors.HexColor('#2563eb')
            elif any(k in titolo.upper() for k in ['RACCOMAND', 'CONCLUS']):
                col = ARANCIO
            story.append(Spacer(1, 8))
            import re as _re2
            titolo_clean = _re2.sub(r'[*][*](.+?)[*][*]', r'\1', titolo)
            story.append(Paragraph(titolo_clean, st('ai_h', fontSize=10,
                fontName='Helvetica-Bold', textColor=col, spaceBefore=4, spaceAfter=3)))
            continue
        import re as _re
        r_safe = r.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        r_safe = _re.sub(r'[*][*](.+?)[*][*]', r'<b>\1</b>', r_safe)
        r_html = r_safe
        if r_html.startswith('- ') or r_html.startswith('\u2022 '):
            r_html = '\u2022 ' + r_html[2:]
            story.append(Paragraph(r_html, st('ai_li', fontSize=9,
                leftIndent=12, spaceBefore=2)))
        else:
            story.append(Paragraph(r_html, body))


def _get_mappa_statica(lat, lng, gmaps_key, width_px=520, height_px=300, concorrenti=None):
    """Scarica mappa statica Google Maps con marker sede + concorrenti + cerchi 500m/1km."""
    if not lat or not lng or not gmaps_key:
        return None
    try:
        import urllib.request as _ur, urllib.parse as _up
        parts = [
            f"center={lat},{lng}",
            f"zoom=15",
            f"size={width_px}x{height_px}",
            f"scale=2",
            f"maptype=roadmap",
            # Marker principale: stella gialla = sede proposta
            f"markers=color:yellow|size:mid|label:S|{lat},{lng}",
        ]
        # Markers concorrenti (rosso=self-service, arancio=tradizionale, blu=industriale)
        if concorrenti:
            # Raggruppa per colore per ridurre parametri URL
            self_sv = [c for c in concorrenti if c.get('tipo') == 'self_service']
            tradi   = [c for c in concorrenti if c.get('tipo') == 'tradizionale']
            indust  = [c for c in concorrenti if c.get('tipo') == 'industriale']
            for group, color, lbl in [(self_sv,'red','C'),(tradi,'orange','T'),(indust,'blue','I')]:
                if group:
                    locs = '|'.join(f"{c['lat']},{c['lng']}" for c in group[:8])
                    parts.append(f"markers=color:{color}|size:small|label:{lbl}|{locs}")
        # Stile mappa scuro/elegante
        styles = [
            "style=element:geometry|color:0x1d2c4d",
            "style=element:labels.text.fill|color:0x8ec3b9",
            "style=element:labels.text.stroke|color:0x1a3646",
            "style=feature:road|element:geometry|color:0x304a7d",
            "style=feature:road|element:geometry.stroke|color:0x255763",
            "style=feature:water|element:geometry|color:0x0e1626",
            "style=feature:poi|visibility:off",
            f"key={gmaps_key}",
        ]
        url = "https://maps.googleapis.com/maps/api/staticmap?" + "&".join(parts + styles)
        req = _ur.Request(url, headers={"User-Agent": "BIOLavaTU-PDF"})
        with _ur.urlopen(req, timeout=8) as r:
            return r.read()
    except Exception:
        return None


def _bar_chart_horizontal(canvas, x, y, items, bar_height=14, bar_gap=6, max_width=200,
                            fill_color=None, label_color=None, val_color=None):
    """Disegna mini grafico a barre orizzontale direttamente sul canvas ReportLab."""
    from reportlab.lib import colors as _c
    fc = fill_color or _c.HexColor('#2563eb')
    lc = label_color or _c.HexColor('#64748b')
    vc = val_color or _c.HexColor('#0f172a')
    if not items:
        return
    max_val = max(v for _, v in items) or 1
    for i, (label, val) in enumerate(items):
        bar_y = y - i * (bar_height + bar_gap)
        bw = max_width * (val / max_val)
        # sfondo barra
        canvas.setFillColor(_c.HexColor('#e2e8f0'))
        canvas.rect(x + 60, bar_y, max_width, bar_height, fill=1, stroke=0)
        # barra valore
        canvas.setFillColor(fc)
        canvas.rect(x + 60, bar_y, bw, bar_height, fill=1, stroke=0)
        # etichetta sinistra
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(lc)
        canvas.drawRightString(x + 56, bar_y + 3, label[:18])
        # valore destra
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(vc)
        canvas.drawString(x + 64 + max_width, bar_y + 3, f'{val:,}')


@pratiche_bp.route('/pratiche/<int:id>/pdf')
@login_required
def genera_pdf(id):
    try:
        return _genera_pdf_interno(id)
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        from flask import current_app
        current_app.logger.error(f"PDF ERROR: {err}")
        return f"<pre>ERRORE PDF:\n{err}</pre>", 500

def _genera_pdf_interno(id):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, HRFlowable, PageBreak, KeepTogether)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.platypus.flowables import Flowable
    from pypdf import PdfWriter, PdfReader
    import os, io as _io

    p  = Pratica.query.get_or_404(id)
    s  = Settings.query.first()
    W, H = A4

    BLU   = colors.HexColor('#2563eb')
    BSCURO= colors.HexColor('#1e3a5f')
    GRIGIO= colors.HexColor('#64748b')
    SCURO = colors.HexColor('#0f172a')
    VERDE = colors.HexColor('#10b981')
    ROSSO = colors.HexColor('#ef4444')
    ARANCIO=colors.HexColor('#f59e0b')
    BG    = colors.HexColor('#f8fafc')
    BIANCO= colors.white

    brand   = (s.brand_name   or 'BIOLavaTU') if s else 'BIOLavaTU'
    company = (s.company_name or 'Rotondi Group Srl') if s else 'Rotondi Group Srl'
    addr    = (s.company_addr  or '') if s else ''
    email   = (s.company_email or '') if s else ''
    web     = (s.company_web   or '') if s else ''
    tel     = (s.company_tel   or '') if s else ''

    _st_counter = [0]
    def st(name, **kw):
        _st_counter[0] += 1
        uname = f'{name}_{_st_counter[0]}'
        kw.setdefault('fontSize', 9)
        kw.setdefault('fontName', 'Helvetica')
        kw.setdefault('textColor', SCURO)
        kw.setdefault('leading', 13)
        return ParagraphStyle(uname, **kw)
    h1  = st('h1',  fontSize=13, fontName='Helvetica-Bold', textColor=BSCURO,
              spaceBefore=14, spaceAfter=6)
    h2  = st('h2',  fontSize=10, fontName='Helvetica-Bold', textColor=GRIGIO,
              spaceBefore=8,  spaceAfter=3)
    body= st('bd',  fontSize=9,  leading=14)
    mu  = st('mu',  fontSize=8,  textColor=GRIGIO)

    page_n = [0]
    def on_page(cv, doc):
        page_n[0] += 1
        if page_n[0] == 1:
            return
        cv.saveState()
        cv.setFillColor(BSCURO); cv.rect(0, H-1.2*cm, W, 1.2*cm, fill=1, stroke=0)
        cv.setFont('Helvetica-Bold', 9); cv.setFillColor(BIANCO)
        cv.drawString(2*cm, H-0.85*cm, brand)
        cv.setFont('Helvetica', 8)
        cv.drawRightString(W-2*cm, H-0.85*cm, f'Preventivo {p.numero}')
        cv.setFillColor(BG); cv.rect(0, 0, W, 0.9*cm, fill=1, stroke=0)
        cv.setFont('Helvetica', 7); cv.setFillColor(GRIGIO)
        cv.drawString(2*cm, 0.32*cm, f'{company}  ·  {addr}')
        cv.drawRightString(W-2*cm, 0.32*cm, f'Pag. {page_n[0]-1}')
        cv.restoreState()

    main_buf = _io.BytesIO()
    doc = SimpleDocTemplate(main_buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.6*cm, bottomMargin=1.4*cm,
        allowSplitting=1,
        onPage=on_page, onLaterPages=on_page)

    def sez(titolo, icona=''):
        t = Table([[Paragraph(f'<b>{icona}  {titolo}</b>',
                   st('sh', fontSize=11, fontName='Helvetica-Bold',
                      textColor=BIANCO, leading=16))]],
                  colWidths=[W-4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),BSCURO),
            ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('LEFTPADDING',(0,0),(-1,-1),10)]))
        return t

    def kpi_box(items):
        n = len(items)
        cw = (W-4*cm)/n
        cells = []
        for lbl,val,col in items:
            cells.append(Table([
                [Paragraph(f'<font color="{col}"><b>{val}</b></font>',
                    st(f'kv{lbl}', fontSize=13, fontName='Helvetica-Bold',
                       alignment=TA_CENTER, textColor=colors.HexColor(col)))],
                [Paragraph(lbl, st(f'kl{lbl}', fontSize=8, textColor=GRIGIO,
                                    alignment=TA_CENTER))],
            ], colWidths=[cw]))
        row = Table([cells], colWidths=[cw]*n)
        row.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),BG),
            ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#e2e8f0')),
            ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#e2e8f0')),
            ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        return row

    story = []

    # ── COPERTINA ────────────────────────────────────────────────────────────
    class Cover(Flowable):
        def __init__(self):
            Flowable.__init__(self)
            self.width  = W - 4*cm
            self.height = H - 6*cm
        def draw(self):
            c = self.canv
            w, h = self.width, self.height

            c.setFillColor(BSCURO)
            c.roundRect(0, 0, w, h, 12, fill=1, stroke=0)

            c.setFillColor(colors.HexColor('#0a1628'))
            c.roundRect(0, h-5.5*cm, w, 5.5*cm, 12, fill=1, stroke=0)
            c.rect(0, h-5.5*cm, w, 0.5*cm, fill=1, stroke=0)

            brand_txt = brand[:20] if len(brand) > 20 else brand
            c.setFont('Helvetica-Bold', 28)
            c.setFillColor(BIANCO)
            c.drawCentredString(w/2, h-2.2*cm, brand_txt)

            c.setFont('Helvetica', 9)
            c.setFillColor(colors.HexColor('#93c5fd'))
            c.drawCentredString(w/2, h-3.0*cm, 'LaundryPro Platform  —  Analisi di Fattibilita')

            c.setStrokeColor(BLU); c.setLineWidth(1)
            c.line(w*0.15, h-3.6*cm, w*0.85, h-3.6*cm)

            c.setFillColor(BLU)
            c.roundRect(w*0.2, h-5.8*cm, w*0.6, 1.4*cm, 8, fill=1, stroke=0)
            c.setFont('Helvetica-Bold', 14); c.setFillColor(BIANCO)
            c.drawCentredString(w/2, h-5.0*cm, p.numero)
            c.setFont('Helvetica', 7); c.setFillColor(colors.HexColor('#bfdbfe'))
            c.drawCentredString(w/2, h-5.55*cm,
                f'Data: {p.created.strftime("%d/%m/%Y")}  |  Stato: {p.stato.upper()}')

            cliente = p.cliente
            nome_cl = (cliente.nome_completo if cliente else 'Cliente')[:40]
            c.setFont('Helvetica-Bold', 11); c.setFillColor(BIANCO)
            c.drawCentredString(w/2, h-7.0*cm, nome_cl)
            ind = f'{p.indirizzo}, {p.citta}' if p.indirizzo else (p.citta or '')
            ind = ind[:60]
            c.setFont('Helvetica', 8); c.setFillColor(colors.HexColor('#93c5fd'))
            c.drawCentredString(w/2, h-7.7*cm, ind)

            capex_iva = p.capex * 1.22
            kpis = [
                ('INVESTIMENTO IVA', f'EUR {capex_iva:,.0f}', '#3b82f6'),
                ('INCASSO/MESE',     f'EUR {p.incasso_mese:,.0f}',
                 '#10b981' if p.incasso_mese > 0 else '#ef4444'),
                ('UTILE/MESE',       f'EUR {p.utile_mese:,.0f}',
                 '#10b981' if p.utile_mese >= 0 else '#ef4444'),
                ('PAYBACK',
                 f'{int(p.payback_mesi/12) if p.payback_mesi else "N/D"} anni', '#f59e0b'),
            ]
            margin = 0.3*cm
            bw = (w - margin * 3) / 4
            by = h - 11.2*cm
            for i, (lbl, val, col) in enumerate(kpis):
                bx = i * (bw + margin)
                c.setFillColor(colors.HexColor('#0f2340'))
                c.roundRect(bx, by, bw, 2.2*cm, 6, fill=1, stroke=0)
                c.setFont('Helvetica', 6.5); c.setFillColor(colors.HexColor('#93c5fd'))
                c.drawCentredString(bx+bw/2, by+1.7*cm, lbl)
                c.setFont('Helvetica-Bold', 9); c.setFillColor(colors.HexColor(col))
                c.drawCentredString(bx+bw/2, by+0.9*cm, val)

            sc = int(p.score_zona or 0)
            scol = '#10b981' if sc >= 70 else '#f59e0b' if sc >= 45 else '#ef4444'
            c.setFont('Helvetica', 8); c.setFillColor(colors.HexColor('#93c5fd'))
            c.drawCentredString(w/2, h-12.5*cm, 'SCORE ZONA')
            c.setFont('Helvetica-Bold', 30); c.setFillColor(colors.HexColor(scol))
            c.drawCentredString(w/2, h-13.8*cm, f'{sc}/100')
            c.setFont('Helvetica', 9); c.setFillColor(BIANCO)
            c.drawCentredString(w/2, h-14.5*cm, p.score_label or '')

            c.setFont('Helvetica', 7); c.setFillColor(colors.HexColor('#64748b'))
            c.drawCentredString(w/2, 0.8*cm, f'{company}  {web}  {tel}')
            c.drawCentredString(w/2, 0.2*cm, 'Documento riservato - uso interno')

    story.append(Cover()); story.append(PageBreak())

    # ── CLIENTE E SEDE ───────────────────────────────────────────────────────
    story.append(sez('CLIENTE E SEDE', '')); story.append(Spacer(1,6))
    cliente=p.cliente
    rows=[
        ['Cliente', cliente.nome_completo if cliente else ''],
        ['Indirizzo', f'{p.indirizzo}, {p.citta}' if p.indirizzo else p.citta or ''],
        ['CAP / Provincia', f'{p.cap or ""}  -  {p.provincia or ""}'],
        ['Superficie', f'{p.mq or ""} mq'],
    ]
    if cliente and cliente.email:    rows.append(['Email',    cliente.email])
    if cliente and cliente.telefono: rows.append(['Telefono', cliente.telefono])
    tbl=Table(rows,colWidths=[3.5*cm,13.5*cm])
    tbl.setStyle(TableStyle([
        ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
        ('TEXTCOLOR',(0,0),(0,-1),GRIGIO),('TEXTCOLOR',(1,0),(1,-1),SCURO),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),
        ('LINEBELOW',(0,0),(-1,-1),0.3,colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[BIANCO,BG])]))
    story.append(tbl); story.append(Spacer(1,14))

    # ── ANALISI ZONA ─────────────────────────────────────────────────────────
    story.append(sez('ANALISI ZONA', '')); story.append(Spacer(1,6))

    # Mappa statica Google Maps
    gmaps_key = os.environ.get('GMAPS_KEY', '')
    if p.lat and p.lng and gmaps_key:
        # Estrai concorrenti dai POI salvati
        _conc_list = []
        try:
            import json as _j2
            _pois_raw = p.pois_raw if hasattr(p, 'pois_raw') and p.pois_raw else '[]'
            _all_pois = _j2.loads(_pois_raw) if isinstance(_pois_raw, str) else (_pois_raw or [])
            _conc_list = [x for x in _all_pois if x.get('tipo') in
                          ('self_service','tradizionale','industriale','concorrente')]
        except Exception:
            _conc_list = []
        mappa_bytes = _get_mappa_statica(p.lat, p.lng, gmaps_key, 520, 260, concorrenti=_conc_list)
        if mappa_bytes:
            from reportlab.platypus import Image as RLImage
            import io as _io2
            img_buf = _io2.BytesIO(mappa_bytes)
            img_w = W - 4*cm
            img_h = img_w * 260 / 520
            rl_img = RLImage(img_buf, width=img_w, height=img_h)
            story.append(rl_img)
            story.append(Spacer(1, 8))

    # KPI popolazione + concorrenti
    story.append(kpi_box([
        ('Pop. 3 min',f'{int(p.pop_3min or 0):,}','#3b82f6'),
        ('Pop. 5 min',f'{int(p.pop_5min or 0):,}','#8b5cf6'),
        ('Pop. 10 min',f'{int(p.pop_10min or 0):,}','#ec4899'),
        ('Concorrenti 500m',str(p.concorrenti_500m or 0),'#ef4444'),
        ('Concorrenti 1km',str(p.concorrenti_1km or 0),'#f59e0b'),
    ]))
    story.append(Spacer(1,8))

    # Score + fattibilità
    sc=int(p.score_zona or 0)
    scol_hex='#10b981' if sc>=70 else '#f59e0b' if sc>=45 else '#ef4444'
    st_sc=Table([[
        Paragraph(f'<b>Score zona: <font color="{scol_hex}">{sc}/100 - {p.score_label or ""}</font></b>',
                  st('ssc',fontSize=12,fontName='Helvetica-Bold',textColor=SCURO)),
        Paragraph(f'Fattibilita: <b><font color="{scol_hex}">{p.fattibilita}%</font></b>',
                  st('sfc',fontSize=10,textColor=GRIGIO,alignment=TA_RIGHT)),
    ]],colWidths=[10*cm,7*cm])
    st_sc.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),BG),
        ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#e2e8f0')),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(-1,-1),10)]))
    story.append(st_sc)

    # ── PAGINA DEMOGRAFICA ISTAT ──────────────────────────────────────────────
    story.append(PageBreak())
    story.append(sez('ANALISI DEMOGRAFICA — Dati ISTAT', ''))
    story.append(Spacer(1, 8))

    # Recupera dati ISTAT per la provincia
    try:
        from services.istat import PROVINCE_DATA, calcola_stima_clienti
        citta_lower = (p.citta or '').lower()
        dati_prov = None
        for cod, dati in PROVINCE_DATA.items():
            if dati.get('nome', '').lower() in citta_lower or citta_lower in dati.get('nome', '').lower():
                dati_prov = dati
                break
        if not dati_prov:
            # Fallback: usa dati medi nazionali
            dati_prov = {'nome': p.citta or 'N/D', 'eta_media': 46.0,
                         'reddito_medio': 20500, 'densita': 200}
    except Exception:
        dati_prov = {'nome': p.citta or 'N/D', 'eta_media': 46.0,
                     'reddito_medio': 20500, 'densita': 200}

    eta_media = dati_prov.get('eta_media', 46.0)
    reddito = dati_prov.get('reddito_medio', 20500)
    densita = dati_prov.get('densita', 200)
    pop_3 = int(p.pop_3min or 0)
    pop_5 = int(p.pop_5min or 0)
    pop_10 = int(p.pop_10min or 0)

    # Stime clienti giornalieri
    bacino = pop_5 if pop_5 > 0 else pop_10
    tasso_base = 0.018
    # Fattore età: ottimale 30-45 anni
    if eta_media < 35: fatt_eta = 1.10
    elif eta_media < 45: fatt_eta = 1.05
    elif eta_media < 50: fatt_eta = 0.98
    else: fatt_eta = 0.90
    # Fattore reddito
    if reddito < 17000: fatt_reddito = 1.15
    elif reddito < 22000: fatt_reddito = 1.05
    elif reddito < 27000: fatt_reddito = 0.95
    else: fatt_reddito = 0.85
    clienti_giorno_stima = int(bacino * tasso_base * fatt_eta * fatt_reddito)

    # Segmentazione demografica stimata
    seg_giovani = int(bacino * 0.22)   # 18-34 anni
    seg_adulti  = int(bacino * 0.35)   # 35-54 anni
    seg_senior  = int(bacino * 0.20)   # 55+ anni
    seg_famiglie= int(bacino * 0.23)   # nuclei familiari

    # Tabella indicatori chiave + mini infografica
    class DemoPage(Flowable):
        def __init__(self, width, height_needed):
            Flowable.__init__(self)
            self.width = width
            self.height = height_needed
        def draw(self):
            c = self.canv
            w = self.width
            # --- Riga 1: 3 card demografiche ---
            card_w = (w - 2*cm/3) / 3
            cards = [
                ('ETA MEDIA', f'{eta_media:.1f} anni',
                 '#8b5cf6', 'Fonte: ISTAT Censimento 2021'),
                ('REDDITO MEDIO', f'EUR {reddito:,}',
                 '#10b981', 'Dichiarazioni MEF 2022'),
                ('DENSITA ABITATIVA', f'{densita:,} ab/km²',
                 '#3b82f6', 'Dati provinciali ISTAT'),
            ]
            for i, (lbl, val, col, fonte) in enumerate(cards):
                cx = i * (card_w + cm/3)
                cy = self.height - 2.8*cm
                c.setFillColor(colors.HexColor('#f8fafc'))
                c.roundRect(cx, cy, card_w, 2.4*cm, 6, fill=1, stroke=0)
                c.setStrokeColor(colors.HexColor(col))
                c.setLineWidth(2)
                c.line(cx + 6, cy + 2.4*cm, cx + card_w - 6, cy + 2.4*cm)
                c.setLineWidth(1)
                c.setFont('Helvetica', 6.5)
                c.setFillColor(colors.HexColor('#64748b'))
                c.drawCentredString(cx + card_w/2, cy + 1.9*cm, lbl)
                c.setFont('Helvetica-Bold', 11)
                c.setFillColor(colors.HexColor(col))
                c.drawCentredString(cx + card_w/2, cy + 1.2*cm, val)
                c.setFont('Helvetica', 6)
                c.setFillColor(colors.HexColor('#94a3b8'))
                c.drawCentredString(cx + card_w/2, cy + 0.5*cm, fonte)

            # --- Riga 2: Bacino d'utenza + Grafico population ---
            top2 = self.height - 3.4*cm
            # Titoletto sezione
            c.setFont('Helvetica-Bold', 8)
            c.setFillColor(BSCURO)
            c.drawString(0, top2 - 0.5*cm, 'BACINO DI UTENZA per raggio')
            # Barre popolazione
            pop_items = [
                ('3 min (~400m)', pop_3),
                ('5 min (~700m)', pop_5),
                ('10 min (~1.5km)', pop_10),
            ]
            bar_colors = ['#3b82f6', '#8b5cf6', '#ec4899']
            max_pop = max(pop_10, 1)
            bar_top = top2 - 1.1*cm
            bar_h = 18
            bar_gap = 8
            bar_max_w = w * 0.55
            for i, (lbl, val) in enumerate(pop_items):
                by = bar_top - i * (bar_h + bar_gap)
                bw_actual = bar_max_w * (val / max_pop)
                # sfondo
                c.setFillColor(colors.HexColor('#e2e8f0'))
                c.roundRect(90, by, bar_max_w, bar_h, 3, fill=1, stroke=0)
                # barra
                c.setFillColor(colors.HexColor(bar_colors[i]))
                if bw_actual > 6:
                    c.roundRect(90, by, bw_actual, bar_h, 3, fill=1, stroke=0)
                # etichetta sinistra
                c.setFont('Helvetica', 7)
                c.setFillColor(colors.HexColor('#64748b'))
                c.drawRightString(86, by + 5, lbl)
                # valore
                c.setFont('Helvetica-Bold', 8)
                c.setFillColor(colors.HexColor('#0f172a'))
                c.drawString(96 + bar_max_w, by + 5, f'{val:,}')

            # --- Riga 3: Segmentazione target ---
            top3 = top2 - (bar_h + bar_gap) * 3 - 1.6*cm
            c.setFont('Helvetica-Bold', 8)
            c.setFillColor(BSCURO)
            c.drawString(0, top3, 'SEGMENTAZIONE TARGET (su pop. 5 min)')
            seg_top = top3 - 0.7*cm
            seg_items = [
                ('Giovani (18-34)', seg_giovani, '#3b82f6', '22%'),
                ('Adulti (35-54)',  seg_adulti,  '#10b981', '35%'),
                ('Senior (55+)',    seg_senior,  '#f59e0b', '20%'),
                ('Nuclei famil.',   seg_famiglie,'#8b5cf6', '23%'),
            ]
            seg_w = (w - 1*cm) / 4
            for i, (lbl, val, col, pct) in enumerate(seg_items):
                sx = i * (seg_w + cm/4 * 0.33)
                sy = seg_top - 2.2*cm
                # card
                c.setFillColor(colors.HexColor('#f8fafc'))
                c.roundRect(sx, sy, seg_w - 2, 2.0*cm, 5, fill=1, stroke=0)
                # cerchio colorato
                cr = 0.3*cm
                c.setFillColor(colors.HexColor(col))
                c.circle(sx + seg_w/2, sy + 1.55*cm, cr, fill=1, stroke=0)
                # percentuale
                c.setFont('Helvetica-Bold', 9)
                c.setFillColor(colors.HexColor(col))
                c.drawCentredString(sx + seg_w/2, sy + 1.05*cm, pct)
                # label
                c.setFont('Helvetica', 6.5)
                c.setFillColor(colors.HexColor('#64748b'))
                c.drawCentredString(sx + seg_w/2, sy + 0.6*cm, lbl)
                # valore
                c.setFont('Helvetica-Bold', 7)
                c.setFillColor(colors.HexColor('#0f172a'))
                c.drawCentredString(sx + seg_w/2, sy + 0.15*cm, f'{val:,}')

            # --- Riga 4: Stima clienti + indicatori wash ---
            top4 = seg_top - 2.6*cm
            c.setFont('Helvetica-Bold', 8)
            c.setFillColor(BSCURO)
            c.drawString(0, top4, 'POTENZIALE COMMERCIALE STIMATO')

            wash_items = [
                ('Clienti/giorno stimati', str(clienti_giorno_stima), '#10b981'),
                ('Clienti/mese (x26gg)',   str(clienti_giorno_stima * 26), '#3b82f6'),
                ('Età media bacino',       f'{eta_media:.0f} anni', '#8b5cf6'),
                ('Reddito pro-capite',     f'EUR {reddito:,}', '#f59e0b'),
                ('Densità ab./km²',        f'{densita:,}', '#ec4899'),
            ]
            wash_top = top4 - 0.7*cm
            wc_w = (w - cm * 0.5) / len(wash_items)
            for i, (lbl, val, col) in enumerate(wash_items):
                wx = i * (wc_w + cm * 0.1)
                wy = wash_top - 1.8*cm
                c.setFillColor(colors.HexColor('#f8fafc'))
                c.roundRect(wx, wy, wc_w - 2, 1.6*cm, 4, fill=1, stroke=0)
                c.setStrokeColor(colors.HexColor(col)); c.setLineWidth(1.5)
                c.line(wx + 4, wy, wx + wc_w - 6, wy)
                c.setLineWidth(1)
                c.setFont('Helvetica-Bold', 9)
                c.setFillColor(colors.HexColor(col))
                c.drawCentredString(wx + wc_w/2, wy + 0.9*cm, val)
                c.setFont('Helvetica', 6)
                c.setFillColor(colors.HexColor('#64748b'))
                # wrap label su 2 righe se troppo lungo
                words = lbl.split()
                if len(words) > 2:
                    line1 = ' '.join(words[:2])
                    line2 = ' '.join(words[2:])
                    c.drawCentredString(wx + wc_w/2, wy + 0.45*cm, line1)
                    c.drawCentredString(wx + wc_w/2, wy + 0.12*cm, line2)
                else:
                    c.drawCentredString(wx + wc_w/2, wy + 0.25*cm, lbl)

            # nota disclaimer
            c.setFont('Helvetica', 6.5)
            c.setFillColor(colors.HexColor('#94a3b8'))
            c.drawString(0, 0.1*cm,
                'Stime basate su dati ISTAT Censimento 2021, MEF 2022 e modello domanda BIOLavaTU. I valori sono indicativi.')

    story.append(DemoPage(W - 4*cm, 20.5*cm))
    story.append(Spacer(1, 10))

    story.append(Spacer(1,14))

    # ── MACCHINE ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(sez('CONFIGURAZIONE MACCHINE', '')); story.append(Spacer(1,6))
    mac_header=[['Macchina','Categoria','Modello','Qty','Prezzo','Totale']]
    mac_rows=[]
    for m in p.get_macchine():
        prezzo=float(m.get('prezzo_effettivo') or m.get('prezzo',0))
        qty=int(m.get('qty',1))
        mac_rows.append([
            m.get('nome',''), m.get('categoria',''), m.get('modello','') or '',
            f'{qty}x', f'EUR {prezzo:,.0f}', f'EUR {prezzo*qty:,.0f}'])
    capex_iva=p.capex*1.22
    mac_rows+=[
        ['','','','','Imponibile',f'EUR {p.capex:,.0f}'],
        ['','','','','IVA 22%',f'EUR {p.capex*0.22:,.0f}'],
        ['','','','','TOTALE IVA INCLUSA',f'EUR {capex_iva:,.0f}'],
    ]
    mt=Table(mac_header+mac_rows,colWidths=[5.5*cm,2.5*cm,2*cm,1.2*cm,2.8*cm,3*cm])
    mt.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
        ('BACKGROUND',(0,0),(-1,0),BSCURO),('TEXTCOLOR',(0,0),(-1,0),BIANCO),
        ('ALIGN',(3,0),(-1,-1),'RIGHT'),
        ('LINEBELOW',(0,0),(-1,-4),0.3,colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS',(0,1),(-1,-4),[BIANCO,BG]),
        ('FONTNAME',(4,-3),(-1,-3),'Helvetica-Bold'),('TEXTCOLOR',(4,-3),(-1,-3),GRIGIO),
        ('FONTNAME',(4,-2),(-1,-2),'Helvetica-Bold'),('TEXTCOLOR',(4,-2),(-1,-2),ARANCIO),
        ('FONTNAME',(4,-1),(-1,-1),'Helvetica-Bold'),('TEXTCOLOR',(4,-1),(-1,-1),BLU),
        ('FONTSIZE',(4,-1),(-1,-1),10),('LINEABOVE',(0,-1),(-1,-1),1.5,BLU),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]))
    story.append(mt); story.append(Spacer(1,14))

    # ── BUSINESS PLAN ────────────────────────────────────────────────────────
    story.append(sez(f'BUSINESS PLAN — Scenario {(p.scenario or "realistico").upper()}', ''))
    story.append(Spacer(1,6))
    story.append(kpi_box([
        ('Investimento + IVA',f'EUR {capex_iva:,.0f}','#3b82f6'),
        ('Incasso/mese',f'EUR {p.incasso_mese:,.0f}','#10b981'),
        ('Costi/mese',f'EUR {p.costi_mese:,.0f}','#ef4444'),
        ('Utile/mese',f'EUR {p.utile_mese:,.0f}',
         '#10b981' if p.utile_mese>=0 else '#ef4444'),
        ('Payback',f'{int(p.payback_mesi/12) if p.payback_mesi else "N/D"} anni','#f59e0b'),
    ]))
    story.append(Spacer(1,10))
    pess=p.utile_mese*0.60; ott=p.utile_mese*1.25
    sc3=Table([
        ['Scenario','Incasso/mese','Utile/mese','Note'],
        ['Pessimistico (x0.60)',f'EUR {p.incasso_mese*0.60:,.0f}',
         f'EUR {pess:,.0f}','Avvio lento, zona difficile'],
        ['Realistico (x1.00)',f'EUR {p.incasso_mese:,.0f}',
         f'EUR {p.utile_mese:,.0f}','Scenario base del modello'],
        ['Ottimistico (x1.25)',f'EUR {p.incasso_mese*1.25:,.0f}',
         f'EUR {ott:,.0f}','Marketing attivo, clientela fidelizzata'],
    ],colWidths=[5*cm,3.5*cm,3.5*cm,5*cm])
    sc3.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
        ('BACKGROUND',(0,0),(-1,0),BSCURO),('TEXTCOLOR',(0,0),(-1,0),BIANCO),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[BIANCO,BG]),
        ('TEXTCOLOR',(2,1),(2,1),ROSSO if pess<0 else VERDE),
        ('TEXTCOLOR',(2,2),(2,2),ROSSO if p.utile_mese<0 else VERDE),
        ('TEXTCOLOR',(2,3),(2,3),VERDE),
        ('FONTNAME',(0,2),(0,2),'Helvetica-Bold'),
        ('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),
        ('LINEBELOW',(0,0),(-1,-2),0.3,colors.HexColor('#e2e8f0'))]))
    story.append(sc3); story.append(Spacer(1,14))

    # ── ANALISI AI BP ────────────────────────────────────────────────────────
    if p.ai_zona:
        ai_text = p.ai_bp or p.ai_zona
        if ai_text:
            story.append(PageBreak())
            story.append(sez('ANALISI AI - RACCOMANDAZIONE',''))
            story.append(Spacer(1,8))
            _render_ai_text(ai_text, story, st, body, h2, BSCURO, VERDE, ROSSO, ARANCIO, Spacer, Paragraph)

    # ── CONDIZIONI DI VENDITA ─────────────────────────────────────────────
    if s and s.condizioni_vendita:
        story.append(PageBreak())
        story.append(sez('CONDIZIONI DI VENDITA', ''))
        story.append(Spacer(1,6))
        for line in s.condizioni_vendita.split('\n'):
            if line.strip():
                story.append(Paragraph(line.strip(),body))

    doc.build(story)
    main_buf.seek(0)

    # ── MERGE ALLEGATI PDF ────────────────────────────────────────────────────
    from flask import current_app
    upload_folder = current_app.config.get('UPLOAD_FOLDER', '/tmp')
    allegati = p.get_allegati()
    pdf_all = [a for a in allegati if isinstance(a,str) and a.lower().endswith('.pdf')]

    if not pdf_all:
        resp = make_response(main_buf.read())
        resp.headers['Content-Type'] = 'application/pdf'
        resp.headers['Content-Disposition'] = f'inline; filename=BIOLavaTU-{p.numero}.pdf'
        return resp

    writer = PdfWriter()
    for pg in PdfReader(main_buf).pages:
        writer.add_page(pg)
    for allegato in pdf_all:
        path = os.path.join(upload_folder, allegato)
        if os.path.exists(path):
            try:
                for pg in PdfReader(path).pages:
                    writer.add_page(pg)
            except Exception:
                pass
    out_buf = _io.BytesIO()
    writer.write(out_buf); out_buf.seek(0)
    resp = make_response(out_buf.read())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'inline; filename=BIOLavaTU-{p.numero}.pdf'
    return resp


@pratiche_bp.route('/pratiche/<int:id>/allegato', methods=['POST'])
@login_required
def aggiungi_allegato(id):
    from flask import current_app
    from werkzeug.utils import secure_filename
    import os, json as _json
    p = Pratica.query.get_or_404(id)
    f = request.files.get('allegato')
    if not f or not f.filename:
        flash('Nessun file selezionato.', 'error')
        return redirect(url_for('pratiche.dettaglio', id=id))
    ext = f.filename.rsplit('.', 1)[-1].lower()
    if ext not in {'pdf','png','jpg','jpeg','gif','webp'}:
        flash('Formato non supportato.', 'error')
        return redirect(url_for('pratiche.dettaglio', id=id))
    fn = secure_filename(f'all_{p.id}_{len(p.get_allegati())+1}_{f.filename}')
    f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fn))
    all_list = p.get_allegati(); all_list.append(fn)
    p.allegati_json = _json.dumps(all_list)
    db.session.commit()
    flash(f'Allegato aggiunto.', 'success')
    return redirect(url_for('pratiche.dettaglio', id=id))


@pratiche_bp.route('/pratiche/<int:id>/allegato/<int:idx>/elimina', methods=['POST'])
@login_required
def elimina_allegato(id, idx):
    import json as _json
    p = Pratica.query.get_or_404(id)
    all_list = p.get_allegati()
    if 0 <= idx < len(all_list):
        all_list.pop(idx)
        p.allegati_json = _json.dumps(all_list)
        db.session.commit()
        flash('Allegato eliminato.', 'success')
    return redirect(url_for('pratiche.dettaglio', id=id))
