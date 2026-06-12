#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# deploy_vps.sh — BIOLavaTU LaundryPro
# Script di deploy completo per VPS Aruba
# Eseguire come root nella directory /var/www/laundrypro
#
# Uso:
#   cd /var/www/laundrypro
#   bash deploy_vps.sh
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Blocca se un comando fallisce

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     BIOLavaTU LaundryPro — Deploy VPS Aruba                 ║"
echo "║     $(date '+%d/%m/%Y %H:%M:%S')                                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. GIT PULL ──────────────────────────────────────────────────────────────
echo "▶ [1/5] Aggiornamento codice da GitHub..."
git pull origin main
echo "   ✅ Codice aggiornato"
echo ""

# ── 2. DIPENDENZE PYTHON ──────────────────────────────────────────────────────
echo "▶ [2/5] Verifica dipendenze Python..."
venv/bin/pip install -q -r requirements.txt 2>/dev/null || \
venv/bin/pip install -q flask flask-sqlalchemy flask-login psycopg2-binary \
    reportlab Pillow requests anthropic gunicorn 2>/dev/null
echo "   ✅ Dipendenze OK"
echo ""

# ── 3. MIGRATION DATABASE ─────────────────────────────────────────────────────
echo "▶ [3/5] Migration database (colonne nuove)..."
if [ -f "migrate_investitore.py" ]; then
    venv/bin/python3 migrate_investitore.py
    echo "   ✅ Migration completata"
else
    echo "   ⚠️  migrate_investitore.py non trovato — skip"
fi
echo ""

# ── 4. AGGIORNAMENTO SETTINGS DB ─────────────────────────────────────────────
echo "▶ [4/5] Aggiornamento dati aziendali nel DB..."
if [ -f "update_settings.py" ]; then
    venv/bin/python3 update_settings.py
    echo "   ✅ Settings aggiornati"
else
    echo "   ⚠️  update_settings.py non trovato — skip"
fi
echo ""

# ── 5. COPIA LOGO IN STATIC ───────────────────────────────────────────────────
echo "▶ [5/5] Verifica asset statici..."
mkdir -p static/img
if [ -f "static/img/biolavatu_logo.png" ]; then
    echo "   ✅ Logo BIOLavaTU presente"
else
    echo "   ⚠️  Logo non trovato in static/img/"
fi
echo ""

# ── RIAVVIO SERVIZIO ──────────────────────────────────────────────────────────
echo "▶ Riavvio servizio laundrypro..."
systemctl restart laundrypro
sleep 3

# Verifica che il servizio sia partito
STATUS=$(systemctl is-active laundrypro)
if [ "$STATUS" = "active" ]; then
    echo "   ✅ Servizio attivo e in esecuzione"
else
    echo "   ❌ Servizio non attivo — controlla i log:"
    echo "      journalctl -u laundrypro -n 30"
    exit 1
fi
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅  DEPLOY COMPLETATO                                       ║"
echo "║                                                              ║"
echo "║  Piattaforma: https://laundryproplatform.it                  ║"
echo "║  Log:  journalctl -u laundrypro -f                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
