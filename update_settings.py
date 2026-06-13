"""
Script da eseguire UNA VOLTA sul VPS per aggiornare i dati aziendali nel DB.
Uso:
    cd /var/www/laundrypro
    venv/bin/python3 update_settings.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models.settings import Settings

DATI = {
    'brand_name':    'BIOLavaTU by Rotondi Group',
    'company_name':  'Rotondi Group Srl',
    'company_addr':  'Via F.lli Rosselli 14/16 - 20019 Settimo Milanese (MI)',
    'company_piva':  'P.IVA 09975740151',
    'company_email': 'info@rotondigroup.it',
    'company_web':   'www.biolavatu.it',
    'company_tel':   '+39 06 41400514',,
}

with app.app_context():
    s = Settings.query.first()
    if not s:
        s = Settings()
        db.session.add(s)
        print("[update_settings] Nessuna riga trovata, creo Settings.")

    for campo, valore in DATI.items():
        setattr(s, campo, valore)
        print(f"  ✅ {campo} = {valore}")

    # Secondo numero in company_tel2 se esiste, altrimenti nella nota
    if hasattr(s, 'company_tel2'):
        s.company_tel2 = '+39 06 41400617'
    db.session.commit()
    print("\n[update_settings] Dati aziendali aggiornati nel DB.")
    print(f"  brand_name   = {s.brand_name}")
    print(f"  company_addr = {s.company_addr}")
    print(f"  company_piva = {s.company_piva}")
    print(f"  company_web  = {s.company_web}")
    print(f"  company_tel  = {s.company_tel}")
