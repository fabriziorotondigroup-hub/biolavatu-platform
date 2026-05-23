from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.pratica import Pratica
from models.cliente import Cliente
from models.user import User
from app import db
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    if current_user.is_admin:
        pratiche = Pratica.query.order_by(Pratica.created.desc()).limit(10).all()
        tot_pratiche = Pratica.query.count()
        tot_clienti = Cliente.query.count()
        tot_venditori = User.query.filter_by(role='sales', attivo=True).count()
        valore_pipeline = db.session.query(func.sum(Pratica.capex)).filter(
            Pratica.stato.in_(['bozza', 'inviato', 'trattativa'])
        ).scalar() or 0
        firmate = Pratica.query.filter_by(stato='firmato').count()
    else:
        pratiche = Pratica.query.filter_by(agente_id=current_user.id).order_by(Pratica.created.desc()).limit(10).all()
        tot_pratiche = Pratica.query.filter_by(agente_id=current_user.id).count()
        tot_clienti = Cliente.query.count()
        tot_venditori = 0
        valore_pipeline = db.session.query(func.sum(Pratica.capex)).filter(
            Pratica.agente_id == current_user.id,
            Pratica.stato.in_(['bozza', 'inviato', 'trattativa'])
        ).scalar() or 0
        firmate = Pratica.query.filter_by(agente_id=current_user.id, stato='firmato').count()

    return render_template('dashboard.html',
        pratiche=pratiche,
        tot_pratiche=tot_pratiche,
        tot_clienti=tot_clienti,
        tot_venditori=tot_venditori,
        valore_pipeline=valore_pipeline,
        firmate=firmate,
    )
