"""Inizializza il database prima di avviare gunicorn."""
import sys
from app import app, db

with app.app_context():
    print("[INIT] Creo tabelle...", flush=True)
    db.create_all()
    print("[INIT] Tabelle create.", flush=True)

    # Migration: allarga colonne troppo corte
    try:
        db.engine.execute('ALTER TABLE pratiche ALTER COLUMN provincia TYPE VARCHAR(100)')
        db.engine.execute('ALTER TABLE pratiche ALTER COLUMN score_label TYPE VARCHAR(50)')
        print('[INIT] Migration provincia OK.', flush=True)
    except Exception as e:
        print(f'[INIT] Migration skip (già ok): {e}', flush=True)



    from models.user import User
    from models.settings import Settings
    from models.macchina import Macchina

    # Admin default
    try:
        if not User.query.filter_by(email='fabrizio@rotondigroup.it').first():
            u = User(
                nome='Fabrizio De Antoniis',
                email='fabrizio@rotondigroup.it',
                role='admin',
                attivo=True
            )
            u.set_password('BioLava2024!')
            db.session.add(u)
            db.session.commit()
            print("[INIT] Admin creato.", flush=True)
        else:
            print("[INIT] Admin già esiste.", flush=True)
    except Exception as e:
        db.session.rollback()
        print(f"[INIT] Admin error: {e}", flush=True)

    # Settings default
    try:
        if not Settings.query.first():
            db.session.add(Settings(
                brand_name='BIOLavaTU by Rotondi Group',
                company_name='Rotondi Group Srl',
                company_addr="Via di Sant'Alessandro 349, Roma",
                company_piva='IT 00000000000',
                company_email='info@garanzierotondi.it',
                company_web='garanzierotondi.it',
                condizioni_vendita="""CONDIZIONI GENERALI DI VENDITA

1. OGGETTO DEL CONTRATTO
Il presente contratto ha per oggetto la fornitura e installazione di attrezzature per lavanderia self-service.

2. PREZZI E PAGAMENTI
I prezzi indicati nel preventivo sono IVA esclusa. Il pagamento deve essere effettuato secondo le modalità concordate.

3. CONSEGNA E INSTALLAZIONE
I tempi di consegna saranno concordati con il cliente. L'installazione è inclusa nel prezzo.

4. GARANZIA
Tutte le macchine sono coperte da garanzia come da documentazione tecnica allegata.

5. ASSISTENZA TECNICA
Il servizio di assistenza tecnica è disponibile nei giorni lavorativi.
""",
            ))
            db.session.commit()
            print("[INIT] Settings create.", flush=True)
    except Exception as e:
        db.session.rollback()
        print(f"[INIT] Settings error: {e}", flush=True)

    # Macchine default
    try:
        if not Macchina.query.first():
            machines = [
                dict(nome='Lavatrice 10kg', categoria='Lavatrici', modello='IPSO CW10', prezzo=3200, kw=2.2, cicli_giorno=10, tariffa=4.0, attiva=True, in_evidenza=False, combustibile='elettrico', capacita_kg=10, durata_ciclo=45),
                dict(nome='Lavatrice 14kg', categoria='Lavatrici', modello='IPSO IY135', prezzo=4500, kw=3.0, cicli_giorno=8, tariffa=5.0, attiva=True, in_evidenza=True, combustibile='elettrico', capacita_kg=14, durata_ciclo=45),
                dict(nome='Lavatrice 18kg', categoria='Lavatrici', modello='IPSO IY180', prezzo=5800, kw=4.0, cicli_giorno=6, tariffa=7.0, attiva=True, in_evidenza=False, combustibile='elettrico', capacita_kg=18, durata_ciclo=50),
                dict(nome='Lavatrice PET 10kg', categoria='Lavatrici', modello='IPSO CS-10', prezzo=3400, kw=2.2, cicli_giorno=6, tariffa=4.0, attiva=True, in_evidenza=False, combustibile='elettrico', capacita_kg=10, durata_ciclo=45),
                dict(nome='Asciugatrice 16kg Elett.', categoria='Asciugatrici', modello='MSGROUP EDS16', prezzo=3800, kw=5.5, cicli_giorno=10, tariffa=3.0, attiva=True, in_evidenza=True, combustibile='elettrico', capacita_kg=16, durata_ciclo=35),
                dict(nome='Asciugatrice 11kg Gas', categoria='Asciugatrici', modello='PRIMUS T11', prezzo=4200, kw=0.5, cicli_giorno=10, tariffa=3.0, attiva=True, in_evidenza=True, combustibile='gas', mc_ciclo=0.20, capacita_kg=11, durata_ciclo=35),
                dict(nome='Asciugatrice 16kg Gas', categoria='Asciugatrici', modello='PRIMUS T16', prezzo=5500, kw=0.5, cicli_giorno=8, tariffa=3.5, attiva=True, in_evidenza=False, combustibile='gas', mc_ciclo=0.28, capacita_kg=16, durata_ciclo=35),
                dict(nome='Cassa Automatica RFID', categoria='Sistemi', modello='EntryPoint RFID', prezzo=2800, kw=0.1, cicli_giorno=0, tariffa=0, attiva=True, in_evidenza=True, combustibile='elettrico'),
                dict(nome='Cabina Ozono', categoria='Sistemi', modello='O3 143W', prezzo=4200, kw=0.1, cicli_giorno=0, tariffa=0, attiva=True, in_evidenza=False, combustibile='elettrico'),
                dict(nome='Impianto Elettrico', categoria='Impianti', modello='Standard', prezzo=3500, kw=0, cicli_giorno=0, tariffa=0, attiva=True, in_evidenza=False, combustibile='elettrico'),
                dict(nome='Impianto Idraulico', categoria='Impianti', modello='Standard', prezzo=2500, kw=0, cicli_giorno=0, tariffa=0, attiva=True, in_evidenza=False, combustibile='elettrico'),
                dict(nome='Impianto Gas', categoria='Impianti', modello='Standard', prezzo=2000, kw=0, cicli_giorno=0, tariffa=0, attiva=True, in_evidenza=False, combustibile='gas'),
                dict(nome='Canna Fumaria', categoria='Impianti', modello='Standard', prezzo=1500, kw=0, cicli_giorno=0, tariffa=0, attiva=True, in_evidenza=False, combustibile='gas'),
                dict(nome='Tavolo Piega + Carrello', categoria='Arredamento', modello='Standard', prezzo=480, kw=0, cicli_giorno=0, tariffa=0, attiva=True, in_evidenza=False, combustibile='elettrico'),
                dict(nome='Insegna LED 220x50cm', categoria='Arredamento', modello='LED', prezzo=1800, kw=0.2, cicli_giorno=0, tariffa=0, attiva=True, in_evidenza=False, combustibile='elettrico'),
            ]
            for m in machines:
                db.session.add(Macchina(**m))
            db.session.commit()
            print("[INIT] Macchine create.", flush=True)
    except Exception as e:
        db.session.rollback()
        print(f"[INIT] Macchine error: {e}", flush=True)

print("[INIT] Database pronto!", flush=True)
