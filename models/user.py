from app import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='sales')  # admin | sales
    attivo = db.Column(db.Boolean, default=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password = bcrypt.generate_password_hash(pw).decode('utf-8')

    def check_password(self, pw):
        return bcrypt.check_password_hash(self.password, pw)

    @property
    def is_admin(self):
        return self.role in ('admin', 'owner')

    @property
    def is_owner(self):
        return self.role == 'owner'
