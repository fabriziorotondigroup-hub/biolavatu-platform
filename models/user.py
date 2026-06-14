from app import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id       = db.Column(db.Integer, primary_key=True)
    nome     = db.Column(db.String(120), nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

    # ── Ruoli ─────────────────────────────────────────────────────────────────
    # owner      → Fabrizio — tutto, incluso codici/VPS/macchine/BP
    # segreteria → Silvana Roma — tutto incluso macchine/impianti/BP
    # admin      → Andrea ecc. — vede pratiche, inserisce venditori
    # sales      → agenti Italia
    # sales_ro   → agenti Romania
    role   = db.Column(db.String(20), default='sales')
    market = db.Column(db.String(5),  default='IT')   # IT | RO
    lingua = db.Column(db.String(5),  default='it')   # it | ro
    attivo = db.Column(db.Boolean, default=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    # Email hardcoded — sicurezza assoluta, non modificabile da UI
    OWNER_EMAIL      = 'fabrizio.rotondigroup@gmail.com'
    SEGRETERIA_EMAIL = 'roma.rotondigroup@gmail.com'

    def set_password(self, pw):
        self.password = bcrypt.generate_password_hash(pw).decode('utf-8')

    def check_password(self, pw):
        return bcrypt.check_password_hash(self.password, pw)

    # ── Property ruoli ────────────────────────────────────────────────────────

    @property
    def is_owner(self):
        """Solo Fabrizio — DOPPIO controllo: ruolo E email.
        Nessun admin può mai diventare owner senza avere questa email."""
        return self.role == 'owner' and self.email == self.OWNER_EMAIL

    @property
    def is_segreteria(self):
        """Silvana Roma — accesso completo incluso macchine/BP."""
        return self.role == 'segreteria' or self.email == self.SEGRETERIA_EMAIL

    @property
    def is_admin(self):
        """Admin, segreteria e owner hanno accesso admin panel."""
        return self.role in ('admin', 'owner', 'segreteria')

    @property
    def can_manage_macchine(self):
        """Solo owner e segreteria possono modificare macchine/impianti/BP."""
        return self.is_owner or self.is_segreteria

    @property
    def can_manage_venditori(self):
        """Owner e admin possono inserire/gestire venditori."""
        return self.role in ('owner', 'admin')

    @property
    def is_sales(self):
        return self.role in ('sales', 'sales_ro')

    @property
    def is_ro(self):
        return self.market == 'RO' or self.role == 'sales_ro'

    def __repr__(self):
        return f'<User {self.email} [{self.role}]>'
