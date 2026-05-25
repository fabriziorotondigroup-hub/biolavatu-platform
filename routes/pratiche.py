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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT

    p = Pratica.query.get_or_404(id)
    s = Settings.query.first()
    buf = io.BytesIO()

    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    # Stili
    styles = getSampleStyleSheet()
    blu = colors.HexColor('#2563eb')
    grigio = colors.HexColor('#64748b')
    scuro = colors.HexColor('#0f172a')

    def st(name, **kw):
        base = styles['Normal']
        return ParagraphStyle(name, parent=base, **kw)

    title_st = st('title', fontSize=22, fontName='Helvetica-Bold', textColor=blu, spaceAfter=4)
    h1_st = st('h1', fontSize=13, fontName='Helvetica-Bold', textColor=scuro, spaceBefore=14, spaceAfter=4)
    h2_st = st('h2', fontSize=10, fontName='Helvetica-Bold', textColor=grigio, spaceBefore=8, spaceAfter=2)
    body_st = st('body', fontSize=9, leading=14, textColor=scuro)
    muted_st = st('muted', fontSize=8, textColor=grigio)
    right_st = st('right', fontSize=9, alignment=TA_RIGHT, textColor=scuro)
    big_st = st('big', fontSize=16, fontName='Helvetica-Bold', textColor=blu, alignment=TA_CENTER)

    story = []
    brand = s.brand_name if s else 'BIOLavaTU'
    company = s.company_name if s else 'Rotondi Group Srl'

    # Header
    header_data = [[
        Paragraph(f'<b>{brand}</b>', title_st),
        Paragraph(f'{company}<br/>{s.company_addr if s and s.company_addr else ""}<br/>{s.company_email if s and s.company_email else ""}', muted_st)
    ]]
    header_tbl = Table(header_data, colWidths=[10*cm, 7*cm])
    header_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_tbl)
    story.append(HRFlowable(width='100%', thickness=1, color=blu, spaceAfter=12))

    # Numero e data
    story.append(Paragraph(f'Preventivo {p.numero}', h1_st))
    story.append(Paragraph(
        f'Data: {p.created.strftime("%d/%m/%Y")} &nbsp;|&nbsp; Stato: {p.stato.upper()} &nbsp;|&nbsp; Fattibilità: {p.fattibilita}%',
        muted_st))
    story.append(Spacer(1, 12))

    # Cliente e sede
    cliente = p.cliente
    story.append(Paragraph('Cliente e sede', h1_st))
    info_data = [
        ['Cliente', cliente.nome_completo if cliente else '—'],
        ['Indirizzo sede', f'{p.indirizzo}, {p.citta}' if p.indirizzo else '—'],
        ['Superficie', f'{p.mq or "—"} mq'],
    ]
    if cliente and cliente.email:
        info_data.append(['Email', cliente.email])
    if cliente and cliente.telefono:
        info_data.append(['Telefono', cliente.telefono])
    info_tbl = Table(info_data, colWidths=[4*cm, 13*cm])
    info_tbl.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), grigio),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 14))

    # Analisi zona
    story.append(Paragraph('Analisi zona', h1_st))
    zona_data = [
        ['Pop. 3 min', f'{int(p.pop_3min or 0):,}', 'Pop. 5 min', f'{int(p.pop_5min or 0):,}', 'Pop. 10 min', f'{int(p.pop_10min or 0):,}'],
        ['Concorrenti 500m', str(p.concorrenti_500m or 0), 'Concorrenti 1km', str(p.concorrenti_1km or 0), 'Score zona', f'{int(p.score_zona or 0)}/100'],
    ]
    zona_tbl = Table(zona_data, colWidths=[3.5*cm, 2.5*cm, 3.5*cm, 2.5*cm, 3.5*cm, 2.5*cm])
    zona_tbl.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), grigio),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica-Bold'),
        ('FONTNAME', (3,0), (3,-1), 'Helvetica-Bold'),
        ('FONTNAME', (5,0), (5,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1,0), (1,-1), scuro),
        ('TEXTCOLOR', (3,0), (3,-1), scuro),
        ('TEXTCOLOR', (5,0), (5,-1), scuro),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
    ]))
    story.append(zona_tbl)

    if p.ai_zona:
        story.append(Spacer(1, 8))
        story.append(Paragraph('Analisi AI della zona', h2_st))
        ai_text = p.ai_zona.replace('\n', '<br/>')
        story.append(Paragraph(ai_text, body_st))
    story.append(Spacer(1, 14))

    # Macchine
    story.append(Paragraph('Configurazione macchine', h1_st))
    mac_header = [['Macchina', 'Qtà', 'Prezzo unit.', 'Totale']]
    mac_rows = []
    for m in p.get_macchine():
        mac_rows.append([
            m.nome,
            f'{m.qty}x',
            f'€{m.prezzo_effettivo:,.0f}',
            f'€{m.prezzo_effettivo * m.qty:,.0f}'
        ])
    capex_iva = p.capex * 1.22
    mac_rows.append(['', '', 'Imponibile', f'€{p.capex:,.0f}'])
    mac_rows.append(['', '', 'IVA 22%', f'€{p.capex * 0.22:,.0f}'])
    mac_rows.append(['', '', 'TOTALE IVA INCLUSA', f'€{capex_iva:,.0f}'])
    mac_tbl = Table(mac_header + mac_rows, colWidths=[9*cm, 2*cm, 3.5*cm, 3*cm])
    mac_tbl.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('LINEBELOW', (0,0), (-1,-2), 0.3, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (2,-1), (-1,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (2,-1), (-1,-1), blu),
        ('FONTSIZE', (2,-1), (-1,-1), 10),
        ('LINEABOVE', (0,-1), (-1,-1), 1.5, blu),
        ('FONTNAME', (2,-2), (-1,-2), 'Helvetica-Bold'),
        ('TEXTCOLOR', (2,-2), (-1,-2), colors.HexColor('#f59e0b')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(mac_tbl)
    story.append(Spacer(1, 14))

    # Business Plan
    story.append(Paragraph(f'Business Plan — Scenario {(p.scenario or "realistico").title()}', h1_st))
    bp_data = [
        ['Incasso mensile', f'€{p.incasso_mese:,.0f}', 'Costi mensili', f'€{p.costi_mese:,.0f}'],
        ['Utile mensile', f'€{p.utile_mese:,.0f}', 'Payback', f'{int(p.payback_mesi or 0)} mesi ({round(p.payback_mesi/12, 1) if p.payback_mesi else "N/D"} anni)'],
    ]
    bp_tbl = Table(bp_data, colWidths=[4*cm, 4.5*cm, 4*cm, 5*cm])
    bp_tbl.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), grigio),
        ('TEXTCOLOR', (2,0), (2,-1), grigio),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica-Bold'),
        ('FONTNAME', (3,0), (3,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1,0), (1,0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (1,1), (1,1), colors.HexColor('#10b981') if p.utile_mese >= 0 else colors.HexColor('#ef4444')),
        ('TEXTCOLOR', (3,1), (3,1), colors.HexColor('#f59e0b')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('LINEBELOW', (0,0), (-1,-2), 0.3, colors.HexColor('#e2e8f0')),
    ]))
    story.append(bp_tbl)

    # Condizioni
    if s and s.condizioni_vendita:
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width='100%', thickness=0.5, color=grigio))
        story.append(Spacer(1, 8))
        story.append(Paragraph('Condizioni di vendita', h2_st))
        story.append(Paragraph(s.condizioni_vendita.replace('\n', '<br/>'), muted_st))

    doc.build(story)
    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'inline; filename=preventivo-{p.numero}.pdf'
    return resp
