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
    from routes.pdf import pdf_bp

    for bp in (auth_bp, dashboard_bp, preventivo_bp, pratiche_bp,
               clienti_bp, admin_bp, geo_bp, pdf_bp):
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
