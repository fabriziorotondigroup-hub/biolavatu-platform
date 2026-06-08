from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models.cliente import Cliente
from app import db

clienti_bp = Blueprint('clienti', __name__)


@clienti_bp.route('/clienti')
@login_required
def index():
    q = request.args.get('q', '')
    query = Cliente.query
    if q:
        query = query.filter(
            Cliente.nome.ilike(f'%{q}%') |
            Cliente.azienda.ilike(f'%{q}%') |
            Cliente.email.ilike(f'%{q}%')
        )
    clienti = query.order_by(Cliente.nome).all()
    return render_template('clienti.html', clienti=clienti, q=q)


@clienti_bp.route('/clienti/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo():
    if request.method == 'POST':
        c = Cliente(
            nome=request.form.get('nome', ''),
            cognome=request.form.get('cognome', ''),
            azienda=request.form.get('azienda', ''),
            email=request.form.get('email', ''),
            telefono=request.form.get('telefono', ''),
            piva=request.form.get('piva', ''),
            cf=request.form.get('cf', ''),
            indirizzo=request.form.get('indirizzo', ''),
            citta=request.form.get('citta', ''),
            cap=request.form.get('cap', ''),
            provincia=request.form.get('provincia', ''),
            tipo=request.form.get('tipo', 'Privato'),
            note=request.form.get('note', ''),
        )
        db.session.add(c)
        db.session.commit()
        flash('Cliente creato con successo.', 'success')
        return redirect(url_for('clienti.index'))
    return render_template('cliente_form.html', cliente=None)


@clienti_bp.route('/clienti/<int:id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica(id):
    c = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        c.nome = request.form.get('nome', c.nome)
        c.cognome = request.form.get('cognome', '')
        c.azienda = request.form.get('azienda', '')
        c.email = request.form.get('email', '')
        c.telefono = request.form.get('telefono', '')
        c.piva = request.form.get('piva', '')
        c.cf = request.form.get('cf', '')
        c.indirizzo = request.form.get('indirizzo', '')
        c.citta = request.form.get('citta', '')
        c.cap = request.form.get('cap', '')
        c.provincia = request.form.get('provincia', '')
        c.tipo = request.form.get('tipo', 'Privato')
        c.note = request.form.get('note', '')
        db.session.commit()
        flash('Cliente aggiornato.', 'success')
        return redirect(url_for('clienti.index'))
    return render_template('cliente_form.html', cliente=c)


@clienti_bp.route('/clienti/<int:id>/elimina', methods=['POST'])
@login_required
def elimina(id):
    from models.cliente import Cliente
    c = Cliente.query.get_or_404(id)
    try:
        from models.pratica import Pratica
        # Controlla se ha pratiche collegate
        n_pratiche = Pratica.query.filter_by(cliente_id=id).count()
        if n_pratiche > 0:
            from flask import flash, redirect, url_for
            flash(f'Impossibile eliminare: il cliente ha {n_pratiche} pratiche collegate.', 'danger')
            return redirect(url_for('clienti.index'))
        from app import db
        db.session.delete(c)
        db.session.commit()
        from flask import flash, redirect, url_for
        flash('Cliente eliminato.', 'success')
    except Exception as e:
        from app import db
        db.session.rollback()
        from flask import flash, redirect, url_for
        flash(f'Errore: {e}', 'danger')
    return redirect(url_for('clienti.index'))


@clienti_bp.route('/api/clienti/cerca')
@login_required
def cerca():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    clienti = Cliente.query.filter(
        Cliente.nome.ilike(f'%{q}%') |
        Cliente.azienda.ilike(f'%{q}%') |
        Cliente.email.ilike(f'%{q}%')
    ).limit(10).all()
    return jsonify([{
        'id':       c.id,
        'nome':     c.nome or '',
        'cognome':  getattr(c, 'cognome', '') or '',
        'azienda':  getattr(c, 'azienda', '') or '',
        'email':    getattr(c, 'email', '') or '',
        'telefono': getattr(c, 'telefono', '') or '',
    } for c in clienti])
