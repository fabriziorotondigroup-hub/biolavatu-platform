from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.macchina import Macchina
from models.settings import Settings
from models.user import User
from app import db, bcrypt
import os
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def safe_float(val, default=0.0):
    """Converte in float in modo sicuro — gestisce None, 'None', stringa vuota."""
    try:
        v = str(val).strip()
        if v in ('', 'None', 'none', 'null'):
            return default
        return float(v)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    try:
        v = str(val).strip()
        if v in ('', 'None', 'none', 'null'):
            return default
        return int(float(v))
    except (ValueError, TypeError):
        return default


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accesso riservato agli amministratori.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/admin')
@login_required
@admin_required
def index():
    macchine = Macchina.query.order_by(Macchina.categoria, Macchina.nome).all()
    venditori = User.query.filter(User.role != 'owner').order_by(User.market, User.nome).all()
    settings = Settings.query.first()
    return render_template('admin.html', macchine=macchine, venditori=venditori, settings=settings)


# ── MACCHINE ──────────────────────────────────────────────

@admin_bp.route('/admin/macchine/nuova', methods=['POST'])
@login_required
@admin_required
def nuova_macchina():
    m = Macchina(
        nome=request.form.get('nome', ''),
        categoria=request.form.get('categoria', 'Lavatrici'),
        modello=request.form.get('modello', ''),
        descrizione=request.form.get('descrizione', ''),
        prezzo=safe_float(request.form.get('prezzo', 0)),
        prezzo_scontato=safe_float(request.form.get('prezzo_scontato')) or None,
        kw=safe_float(request.form.get('kw', 0)),
        cicli_giorno=safe_int(request.form.get('cicli_giorno', 8)),
        tariffa=safe_float(request.form.get('tariffa', 0)),
        combustibile=request.form.get('combustibile', 'elettrico'),
        mc_ciclo=safe_float(request.form.get('mc_ciclo', 0)),
        capacita_kg=safe_float(request.form.get('capacita_kg', 0)),
        durata_ciclo=safe_int(request.form.get('durata_ciclo', 45)),
        attiva='attiva' in request.form,
        in_evidenza='in_evidenza' in request.form,
        note_commerciali=request.form.get('note_commerciali', ''),
    )
    db.session.add(m)
    db.session.flush()

    if 'foto' in request.files:
        f = request.files['foto']
        if f and f.filename and allowed_file(f.filename):
            from flask import current_app
            fn = secure_filename(f'mac_{m.id}_{f.filename}')
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fn))
            m.foto_path = fn

    db.session.commit()
    flash('Macchina aggiunta.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/admin/macchine/<int:id>/modifica', methods=['POST'])
@login_required
@admin_required
def modifica_macchina(id):
    m = Macchina.query.get_or_404(id)
    m.nome = request.form.get('nome', m.nome)
    m.categoria = request.form.get('categoria', m.categoria)
    m.modello = request.form.get('modello', '')
    m.descrizione = request.form.get('descrizione', '')
    m.prezzo = safe_float(request.form.get('prezzo', 0))
    ps = safe_float(request.form.get('prezzo_scontato'))
    m.prezzo_scontato = ps if ps > 0 else None
    m.kw = safe_float(request.form.get('kw', 0))
    m.cicli_giorno = safe_int(request.form.get('cicli_giorno', 8))
    m.tariffa = safe_float(request.form.get('tariffa', 0))
    m.combustibile = request.form.get('combustibile', 'elettrico')
    m.mc_ciclo = safe_float(request.form.get('mc_ciclo', 0))
    m.capacita_kg = safe_float(request.form.get('capacita_kg', 0))
    m.durata_ciclo = safe_int(request.form.get('durata_ciclo', 45))
    m.attiva = 'attiva' in request.form
    m.in_evidenza = 'in_evidenza' in request.form
    m.note_commerciali = request.form.get('note_commerciali', '')

    if 'foto' in request.files:
        f = request.files['foto']
        if f and f.filename and allowed_file(f.filename):
            from flask import current_app
            fn = secure_filename(f'mac_{m.id}_{f.filename}')
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fn))
            m.foto_path = fn

    db.session.commit()
    flash('Macchina aggiornata.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/admin/macchine/<int:id>/elimina', methods=['POST'])
@login_required
@admin_required
def elimina_macchina(id):
    m = Macchina.query.get_or_404(id)
    db.session.delete(m)
    db.session.commit()
    flash('Macchina eliminata.', 'success')
    return redirect(url_for('admin.index'))


# ── VENDITORI ──────────────────────────────────────────────

@admin_bp.route('/admin/venditori/nuovo', methods=['POST'])
@login_required
@admin_required
def nuovo_venditore():
    email = request.form.get('email', '')
    if User.query.filter_by(email=email).first():
        flash('Email già registrata.', 'error')
        return redirect(url_for('admin.index'))
    role_input = request.form.get('role', 'sales')
    valid_roles = ('admin', 'segreteria', 'sales', 'sales_ro', 'sales_al', 'sales_pl', 'sales_hr', 'sales_si')
    role_input = role_input if role_input in valid_roles else 'sales'
    market_input = request.form.get('market', 'IT')
    valid_markets = ('IT', 'RO', 'AL', 'PL', 'HR', 'SI')
    market_input = market_input if market_input in valid_markets else 'IT'
    u = User(
        nome=request.form.get('nome', ''),
        email=email,
        role=role_input,
        market=market_input,
        attivo=True,
    )
    u.set_password(request.form.get('password', 'Cambiapassword1!'))
    db.session.add(u)
    db.session.commit()
    flash('Venditore creato.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/admin/venditori/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_venditore(id):
    u = User.query.get_or_404(id)
    u.attivo = not u.attivo
    db.session.commit()
    return jsonify({'attivo': u.attivo})


@admin_bp.route('/admin/venditori/<int:id>/elimina', methods=['POST'])
@login_required
@admin_required
def elimina_venditore(id):
    u = User.query.get_or_404(id)
    if u.is_owner:
        flash('Il proprietario non può essere eliminato.', 'error')
        return redirect(url_for('admin.index'))
    db.session.delete(u)
    db.session.commit()
    flash(f'Venditore {u.nome} eliminato.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/admin/venditori/<int:id>/cambia-ruolo', methods=['POST'])
@login_required
@admin_required
def cambia_ruolo(id):
    from flask_login import current_user
    u = User.query.get_or_404(id)
    if u.is_owner:
        flash('Il ruolo del proprietario non può essere modificato.', 'error')
        return redirect(url_for('admin.index'))
    if u.id == current_user.id:
        flash('Non puoi cambiare il tuo stesso ruolo.', 'error')
        return redirect(url_for('admin.index'))
    nuovo_ruolo = request.form.get('ruolo', 'sales')
    valid_roles = ('admin', 'segreteria', 'sales', 'sales_ro', 'sales_al', 'sales_pl', 'sales_hr', 'sales_si')
    if nuovo_ruolo not in valid_roles:
        flash('Ruolo non valido.', 'error')
        return redirect(url_for('admin.index'))
    nuovo_market = request.form.get('market', 'IT')
    valid_markets = ('IT', 'RO', 'AL', 'PL', 'HR', 'SI')
    if nuovo_market in valid_markets:
        u.market = nuovo_market
    u.role = nuovo_ruolo
    db.session.commit()
    flash(f'{u.nome} aggiornato: {nuovo_ruolo} / {u.market}.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/admin/venditori/<int:id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(id):
    u = User.query.get_or_404(id)
    nuova_pw = request.form.get('password', '')
    if nuova_pw:
        u.set_password(nuova_pw)
        db.session.commit()
        flash('Password aggiornata.', 'success')
    return redirect(url_for('admin.index'))


# ── SETTINGS ──────────────────────────────────────────────

@admin_bp.route('/admin/settings', methods=['POST'])
@login_required
@admin_required
def salva_settings():
    from flask import current_app
    s = Settings.query.first()
    if not s:
        s = Settings()
        db.session.add(s)

    s.brand_name = request.form.get('brand_name', s.brand_name)
    s.company_name = request.form.get('company_name', s.company_name)
    s.company_addr = request.form.get('company_addr', '')
    s.company_piva = request.form.get('company_piva', '')
    s.company_email = request.form.get('company_email', '')
    s.company_web = request.form.get('company_web', '')
    s.company_tel = request.form.get('company_tel', '')
    s.kwh_cost = float(request.form.get('kwh_cost', 0.28) or 0.28)
    s.gas_mc_cost = float(request.form.get('gas_mc_cost', 1.20) or 1.20)
    s.acqua_mc_cost = float(request.form.get('acqua_mc_cost', 2.50) or 2.50)
    s.scarico_mc_cost = float(request.form.get('scarico_mc_cost', 1.80) or 1.80)
    s.affitto_mq = float(request.form.get('affitto_mq', 12) or 12)
    s.commercialista = float(request.form.get('commercialista', 150) or 150)
    s.cciaa = float(request.form.get('cciaa', 50) or 50)
    s.assicurazione = float(request.form.get('assicurazione', 100) or 100)
    s.manutenzione = float(request.form.get('manutenzione', 200) or 200)
    s.det1_nome = request.form.get('det1_nome', 'Detergente')
    s.det1_costo_kg = float(request.form.get('det1_costo_kg', 2.50) or 2.50)
    s.det1_grammi_ciclo = float(request.form.get('det1_grammi_ciclo', 80) or 80)
    s.det2_nome = request.form.get('det2_nome', 'Ammorbidente')
    s.det2_costo_kg = float(request.form.get('det2_costo_kg', 3.00) or 3.00)
    s.det2_grammi_ciclo = float(request.form.get('det2_grammi_ciclo', 40) or 40)
    s.det3_nome = request.form.get('det3_nome', 'Igienizzante')
    s.det3_costo_kg = float(request.form.get('det3_costo_kg', 4.00) or 4.00)
    s.det3_grammi_ciclo = float(request.form.get('det3_grammi_ciclo', 20) or 20)
    s.condizioni_vendita = request.form.get('condizioni_vendita', '')
    s.color_primary = request.form.get('color_primary', '#1B4F72')
    s.color_accent = request.form.get('color_accent', '#C15E59')

    # Logo upload
    if 'logo' in request.files:
        f = request.files['logo']
        if f and f.filename and allowed_file(f.filename):
            fn = secure_filename(f'logo_{f.filename}')
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fn))
            s.logo_path = fn

    db.session.commit()
    flash('Impostazioni salvate.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/admin/migrate-db', methods=['GET'])
@login_required
@admin_required
def migrate_db():
    """Aggiunge le colonne mancanti al database — eseguire una sola volta dopo deploy."""
    from sqlalchemy import text
    results = []
    migrazioni = [
        "ALTER TABLE pratiche ADD COLUMN IF NOT EXISTS perc_asciugatura FLOAT DEFAULT 65",
        "ALTER TABLE pratiche ADD COLUMN IF NOT EXISTS giorni_mese FLOAT DEFAULT 30",
        "ALTER TABLE pratiche ADD COLUMN IF NOT EXISTS ore_apertura FLOAT DEFAULT 13",
    ]
    for sql in migrazioni:
        try:
            db.session.execute(text(sql))
            results.append(f'✅ {sql}')
        except Exception as e:
            results.append(f'⚠️ {sql} — {str(e)[:60]}')
    db.session.commit()
    return '<br>'.join(results) + '<br><br><b>Migrazione completata. <a href="/admin">Torna ad Admin</a></b>'
