from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file, flash
from flask_login import login_required, current_user
from app import db
from models.pratica import Pratica
from models.cliente import Cliente
from models.settings import Settings
import io, os

pratiche_bp = Blueprint('pratiche', __name__)
clienti_bp  = Blueprint('clienti', __name__)
admin_bp    = Blueprint('admin', __name__)
pdf_bp      = Blueprint('pdf', __name__)

# ── PRATICHE ──────────────────────────────────────────────────────────────────

@pratiche_bp.route('/pratiche')
@login_required
def lista():
    q = Pratica.query
    if not current_user.is_admin:
        q = q.filter_by(agente_id=current_user.id)
    stato  = request.args.get('stato', '')
    search = request.args.get('q', '')
    if stato:
        q = q.filter_by(stato=stato)
    if search:
        q = q.join(Cliente).filter(Cliente.nome.ilike(f'%{search}%'))
    pratiche = q.order_by(Pratica.created.desc()).all()
    return render_template('pratiche.html', pratiche=pratiche,
                           stato=stato, search=search)


@pratiche_bp.route('/pratiche/<int:pid>')
@login_required
def dettaglio(pid):
    p = Pratica.query.get_or_404(pid)
    if not current_user.is_admin and p.agente_id != current_user.id:
        return 'Non autorizzato', 403
    gmaps_key = os.environ.get('GMAPS_KEY', '')
    return render_template('pratica_dettaglio.html', p=p,
                           competitors=p.get_competitors(),
                           gmaps_key=gmaps_key)


@pratiche_bp.route('/pratiche/<int:pid>/stato', methods=['POST'])
@login_required
def aggiorna_stato(pid):
    p = Pratica.query.get_or_404(pid)
    if not current_user.is_admin and p.agente_id != current_user.id:
        return jsonify({'error': 'Non autorizzato'}), 403
    p.stato = request.json.get('stato', p.stato)
    db.session.commit()
    return jsonify({'ok': True})


@pratiche_bp.route('/pratiche/<int:pid>/elimina', methods=['POST'])
@login_required
def elimina(pid):
    if not current_user.is_admin:
        return jsonify({'error': 'Solo admin'}), 403
    p = Pratica.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'ok': True})


# ── CLIENTI ───────────────────────────────────────────────────────────────────

@clienti_bp.route('/clienti')
@login_required
def lista():
    search   = request.args.get('q', '')
    q        = Cliente.query
    if search:
        q = q.filter(Cliente.nome.ilike(f'%{search}%') |
                     Cliente.email.ilike(f'%{search}%') |
                     Cliente.citta.ilike(f'%{search}%'))
    clienti = q.order_by(Cliente.nome).all()
    return render_template('clienti.html', clienti=clienti, search=search)


@clienti_bp.route('/clienti/nuovo', methods=['POST'])
@login_required
def nuovo():
    d = request.get_json()
    c = Cliente(
        nome=d['nome'], email=d.get('email',''), telefono=d.get('telefono',''),
        piva=d.get('piva',''), tipo=d.get('tipo','Privato'),
        citta=d.get('citta',''), note=d.get('note',''),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({'ok': True, 'id': c.id, 'cliente': c.to_dict()})


@clienti_bp.route('/clienti/<int:cid>/modifica', methods=['POST'])
@login_required
def modifica(cid):
    c = Cliente.query.get_or_404(cid)
    d = request.get_json()
    for k in ('nome','email','telefono','piva','tipo','citta','note'):
        if k in d:
            setattr(c, k, d[k])
    db.session.commit()
    return jsonify({'ok': True})


@clienti_bp.route('/clienti/<int:cid>/elimina', methods=['POST'])
@login_required
def elimina(cid):
    if not current_user.is_admin:
        return jsonify({'error': 'Solo admin'}), 403
    c = Cliente.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'ok': True})


@clienti_bp.route('/clienti/export')
@login_required
def export_csv():
    import csv
    from io import StringIO
    si = StringIO()
    w  = csv.writer(si, delimiter=';')
    w.writerow(['Nome','Email','Telefono','P.IVA','Tipo','Città','Note'])
    for c in Cliente.query.order_by(Cliente.nome).all():
        w.writerow([c.nome, c.email, c.telefono, c.piva, c.tipo, c.citta, c.note])
    output = io.BytesIO(('\ufeff' + si.getvalue()).encode('utf-8'))
    return send_file(output, mimetype='text/csv',
                     as_attachment=True, download_name='clienti_biolavatu.csv')


# ── ADMIN ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/admin')
@login_required
def index():
    if not current_user.is_admin:
        return redirect(url_for('dashboard.index'))
    from models.user import User
    users    = User.query.all()
    settings = Settings.query.first()
    return render_template('admin.html', users=users, settings=settings)


@admin_bp.route('/admin/settings', methods=['POST'])
@login_required
def save_settings():
    if not current_user.is_admin:
        return jsonify({'error': 'Non autorizzato'}), 403
    s = Settings.query.first()
    d = request.get_json()
    for k, v in d.items():
        if hasattr(s, k):
            setattr(s, k, v)
    db.session.commit()
    return jsonify({'ok': True})


@admin_bp.route('/admin/utenti/nuovo', methods=['POST'])
@login_required
def nuovo_utente():
    if not current_user.is_admin:
        return jsonify({'error': 'Non autorizzato'}), 403
    from models.user import User
    d = request.get_json()
    if User.query.filter_by(email=d['email']).first():
        return jsonify({'error': 'Email già esistente'}), 400
    u = User(nome=d['nome'], email=d['email'], role=d.get('role','sales'))
    u.set_password(d['password'])
    db.session.add(u)
    db.session.commit()
    return jsonify({'ok': True})


@admin_bp.route('/admin/utenti/<int:uid>/toggle', methods=['POST'])
@login_required
def toggle_utente(uid):
    if not current_user.is_admin:
        return jsonify({'error': 'Non autorizzato'}), 403
    from models.user import User
    u = User.query.get_or_404(uid)
    u.attivo = not u.attivo
    db.session.commit()
    return jsonify({'ok': True, 'attivo': u.attivo})


# ── PDF ───────────────────────────────────────────────────────────────────────

@pdf_bp.route('/pdf/<int:pid>')
@login_required
def genera(pid):
    from services.pdf_service import build_pdf
    p = Pratica.query.get_or_404(pid)
    if not current_user.is_admin and p.agente_id != current_user.id:
        return 'Non autorizzato', 403
    s   = Settings.query.first()
    buf = build_pdf(p, s)
    return send_file(
        buf,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f'BIOLavaTU_{p.numero}.pdf'
    )
