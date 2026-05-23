from app import db


class Settings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    # Azienda
    brand_name = db.Column(db.String(200), default='BIOLavaTU by Rotondi Group')
    company_name = db.Column(db.String(200), default='Rotondi Group Srl')
    company_addr = db.Column(db.String(300))
    company_piva = db.Column(db.String(30))
    company_email = db.Column(db.String(120))
    company_web = db.Column(db.String(120))
    company_tel = db.Column(db.String(30))
    logo_path = db.Column(db.String(300))
    # Costi default
    kwh_cost = db.Column(db.Float, default=0.28)        # €/kWh
    gas_mc_cost = db.Column(db.Float, default=1.20)     # €/m³
    acqua_mc_cost = db.Column(db.Float, default=2.50)   # €/m³
    scarico_mc_cost = db.Column(db.Float, default=1.80) # €/m³
    affitto_mq = db.Column(db.Float, default=12.0)      # €/mq/mese
    commercialista = db.Column(db.Float, default=150.0) # €/mese
    cciaa = db.Column(db.Float, default=50.0)           # €/mese
    assicurazione = db.Column(db.Float, default=100.0)  # €/mese
    manutenzione = db.Column(db.Float, default=200.0)   # €/mese
    # Detergenti (costo €/kg e grammi per ciclo)
    det1_nome = db.Column(db.String(100), default='Detergente')
    det1_costo_kg = db.Column(db.Float, default=2.50)
    det1_grammi_ciclo = db.Column(db.Float, default=80.0)
    det2_nome = db.Column(db.String(100), default='Ammorbidente')
    det2_costo_kg = db.Column(db.Float, default=3.00)
    det2_grammi_ciclo = db.Column(db.Float, default=40.0)
    det3_nome = db.Column(db.String(100), default='Igienizzante')
    det3_costo_kg = db.Column(db.Float, default=4.00)
    det3_grammi_ciclo = db.Column(db.Float, default=20.0)
    # PDF e documenti
    condizioni_vendita = db.Column(db.Text)
    pdf_allegato = db.Column(db.String(300))
    # Colori
    color_primary = db.Column(db.String(10), default='#1B4F72')
    color_accent = db.Column(db.String(10), default='#C15E59')
