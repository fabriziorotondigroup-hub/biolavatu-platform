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
    role     = db.Column(db.String(20), default='sales')
    # owner | admin | segreteria | sales | sales_ro | sales_al | sales_pl | sales_hr | sales_si
    market   = db.Column(db.String(5), default='IT')
    # IT | RO | AL | PL | HR | SI
    attivo   = db.Column(db.Boolean, default=True)
    created  = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password = bcrypt.generate_password_hash(pw).decode('utf-8')

    def check_password(self, pw):
        return bcrypt.check_password_hash(self.password, pw)

    @property
    def is_admin(self):
        return self.role in ('admin', 'owner', 'segreteria')

    @property
    def is_owner(self):
        return self.role == 'owner'

    @property
    def can_manage_venditori(self):
        return self.role in ('owner', 'admin', 'segreteria')
