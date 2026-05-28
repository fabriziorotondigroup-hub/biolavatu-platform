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
    c = Cliente.query.get_or_404(id)
    if c.pratiche:
        flash(f'Impossibile eliminare: il cliente ha {len(c.pratiche)} pratica/e associate.', 'error')
        return redirect(url_for('clienti.index'))
    db.session.delete(c)
    db.session.commit()
    flash('Cliente eliminato.', 'success')
    return redirect(url_for('clienti.index'))


@clienti_bp.route('/api/clienti/cerca')
@login_required
def cerca():
    q = request.args.get('q', '')
    clienti = Cliente.query.filter(
        Cliente.nome.ilike(f'%{q}%') |
        Cliente.azienda.ilike(f'%{q}%')
    ).limit(10).all()
    return jsonify([c.to_dict() for c in clienti])
