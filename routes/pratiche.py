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



def _geocodifica_indirizzo(indirizzo, citta, gmaps_key):
    """Geocodifica un indirizzo e restituisce (lat, lng) o (None, None)."""
    import urllib.parse as _up, urllib.request as _ur2
    tentativi = []
    if indirizzo and citta:
        tentativi.append(f"{indirizzo}, {citta}, Italia")
    if citta:
        tentativi.append(f"{citta}, Italia")
    for addr in tentativi:
        try:
            url = ("https://maps.googleapis.com/maps/api/geocode/json?address="
                   + _up.quote_plus(addr) + "&key=" + gmaps_key)
            req = _ur2.Request(url, headers={"User-Agent": "BIOLavaTU-PDF"})
            with _ur2.urlopen(req, timeout=6) as r:
                data = __import__('json').loads(r.read())
            if data.get('results'):
                loc = data['results'][0]['geometry']['location']
                return float(loc['lat']), float(loc['lng'])
        except Exception:
            continue
    return None, None


def _cerchio_path(lat, lng, raggio_m, punti=20):
    """Genera stringa path per cerchio approssimato su Google Maps Static API."""
    import math as _m
    R_lat = raggio_m / 111000
    R_lng = raggio_m / (111000 * _m.cos(_m.radians(lat)))
    pts = []
    for i in range(punti + 1):
        a = 2 * _m.pi * i / punti
        pts.append(f"{lat + R_lat*_m.sin(a):.6f},{lng + R_lng*_m.cos(a):.6f}")
    return "|".join(pts)


def _get_mappa_statica(lat, lng, gmaps_key, width_px=640, height_px=360,
                       concorrenti=None, attractors=None):
    """Mappa statica Google Maps con cerchi 3/5/10 min + markers + attractor points."""
    if not lat or not lng or not gmaps_key:
        return None
    try:
        import urllib.request as _ur

        parts = [
            f"center={lat},{lng}",
            f"zoom=14",
            f"size={width_px}x{height_px}",
            f"scale=2",
            f"maptype=roadmap",
        ]

        # ── Cerchi 3/5/10 minuti ──────────────────────────────────────────
        # 3 min ≈ 240m blu, 5 min ≈ 400m viola, 10 min ≈ 800m rosa
        cerchi = [
            (240,  '0x3b82f640', '0x3b82f618'),  # blu
            (400,  '0x8b5cf640', '0x8b5cf610'),  # viola
            (800,  '0xec489920', '0xec489908'),  # rosa
        ]
        for raggio, colore_bordo, colore_fill in cerchi:
            path_pts = _cerchio_path(lat, lng, raggio, 20)
            parts.append(
                f"path=color:{colore_bordo}|fillcolor:{colore_fill}|weight:2|{path_pts}"
            )

        # ── Marker sede ───────────────────────────────────────────────────
        parts.append(f"markers=color:yellow|size:mid|label:S|{lat},{lng}")

        # ── Concorrenti ───────────────────────────────────────────────────
        if concorrenti:
            self_sv = [c for c in concorrenti if c.get('tipo') == 'self_service']
            tradi   = [c for c in concorrenti if c.get('tipo') == 'tradizionale']
            indust  = [c for c in concorrenti if c.get('tipo') == 'industriale']
            for group, color, lbl in [
                (self_sv, 'red',    'C'),
                (tradi,   'orange', 'T'),
                (indust,  'blue',   'I'),
            ]:
                if group:
                    locs = "|".join(f"{c['lat']},{c['lng']}" for c in group[:6])
                    parts.append(f"markers=color:{color}|size:small|label:{lbl}|{locs}")

        # ── Attractor points ──────────────────────────────────────────────
        if attractors:
            univ = [a for a in attractors if a.get('tipo') == 'universita']
            osp  = [a for a in attractors if a.get('tipo') == 'ospedale']
            mil  = [a for a in attractors if a.get('tipo') in
                    ('caserma', 'scuola_militare')]
            staz = [a for a in attractors if a.get('tipo') == 'stazione']
            vvf  = [a for a in attractors if a.get('tipo') == 'vvf']
            for group, color, lbl in [
                (univ, 'purple', 'U'),
                (osp,  'green',  'H'),
                (mil,  'red',    'M'),
                (staz, 'blue',   'Z'),
                (vvf,  'orange', 'V'),
            ]:
                if group:
                    locs = "|".join(f"{a['lat']},{a['lng']}" for a in group[:4])
                    parts.append(f"markers=color:{color}|size:small|label:{lbl}|{locs}")

        # ── Stile mappa scuro ─────────────────────────────────────────────
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
        url = ("https://maps.googleapis.com/maps/api/staticmap?"
               + "&".join(parts + styles))
        req = _ur.Request(url, headers={"User-Agent": "BIOLavaTU-PDF"})
        with _ur.urlopen(req, timeout=10) as r:
            return r.read()
    except Exception:
        return None



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
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, PageBreak, KeepTogether)
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.platypus.flowables import Flowable
    from pypdf import PdfWriter, PdfReader
    import os, io as _io

    p = Pratica.query.get_or_404(id)
    s = Settings.query.first()
    W, H = A4
    PW = W - 4*cm  # larghezza utile

    # ── PALETTE ──────────────────────────────────────────────────────────────
    C = {
        'navy':    colors.HexColor('#0f1f3d'),
        'blue':    colors.HexColor('#2563eb'),
        'lblue':   colors.HexColor('#3b82f6'),
        'sky':     colors.HexColor('#93c5fd'),
        'slate':   colors.HexColor('#64748b'),
        'light':   colors.HexColor('#f1f5f9'),
        'border':  colors.HexColor('#e2e8f0'),
        'white':   colors.white,
        'green':   colors.HexColor('#10b981'),
        'red':     colors.HexColor('#ef4444'),
        'orange':  colors.HexColor('#f59e0b'),
        'purple':  colors.HexColor('#8b5cf6'),
        'pink':    colors.HexColor('#ec4899'),
        'dark':    colors.HexColor('#0f172a'),
        'text':    colors.HexColor('#1e293b'),
    }

    brand   = (s.brand_name   or 'BIOLavaTU')      if s else 'BIOLavaTU'
    company = (s.company_name or 'Rotondi Group Srl') if s else 'Rotondi Group Srl'
    addr    = (s.company_addr  or '')               if s else ''
    web     = (s.company_web   or '')               if s else ''
    tel     = (s.company_tel   or '')               if s else ''

    # ── STILI ─────────────────────────────────────────────────────────────────
    _sc = [0]
    def st(name, **kw):
        _sc[0] += 1
        kw.setdefault('fontSize', 9)
        kw.setdefault('fontName', 'Helvetica')
        kw.setdefault('textColor', C['text'])
        kw.setdefault('leading', 13)
        return ParagraphStyle(f'{name}_{_sc[0]}', **kw)

    S = {
        'h1':   st('h1',  fontSize=14, fontName='Helvetica-Bold', textColor=C['navy'], spaceBefore=16, spaceAfter=6),
        'h2':   st('h2',  fontSize=10, fontName='Helvetica-Bold', textColor=C['slate'], spaceBefore=10, spaceAfter=4),
        'body': st('bd',  fontSize=9,  leading=14),
        'tiny': st('ti',  fontSize=7.5, textColor=C['slate']),
        'bold': st('bl',  fontSize=9,  fontName='Helvetica-Bold'),
    }

    # ── HEADER/FOOTER ─────────────────────────────────────────────────────────
    pn = [0]
    def on_page(cv, doc):
        pn[0] += 1
        if pn[0] == 1:
            return
        cv.saveState()
        # Header
        cv.setFillColor(C['navy']); cv.rect(0, H-1.1*cm, W, 1.1*cm, fill=1, stroke=0)
        cv.setFillColor(C['blue']); cv.rect(0, H-1.1*cm, 0.4*cm, 1.1*cm, fill=1, stroke=0)
        cv.setFont('Helvetica-Bold', 8.5); cv.setFillColor(C['white'])
        cv.drawString(0.8*cm, H-0.72*cm, brand)
        cv.setFont('Helvetica', 8); cv.setFillColor(C['sky'])
        cv.drawRightString(W-0.8*cm, H-0.72*cm, f'{p.numero}  ·  {p.citta}')
        # Footer
        cv.setFillColor(C['light']); cv.rect(0, 0, W, 0.85*cm, fill=1, stroke=0)
        cv.setStrokeColor(C['border']); cv.setLineWidth(0.5)
        cv.line(0, 0.85*cm, W, 0.85*cm)
        cv.setFont('Helvetica', 7); cv.setFillColor(C['slate'])
        cv.drawString(0.8*cm, 0.28*cm, f'{company}  ·  {addr}  ·  {web}')
        cv.drawRightString(W-0.8*cm, 0.28*cm, f'Pag. {pn[0]-1}')
        cv.restoreState()

    main_buf = _io.BytesIO()
    doc = SimpleDocTemplate(main_buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.4*cm, bottomMargin=1.2*cm,
        onPage=on_page, onLaterPages=on_page)

    story = []

    # ─────────────────────────────────────────────────────────────────────────
    # HELPER: sezione header con barra laterale colorata
    # ─────────────────────────────────────────────────────────────────────────
    def section_header(title, accent=None):
        acc = accent or C['blue']
        tbl = Table([[
            '',
            Paragraph(f'<b>{title}</b>',
                      st('sh', fontSize=11, fontName='Helvetica-Bold',
                         textColor=C['navy'], leading=15))
        ]], colWidths=[0.35*cm, PW - 0.35*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',  (0,0),(0,0), acc),
            ('BACKGROUND',  (1,0),(1,0), C['light']),
            ('TOPPADDING',  (0,0),(-1,-1), 8),
            ('BOTTOMPADDING',(0,0),(-1,-1), 8),
            ('LEFTPADDING', (1,0),(1,0), 10),
            ('VALIGN',      (0,0),(-1,-1), 'MIDDLE'),
        ]))
        return tbl

    # ─────────────────────────────────────────────────────────────────────────
    # HELPER: riga di KPI colorati
    # ─────────────────────────────────────────────────────────────────────────
    def kpi_row(items):
        """items = [(label, value, hex_color), ...]"""
        n  = len(items)
        cw = PW / n
        cells = []
        for lbl, val, col in items:
            inner = Table([
                [Paragraph(f'<b>{val}</b>',
                           st(f'kv', fontSize=12, fontName='Helvetica-Bold',
                              textColor=colors.HexColor(col), alignment=TA_CENTER))],
                [Paragraph(lbl, st(f'kl', fontSize=7.5, textColor=C['slate'],
                                   alignment=TA_CENTER))],
            ], colWidths=[cw - 0.4*cm])
            cells.append(inner)
        t = Table([cells], colWidths=[cw]*n)
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), C['light']),
            ('BOX',           (0,0),(-1,-1), 0.5, C['border']),
            ('INNERGRID',     (0,0),(-1,-1), 0.3, C['border']),
            ('TOPPADDING',    (0,0),(-1,-1), 9),
            ('BOTTOMPADDING', (0,0),(-1,-1), 9),
        ]))
        return t

    # ─────────────────────────────────────────────────────────────────────────
    # PAG 1 — COPERTINA
    # ─────────────────────────────────────────────────────────────────────────
    class Cover(Flowable):
        def __init__(self):
            Flowable.__init__(self)
            self.width  = PW
            self.height = H - 5.5*cm

        def draw(self):
            c   = self.canv
            w   = self.width
            h   = self.height

            # ── Sfondo bianco/grigio chiaro ──────────────────────────────
            c.setFillColor(colors.HexColor('#f8fafc'))
            c.roundRect(0, 0, w, h, 8, fill=1, stroke=0)

            # ── Header band blu scuro (30% superiore) ────────────────────
            c.setFillColor(C['navy'])
            c.roundRect(0, h*0.70, w, h*0.30, 8, fill=1, stroke=0)
            c.rect(0, h*0.70, w, h*0.04, fill=1, stroke=0)

            # Accent strip sinistra blu vivo
            c.setFillColor(C['blue'])
            c.rect(0, 0, 0.45*cm, h, fill=1, stroke=0)

            # ── Brand + tagline nell'header ──────────────────────────
            c.setFont('Helvetica-Bold', 26)
            c.setFillColor(colors.white)
            c.drawString(1.2*cm, h - 1.7*cm, brand)
            c.setFont('Helvetica', 9)
            c.setFillColor(C['sky'])
            c.drawString(1.2*cm, h - 2.35*cm,
                         'LaundryPro Platform  ·  Analisi di Fattibilità')

            # Linea separatrice
            c.setStrokeColor(C['blue']); c.setLineWidth(1.5)
            c.line(1.2*cm, h - 2.85*cm, w - 0.5*cm, h - 2.85*cm)

            # Numero pratica
            c.setFillColor(C['blue'])
            c.roundRect(1.2*cm, h - 4.3*cm, w*0.52, 1.1*cm, 5, fill=1, stroke=0)
            c.setFont('Helvetica-Bold', 14); c.setFillColor(colors.white)
            c.drawString(1.6*cm, h - 3.65*cm, p.numero)
            c.setFont('Helvetica', 7.5); c.setFillColor(C['sky'])
            c.drawString(1.6*cm, h - 4.15*cm,
                f'{p.created.strftime("%d/%m/%Y")}   ·   {p.stato.upper()}')

            # ── Sezione cliente su sfondo chiaro ─────────────────────────
            # Rettangolo bianco per dati cliente
            c.setFillColor(colors.white)
            c.roundRect(0.7*cm, h*0.70 - 3.8*cm, w - 0.7*cm, 3.4*cm, 6, fill=1, stroke=0)
            c.setStrokeColor(C['border']); c.setLineWidth(0.5)
            c.roundRect(0.7*cm, h*0.70 - 3.8*cm, w - 0.7*cm, 3.4*cm, 6, fill=0, stroke=1)

            cliente = p.cliente
            nome_cl = (cliente.nome_completo if cliente else 'Cliente')[:42]
            ind = f'{p.indirizzo}, {p.citta}' if p.indirizzo else (p.citta or '')

            c.setFont('Helvetica', 7); c.setFillColor(C['slate'])
            c.drawString(1.2*cm, h*0.70 - 1.0*cm, 'CLIENTE')
            c.setFont('Helvetica-Bold', 13); c.setFillColor(C['dark'])
            c.drawString(1.2*cm, h*0.70 - 1.7*cm, nome_cl)
            c.setFont('Helvetica', 9); c.setFillColor(C['slate'])
            c.drawString(1.2*cm, h*0.70 - 2.3*cm, ind[:65])
            if p.mq:
                c.setFont('Helvetica', 8); c.setFillColor(C['slate'])
                c.drawString(1.2*cm, h*0.70 - 2.85*cm, f'Superficie: {p.mq} mq')

            # ── 4 KPI box ────────────────────────────────────────────────
            capex_iva = p.capex * 1.22
            kpis = [
                ('INVESTIMENTO + IVA', f'€ {capex_iva:,.0f}', '#2563eb'),
                ('INCASSO / MESE',     f'€ {p.incasso_mese:,.0f}',
                 '#059669' if p.incasso_mese > 0 else '#dc2626'),
                ('UTILE / MESE',       f'€ {p.utile_mese:,.0f}',
                 '#059669' if p.utile_mese >= 0 else '#dc2626'),
                ('PAYBACK',
                 f'{int(p.payback_mesi/12)} anni' if p.payback_mesi else 'N/D',
                 '#d97706'),
            ]
            gap = 0.3*cm
            bw  = (w - 0.7*cm - gap*3) / 4
            by  = h*0.70 - 5.6*cm
            for i,(lbl,val,col) in enumerate(kpis):
                bx = 0.7*cm + i*(bw+gap)
                # Card bianca con bordo colorato in basso
                c.setFillColor(colors.white)
                c.roundRect(bx, by, bw, 2.0*cm, 5, fill=1, stroke=0)
                c.setStrokeColor(colors.HexColor(col)); c.setLineWidth(2.5)
                c.line(bx+4, by, bx+bw-4, by)
                c.setLineWidth(1)
                # Value grande colorata
                c.setFont('Helvetica-Bold', 10); c.setFillColor(colors.HexColor(col))
                c.drawCentredString(bx+bw/2, by+1.15*cm, val)
                # Label grigia piccola
                c.setFont('Helvetica', 6.5); c.setFillColor(C['slate'])
                c.drawCentredString(bx+bw/2, by+0.5*cm, lbl)

            # ── Score zona cerchio ───────────────────────────────────
            sc   = int(p.score_zona or 0)
            scol = '#059669' if sc>=70 else '#d97706' if sc>=45 else '#dc2626'
            cx   = 0.7*cm + (w - 0.7*cm)*0.80
            cy   = by - 2.4*cm
            # Cerchio sfondo grigio chiaro
            c.setFillColor(colors.HexColor('#f1f5f9'))
            c.circle(cx, cy, 1.6*cm, fill=1, stroke=0)
            c.setStrokeColor(colors.HexColor('#e2e8f0')); c.setLineWidth(1)
            c.circle(cx, cy, 1.6*cm, fill=0, stroke=1)
            # Arco colorato
            import math
            angle = 360 * sc / 100
            c.setStrokeColor(colors.HexColor(scol)); c.setLineWidth(5)
            c.arc(cx-1.4*cm, cy-1.4*cm, cx+1.4*cm, cy+1.4*cm,
                  startAng=90, extent=-angle)
            # Testo score
            c.setFont('Helvetica-Bold', 24); c.setFillColor(colors.HexColor(scol))
            c.drawCentredString(cx, cy+0.05*cm, str(sc))
            c.setFont('Helvetica', 7); c.setFillColor(C['slate'])
            c.drawCentredString(cx, cy-0.65*cm, 'score /100')
            c.setFont('Helvetica-Bold', 8); c.setFillColor(C['dark'])
            c.drawCentredString(cx, cy-1.15*cm, p.score_label or '')
            c.setFont('Helvetica', 7); c.setFillColor(C['slate'])
            c.drawString(0.7*cm, cy+0.5*cm, 'SCORE ZONA')

            # ── Footer ───────────────────────────────────────────────────
            c.setFillColor(C['navy'])
            c.rect(0, 0, w, 0.9*cm, fill=1, stroke=0)
            c.setFont('Helvetica', 7.5); c.setFillColor(colors.white)
            c.drawCentredString(w/2, 0.55*cm, f'{company}  ·  {web}  ·  {tel}')
            c.setFont('Helvetica', 6.5); c.setFillColor(C['sky'])
            c.drawCentredString(w/2, 0.15*cm, 'Documento riservato — uso interno')

    story.append(Cover()); story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # PAG 2 — CLIENTE + MAPPA ZONA FULL WIDTH + KPI + SCORE
    # ─────────────────────────────────────────────────────────────────────────
    story.append(section_header('CLIENTE E SEDE', C['blue']))
    story.append(Spacer(1, 6))

    cliente = p.cliente
    # Info cliente in 2 colonne
    col1 = [
        ['Cliente',   cliente.nome_completo if cliente else '—'],
        ['Indirizzo', f'{p.indirizzo}, {p.citta}' if p.indirizzo else p.citta or '—'],
        ['CAP / Prov.', f'{p.cap or ""}  {p.provincia or ""}'],
    ]
    col2 = [
        ['Superficie', f'{p.mq or "—"} mq'],
        ['Email',      (cliente.email or '—') if cliente else '—'],
        ['Telefono',   (cliente.telefono or '—') if cliente else '—'],
    ]
    def info_tbl(rows, cw1=2.8*cm, cw2=6.2*cm):
        t = Table(rows, colWidths=[cw1, cw2])
        t.setStyle(TableStyle([
            ('FONTNAME',  (0,0),(0,-1), 'Helvetica-Bold'),
            ('FONTSIZE',  (0,0),(-1,-1), 8.5),
            ('TEXTCOLOR', (0,0),(0,-1), C['slate']),
            ('TEXTCOLOR', (1,0),(1,-1), C['dark']),
            ('TOPPADDING', (0,0),(-1,-1), 4),
            ('BOTTOMPADDING',(0,0),(-1,-1), 4),
            ('LINEBELOW', (0,0),(-1,-1), 0.3, C['border']),
            ('ROWBACKGROUNDS',(0,0),(-1,-1), [C['white'], C['light']]),
        ]))
        return t

    two_col = Table([[info_tbl(col1), info_tbl(col2)]], colWidths=[PW/2]*2)
    two_col.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                                  ('LEFTPADDING',(1,0),(1,0),6)]))
    story.append(two_col)
    story.append(Spacer(1, 14))

    # ── MAPPA ZONA ────────────────────────────────────────────────────────────
    story.append(section_header('MAPPA ZONA', C['blue']))
    story.append(Spacer(1, 6))

    gmaps_key = os.environ.get('GMAPS_KEY', '')
    mappa_ok  = False

    # Se mancano le coordinate, prova a geocodificare dall'indirizzo/città
    _map_lat = float(p.lat or 0)
    _map_lng = float(p.lng or 0)
    if (not _map_lat or not _map_lng) and gmaps_key:
        # Prova prima con indirizzo completo, poi solo città
        _geo_attempts = []
        if p.indirizzo and p.citta:
            _geo_attempts.append(f"{p.indirizzo}, {p.citta}, Italia")
        if p.citta:
            _geo_attempts.append(f"{p.citta}, Italia")
        for _geo_addr in _geo_attempts:
            try:
                import urllib.parse as _upgeo
                _gurl = ("https://maps.googleapis.com/maps/api/geocode/json"
                         "?address=" + _upgeo.quote_plus(_geo_addr)
                         + "&key=" + gmaps_key)
                _greq = ur.Request(_gurl, headers={"User-Agent": "BIOLavaTU-PDF"})
                with ur.urlopen(_greq, timeout=8) as _gr:
                    _gdata = __import__('json').loads(_gr.read())
                if _gdata.get('results'):
                    _loc = _gdata['results'][0]['geometry']['location']
                    _map_lat = float(_loc['lat'])
                    _map_lng = float(_loc['lng'])
                    break  # trovato, esci dal loop
            except Exception:
                continue

    if _map_lat and _map_lng and gmaps_key:
        _mlat, _mlng = _map_lat, _map_lng
        _conc_list = []
        try:
            import json as _j2
            _pois_raw = p.pois_raw if hasattr(p, 'pois_raw') and p.pois_raw else '[]'
            _all_pois = _j2.loads(_pois_raw) if isinstance(_pois_raw, str) else (_pois_raw or [])
            _conc_list = [x for x in _all_pois
                          if x.get('tipo') in ('self_service','tradizionale','industriale','concorrente')]
        except Exception:
            _conc_list = []

        _attr_list = []
        try:
            _attr_list = [x for x in _all_pois if x.get('categoria') == 'attractor'
                          or x.get('tipo') in ('universita','ospedale','caserma',
                                               'scuola_militare','stazione','vvf')]
        except Exception:
            _attr_list = []
        mappa_bytes = _get_mappa_statica(_mlat, _mlng, gmaps_key,
                                          width_px=640, height_px=320,
                                          concorrenti=_conc_list,
                                          attractors=_attr_list)
        if mappa_bytes:
            from reportlab.platypus import Image as RLImage
            import io as _io2
            img_w = PW
            img_h = img_w * 320 / 640
            rl_img = RLImage(_io2.BytesIO(mappa_bytes), width=img_w, height=img_h)
            story.append(rl_img)
            mappa_ok = True

            # Legenda concorrenti sotto la mappa
            if _conc_list:
                n_self = sum(1 for c in _conc_list if c.get('tipo')=='self_service')
                n_trad = sum(1 for c in _conc_list if c.get('tipo')=='tradizionale')
                n_ind  = sum(1 for c in _conc_list if c.get('tipo')=='industriale')
                legend_items = []
                if n_self: legend_items.append(('Rosso C = Self-service', n_self, '#ef4444'))
                if n_trad: legend_items.append(('Arancio T = Tradizionale', n_trad, '#f59e0b'))
                if n_ind:  legend_items.append(('Blu I = Industriale', n_ind, '#3b82f6'))
                if legend_items:
                    leg_parts = [
                        Paragraph(
                            f'<font color="{col}">●</font>  {lbl}: <b>{n}</b>',
                            st('leg', fontSize=8, textColor=C['text'])
                        )
                        for lbl, n, col in legend_items
                    ]
                    leg_parts.insert(0, Paragraph(
                        '<font color="#f59e0b">★</font>  Giallo S = Sede  '
                        '<font color="#800080">●</font> U=Università  '
                        '<font color="#008000">●</font> H=Ospedale  '
                        '<font color="#ef4444">●</font> M=Militare  '
                        '<font color="#3b82f6">●</font> Z=Stazione',
                        st('leg0', fontSize=7.5, textColor=C['text'])
                    ))
                    # Distribuisci su 4 colonne max
                    while len(leg_parts) < 4:
                        leg_parts.append(Paragraph('', st('legx', fontSize=8)))
                    leg_tbl = Table([leg_parts[:4]], colWidths=[PW/4]*4)
                    leg_tbl.setStyle(TableStyle([
                        ('BACKGROUND', (0,0),(-1,-1), C['light']),
                        ('TOPPADDING', (0,0),(-1,-1), 5),
                        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
                        ('LEFTPADDING', (0,0),(-1,-1), 8),
                    ]))
                    story.append(leg_tbl)

    if not mappa_ok:
        story.append(Paragraph('Coordinate non disponibili per questa pratica.',
                                st('nomappa', fontSize=9, textColor=C['slate'])))

    story.append(Spacer(1, 12))

    # ── KPI ZONA + SCORE ───────────────────────────────────────────────────────
    story.append(section_header('ANALISI ZONA', C['purple']))
    story.append(Spacer(1, 6))

    story.append(kpi_row([
        ('Abitanti 3 min',   f'{int(p.pop_3min  or 0):,}', '#3b82f6'),
        ('Abitanti 5 min',   f'{int(p.pop_5min  or 0):,}', '#8b5cf6'),
        ('Abitanti 10 min',  f'{int(p.pop_10min or 0):,}', '#ec4899'),
        ('Concorrenti 500m', str(p.concorrenti_500m or 0),  '#ef4444'),
        ('Concorrenti 1km',  str(p.concorrenti_1km  or 0),  '#f59e0b'),
    ]))
    story.append(Spacer(1, 8))

    # Score + fattibilità — barra orizzontale
    sc      = int(p.score_zona or 0)
    scol_h  = '#10b981' if sc>=70 else '#f59e0b' if sc>=45 else '#ef4444'
    fat     = int(p.fattibilita or 0)
    fat_h   = '#10b981' if fat>=70 else '#f59e0b' if fat>=40 else '#ef4444'

    class ScoreBar(Flowable):
        def __init__(self, label, value, max_val, color_hex, subtitle='', width=None):
            Flowable.__init__(self)
            self.label    = label
            self.value    = value
            self.max_val  = max_val
            self.col      = color_hex
            self.subtitle = subtitle
            self.width    = width or PW
            self.height   = 1.1*cm
        def draw(self):
            c   = self.canv
            w   = self.width
            lw  = 3.5*cm   # larghezza etichetta
            bw  = w - lw - 3.0*cm  # larghezza barra
            bx  = lw
            by  = 0.35*cm
            bh  = 0.45*cm
            pct = self.value / self.max_val
            # Label
            c.setFont('Helvetica-Bold', 9); c.setFillColor(C['dark'])
            c.drawString(0, by + 0.05*cm, self.label)
            # Sfondo barra
            c.setFillColor(C['border'])
            c.roundRect(bx, by, bw, bh, 3, fill=1, stroke=0)
            # Barra colorata
            c.setFillColor(colors.HexColor(self.col))
            fill_w = max(6, bw * pct)
            c.roundRect(bx, by, fill_w, bh, 3, fill=1, stroke=0)
            # Valore
            c.setFont('Helvetica-Bold', 10); c.setFillColor(colors.HexColor(self.col))
            c.drawString(bx + bw + 0.3*cm, by, f'{self.value}')
            c.setFont('Helvetica', 7); c.setFillColor(C['slate'])
            c.drawString(bx + bw + 0.3*cm, by + 0.35*cm, f'/{self.max_val}')
            # Subtitle
            if self.subtitle:
                c.setFont('Helvetica', 7.5); c.setFillColor(C['slate'])
                c.drawString(bx + bw + 1.2*cm, by, self.subtitle)

    story.append(ScoreBar('Score zona',  sc,  100, scol_h, p.score_label or '',  PW))
    story.append(Spacer(1, 4))
    story.append(ScoreBar('Fattibilità', fat, 100, fat_h,  '',                   PW))
    story.append(Spacer(1, 14))

    # ─────────────────────────────────────────────────────────────────────────
    # PAG 3 — DEMOGRAFICA ISTAT (layout grafico)
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_header('ANALISI DEMOGRAFICA  —  Dati ISTAT', C['purple']))
    story.append(Spacer(1, 8))

    # Recupera dati ISTAT
    try:
        from services.istat import PROVINCE_DATA
        citta_lower = (p.citta or '').lower()
        dati_prov = None
        for cod, dati in PROVINCE_DATA.items():
            nn = dati.get('nome', '').lower()
            if nn in citta_lower or citta_lower in nn:
                dati_prov = dati; break
        if not dati_prov:
            dati_prov = {'nome': p.citta or 'N/D', 'eta_media': 46.0,
                         'reddito_medio': 20500, 'densita': 200}
    except Exception:
        dati_prov = {'nome': p.citta or 'N/D', 'eta_media': 46.0,
                     'reddito_medio': 20500, 'densita': 200}

    eta     = dati_prov.get('eta_media', 46.0)
    reddito = dati_prov.get('reddito_medio', 20500)
    densita = dati_prov.get('densita', 200)
    pop5    = int(p.pop_5min  or 0)
    pop10   = int(p.pop_10min or 0)
    pop3    = int(p.pop_3min  or 0)
    bacino  = pop5 if pop5 > 0 else pop10
    tasso_b = 0.018
    fatt_e  = 1.10 if eta<35 else 1.05 if eta<45 else 0.98 if eta<50 else 0.90
    fatt_r  = 1.15 if reddito<17000 else 1.05 if reddito<22000 else 0.95 if reddito<27000 else 0.85
    clienti_giorno = max(1, int(bacino * tasso_b * fatt_e * fatt_r))

    class DemoGraphic(Flowable):
        def __init__(self, width, height):
            Flowable.__init__(self)
            self.width  = width
            self.height = height

        def draw(self):
            c = self.canv
            w = self.width
            h = self.height

            # ── ROW 1: 3 card indicatori ISTAT ─────────────────────────────
            cards = [
                ('ETÀ MEDIA', f'{eta:.1f}', 'anni', '#8b5cf6', 'ISTAT 2021'),
                ('REDDITO MEDIO', f'€ {reddito:,}', '/anno', '#10b981', 'MEF 2022'),
                ('DENSITÀ', f'{densita:,}', 'ab/km²', '#3b82f6', 'ISTAT 2021'),
            ]
            cw = (w - 2*0.3*cm) / 3
            for i, (lbl, val, unit, col, fonte) in enumerate(cards):
                cx = i * (cw + 0.3*cm)
                ch = 2.3*cm
                cy = h - ch - 0.1*cm
                # Card background
                c.setFillColor(colors.HexColor('#f8fafc'))
                c.roundRect(cx, cy, cw, ch, 6, fill=1, stroke=0)
                # Accent top strip
                c.setFillColor(colors.HexColor(col))
                c.roundRect(cx, cy+ch-0.22*cm, cw, 0.22*cm, 3, fill=1, stroke=0)
                c.rect(cx, cy+ch-0.22*cm, cw, 0.11*cm, fill=1, stroke=0)
                # Etichetta
                c.setFont('Helvetica-Bold', 6.5); c.setFillColor(colors.HexColor('#64748b'))
                c.drawCentredString(cx+cw/2, cy+1.75*cm, lbl)
                # Valore grande
                c.setFont('Helvetica-Bold', 14); c.setFillColor(colors.HexColor(col))
                c.drawCentredString(cx+cw/2, cy+1.1*cm, val)
                # Unità
                c.setFont('Helvetica', 7.5); c.setFillColor(colors.HexColor('#94a3b8'))
                c.drawCentredString(cx+cw/2, cy+0.6*cm, unit)
                # Fonte
                c.setFont('Helvetica', 6); c.setFillColor(colors.HexColor('#cbd5e1'))
                c.drawCentredString(cx+cw/2, cy+0.15*cm, fonte)

            # ── ROW 2: Grafico bacino a barre orizzontali ──────────────────
            row2_top = h - 2.8*cm
            c.setFont('Helvetica-Bold', 8); c.setFillColor(C['navy'])
            c.drawString(0, row2_top - 0.5*cm, 'BACINO DI UTENZA')

            bar_items = [
                (f'3 min  (~400m)', pop3,  '#3b82f6'),
                (f'5 min  (~700m)', pop5,  '#8b5cf6'),
                (f'10 min (~1.5km)', pop10, '#ec4899'),
            ]
            max_pop = max(pop10, 1)
            bar_top = row2_top - 1.1*cm
            bh_bar  = 16
            gap_bar = 7
            label_w = 3.5*cm
            bar_max_w = w * 0.52

            for i, (lbl, val, col) in enumerate(bar_items):
                by_ = bar_top - i*(bh_bar+gap_bar)
                bw_ = bar_max_w * (val / max_pop)
                # Sfondo
                c.setFillColor(colors.HexColor('#e2e8f0'))
                c.roundRect(label_w, by_, bar_max_w, bh_bar, 3, fill=1, stroke=0)
                # Fill
                if bw_ > 4:
                    c.setFillColor(colors.HexColor(col))
                    c.roundRect(label_w, by_, bw_, bh_bar, 3, fill=1, stroke=0)
                # Label sinistra
                c.setFont('Helvetica', 7.5); c.setFillColor(colors.HexColor('#64748b'))
                c.drawRightString(label_w - 4, by_ + 4, lbl)
                # Valore
                c.setFont('Helvetica-Bold', 8); c.setFillColor(colors.HexColor('#0f172a'))
                c.drawString(label_w + bar_max_w + 6, by_ + 4, f'{val:,} ab.')

            # ── ROW 2b: segmentazione (destra delle barre) ─────────────────
            seg_x = label_w + bar_max_w + w*0.15
            c.setFont('Helvetica-Bold', 8); c.setFillColor(C['navy'])
            c.drawString(seg_x, row2_top - 0.5*cm, 'TARGET')

            seg_items = [
                ('18-34 anni', 22, '#3b82f6'),
                ('35-54 anni', 35, '#10b981'),
                ('55+ anni',   20, '#f59e0b'),
                ('Famiglie',   23, '#8b5cf6'),
            ]
            seg_top2 = row2_top - 1.1*cm
            seg_h    = 14
            seg_gap  = 9
            seg_bw   = w - seg_x - 1.5*cm
            for i,(lbl,pct,col) in enumerate(seg_items):
                sy = seg_top2 - i*(seg_h+seg_gap)
                bw_s = seg_bw * pct / 100
                c.setFillColor(colors.HexColor('#e2e8f0'))
                c.roundRect(seg_x, sy, seg_bw, seg_h, 3, fill=1, stroke=0)
                c.setFillColor(colors.HexColor(col))
                c.roundRect(seg_x, sy, bw_s, seg_h, 3, fill=1, stroke=0)
                c.setFont('Helvetica', 7); c.setFillColor(colors.HexColor('#64748b'))
                c.drawString(seg_x - 1.5*cm, sy + 3, lbl)
                c.setFont('Helvetica-Bold', 7); c.setFillColor(colors.HexColor(col))
                c.drawString(seg_x + seg_bw + 4, sy + 3, f'{pct}%')

            # ── ROW 3: 5 KPI commerciali ───────────────────────────────────
            row3_top = row2_top - 3.8*cm
            c.setFont('Helvetica-Bold', 8); c.setFillColor(C['navy'])
            c.drawString(0, row3_top - 0.3*cm, 'POTENZIALE COMMERCIALE STIMATO')

            kpis_c = [
                ('Clienti/giorno',  str(clienti_giorno),     '#10b981'),
                ('Clienti/mese',    str(clienti_giorno*26),  '#3b82f6'),
                ('Età media',       f'{eta:.0f} anni',        '#8b5cf6'),
                ('Reddito/capite',  f'€ {reddito:,}',         '#f59e0b'),
                ('Densità ab/km²',  f'{densita:,}',           '#ec4899'),
            ]
            kpi_top = row3_top - 1.0*cm
            kw_c    = (w - 4*0.2*cm) / 5
            for i,(lbl,val,col) in enumerate(kpis_c):
                kx = i*(kw_c + 0.2*cm)
                ky = kpi_top - 1.6*cm
                c.setFillColor(colors.HexColor('#f8fafc'))
                c.roundRect(kx, ky, kw_c, 1.5*cm, 4, fill=1, stroke=0)
                c.setStrokeColor(colors.HexColor(col)); c.setLineWidth(1.5)
                c.line(kx+4, ky+1.5*cm, kx+kw_c-4, ky+1.5*cm)
                c.setLineWidth(1)
                c.setFont('Helvetica-Bold', 9.5); c.setFillColor(colors.HexColor(col))
                c.drawCentredString(kx+kw_c/2, ky+0.8*cm, val)
                words = lbl.split()
                c.setFont('Helvetica', 6.5); c.setFillColor(colors.HexColor('#64748b'))
                if len(words) > 2:
                    c.drawCentredString(kx+kw_c/2, ky+0.38*cm, ' '.join(words[:2]))
                    c.drawCentredString(kx+kw_c/2, ky+0.1*cm, ' '.join(words[2:]))
                else:
                    c.drawCentredString(kx+kw_c/2, ky+0.25*cm, lbl)

            # Disclaimer
            c.setFont('Helvetica', 6.5); c.setFillColor(colors.HexColor('#94a3b8'))
            c.drawString(0, 0.1*cm, 'Stime ISTAT Censimento 2021 + MEF 2022 + modello domanda BIOLavaTU. Valori indicativi.')

    story.append(DemoGraphic(PW, 19.5*cm))

    # ─────────────────────────────────────────────────────────────────────────
    # PAG 4 — MACCHINE
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_header('CONFIGURAZIONE MACCHINE', C['orange']))
    story.append(Spacer(1, 6))

    mac_rows  = []
    capex_iva = p.capex * 1.22
    for m in p.get_macchine():
        prezzo = float(m.get('prezzo_effettivo') or m.get('prezzo', 0))
        qty    = int(m.get('qty', 1))
        cat    = m.get('categoria', '')
        modello = m.get('modello', '') or ''
        nome    = m.get('nome', '')
        # Prima cella: nome bold + categoria + modello su righe separate
        sub_lines = []
        if cat:     sub_lines.append(f'<font color="#64748b">{cat}</font>')
        if modello: sub_lines.append(f'<font color="#94a3b8">{modello}</font>')
        sub_text = '  ·  '.join(sub_lines) if sub_lines else ''
        desc_html = f'<b>{nome}</b>'
        if sub_text:
            desc_html += f'<br/><font size="7.5">{sub_text}</font>'
        mac_rows.append([
            Paragraph(desc_html, st('mn', fontSize=8.5, fontName='Helvetica-Bold',
                                    textColor=C['dark'], leading=13)),
            Paragraph(f'<b>{qty}x</b>', st('mq2', fontSize=9, fontName='Helvetica-Bold',
                                            alignment=TA_CENTER)),
            Paragraph(f'€ {prezzo:,.0f}', st('mp', fontSize=8.5, alignment=TA_RIGHT)),
            Paragraph(f'<b>€ {prezzo*qty:,.0f}</b>',
                      st('mt', fontSize=9, fontName='Helvetica-Bold',
                         textColor=C['blue'], alignment=TA_RIGHT)),
        ])

    header_row = [
        Paragraph('<b>Descrizione macchina</b>', st('mh',  fontSize=8.5, fontName='Helvetica-Bold', textColor=C['white'])),
        Paragraph('<b>Qty</b>',   st('mh4', fontSize=8.5, fontName='Helvetica-Bold', textColor=C['white'], alignment=TA_CENTER)),
        Paragraph('<b>Prezzo unit.</b>', st('mh5', fontSize=8.5, fontName='Helvetica-Bold', textColor=C['white'], alignment=TA_RIGHT)),
        Paragraph('<b>Totale</b>', st('mh6', fontSize=8.5, fontName='Helvetica-Bold', textColor=C['white'], alignment=TA_RIGHT)),
    ]

    totali = [
        ['', '', Paragraph('Imponibile', st('ti1',fontSize=8,textColor=C['slate'],alignment=TA_RIGHT)),
                 Paragraph(f'€ {p.capex:,.0f}', st('tv1',fontSize=8,alignment=TA_RIGHT))],
        ['', '', Paragraph('IVA 22%', st('ti2',fontSize=8,textColor=C['orange'],alignment=TA_RIGHT)),
                 Paragraph(f'€ {p.capex*0.22:,.0f}', st('tv2',fontSize=8,textColor=C['orange'],alignment=TA_RIGHT))],
        ['', '', Paragraph('<b>Totale IVA inclusa</b>', st('ti3',fontSize=9.5,fontName='Helvetica-Bold',textColor=C['blue'],alignment=TA_RIGHT)),
                 Paragraph(f'<b>€ {capex_iva:,.0f}</b>', st('tv3',fontSize=9.5,fontName='Helvetica-Bold',textColor=C['blue'],alignment=TA_RIGHT))],
    ]

    # 4 colonne: Descrizione (larga) | Qty | Prezzo unit | Totale
    # PW = 17cm → 10.5 + 1.2 + 2.5 + 2.8 = 17.0
    mt = Table([header_row] + mac_rows + totali,
               colWidths=[10.5*cm, 1.2*cm, 2.5*cm, 2.8*cm])
    ts = TableStyle([
        ('BACKGROUND',     (0,0),(-1,0),   C['navy']),
        ('FONTSIZE',       (0,0),(-1,-1),  8.5),
        ('ROWBACKGROUNDS', (0,1),(-1,-(len(totali)+1)), [C['white'], C['light']]),
        ('ALIGN',          (1,0),(-1,-1),  'RIGHT'),
        ('ALIGN',          (1,0),(1,-1),   'CENTER'),
        ('VALIGN',         (0,0),(-1,-1),  'MIDDLE'),
        ('TOPPADDING',     (0,0),(-1,-1),  7),
        ('BOTTOMPADDING',  (0,0),(-1,-1),  7),
        ('LEFTPADDING',    (0,0),(0,-1),   10),
        ('LINEBELOW',      (0,0),(-1,-(len(totali)+1)), 0.3, C['border']),
        ('LINEABOVE',      (0,-len(totali)),(-1,-len(totali)), 1.2, C['blue']),
        ('FONTNAME',       (2,-1),(-1,-1), 'Helvetica-Bold'),
        # Sfondo navy header
        ('TEXTCOLOR',      (0,0),(-1,0),   C['white']),
    ])
    mt.setStyle(ts)
    story.append(mt)
    story.append(Spacer(1, 14))

    # ─────────────────────────────────────────────────────────────────────────
    # PAG 4 continua — BUSINESS PLAN
    # ─────────────────────────────────────────────────────────────────────────
    story.append(section_header(
        f'BUSINESS PLAN  —  Scenario {(p.scenario or "realistico").upper()}', C['green']))
    story.append(Spacer(1, 6))

    # ── BOX FORMULA INCASSO ─────────────────────────────────────────────────
    _bp2 = {}
    try:
        import json as _jbp
        _bp2 = _jbp.loads(p.bp_dettaglio_json) if hasattr(p,'bp_dettaglio_json') and p.bp_dettaglio_json else {}
    except Exception:
        _bp2 = {}
    _cli_g2  = float(_bp2.get('clienti_giorno', 0) or 0)
    _spesa2  = float(_bp2.get('spesa_cliente',  0) or 0)
    _giorni2 = float(_bp2.get('giorni_mese',   30) or 30)
    if _cli_g2 == 0 and p.incasso_mese > 0 and _spesa2 > 0:
        _cli_g2 = p.incasso_mese / (_spesa2 * _giorni2)

    class FormulaBox(Flowable):
        def __init__(self, cli_g, spesa, giorni, incasso, width):
            Flowable.__init__(self)
            self.cli_g   = cli_g
            self.spesa   = spesa
            self.giorni  = giorni
            self.incasso = incasso
            self.width   = width
            self.height  = 2.2*cm

        def draw(self):
            c   = self.canv
            w   = self.width
            cli = self.cli_g
            sp  = self.spesa
            gg  = self.giorni
            inc = self.incasso

            c.setFillColor(colors.HexColor('#f0fdf4'))
            c.roundRect(0, 0, w, self.height, 6, fill=1, stroke=0)
            c.setStrokeColor(colors.HexColor('#10b981')); c.setLineWidth(1)
            c.roundRect(0, 0, w, self.height, 6, fill=0, stroke=1)

            c.setFont('Helvetica-Bold', 7); c.setFillColor(colors.HexColor('#065f46'))
            label_formula = 'COME SI CALCOLA L' + chr(39) + 'INCASSO MENSILE'
            c.drawString(0.3*cm, self.height - 0.4*cm, label_formula)

            items = [
                (f'{cli:.1f}',   '#7c3aed', 'clienti/giorno'),
                ('x',            '#94a3b8', ''),
                (f'€{sp:.2f}',   '#1d4ed8', 'spesa/visita'),
                ('x',            '#94a3b8', ''),
                (f'{gg:.0f}',    '#b45309', 'gg/mese'),
                ('=',            '#94a3b8', ''),
                (f'€{inc:,.0f}', '#059669', '/mese'),
            ]
            x = 0.3*cm
            y_val = self.height - 1.0*cm
            y_lbl = self.height - 1.55*cm
            for val, col, lbl in items:
                is_op = val in ('x', '=')
                fs = 7 if is_op else 13
                fn = 'Helvetica' if is_op else 'Helvetica-Bold'
                c.setFont(fn, fs)
                c.setFillColor(colors.HexColor(col))
                tw = c.stringWidth(val, fn, fs)
                c.drawString(x, y_val, val)
                if lbl:
                    c.setFont('Helvetica', 6.5); c.setFillColor(colors.HexColor('#64748b'))
                    c.drawString(x, y_lbl, lbl)
                x += tw + (0.25*cm if not is_op else 0.15*cm)

            if cli < 1:
                ogni = int(round(1/cli)) if cli > 0 else 99
                nota = f'ATTENZIONE: meno di 1 cliente al giorno — 1 ogni {ogni} giorni. Zona a domanda molto bassa.'
                ncol = '#ef4444'
            elif cli < 5:
                nota = f'{int(cli*gg)} clienti stimati al mese — zona a bassa affluenza.'
                ncol = '#f59e0b'
            else:
                nota = f'{int(cli*gg)} clienti stimati al mese — domanda nella norma per questa zona.'
                ncol = '#059669'
            c.setFont('Helvetica', 7.5); c.setFillColor(colors.HexColor(ncol))
            c.drawString(0.3*cm, 0.2*cm, nota)

    story.append(FormulaBox(_cli_g2, _spesa2, _giorni2, p.incasso_mese, PW))
    story.append(Spacer(1, 8))

    story.append(kpi_row([
        ('Investimento + IVA', f'€ {capex_iva:,.0f}',     '#3b82f6'),
        ('Incasso / mese',     f'€ {p.incasso_mese:,.0f}','#10b981'),
        ('Costi / mese',       f'€ {p.costi_mese:,.0f}',  '#ef4444'),
        ('Utile / mese',       f'€ {p.utile_mese:,.0f}',
         '#10b981' if p.utile_mese>=0 else '#ef4444'),
        ('Payback',
         f'{int(p.payback_mesi/12)} anni' if p.payback_mesi else 'N/D', '#f59e0b'),
    ]))
    story.append(Spacer(1, 10))

    # 3 scenari con barra visiva
    class ScenariChart(Flowable):
        def __init__(self, inc, cos, uti, cli_g, spesa, giorni, width):
            Flowable.__init__(self)
            self.inc    = inc
            self.cos    = cos
            self.uti    = uti
            self.cli_g  = cli_g    # clienti/giorno realistico
            self.spesa  = spesa    # spesa media/visita
            self.giorni = giorni   # giorni apertura/mese
            self.width  = width
            self.height = 6.0*cm

        def draw(self):
            c = self.canv
            w = self.width
            giorni = self.giorni or 30
            sc3 = [
                ('Pessimistico ×0.60', self.cli_g*0.60, self.inc*0.60, self.inc*0.60 - self.cos, '#ef4444'),
                ('Realistico   ×1.00', self.cli_g,      self.inc,      self.uti,                  '#3b82f6'),
                ('Ottimistico  ×1.25', self.cli_g*1.25, self.inc*1.25, self.inc*1.25 - self.cos,  '#10b981'),
            ]
            max_inc = max(self.inc*1.25, 1)
            bh  = 16
            gap = 8
            top = self.height - 0.1*cm

            # Intestazioni colonne
            col_cli  = 0
            col_bar  = 2.8*cm
            col_inc  = col_bar + w*0.38 + 0.3*cm
            col_uti  = col_inc + 2.2*cm

            c.setFont('Helvetica-Bold', 7.5); c.setFillColor(C['slate'])
            c.drawString(col_cli,  top, 'Scenario')
            c.drawString(col_bar,  top, 'Clienti/giorno → Incasso/mese')
            c.drawRightString(w,   top, 'Utile/mese')

            c.setStrokeColor(C['border']); c.setLineWidth(0.5)
            c.line(0, top - 0.25*cm, w, top - 0.25*cm)

            for i,(nome,cli_s,inc_s,uti_s,col) in enumerate(sc3):
                by_ = top - 0.65*cm - i*(bh+gap+4)
                # Nome scenario
                c.setFont('Helvetica-Bold' if i==1 else 'Helvetica', 8)
                c.setFillColor(colors.HexColor(col))
                c.drawString(col_cli, by_+4, nome)
                # Clienti/giorno
                c.setFont('Helvetica', 7.5); c.setFillColor(C['slate'])
                c.drawString(col_cli, by_-5, f'{cli_s:.1f} clienti/g  ·  €{inc_s/giorni:.1f}/g')
                # Barra incasso mensile
                bar_max_w = w * 0.37
                c.setFillColor(colors.HexColor('#e2e8f0'))
                c.roundRect(col_bar, by_, bar_max_w, bh, 3, fill=1, stroke=0)
                bw_i = bar_max_w * (inc_s / max_inc)
                c.setFillColor(colors.HexColor(col))
                c.roundRect(col_bar, by_, max(4, bw_i), bh, 3, fill=1, stroke=0)
                # Valore incasso mensile
                c.setFont('Helvetica-Bold', 8.5); c.setFillColor(colors.HexColor(col))
                c.drawString(col_bar + bar_max_w + 0.25*cm, by_+4,
                             f'€ {inc_s:,.0f}/mese')
                # Utile mensile
                uti_col = '#10b981' if uti_s >= 0 else '#ef4444'
                c.setFont('Helvetica-Bold', 9); c.setFillColor(colors.HexColor(uti_col))
                c.drawRightString(w, by_+4, f'€ {uti_s:,.0f}')
                # Separatore leggero
                if i < 2:
                    c.setStrokeColor(C['border']); c.setLineWidth(0.3)
                    c.line(0, by_ - 6, w, by_ - 6)

            # Nota costi fissi
            c.setFont('Helvetica', 7); c.setFillColor(C['slate'])
            c.drawString(0, 0.1*cm,
                f'Costi mensili totali: € {self.cos:,.0f}  '
                f'(fissi: affitto + ammort. + assic.; variabili: energia + acqua scalano con i cicli)')

    # Recupera clienti/giorno e spesa dal dettaglio BP salvato
    _bp_det = {}
    try:
        import json as _j3
        _bp_det = _j3.loads(p.bp_dettaglio_json) if hasattr(p, 'bp_dettaglio_json') and p.bp_dettaglio_json else {}
    except Exception:
        _bp_det = {}
    _cli_g  = float(_bp_det.get('clienti_giorno', 0) or 0)
    _spesa  = float(_bp_det.get('spesa_cliente', 0)  or p.incasso_mese / max((_cli_g * 30), 1))
    _giorni = float(_bp_det.get('giorni_mese', 30)   or 30)
    # Fallback: stima clienti/giorno da incasso se non salvato
    if _cli_g == 0 and p.incasso_mese > 0 and _spesa > 0:
        _cli_g = p.incasso_mese / (_spesa * _giorni)

    story.append(ScenariChart(p.incasso_mese, p.costi_mese, p.utile_mese,
                               _cli_g, _spesa, _giorni, PW))
    story.append(Spacer(1, 14))

    # ─────────────────────────────────────────────────────────────────────────
    # PAG 5 — ANALISI AI
    # ─────────────────────────────────────────────────────────────────────────
    if p.ai_zona:
        ai_text = p.ai_bp or p.ai_zona
        if ai_text:
            story.append(PageBreak())
            story.append(section_header('ANALISI AI  —  Raccomandazione', C['orange']))
            story.append(Spacer(1, 8))
            _render_ai_text(ai_text, story, st, S['body'], S['h2'],
                            C['navy'], C['green'], C['red'], C['orange'],
                            Spacer, Paragraph)

    # ─────────────────────────────────────────────────────────────────────────
    # PAG 6 — CONDIZIONI DI VENDITA
    # ─────────────────────────────────────────────────────────────────────────
    if s and s.condizioni_vendita:
        story.append(PageBreak())
        story.append(section_header('CONDIZIONI DI VENDITA', C['slate']))
        story.append(Spacer(1, 6))
        for line in s.condizioni_vendita.split('\n'):
            if line.strip():
                story.append(Paragraph(line.strip(), S['body']))
                story.append(Spacer(1, 2))

    # ─────────────────────────────────────────────────────────────────────────
    # BUILD + MERGE ALLEGATI
    # ─────────────────────────────────────────────────────────────────────────
    doc.build(story)
    main_buf.seek(0)

    from flask import current_app
    upload_folder = current_app.config.get('UPLOAD_FOLDER', '/tmp')
    allegati = p.get_allegati()
    pdf_all  = [a for a in allegati if isinstance(a,str) and a.lower().endswith('.pdf')]

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
                for pg in PdfReader(path).pages: writer.add_page(pg)
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


