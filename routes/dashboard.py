from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.pratica import Pratica
from models.cliente import Cliente
from models.user import User
from app import db

dashboard_bp = Blueprint('dashboard', __name__)


def _get_cambio_ron():
    try:
        import urllib.request as _ur, json as _json
        with _ur.urlopen('https://api.frankfurter.app/latest?from=EUR&to=RON', timeout=2) as r:
            return float(_json.loads(r.read())['rates']['RON'])
    except Exception:
        return 4.97


@dashboard_bp.route('/')
@login_required
def index():

    # ── OWNER / ADMIN — dashboard unificata multi-mercato ────────────────────
    if current_user.is_admin:
        cambio_ron = _get_cambio_ron()

        # Italia
        pratiche_it = Pratica.query.filter_by(market='IT')\
            .order_by(Pratica.created.desc()).limit(8).all()
        tot_it       = Pratica.query.filter_by(market='IT').count()
        firmate_it   = Pratica.query.filter_by(market='IT', stato='firmato').count()
        pipeline_it  = sum(
            (p.capex or 0) * ((p.fattibilita or 0) / 100.0)
            for p in Pratica.query.filter(
                Pratica.market == 'IT',
                Pratica.stato.in_(['bozza','inviato','trattativa'])
            ).all()
        )

        # Romania
        pratiche_ro = Pratica.query.filter_by(market='RO')\
            .order_by(Pratica.created.desc()).limit(8).all()
        tot_ro      = Pratica.query.filter_by(market='RO').count()
        firmate_ro  = Pratica.query.filter_by(market='RO', stato='firmato').count()
        pipeline_ro = sum(
            (p.incasso_mese or 0) * cambio_ron
            for p in Pratica.query.filter_by(market='RO').all()
        )

        # Venditori (solo owner li vede tutti)
        venditori_it = User.query.filter(
            User.role.in_(['sales','admin']),
            User.market == 'IT',
            User.attivo == True
        ).all() if current_user.is_owner else []

        venditori_ro = User.query.filter(
            User.role.in_(['sales','admin']),
            User.market == 'RO',
            User.attivo == True
        ).all() if current_user.is_owner else []

        tot_clienti  = Cliente.query.count()

        return render_template('dashboard.html',
            # Dati Italia
            pratiche=pratiche_it,
            tot_pratiche=tot_it,
            firmate=firmate_it,
            valore_pipeline=pipeline_it,
            # Dati Romania
            pratiche_ro=pratiche_ro,
            tot_pratiche_ro=tot_ro,
            firmate_ro=firmate_ro,
            valore_pipeline_ro=pipeline_ro,
            cambio_ron=cambio_ron,
            # Venditori
            venditori_it=venditori_it,
            venditori_ro=venditori_ro,
            tot_clienti=tot_clienti,
            tot_venditori=len(venditori_it) + len(venditori_ro),
            # Flag
            is_multi_market=True,
        )

    # ── SALES ITALIA ─────────────────────────────────────────────────────────
    if getattr(current_user, 'market', 'IT') == 'IT':
        pratiche = Pratica.query.filter_by(agente_id=current_user.id)\
            .order_by(Pratica.created.desc()).limit(10).all()
        tot_pratiche = Pratica.query.filter_by(agente_id=current_user.id).count()
        pipeline = sum(
            (p.capex or 0) * ((p.fattibilita or 0) / 100.0)
            for p in Pratica.query.filter(
                Pratica.agente_id == current_user.id,
                Pratica.stato.in_(['bozza','inviato','trattativa'])
            ).all()
        )
        firmate = Pratica.query.filter_by(
            agente_id=current_user.id, stato='firmato').count()
        return render_template('dashboard.html',
            pratiche=pratiche,
            tot_pratiche=tot_pratiche,
            firmate=firmate,
            valore_pipeline=pipeline,
            tot_clienti=Cliente.query.count(),
            tot_venditori=0,
            tot_pratiche_ro=0,
            valore_pipeline_ro=0,
            cambio_ron=4.97,
            is_multi_market=False,
        )

    # ── SALES ROMANIA — redirect alla dashboard Romania ───────────────────────
    from flask import redirect, url_for
    return redirect(url_for('romania.dashboard'))
