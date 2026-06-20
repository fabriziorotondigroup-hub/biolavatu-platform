import os, sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()


def _get_db_url():
    url = os.environ.get('DATABASE_URL', '')
    if url:
        return url.replace('postgres://', 'postgresql://')
    return 'sqlite:///biolavatu.db'


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = _get_db_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Accedi per continuare.'

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.preventivo import preventivo_bp
    from routes.pratiche import pratiche_bp
    from routes.clienti import clienti_bp
    from routes.admin import admin_bp
    from routes.geo import geo_bp
    from routes.romania import ro_bp
    from routes.albania import al_bp
    from routes.polonia import pl_bp
    from routes.croazia import hr_bp
    from routes.slovenia import si_bp
    from routes.investitore import inv_bp
    from routes.pdf import pdf_bp

    for bp in (auth_bp, dashboard_bp, preventivo_bp, pratiche_bp,
               clienti_bp, admin_bp, geo_bp, pdf_bp, inv_bp, ro_bp, al_bp, pl_bp, hr_bp, si_bp):
        app.register_blueprint(bp)

    # Custom Jinja filters
    @app.template_filter('format_number')
    def format_number(value):
        try:
            return f"{int(value):,}".replace(',', '.')
        except (ValueError, TypeError):
            return value

    # Make enumerate available in templates
    app.jinja_env.globals['enumerate'] = enumerate

    @app.context_processor
    def inject_globals():
        try:
            from models.settings import Settings
            s = Settings.query.first()
            return {'settings_global': s}
        except Exception:
            return {'settings_global': None}

    return app


app = create_app()

# ── Migrazione automatica colonne mancanti ────────────────────────────────
def _run_migrations():
    from sqlalchemy import text
    cols = [
        ('pratiche', 'bp_avanzato_json', 'TEXT'),
        ('pratiche', 'pop_3min',         'INTEGER DEFAULT 0'),
        ('pratiche', 'ai_risk',          'TEXT'),
        ('pratiche', 'allegati_json',    'TEXT'),
        ('pratiche', 'foto_mappa',       'TEXT'),
        # ── Versione Investitore ──────────────────────────────────────────
        ('pratiche', 'tipo_pratica',             "VARCHAR(20) DEFAULT 'standard'"),
        ('pratiche', 'sopralluogo_json',          'TEXT'),
        ('pratiche', 'sopralluogo_completato',    'BOOLEAN DEFAULT FALSE'),
        ('pratiche', 'concorrenza_campo_json',    'TEXT'),
        ('pratiche', 'score_investitore',         'FLOAT DEFAULT 0.0'),
        ('pratiche', 'confidenza_pct',            'INTEGER DEFAULT 0'),
        ('pratiche', 'confidenza_label',          'VARCHAR(20)'),
        ('pratiche', 'raccomandazione',           'VARCHAR(20)'),
        ('pratiche', 'analisi_investitore_json',  'TEXT'),
        # ── [ADD-ON COMMERCIALE] Risk Score Investimento ────────────────────────
        ('pratiche', 'risk_score',                'INTEGER'),
        # ── [FIX CRITICO] Campi mercato mai migrati — causavano UndefinedColumn ──
        ('pratiche', 'market',                    "VARCHAR(5) DEFAULT 'IT'"),
        ('pratiche', 'valuta',                     "VARCHAR(5) DEFAULT 'EUR'"),
        ('pratiche', 'cambio_ron',                 'FLOAT DEFAULT 4.97'),
        ('pratiche', 'judet_cod',                  'VARCHAR(10)'),
        ('pratiche', 'risk_label',                'VARCHAR(80)'),
        ('pratiche', 'risk_assessment_json',      'TEXT'),
        ('pratiche', 'visibilita_vetrina',        'INTEGER DEFAULT 0'),
        ('pratiche', 'parcheggio_diretto',        'BOOLEAN DEFAULT FALSE'),
        ('pratiche', 'n_posti_parcheggio',        'INTEGER DEFAULT 0'),
        ('pratiche', 'distanza_arteria_m',        'INTEGER DEFAULT 0'),
        ('pratiche', 'lato_soleggiato',           'BOOLEAN DEFAULT TRUE'),
        ('pratiche', 'cantieri_previsti',         'BOOLEAN DEFAULT FALSE'),
        ('pratiche', 'note_sopralluogo',          'TEXT'),
        # ── Lettera presentazione ─────────────────────────────────────────
        ('pratiche', 'lettera_presentazione',     'TEXT'),
        # ── Mercato utenti ────────────────────────────────────────────────────
        ('users',    'market',    "VARCHAR(5) DEFAULT 'IT'"),
    ]
    with app.app_context():
        with db.engine.connect() as conn:
            for tbl, col, typ in cols:
                try:
                    conn.execute(text(
                        f'ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS {col} {typ}'
                    ))
                    conn.commit()
                except Exception:
                    conn.rollback()

try:
    _run_migrations()
except Exception:
    pass

if __name__ == '__main__':
    app.run(debug=True, port=5000)
