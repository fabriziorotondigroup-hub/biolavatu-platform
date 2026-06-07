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
        # Separatori ---
        if r.startswith('---'):
            story.append(Spacer(1, 6))
            continue
        # Titoli ## 1. SINTESI o ## TITOLO
        if r.startswith('##') or r.startswith('#'):
            titolo = r.lstrip('#').strip()
            # Determina colore per tipo sezione
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
            story.append(Paragraph(titolo, st('ai_h', fontSize=10,
                fontName='Helvetica-Bold', textColor=col, spaceBefore=4, spaceAfter=3)))
            continue
        # Testo con **grassetto**
        import re
        # Converti **testo** in <b>testo</b> per ReportLab
        r_html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', r)
        # Punti elenco - 
        if r_html.startswith('- ') or r_html.startswith('• '):
            r_html = '• ' + r_html[2:]
            story.append(Paragraph(r_html, st('ai_li', fontSize=9,
                leftIndent=10, spaceBefore=2)))
        else:
            story.append(Paragraph(r_html, body))


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
        def __init__(self): Flowable.__init__(self); self.width=W-4*cm; self.height=H-4*cm
        def draw(self):
            c=self.canv; w,h=self.width,self.height
            c.setFillColor(BSCURO); c.roundRect(0,0,w,h,16,fill=1,stroke=0)
            c.setFillColor(colors.HexColor('#0f2340'))
            c.roundRect(0,h-7*cm,w,7*cm,16,fill=1,stroke=0)
            c.rect(0,h-7*cm+14,w,14,fill=1,stroke=0)
            c.setFont('Helvetica-Bold',40); c.setFillColor(BIANCO)
            c.drawCentredString(w/2,h-3.0*cm,brand)
            c.setFont('Helvetica',12); c.setFillColor(colors.HexColor('#93c5fd'))
            c.drawCentredString(w/2,h-4.0*cm,'LaundryPro Platform  —  Analisi di Fattibilita')
            c.setStrokeColor(BLU); c.setLineWidth(1.5)
            c.line(w*0.2,h-4.6*cm,w*0.8,h-4.6*cm)
            c.setFillColor(BLU); c.roundRect(w*0.2,h-7.2*cm,w*0.6,1.6*cm,10,fill=1,stroke=0)
            c.setFont('Helvetica-Bold',18); c.setFillColor(BIANCO)
            c.drawCentredString(w/2,h-6.2*cm,p.numero)
            c.setFont('Helvetica',8); c.setFillColor(colors.HexColor('#bfdbfe'))
            c.drawCentredString(w/2,h-6.9*cm,
                f'Data: {p.created.strftime("%d/%m/%Y")}  |  Stato: {p.stato.upper()}')
            cliente=p.cliente
            c.setFont('Helvetica-Bold',12); c.setFillColor(BIANCO)
            c.drawCentredString(w/2,h-8.5*cm,
                cliente.nome_completo if cliente else 'Cliente')
            c.setFont('Helvetica',9); c.setFillColor(colors.HexColor('#93c5fd'))
            ind=f'{p.indirizzo}, {p.citta}' if p.indirizzo else p.citta or ''
            c.drawCentredString(w/2,h-9.2*cm,ind)
            capex_iva=p.capex*1.22
            kpis=[
                ('INVESTIMENTO IVA',f'EUR {capex_iva:,.0f}','#3b82f6'),
                ('INCASSO/MESE',f'EUR {p.incasso_mese:,.0f}',
                 '#10b981' if p.incasso_mese>0 else '#ef4444'),
                ('UTILE/MESE',f'EUR {p.utile_mese:,.0f}',
                 '#10b981' if p.utile_mese>=0 else '#ef4444'),
                ('PAYBACK',
                 f'{int(p.payback_mesi/12) if p.payback_mesi else "N/D"} anni','#f59e0b'),
            ]
            bw=(w-1.2*cm)/4
            for i,(lbl,val,col) in enumerate(kpis):
                bx=i*(bw+0.4*cm); by=h-13.5*cm
                c.setFillColor(colors.HexColor('#0f2340'))
                c.roundRect(bx,by,bw,2.4*cm,8,fill=1,stroke=0)
                c.setFont('Helvetica',7); c.setFillColor(colors.HexColor('#93c5fd'))
                c.drawCentredString(bx+bw/2,by+1.9*cm,lbl)
                c.setFont('Helvetica-Bold',11); c.setFillColor(colors.HexColor(col))
                c.drawCentredString(bx+bw/2,by+1.1*cm,val)
            sc=int(p.score_zona or 0)
            scol='#10b981' if sc>=70 else '#f59e0b' if sc>=45 else '#ef4444'
            c.setFont('Helvetica',9); c.setFillColor(colors.HexColor('#93c5fd'))
            c.drawCentredString(w/2,h-14.8*cm,'SCORE ZONA')
            c.setFont('Helvetica-Bold',36); c.setFillColor(colors.HexColor(scol))
            c.drawCentredString(w/2,h-16.2*cm,f'{sc}/100')
            c.setFont('Helvetica',10); c.setFillColor(BIANCO)
            c.drawCentredString(w/2,h-17.0*cm,p.score_label or '')
            c.setFont('Helvetica',8); c.setFillColor(colors.HexColor('#64748b'))
            c.drawCentredString(w/2,1.2*cm,f'{company}  {web}  {tel}')
            c.drawCentredString(w/2,0.5*cm,'Documento riservato - uso interno')

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
    story.append(kpi_box([
        ('Pop. 3 min',f'{int(p.pop_3min or 0):,}','#3b82f6'),
        ('Pop. 5 min',f'{int(p.pop_5min or 0):,}','#8b5cf6'),
        ('Pop. 10 min',f'{int(p.pop_10min or 0):,}','#ec4899'),
        ('Concorrenti 500m',str(p.concorrenti_500m or 0),'#ef4444'),
        ('Concorrenti 1km',str(p.concorrenti_1km or 0),'#f59e0b'),
    ]))
    story.append(Spacer(1,8))
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
    if p.ai_zona:
        story.append(Spacer(1,10))
        story.append(Paragraph('Analisi AI della zona', h2))
        _render_ai_text(p.ai_zona, story, st, body, h2, BSCURO, VERDE, ROSSO, ARANCIO, Spacer, Paragraph)
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
        story.append(sez('CONDIZIONI DI VENDITA','Documento'))
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