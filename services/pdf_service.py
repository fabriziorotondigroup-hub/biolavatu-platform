import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

W, H = A4
M    = 1.7 * cm
CW   = W - 2 * M

CLAUSOLE = [
    ("Oggetto e natura dell'accordo",
     "Il presente contratto disciplina la fornitura, installazione e messa in opera delle attrezzature per lavanderia self-service automatica ecocompatibile da parte di BIOLavaTU by Rotondi Group Srl («Fornitore»), senza vincoli di esclusiva territoriale, canoni d'ingresso (franchise fee), royalty o qualsiasi altra forma di compenso periodico diversa dal corrispettivo della presente fornitura."),
    ("Durata, rinnovo e recesso",
     "Durata 5 anni dal collaudo positivo, tacito rinnovo annuale salvo disdetta scritta con 90 giorni di preavviso tramite raccomandata A/R o PEC. Il Cliente può recedere anticipatamente, senza penali, decorsi 24 mesi dall'avvio, con preavviso scritto di 60 giorni."),
    ("Fornitura, installazione e collaudo",
     "Consegna e installazione entro 30 giorni lavorativi dalla conferma ordine e ricevimento acconto. Include allacciamenti idraulici ed elettrici a norma CEI/UNI, collaudo funzionale certificato, formazione del personale (minimo 4 ore)."),
    ("Garanzia legale e convenzionale",
     "Garanzia convenzionale 24 mesi su parti e manodopera. Risposta entro 4 ore dalla segnalazione; intervento in loco entro 48 ore lavorative; macchina sostitutiva entro 72 ore se necessario. Disponibilità ricambi originali garantita per almeno 10 anni dalla data di produzione."),
    ("Assistenza tecnica e manutenzione",
     "Assistenza tecnica dedicata feriali 8:30-17:00. Contratto manutenzione preventiva semestrale disponibile a condizioni agevolate. Stock ricambi critici per intervento entro 24 ore."),
    ("Obblighi del Cliente",
     "Il Cliente predispone i locali nel rispetto delle specifiche tecniche (impianti CEI 64-8, idraulici, aerazione forzata), ottiene tutte le autorizzazioni amministrative, sanitarie e urbanistiche necessarie e conduce l'attività nel rispetto delle normative vigenti in materia di igiene, sicurezza e GDPR."),
    ("Proprietà intellettuale e marchio",
     "Licenza non esclusiva e non trasferibile del marchio BIOLavaTU per segnaletica del punto vendita entro 5 km dalla sede, per la sola durata contrattuale. Vietata qualsiasi modifica del marchio senza autorizzazione scritta."),
    ("Responsabilità e limitazione di responsabilità",
     "Il Fornitore non risponde di danni da uso improprio, mancato rispetto delle istruzioni, interventi non autorizzati o forza maggiore. La responsabilità massima per danni diretti è limitata al valore del corrispettivo contrattuale."),
    ("Riservatezza e GDPR",
     "Le parti mantengono riservate tutte le informazioni tecniche, commerciali e finanziarie per l'intera durata contrattuale e per 5 anni successivi. Il trattamento dei dati personali avviene nel rispetto del Regolamento UE 2016/679 (GDPR)."),
    ("Risoluzione e clausola risolutiva espressa",
     "Costituisce causa di risoluzione immediata ex art. 1456 c.c.: inadempimento pagamenti oltre 30 giorni, uso non autorizzato del marchio, cessione senza consenso. Penale: 15% del valore residuo, fatta salva la risarcibilità del maggior danno."),
    ("Foro competente e mediazione obbligatoria",
     "Legge italiana. Tentativo obbligatorio di mediazione (D.Lgs. 28/2010) prima delle vie giudiziarie. Foro competente esclusivo: Tribunale di Roma, con espressa rinuncia a qualsiasi altro foro."),
]


def _st(name, **kw):
    d = dict(fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#0F172A'), leading=14)
    d.update(kw)
    return ParagraphStyle(name, **d)


def _hdr(left, right, bg):
    t = Table([[
        Paragraph(left, _st('hl', fontName='Helvetica-Bold', fontSize=10,
                             textColor=colors.white, leading=13)),
        Paragraph(right, _st('hr', fontName='Helvetica', fontSize=7.5,
                              textColor=colors.HexColor('#93C5FD'), alignment=TA_RIGHT)),
    ]], colWidths=[CW * 0.72, CW * 0.28])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('TOPPADDING', (0, 0), (-1, -1), 11), ('BOTTOMPADDING', (0, 0), (-1, -1), 11),
        ('LEFTPADDING', (0, 0), (-1, -1), 14), ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    return t


def _secbar(text, bg):
    t = Table([[Paragraph(text, _st('sb', fontName='Helvetica-Bold', fontSize=8.5,
                                     textColor=colors.white, letterSpacing=0.8))]],
              colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    return t


def _kpi(items):
    n = len(items)
    cw = CW / n
    vals = [Paragraph(str(v), _st('kv', fontName='Helvetica-Bold', fontSize=13,
                                    textColor=colors.HexColor(c), alignment=TA_CENTER, leading=16))
            for _, v, c in items]
    lbls = [Paragraph(l, _st('kl', fontName='Helvetica', fontSize=7,
                               textColor=colors.HexColor('#94A3B8'), alignment=TA_CENTER))
            for l, _, _ in items]
    t = Table([vals, lbls], colWidths=[cw] * n)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#BFDBFE')),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#DBEAFE')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    return t


def _aibox(label, text, bg_hex, border_hex):
    inner = Table([[
        Paragraph(f'🤖  {label}', _st('ail', fontName='Helvetica-Bold', fontSize=7.5,
                                       textColor=colors.HexColor(border_hex), letterSpacing=0.8)),
        Paragraph(text or '—', _st('aib', fontSize=8, leading=12.5, alignment=TA_JUSTIFY)),
    ]], colWidths=[CW * 0.22, CW * 0.74])
    inner.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('TOPPADDING', (0, 0), (-1, -1), 3),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    box = Table([[inner]], colWidths=[CW])
    box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg_hex)),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(border_hex)),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    return box


def build_pdf(pratica, settings):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=M, rightMargin=M,
                            topMargin=0.9 * cm, bottomMargin=1.4 * cm)

    s      = settings
    p      = pratica
    c      = pratica.cliente
    BLU    = colors.HexColor(s.color_primary if s else '#1B4F72')
    DARK   = colors.HexColor(s.color_dark if s else '#0D2B3E')
    ROSSO  = colors.HexColor(s.color_accent if s else '#C15E59')
    TEAL   = colors.HexColor('#0E7490')
    GREEN  = colors.HexColor('#059669')
    GOLD   = colors.HexColor('#D97706')
    TODAY  = __import__('datetime').date.today().strftime('%d %B %Y')
    story  = []
    sp     = lambda n=8: Spacer(1, n)

    # ── COPERTINA ─────────────────────────────────────────────────────────────
    cov = Table([[
        Paragraph(
            f"<font size='9' color='#F59E0B'><b>LAVANDERIA AUTOMATICA ECOCOMPATIBILE</b></font>",
            _st('ce', alignment=TA_CENTER, letterSpacing=2)),
    ], [
        Paragraph(s.brand_name if s else 'BIOLavaTU',
                  _st('ct', fontName='Helvetica-Bold', fontSize=40,
                      textColor=colors.white, alignment=TA_CENTER, leading=48)),
    ], [
        Paragraph('by Rotondi Group Srl',
                  _st('cs', textColor=colors.HexColor('#93C5FD'),
                      alignment=TA_CENTER, fontSize=12)),
    ], [
        sp(6),
    ], [
        Table([['']], colWidths=[CW * 0.6],
              style=TableStyle([('BACKGROUND', (0, 0), (-1, -1), ROSSO),
                                 ('TOPPADDING', (0, 0), (-1, -1), 2),
                                 ('BOTTOMPADDING', (0, 0), (-1, -1), 2)])),
    ], [
        sp(14),
    ], [
        Paragraph('STUDIO DI FATTIBILITÀ · PREVENTIVO · CONTRATTO DI FORNITURA',
                  _st('doc', fontName='Helvetica-Bold', fontSize=9,
                      textColor=colors.white, alignment=TA_CENTER, letterSpacing=1)),
    ]], colWidths=[CW])
    cov.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    cov_wrap = Table([[cov]], colWidths=[CW])
    cov_wrap.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK),
        ('TOPPADDING', (0, 0), (-1, -1), 44), ('BOTTOMPADDING', (0, 0), (-1, -1), 36),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
    ]))
    story.append(cov_wrap)
    story.append(sp(14))

    # Score badge
    sc = p.score_zona or 0
    sc_c = '#059669' if sc >= 8 else ('#D97706' if sc >= 6 else '#EF4444')
    sc_t = p.score_label or ('OTTIMA' if sc >= 8 else 'BUONA' if sc >= 6 else 'DIFFICILE')
    badge = Table([[Paragraph(
        f'SCORE LOCATION  {sc}/10  —  {sc_t}',
        _st('sc', fontName='Helvetica-Bold', fontSize=9,
            textColor=colors.HexColor(sc_c), alignment=TA_CENTER)
    )]], colWidths=[CW * 0.6])
    badge.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(sc_c + '18')),
        ('BOX', (0, 0), (-1, -1), 1.2, colors.HexColor(sc_c)),
        ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    badge_wrap = Table([[badge]], colWidths=[CW])
    badge_wrap.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    story.append(badge_wrap)
    story.append(sp(14))

    # Scheda copertina
    cov_info = Table([
        [Paragraph('<b>Committente:</b>', _st('ci', fontName='Helvetica-Bold', fontSize=8.5)),
         c.nome if c else '—',
         Paragraph('<b>Sede proposta:</b>', _st('ci2', fontName='Helvetica-Bold', fontSize=8.5)),
         (p.indirizzo or '') + ', ' + (p.citta or '')],
        [Paragraph('<b>Documento N°:</b>', _st('ci3', fontName='Helvetica-Bold', fontSize=8.5)),
         p.numero,
         Paragraph('<b>Data:</b>', _st('ci4', fontName='Helvetica-Bold', fontSize=8.5)),
         TODAY],
        [Paragraph('<b>Investimento:</b>', _st('ci5', fontName='Helvetica-Bold', fontSize=8.5)),
         f'€ {int(p.capex or 0):,}'.replace(',', '.'),
         Paragraph('<b>Payback:</b>', _st('ci6', fontName='Helvetica-Bold', fontSize=8.5)),
         f'{p.payback_mesi:.1f} mesi' if p.payback_mesi and p.payback_mesi < 999 else 'N/D'],
    ], colWidths=[CW * 0.20, CW * 0.30, CW * 0.20, CW * 0.30])
    cov_info.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#EFF6FF'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#BFDBFE')),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#DBEAFE')),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    story.append(cov_info)
    story.append(sp(14))
    story.append(Table([[
        Paragraph(f'{s.brand_name if s else "BIOLavaTU"}  ·  {s.company_addr if s else ""}',
                  _st('cf', fontName='Helvetica-Bold', fontSize=8.5,
                      textColor=colors.white, alignment=TA_CENTER)),
        Paragraph(f'{s.company_web if s else ""}  ·  IPSO · WASCOMAT · MSGROUP',
                  _st('cf2', fontSize=8, textColor=colors.HexColor('#FCA5A5'),
                      alignment=TA_CENTER)),
    ]], colWidths=[CW * 0.56, CW * 0.44],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DARK),
            ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 16), ('RIGHTPADDING', (0, 0), (-1, -1), 16),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])))

    # ── PAGINA 2: ZONA + PARTI ────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(_hdr('📍  CAP. 1 — ANALISI ZONA E GEOLOCALIZZAZIONE',
                       f'N° {p.numero}  ·  {TODAY}', TEAL))
    story.append(sp(10))

    # Parti contraenti
    story.append(_secbar('PARTI CONTRAENTI', BLU))
    story.append(sp(8))

    def _parte(titolo, nome, dettagli, bg_hex, border_hex):
        rows = [
            [Paragraph(titolo, _st('pt', fontName='Helvetica-Bold', fontSize=7.5,
                                    textColor=colors.HexColor(border_hex), letterSpacing=1))],
            [Paragraph(f'<b>{nome}</b>', _st('pn', fontName='Helvetica-Bold', fontSize=12,
                                              textColor=colors.HexColor('#0F172A'), leading=15))],
            [Paragraph(dettagli, _st('pd', fontSize=8, textColor=colors.HexColor('#64748B'),
                                      leading=12))],
        ]
        inner = Table(rows, colWidths=[CW * 0.48])
        inner.setStyle(TableStyle([('TOPPADDING', (0, 0), (-1, -1), 2),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
        outer = Table([[inner]], colWidths=[CW * 0.50])
        outer.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg_hex)),
            ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor(border_hex)),
            ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ]))
        return outer

    left_p = _parte('IL FORNITORE',
                    s.brand_name if s else 'BIOLavaTU by Rotondi Group Srl',
                    f'{s.company_addr if s else ""}\n{s.company_piva if s else ""}\n{s.company_email if s else ""}',
                    '#EFF6FF', '#0E7490')
    right_p = _parte('IL CLIENTE',
                     c.nome if c else '—',
                     f'C.F.: {c.piva or "—"}\n{c.email or ""}  ·  {c.telefono or ""}\nSede: {p.indirizzo or ""}, {p.citta or ""}',
                     '#F0FDF4', '#059669')
    parti_t = Table([[left_p, right_p]], colWidths=[CW * 0.50, CW * 0.50])
    parti_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (1, 0), (1, 0), 8),
    ]))
    story.append(parti_t)
    story.append(sp(12))

    # KPI Zona
    story.append(_secbar('DATI GEOLOCALIZZAZIONE — ANALISI ZONA REALE', TEAL))
    story.append(sp(6))
    story.append(_kpi([
        ('Pop. 3 min a piedi', f'~{int(p.pop_3min or 0):,}'.replace(',', '.'), '#059669'),
        ('Pop. 5 min a piedi', f'~{int(p.pop_5min or 0):,}'.replace(',', '.'), '#10B981'),
        ('Concorrenti 600m',   '✓ Nessuno' if p.concorrenti == 0 else str(p.concorrenti),
         '#059669' if p.concorrenti == 0 else '#D97706'),
        ('Tipo edilizio',      f'{p.apt_ratio or 70}% cond.', '#0E7490'),
        ('Servizi 400m',       str(p.servizi_400m or 0), '#7C3AED'),
        ('Score Location',     f'{p.score_zona or 0}/10', sc_c),
    ]))
    story.append(sp(8))
    if p.ai_zona:
        story.append(_aibox('ANALISI AI ZONA', p.ai_zona, '#F0FDFA', '#0E7490'))
    story.append(sp(10))

    # Concorrenti trovati
    competitors = p.get_competitors()
    if competitors:
        story.append(_secbar(f'CONCORRENTI TROVATI ENTRO 600m — {len(competitors)} rilevati', colors.HexColor('#7C3AED')))
        story.append(sp(6))
        rows_c = [[Paragraph(h, _st('th', fontName='Helvetica-Bold', fontSize=8, textColor=colors.white))
                   for h in ['Nome', 'Indirizzo', 'Distanza', 'Rating']]]
        for i, comp in enumerate(competitors):
            rows_c.append([
                Paragraph(comp.get('name', '—'), _st('td', fontSize=8)),
                Paragraph(comp.get('address', '—'), _st('td2', fontSize=7.5,
                                                          textColor=colors.HexColor('#64748B'))),
                Paragraph(f"{comp.get('dist_m', 0)}m (~{comp.get('dist_m', 0)//80} min)",
                          _st('td3', fontSize=8, alignment=TA_CENTER)),
                Paragraph(str(comp.get('rating', '—')), _st('td4', fontSize=8, alignment=TA_CENTER)),
            ])
        ct = Table(rows_c, colWidths=[CW * 0.35, CW * 0.35, CW * 0.18, CW * 0.12])
        ct.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7C3AED')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FAF5FF'), colors.white]),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#E2E8F0')),
            ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#64748B')),
        ]))
        story.append(ct)

    # ── PAGINA 3: MACCHINE + BUSINESS PLAN ───────────────────────────────────
    story.append(PageBreak())
    story.append(_hdr('💰  CAP. 2 — CONFIGURAZIONE MACCHINE E BUSINESS PLAN',
                       f'N° {p.numero}  ·  {TODAY}', GREEN))
    story.append(sp(10))

    # Macchine
    story.append(_secbar('CONFIGURAZIONE MACCHINE PROPOSTA', BLU))
    story.append(sp(6))
    macchine = [m for m in p.get_macchine() if m.get('qty', 0) > 0]
    rows_m = [[Paragraph(h, _st('mh', fontName='Helvetica-Bold', fontSize=8, textColor=colors.white))
               for h in ['Macchina / Prodotto', 'Modello', 'Qty', 'Prezzo unitario', 'Totale']]]
    for i, m in enumerate(macchine):
        rows_m.append([
            Paragraph(m.get('nome', ''), _st('mn', fontSize=8, fontName='Helvetica-Bold')),
            Paragraph(m.get('sub', m.get('modello', '')),
                      _st('ms', fontSize=7.5, textColor=colors.HexColor('#64748B'))),
            Paragraph(str(m.get('qty', 0)),
                      _st('mq', fontSize=9, fontName='Helvetica-Bold',
                          textColor=colors.HexColor('#0E7490'), alignment=TA_CENTER)),
            Paragraph(f"€ {int(m.get('prezzo', 0)):,}".replace(',', '.'),
                      _st('mp', fontSize=8, alignment=TA_RIGHT)),
            Paragraph(f"<b>€ {int(m.get('prezzo', 0) * m.get('qty', 0)):,}</b>".replace(',', '.'),
                      _st('mt', fontName='Helvetica-Bold', fontSize=8.5,
                          textColor=colors.HexColor('#1B4F72'))),
        ])
    rows_m.append([
        Paragraph('<b>TOTALE INVESTIMENTO (CAPEX)</b>',
                  _st('tt', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
        '', '', '',
        Paragraph(f"<b>€ {int(p.capex or 0):,}</b>".replace(',', '.'),
                  _st('tv', fontName='Helvetica-Bold', fontSize=12,
                      textColor=colors.white, alignment=TA_RIGHT)),
    ])
    mac_t = Table(rows_m, colWidths=[CW * 0.34, CW * 0.20, CW * 0.08, CW * 0.19, CW * 0.19])
    mac_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLU),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.HexColor('#EFF6FF'), colors.white]),
        ('BACKGROUND', (0, -1), (-1, -1), DARK),
        ('SPAN', (0, -1), (3, -1)),
        ('ALIGN', (2, 0), (4, -1), 'CENTER'), ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -2), 0.3, colors.HexColor('#E2E8F0')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#64748B')),
    ]))
    story.append(mac_t)
    story.append(sp(10))

    # KPI Economici
    story.append(_secbar('PROIEZIONE ECONOMICA MENSILE', GREEN))
    story.append(sp(6))
    story.append(_kpi([
        ('Investimento CAPEX',  f"€ {int(p.capex or 0):,}".replace(',', '.'), '#1B4F72'),
        ('Incasso/mese',        f"€ {int(p.incasso_mese or 0):,}".replace(',', '.'), '#059669'),
        ('Costi fissi/mese',    f"€ {int(p.costi_mese or 0):,}".replace(',', '.'), '#C15E59'),
        ('Utile netto/mese',    f"€ {int(p.utile_mese or 0):,}".replace(',', '.'),
         '#059669' if (p.utile_mese or 0) > 0 else '#EF4444'),
        ('Payback',             f'{p.payback_mesi:.1f} mesi' if p.payback_mesi and p.payback_mesi < 999 else 'N/D',
         '#D97706'),
        ('Break-even',          f'Mese {int(p.payback_mesi)+1}' if p.payback_mesi and p.payback_mesi < 999 else 'N/D',
         '#D97706'),
    ]))
    story.append(sp(8))
    if p.ai_bp:
        story.append(_aibox('BUSINESS PLAN', p.ai_bp, '#F0FDF4', '#059669'))
    story.append(sp(8))
    if p.ai_risk:
        story.append(_aibox('ANALISI RISCHI', p.ai_risk, '#FFFBEB', '#D97706'))

    # ── PAGINA 4: CONTRATTO ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(_hdr('📋  CAP. 3 — CONTRATTO DI FORNITURA E CONDIZIONI LEGALI',
                       f'N° {p.numero}  ·  {TODAY}', colors.HexColor(s.color_accent if s else '#C15E59')))
    story.append(sp(10))
    story.append(_secbar(f'ARTICOLI CONTRATTUALI — {len(CLAUSOLE)} CLAUSOLE BLINDATE',
                         colors.HexColor(s.color_accent if s else '#C15E59')))
    story.append(sp(8))

    cl_st  = _st('cl', fontName='Helvetica-Bold', fontSize=8.5,
                  textColor=colors.HexColor('#1B4F72'), spaceBefore=6, spaceAfter=2)
    cl_bod = _st('cb', fontSize=7.5, leading=11.5, alignment=TA_JUSTIFY, spaceAfter=4)

    left_cl, right_cl = [], []
    for i, (title, text) in enumerate(CLAUSOLE):
        blk = [Paragraph(f'Art. {i+1} — {title}', cl_st), Paragraph(text, cl_bod)]
        (left_cl if i < 6 else right_cl).extend(blk)

    def _col(items, w):
        t = Table([[item] for item in items], colWidths=[w])
        t.setStyle(TableStyle([('TOPPADDING', (0, 0), (-1, -1), 2),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
        return t

    cl_t = Table([[_col(left_cl, CW * 0.475), _col(right_cl, CW * 0.475)]],
                  colWidths=[CW * 0.50, CW * 0.50])
    cl_t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('LEFTPADDING', (1, 0), (1, 0), 12)]))
    story.append(cl_t)
    story.append(sp(8))

    if p.ai_clausole:
        story.append(_secbar('CLAUSOLE PERSONALIZZATE — Redatte da Claude AI su questo contratto',
                              colors.HexColor('#064E3B')))
        story.append(sp(6))
        story.append(_aibox('CLAUSOLE AI', p.ai_clausole, '#F0FDF4', '#059669'))

    story.append(sp(12))

    # Firme
    story.append(HRFlowable(width=CW, thickness=2, color=DARK))
    story.append(sp(10))
    story.append(_secbar('SOTTOSCRIZIONE', BLU))
    story.append(sp(10))

    def _firma(titolo, nome):
        rows = [
            [Paragraph(titolo, _st('fl', fontName='Helvetica-Bold', fontSize=7.5,
                                    textColor=colors.HexColor('#64748B')))],
            [Paragraph(f'<b>{nome}</b>', _st('fn', fontName='Helvetica-Bold', fontSize=11,
                                              textColor=colors.HexColor('#0F172A')))],
            [Spacer(1, 32)],
            [HRFlowable(width=CW * 0.38, thickness=0.7, color=colors.HexColor('#94A3B8'))],
            [Paragraph('Firma e timbro', _st('fsm', fontSize=8, alignment=TA_CENTER,
                                              textColor=colors.HexColor('#94A3B8')))],
            [Spacer(1, 6)],
            [HRFlowable(width=CW * 0.38, thickness=0.7, color=colors.HexColor('#94A3B8'))],
            [Paragraph('Data: ___________________________',
                       _st('fd', fontSize=8.5, textColor=colors.HexColor('#94A3B8')))],
            [Spacer(1, 5)],
            [HRFlowable(width=CW * 0.38, thickness=0.7, color=colors.HexColor('#94A3B8'))],
            [Paragraph('Luogo: __________________________',
                       _st('fl2', fontSize=8.5, textColor=colors.HexColor('#94A3B8')))],
        ]
        t = Table(rows, colWidths=[CW * 0.44])
        t.setStyle(TableStyle([('TOPPADDING', (0, 0), (-1, -1), 2),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
        return t

    firme_t = Table([[
        _firma('IL FORNITORE', s.brand_name if s else 'BIOLavaTU by Rotondi Group Srl'),
        _firma('IL CLIENTE', c.nome if c else '—'),
    ]], colWidths=[CW * 0.50, CW * 0.50])
    firme_t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                  ('TOPPADDING', (0, 0), (-1, -1), 4),
                                  ('LEFTPADDING', (1, 0), (1, 0), 16)]))
    story.append(firme_t)
    story.append(sp(14))

    # Doppia firma clausole vessatorie
    vest_box = Table([[Paragraph(
        '<b>⚠️ DOPPIA SOTTOSCRIZIONE — Art. 1341-1342 c.c.</b>',
        _st('dft', fontName='Helvetica-Bold', fontSize=8.5,
            textColor=colors.HexColor('#D97706')))],
        [Paragraph(
            'Ai sensi degli artt. 1341 e 1342 del Codice Civile, il Cliente dichiara di aver letto '
            'e di approvare specificamente le seguenti clausole: Art. 8 (Limitazione responsabilità), '
            'Art. 10 (Risoluzione e clausola risolutiva espressa), Art. 11 (Foro competente).',
            _st('dfb', fontSize=8, leading=12, textColor=colors.HexColor('#374151')))],
        [sp(14)],
        [Table([[
            Table([[HRFlowable(width=CW * 0.35, thickness=0.7, color=colors.HexColor('#D97706')),
                    Spacer(1, 5),
                    Paragraph('Firma del Cliente per approvazione specifica clausole',
                               _st('dfs', fontSize=7.5, textColor=colors.HexColor('#D97706'),
                                    alignment=TA_CENTER))]],
                  colWidths=[CW * 0.46]),
            Table([[HRFlowable(width=CW * 0.35, thickness=0.7, color=colors.HexColor('#D97706')),
                    Spacer(1, 5),
                    Paragraph('Data e luogo',
                               _st('dfs2', fontSize=7.5, textColor=colors.HexColor('#D97706'),
                                    alignment=TA_CENTER))]],
                  colWidths=[CW * 0.46]),
        ]], colWidths=[CW * 0.50, CW * 0.50])]
    ], colWidths=[CW])
    vest_wrap = Table([[vest_box]], colWidths=[CW])
    vest_wrap.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFBEB')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#FCD34D')),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    story.append(vest_wrap)
    story.append(sp(12))

    # Footer
    story.append(Table([[Paragraph(
        f'N° {p.numero}  ·  {TODAY}  ·  {s.brand_name if s else "BIOLavaTU"}  ·  '
        f'{s.company_web if s else "garanzierotondi.it"}  ·  '
        f'Documento generato da LaundryPro AI Platform  ·  '
        f'Contiene {len(CLAUSOLE)} articoli standard + clausole AI personalizzate  ·  '
        f'Doppia sottoscrizione richiesta ex artt. 1341-1342 c.c.',
        _st('ft', fontSize=6.5, textColor=colors.HexColor('#94A3B8'), alignment=TA_CENTER),
    )]], colWidths=[CW],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DARK),
            ('TOPPADDING', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ])))

    doc.build(story)
    buf.seek(0)
    return buf
