from app import db
from datetime import datetime
import json


class Pratica(db.Model):
    __tablename__ = 'pratiche'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(30), unique=True, nullable=False)
    stato = db.Column(db.String(20), default='bozza')
    # bozza | inviato | trattativa | firmato | perso
    fattibilita = db.Column(db.Integer, default=50)  # % 0-100

    cliente_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), nullable=False)
    agente_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Sede
    indirizzo = db.Column(db.String(300))
    citta = db.Column(db.String(100))
    cap = db.Column(db.String(10))
    provincia = db.Column(db.String(100))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    mq = db.Column(db.Integer, default=60)

    # Analisi zona
    pop_3min = db.Column(db.Integer, default=0)
    pop_5min = db.Column(db.Integer, default=0)
    pop_10min = db.Column(db.Integer, default=0)
    concorrenti_500m = db.Column(db.Integer, default=0)
    concorrenti_1km = db.Column(db.Integer, default=0)
    servizi_400m = db.Column(db.Integer, default=0)
    score_zona = db.Column(db.Float, default=0.0)
    score_label = db.Column(db.String(30))
    traffico_pedonale = db.Column(db.String(20), default='medio')  # basso|medio|alto

    # Dati raw JSON
    geo_raw = db.Column(db.Text)
    competitors_raw = db.Column(db.Text)
    pois_raw = db.Column(db.Text)
    zona_info_raw = db.Column(db.Text)

    # Macchine selezionate (JSON)
    macchine_json = db.Column(db.Text)

    # Business plan — tariffe
    tariffa_lavaggio_std = db.Column(db.Float, default=4.0)
    tariffa_lavaggio_med = db.Column(db.Float, default=5.0)
    tariffa_lavaggio_grd = db.Column(db.Float, default=7.0)
    tariffa_asciugatura = db.Column(db.Float, default=3.0)
    durata_lavaggio = db.Column(db.Integer, default=45)
    durata_asciugatura = db.Column(db.Integer, default=35)

    # Business plan — costi personalizzati (override settings)
    kwh_cost = db.Column(db.Float)
    gas_mc_cost = db.Column(db.Float)
    acqua_mc_cost = db.Column(db.Float)
    scarico_mc_cost = db.Column(db.Float)
    affitto_mese = db.Column(db.Float, default=0)
    commercialista = db.Column(db.Float)
    cciaa = db.Column(db.Float)
    assicurazione = db.Column(db.Float)
    manutenzione = db.Column(db.Float)
    det1_costo_mese = db.Column(db.Float, default=0)
    det2_costo_mese = db.Column(db.Float, default=0)
    det3_costo_mese = db.Column(db.Float, default=0)

    # Risultati economici
    capex = db.Column(db.Float, default=0)
    incasso_mese = db.Column(db.Float, default=0)
    costi_mese = db.Column(db.Float, default=0)
    utile_mese = db.Column(db.Float, default=0)
    payback_mesi = db.Column(db.Float, default=0)
    scenario = db.Column(db.String(20), default='realistico')

    # AI testi
    ai_zona = db.Column(db.Text)
    ai_bp   = db.Column(db.Text)
    bp_avanzato_json = db.Column(db.Text)  # JSON con tutti i dati modalità avanzata
    lettera_presentazione = db.Column(db.Text)  # Lettera AI personalizzata per il PDF
    ai_risk = db.Column(db.Text)

    # Allegati
    foto_sede = db.Column(db.String(300))
    foto_mappa = db.Column(db.String(300))
    allegati_json = db.Column(db.Text)  # lista path allegati
    note_interne = db.Column(db.Text)

    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agente = db.relationship('User', backref='pratiche', lazy=True)

    def get_macchine(self):
        if self.macchine_json:
            return json.loads(self.macchine_json)
        return []

    def set_macchine(self, data):
        self.macchine_json = json.dumps(data)

    def get_allegati(self):
        if self.allegati_json:
            return json.loads(self.allegati_json)
        return []

    def get_competitors(self):
        if self.competitors_raw:
            try:
                return json.loads(self.competitors_raw)
            except Exception:
                return []
        return []

    def get_pois(self):
        if self.pois_raw:
            try:
                return json.loads(self.pois_raw)
            except Exception:
                return []
        return []

    @property
    def semaforo(self):
        if self.fattibilita >= 70:
            return 'verde'
        elif self.fattibilita >= 40:
            return 'giallo'
        return 'rosso'

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'stato': self.stato,
            'fattibilita': self.fattibilita,
            'cliente': self.cliente.to_dict() if self.cliente else {},
            'indirizzo': self.indirizzo or '',
            'citta': self.citta or '',
            'lat': self.lat,
            'lng': self.lng,
            'mq': self.mq,
            'pop_3min': self.pop_3min,
            'pop_5min': self.pop_5min,
            'pop_10min': self.pop_10min,
            'concorrenti_500m': self.concorrenti_500m,
            'concorrenti_1km': self.concorrenti_1km,
            'score_zona': self.score_zona,
            'score_label': self.score_label or '',
            'macchine': self.get_macchine(),
            'capex': self.capex,
            'incasso_mese': self.incasso_mese,
            'costi_mese': self.costi_mese,
            'utile_mese': self.utile_mese,
            'payback_mesi': self.payback_mesi,
        }

    # ── VERSIONE INVESTITORE — Sopralluogo obbligatorio ───────────────────────
    tipo_pratica = db.Column(db.String(20), default='standard')
    tipo_zona    = db.Column(db.String(20), default='residenziale')
    # 'standard' | 'investitore'

    # Sopralluogo A — Traffico pedonale (6 fasce orarie × 2 direzioni)
    sopralluogo_json = db.Column(db.Text)   # JSON strutturato completo
    sopralluogo_completato = db.Column(db.Boolean, default=False)

    # Sopralluogo B — Concorrenza rilevata sul campo
    concorrenza_campo_json = db.Column(db.Text)  # JSON per concorrente

    # Analisi avanzata risultati
    score_investitore = db.Column(db.Float, default=0.0)
    confidenza_pct = db.Column(db.Integer, default=0)   # 0-100
    confidenza_label = db.Column(db.String(20))          # Alta/Media/Bassa
    raccomandazione = db.Column(db.String(20))           # Procedi/Approfondisci/Sconsigliato
    analisi_investitore_json = db.Column(db.Text)        # report completo AI

    # Segnali extra zona
    visibilita_vetrina = db.Column(db.Integer, default=0)   # 1-10
    parcheggio_diretto = db.Column(db.Boolean, default=False)
    n_posti_parcheggio = db.Column(db.Integer, default=0)
    distanza_arteria_m = db.Column(db.Integer, default=0)
    lato_soleggiato = db.Column(db.Boolean, default=True)
    cantieri_previsti = db.Column(db.Boolean, default=False)
    note_sopralluogo = db.Column(db.Text)

    def get_sopralluogo(self):
        if self.sopralluogo_json:
            try: return json.loads(self.sopralluogo_json)
            except: return {}
        return {}

    def get_concorrenza_campo(self):
        if self.concorrenza_campo_json:
            try: return json.loads(self.concorrenza_campo_json)
            except: return []
        return []

    def get_analisi_investitore(self):
        if self.analisi_investitore_json:
            try: return json.loads(self.analisi_investitore_json)
            except: return {}
        return {}
