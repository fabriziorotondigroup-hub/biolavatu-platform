from app import db
from datetime import datetime


class Cliente(db.Model):
    __tablename__ = 'clienti'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cognome = db.Column(db.String(200))
    azienda = db.Column(db.String(200))
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(30))
    piva = db.Column(db.String(20))
    cf = db.Column(db.String(20))
    indirizzo = db.Column(db.String(300))
    citta = db.Column(db.String(100))
    cap = db.Column(db.String(10))
    provincia = db.Column(db.String(5))
    tipo = db.Column(db.String(20), default='Privato')  # Privato|Azienda|Prospect
    note = db.Column(db.Text)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pratiche = db.relationship('Pratica', backref='cliente', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cognome': self.cognome or '',
            'azienda': self.azienda or '',
            'email': self.email or '',
            'telefono': self.telefono or '',
            'piva': self.piva or '',
            'cf': self.cf or '',
            'citta': self.citta or '',
            'tipo': self.tipo,
        }

    @property
    def nome_completo(self):
        if self.azienda:
            return self.azienda
        parts = [self.nome]
        if self.cognome:
            parts.append(self.cognome)
        return ' '.join(parts)
