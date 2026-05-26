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


@pratiche_bp.route('/pratiche/<int:id>/pdf')
@login_required
def genera_pdf(id):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, HRFlowable, PageBreak, KeepTogether)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus.flowables import Flowable
    import math

    p = Pratica.query.get_or_404(id)
    s = Settings.query.first()
    buf = io.BytesIO()

    W, H = A4  # 595 x 842

    # ── COLORI ────────────────────────────────────────────────────────────────
    BLU       = colors.HexColor('#2563eb')
    BLU_SCURO = colors.HexColor('#1e3a5f')
    BLU_LIGHT = colors.HexColor('#eff6ff')
    GRIGIO    = colors.HexColor('#64748b')
    GRIGIO_BG = colors.HexColor('#f8fafc')
    SCURO     = colors.HexColor('#0f172a')
    VERDE     = colors.HexColor('#10b981')
    ROSSO     = colors.HexColor('#ef4444')
    ARANCIO   = colors.HexColor('#f59e0b')
    BIANCO    = colors.white

    brand   = s.brand_name   if s else 'BIOLavaTU'
    company = s.company_name if s else 'Rotondi Group Srl'
    addr    = (s.company_addr  or '') if s else ''
    email   = (s.company_email or '') if s else ''
    web     = (s.company_web   or '') if s else ''
    tel     = (s.company_tel   or '') if s else ''

    # ── STILI ─────────────────────────────────────────────────────────────────
    def st(name, **kw):
        return ParagraphStyle(name, fontName='Helvetica', fontSize=9,
                              textColor=SCURO, leading=13, **kw)

    cover_brand  = st('cb',  fontSize=38, fontName='Helvetica-Bold', textColor=BIANCO,
                      leading=42, alignment=TA_CENTER)
    cover_sub    = st('cs',  fontSize=13, textColor=colors.HexColor('#93c5fd'),
                      alignment=TA_CENTER, leading=18)
    cover_num    = st('cn',  fontSize=22, fontName='Helvetica-Bold', textColor=BIANCO,
                      alignment=TA_CENTER, leading=28)
    cover_info   = st('ci',  fontSize=10, textColor=colors.HexColor('#bfdbfe'),
                      alignment=TA_CENTER, leading=16)
    h1_st  = st('h1', fontSize=13, fontName='Helvetica-Bold', textColor=BLU_SCURO,
                spaceBefore=16, spaceAfter=6)
    h2_st  = st('h2', fontSize=10, fontName='Helvetica-Bold', textColor=GRIGIO,
                spaceBefore=10, spaceAfter=3)
    body_st= st('body', fontSize=9, leading=14)
    muted_st=st('mu',  fontSize=8,  textColor=GRIGIO)
    kpi_val= st('kv',  fontSize=20, fontName='Helvetica-Bold', textColor=BLU,
                alignment=TA_CENTER, leading=24)
    kpi_lbl= st('kl',  fontSize=8,  textColor=GRIGIO, alignment=TA_CENTER)
    footer_st=st('ft', fontSize=7,  textColor=GRIGIO, alignment=TA_CENTER)

    # ── HEADER/FOOTER su ogni pagina ─────────────────────────────────────────
    page_num = [0]
    def on_page(canvas, doc):
        page_num[0] += 1
        if page_num[0] == 1:
            return  # copertina: niente header/footer
        canvas.saveState()
        # Header sottile
        canvas.setFillColor(BLU_SCURO)
        canvas.rect(0, H - 1.2*cm, W, 1.2*cm, fill=1, stroke=0)
        canvas.setFont('Helvetica-Bold', 9)
        canvas.setFillColor(BIANCO)
        canvas.drawString(2*cm, H - 0.85*cm, brand)
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(W - 2*cm, H - 0.85*cm, f'Preventivo {p.numero}')
        # Footer
        canvas.setFillColor(GRIGIO_BG)
        canvas.rect(0, 0, W, 0.9*cm, fill=1, stroke=0)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(GRIGIO)
        canvas.drawString(2*cm, 0.32*cm, f'{company} — {addr}')
        canvas.drawRightString(W - 2*cm, 0.32*cm, f'Pag. {page_num[0] - 1}')
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.6*cm, bottomMargin=1.4*cm,
        onPage=on_page, onLaterPages=on_page,
    )

    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # PAGINA 1 — COPERTINA
    # ══════════════════════════════════════════════════════════════════════════

    class CopertinaFlowable(Flowable):
        """Disegna la copertina intera come canvas."""
        def __init__(self):
            Flowable.__init__(self)
            self.width  = W - 4*cm
            self.height = H - 3*cm

        def draw(self):
            c = self.canv
            w, h = self.width, self.height

            # Sfondo blu scuro
            c.setFillColor(BLU_SCURO)
            c.roundRect(0, 0, w, h, 16, fill=1, stroke=0)

            # Banda superiore più scura
            c.setFillColor(colors.HexColor('#0f2340'))
            c.roundRect(0, h - 7*cm, w, 7*cm, 16, fill=1, stroke=0)
            c.rect(0, h - 7*cm + 14, w, 14, fill=1, stroke=0)  # raccordo

            # Logo testuale BIOLavaTU
            c.setFont('Helvetica-Bold', 42)
            c.setFillColor(BIANCO)
            c.drawCentredString(w/2, h - 3.2*cm, 'BIOLavaTU')

            # Sottotitolo
            c.setFont('Helvetica', 13)
            c.setFillColor(colors.HexColor('#93c5fd'))
            c.drawCentredString(w/2, h - 4.2*cm, 'LaundryPro Platform')

            # Linea separatrice
            c.setStrokeColor(colors.HexColor('#3b82f6'))
            c.setLineWidth(1.5)
            c.line(w*0.2, h - 4.8*cm, w*0.8, h - 4.8*cm)

            # Titolo documento
            c.setFont('Helvetica-Bold', 18)
            c.setFillColor(BIANCO)
            c.drawCentredString(w/2, h - 5.8*cm, 'ANALISI DI FATTIBILITÀ')
            c.setFont('Helvetica', 12)
            c.setFillColor(colors.HexColor('#93c5fd'))
            c.drawCentredString(w/2, h - 6.5*cm, 'Lavanderia Self-Service')

            # Box numero preventivo
            c.setFillColor(BLU)
            c.roundRect(w*0.25, h - 9.5*cm, w*0.5, 1.8*cm, 10, fill=1, stroke=0)
            c.setFont('Helvetica-Bold', 20)
            c.setFillColor(BIANCO)
            c.drawCentredString(w/2, h - 8.4*cm, p.numero)
            c.setFont('Helvetica', 9)
            c.setFillColor(colors.HexColor('#bfdbfe'))
            c.drawCentredString(w/2, h - 9.1*cm,
                f'Data: {p.created.strftime("%d/%m/%Y")}  |  Stato: {p.stato.upper()}')

            # Dati cliente
            cliente = p.cliente
            c.setFont('Helvetica-Bold', 11)
            c.setFillColor(BIANCO)
            nome_cl = cliente.nome_completo if cliente else '—'
            c.drawCentredString(w/2, h - 10.8*cm, nome_cl)
            c.setFont('Helvetica', 9)
            c.setFillColor(colors.HexColor('#93c5fd'))
            indirizzo = f'{p.indirizzo}, {p.citta}' if p.indirizzo else p.citta or '—'
            c.drawCentredString(w/2, h - 11.5*cm, indirizzo)

            # KPI principali (4 box in fila)
            capex_iva = p.capex * 1.22
            kpis = [
                ('INVESTIMENTO', f'€{capex_iva:,.0f}', '#3b82f6'),
                ('UTILE/MESE',
                 f'€{p.utile_mese:,.0f}',
                 '#10b981' if p.utile_mese >= 0 else '#ef4444'),
                ('PAYBACK',
                 f'{int(p.payback_mesi or 0)} mesi' if p.payback_mesi else 'N/D',
                 '#f59e0b'),
                ('FATTIBILITÀ', f'{p.fattibilita}%',
                 '#10b981' if p.fattibilita >= 70 else '#f59e0b' if p.fattibilita >= 40 else '#ef4444'),
            ]
            box_w = (w - 1.2*cm) / 4
            for i, (lbl, val, col) in enumerate(kpis):
                bx = i * box_w + (i * 0.4*cm if i > 0 else 0)
                by = h - 16*cm
                c.setFillColor(colors.HexColor('#0f2340'))
                c.roundRect(bx, by, box_w - 0.2*cm, 2.6*cm, 8, fill=1, stroke=0)
                c.setFont('Helvetica', 7)
                c.setFillColor(colors.HexColor('#93c5fd'))
                c.drawCentredString(bx + (box_w-0.2*cm)/2, by + 2.1*cm, lbl)
                c.setFont('Helvetica-Bold', 13)
                c.setFillColor(colors.HexColor(col))
                c.drawCentredString(bx + (box_w-0.2*cm)/2, by + 1.2*cm, val)

            # Score zona
            score = int(p.score_zona or 0)
            score_col = ('#10b981' if score >= 70 else
                         '#f59e0b' if score >= 45 else '#ef4444')
            c.setFont('Helvetica', 9)
            c.setFillColor(colors.HexColor('#93c5fd'))
            c.drawCentredString(w/2, h - 17.2*cm, 'SCORE ZONA')
            c.setFont('Helvetica-Bold', 32)
            c.setFillColor(colors.HexColor(score_col))
            c.drawCentredString(w/2, h - 18.5*cm, f'{score}/100')
            c.setFont('Helvetica', 10)
            c.setFillColor(BIANCO)
            c.drawCentredString(w/2, h - 19.2*cm, p.score_label or '')

            # Footer copertina
            c.setFont('Helvetica', 8)
            c.setFillColor(colors.HexColor('#64748b'))
            c.drawCentredString(w/2, 1.2*cm,
                f'{company}  ·  {web}  ·  {tel}')
            c.drawCentredString(w/2, 0.5*cm,
                'Documento riservato — uso interno')

    story.append(CopertinaFlowable())
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGINA 2+ — CONTENUTO
    # ══════════════════════════════════════════════════════════════════════════

    def sezione(titolo, icona=''):
        """Intestazione sezione con sfondo colorato."""
        data = [[Paragraph(f'<b>{icona}  {titolo}</b>',
                           st('sh', fontSize=11, fontName='Helvetica-Bold',
                              textColor=BIANCO, leading=16))]]
        t = Table(data, colWidths=[W - 4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BLU_SCURO),
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING',   (0,0), (-1,-1), 10),
            ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ]))
        return t

    def kpi_row(items):
        """Riga di KPI colorati."""
        cells = []
        for lbl, val, col in items:
            cells.append(Table([
                [Paragraph(f'<font color="{col}"><b>{val}</b></font>',
                           st('kv2', fontSize=16, fontName='Helvetica-Bold',
                              alignment=TA_CENTER, leading=20,
                              textColor=colors.HexColor(col)))],
                [Paragraph(lbl, st('kl2', fontSize=8, textColor=GRIGIO,
                                   alignment=TA_CENTER))],
            ], colWidths=[3.8*cm]))
        row_tbl = Table([cells], colWidths=[3.8*cm]*len(items))
        row_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), GRIGIO_BG),
            ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID',     (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        return row_tbl

    # ── 1. CLIENTE E SEDE ─────────────────────────────────────────────────────
    story.append(sezione('CLIENTE E SEDE', '👤'))
    story.append(Spacer(1, 6))
    cliente = p.cliente
    info_rows = [
        ['Cliente', cliente.nome_completo if cliente else '—'],
        ['Indirizzo', f'{p.indirizzo}, {p.citta}' if p.indirizzo else p.citta or '—'],
        ['Superficie', f'{p.mq or "—"} mq'],
        ['CAP / Provincia', f'{p.cap or "—"} — {p.provincia or "—"}'],
    ]
    if cliente and cliente.email:    info_rows.append(['Email',    cliente.email])
    if cliente and cliente.telefono: info_rows.append(['Telefono', cliente.telefono])
    if cliente and cliente.azienda:  info_rows.append(['Azienda',  cliente.azienda])
    info_tbl = Table(info_rows, colWidths=[3.5*cm, 13.5*cm])
    info_tbl.setStyle(TableStyle([
        ('FONTNAME',      (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('TEXTCOLOR',     (0,0), (0,-1), GRIGIO),
        ('TEXTCOLOR',     (1,0), (1,-1), SCURO),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('LINEBELOW',     (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS',(0,0), (-1,-1), [BIANCO, GRIGIO_BG]),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 14))

    # ── 2. ANALISI ZONA ───────────────────────────────────────────────────────
    story.append(sezione('ANALISI ZONA', '📍'))
    story.append(Spacer(1, 6))

    # KPI popolazione
    story.append(kpi_row([
        ('Pop. 3 min a piedi', f'{int(p.pop_3min or 0):,}', '#3b82f6'),
        ('Pop. 5 min a piedi', f'{int(p.pop_5min or 0):,}', '#8b5cf6'),
        ('Pop. 10 min a piedi', f'{int(p.pop_10min or 0):,}', '#ec4899'),
        ('Concorrenti 500m', str(p.concorrenti_500m or 0), '#ef4444'),
        ('Concorrenti 1km', str(p.concorrenti_1km or 0), '#f59e0b'),
    ]))
    story.append(Spacer(1, 8))

    # Score zona con barra
    score = int(p.score_zona or 0)
    score_col_hex = ('#10b981' if score >= 70 else
                     '#f59e0b' if score >= 45 else '#ef4444')
    score_data = [[
        Paragraph(f'<b>Score zona: <font color="{score_col_hex}">{score}/100</font></b>',
                  st('sc', fontSize=12, fontName='Helvetica-Bold', textColor=SCURO)),
        Paragraph(f'<font color="{score_col_hex}"><b>{p.score_label or ""}</b></font>',
                  st('sl', fontSize=10, textColor=colors.HexColor(score_col_hex),
                     alignment=TA_RIGHT)),
    ]]
    score_tbl = Table(score_data, colWidths=[9*cm, 8*cm])
    score_tbl.setStyle(TableStyle([
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('BACKGROUND',    (0,0), (-1,-1), GRIGIO_BG),
        ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(score_tbl)

    if p.ai_zona:
        story.append(Spacer(1, 8))
        story.append(Paragraph('Analisi AI della zona', h2_st))
        for line in p.ai_zona.split('\n'):
            if line.strip():
                clean = line.replace('#', '').replace('**', '').replace('*', '').strip()
                if clean.startswith('##') or clean.startswith('1.') or clean.startswith('2.') or clean.startswith('3.') or clean.startswith('4.'):
                    story.append(Paragraph(clean, st('ai_h', fontSize=9,
                        fontName='Helvetica-Bold', textColor=BLU_SCURO, spaceBefore=4)))
                else:
                    story.append(Paragraph(clean, body_st))
    story.append(Spacer(1, 14))

    # ── 3. CONFIGURAZIONE MACCHINE ────────────────────────────────────────────
    story.append(sezione('CONFIGURAZIONE MACCHINE', '⚙️'))
    story.append(Spacer(1, 6))

    mac_header = [['Macchina', 'Cat.', 'Modello', 'Qtà', 'Prezzo unit.', 'Totale']]
    mac_rows   = []
    for m in p.get_macchine():
        mac_rows.append([
            m.nome,
            getattr(m, 'categoria', ''),
            getattr(m, 'modello', '') or '',
            f'{m.qty}×',
            f'€{m.prezzo_effettivo:,.0f}',
            f'€{m.prezzo_effettivo * m.qty:,.0f}',
        ])
    capex_iva = p.capex * 1.22
    mac_rows += [
        ['', '', '', '', 'Imponibile', f'€{p.capex:,.0f}'],
        ['', '', '', '', 'IVA 22%',    f'€{p.capex * 0.22:,.0f}'],
        ['', '', '', '', 'TOTALE IVA INCLUSA', f'€{capex_iva:,.0f}'],
    ]
    mac_tbl = Table(mac_header + mac_rows,
                    colWidths=[5.5*cm, 2.5*cm, 2.5*cm, 1.2*cm, 2.8*cm, 2.5*cm])
    mac_tbl.setStyle(TableStyle([
        ('FONTNAME',      (0,0), (-1,0),   'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1),  9),
        ('BACKGROUND',    (0,0), (-1,0),   BLU_SCURO),
        ('TEXTCOLOR',     (0,0), (-1,0),   BIANCO),
        ('ALIGN',         (3,0), (-1,-1),  'RIGHT'),
        ('LINEBELOW',     (0,0), (-1,-4),  0.3, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS',(0,1), (-1,-4),  [BIANCO, GRIGIO_BG]),
        # Righe totali
        ('FONTNAME',      (4,-3), (-1,-3), 'Helvetica-Bold'),
        ('TEXTCOLOR',     (4,-3), (-1,-3), GRIGIO),
        ('FONTNAME',      (4,-2), (-1,-2), 'Helvetica-Bold'),
        ('TEXTCOLOR',     (4,-2), (-1,-2), colors.HexColor('#f59e0b')),
        ('FONTNAME',      (4,-1), (-1,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR',     (4,-1), (-1,-1), BLU),
        ('FONTSIZE',      (4,-1), (-1,-1), 10),
        ('LINEABOVE',     (0,-1), (-1,-1), 1.5, BLU),
        ('BOTTOMPADDING', (0,0), (-1,-1),  6),
        ('TOPPADDING',    (0,0), (-1,-1),  6),
    ]))
    story.append(mac_tbl)
    story.append(Spacer(1, 14))

    # ── 4. BUSINESS PLAN ──────────────────────────────────────────────────────
    story.append(sezione(
        f'BUSINESS PLAN — Scenario {(p.scenario or "realistico").upper()}', '📊'))
    story.append(Spacer(1, 6))

    # KPI principali
    story.append(kpi_row([
        ('Investimento + IVA', f'€{capex_iva:,.0f}', '#3b82f6'),
        ('Incasso/mese', f'€{p.incasso_mese:,.0f}', '#10b981'),
        ('Costi/mese',   f'€{p.costi_mese:,.0f}',   '#ef4444'),
        ('Utile/mese',
         f'€{p.utile_mese:,.0f}',
         '#10b981' if p.utile_mese >= 0 else '#ef4444'),
        ('Payback',
         f'{int(p.payback_mesi or 0)} mesi' if p.payback_mesi else 'N/D',
         '#f59e0b'),
    ]))
    story.append(Spacer(1, 8))

    # Tabella dettaglio BP
    bp_rows = [
        ['Incasso mensile stimato',  f'€{p.incasso_mese:,.0f}', '',
         'Costi mensili totali',     f'€{p.costi_mese:,.0f}'],
        ['Utile mensile netto',
         f'€{p.utile_mese:,.0f}', '',
         'Payback (IVA inclusa)',
         f'{int(p.payback_mesi or 0)} mesi ({round((p.payback_mesi or 0)/12,1)} anni)'],
    ]
    bp_tbl = Table(bp_rows, colWidths=[5*cm, 3.5*cm, 0.5*cm, 5*cm, 3*cm])
    bp_tbl.setStyle(TableStyle([
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('FONTNAME',      (0,0), (0,-1),  'Helvetica-Bold'),
        ('FONTNAME',      (3,0), (3,-1),  'Helvetica-Bold'),
        ('TEXTCOLOR',     (0,0), (0,-1),  GRIGIO),
        ('TEXTCOLOR',     (3,0), (3,-1),  GRIGIO),
        ('FONTNAME',      (1,0), (1,-1),  'Helvetica-Bold'),
        ('FONTNAME',      (4,0), (4,-1),  'Helvetica-Bold'),
        ('TEXTCOLOR',     (1,0), (1,0),   VERDE),
        ('TEXTCOLOR',     (4,0), (4,0),   ROSSO),
        ('TEXTCOLOR',     (1,1), (1,1),   VERDE if p.utile_mese >= 0 else ROSSO),
        ('TEXTCOLOR',     (4,1), (4,1),   ARANCIO),
        ('ROWBACKGROUNDS',(0,0), (-1,-1), [GRIGIO_BG, BIANCO]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(bp_tbl)
    story.append(Spacer(1, 14))

    # ── 5. FATTIBILITÀ ────────────────────────────────────────────────────────
    story.append(sezione('VALUTAZIONE FATTIBILITÀ', '🎯'))
    story.append(Spacer(1, 6))
    fatt = p.fattibilita
    fatt_col = ('#10b981' if fatt >= 70 else '#f59e0b' if fatt >= 40 else '#ef4444')
    fatt_label = ('Alta' if fatt >= 70 else 'Media' if fatt >= 40 else 'Scarsa')
    fatt_data = [[
        Paragraph(f'<b>Fattibilità: <font color="{fatt_col}">{fatt}% — {fatt_label}</font></b>',
                  st('fd', fontSize=11, fontName='Helvetica-Bold')),
    ]]
    fatt_tbl = Table(fatt_data, colWidths=[W - 4*cm])
    fatt_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), GRIGIO_BG),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('BOX',           (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(fatt_tbl)

    if p.note_interne:
        story.append(Spacer(1, 8))
        story.append(Paragraph('Note interne', h2_st))
        story.append(Paragraph(p.note_interne, body_st))
    story.append(Spacer(1, 14))

    # ── 6. CONDIZIONI DI VENDITA ──────────────────────────────────────────────
    if s and s.condizioni_vendita:
        story.append(PageBreak())
        story.append(sezione('CONDIZIONI DI VENDITA', '📋'))
        story.append(Spacer(1, 6))
        for line in s.condizioni_vendita.split('\n'):
            if line.strip():
                story.append(Paragraph(line.strip(), body_st))

    # ── BUILD ─────────────────────────────────────────────────────────────────
    doc.build(story)
    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = (
        f'inline; filename=BIOLavaTU-{p.numero}.pdf')
    return resp
