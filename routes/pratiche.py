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
            with _ur2.urlopen(req, timeout=8) as r:
                raw = r.read()
                data = __import__('json').loads(raw)
            print(f'[GEO] {addr} → status={data.get("status")} results={len(data.get("results",[]))}', flush=True)
            if data.get('results'):
                loc = data['results'][0]['geometry']['location']
                return float(loc['lat']), float(loc['lng'])
        except Exception as _ge:
            print(f'[GEO] errore per {addr}: {_ge}', flush=True)
            continue
    print(f'[GEO] Nessun risultato per tutti i tentativi: {tentativi}', flush=True)
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
    except Exception as _me:
        print(f'[PDF] _get_mappa_statica errore: {type(_me).__name__}: {_me}', flush=True)
        return None



@pratiche_bp.route('/pratiche/<int:id>/pdf')
@login_required
def genera_pdf(id):
    """Reindirizza al nuovo pdf_service professionale."""
    try:
        from models.pratica import Pratica
        from models.settings import Settings
        from services.pdf_service import build_pdf
        from flask import send_file, abort
        p = Pratica.query.get_or_404(id)
        if current_user.role not in ('owner', 'admin') and p.agente_id != current_user.id:
            abort(403)
        s   = Settings.query.first()
        buf = build_pdf(p, s)
        nome = f"BIOLavaTU_{p.numero}_{(p.cliente.nome if p.cliente else 'cliente').replace(' ', '_')}.pdf"
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=False, download_name=nome)
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        from flask import current_app
        current_app.logger.error(f"PDF ERROR: {err}")
        return f"<pre>ERRORE PDF:\n{err}</pre>", 500



def _get_cgv_default():
    """Ritorna il testo CGV standard."""
    return None  # viene letto dalle pratiche o dal DB

def _formatta_cgv(cgv_text, h2_s, h3_s, body_j, small, section_title, NAVY, BLUE):
    """Formatta il testo CGV per il PDF."""
    from reportlab.platypus import Paragraph, Spacer, PageBreak
    elements = []
    for el in section_title('Condizioni Generali di Vendita', NAVY):
        elements.append(el)
    for line in cgv_text.split('\n'):
        line = line.strip()
        if not line: elements.append(Spacer(1,4)); continue
        if line.startswith('Art.'): elements.append(Paragraph(line, h3_s))
        elif line.startswith('PARTE') or line.startswith('ALLEGATO'):
            elements.append(Spacer(1,8))
            elements.append(Paragraph(line, h2_s))
        else:
            elements.append(Paragraph(line, body_j))
    return elements


# ═══════════════════════════════════════════════════════════════════════════
# NUOVO PDF — Progetto Lavanderia Self-Service BIOLavaTU
# Struttura: Copertina → Lettera AI → Analisi → BP → Ordine → CGV → Firma
# ═══════════════════════════════════════════════════════════════════════════

def _genera_pdf_interno(id):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, PageBreak, KeepTogether, HRFlowable)
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus.flowables import Flowable
    from pypdf import PdfWriter, PdfReader
    import os, io as _io, json as _json

    p = Pratica.query.get_or_404(id)
    s = Settings.query.first()
    W, H = A4
    PW = W - 4*cm

    # ── PALETTE ──────────────────────────────────────────────────────────────
    NAVY   = colors.HexColor('#0F1F3D')
    BLUE   = colors.HexColor('#2563EB')
    LBLUE  = colors.HexColor('#3B82F6')
    SKY    = colors.HexColor('#DBEAFE')
    SLATE  = colors.HexColor('#64748B')
    LIGHT  = colors.HexColor('#F8FAFC')
    BORDER = colors.HexColor('#E2E8F0')
    WHITE  = colors.white
    GREEN  = colors.HexColor('#059669')
    LGREEN = colors.HexColor('#D1FAE5')
    RED    = colors.HexColor('#DC2626')
    ORANGE = colors.HexColor('#D97706')
    LORNG  = colors.HexColor('#FEF3C7')
    GOLD   = colors.HexColor('#F59E0B')

    # ── DATI AZIENDA ─────────────────────────────────────────────────────────
    company = (s and s.nome_azienda) or 'Rotondi Group Srl'
    web     = (s and s.sito_web)    or 'biolavatu.it'
    tel     = (s and s.telefono)    or '+39 02 0000000'
    via     = (s and s.indirizzo)   or 'Via Vignate 2 · 20019 Settimo Milanese (MI)'
    piva    = (s and s.partita_iva) or ''
    cliente = p.cliente
    nome_cl = cliente.nome_completo if cliente else (p.nome_cliente or 'Cliente')
    citta_p = p.citta or ''
    data_str = p.created.strftime('%d/%m/%Y') if p.created else ''
    num_pr  = p.numero_pratica or ''

    # ── STILI ─────────────────────────────────────────────────────────────────
    def st(name, **kw):
        defaults = dict(fontName='Helvetica', fontSize=9, leading=13,
                        textColor=colors.HexColor('#1E293B'))
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    body    = st('body', fontSize=9.5, leading=14, textColor=colors.HexColor('#334155'))
    body_j  = st('body_j', fontSize=9.5, leading=15, textColor=colors.HexColor('#334155'), alignment=TA_JUSTIFY)
    h1_s    = st('h1_s', fontSize=18, fontName='Helvetica-Bold', textColor=NAVY, spaceBefore=12, spaceAfter=6)
    h2_s    = st('h2_s', fontSize=12, fontName='Helvetica-Bold', textColor=NAVY, spaceBefore=10, spaceAfter=4)
    h3_s    = st('h3_s', fontSize=10, fontName='Helvetica-Bold', textColor=BLUE, spaceBefore=8, spaceAfter=3)
    small   = st('small', fontSize=8, textColor=SLATE, leading=11)
    center  = st('center', fontSize=9, alignment=TA_CENTER)
    bold9   = st('bold9', fontName='Helvetica-Bold', fontSize=9)
    italic9 = st('italic9', fontName='Helvetica-Oblique', fontSize=9, textColor=SLATE)

    # ── HELPER ────────────────────────────────────────────────────────────────
    def eur(v):
        try: return f'€ {float(v or 0):,.0f}'.replace(',', '.')
        except: return '—'

    def kv_table(rows, col_w=None):
        cw = col_w or [4*cm, PW-4*cm]
        data = [[Paragraph(str(k), bold9), Paragraph(str(v), body)] for k,v in rows]
        t = Table(data, colWidths=cw)
        t.setStyle(TableStyle([
            ('VALIGN',    (0,0),(-1,-1), 'TOP'),
            ('ROWBACKGROUNDS', (0,0),(-1,-1), [LIGHT, WHITE]),
            ('LINEBELOW', (0,0),(-1,-1), 0.3, BORDER),
            ('PADDING',   (0,0),(-1,-1), 5),
        ]))
        return t

    def section_title(txt, color=NAVY):
        elements = []
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width=PW, thickness=2, color=color, spaceAfter=4))
        elements.append(Paragraph(txt.upper(), st('sec', fontSize=11,
            fontName='Helvetica-Bold', textColor=color)))
        elements.append(HRFlowable(width=PW, thickness=0.5, color=BORDER, spaceAfter=6))
        return elements

    # ── FOOTER ────────────────────────────────────────────────────────────────
    def on_page(canvas, doc):
        canvas.saveState()
        # Footer navy
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, W, 0.8*cm, fill=1, stroke=0)
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(WHITE)
        canvas.drawString(1*cm, 0.52*cm, f'{company}  ·  {via}')
        if piva: canvas.drawString(1*cm, 0.22*cm, f'P.IVA {piva}')
        canvas.drawRightString(W-1*cm, 0.52*cm, f'{web}  ·  {tel}')
        canvas.drawRightString(W-1*cm, 0.22*cm,
            f'Progetto {num_pr}  ·  Pag. {doc.page}')
        # Logo BIOLavaTU piccolo in basso a dx
        canvas.setFont('Helvetica-Bold', 9)
        canvas.setFillColor(colors.HexColor('#3B82F6'))
        canvas.drawRightString(W-1*cm, 0.52*cm, 'BIOLavaTU')
        canvas.restoreState()

    # ── DOCUMENTO ────────────────────────────────────────────────────────────
    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=1.8*cm,
        onPage=on_page, onLaterPages=on_page)
    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 1 — COPERTINA
    # ══════════════════════════════════════════════════════════════════════════
    class Cover(Flowable):
        def wrap(self, aw, ah): return aw, ah
        def draw(self):
            c = self.canv
            w, h = W - 4*cm, H - 4*cm  # area utile

            # Sfondo navy superiore (60% pagina)
            c.setFillColor(NAVY)
            c.rect(-2*cm, h*0.38, W, h*0.62+2*cm, fill=1, stroke=0)

            # Fascia blu diagonale decorativa
            c.setFillColor(BLUE)
            from reportlab.graphics.shapes import Polygon
            p_path = c.beginPath()
            p_path.moveTo(-2*cm, h*0.38)
            p_path.lineTo(W-2*cm, h*0.38)
            p_path.lineTo(W-2*cm, h*0.42)
            p_path.lineTo(-2*cm, h*0.45)
            p_path.close()
            c.drawPath(p_path, fill=1, stroke=0)

            # Titolo principale
            c.setFont('Helvetica-Bold', 26)
            c.setFillColor(WHITE)
            c.drawString(0, h*0.75, 'PROGETTO LAVANDERIA')
            c.setFont('Helvetica-Bold', 22)
            c.setFillColor(colors.HexColor('#93C5FD'))
            c.drawString(0, h*0.68, 'SELF-SERVICE BIOLavaTU')

            # Linea oro
            c.setStrokeColor(GOLD)
            c.setLineWidth(2)
            c.line(0, h*0.65, PW*0.5, h*0.65)

            # Numero pratica e data
            c.setFont('Helvetica', 10)
            c.setFillColor(colors.HexColor('#94A3B8'))
            c.drawString(0, h*0.61, f'Rif. {num_pr}  ·  {data_str}')

            # Nome cliente (grande)
            c.setFont('Helvetica-Bold', 16)
            c.setFillColor(WHITE)
            c.drawString(0, h*0.54, f'Progetto per:')
            c.setFont('Helvetica-Bold', 20)
            c.setFillColor(GOLD)
            c.drawString(0, h*0.47, nome_cl)

            # Città
            c.setFont('Helvetica', 12)
            c.setFillColor(colors.HexColor('#93C5FD'))
            c.drawString(0, h*0.41, citta_p)

            # Sezione bianca inferiore
            c.setFillColor(WHITE)
            c.rect(-2*cm, -2*cm, W, h*0.40, fill=1, stroke=0)

            # KPI principali nella sezione bianca
            try:
                capex = float(p.capex or 0)
                capex_iva = capex * 1.22
                incasso = float(p.incasso_mese or 0)
                score = int(p.score_zona or 0)
            except: capex_iva = incasso = score = 0

            kpis = [
                ('INVESTIMENTO', eur(capex_iva), NAVY),
                ('INCASSO / MESE', eur(incasso), GREEN),
                ('SCORE ZONA', f'{score}/100', BLUE),
            ]
            kw = PW / len(kpis)
            for i, (lbl, val, col) in enumerate(kpis):
                x = i * kw
                # Box
                c.setFillColor(colors.HexColor('#F8FAFC'))
                c.roundRect(x, h*0.08, kw-0.3*cm, h*0.22, 6, fill=1, stroke=0)
                c.setStrokeColor(col)
                c.setLineWidth(1.5)
                c.roundRect(x, h*0.08, kw-0.3*cm, h*0.22, 6, fill=0, stroke=1)
                # Valore
                c.setFont('Helvetica-Bold', 16)
                c.setFillColor(col)
                c.drawCentredString(x + kw/2 - 0.15*cm, h*0.20, val)
                # Label
                c.setFont('Helvetica', 7.5)
                c.setFillColor(SLATE)
                c.drawCentredString(x + kw/2 - 0.15*cm, h*0.11, lbl)

            # ── LOGO BIOLavaTU GROSSO CENTRALE nella sezione bianca ──────────────
            # Sfondo azzurro morbido per il logo
            c.setFillColor(colors.HexColor('#EFF6FF'))
            c.roundRect(PW*0.15, h*0.30, PW*0.70, h*0.07, 8, fill=1, stroke=0)

            # "BIO" in grande blu
            c.setFont('Helvetica-Bold', 38)
            c.setFillColor(BLUE)
            c.drawCentredString(PW*0.37, h*0.34, 'BIO')

            # "LavaTU" in navy
            c.setFont('Helvetica-Bold', 38)
            c.setFillColor(NAVY)
            c.drawCentredString(PW*0.63, h*0.34, 'LavaTU')

            # Sottotitolo brand
            c.setFont('Helvetica', 9)
            c.setFillColor(SLATE)
            c.drawCentredString(PW/2, h*0.30, 'LaundryPro Platform')

            # Linea oro sotto il logo
            c.setStrokeColor(GOLD)
            c.setLineWidth(1.5)
            c.line(PW*0.25, h*0.29, PW*0.75, h*0.29)

            # ── PIÈ DI PAGINA COPERTINA — dati Rotondi Group in basso a dx ──────────
            c.setFillColor(NAVY)
            c.rect(-2*cm, -2*cm, W, 1.2*cm, fill=1, stroke=0)

            # Dati Rotondi Group — solo lato destro
            c.setFont('Helvetica-Bold', 8.5)
            c.setFillColor(colors.HexColor('#93C5FD'))
            c.drawRightString(PW, -0.4*cm, company)
            c.setFont('Helvetica', 7.5)
            c.setFillColor(colors.HexColor('#94A3B8'))
            c.drawRightString(PW, -0.85*cm, via)
            c.setFont('Helvetica', 7)
            c.setFillColor(colors.HexColor('#64748B'))
            c.drawRightString(PW, -1.25*cm, web + '  ·  ' + tel + (f'  ·  P.IVA {piva}' if piva else ''))

    story.append(Cover())
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 2 — LETTERA DI PRESENTAZIONE (generata da AI)
    # ══════════════════════════════════════════════════════════════════════════
    for el in section_title('Lettera di Presentazione', NAVY): story.append(el)

    # Intestazione lettera
    story.append(Spacer(1, 8))
    story.append(Paragraph(f'Settimo Milanese, {data_str}', st('date', fontSize=9, textColor=SLATE, alignment=TA_RIGHT)))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f'Gentile {nome_cl},', h2_s))
    story.append(Spacer(1, 8))

    # Lettera AI personalizzata
    lettera_ai = getattr(p, 'lettera_presentazione', None) or ''
    if not lettera_ai:
        # Genera al momento se non esiste
        try:
            import anthropic as _ant, os as _os
            _client = _ant.Anthropic(api_key=_os.environ.get('ANTHROPIC_API_KEY'))
            mac_txt = ''
            try:
                mac_list = _json.loads(p.macchine_json or '[]')
                mac_txt = ', '.join([f"{m.get('qty',1)}× {m.get('nome','')}" for m in mac_list if m.get('nome')])
            except: pass
            _prompt = f"""Scrivi una lettera di presentazione commerciale professionale per un progetto di lavanderia self-service BIOLavaTU.

Cliente: {nome_cl}
Città: {citta_p}
Macchine selezionate: {mac_txt or 'configurazione standard'}
Score zona: {p.score_zona or 'N/D'}/100 ({p.score_label or ''})
Investimento: {eur(float(p.capex or 0)*1.22)}
Incasso stimato: {eur(p.incasso_mese)}/mese

La lettera deve:
- Essere indirizzata personalmente al cliente
- Presentare il progetto BIOLavaTU come opportunità imprenditoriale
- Citare brevemente la zona analizzata e le sue caratteristiche
- Menzionare la configurazione macchine scelta
- Comunicare la solidità e l'esperienza di Rotondi Group (dal 1972)
- Essere professionale ma calorosa, 3-4 paragrafi
- Concludere con disponibilità per chiarimenti
- NON includere intestazione né firma (vengono aggiunte a parte)
- Rispondere solo con il testo della lettera, niente altro"""
            _resp = _client.messages.create(
                model='claude-sonnet-4-5', max_tokens=800,
                messages=[{'role':'user','content':_prompt}])
            lettera_ai = _resp.content[0].text.strip()
            # Salva per riuso
            try:
                p.lettera_presentazione = lettera_ai
                from app import db as _db
                _db.session.commit()
            except: pass
        except Exception as _e:
            lettera_ai = (f'Con piacere Le presentiamo il progetto di lavanderia self-service BIOLavaTU '
                         f'sviluppato appositamente per {citta_p}. '
                         f'L\'analisi della zona ha evidenziato un potenziale significativo per questo tipo di attività. '
                         f'Rotondi Group, con oltre 50 anni di esperienza nel settore, è il partner ideale per realizzare '
                         f'il Suo progetto imprenditoriale con macchine di qualità professionale e supporto completo. '
                         f'Restiamo a disposizione per qualsiasi chiarimento.')

    for para in lettera_ai.split('\n\n'):
        if para.strip():
            story.append(Paragraph(para.strip(), body_j))
            story.append(Spacer(1, 6))

    # Firma lettera
    story.append(Spacer(1, 16))
    story.append(Paragraph('Cordiali saluti,', body))
    story.append(Spacer(1, 4))
    story.append(Paragraph('<b>Rotondi Group Srl — Team BIOLavaTU</b>', bold9))
    story.append(Paragraph(f'{web}  ·  {tel}', small))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 3-4 — ANALISI DI ZONA
    # ══════════════════════════════════════════════════════════════════════════
    for el in section_title('Analisi della Zona', BLUE): story.append(el)

    # Dati sede
    story.append(Paragraph('Dati della sede analizzata', h3_s))
    story.append(kv_table([
        ('Indirizzo', f'{p.indirizzo or ""}, {p.citta or ""}'),
        ('Superficie locale', f'{p.mq or 60} mq'),
        ('Affitto mensile', eur(p.affitto_mese) if p.affitto_mese else 'Locale di proprietà'),
        ('Data analisi', data_str),
    ]))
    story.append(Spacer(1, 10))

    # Score zona
    score_val = int(p.score_zona or 0)
    score_lbl = p.score_label or '—'
    score_col = GREEN if score_val >= 65 else ORANGE if score_val >= 45 else RED
    story.append(Paragraph('Valutazione della zona', h3_s))
    score_data = [[
        Paragraph(f'<b>{score_val}/100</b>', st('sv', fontSize=28, fontName='Helvetica-Bold',
            textColor=score_col, alignment=TA_CENTER)),
        Paragraph(f'<b>{score_lbl}</b>\n\nIndice composto da: densità demografica, età media, reddito, traffico pedonale, GDO vicine, pressione competitiva.',
            st('sl', fontSize=10, textColor=colors.HexColor('#334155'))),
    ]]
    t_score = Table(score_data, colWidths=[3.5*cm, PW-3.5*cm])
    t_score.setStyle(TableStyle([
        ('VALIGN',  (0,0),(-1,-1), 'MIDDLE'),
        ('BACKGROUND',(0,0),(0,0), LIGHT),
        ('ROUNDEDCORNERS', [6]),
        ('BOX', (0,0),(-1,-1), 1.5, score_col),
        ('PADDING',(0,0),(-1,-1), 10),
    ]))
    story.append(t_score)
    story.append(Spacer(1, 10))

    # Dati demografici
    story.append(Paragraph('Dati demografici ISTAT', h3_s))
    pop3  = int(p.pop_3min or 0)
    pop5  = int(getattr(p,'pop_5min',0) or 0)
    pop10 = int(getattr(p,'pop_10min',0) or 0)
    dem_rows = [
        ('Popolazione 3 min (~240m)', f'{pop3:,} abitanti — bacino primario'),
        ('Popolazione 5 min (~400m)', f'{pop5:,} abitanti — bacino secondario'),
        ('Popolazione 10 min (~800m)', f'{pop10:,} abitanti — bacino terziario'),
        ('Densità abitativa', f'{int(getattr(p,"densita",200) or 200):,} ab/km²'),
        ('Età media zona', f'{getattr(p,"eta_media",46) or 46} anni'),
        ('Reddito medio', eur(getattr(p,"reddito_medio",20000))),
        ('Concorrenti self-service 500m', str(p.concorrenti_500m or 0)),
        ('Lavanderie totali 1km', str(p.concorrenti_1km or 0)),
        ('Clienti/giorno stimati', f'{float(p.clienti_g or 0):.1f} clienti/giorno'),
    ]
    story.append(kv_table(dem_rows))
    story.append(Spacer(1, 10))

    # Mappa zona
    for el in section_title('Mappa della Zona', BLUE): story.append(el)
    gmaps_key = os.environ.get('GMAPS_KEY','')
    _map_lat = float(p.lat or 0)
    _map_lng = float(p.lng or 0)
    if (not _map_lat or not _map_lng) and gmaps_key:
        _map_lat, _map_lng = _geocodifica_indirizzo(p.indirizzo, p.citta, gmaps_key)
    if _map_lat and _map_lng and gmaps_key:
        try:
            import urllib.request as _ur, urllib.parse as _up
            _murl = (f'https://maps.googleapis.com/maps/api/staticmap'
                     f'?center={_map_lat},{_map_lng}&zoom=15&size=640x320&scale=2'
                     f'&maptype=roadmap&style=feature:poi|visibility:simplified'
                     f'&markers=color:blue%7Clabel:S%7C{_map_lat},{_map_lng}'
                     f'&path=color:0x2563EB88|fillcolor:0x2563EB22|weight:2'
                     f'&key={gmaps_key}')
            _mreq = _ur.Request(_murl, headers={'User-Agent':'BIOLavaTU-PDF'})
            with _ur.urlopen(_mreq, timeout=8) as _mr:
                _mb = _mr.read()
            if _mb:
                from reportlab.platypus import Image as RLImage
                _img_w = PW
                _img_h = _img_w * 320 / 640
                _io2 = _io.BytesIO(_mb)
                story.append(RLImage(_io2, width=_img_w, height=_img_h))
        except: pass
    story.append(Spacer(1, 6))

    # Analisi AI zona
    if p.ai_zona:
        for el in section_title('Analisi Territoriale', BLUE): story.append(el)
        story.extend(_formatta_ai(p.ai_zona, body_j, h3_s, small))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 5 — BUSINESS PLAN
    # ══════════════════════════════════════════════════════════════════════════
    for el in section_title('Business Plan', GREEN): story.append(el)

    try:
        capex     = float(p.capex or 0)
        capex_iva = capex * 1.22
        incasso   = float(p.incasso_mese or 0)
        costi     = float(p.costi_mese or 0)
        utile     = float(p.utile_mese or 0)
        payback   = float(p.payback_mesi or 0)
        cli_g     = float(p.clienti_g or 0)
        spesa_v   = float(p.spesa_visita or 0)
    except: capex=capex_iva=incasso=costi=utile=payback=cli_g=spesa_v=0

    # Formula incasso
    story.append(Paragraph('Come si calcola l\'incasso mensile', h3_s))
    formula_data = [[
        Paragraph(f'<b>{cli_g:.1f}</b>', st('f1',fontSize=18,fontName='Helvetica-Bold',textColor=NAVY,alignment=TA_CENTER)),
        Paragraph('×', st('fx',fontSize=16,textColor=SLATE,alignment=TA_CENTER)),
        Paragraph(f'<b>{eur(spesa_v)}</b>', st('f2',fontSize=16,fontName='Helvetica-Bold',textColor=BLUE,alignment=TA_CENTER)),
        Paragraph('×', st('fx',fontSize=16,textColor=SLATE,alignment=TA_CENTER)),
        Paragraph('<b>30</b>', st('f3',fontSize=16,fontName='Helvetica-Bold',textColor=NAVY,alignment=TA_CENTER)),
        Paragraph('=', st('fx',fontSize=16,textColor=SLATE,alignment=TA_CENTER)),
        Paragraph(f'<b>{eur(incasso)}</b>', st('f4',fontSize=18,fontName='Helvetica-Bold',textColor=GREEN,alignment=TA_CENTER)),
    ]]
    formula_lbl = [[
        Paragraph('clienti/g', st('fl',fontSize=7,textColor=SLATE,alignment=TA_CENTER)),
        Paragraph('', small),
        Paragraph('spesa/visita', st('fl',fontSize=7,textColor=SLATE,alignment=TA_CENTER)),
        Paragraph('', small),
        Paragraph('gg/mese', st('fl',fontSize=7,textColor=SLATE,alignment=TA_CENTER)),
        Paragraph('', small),
        Paragraph('/mese', st('fl',fontSize=7,textColor=SLATE,alignment=TA_CENTER)),
    ]]
    cw7 = [PW/7]*7
    tf = Table(formula_data+formula_lbl, colWidths=cw7)
    tf.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BACKGROUND',(0,0),(-1,0),LIGHT),
        ('BOX',(0,0),(-1,0),1,BORDER),
        ('PADDING',(0,0),(-1,-1),6),
    ]))
    story.append(tf)
    story.append(Spacer(1, 10))

    # KPI economici
    story.append(Paragraph('Indicatori economici', h3_s))
    kpi_data = [
        ['Investimento + IVA 22%', eur(capex_iva), 'BLUE'],
        ['Incasso mensile (scenario realistico)', eur(incasso), 'GREEN'],
        ['Costi mensili totali', eur(costi), 'RED'],
        ['Utile netto mensile', eur(utile), 'GREEN' if utile >= 0 else 'RED'],
        ['Payback investimento', f'{payback/12:.1f} anni' if payback > 0 else 'N/D', 'ORANGE'],
    ]
    kpi_rows = []
    for lbl, val, col_name in kpi_data:
        c_obj = {'BLUE':BLUE,'GREEN':GREEN,'RED':RED,'ORANGE':ORANGE}[col_name]
        kpi_rows.append([
            Paragraph(lbl, body),
            Paragraph(f'<b>{val}</b>', st('kv', fontSize=10, fontName='Helvetica-Bold',
                textColor=c_obj, alignment=TA_RIGHT)),
        ])
    tk = Table(kpi_rows, colWidths=[PW*0.65, PW*0.35])
    tk.setStyle(TableStyle([
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[LIGHT,WHITE]),
        ('LINEBELOW',(0,0),(-1,-1),0.3,BORDER),
        ('PADDING',(0,0),(-1,-1),7),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))
    story.append(tk)
    story.append(Spacer(1, 10))

    # 3 scenari
    story.append(Paragraph('Scenari di sviluppo', h3_s))
    sc_header = [Paragraph(t, st('sh',fontName='Helvetica-Bold',fontSize=9,
        textColor=WHITE,alignment=TA_CENTER))
        for t in ['Scenario','Clienti/g','Incasso/mese','Utile/mese']]
    sc_rows = [sc_header]
    for mult, nome, bg in [(0.6,'Pessimistico',LGREEN),(1.0,'Realistico',LIGHT),(1.25,'Ottimistico',LGREEN)]:
        inc_s = incasso * mult
        ut_s  = inc_s - costi
        bg_row = colors.HexColor('#FEE2E2') if mult==0.6 and ut_s<0 else (LGREEN if ut_s>0 else LORNG)
        sc_rows.append([
            Paragraph(nome, st('sn',fontName='Helvetica-Bold',fontSize=9)),
            Paragraph(f'{cli_g*mult:.1f}', st('sv2',fontSize=9,alignment=TA_CENTER)),
            Paragraph(eur(inc_s), st('si',fontSize=9,alignment=TA_RIGHT)),
            Paragraph(f'<b>{eur(ut_s)}</b>', st('su',fontSize=9,fontName='Helvetica-Bold',
                textColor=GREEN if ut_s>=0 else RED, alignment=TA_RIGHT)),
        ])
    ts = Table(sc_rows, colWidths=[PW*0.28,PW*0.18,PW*0.27,PW*0.27])
    ts.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[LIGHT,WHITE,LGREEN]),
        ('LINEBELOW',(0,0),(-1,-1),0.3,BORDER),
        ('PADDING',(0,0),(-1,-1),7),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BOX',(0,0),(-1,-1),1,BORDER),
    ]))
    story.append(ts)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 6 — ORDINE MACCHINE
    # ══════════════════════════════════════════════════════════════════════════
    for el in section_title('Ordine Macchine e Accessori', NAVY): story.append(el)

    story.append(Paragraph(
        f'Configurazione selezionata per il progetto di <b>{nome_cl}</b> — {citta_p}', body))
    story.append(Spacer(1, 8))

    # Tabella macchine SENZA prezzi unitari
    try:
        mac_list = _json.loads(p.macchine_json or '[]')
    except: mac_list = []

    mac_header = [Paragraph(t, st('mh',fontName='Helvetica-Bold',fontSize=9,
        textColor=WHITE, alignment=TA_CENTER))
        for t in ['N°', 'Descrizione macchina / Accessorio', 'Categoria', 'Qtà']]
    mac_rows = [mac_header]
    n_mac = 0
    for i, m in enumerate(mac_list, 1):
        nome_m = m.get('nome','') or m.get('descrizione','')
        cat_m  = m.get('categoria','') or ''
        qty_m  = m.get('qty', 1)
        if nome_m:
            n_mac += 1
            bg_r = LIGHT if i%2==0 else WHITE
            mac_rows.append([
                Paragraph(str(i), st('mn',fontSize=9,alignment=TA_CENTER)),
                Paragraph(f'<b>{nome_m}</b>', st('md',fontSize=9,fontName='Helvetica-Bold')),
                Paragraph(cat_m, st('mc',fontSize=8,textColor=SLATE)),
                Paragraph(str(qty_m), st('mq2',fontSize=9,alignment=TA_CENTER,fontName='Helvetica-Bold')),
            ])

    if n_mac == 0:
        mac_rows.append([Paragraph('—',body), Paragraph('Nessuna macchina selezionata',body),
                         Paragraph('',body), Paragraph('',body)])

    tm = Table(mac_rows, colWidths=[1*cm, PW*0.55, PW*0.25, 1.5*cm])
    tm.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), NAVY),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[LIGHT,WHITE]),
        ('LINEBELOW',(0,0),(-1,-1),0.3,BORDER),
        ('PADDING',(0,0),(-1,-1),7),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BOX',(0,0),(-1,-1),1,BORDER),
    ]))
    story.append(tm)
    story.append(Spacer(1, 10))

    # Totale (solo totale + IVA, no prezzi unitari)
    story.append(Spacer(1, 4))
    tot_data = [
        [Paragraph('Imponibile', st('ti',fontSize=10,fontName='Helvetica-Bold',textColor=NAVY)),
         Paragraph(eur(capex), st('tv',fontSize=10,fontName='Helvetica-Bold',textColor=NAVY,alignment=TA_RIGHT))],
        [Paragraph('IVA 22%', st('ti2',fontSize=9,textColor=SLATE)),
         Paragraph(eur(capex*0.22), st('tv2',fontSize=9,textColor=SLATE,alignment=TA_RIGHT))],
        [Paragraph('<b>TOTALE IVA INCLUSA</b>', st('tt',fontSize=12,fontName='Helvetica-Bold',textColor=WHITE)),
         Paragraph(f'<b>{eur(capex_iva)}</b>', st('ttv',fontSize=14,fontName='Helvetica-Bold',
            textColor=WHITE,alignment=TA_RIGHT))],
    ]
    tt = Table(tot_data, colWidths=[PW*0.6, PW*0.4])
    tt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,1),LIGHT),
        ('BACKGROUND',(0,2),(-1,2),NAVY),
        ('LINEBELOW',(0,0),(-1,1),0.5,BORDER),
        ('PADDING',(0,0),(-1,-1),9),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BOX',(0,0),(-1,-1),1.5,NAVY),
    ]))
    story.append(tt)
    story.append(Spacer(1, 14))

    # Condizioni di pagamento
    for el in section_title('Condizioni di Pagamento', NAVY): story.append(el)
    pag_data = [
        [Paragraph('Tranche', st('ph',fontName='Helvetica-Bold',fontSize=9,textColor=WHITE,alignment=TA_CENTER)),
         Paragraph('%', st('ph',fontName='Helvetica-Bold',fontSize=9,textColor=WHITE,alignment=TA_CENTER)),
         Paragraph('Importo', st('ph',fontName='Helvetica-Bold',fontSize=9,textColor=WHITE,alignment=TA_CENTER)),
         Paragraph('Scadenza', st('ph',fontName='Helvetica-Bold',fontSize=9,textColor=WHITE,alignment=TA_CENTER))],
        [Paragraph('1° Acconto', bold9),
         Paragraph('40%', st('pc',fontSize=9,alignment=TA_CENTER,fontName='Helvetica-Bold',textColor=BLUE)),
         Paragraph(eur(capex_iva*0.40), st('pv',fontSize=9,alignment=TA_RIGHT,fontName='Helvetica-Bold',textColor=BLUE)),
         Paragraph('All\'accettazione dell\'ordine / firma contratto', body)],
        [Paragraph('2° Acconto', bold9),
         Paragraph('40%', st('pc2',fontSize=9,alignment=TA_CENTER,fontName='Helvetica-Bold',textColor=NAVY)),
         Paragraph(eur(capex_iva*0.40), st('pv2',fontSize=9,alignment=TA_RIGHT,fontName='Helvetica-Bold',textColor=NAVY)),
         Paragraph('Ad avviso macchine pronte / pronto-spedizione', body)],
        [Paragraph('Saldo parziale', bold9),
         Paragraph('15%', st('pc3',fontSize=9,alignment=TA_CENTER,fontName='Helvetica-Bold',textColor=ORANGE)),
         Paragraph(eur(capex_iva*0.15), st('pv3',fontSize=9,alignment=TA_RIGHT,fontName='Helvetica-Bold',textColor=ORANGE)),
         Paragraph('Allo scarico / consegna in cantiere', body)],
        [Paragraph('Saldo finale', bold9),
         Paragraph('5%', st('pc4',fontSize=9,alignment=TA_CENTER,fontName='Helvetica-Bold',textColor=GREEN)),
         Paragraph(eur(capex_iva*0.05), st('pv4',fontSize=9,alignment=TA_RIGHT,fontName='Helvetica-Bold',textColor=GREEN)),
         Paragraph('Al collaudo funzionale con verbale firmato', body)],
    ]
    tp = Table(pag_data, colWidths=[3*cm, 1.5*cm, 3*cm, PW-7.5*cm])
    tp.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[LIGHT,WHITE,LIGHT,WHITE]),
        ('LINEBELOW',(0,0),(-1,-1),0.3,BORDER),
        ('PADDING',(0,0),(-1,-1),8),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BOX',(0,0),(-1,-1),1,BORDER),
    ]))
    story.append(tp)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAG 7+ — CONDIZIONI GENERALI DI VENDITA
    # ══════════════════════════════════════════════════════════════════════════
    cgv_text = getattr(p, 'cgv_text', None)
    if not cgv_text:
        cgv_text = _get_cgv_default()

    if cgv_text:
        story.extend(_formatta_cgv(cgv_text, h2_s, h3_s, body_j, small, section_title, NAVY, BLUE))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # ULTIMA PAG — FIRME
    # ══════════════════════════════════════════════════════════════════════════
    for el in section_title('Accettazione e Firme', NAVY): story.append(el)

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f'Il sottoscritto <b>{nome_cl}</b> dichiara di aver letto, compreso e accettato '
        f'integralmente il presente documento "Progetto Lavanderia Self-Service BIOLavaTU" '
        f'composto da: Lettera di Presentazione, Analisi di Zona, Business Plan, '
        f'Ordine Macchine e Condizioni Generali di Vendita.', body_j))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'Ai sensi degli artt. 1341 e 1342 c.c., il Cliente approva specificamente: '
        'Art. 5 (Pagamenti), Art. 8 (Riserva di proprietà), Art. 9 (Limitazione responsabilità), '
        'Art. 11 (Recesso), Art. 12 (Foro competente), Art. 15 (Esclusività detergenti), '
        'Art. 19 (SLA).', body_j))
    story.append(Spacer(1, 24))

    # Box firme
    firma_data = [
        # Intestazioni
        [Paragraph('<b>Per ROTONDI GROUP Srl</b>', st('fh',fontSize=9,fontName='Helvetica-Bold',
            textColor=WHITE, alignment=TA_CENTER)),
         Paragraph('<b>Per il CLIENTE</b>', st('fh2',fontSize=9,fontName='Helvetica-Bold',
            textColor=WHITE, alignment=TA_CENTER))],
        # Spazio firma
        [Paragraph(' ', st('fs',fontSize=40)), Paragraph(' ', st('fs2',fontSize=40))],
        # Linee
        [Paragraph('_'*35, st('fl2',fontSize=9,textColor=SLATE,alignment=TA_CENTER)),
         Paragraph('_'*35, st('fl3',fontSize=9,textColor=SLATE,alignment=TA_CENTER))],
        # Label
        [Paragraph('Il Legale Rappresentante\nFirma e timbro', st('flb',fontSize=8,textColor=SLATE,alignment=TA_CENTER)),
         Paragraph(f'{nome_cl}\nFirma', st('flb2',fontSize=8,textColor=SLATE,alignment=TA_CENTER))],
        # Data
        [Paragraph('Data: _____ / _____ / _________', st('fd',fontSize=9,textColor=SLATE,alignment=TA_CENTER)),
         Paragraph('Data: _____ / _____ / _________', st('fd2',fontSize=9,textColor=SLATE,alignment=TA_CENTER))],
    ]
    tf2 = Table(firma_data, colWidths=[PW/2-0.5*cm, PW/2-0.5*cm], spaceBefore=10)
    tf2.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),
        ('BACKGROUND',(0,1),(-1,-1),LIGHT),
        ('BOX',(0,0),(0,-1),1,BORDER),
        ('BOX',(1,0),(1,-1),1,BORDER),
        ('PADDING',(0,0),(-1,-1),10),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEBELOW',(0,2),(-1,2),0.5,SLATE),
    ]))
    story.append(tf2)

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width=PW, thickness=0.5, color=BORDER))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f'{company}  ·  {via}  ·  P.IVA {piva}\n{web}  ·  {tel}',
        st('final', fontSize=7.5, textColor=SLATE, alignment=TA_CENTER)))

    # ── BUILD ────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    return buf.read()

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



