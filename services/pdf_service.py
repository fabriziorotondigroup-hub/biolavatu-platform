"""
BIOLavaTU LaundryPro Platform — PDF Service
Struttura: Copertina | Lettera AI | Analisi Zona | Business Plan | Ordine Macchine | CGV | Firme
Ogni pagina ha footer fisso con logo BIOLavaTU + dati Rotondi Group + numero pagina
"""
import io
import os
import base64
import textwrap
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image, KeepTogether
)
from reportlab.platypus.flowables import BalancedColumns
from reportlab.lib.utils import ImageReader

# ─── DIMENSIONI ──────────────────────────────────────────────────────────────
W, H   = A4
M      = 1.7 * cm
CW     = W - 2 * M
FOOTER_H = 1.2 * cm   # altezza riservata al footer

# ─── COLORI BRAND ────────────────────────────────────────────────────────────
C_NAVY   = colors.HexColor('#0B1F3A')   # navy profondo copertina
C_BLU    = colors.HexColor('#1B4F72')   # blu primario
C_TEAL   = colors.HexColor('#0E7490')   # teal zona
C_GREEN  = colors.HexColor('#059669')   # verde positivo
C_GOLD   = colors.HexColor('#D97706')   # oro / warning
C_RED    = colors.HexColor('#EF4444')   # rosso alert
C_ROSSO  = colors.HexColor('#C15E59')   # rosso brand
C_LIGHT  = colors.HexColor('#EFF6FF')   # sfondo card blu
C_GRAY   = colors.HexColor('#64748B')   # testo secondario
C_LGRAY  = colors.HexColor('#E2E8F0')   # bordi
C_WHITE  = colors.white
C_DARK   = colors.HexColor('#0D2B3E')   # dark header

# ─── CLAUSOLE CGV ─────────────────────────────────────────────────────────────
CGV = [
    ("Oggetto e natura dell'accordo",
     "Il presente contratto disciplina la fornitura, installazione e messa in opera delle "
     "attrezzature per lavanderia self-service automatica ecocompatibile da parte di BIOLavaTU "
     "by Rotondi Group Srl («Fornitore»), senza vincoli di esclusiva territoriale, canoni "
     "d'ingresso (franchise fee), royalty o qualsiasi altra forma di compenso periodico diversa "
     "dal corrispettivo della presente fornitura."),
    ("Durata, rinnovo e recesso",
     "Durata 5 anni dal collaudo positivo, tacito rinnovo annuale salvo disdetta scritta con "
     "90 giorni di preavviso tramite raccomandata A/R o PEC. Il Cliente può recedere "
     "anticipatamente, senza penali, decorsi 24 mesi dall'avvio, con preavviso scritto di "
     "60 giorni."),
    ("Fornitura, installazione e collaudo",
     "Consegna e installazione entro 30 giorni lavorativi dalla conferma ordine e ricevimento "
     "acconto. Include allacciamenti idraulici ed elettrici a norma CEI/UNI, collaudo "
     "funzionale certificato, formazione del personale (minimo 4 ore)."),
    ("Condizioni di pagamento",
     "Il corrispettivo è dovuto secondo le seguenti scadenze: 40% alla conferma ordine; "
     "40% alla comunicazione di merce pronta alla spedizione; 15% alla consegna e scarico; "
     "5% al collaudo positivo certificato. Ogni rata è soggetta a IVA 22%."),
    ("Garanzia legale e convenzionale",
     "Garanzia convenzionale 24 mesi su parti e manodopera. Risposta entro 4 ore dalla "
     "segnalazione; intervento in loco entro 48 ore lavorative; macchina sostitutiva entro "
     "72 ore se necessario. Disponibilità ricambi originali garantita per almeno 10 anni "
     "dalla data di produzione."),
    ("Assistenza tecnica e manutenzione",
     "Assistenza tecnica dedicata feriali 8:30-17:00. Contratto manutenzione preventiva "
     "semestrale disponibile a condizioni agevolate. Stock ricambi critici per intervento "
     "entro 24 ore."),
    ("Obblighi del Cliente",
     "Il Cliente predispone i locali nel rispetto delle specifiche tecniche (impianti CEI "
     "64-8, idraulici, aerazione forzata), ottiene tutte le autorizzazioni amministrative, "
     "sanitarie e urbanistiche necessarie e conduce l'attività nel rispetto delle normative "
     "vigenti in materia di igiene, sicurezza e GDPR."),
    ("Proprietà intellettuale e marchio",
     "Licenza non esclusiva e non trasferibile del marchio BIOLavaTU per segnaletica del "
     "punto vendita entro 5 km dalla sede, per la sola durata contrattuale. Vietata qualsiasi "
     "modifica del marchio senza autorizzazione scritta del Fornitore."),
    ("Responsabilità e limitazione di responsabilità",
     "Il Fornitore non risponde di danni da uso improprio, mancato rispetto delle istruzioni, "
     "interventi non autorizzati o forza maggiore. La responsabilità massima per danni diretti "
     "è limitata al valore del corrispettivo contrattuale."),
    ("Riservatezza e GDPR",
     "Le parti mantengono riservate tutte le informazioni tecniche, commerciali e finanziarie "
     "per l'intera durata contrattuale e per 5 anni successivi. Il trattamento dei dati "
     "personali avviene nel rispetto del Regolamento UE 2016/679 (GDPR)."),
    ("Risoluzione e clausola risolutiva espressa",
     "Costituisce causa di risoluzione immediata ex art. 1456 c.c.: inadempimento pagamenti "
     "oltre 30 giorni, uso non autorizzato del marchio, cessione senza consenso. Penale: "
     "15% del valore residuo, fatta salva la risarcibilità del maggior danno."),
    ("Foro competente e mediazione obbligatoria",
     "Legge italiana. Tentativo obbligatorio di mediazione (D.Lgs. 28/2010) prima delle vie "
     "giudiziarie. Foro competente esclusivo: Tribunale di Roma, con espressa rinuncia a "
     "qualsiasi altro foro."),
]

# ─── PATH LOGO ───────────────────────────────────────────────────────────────
_LOGO_PATHS = [
    '/var/www/laundrypro/static/img/biolavatu_logo.png',
    os.path.join(os.path.dirname(__file__), '..', 'static', 'img', 'biolavatu_logo.png'),
    '/tmp/biolavatu_logo_final.png',
]

def _get_logo_path():
    for p in _LOGO_PATHS:
        if os.path.exists(p):
            return p
    return None


# ─── STILI TESTO ─────────────────────────────────────────────────────────────
def _s(name, **kw):
    """Crea un ParagraphStyle con nome univoco (aggiunge suffix random)"""
    import random, string
    uid = ''.join(random.choices(string.ascii_lowercase, k=4))
    base = dict(fontName='Helvetica', fontSize=9,
                textColor=colors.HexColor('#0F172A'), leading=13)
    base.update(kw)
    return ParagraphStyle(f'{name}_{uid}', **base)


def sp(n=8):
    return Spacer(1, n)


# ─── COMPONENTI RIUTILIZZABILI ────────────────────────────────────────────────

def _section_bar(text, bg=None, fg=C_WHITE):
    bg = bg or C_BLU
    t = Table([[Paragraph(
        text,
        _s('sb', fontName='Helvetica-Bold', fontSize=8.5,
           textColor=fg, letterSpacing=0.6, leading=13)
    )]], colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), bg),
        ('TOPPADDING',    (0,0),(-1,-1), 7),
        ('BOTTOMPADDING', (0,0),(-1,-1), 7),
        ('LEFTPADDING',   (0,0),(-1,-1), 12),
        ('RIGHTPADDING',  (0,0),(-1,-1), 12),
        ('ROUNDEDCORNERS',[4,4,4,4]),
    ]))
    return t


def _kpi_row(items):
    """items = list of (label, valore, colore_hex)"""
    n   = len(items)
    cw  = CW / n
    vals = [Paragraph(str(v), _s('kv', fontName='Helvetica-Bold', fontSize=13,
                                  textColor=colors.HexColor(c),
                                  alignment=TA_CENTER, leading=17))
            for _, v, c in items]
    lbls = [Paragraph(l, _s('kl', fontSize=7, textColor=C_GRAY,
                              alignment=TA_CENTER, leading=10))
            for l, _, _ in items]
    t = Table([vals, lbls], colWidths=[cw]*n)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_LIGHT),
        ('BOX',           (0,0),(-1,-1), 0.5, colors.HexColor('#BFDBFE')),
        ('INNERGRID',     (0,0),(-1,-1), 0.3, colors.HexColor('#DBEAFE')),
        ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('ROUNDEDCORNERS',[6,6,6,6]),
    ]))
    return t


def _ai_box(label, text, bg='#F0FDFA', border='#0E7490'):
    inner = Table([[
        Paragraph(f'🤖 {label}',
                  _s('ail', fontName='Helvetica-Bold', fontSize=7.5,
                     textColor=colors.HexColor(border), letterSpacing=0.6)),
        Paragraph(text or '—',
                  _s('aib', fontSize=8, leading=12.5, alignment=TA_JUSTIFY)),
    ]], colWidths=[CW*0.20, CW*0.76])
    inner.setStyle(TableStyle([
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 2),
        ('BOTTOMPADDING', (0,0),(-1,-1), 2),
    ]))
    box = Table([[inner]], colWidths=[CW])
    box.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), colors.HexColor(bg)),
        ('BOX',           (0,0),(-1,-1), 1, colors.HexColor(border)),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
        ('ROUNDEDCORNERS',[6,6,6,6]),
    ]))
    return box


def _info_table(rows_data, col_widths=None):
    """Tabella 2-colonne label/valore con righe alternate"""
    col_widths = col_widths or [CW*0.30, CW*0.70]
    rows = [[Paragraph(f'<b>{k}</b>', _s('ik', fontSize=8.5, fontName='Helvetica-Bold')),
             Paragraph(str(v), _s('iv', fontSize=8.5))]
            for k, v in rows_data]
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0),(-1,-1), [C_LIGHT, C_WHITE]),
        ('TOPPADDING',     (0,0),(-1,-1), 5),
        ('BOTTOMPADDING',  (0,0),(-1,-1), 5),
        ('LEFTPADDING',    (0,0),(-1,-1), 10),
        ('RIGHTPADDING',   (0,0),(-1,-1), 10),
        ('BOX',            (0,0),(-1,-1), 0.8, colors.HexColor('#BFDBFE')),
        ('INNERGRID',      (0,0),(-1,-1), 0.3, C_LGRAY),
        ('ROUNDEDCORNERS', [4,4,4,4]),
    ]))
    return t


# ─── CLASSE DOCUMENTO CON FOOTER ──────────────────────────────────────────────

class _DocWithFooter(SimpleDocTemplate):
    """Aggiunge footer fisso su ogni pagina: logo small + dati Rotondi + n. pagina"""

    def __init__(self, buf, pratica, settings, **kw):
        self._pratica  = pratica
        self._settings = settings
        super().__init__(buf, **kw)

    def handle_pageEnd(self):
        self._draw_footer()
        super().handle_pageEnd()

    def _draw_footer(self):
        canvas = self.canv
        s      = self._settings
        p      = self._pratica
        TODAY  = datetime.date.today().strftime('%d/%m/%Y')

        canvas.saveState()
        y_line = FOOTER_H + 0.2*cm

        # Linea divisoria
        canvas.setStrokeColor(C_LGRAY)
        canvas.setLineWidth(0.5)
        canvas.line(M, y_line, W - M, y_line)

        # Sfondo footer
        canvas.setFillColor(C_NAVY)
        canvas.rect(0, 0, W, FOOTER_H, fill=1, stroke=0)

        # Testo footer sx
        brand = (s.brand_name if s else 'BIOLavaTU') or 'BIOLavaTU'
        addr  = (s.company_addr if s else '') or 'Via Trieste 2, 20019 Settimo Milanese (MI)'
        web   = (s.company_web if s else '') or 'www.biolavatu.it'
        tel   = (s.company_tel if s else '') or ''
        footer_left = f"{brand}  ·  {addr}  ·  {web}{('  ·  ' + tel) if tel else ''}"

        canvas.setFillColor(C_WHITE)
        canvas.setFont('Helvetica', 6.5)
        canvas.drawString(M, 0.38*cm, footer_left)

        # N° pratica + data centro
        canvas.setFont('Helvetica', 6.5)
        canvas.setFillColor(colors.HexColor('#93C5FD'))
        mid_text = f"Pratica N° {p.numero}  ·  {TODAY}"
        canvas.drawCentredString(W/2, 0.38*cm, mid_text)

        # Numero pagina dx
        canvas.setFont('Helvetica-Bold', 7)
        canvas.setFillColor(colors.HexColor('#FCA5A5'))
        pg = self.page
        canvas.drawRightString(W - M, 0.38*cm, f"Pag. {pg}")

        # Logo BIOLavaTU piccolo a dx (se disponibile)
        logo_path = _get_logo_path()
        if logo_path:
            try:
                logo_h = FOOTER_H * 0.72
                logo_w = logo_h  # quadrato
                canvas.drawImage(
                    logo_path,
                    W - M - logo_w - 1.8*cm, 0.12*cm,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask='auto'
                )
            except Exception:
                pass

        canvas.restoreState()


# ─── BUILD PRINCIPALE ─────────────────────────────────────────────────────────

def build_pdf(pratica, settings):
    """Genera il PDF completo. Ritorna BytesIO."""
    buf  = io.BytesIO()
    p    = pratica
    s    = settings
    c    = getattr(pratica, 'cliente', None)
    TODAY_LONG  = datetime.date.today().strftime('%d %B %Y')
    TODAY_SHORT = datetime.date.today().strftime('%d/%m/%Y')

    # Colori da settings (con fallback)
    BLU  = colors.HexColor(s.color_primary if s else '#1B4F72')
    ACC  = colors.HexColor(s.color_accent  if s else '#C15E59')

    doc = _DocWithFooter(
        buf, pratica, settings,
        pagesize=A4,
        leftMargin=M, rightMargin=M,
        topMargin=1.0*cm, bottomMargin=FOOTER_H + 0.7*cm,
    )
    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 1 — COPERTINA
    # ══════════════════════════════════════════════════════════════════════════
    brand_name = (s.brand_name if s else 'BIOLavaTU') or 'BIOLavaTU'
    cliente_nome = (c.nome if c else '—') or '—'
    sc = float(p.score_zona or 0)
    sc_c = ('#059669' if sc >= 8 else '#D97706' if sc >= 6 else '#EF4444')
    sc_t = p.score_label or ('OTTIMA' if sc >= 8 else 'BUONA' if sc >= 6 else 'DIFFICILE')

    # Blocco copertina navy full-width
    def _cov_row(content):
        t = Table([[content]], colWidths=[CW])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
            ('LEFTPADDING',   (0,0),(-1,-1), 0),
            ('RIGHTPADDING',  (0,0),(-1,-1), 0),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ]))
        return t

    # Badge sopra il titolo
    story.append(Table([[
        Paragraph('STUDIO DI FATTIBILITÀ · PREVENTIVO · CONTRATTO DI FORNITURA',
                  _s('cv0', fontName='Helvetica-Bold', fontSize=8,
                     textColor=colors.HexColor('#F59E0B'),
                     alignment=TA_CENTER, letterSpacing=1.5, leading=12))
    ]], colWidths=[CW], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
        ('TOPPADDING',    (0,0),(-1,-1), 28),
        ('BOTTOMPADDING', (0,0),(-1,-1), 12),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ])))

    # Titolo principale
    story.append(Table([[
        Paragraph('PROGETTO', _s('cvt1', fontName='Helvetica-Bold', fontSize=11,
                                  textColor=colors.HexColor('#93C5FD'),
                                  alignment=TA_CENTER, letterSpacing=4, leading=14)),
    ]], colWidths=[CW], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ])))
    story.append(Table([[
        Paragraph('Lavanderia Self-Service',
                  _s('cvt2', fontName='Helvetica-Bold', fontSize=32,
                     textColor=C_WHITE, alignment=TA_CENTER, leading=38)),
    ]], colWidths=[CW], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ])))
    story.append(Table([[
        Paragraph('ECOCOMPATIBILE',
                  _s('cvt3', fontName='Helvetica-Bold', fontSize=18,
                     textColor=colors.HexColor('#34D399'),
                     alignment=TA_CENTER, letterSpacing=5, leading=24)),
    ]], colWidths=[CW], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 18),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ])))

    # Linea decorativa oro
    story.append(Table([['']], colWidths=[CW*0.5],
        style=TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), colors.HexColor('#D97706')),
            ('TOPPADDING',    (0,0),(-1,-1), 1.5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 1.5),
            ('LEFTPADDING',   (0,0),(-1,-1), 0),
            ('RIGHTPADDING',  (0,0),(-1,-1), 0),
        ])))
    story.append(sp(4))

    # Nome cliente in oro
    story.append(Table([[
        Paragraph(f'Preparato per:  <b>{cliente_nome.upper()}</b>',
                  _s('cvcli', fontSize=13, fontName='Helvetica-Bold',
                     textColor=colors.HexColor('#FCD34D'),
                     alignment=TA_CENTER, leading=18)),
    ]], colWidths=[CW], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ])))
    story.append(Table([[
        Paragraph(f'{p.indirizzo or ""} — {p.citta or ""}',
                  _s('cvadr', fontSize=9, textColor=colors.HexColor('#93C5FD'),
                     alignment=TA_CENTER, leading=13)),
    ]], colWidths=[CW], style=TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 20),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ])))

    # 3 KPI copertina
    capex_str   = f"€ {int(p.capex or 0):,}".replace(',', '.')
    incasso_str = f"€ {int(p.incasso_mese or 0):,}/m".replace(',', '.')
    score_str   = f"{sc}/10 — {sc_t}"
    kpi_cov = Table([[
        Table([[
            Paragraph('INVESTIMENTO', _s('k1l', fontSize=7, textColor=colors.HexColor('#93C5FD'),
                                         alignment=TA_CENTER, letterSpacing=0.8)),
            Paragraph(capex_str, _s('k1v', fontName='Helvetica-Bold', fontSize=14,
                                     textColor=C_WHITE, alignment=TA_CENTER, leading=18)),
        ]], colWidths=[CW/3-4], style=TableStyle([
            ('BACKGROUND', (0,0),(-1,-1), C_NAVY),
            ('TOPPADDING', (0,0),(-1,-1), 4), ('BOTTOMPADDING', (0,0),(-1,-1), 4),
            ('LEFTPADDING', (0,0),(-1,-1), 4), ('RIGHTPADDING', (0,0),(-1,-1), 4),
        ])),
        Table([[
            Paragraph('INCASSO MENSILE', _s('k2l', fontSize=7, textColor=colors.HexColor('#93C5FD'),
                                             alignment=TA_CENTER, letterSpacing=0.8)),
            Paragraph(incasso_str, _s('k2v', fontName='Helvetica-Bold', fontSize=14,
                                       textColor=colors.HexColor('#34D399'),
                                       alignment=TA_CENTER, leading=18)),
        ]], colWidths=[CW/3-4], style=TableStyle([
            ('BACKGROUND', (0,0),(-1,-1), C_NAVY),
            ('TOPPADDING', (0,0),(-1,-1), 4), ('BOTTOMPADDING', (0,0),(-1,-1), 4),
            ('LEFTPADDING', (0,0),(-1,-1), 4), ('RIGHTPADDING', (0,0),(-1,-1), 4),
        ])),
        Table([[
            Paragraph('SCORE ZONA', _s('k3l', fontSize=7, textColor=colors.HexColor('#93C5FD'),
                                        alignment=TA_CENTER, letterSpacing=0.8)),
            Paragraph(score_str, _s('k3v', fontName='Helvetica-Bold', fontSize=12,
                                     textColor=colors.HexColor(sc_c),
                                     alignment=TA_CENTER, leading=16)),
        ]], colWidths=[CW/3-4], style=TableStyle([
            ('BACKGROUND', (0,0),(-1,-1), C_NAVY),
            ('TOPPADDING', (0,0),(-1,-1), 4), ('BOTTOMPADDING', (0,0),(-1,-1), 4),
            ('LEFTPADDING', (0,0),(-1,-1), 4), ('RIGHTPADDING', (0,0),(-1,-1), 4),
        ])),
    ]], colWidths=[CW/3, CW/3, CW/3])
    kpi_cov.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), colors.HexColor('#112240')),
        ('BOX',           (0,0),(-1,-1), 1, colors.HexColor('#1E3A5F')),
        ('INNERGRID',     (0,0),(-1,-1), 0.5, colors.HexColor('#1E3A5F')),
        ('TOPPADDING',    (0,0),(-1,-1), 12),
        ('BOTTOMPADDING', (0,0),(-1,-1), 12),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
        ('RIGHTPADDING',  (0,0),(-1,-1), 8),
    ]))
    story.append(kpi_cov)
    story.append(sp(16))

    # Logo BIOLavaTU in basso copertina
    logo_path = _get_logo_path()
    if logo_path:
        logo_img = Image(logo_path, width=5.5*cm, height=5.5*cm, kind='proportional')
        logo_wrap = Table([[logo_img]], colWidths=[CW])
        logo_wrap.setStyle(TableStyle([
            ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 14),
        ]))
        story.append(logo_wrap)
    else:
        story.append(Table([[
            Paragraph(brand_name, _s('cvbr', fontName='Helvetica-Bold', fontSize=22,
                                      textColor=colors.HexColor('#34D399'),
                                      alignment=TA_CENTER, leading=28)),
            Paragraph('LAVANDERIA AUTOMATICA ECOCOMPATIBILE',
                      _s('cvsub', fontSize=8, textColor=colors.HexColor('#93C5FD'),
                         alignment=TA_CENTER, letterSpacing=1)),
        ]], colWidths=[CW], style=TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), C_NAVY),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 20),
            ('LEFTPADDING',   (0,0),(-1,-1), 0),
            ('RIGHTPADDING',  (0,0),(-1,-1), 0),
        ])))

    # Data e numero documento
    story.append(Table([[
        Paragraph(f'N° {p.numero}  ·  Data: {TODAY_LONG}  ·  Documento riservato e confidenziale',
                  _s('cvdate', fontSize=8, textColor=C_GRAY, alignment=TA_CENTER, leading=12)),
    ]], colWidths=[CW], style=TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
    ])))

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 2 — LETTERA DI PRESENTAZIONE AI
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    story.append(_section_bar('✉  LETTERA DI PRESENTAZIONE — Redatta da BIOLavaTU AI per questo progetto',
                               bg=C_BLU))
    story.append(sp(14))

    lettera = (p.lettera_presentazione or '').strip()
    if lettera:
        # Parsing paragrafi dalla lettera AI
        # Rimuovi markdown se presente
        import re
        clean = re.sub(r'\*\*(.*?)\*\*', r'\1', lettera)
        clean = re.sub(r'\*(.*?)\*', r'\1', clean)
        clean = re.sub(r'#{1,4}\s*', '', clean)
        clean = re.sub(r'^[-•]\s*', '', clean, flags=re.MULTILINE)

        paragraphs = [p_txt.strip() for p_txt in clean.split('\n\n') if p_txt.strip()]
        for i, par in enumerate(paragraphs):
            if i == 0:
                # Prima riga: eventuale "Gentile X,"
                story.append(Paragraph(par, _s('lp0', fontSize=11, fontName='Helvetica-Bold',
                                                leading=15, spaceBefore=0, spaceAfter=8)))
            elif par.startswith('Con i migliori') or par.startswith('Cordiali') or par.startswith('Distinti'):
                # Chiusura lettera
                story.append(sp(12))
                story.append(Paragraph(par, _s('lpclose', fontSize=9, leading=13, spaceAfter=4)))
            else:
                story.append(Paragraph(par, _s(f'lp{i}', fontSize=9, leading=14,
                                                 alignment=TA_JUSTIFY, spaceAfter=6)))
    else:
        story.append(_ai_box(
            'LETTERA AI',
            'Lettera di presentazione non ancora generata. '
            'Torna alla pratica, step 6 Riepilogo, e clicca "Genera Analisi AI" per crearla.',
            '#FFFBEB', '#D97706'
        ))

    story.append(sp(20))

    # Firma lettera
    firma_lett = Table([[
        Table([[
            Paragraph('Cordialmente,', _s('fl0', fontSize=9, textColor=C_GRAY, leading=13)),
            sp(8),
            Paragraph('<b>Rotondi Group Srl</b>',
                      _s('fl1', fontName='Helvetica-Bold', fontSize=11, leading=14)),
            Paragraph('BIOLavaTU — Lavanderia Automatica Ecocompatibile',
                      _s('fl2', fontSize=8.5, textColor=C_TEAL, leading=12)),
            Paragraph((s.company_addr if s else '') or 'Via Trieste 2, 20019 Settimo Milanese (MI)',
                      _s('fl3', fontSize=8, textColor=C_GRAY, leading=12)),
            Paragraph((s.company_web if s else '') or 'www.biolavatu.it',
                      _s('fl4', fontSize=8, textColor=C_BLU, leading=12)),
        ]], colWidths=[CW*0.48]),
        Table([[
            sp(40),
            HRFlowable(width=CW*0.38, thickness=0.7, color=C_LGRAY),
            Paragraph('Firma autorizzata', _s('fls', fontSize=8, textColor=C_GRAY,
                                               alignment=TA_CENTER, leading=12)),
            sp(6),
            HRFlowable(width=CW*0.38, thickness=0.7, color=C_LGRAY),
            Paragraph('Timbro aziendale', _s('flt', fontSize=8, textColor=C_GRAY,
                                              alignment=TA_CENTER, leading=12)),
        ]], colWidths=[CW*0.45]),
    ]], colWidths=[CW*0.52, CW*0.48])
    firma_lett.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(1,0),(1,0),16)]))
    story.append(firma_lett)

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 3-4 — ANALISI DI ZONA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_section_bar('📍  ANALISI DI ZONA E GEOLOCALIZZAZIONE', bg=C_TEAL))
    story.append(sp(10))

    # KPI zona
    conc_n   = getattr(p, 'concorrenti_500m', 0) or 0
    servizi  = getattr(p, 'servizi_400m', 0) or 0
    story.append(_kpi_row([
        ('Pop. 3 min a piedi', f"~{int(p.pop_3min or 0):,}".replace(',','.'), '#059669'),
        ('Pop. 5 min a piedi', f"~{int(p.pop_5min or 0):,}".replace(',','.'), '#10B981'),
        ('Pop. 10 min a piedi',f"~{int(p.pop_10min or 0):,}".replace(',','.'), '#34D399'),
        ('Concorrenti 500m',   '✓ Nessuno' if conc_n==0 else str(conc_n),
         '#059669' if conc_n==0 else '#D97706'),
        ('Servizi attrattori', str(servizi), '#0E7490'),
        ('Score Zona',         f'{sc}/10', sc_c),
    ]))
    story.append(sp(10))

    # Mappa Google Static (se foto_mappa salvata)
    if getattr(p, 'foto_mappa', None) and os.path.exists(p.foto_mappa):
        try:
            map_img = Image(p.foto_mappa, width=CW, height=6*cm, kind='proportional')
            map_wrap = Table([[map_img]], colWidths=[CW])
            map_wrap.setStyle(TableStyle([
                ('ALIGN', (0,0),(-1,-1), 'CENTER'),
                ('BOX',   (0,0),(-1,-1), 0.5, C_LGRAY),
                ('ROUNDEDCORNERS', [4,4,4,4]),
            ]))
            story.append(map_wrap)
            story.append(sp(8))
        except Exception:
            pass

    # Dati ISTAT
    zona_info = {}
    if getattr(p, 'zona_info_raw', None):
        try:
            import json
            zona_info = json.loads(p.zona_info_raw)
        except Exception:
            pass

    if zona_info:
        story.append(_section_bar('DATI DEMOGRAFICI ISTAT 2023', bg=C_TEAL))
        story.append(sp(6))
        istat_rows = []
        if zona_info.get('perc_stranieri'):
            istat_rows.append(('Popolazione straniera', f"{zona_info['perc_stranieri']:.1f}%"))
        if zona_info.get('reddito_medio'):
            istat_rows.append(('Reddito medio dichiarato', f"€ {int(zona_info['reddito_medio']):,}/anno".replace(',','.')))
        if zona_info.get('indice_affollamento'):
            istat_rows.append(('Indice affollamento abitazioni', f"{zona_info['indice_affollamento']:.2f}"))
        if zona_info.get('perc_affittuari'):
            istat_rows.append(('% inquilini in affitto', f"{zona_info['perc_affittuari']:.1f}%"))
        if zona_info.get('eta_media'):
            istat_rows.append(('Età media popolazione', f"{zona_info['eta_media']:.1f} anni"))
        if istat_rows:
            story.append(_info_table(istat_rows, [CW*0.45, CW*0.55]))
            story.append(sp(10))

    # Analisi AI zona
    if getattr(p, 'ai_zona', None):
        story.append(_section_bar('ANALISI AI TERRITORIALE — Elaborata da Claude', bg=C_TEAL))
        story.append(sp(6))
        story.append(_ai_box('ANALISI AI ZONA', p.ai_zona, '#F0FDFA', '#0E7490'))
        story.append(sp(10))

    # Concorrenti
    competitors = p.get_competitors() if hasattr(p, 'get_competitors') else []
    if competitors:
        story.append(PageBreak())
        story.append(_section_bar(
            f'CONCORRENTI RILEVATI ENTRO 600m — {len(competitors)} trovati',
            bg=colors.HexColor('#7C3AED')
        ))
        story.append(sp(6))
        hdr = [Paragraph(h, _s(f'ch{i}', fontName='Helvetica-Bold', fontSize=8, textColor=C_WHITE))
               for i, h in enumerate(['Nome', 'Indirizzo', 'Distanza', 'Rating'])]
        rows_c = [hdr]
        for comp in competitors:
            dist_m = comp.get('dist_m', 0) or 0
            rows_c.append([
                Paragraph(comp.get('name','—'), _s('cdn', fontSize=8, fontName='Helvetica-Bold')),
                Paragraph(comp.get('address', comp.get('vicinity','—')),
                          _s('cda', fontSize=7.5, textColor=C_GRAY)),
                Paragraph(f"{dist_m}m (~{dist_m//80} min)",
                          _s('cdd', fontSize=8, alignment=TA_CENTER)),
                Paragraph(str(comp.get('rating','—')),
                          _s('cdr', fontSize=8, alignment=TA_CENTER,
                             textColor=C_GREEN if float(comp.get('rating',0) or 0) >= 4 else C_GOLD)),
            ])
        ct = Table(rows_c, colWidths=[CW*0.34, CW*0.36, CW*0.18, CW*0.12])
        ct.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,0), colors.HexColor('#7C3AED')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.HexColor('#FAF5FF'), C_WHITE]),
            ('ALIGN',         (2,0),(-1,-1), 'CENTER'),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('RIGHTPADDING',  (0,0),(-1,-1), 8),
            ('GRID',          (0,0),(-1,-1), 0.3, C_LGRAY),
            ('BOX',           (0,0),(-1,-1), 0.8, C_GRAY),
        ]))
        story.append(ct)

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 5 — BUSINESS PLAN
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_section_bar('💰  BUSINESS PLAN — PROIEZIONE ECONOMICA', bg=C_GREEN))
    story.append(sp(10))

    # KPI economici
    utile = float(p.utile_mese or 0)
    story.append(_kpi_row([
        ('Investimento CAPEX',  f"€ {int(p.capex or 0):,}".replace(',','.'), '#1B4F72'),
        ('Incasso / mese',      f"€ {int(p.incasso_mese or 0):,}".replace(',','.'), '#059669'),
        ('Costi fissi / mese',  f"€ {int(p.costi_mese or 0):,}".replace(',','.'), '#C15E59'),
        ('Utile netto / mese',  f"€ {int(utile):,}".replace(',','.'),
         '#059669' if utile >= 0 else '#EF4444'),
        ('Payback stimato',
         f"{p.payback_mesi:.1f} mesi" if p.payback_mesi and p.payback_mesi < 999 else 'N/D',
         '#D97706'),
        ('Break-even',
         f"Mese {int(p.payback_mesi)+1}" if p.payback_mesi and p.payback_mesi < 999 else 'N/D',
         '#D97706'),
    ]))
    story.append(sp(10))

    # Formula incasso
    story.append(_section_bar('FORMULA DI CALCOLO INCASSO', bg=C_BLU))
    story.append(sp(6))
    formula_rows = [
        ('Cicli lavaggio piccolo', f"€ {p.tariffa_lavaggio_std or 6:.2f} / ciclo"),
        ('Cicli lavaggio medio',   f"€ {p.tariffa_lavaggio_med or 8:.2f} / ciclo"),
        ('Cicli lavaggio grande',  f"€ {p.tariffa_lavaggio_grd or 10:.2f} / ciclo"),
        ('Asciugatura',            f"€ {p.tariffa_asciugatura or 1:.2f} / ciclo × ~3 cicli/cliente"),
        ('Cicli max lavaggio',     '18 cicli/macchina/giorno (14 ore, 45 min/ciclo)'),
        ('Cicli max asciugatura',  '52 cicli/macchina/giorno (14 ore, 16 min/ciclo)'),
        ('Apertura annua',         '365 giorni, 12–14 ore/giorno'),
        ('Scenario applicato',     (p.scenario or 'realistico').upper()),
    ]
    story.append(_info_table(formula_rows))
    story.append(sp(10))

    # 3 Scenari
    story.append(_section_bar('3 SCENARI DI BUSINESS', bg=C_BLU))
    story.append(sp(6))
    inc_base = float(p.incasso_mese or 0)
    cos_base = float(p.costi_mese or 0)
    scenarios = [
        ('PESSIMISTICO', inc_base * 0.70, cos_base, colors.HexColor('#FEE2E2'), C_RED),
        ('REALISTICO',   inc_base,          cos_base, colors.HexColor('#ECFDF5'), C_GREEN),
        ('OTTIMISTICO',  inc_base * 1.30,  cos_base, colors.HexColor('#EFF6FF'), C_BLU),
    ]
    sc_rows = [[Paragraph(h, _s(f'sch{i}', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_WHITE))
                for i, h in enumerate(['SCENARIO','INCASSO/MESE','COSTI/MESE','UTILE NETTO','ROI ANNUO'])]]
    for nome, inc_s, cos_s, bg_c, txt_c in scenarios:
        utile_s = inc_s - cos_s
        roi = (utile_s * 12 / (p.capex or 1)) * 100 if p.capex else 0
        sc_rows.append([
            Paragraph(f'<b>{nome}</b>', _s(f'sn{nome}', fontName='Helvetica-Bold',
                                             fontSize=8.5, textColor=txt_c)),
            Paragraph(f"€ {int(inc_s):,}".replace(',','.'),
                      _s(f'si{nome}', fontSize=9, fontName='Helvetica-Bold',
                         textColor=txt_c, alignment=TA_RIGHT)),
            Paragraph(f"€ {int(cos_s):,}".replace(',','.'),
                      _s(f'sc{nome}', fontSize=8.5, textColor=C_RED, alignment=TA_RIGHT)),
            Paragraph(f"€ {int(utile_s):,}".replace(',','.'),
                      _s(f'su{nome}', fontName='Helvetica-Bold', fontSize=9,
                         textColor=C_GREEN if utile_s>=0 else C_RED, alignment=TA_RIGHT)),
            Paragraph(f"{roi:.1f}%",
                      _s(f'sr{nome}', fontName='Helvetica-Bold', fontSize=9,
                         textColor=txt_c, alignment=TA_CENTER)),
        ])
    sc_tab = Table(sc_rows, colWidths=[CW*0.25, CW*0.20, CW*0.20, CW*0.20, CW*0.15])
    sc_tab.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), C_DARK),
        ('BACKGROUND',    (0,1),(0,1), colors.HexColor('#FEE2E2')),
        ('BACKGROUND',    (0,2),(0,2), colors.HexColor('#ECFDF5')),
        ('BACKGROUND',    (0,3),(0,3), colors.HexColor('#EFF6FF')),
        ('ALIGN',         (1,0),(-1,-1), 'RIGHT'),
        ('ALIGN',         (4,0),(4,-1), 'CENTER'),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 7),
        ('BOTTOMPADDING', (0,0),(-1,-1), 7),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
        ('GRID',          (0,0),(-1,-1), 0.4, C_LGRAY),
        ('BOX',           (0,0),(-1,-1), 1, C_BLU),
        ('ROUNDEDCORNERS',[6,6,6,6]),
    ]))
    story.append(sc_tab)
    story.append(sp(8))

    if getattr(p, 'ai_bp', None):
        story.append(_ai_box('ANALISI AI BUSINESS PLAN', p.ai_bp, '#F0FDF4', '#059669'))
        story.append(sp(6))
    if getattr(p, 'ai_risk', None):
        story.append(_ai_box('ANALISI RISCHI', p.ai_risk, '#FFFBEB', '#D97706'))

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 6 — ORDINE MACCHINE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_section_bar('🛒  ORDINE MACCHINE — CONFIGURAZIONE PROPOSTA', bg=C_BLU))
    story.append(sp(6))

    # Dati cliente / fornitore intestazione ordine
    ord_header = Table([[
        Table([
            [Paragraph('FORNITORE', _s('ofh', fontName='Helvetica-Bold', fontSize=7,
                                        textColor=C_TEAL, letterSpacing=0.8))],
            [Paragraph('<b>Rotondi Group Srl</b>',
                       _s('ofn', fontName='Helvetica-Bold', fontSize=10, leading=13))],
            [Paragraph((s.company_addr if s else '') or 'Via Trieste 2, 20019 Settimo Milanese (MI)',
                       _s('ofa', fontSize=8, textColor=C_GRAY, leading=11))],
            [Paragraph((s.company_piva if s else '') or 'P.IVA 04XXXXXXXX',
                       _s('ofp', fontSize=8, textColor=C_GRAY, leading=11))],
        ], colWidths=[CW*0.44]),
        Table([
            [Paragraph('CLIENTE / DESTINATARIO', _s('och', fontName='Helvetica-Bold', fontSize=7,
                                                     textColor=C_GREEN, letterSpacing=0.8))],
            [Paragraph(f'<b>{cliente_nome}</b>',
                       _s('ocn', fontName='Helvetica-Bold', fontSize=10, leading=13))],
            [Paragraph(f"C.F./P.IVA: {(c.piva if c else '') or '—'}",
                       _s('ocp', fontSize=8, textColor=C_GRAY, leading=11))],
            [Paragraph(f"Sede lavanderia: {p.indirizzo or ''}, {p.citta or ''}",
                       _s('ocs', fontSize=8, textColor=C_GRAY, leading=11))],
        ], colWidths=[CW*0.44]),
    ]], colWidths=[CW*0.50, CW*0.50])
    ord_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(0,0), colors.HexColor('#EFF6FF')),
        ('BACKGROUND', (1,0),(1,0), colors.HexColor('#F0FDF4')),
        ('BOX',        (0,0),(0,0), 0.8, C_TEAL),
        ('BOX',        (1,0),(1,0), 0.8, C_GREEN),
        ('TOPPADDING',    (0,0),(-1,-1), 10),
        ('BOTTOMPADDING', (0,0),(-1,-1), 10),
        ('LEFTPADDING',   (0,0),(-1,-1), 12),
        ('RIGHTPADDING',  (0,0),(-1,-1), 12),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('ROUNDEDCORNERS',[6,6,6,6]),
    ]))
    story.append(ord_header)
    story.append(sp(10))

    # Tabella macchine SENZA prezzi unitari — solo qty + totale
    macchine = [m for m in (p.get_macchine() if hasattr(p,'get_macchine') else [])
                if int(m.get('qty',0)) > 0]
    story.append(_section_bar('DETTAGLIO ARTICOLI', bg=C_BLU))
    story.append(sp(4))

    hdr_mac = [Paragraph(h, _s(f'mh{i}', fontName='Helvetica-Bold', fontSize=8.5, textColor=C_WHITE))
               for i, h in enumerate(['N°', 'Descrizione articolo', 'Modello / Codice', 'Qty', 'Totale'])]
    rows_mac = [hdr_mac]
    for idx, m in enumerate(macchine, 1):
        prezzo = float(m.get('prezzo', 0) or 0)
        qty    = int(m.get('qty', 0) or 0)
        tot    = prezzo * qty
        rows_mac.append([
            Paragraph(str(idx), _s(f'mi{idx}', fontSize=9, alignment=TA_CENTER)),
            Table([[
                Paragraph(f"<b>{m.get('nome','')}</b>",
                          _s(f'mnn{idx}', fontName='Helvetica-Bold', fontSize=9, leading=13)),
                Paragraph(m.get('descrizione', m.get('sub', '')),
                          _s(f'mds{idx}', fontSize=7.5, textColor=C_GRAY, leading=11)),
            ]], colWidths=[CW*0.38]),
            Paragraph(m.get('modello', m.get('sub', '—')),
                      _s(f'mmod{idx}', fontSize=8, textColor=C_GRAY, alignment=TA_CENTER)),
            Paragraph(f'<b>{qty}</b>', _s(f'mqt{idx}', fontName='Helvetica-Bold',
                                           fontSize=11, textColor=C_TEAL, alignment=TA_CENTER)),
            Paragraph(f"<b>€ {int(tot):,}</b>".replace(',','.'),
                      _s(f'mtot{idx}', fontName='Helvetica-Bold', fontSize=9,
                         textColor=C_BLU, alignment=TA_RIGHT)),
        ])

    # Riga totale imponibile
    imponibile = int(p.capex or 0)
    iva        = int(imponibile * 0.22)
    totale_iva = imponibile + iva

    rows_mac.append([
        Paragraph('', _s('msp', fontSize=8)), '', '', '',
        Paragraph('', _s('msp2', fontSize=8)),
    ])
    rows_mac.append([
        Paragraph('', _s('mbl', fontSize=8)),
        Paragraph('<b>TOTALE IMPONIBILE</b>',
                  _s('mtilab', fontName='Helvetica-Bold', fontSize=9, textColor=C_DARK)),
        '', '',
        Paragraph(f"<b>€ {imponibile:,}</b>".replace(',','.'),
                  _s('mtiv', fontName='Helvetica-Bold', fontSize=10,
                     textColor=C_DARK, alignment=TA_RIGHT)),
    ])
    rows_mac.append([
        Paragraph('', _s('mbl2', fontSize=8)),
        Paragraph('IVA 22%',
                  _s('mivalab', fontSize=9, textColor=C_GRAY)),
        '', '',
        Paragraph(f"€ {iva:,}".replace(',','.'),
                  _s('miva', fontSize=9, textColor=C_GRAY, alignment=TA_RIGHT)),
    ])
    rows_mac.append([
        Paragraph('', _s('mbl3', fontSize=8)),
        Paragraph('<b>TOTALE IVA INCLUSA</b>',
                  _s('mtotlab', fontName='Helvetica-Bold', fontSize=11,
                     textColor=C_WHITE)),
        '', '',
        Paragraph(f"<b>€ {totale_iva:,}</b>".replace(',','.'),
                  _s('mtotval', fontName='Helvetica-Bold', fontSize=13,
                     textColor=C_WHITE, alignment=TA_RIGHT)),
    ])

    mac_tab = Table(rows_mac,
                    colWidths=[CW*0.06, CW*0.40, CW*0.16, CW*0.09, CW*0.19])
    n_data = len(rows_mac)
    mac_tab.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),   C_BLU),
        ('ROWBACKGROUNDS',(0,1), (-1,-5),  [C_LIGHT, C_WHITE]),
        ('BACKGROUND',    (0,-3),(-1,-3),  colors.HexColor('#F8FAFC')),
        ('BACKGROUND',    (1,-2),(4,-2),   colors.HexColor('#FEF3C7')),
        ('BACKGROUND',    (1,-1),(4,-1),   C_DARK),
        ('SPAN',          (1,-2),(3,-2)),
        ('SPAN',          (1,-1),(3,-1)),
        ('SPAN',          (1,-3),(3,-3)),
        ('ALIGN',         (3,0), (-1,-1),  'RIGHT'),
        ('ALIGN',         (0,0), (0,-1),   'CENTER'),
        ('ALIGN',         (2,0), (2,-1),   'CENTER'),
        ('VALIGN',        (0,0), (-1,-1),  'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1),  5),
        ('BOTTOMPADDING', (0,0), (-1,-1),  5),
        ('LEFTPADDING',   (0,0), (-1,-1),  8),
        ('RIGHTPADDING',  (0,0), (-1,-1),  8),
        ('GRID',          (0,0), (-1,-4),  0.3, C_LGRAY),
        ('BOX',           (0,0), (-1,-1),  0.8, C_BLU),
        ('LINEABOVE',     (0,-3),(4,-3),   1, C_LGRAY),
    ]))
    story.append(mac_tab)
    story.append(sp(10))

    # Condizioni di pagamento con importi
    story.append(_section_bar('CONDIZIONI DI PAGAMENTO', bg=C_TEAL))
    story.append(sp(6))
    pag_rows = [
        [Paragraph('<b>Acconto alla conferma ordine</b>',
                   _s('pp1', fontName='Helvetica-Bold', fontSize=9)),
         Paragraph('40%', _s('pp1p', fontName='Helvetica-Bold', fontSize=9, alignment=TA_CENTER)),
         Paragraph(f"<b>€ {int(totale_iva*0.40):,}</b>".replace(',','.'),
                   _s('pp1v', fontName='Helvetica-Bold', fontSize=10,
                      textColor=C_BLU, alignment=TA_RIGHT))],
        [Paragraph('Merce pronta alla spedizione',
                   _s('pp2', fontSize=9)),
         Paragraph('40%', _s('pp2p', fontSize=9, alignment=TA_CENTER)),
         Paragraph(f"€ {int(totale_iva*0.40):,}".replace(',','.'),
                   _s('pp2v', fontSize=9, textColor=C_BLU, alignment=TA_RIGHT))],
        [Paragraph('Consegna e scarico',
                   _s('pp3', fontSize=9)),
         Paragraph('15%', _s('pp3p', fontSize=9, alignment=TA_CENTER)),
         Paragraph(f"€ {int(totale_iva*0.15):,}".replace(',','.'),
                   _s('pp3v', fontSize=9, textColor=C_BLU, alignment=TA_RIGHT))],
        [Paragraph('Collaudo positivo certificato',
                   _s('pp4', fontSize=9)),
         Paragraph('5%', _s('pp4p', fontSize=9, alignment=TA_CENTER)),
         Paragraph(f"€ {int(totale_iva*0.05):,}".replace(',','.'),
                   _s('pp4v', fontSize=9, textColor=C_BLU, alignment=TA_RIGHT))],
    ]
    pag_tab = Table(pag_rows, colWidths=[CW*0.58, CW*0.12, CW*0.30])
    pag_tab.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0),(-1,-1), [C_LIGHT, C_WHITE]),
        ('TOPPADDING',     (0,0),(-1,-1), 7),
        ('BOTTOMPADDING',  (0,0),(-1,-1), 7),
        ('LEFTPADDING',    (0,0),(-1,-1), 12),
        ('RIGHTPADDING',   (0,0),(-1,-1), 12),
        ('ALIGN',          (1,0),(-1,-1), 'RIGHT'),
        ('BOX',            (0,0),(-1,-1), 0.8, C_TEAL),
        ('INNERGRID',      (0,0),(-1,-1), 0.3, C_LGRAY),
        ('ROUNDEDCORNERS', [6,6,6,6]),
    ]))
    story.append(pag_tab)

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 7+ — CONDIZIONI GENERALI DI VENDITA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_section_bar(
        f'📋  CONDIZIONI GENERALI DI VENDITA — {len(CGV)} ARTICOLI',
        bg=ACC
    ))
    story.append(sp(10))

    # Controlla se ci sono CGV custom in settings
    cgv_text = getattr(s, 'condizioni_vendita', None) if s else None

    if cgv_text and len(cgv_text.strip()) > 50:
        # CGV personalizzate da settings
        import re
        clean_cgv = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cgv_text)
        for par in clean_cgv.split('\n\n'):
            par = par.strip()
            if par:
                story.append(Paragraph(par, _s('cgvc', fontSize=8, leading=12.5,
                                                 alignment=TA_JUSTIFY, spaceAfter=5)))
    else:
        # CGV standard in 2 colonne
        cl_title = _s('cgt', fontName='Helvetica-Bold', fontSize=8.5,
                       textColor=C_BLU, spaceBefore=8, spaceAfter=3, leading=13)
        cl_body  = _s('cgb', fontSize=7.5, leading=11.5,
                       alignment=TA_JUSTIFY, spaceAfter=5, textColor=C_DARK)

        left_art, right_art = [], []
        for i, (title, text) in enumerate(CGV):
            col = left_art if i < 6 else right_art
            col.append(Paragraph(f'Art. {i+1} — {title}', cl_title))
            col.append(Paragraph(text, cl_body))

        def _cgv_col(items, w):
            t = Table([[item] for item in items], colWidths=[w])
            t.setStyle(TableStyle([
                ('TOPPADDING',    (0,0),(-1,-1), 1),
                ('BOTTOMPADDING', (0,0),(-1,-1), 1),
            ]))
            return t

        cgv_t = Table([[
            _cgv_col(left_art,  CW*0.472),
            _cgv_col(right_art, CW*0.472),
        ]], colWidths=[CW*0.50, CW*0.50])
        cgv_t.setStyle(TableStyle([
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            ('LEFTPADDING',   (1,0),(1,0), 12),
        ]))
        story.append(cgv_t)

    # ══════════════════════════════════════════════════════════════════════════
    # ULTIMA PAGINA — FIRME
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_section_bar('✍  SOTTOSCRIZIONE DEL CONTRATTO', bg=C_BLU))
    story.append(sp(10))

    # Riepilogo finale
    riepilogo_rows = [
        ('Committente',        cliente_nome),
        ('Fornitore',          (s.brand_name if s else 'BIOLavaTU by Rotondi Group Srl') or 'BIOLavaTU by Rotondi Group Srl'),
        ('Sede lavanderia',    f"{p.indirizzo or ''}, {p.citta or ''}"),
        ('Investimento totale (IVA incl.)', f"€ {totale_iva:,}".replace(',','.')),
        ('Numero documento',   p.numero),
        ('Data',               TODAY_LONG),
    ]
    story.append(_info_table(riepilogo_rows))
    story.append(sp(16))
    story.append(HRFlowable(width=CW, thickness=1.5, color=C_DARK))
    story.append(sp(14))

    # Blocchi firma
    def _firma_block(titolo, nome, color_hex):
        rows = [
            [Paragraph(titolo, _s(f'ft_{titolo[:3]}', fontName='Helvetica-Bold', fontSize=7.5,
                                   textColor=colors.HexColor(color_hex), letterSpacing=0.8))],
            [Paragraph(f'<b>{nome}</b>', _s(f'fn_{titolo[:3]}', fontName='Helvetica-Bold',
                                             fontSize=11, textColor=C_DARK, leading=14))],
            [sp(36)],
            [HRFlowable(width=CW*0.38, thickness=0.8, color=C_LGRAY)],
            [Paragraph('Firma e timbro', _s(f'ffs_{titolo[:3]}', fontSize=8,
                                             alignment=TA_CENTER, textColor=C_GRAY))],
            [sp(10)],
            [HRFlowable(width=CW*0.38, thickness=0.8, color=C_LGRAY)],
            [Paragraph('Data: ___________________________',
                       _s(f'ffd_{titolo[:3]}', fontSize=8.5, textColor=C_GRAY))],
            [sp(6)],
            [HRFlowable(width=CW*0.38, thickness=0.8, color=C_LGRAY)],
            [Paragraph('Luogo: __________________________',
                       _s(f'ffl_{titolo[:3]}', fontSize=8.5, textColor=C_GRAY))],
        ]
        t = Table(rows, colWidths=[CW*0.44])
        t.setStyle(TableStyle([
            ('TOPPADDING',    (0,0),(-1,-1), 2),
            ('BOTTOMPADDING', (0,0),(-1,-1), 2),
        ]))
        return t

    firme_t = Table([[
        _firma_block('IL FORNITORE',
                     (s.brand_name if s else 'BIOLavaTU by Rotondi Group Srl') or 'BIOLavaTU by Rotondi Group Srl',
                     '#0E7490'),
        _firma_block('IL CLIENTE', cliente_nome, '#059669'),
    ]], colWidths=[CW*0.50, CW*0.50])
    firme_t.setStyle(TableStyle([
        ('VALIGN',       (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING',  (1,0),(1,0), 20),
    ]))
    story.append(firme_t)
    story.append(sp(20))

    # ── DOPPIA FIRMA EX ART. 1341-1342 c.c. ──────────────────────────────────
    vest_inner = Table([
        [Paragraph(
            '<b>⚠  APPROVAZIONE SPECIFICA CLAUSOLE — Art. 1341-1342 c.c.</b>',
            _s('v0', fontName='Helvetica-Bold', fontSize=9,
               textColor=colors.HexColor('#D97706'), leading=13))],
        [Paragraph(
            'Ai sensi degli artt. 1341 e 1342 del Codice Civile, il Cliente dichiara di aver '
            'letto e di approvare specificamente le seguenti clausole: '
            '<b>Art. 9</b> (Limitazione della responsabilità del Fornitore); '
            '<b>Art. 11</b> (Risoluzione e clausola risolutiva espressa ex art. 1456 c.c.); '
            '<b>Art. 12</b> (Foro competente esclusivo: Tribunale di Roma).',
            _s('v1', fontSize=8.5, leading=13, textColor=colors.HexColor('#374151'),
               alignment=TA_JUSTIFY))],
        [sp(18)],
        [Table([[
            Table([
                [HRFlowable(width=CW*0.36, thickness=0.8, color=colors.HexColor('#D97706'))],
                [Paragraph('Firma del Cliente per approvazione specifica',
                           _s('vs1', fontSize=7.5, textColor=colors.HexColor('#D97706'),
                              alignment=TA_CENTER, leading=11))],
            ], colWidths=[CW*0.44]),
            Table([
                [HRFlowable(width=CW*0.36, thickness=0.8, color=colors.HexColor('#D97706'))],
                [Paragraph('Data e luogo',
                           _s('vs2', fontSize=7.5, textColor=colors.HexColor('#D97706'),
                              alignment=TA_CENTER, leading=11))],
            ], colWidths=[CW*0.44]),
        ]], colWidths=[CW*0.50, CW*0.50])],
    ], colWidths=[CW])
    vest_box = Table([[vest_inner]], colWidths=[CW])
    vest_box.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), colors.HexColor('#FFFBEB')),
        ('BOX',           (0,0),(-1,-1), 1.5, colors.HexColor('#FCD34D')),
        ('TOPPADDING',    (0,0),(-1,-1), 14),
        ('BOTTOMPADDING', (0,0),(-1,-1), 14),
        ('LEFTPADDING',   (0,0),(-1,-1), 16),
        ('RIGHTPADDING',  (0,0),(-1,-1), 16),
        ('ROUNDEDCORNERS',[8,8,8,8]),
    ]))
    story.append(vest_box)
    story.append(sp(16))

    # Nota finale
    story.append(Paragraph(
        f'Documento N° <b>{p.numero}</b> — Generato il {TODAY_LONG} da LaundryPro AI Platform · '
        f'{brand_name} · Contiene {len(CGV)} articoli CGV standard · '
        'Doppia sottoscrizione richiesta ex artt. 1341-1342 c.c. · '
        'Documento riservato e confidenziale.',
        _s('nota_fin', fontSize=7, textColor=C_GRAY, alignment=TA_CENTER, leading=11)
    ))

    # ── BUILD ──────────────────────────────────────────────────────────────────
    doc.build(story)
    buf.seek(0)
    return buf
