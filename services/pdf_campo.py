"""
services/pdf_campo.py — BIOLavaTU LaundryPro
Genera il PDF da campo per analisi investitore.
Documento stampabile A4, da portare sul posto per raccogliere dati reali.
4 pagine:
  1. Copertina + dati pratica + istruzioni
  2. SCHEDA A — Traffico pedonale (6 fasce orarie)
  3. SCHEDA B — Analisi concorrenti (fino a 4)
  4. SCHEDA C — Qualita locale + note finali
"""
import io, os, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image
)

W, H  = A4
M     = 1.5 * cm
CW    = W - 2 * M

# Colori
C_NAVY  = colors.HexColor('#0B1F3A')
C_BLU   = colors.HexColor('#1B4F72')
C_TEAL  = colors.HexColor('#0E7490')
C_GREEN = colors.HexColor('#059669')
C_GOLD  = colors.HexColor('#D97706')
C_RED   = colors.HexColor('#EF4444')
C_GRAY  = colors.HexColor('#64748B')
C_LGRAY = colors.HexColor('#E2E8F0')
C_WHITE = colors.white
C_LIGHT = colors.HexColor('#F0F9FF')
C_YELLOW= colors.HexColor('#FFFBEB')
C_ORANGE= colors.HexColor('#FFF7ED')

def _s(name, **kw):
    import random, string
    uid = ''.join(random.choices(string.ascii_lowercase, k=4))
    base = dict(fontName='Helvetica', fontSize=9, leading=13,
                textColor=colors.HexColor('#0F172A'))
    base.update(kw)
    return ParagraphStyle(f'{name}_{uid}', **base)

def sp(n=6):
    return Spacer(1, n)

def _box(titolo, contenuto_rows, col_w=None, header_bg=None):
    """Tabella con header colorato e righe contenuto"""
    header_bg = header_bg or C_BLU
    col_w = col_w or [CW]
    hdr = Table([[Paragraph(titolo, _s('bh', fontName='Helvetica-Bold',
                  fontSize=8.5, textColor=C_WHITE, letterSpacing=0.5,
                  leading=12))]], colWidths=[CW])
    hdr.setStyle(TableStyle([
        ('BACKGROUND',  (0,0),(-1,-1), header_bg),
        ('TOPPADDING',  (0,0),(-1,-1), 7),
        ('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('LEFTPADDING', (0,0),(-1,-1), 10),
    ]))
    return hdr

def _campo_riga(label, note='', h=0.9*cm, bg=C_WHITE):
    """Riga con label + rettangolo vuoto per scrittura a mano"""
    riga = Table([[
        Paragraph(label, _s('cl', fontSize=8, fontName='Helvetica-Bold',
                             textColor=C_NAVY)),
        Paragraph(note, _s('cn', fontSize=7, textColor=C_GRAY)),
        ''  # spazio scrittura
    ]], colWidths=[CW*0.32, CW*0.25, CW*0.43])
    riga.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('BOX',           (2,0),(2,0), 0.8, C_LGRAY),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('ROWHEIGHT',     (0,0),(-1,-1), h),
    ]))
    return riga

def _campo_grande(label, h=1.8*cm):
    """Campo grande per testo libero"""
    t = Table([[
        Paragraph(label, _s('cgl', fontSize=8, fontName='Helvetica-Bold',
                              textColor=C_NAVY)),
        ''
    ]], colWidths=[CW*0.25, CW*0.75])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_WHITE),
        ('BOX',           (1,0),(1,0), 0.8, C_LGRAY),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('ROWHEIGHT',     (0,0),(-1,-1), h),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ]))
    return t

def _checkbox_row(items):
    """Riga di checkbox (quadratino + label)"""
    cols = []
    for item in items:
        cols.append(Table([[
            Table([['']], colWidths=[0.35*cm], style=TableStyle([
                ('BOX',           (0,0),(0,0), 0.8, C_GRAY),
                ('ROWHEIGHT',     (0,0),(0,0), 0.35*cm),
                ('TOPPADDING',    (0,0),(0,0), 0),
                ('BOTTOMPADDING', (0,0),(0,0), 0),
            ])),
            Paragraph(item, _s('cb', fontSize=8, textColor=C_NAVY)),
        ]], colWidths=[0.45*cm, CW/len(items)-0.55*cm]))
    row = Table([cols], colWidths=[CW/len(items)]*len(items))
    row.setStyle(TableStyle([
        ('VALIGN',   (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
    ]))
    return row

def _rating_row(label):
    """Riga con cerchi 1-5 da barrare"""
    circles = '  '.join(['○'] * 5) + '  (1=pessimo  5=ottimo)'
    t = Table([[
        Paragraph(label, _s('rl', fontSize=8, fontName='Helvetica-Bold',
                              textColor=C_NAVY)),
        Paragraph(circles, _s('rc', fontSize=10, textColor=C_GRAY)),
    ]], colWidths=[CW*0.40, CW*0.60])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_WHITE),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('LINEBELOW',     (0,0),(-1,-1), 0.3, C_LGRAY),
    ]))
    return t


def _fascia_block(n, label, orario, peso_label):
    """Blocco per una fascia oraria — 2 colonne nella griglia"""
    bg = C_LIGHT if n % 2 == 0 else C_YELLOW
    t = Table([
        [Paragraph(f'{n}. {label}',
                   _s('fl', fontName='Helvetica-Bold', fontSize=8.5,
                      textColor=C_NAVY)),
         Paragraph(orario, _s('fo', fontSize=7.5, textColor=C_GRAY,
                               alignment=TA_RIGHT))],
        [Paragraph('Persone in 15 min: ______',
                   _s('ff', fontSize=8, textColor=C_GRAY)),
         Paragraph(f'Peso: {peso_label}',
                   _s('fp', fontSize=7, textColor=C_TEAL, alignment=TA_RIGHT))],
        [Paragraph('Data: ___________  Ora: _______',
                   _s('fd', fontSize=7.5, textColor=C_GRAY)),
         Paragraph('Note: _____________________',
                   _s('fn', fontSize=7.5, textColor=C_GRAY))],
    ], colWidths=[CW/2*0.76, CW/2*0.24])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('BOX',           (0,0),(-1,-1), 0.8, C_LGRAY),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('RIGHTPADDING',  (0,0),(-1,-1), 8),
        ('ROUNDEDCORNERS',[4,4,4,4]),
    ]))
    return t


def _concorrente_block(n):
    """Scheda raccolta dati per un singolo concorrente"""
    bg = C_LIGHT if n % 2 == 0 else C_ORANGE

    rows = [
        # Header concorrente
        Table([[Paragraph(f'CONCORRENTE N. {n}',
                         _s('ch', fontName='Helvetica-Bold', fontSize=9,
                            textColor=C_WHITE))
               ]], colWidths=[CW],
               style=TableStyle([
                   ('BACKGROUND',    (0,0),(-1,-1), C_TEAL if n%2==0 else C_GOLD),
                   ('TOPPADDING',    (0,0),(-1,-1), 6),
                   ('BOTTOMPADDING', (0,0),(-1,-1), 6),
                   ('LEFTPADDING',   (0,0),(-1,-1), 10),
               ])),
        # Dati base
        Table([[
            Paragraph('Nome: _______________________________',
                      _s('ci1', fontSize=8)),
            Paragraph('Indirizzo: _________________________',
                      _s('ci2', fontSize=8)),
            Paragraph('Distanza: _______ m',
                      _s('ci3', fontSize=8)),
        ]], colWidths=[CW*0.36, CW*0.40, CW*0.24],
        style=TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), bg),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ])),
        # Macchine e prezzi
        Table([[
            Paragraph('N. Lavatrici: ___',  _s('cm1', fontSize=8)),
            Paragraph('N. Asciugatrici: ___', _s('cm2', fontSize=8)),
            Paragraph('Prezzo lavaggio: € ___',  _s('cm3', fontSize=8)),
            Paragraph('Prezzo asciug: € ___', _s('cm4', fontSize=8)),
        ]], colWidths=[CW*0.22, CW*0.24, CW*0.27, CW*0.27],
        style=TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), C_WHITE),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('LINEABOVE',     (0,0),(-1,-1), 0.3, C_LGRAY),
        ])),
        # Orari
        Table([[
            Paragraph('Orario: _____ - _____  [ ]H24  [ ]App  [ ]Eco',
                      _s('co1', fontSize=8)),
            Paragraph('Prezzi: Lav € ___  Asc € ___',
                      _s('co2', fontSize=8)),
        ]], colWidths=[CW*0.56, CW*0.44],
        style=TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), bg),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('LINEABOVE',     (0,0),(-1,-1), 0.3, C_LGRAY),
        ])),
        # Visite occupazione
        Table([[
            Paragraph('VISITA 1 — Data/Ora: ____________',
                      _s('cv1', fontSize=7.5, fontName='Helvetica-Bold', textColor=C_TEAL)),
            Paragraph('Lav. occupate: ___ / ___',
                      _s('cv1l', fontSize=7.5, textColor=C_GRAY)),
            Paragraph('Asc. occupate: ___ / ___',
                      _s('cv1a', fontSize=7.5, textColor=C_GRAY)),
        ]], colWidths=[CW*0.42, CW*0.29, CW*0.29],
        style=TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), C_WHITE),
            ('TOPPADDING',    (0,0),(-1,-1), 4),
            ('BOTTOMPADDING', (0,0),(-1,-1), 4),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('LINEABOVE',     (0,0),(-1,-1), 0.3, C_LGRAY),
        ])),
        Table([[
            Paragraph('VISITA 2 — Data/Ora: ____________',
                      _s('cv2', fontSize=7.5, fontName='Helvetica-Bold', textColor=C_TEAL)),
            Paragraph('Lav. occupate: ___ / ___',
                      _s('cv2l', fontSize=7.5, textColor=C_GRAY)),
            Paragraph('Asc. occupate: ___ / ___',
                      _s('cv2a', fontSize=7.5, textColor=C_GRAY)),
        ]], colWidths=[CW*0.42, CW*0.29, CW*0.29],
        style=TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), C_LIGHT),
            ('TOPPADDING',    (0,0),(-1,-1), 4),
            ('BOTTOMPADDING', (0,0),(-1,-1), 4),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('LINEABOVE',     (0,0),(-1,-1), 0.3, C_LGRAY),
        ])),
        # Qualita
        Table([[
            Paragraph('Pulizia: ○ ○ ○ ○ ○',  _s('cq1', fontSize=8)),
            Paragraph('Funzionamento: ○ ○ ○ ○ ○', _s('cq2', fontSize=8)),
            Paragraph('Assistenza: ○ ○ ○ ○ ○', _s('cq3', fontSize=8)),
        ]], colWidths=[CW*0.30, CW*0.36, CW*0.34],
        style=TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), bg),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('LINEABOVE',     (0,0),(-1,-1), 0.3, C_LGRAY),
        ])),
        # Punti deboli
        Table([[
            Paragraph('Punti deboli osservati:',
                      _s('cpd', fontSize=8, fontName='Helvetica-Bold', textColor=C_RED)),
            Paragraph('_' * 60, _s('cpd2', fontSize=8, textColor=C_LGRAY)),
        ]], colWidths=[CW*0.30, CW*0.70],
        style=TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), C_WHITE),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 8),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('LINEABOVE',     (0,0),(-1,-1), 0.3, C_LGRAY),
            ('BOX',           (0,0),(-1,-1), 0.5, C_LGRAY),
        ])),
    ]
    return rows


def build_pdf_campo(pratica=None, settings=None):
    """Genera PDF da campo. pratica e settings opzionali (per pre-compilare)."""
    buf  = io.BytesIO()
    TODAY = datetime.date.today().strftime('%d/%m/%Y')

    # Dati pratica (se disponibili)
    p_numero  = getattr(pratica, 'numero',   '________________') or '________________'
    p_cliente = ''
    if pratica and pratica.cliente:
        p_cliente = pratica.cliente.nome or ''
    p_indirizzo = getattr(pratica, 'indirizzo', '') or ''
    p_citta     = getattr(pratica, 'citta',     '') or ''
    p_sede      = f'{p_indirizzo}, {p_citta}' if p_indirizzo else '________________________________'

    s_brand = 'BIOLavaTU by Rotondi Group'
    s_addr  = 'Via F.lli Rosselli 14/16 - 20019 Settimo Milanese (MI)'
    s_web   = 'www.biolavatu.it'
    if settings:
        s_brand = getattr(settings, 'brand_name', s_brand) or s_brand
        s_addr  = getattr(settings, 'company_addr', s_addr) or s_addr
        s_web   = getattr(settings, 'company_web', s_web) or s_web

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=M, rightMargin=M,
        topMargin=1.2*cm, bottomMargin=1.2*cm,
    )
    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 1 — COPERTINA + ISTRUZIONI
    # ══════════════════════════════════════════════════════════════════════════

    # Header brand
    story.append(Table([[
        Paragraph(s_brand, _s('br', fontName='Helvetica-Bold', fontSize=14,
                               textColor=C_WHITE, leading=18)),
        Paragraph(s_web,   _s('bw', fontSize=9, textColor=colors.HexColor('#93C5FD'),
                               alignment=TA_RIGHT)),
    ]], colWidths=[CW*0.70, CW*0.30], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
        ('TOPPADDING',    (0,0),(-1,-1), 14),
        ('BOTTOMPADDING', (0,0),(-1,-1), 14),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS',[8,8,8,8]),
    ])))
    story.append(sp(8))

    # Titolo documento
    story.append(Table([[
        Paragraph('SCHEDA DI SOPRALLUOGO — VERSIONE INVESTITORE',
                  _s('ti', fontName='Helvetica-Bold', fontSize=16,
                     textColor=C_NAVY, alignment=TA_CENTER, letterSpacing=1, leading=20)),
        Paragraph('Documento riservato — da compilare sul campo',
                  _s('ti2', fontSize=9, textColor=C_GRAY, alignment=TA_CENTER)),
    ]], colWidths=[CW], style=TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 12),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
    ])))
    story.append(sp(10))

    # Dati pratica
    story.append(Table([[
        Paragraph('<b>N° Pratica:</b>',  _s('dp1', fontSize=9)),
        Paragraph(p_numero,              _s('dp1v', fontSize=10, fontName='Helvetica-Bold', textColor=C_BLU)),
        Paragraph('<b>Data sopralluogo:</b>', _s('dp2', fontSize=9)),
        Paragraph('_______________',     _s('dp2v', fontSize=9)),
    ]], colWidths=[CW*0.18, CW*0.25, CW*0.28, CW*0.29],
    style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_LIGHT),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('BOX',           (0,0),(-1,-1), 0.5, colors.HexColor('#BFDBFE')),
        ('ROUNDEDCORNERS',[6,6,6,6]),
    ])))
    story.append(sp(4))
    story.append(Table([[
        Paragraph('<b>Cliente:</b>',  _s('dc1', fontSize=9)),
        Paragraph(p_cliente or '________________________________',
                  _s('dc1v', fontSize=9, textColor=C_NAVY)),
        Paragraph('<b>Operatore:</b>', _s('dc2', fontSize=9)),
        Paragraph('________________________________', _s('dc2v', fontSize=9)),
    ]], colWidths=[CW*0.13, CW*0.38, CW*0.18, CW*0.31],
    style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_WHITE),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('BOX',           (0,0),(-1,-1), 0.5, C_LGRAY),
        ('ROUNDEDCORNERS',[6,6,6,6]),
    ])))
    story.append(sp(4))
    story.append(Table([[
        Paragraph('<b>Sede proposta:</b>', _s('ds1', fontSize=9)),
        Paragraph(p_sede, _s('ds1v', fontSize=9, textColor=C_NAVY)),
    ]], colWidths=[CW*0.18, CW*0.82],
    style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_LIGHT),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('BOX',           (0,0),(-1,-1), 0.5, colors.HexColor('#BFDBFE')),
        ('ROUNDEDCORNERS',[6,6,6,6]),
    ])))
    story.append(sp(14))

    # Istruzioni
    story.append(_box('ISTRUZIONI — Leggere prima di iniziare', None, header_bg=C_BLU))
    story.append(sp(4))
    istr = [
        ('A', 'TRAFFICO PEDONALE', 'Conta le persone che passano davanti al locale per 15 minuti consecutivi. '
         'Fallo in almeno 4 fasce orarie diverse in giorni diversi. Non contare le auto. '
         'Conta solo i pedoni che camminano sul marciapiede davanti all\'ingresso.'),
        ('B', 'ANALISI CONCORRENTI', 'Per ogni lavanderia concorrente entro 1km: annota le macchine fisicamente visibili, '
         'il cartello prezzi e gli orari. Poi torna 2 volte in orari diversi e annota quante macchine '
         'sono occupate. Sono i dati piu preziosi per stimare il mercato reale.'),
        ('C', 'QUALITA LOCALE', 'Valuta il locale proposto dal punto di vista della visibilita dalla strada, '
         'accessibilita, parcheggio e contesto. Cerca cantieri, sensi unici o altri fattori che '
         'possono ridurre il traffico.'),
        ('D', 'REINSERIMENTO', 'Dopo il sopralluogo, accedi alla piattaforma LaundryPro e inserisci tutti i dati '
         'raccolti nello step 3B del wizard. Il sistema calcola automaticamente l\'analisi a 3 metodi '
         'convergenti con margine di errore stimato.'),
    ]
    for cod, tit, txt in istr:
        row = Table([[
            Paragraph(cod, _s('ic', fontName='Helvetica-Bold', fontSize=14,
                               textColor=C_WHITE, alignment=TA_CENTER)),
            Table([[
                Paragraph(tit, _s('it', fontName='Helvetica-Bold', fontSize=9,
                                   textColor=C_NAVY, leading=12)),
                Paragraph(txt, _s('ib', fontSize=8, textColor=C_GRAY,
                                   leading=12, alignment=TA_LEFT)),
            ]], colWidths=[CW*0.82]),
        ]], colWidths=[0.7*cm, CW-0.7*cm])
        bg_c = {'A':C_BLU,'B':C_TEAL,'C':C_GREEN,'D':C_GOLD}[cod]
        row.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(0,0), bg_c),
            ('BACKGROUND',    (1,0),(1,0), C_LIGHT if cod in ('A','C') else C_YELLOW),
            ('TOPPADDING',    (0,0),(-1,-1), 8),
            ('BOTTOMPADDING', (0,0),(-1,-1), 8),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            ('LINEBELOW',     (0,0),(-1,-1), 0.3, C_LGRAY),
        ]))
        story.append(row)
    story.append(sp(10))

    # Scala occupazione
    story.append(_box('SCALA DI RIFERIMENTO — OCCUPAZIONE MACCHINE',
                      None, header_bg=C_NAVY))
    story.append(sp(3))
    scala_rows = [
        ['Occupazione', 'Incasso stimato (6L+4A)', 'Situazione'],
        ['< 25%',  '< € 8.000/mese',   'Zona satura — alta concorrenza'],
        ['25-40%', '€ 8.000-12.000',   'Zona competitiva'],
        ['40-60%', '€ 12.000-18.000',  'Zona interessante'],
        ['> 60%',  '> € 18.000/mese',  'Zona ottimale — bassa concorrenza'],
    ]
    t_scala = Table(scala_rows, colWidths=[CW*0.18, CW*0.38, CW*0.44])
    t_scala.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0), C_WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,-1), 8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),
         [colors.HexColor('#FEE2E2'), C_YELLOW,
          colors.HexColor('#ECFDF5'), colors.HexColor('#EFF6FF')]),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('GRID',          (0,0),(-1,-1), 0.3, C_LGRAY),
        ('BOX',           (0,0),(-1,-1), 0.8, C_NAVY),
    ]))
    story.append(t_scala)

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 2 — SCHEDA A: TRAFFICO PEDONALE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    story.append(Table([[
        Paragraph('SCHEDA A — TRAFFICO PEDONALE',
                  _s('sa', fontName='Helvetica-Bold', fontSize=13,
                     textColor=C_WHITE, letterSpacing=1, leading=16)),
        Paragraph('Conta persone in 15 minuti davanti al locale',
                  _s('sa2', fontSize=9, textColor=colors.HexColor('#93C5FD'),
                     alignment=TA_RIGHT)),
    ]], colWidths=[CW*0.62, CW*0.38], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_BLU),
        ('TOPPADDING',    (0,0),(-1,-1), 12),
        ('BOTTOMPADDING', (0,0),(-1,-1), 12),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS',[8,8,8,8]),
    ])))
    story.append(sp(6))

    story.append(Table([[
        Paragraph('Indirizzo locale osservato: _____________________________________ '
                  '    Piano: ________     Lato: [ ] Nord  [ ] Sud  [ ] Est  [ ] Ovest',
                  _s('si', fontSize=8, textColor=C_NAVY)),
    ]], colWidths=[CW], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_LIGHT),
        ('TOPPADDING',    (0,0),(-1,-1), 7),
        ('BOTTOMPADDING', (0,0),(-1,-1), 7),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('BOX',           (0,0),(-1,-1), 0.5, colors.HexColor('#BFDBFE')),
    ])))
    story.append(sp(8))

    # Griglia 6 fasce orarie (2 colonne × 3 righe)
    fasce = [
        (1, 'Lunedi mattina',     '9:00-10:00',   'ALTA (x1.0)'),
        (2, 'Lunedi pranzo',      '12:30-13:30',  'MEDIA (x0.8)'),
        (3, 'Lunedi sera',        '18:00-19:00',  'ALTA (x1.2)'),
        (4, 'Sabato mattina',     '10:00-11:00',  'MAX (x1.5)'),
        (5, 'Sabato pomeriggio',  '15:00-16:00',  'ALTA (x1.3)'),
        (6, 'Feriale casuale',    'orario libero', 'MEDIA (x1.0)'),
    ]
    for i in range(0, 6, 2):
        row = Table([[
            _fascia_block(*fasce[i]),
            sp(6),
            _fascia_block(*fasce[i+1]) if i+1 < 6 else '',
        ]], colWidths=[CW*0.48, 0.04*CW, CW*0.48])
        row.setStyle(TableStyle([
            ('VALIGN', (0,0),(-1,-1), 'TOP'),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ]))
        story.append(row)
        story.append(sp(6))

    story.append(sp(8))

    # Calcolo medio
    story.append(_box('RIEPILOGO TRAFFICO', None, header_bg=C_TEAL))
    story.append(sp(3))
    story.append(Table([[
        Paragraph('Media persone/15min (somma ÷ n.rilevazioni): ___________',
                  _s('rm1', fontSize=9)),
        Paragraph('x 4 = persone/ora: ___________',
                  _s('rm2', fontSize=9)),
        Paragraph('x 13h = persone/giorno: ___________',
                  _s('rm3', fontSize=9, fontName='Helvetica-Bold', textColor=C_BLU)),
    ]], colWidths=[CW*0.44, CW*0.28, CW*0.28], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), colors.HexColor('#F0FDFA')),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('BOX',           (0,0),(-1,-1), 0.8, C_TEAL),
        ('INNERGRID',     (0,0),(-1,-1), 0.3, C_LGRAY),
        ('ROUNDEDCORNERS',[6,6,6,6]),
    ])))
    story.append(sp(6))

    # Note traffico
    story.append(Table([[
        Paragraph('Note aggiuntive (tipo di passanti, orari di punta, eventi particolari):',
                  _s('nt', fontSize=8, fontName='Helvetica-Bold', textColor=C_NAVY)),
    ]], colWidths=[CW], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_LIGHT),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
    ])))
    story.append(Table([['']], colWidths=[CW], rowHeights=[1.8*cm],
        style=TableStyle([
            ('BOX', (0,0),(-1,-1), 0.5, C_LGRAY),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ])))

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 3 — SCHEDA B: ANALISI CONCORRENTI
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    story.append(Table([[
        Paragraph('SCHEDA B — ANALISI CONCORRENTI',
                  _s('sb', fontName='Helvetica-Bold', fontSize=13,
                     textColor=C_WHITE, letterSpacing=1, leading=16)),
        Paragraph('Visita ogni concorrente almeno 2 volte in orari diversi',
                  _s('sb2', fontSize=9, textColor=colors.HexColor('#FCD34D'),
                     alignment=TA_RIGHT)),
    ]], colWidths=[CW*0.62, CW*0.38], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_GOLD),
        ('TOPPADDING',    (0,0),(-1,-1), 12),
        ('BOTTOMPADDING', (0,0),(-1,-1), 12),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS',[8,8,8,8]),
    ])))
    story.append(sp(8))

    # 2 concorrenti per pagina
    for n in [1, 2]:
        for row in _concorrente_block(n):
            story.append(row)
        story.append(sp(10))

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 4 — CONCORRENTI 3-4 + SCHEDA C QUALITA LOCALE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    # Concorrenti 3 e 4
    story.append(Table([[
        Paragraph('SCHEDA B (continua) — CONCORRENTI 3 e 4',
                  _s('sb3', fontName='Helvetica-Bold', fontSize=11,
                     textColor=C_WHITE, leading=14)),
    ]], colWidths=[CW], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_GOLD),
        ('TOPPADDING',    (0,0),(-1,-1), 10),
        ('BOTTOMPADDING', (0,0),(-1,-1), 10),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('ROUNDEDCORNERS',[8,8,8,8]),
    ])))
    story.append(sp(6))
    for n in [3, 4]:
        for row in _concorrente_block(n):
            story.append(row)
        story.append(sp(6))

    story.append(sp(4))
    story.append(HRFlowable(width=CW, thickness=1.5, color=C_NAVY))
    story.append(sp(8))

    # SCHEDA C
    story.append(Table([[
        Paragraph('SCHEDA C — QUALITA DEL LOCALE',
                  _s('sc', fontName='Helvetica-Bold', fontSize=13,
                     textColor=C_WHITE, letterSpacing=1, leading=16)),
        Paragraph('Valutazione fisica della sede proposta',
                  _s('sc2', fontSize=9, textColor=colors.HexColor('#A7F3D0'),
                     alignment=TA_RIGHT)),
    ]], colWidths=[CW*0.60, CW*0.40], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_GREEN),
        ('TOPPADDING',    (0,0),(-1,-1), 10),
        ('BOTTOMPADDING', (0,0),(-1,-1), 10),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS',[8,8,8,8]),
    ])))
    story.append(sp(6))

    # Valutazioni qualitative
    campi_c = [
        ('Visibilita dalla strada', 'Quanto e visibile il locale?',   '○ ○ ○ ○ ○ ○ ○ ○ ○ ○  (1-10)'),
        ('Distanza arteria princ.',  'Metri dalla via piu trafficata', '_______ m'),
        ('Parcheggio diretto',        'Posti auto davanti al locale',   '[ ] Si, n.___ posti   [ ] No'),
        ('Lato soleggiato',           'Vetrina luminosa durante il giorno', '[ ] Si   [ ] No'),
        ('Piano del locale',          '',                               '[ ] Piano strada   [ ] Seminterrato   [ ] Sup.'),
        ('Cantieri previsti',         'Lavori stradali programmati',    '[ ] Si (durata: _______)   [ ] No'),
        ('Gas metano disponibile',    'Allaccio gas presente',          '[ ] Si   [ ] No   [ ] Predisposizione'),
        ('Larghezza ingresso',        'Per accesso con carrelli',       '_______ cm'),
        ('Attivita adiacenti',        'Cosa c\'e vicino?',              '[ ] Sup.  [ ] Bar  [ ] Farmacia  [ ] Altro: _____'),
    ]
    for i, (label, note, campo) in enumerate(campi_c):
        bg = C_LIGHT if i % 2 == 0 else C_WHITE
        t = Table([[
            Paragraph(label, _s(f'cc{i}', fontSize=8, fontName='Helvetica-Bold',
                                 textColor=C_NAVY)),
            Paragraph(note,  _s(f'cn{i}', fontSize=7, textColor=C_GRAY)),
            Paragraph(campo, _s(f'cv{i}', fontSize=8, textColor=C_NAVY)),
        ]], colWidths=[CW*0.30, CW*0.22, CW*0.48])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), bg),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('LINEBELOW',     (0,0),(-1,-1), 0.3, C_LGRAY),
        ]))
        story.append(t)

    story.append(sp(8))

    # Note finali
    story.append(_box('NOTE FINALI DEL SOPRALLUOGO', None, header_bg=C_NAVY))
    story.append(Table([['']], colWidths=[CW], rowHeights=[2.2*cm],
        style=TableStyle([
            ('BOX',           (0,0),(-1,-1), 0.5, C_LGRAY),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ])))
    story.append(sp(6))

    # Firma operatore
    story.append(Table([[
        Table([[
            Paragraph('Firma operatore:', _s('fo1', fontSize=8, textColor=C_GRAY)),
            sp(20),
            HRFlowable(width=CW*0.35, thickness=0.7, color=C_LGRAY),
        ]], colWidths=[CW*0.40]),
        Table([[
            Paragraph('Data: _______________', _s('fd1', fontSize=8, textColor=C_GRAY)),
        ]], colWidths=[CW*0.25]),
        Table([[
            Paragraph('Pratica N°: ' + p_numero,
                      _s('fp1', fontSize=8, textColor=C_BLU, fontName='Helvetica-Bold')),
        ]], colWidths=[CW*0.30]),
    ]], colWidths=[CW*0.45, CW*0.25, CW*0.30]))

    story.append(sp(6))
    story.append(Paragraph(
        f'Documento generato da LaundryPro AI Platform — {s_brand} — {TODAY} — Riservato e confidenziale',
        _s('ft', fontSize=6.5, textColor=C_GRAY, alignment=TA_CENTER)
    ))

    doc.build(story)
    buf.seek(0)
    return buf
