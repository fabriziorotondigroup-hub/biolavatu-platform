"""
services/pdf_campo.py — BIOLavaTU LaundryPro
PDF da campo versione investitore — 5 pagine A4 ottimizzate per stampa.
"""
import io, os, datetime, random, string
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)

W, H = A4
M    = 1.6 * cm
CW   = W - 2 * M   # ~17.9 cm

# Colori
C_NAVY  = colors.HexColor('#0B1F3A')
C_BLU   = colors.HexColor('#1B4F72')
C_TEAL  = colors.HexColor('#0E7490')
C_GREEN = colors.HexColor('#059669')
C_GOLD  = colors.HexColor('#D97706')
C_RED   = colors.HexColor('#DC2626')
C_GRAY  = colors.HexColor('#64748B')
C_LGRAY = colors.HexColor('#CBD5E1')
C_WHITE = colors.white
C_LIGHT = colors.HexColor('#F0F9FF')
C_YELL  = colors.HexColor('#FFFBEB')
C_ORAN  = colors.HexColor('#FFF7ED')

def uid():
    return ''.join(random.choices(string.ascii_lowercase, k=5))

def st(name, **kw):
    base = dict(fontName='Helvetica', fontSize=8.5, leading=12,
                textColor=colors.HexColor('#0F172A'))
    base.update(kw)
    return ParagraphStyle(f'{name}_{uid()}', **base)

def sp(n=5):
    return Spacer(1, n)

def hdr_bar(testo, bg, txt_color=colors.white, sz=11):
    t = Table([[Paragraph(testo, st('h', fontName='Helvetica-Bold',
                fontSize=sz, textColor=txt_color, leading=sz+3,
                letterSpacing=0.4))]],
              colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('TOPPADDING',    (0,0),(-1,-1), 9),
        ('BOTTOMPADDING', (0,0),(-1,-1), 9),
        ('LEFTPADDING',   (0,0),(-1,-1), 12),
        ('RIGHTPADDING',  (0,0),(-1,-1), 12),
        ('ROUNDEDCORNERS',[6,6,6,6]),
    ]))
    return t

def sub_bar(testo, bg):
    t = Table([[Paragraph(testo, st('sh', fontName='Helvetica-Bold',
                fontSize=8, textColor=colors.white, leading=11))]],
              colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
    ]))
    return t

def riga(cols_data, col_widths, bg=C_WHITE, border=True, bold_first=True):
    """cols_data = lista di (testo, extra_style_kwargs)"""
    cells = []
    for i, (txt, kw) in enumerate(cols_data):
        fn = 'Helvetica-Bold' if (bold_first and i == 0) else 'Helvetica'
        tc = C_NAVY if i == 0 else C_GRAY
        cells.append(Paragraph(txt, st('r', fontName=fn, fontSize=8,
                                        textColor=tc, leading=11, **kw)))
    t = Table([cells], colWidths=col_widths)
    style = [
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]
    if border:
        style.append(('LINEBELOW', (0,0),(-1,-1), 0.3, C_LGRAY))
    t.setStyle(TableStyle(style))
    return t

def campo_riga(label, note, campo_txt, bg=C_WHITE):
    """Riga con label + nota + campo compilabile"""
    w1, w2, w3 = CW*0.28, CW*0.22, CW*0.50
    t = Table([[
        Paragraph(label, st('l', fontName='Helvetica-Bold', fontSize=8,
                              textColor=C_NAVY, leading=11)),
        Paragraph(note,  st('n', fontSize=7, textColor=C_GRAY, leading=10)),
        Paragraph(campo_txt, st('c', fontSize=8, textColor=C_NAVY, leading=11)),
    ]], colWidths=[w1, w2, w3])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('LINEBELOW',     (0,0),(-1,-1), 0.3, C_LGRAY),
    ]))
    return t

def fascia_block(n, label, orario, peso):
    """Singolo blocco fascia oraria — metà larghezza pagina"""
    fw = CW / 2 - 3*mm
    bg = C_LIGHT if n % 2 == 1 else C_YELL
    t = Table([
        [Paragraph(f'<b>{n}. {label}</b>',
                   st('ft', fontName='Helvetica-Bold', fontSize=8.5,
                      textColor=C_NAVY, leading=12)),
         Paragraph(orario, st('fo', fontSize=7.5, textColor=C_GRAY,
                               alignment=TA_RIGHT, leading=11))],
        [Paragraph('Persone/15min: <b>______</b>',
                   st('fp', fontSize=8, textColor=C_GRAY, leading=11)),
         Paragraph(f'Peso: <b>{peso}</b>',
                   st('fpeso', fontSize=7.5, textColor=C_TEAL,
                      alignment=TA_RIGHT, leading=11))],
        [Paragraph('Data: __________ Ora: _____',
                   st('fd', fontSize=7.5, textColor=C_GRAY, leading=11)),
         Paragraph('Note: __________',
                   st('fn', fontSize=7.5, textColor=C_GRAY,
                      alignment=TA_RIGHT, leading=11))],
    ], colWidths=[fw*0.65, fw*0.35])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('BOX',           (0,0),(-1,-1), 0.6, C_LGRAY),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),
        ('RIGHTPADDING',  (0,0),(-1,-1), 7),
        ('LINEBELOW',     (0,0),(1,0), 0.3, C_LGRAY),
        ('LINEBELOW',     (0,1),(1,1), 0.3, C_LGRAY),
        ('ROUNDEDCORNERS',[4,4,4,4]),
    ]))
    return t

def concorrente_scheda(n):
    """Scheda dati concorrente — larghezza piena CW"""
    bg  = C_LIGHT if n % 2 == 1 else C_ORAN
    hbg = C_TEAL  if n % 2 == 1 else C_GOLD
    rows = []
    # Header
    rows.append(Table([[
        Paragraph(f'CONCORRENTE N. {n}',
                  st('ch', fontName='Helvetica-Bold', fontSize=9,
                     textColor=colors.white, leading=12))
    ]], colWidths=[CW], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), hbg),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
    ])))
    # Riga 1: Nome / Indirizzo / Distanza
    rows.append(Table([[
        Paragraph('Nome:', st('l1', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('_______________________________', st('v1', fontSize=7.5, textColor=C_GRAY)),
        Paragraph('Indirizzo:', st('l2', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('_______________________', st('v2', fontSize=7.5, textColor=C_GRAY)),
        Paragraph('Dist:', st('l3', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('_____ m', st('v3', fontSize=7.5, textColor=C_GRAY)),
    ]], colWidths=[CW*0.09, CW*0.27, CW*0.12, CW*0.30, CW*0.07, CW*0.15],
    style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('LINEBELOW',     (0,0),(-1,-1), 0.3, C_LGRAY),
    ])))
    # Riga 2: Macchine / Prezzi
    rows.append(Table([[
        Paragraph('N. Lav:', st('ml', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('___', st('mv', fontSize=7.5, textColor=C_GRAY)),
        Paragraph('N. Asc:', st('al', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('___', st('av', fontSize=7.5, textColor=C_GRAY)),
        Paragraph('Pr. lav €:', st('pl', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('______', st('pv', fontSize=7.5, textColor=C_GRAY)),
        Paragraph('Pr. asc €:', st('pal', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('______', st('pav', fontSize=7.5, textColor=C_GRAY)),
    ]], colWidths=[CW*0.10, CW*0.08, CW*0.10, CW*0.08, CW*0.13, CW*0.12, CW*0.13, CW*0.14],
    style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_WHITE),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('LINEBELOW',     (0,0),(-1,-1), 0.3, C_LGRAY),
    ])))
    # Riga 3: Orari + check
    rows.append(Table([[
        Paragraph('Orario:', st('ol', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('_____ - _____', st('ov', fontSize=7.5, textColor=C_GRAY)),
        Paragraph('[ ] H24', st('h24', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('[ ] App pagam.', st('app', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('[ ] Eco', st('eco', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('[ ] Tessera', st('tes', fontSize=7.5, textColor=C_NAVY)),
    ]], colWidths=[CW*0.10, CW*0.21, CW*0.13, CW*0.20, CW*0.13, CW*0.15],
    style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('LINEBELOW',     (0,0),(-1,-1), 0.3, C_LGRAY),
    ])))
    # Visite 1 e 2
    for v in [1, 2]:
        vbg = C_WHITE if v == 1 else C_LIGHT
        rows.append(Table([[
            Paragraph(f'VISITA {v} — Data/Ora:',
                      st(f'vl{v}', fontName='Helvetica-Bold', fontSize=7.5,
                         textColor=C_TEAL, leading=11)),
            Paragraph('_______________',
                      st(f'vd{v}', fontSize=7.5, textColor=C_GRAY)),
            Paragraph('Lav. occupate:',
                      st(f'vll{v}', fontName='Helvetica-Bold', fontSize=7.5,
                         textColor=C_NAVY)),
            Paragraph('___ / ___',
                      st(f'vlv{v}', fontSize=7.5, textColor=C_GRAY)),
            Paragraph('Asc. occupate:',
                      st(f'val{v}', fontName='Helvetica-Bold', fontSize=7.5,
                         textColor=C_NAVY)),
            Paragraph('___ / ___',
                      st(f'vav{v}', fontSize=7.5, textColor=C_GRAY)),
        ]], colWidths=[CW*0.22, CW*0.18, CW*0.17, CW*0.13, CW*0.17, CW*0.13],
        style=TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), vbg),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',   (0,0),(-1,-1), 7),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('LINEBELOW',     (0,0),(-1,-1), 0.3, C_LGRAY),
        ])))
    # Qualita
    rows.append(Table([[
        Paragraph('Pulizia:', st('ql', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('1 2 3 4 5', st('qv', fontSize=8, textColor=C_GRAY)),
        Paragraph('Funzion.:', st('fl', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('1 2 3 4 5', st('fv', fontSize=8, textColor=C_GRAY)),
        Paragraph('Assistenza:', st('asl', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_NAVY)),
        Paragraph('1 2 3 4 5', st('asv', fontSize=8, textColor=C_GRAY)),
    ]], colWidths=[CW*0.12, CW*0.20, CW*0.12, CW*0.20, CW*0.16, CW*0.20],
    style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('LINEBELOW',     (0,0),(-1,-1), 0.3, C_LGRAY),
    ])))
    # Punti deboli
    rows.append(Table([[
        Paragraph('Punti deboli / note:',
                  st('pdl', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_RED)),
        Paragraph('__________________________________________________________________',
                  st('pdv', fontSize=7.5, textColor=C_LGRAY)),
    ]], colWidths=[CW*0.24, CW*0.76],
    style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_WHITE),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),
        ('BOX',           (0,0),(-1,-1), 0.5, C_LGRAY),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ])))
    return rows


def build_pdf_campo(pratica=None, settings=None):
    buf   = io.BytesIO()
    TODAY = datetime.date.today().strftime('%d/%m/%Y')

    p_numero  = (getattr(pratica,'numero',None)   or '________________')
    p_cliente = ''
    if pratica and getattr(pratica,'cliente',None):
        p_cliente = pratica.cliente.nome or ''
    p_indirizzo = getattr(pratica,'indirizzo','') or ''
    p_citta     = getattr(pratica,'citta','')     or ''
    p_sede = f'{p_indirizzo}, {p_citta}' if p_indirizzo else '________________________________'

    s_brand = 'BIOLavaTU by Rotondi Group'
    s_addr  = 'Via F.lli Rosselli 14/16 - 20019 Settimo Milanese (MI)'
    s_web   = 'www.biolavatu.it'
    if settings:
        s_brand = getattr(settings,'brand_name',s_brand) or s_brand
        s_addr  = getattr(settings,'company_addr',s_addr) or s_addr
        s_web   = getattr(settings,'company_web',s_web)   or s_web

    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=M, rightMargin=M,
        topMargin=1.3*cm, bottomMargin=1.1*cm)
    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 1 — COPERTINA + ISTRUZIONI
    # ══════════════════════════════════════════════════════════════════════════

    # Header brand
    story.append(Table([[
        Paragraph(f'<b>{s_brand}</b>',
                  st('br', fontName='Helvetica-Bold', fontSize=13,
                     textColor=colors.white, leading=17)),
        Paragraph(s_web,
                  st('bw', fontSize=8.5, textColor=colors.HexColor('#93C5FD'),
                     alignment=TA_RIGHT)),
    ]], colWidths=[CW*0.68, CW*0.32], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
        ('TOPPADDING',    (0,0),(-1,-1), 12),
        ('BOTTOMPADDING', (0,0),(-1,-1), 12),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS',[8,8,8,8]),
    ])))
    story.append(sp(8))

    # Titolo
    story.append(Table([[
        Paragraph('SCHEDA DI SOPRALLUOGO',
                  st('t1', fontName='Helvetica-Bold', fontSize=15,
                     textColor=C_NAVY, alignment=TA_CENTER, leading=19,
                     letterSpacing=0.5)),
    ], [
        Paragraph('VERSIONE INVESTITORE — Documento riservato da compilare sul campo',
                  st('t2', fontSize=8.5, textColor=C_GRAY,
                     alignment=TA_CENTER, leading=12)),
    ]], colWidths=[CW], style=TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
    ])))
    story.append(sp(10))

    # Dati pratica (3 righe)
    def dati_row(cells, widths, bg):
        t = Table([cells], colWidths=widths)
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), bg),
            ('TOPPADDING',    (0,0),(-1,-1), 7),
            ('BOTTOMPADDING', (0,0),(-1,-1), 7),
            ('LEFTPADDING',   (0,0),(-1,-1), 10),
            ('RIGHTPADDING',  (0,0),(-1,-1), 6),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('LINEBELOW',     (0,0),(-1,-1), 0.3, C_LGRAY),
        ]))
        return t

    story.append(dati_row([
        Paragraph('<b>N° Pratica:</b>',    st('dp1', fontSize=8, textColor=C_NAVY)),
        Paragraph(p_numero,                st('dp1v', fontSize=9, fontName='Helvetica-Bold',
                                              textColor=C_BLU)),
        Paragraph('<b>Data sopralluogo:</b>', st('dp2', fontSize=8, textColor=C_NAVY)),
        Paragraph('_____________________', st('dp2v', fontSize=8, textColor=C_GRAY)),
        Paragraph('<b>Operatore:</b>',     st('dp3', fontSize=8, textColor=C_NAVY)),
        Paragraph('_____________________', st('dp3v', fontSize=8, textColor=C_GRAY)),
    ], [CW*0.14, CW*0.18, CW*0.18, CW*0.18, CW*0.13, CW*0.19], C_LIGHT))

    story.append(dati_row([
        Paragraph('<b>Cliente:</b>',       st('dc1', fontSize=8, textColor=C_NAVY)),
        Paragraph(p_cliente or '_________________________',
                                           st('dc1v', fontSize=8, textColor=C_NAVY)),
        Paragraph('<b>Sede proposta:</b>', st('dc2', fontSize=8, textColor=C_NAVY)),
        Paragraph(p_sede,                  st('dc2v', fontSize=8, textColor=C_NAVY)),
    ], [CW*0.11, CW*0.34, CW*0.17, CW*0.38], C_WHITE))
    story.append(sp(12))

    # Istruzioni A-B-C-D
    story.append(hdr_bar('ISTRUZIONI — Leggere prima di iniziare', C_BLU, sz=9))
    story.append(sp(3))

    istr = [
        ('A', C_BLU,  C_LIGHT,
         'TRAFFICO PEDONALE',
         'Conta le persone che passano davanti al locale per 15 minuti. '
         'Ripeti in almeno 4 fasce orarie diverse (giorni diversi). '
         'Conta solo i pedoni sul marciapiede davanti all\'ingresso — non le auto.'),
        ('B', C_TEAL, C_YELL,
         'ANALISI CONCORRENTI',
         'Per ogni lavanderia entro 1km: annota macchine, prezzi, orari. '
         'Torna almeno 2 volte e conta quante macchine sono occupate. '
         'Questo e il dato piu prezioso per stimare il mercato reale della zona.'),
        ('C', C_GREEN, C_LIGHT,
         'QUALITA DEL LOCALE',
         'Valuta visibilita dalla strada, parcheggio, accessibilita, piano. '
         'Verifica presenza di cantieri o lavori stradali previsti nei prossimi 12 mesi.'),
        ('D', C_GOLD, C_YELL,
         'REINSERIMENTO PIATTAFORMA',
         'Dopo il sopralluogo accedi a LaundryPro, apri la pratica, '
         'vai allo step 3B e inserisci tutti i dati. '
         'Il sistema calcola l\'analisi a 3 metodi convergenti con margine di errore stimato.'),
    ]
    LW = 0.68*cm
    TW = CW - LW
    for cod, bg_let, bg_txt, tit, txt in istr:
        row = Table([[
            Paragraph(cod, st(f'ic{cod}', fontName='Helvetica-Bold', fontSize=15,
                               textColor=colors.white, alignment=TA_CENTER, leading=19)),
            Paragraph(
                f'<b>{tit}</b><br/>'
                f'<font size="7.5" color="#64748B">{txt}</font>',
                st(f'ib{cod}', fontSize=8.5, fontName='Helvetica-Bold',
                   textColor=C_NAVY, leading=13)),
        ]], colWidths=[LW, TW])
        row.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(0,0), bg_let),
            ('BACKGROUND',    (1,0),(1,0), bg_txt),
            ('TOPPADDING',    (0,0),(-1,-1), 7),
            ('BOTTOMPADDING', (0,0),(-1,-1), 7),
            ('LEFTPADDING',   (0,0),(0,0), 3),
            ('RIGHTPADDING',  (0,0),(0,0), 2),
            ('LEFTPADDING',   (1,0),(1,0), 8),
            ('RIGHTPADDING',  (1,0),(1,0), 6),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            ('LINEBELOW',     (0,0),(-1,-1), 0.4, C_LGRAY),
        ]))
        story.append(row)
    story.append(sp(10))

    # Scala occupazione
    story.append(hdr_bar('SCALA DI RIFERIMENTO — OCCUPAZIONE MACCHINE (6L+4A)', C_NAVY, sz=8.5))
    story.append(sp(2))
    scala = [
        ['Occupazione', 'Incasso stimato', 'Situazione di mercato'],
        ['< 25%',  '< € 8.000/mese',   'Zona satura — troppa concorrenza'],
        ['25-40%', '€ 8.000-12.000',   'Zona competitiva — possibile'],
        ['40-60%', '€ 12.000-18.000',  'Zona interessante — buona opportunita'],
        ['> 60%',  '> € 18.000/mese',  'Zona ottimale — poca concorrenza'],
    ]
    t_sc = Table(scala, colWidths=[CW*0.16, CW*0.28, CW*0.56])
    t_sc.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0),  colors.white),
        ('FONTNAME',      (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,-1), 8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),
         [colors.HexColor('#FEE2E2'), C_YELL,
          colors.HexColor('#ECFDF5'), colors.HexColor('#EFF6FF')]),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('GRID',          (0,0),(-1,-1), 0.3, C_LGRAY),
        ('BOX',           (0,0),(-1,-1), 0.8, C_NAVY),
    ]))
    story.append(t_sc)

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 2 — SCHEDA A: TRAFFICO PEDONALE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Table([[
        Paragraph('<b>SCHEDA A — TRAFFICO PEDONALE</b>',
                  st('sa', fontName='Helvetica-Bold', fontSize=13,
                     textColor=colors.white, leading=16)),
        Paragraph('Conta persone in 15 minuti davanti al locale',
                  st('sa2', fontSize=8, textColor=colors.HexColor('#93C5FD'),
                     alignment=TA_RIGHT, leading=11)),
    ]], colWidths=[CW*0.58, CW*0.42], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_BLU),
        ('TOPPADDING',    (0,0),(-1,-1), 11),
        ('BOTTOMPADDING', (0,0),(-1,-1), 11),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 12),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS',[8,8,8,8]),
    ])))
    story.append(sp(6))

    story.append(Table([[
        Paragraph('Indirizzo locale: _________________________________'
                  '     Piano: ________     '
                  'Lato: [ ] N  [ ] S  [ ] E  [ ] O',
                  st('si', fontSize=8, textColor=C_NAVY, leading=11)),
    ]], colWidths=[CW], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_LIGHT),
        ('TOPPADDING',    (0,0),(-1,-1), 7),
        ('BOTTOMPADDING', (0,0),(-1,-1), 7),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('BOX',           (0,0),(-1,-1), 0.5, colors.HexColor('#BFDBFE')),
    ])))
    story.append(sp(8))

    # 6 fasce in griglia 2×3
    fasce = [
        (1, 'Lunedi mattina',    '9:00-10:00',   'ALTA (x1.0)'),
        (2, 'Lunedi pranzo',     '12:30-13:30',  'MEDIA (x0.8)'),
        (3, 'Lunedi sera',       '18:00-19:00',  'ALTA (x1.2)'),
        (4, 'Sabato mattina',    '10:00-11:00',  'MAX (x1.5)'),
        (5, 'Sabato pomeriggio', '15:00-16:00',  'ALTA (x1.3)'),
        (6, 'Feriale casuale',   'orario libero','MEDIA (x1.0)'),
    ]
    gap = 4*mm
    fw  = (CW - gap) / 2
    for i in range(0, 6, 2):
        row = Table([[
            fascia_block(*fasce[i]),
            Spacer(gap, 1),
            fascia_block(*fasce[i+1]),
        ]], colWidths=[fw, gap, fw])
        row.setStyle(TableStyle([
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 0),
            ('LEFTPADDING',   (0,0),(-1,-1), 0),
            ('RIGHTPADDING',  (0,0),(-1,-1), 0),
        ]))
        story.append(row)
        story.append(sp(5))

    story.append(sp(6))
    story.append(hdr_bar('RIEPILOGO TRAFFICO', C_TEAL, sz=8.5))
    story.append(sp(3))
    story.append(Table([[
        Paragraph('Somma persone/15min: ________',  st('rm1', fontSize=8)),
        Paragraph('Diviso n.rilevazioni: _____ = Media: _____',
                  st('rm2', fontSize=8)),
        Paragraph('x 4 = _____ pers/ora',  st('rm3', fontSize=8)),
        Paragraph('<b>x 13h = _____ pers/g</b>',
                  st('rm4', fontName='Helvetica-Bold', fontSize=8.5,
                     textColor=C_BLU)),
    ]], colWidths=[CW*0.26, CW*0.34, CW*0.20, CW*0.20],
    style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), colors.HexColor('#F0FDFA')),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('BOX',           (0,0),(-1,-1), 0.8, C_TEAL),
        ('INNERGRID',     (0,0),(-1,-1), 0.3, C_LGRAY),
    ])))
    story.append(sp(6))
    story.append(Paragraph('<b>Note aggiuntive</b> (tipo di passanti, orari di punta, eventi):',
                           st('nt', fontSize=8, textColor=C_NAVY)))
    story.append(sp(2))
    story.append(Table([['']], colWidths=[CW], rowHeights=[1.8*cm],
        style=TableStyle([
            ('BOX',           (0,0),(-1,-1), 0.5, C_LGRAY),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ])))

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 3 — SCHEDA B: CONCORRENTI 1 e 2
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Table([[
        Paragraph('<b>SCHEDA B — ANALISI CONCORRENTI</b>',
                  st('sb', fontName='Helvetica-Bold', fontSize=13,
                     textColor=colors.white, leading=16)),
        Paragraph('Visita ogni concorrente almeno 2 volte in orari diversi',
                  st('sb2', fontSize=8, textColor=colors.HexColor('#FCD34D'),
                     alignment=TA_RIGHT, leading=11)),
    ]], colWidths=[CW*0.60, CW*0.40], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_GOLD),
        ('TOPPADDING',    (0,0),(-1,-1), 11),
        ('BOTTOMPADDING', (0,0),(-1,-1), 11),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 12),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS',[8,8,8,8]),
    ])))
    story.append(sp(8))
    for n in [1, 2]:
        for row in concorrente_scheda(n):
            story.append(row)
        story.append(sp(8))

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 4 — CONCORRENTI 3-4 + INIZIO SCHEDA C
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(hdr_bar('SCHEDA B (continua) — CONCORRENTI 3 e 4', C_GOLD, sz=10))
    story.append(sp(6))
    for n in [3, 4]:
        for row in concorrente_scheda(n):
            story.append(row)
        story.append(sp(6))

    story.append(sp(4))
    story.append(HRFlowable(width=CW, thickness=1.5, color=C_NAVY))
    story.append(sp(8))

    # SCHEDA C
    story.append(Table([[
        Paragraph('<b>SCHEDA C — QUALITA DEL LOCALE</b>',
                  st('sc', fontName='Helvetica-Bold', fontSize=13,
                     textColor=colors.white, leading=16)),
        Paragraph('Valutazione fisica della sede proposta',
                  st('sc2', fontSize=8, textColor=colors.HexColor('#A7F3D0'),
                     alignment=TA_RIGHT, leading=11)),
    ]], colWidths=[CW*0.60, CW*0.40], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_GREEN),
        ('TOPPADDING',    (0,0),(-1,-1), 11),
        ('BOTTOMPADDING', (0,0),(-1,-1), 11),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 12),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS',[8,8,8,8]),
    ])))
    story.append(sp(4))

    campi_c = [
        ('Visibilita dalla strada',  'Quanto e visibile?',
         '[ ]1  [ ]2  [ ]3  [ ]4  [ ]5  [ ]6  [ ]7  [ ]8  [ ]9  [ ]10',
         C_LIGHT),
        ('Distanza arteria princ.',  'Metri dalla via piu trafficata',
         '__________ m',
         C_WHITE),
        ('Parcheggio diretto',        'Posti auto davanti',
         '[ ] Si, n.___ posti     [ ] No',
         C_LIGHT),
        ('Lato soleggiato',           'Vetrina luminosa',
         '[ ] Si     [ ] No',
         C_WHITE),
        ('Piano del locale',          '',
         '[ ] Piano strada (ottimo)     [ ] Seminterrato     [ ] Piano sup.',
         C_LIGHT),
        ('Cantieri previsti',         'Lavori stradali',
         '[ ] Si, durata stimata: ___________     [ ] No',
         C_WHITE),
        ('Gas metano',                'Allaccio disponibile',
         '[ ] Si     [ ] No     [ ] Predisposizione',
         C_LIGHT),
        ('Larghezza ingresso',        'Per accesso carrelli',
         '__________ cm',
         C_WHITE),
        ('Attivita adiacenti',        '',
         '[ ] Supermercato     [ ] Bar     [ ] Farmacia     [ ] Altro: __________',
         C_LIGHT),
        ('Accessibilita disabili',    '',
         '[ ] Si     [ ] No     [ ] Parziale',
         C_WHITE),
    ]
    for label, note, campo, bg in campi_c:
        story.append(campo_riga(label, note, campo, bg))

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 5 — NOTE FINALI + FIRMA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(hdr_bar('NOTE FINALI DEL SOPRALLUOGO', C_NAVY, sz=10))
    story.append(sp(3))
    story.append(Paragraph(
        'Impressioni generali, opportunita rilevate, rischi, domande da approfondire:',
        st('nf', fontSize=8, textColor=C_GRAY)))
    story.append(sp(2))
    story.append(Table([['']], colWidths=[CW], rowHeights=[3.5*cm],
        style=TableStyle([
            ('BOX', (0,0),(-1,-1), 0.5, C_LGRAY),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ])))
    story.append(sp(10))

    # Riepilogo rapido (checklist)
    story.append(hdr_bar('CHECKLIST — Dati raccolti', C_BLU, sz=9))
    story.append(sp(3))
    checklist = [
        ('[ ] Scheda A completata',    '(min. 4 fasce orarie)',
         '[ ] Scheda B concorrenti',   '(min. 2 visite ciascuno)'),
        ('[ ] Qualita locale valutata','(Scheda C)',
         '[ ] Dati reinseriti',        'in LaundryPro piattaforma'),
    ]
    for r in checklist:
        t = Table([[
            Paragraph(r[0], st('ck0', fontName='Helvetica-Bold', fontSize=8, textColor=C_NAVY)),
            Paragraph(r[1], st('ck1', fontSize=7.5, textColor=C_GRAY)),
            Paragraph(r[2], st('ck2', fontName='Helvetica-Bold', fontSize=8, textColor=C_NAVY)),
            Paragraph(r[3], st('ck3', fontSize=7.5, textColor=C_GRAY)),
        ]], colWidths=[CW*0.28, CW*0.24, CW*0.28, CW*0.20])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), C_LIGHT),
            ('TOPPADDING',    (0,0),(-1,-1), 6),
            ('BOTTOMPADDING', (0,0),(-1,-1), 6),
            ('LEFTPADDING',   (0,0),(-1,-1), 10),
            ('LINEBELOW',     (0,0),(-1,-1), 0.3, C_LGRAY),
        ]))
        story.append(t)
    story.append(sp(14))

    # Firme
    story.append(HRFlowable(width=CW, thickness=1, color=C_NAVY))
    story.append(sp(10))
    story.append(Table([[
        Table([[
            Paragraph('Firma operatore:', st('fo', fontSize=8, textColor=C_GRAY)),
            sp(22),
            HRFlowable(width=CW*0.32, thickness=0.8, color=C_LGRAY),
            Paragraph('______________________________',
                      st('fl', fontSize=8, textColor=C_LGRAY)),
        ]], colWidths=[CW*0.42]),
        Table([[
            Paragraph(f'Data: _______________',
                      st('fd', fontSize=8, textColor=C_GRAY)),
        ]], colWidths=[CW*0.22]),
        Table([[
            Paragraph(f'Pratica N°: <b>{p_numero}</b>',
                      st('fp', fontSize=8.5, textColor=C_BLU,
                         fontName='Helvetica-Bold')),
        ]], colWidths=[CW*0.32]),
    ]], colWidths=[CW*0.45, CW*0.22, CW*0.33],
    style=TableStyle([
        ('VALIGN', (0,0),(-1,-1), 'TOP'),
    ])))
    story.append(sp(8))
    story.append(Paragraph(
        f'Documento generato da LaundryPro AI Platform — {s_brand} — {TODAY} — '
        'Riservato e confidenziale — da riconsegnare dopo il sopralluogo',
        st('ft', fontSize=6.5, textColor=C_GRAY, alignment=TA_CENTER)))

    doc.build(story)
    buf.seek(0)
    return buf
