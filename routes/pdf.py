import os
from flask import Blueprint, send_file, abort, current_app
from flask_login import login_required, current_user
from models.pratica import Pratica
from models.settings import Settings
from services.pdf_service import build_pdf

pdf_bp = Blueprint('pdf', __name__)


@pdf_bp.route('/pratiche/<int:id>/pdf')
@login_required
def genera(id):
    p = Pratica.query.get_or_404(id)

    # Solo owner/admin/agente assegnato
    if current_user.role not in ('owner', 'admin') and p.agente_id != current_user.id:
        abort(403)

    s = Settings.query.first()

    try:
        buf = build_pdf(p, s)
    except Exception as e:
        current_app.logger.error(f'PDF error pratica {id}: {e}', exc_info=True)
        abort(500)

    nome_file = f"BIOLavaTU_{p.numero}_{(p.cliente.nome if p.cliente else 'cliente').replace(' ', '_')}.pdf"
    return send_file(
        buf,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=nome_file,
    )


@pdf_bp.route('/pratiche/<int:id>/pdf/download')
@login_required
def scarica(id):
    p = Pratica.query.get_or_404(id)
    if current_user.role not in ('owner', 'admin') and p.agente_id != current_user.id:
        abort(403)

    s = Settings.query.first()
    try:
        buf = build_pdf(p, s)
    except Exception as e:
        current_app.logger.error(f'PDF download error pratica {id}: {e}', exc_info=True)
        abort(500)

    nome_file = f"BIOLavaTU_{p.numero}_{(p.cliente.nome if p.cliente else 'cliente').replace(' ', '_')}.pdf"
    return send_file(
        buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nome_file,
    )
