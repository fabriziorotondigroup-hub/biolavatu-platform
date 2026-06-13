"""
migrate_investitore.py — Aggiunge i campi versione investitore alla tabella pratiche.
Eseguire UNA VOLTA su Railway e VPS dopo il deploy.

Railway:
  railway run python migrate_investitore.py

VPS:
  cd /var/www/laundrypro && venv/bin/python3 migrate_investitore.py
"""
import os, sys

# Usa DATABASE_URL dall'ambiente
database_url = os.environ.get('DATABASE_URL', '')
if not database_url:
    print("❌ DATABASE_URL non trovata nelle variabili d'ambiente")
    sys.exit(1)

print(f"✅ DATABASE_URL trovata: {database_url[:40]}...")

import psycopg2
from urllib.parse import urlparse

# Parse URL
url = urlparse(database_url)
conn = psycopg2.connect(
    host=url.hostname,
    port=url.port or 5432,
    database=url.path[1:],
    user=url.username,
    password=url.password,
    sslmode='require' if 'railway' in database_url else 'prefer'
)
conn.autocommit = True
cur = conn.cursor()

# Lista colonne da aggiungere: (nome, tipo_sql, default)
COLONNE = [
    ('tipo_pratica',              'VARCHAR(20)',  "'standard'"),
    ('sopralluogo_json',          'TEXT',         'NULL'),
    ('sopralluogo_completato',    'BOOLEAN',      'FALSE'),
    ('concorrenza_campo_json',    'TEXT',         'NULL'),
    ('score_investitore',         'FLOAT',        '0.0'),
    ('confidenza_pct',            'INTEGER',      '0'),
    ('confidenza_label',          'VARCHAR(20)',  'NULL'),
    ('raccomandazione',           'VARCHAR(20)',  'NULL'),
    ('analisi_investitore_json',  'TEXT',         'NULL'),
    ('visibilita_vetrina',        'INTEGER',      '0'),
    ('parcheggio_diretto',        'BOOLEAN',      'FALSE'),
    ('n_posti_parcheggio',        'INTEGER',      '0'),
    ('distanza_arteria_m',        'INTEGER',      '0'),
    ('lato_soleggiato',           'BOOLEAN',      'TRUE'),
    ('cantieri_previsti',         'BOOLEAN',      'FALSE'),
    ('note_sopralluogo',          'TEXT',         'NULL'),
    # Modifica 3 — tipo zona per stagionalità
    ('tipo_zona',                 "VARCHAR(20)",  "'residenziale'"),
]

print("\n📋 Verifico colonne nella tabella pratiche...")

aggiunte = 0
esistenti = 0

for nome, tipo, default in COLONNE:
    # Controlla se la colonna esiste già
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name = 'pratiche' AND column_name = %s
    """, (nome,))
    esiste = cur.fetchone()[0] > 0

    if esiste:
        print(f"  ✓ {nome} — già presente")
        esistenti += 1
    else:
        try:
            sql = f"ALTER TABLE pratiche ADD COLUMN {nome} {tipo} DEFAULT {default}"
            cur.execute(sql)
            print(f"  ✅ {nome} — aggiunta")
            aggiunte += 1
        except Exception as e:
            print(f"  ❌ {nome} — errore: {e}")

cur.close()
conn.close()

print(f"\n{'='*50}")
print(f"✅ Migration completata:")
print(f"   Colonne aggiunte:   {aggiunte}")
print(f"   Colonne esistenti:  {esistenti}")
print(f"   Totale processate:  {aggiunte + esistenti}/{len(COLONNE)}")

if aggiunte + esistenti == len(COLONNE):
    print("\n🟢 Database aggiornato correttamente — riavvia l'app.")
else:
    print("\n🔴 Alcune colonne non sono state aggiunte — controlla gli errori sopra.")
