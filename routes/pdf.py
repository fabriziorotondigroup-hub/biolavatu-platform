from flask import Blueprint, send_file, abort
from flask_login import login_required
from models.pratica import Pratica

pdf_bp = Blueprint('pdf', __name__)


@pdf_bp.route('/pratiche/<int:id>/pdf')
@login_required
def genera(id):
    p = Pratica.query.get_or_404(id)
    # PDF generation - to be implemented
    abort(501)
