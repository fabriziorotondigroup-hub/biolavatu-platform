from app import db
from datetime import datetime


class Macchina(db.Model):
    __tablename__ = 'macchine'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(50), default='Lavatrici')
    # Categorie: Lavatrici | Asciugatrici | Sistemi | Arredamento | Impianti
    modello = db.Column(db.String(100))
    descrizione = db.Column(db.Text)
    prezzo = db.Column(db.Float, default=0)
    prezzo_scontato = db.Column(db.Float, nullable=True)
    kw = db.Column(db.Float, default=0)
    cicli_giorno = db.Column(db.Integer, default=8)
    tariffa = db.Column(db.Float, default=0)  # €/ciclo
    attiva = db.Column(db.Boolean, default=True)
    in_evidenza = db.Column(db.Boolean, default=False)
    note_commerciali = db.Column(db.Text)
    combustibile = db.Column(db.String(20), default='elettrico')  # elettrico | gas
    mc_ciclo = db.Column(db.Float, default=0)  # m³ gas per ciclo
    capacita_kg = db.Column(db.Float, default=0)  # capacità in kg
    durata_ciclo = db.Column(db.Integer, default=45)  # minuti
    foto_path = db.Column(db.String(300))
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def prezzo_effettivo(self):
        return self.prezzo_scontato if self.prezzo_scontato else self.prezzo

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'categoria': self.categoria,
            'modello': self.modello or '',
            'descrizione': self.descrizione or '',
            'prezzo': self.prezzo,
            'prezzo_scontato': self.prezzo_scontato,
            'prezzo_effettivo': self.prezzo_effettivo,
            'kw': self.kw,
            'cicli_giorno': self.cicli_giorno,
            'tariffa': self.tariffa,
            'attiva': self.attiva,
            'in_evidenza': self.in_evidenza,
            'combustibile': self.combustibile,
            'mc_ciclo': self.mc_ciclo,
            'capacita_kg': self.capacita_kg,
            'durata_ciclo': self.durata_ciclo,
            'foto_path': self.foto_path or '',
            'note_commerciali': self.note_commerciali or '',
        }
