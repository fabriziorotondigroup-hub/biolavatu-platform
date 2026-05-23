from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.pratica import Pratica
from models.cliente import Cliente
from app import db

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
