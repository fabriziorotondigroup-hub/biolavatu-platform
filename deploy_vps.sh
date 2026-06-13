#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# deploy_vps.sh — BIOLavaTU LaundryPro Platform
# Deploy completo VPS Aruba 80.211.27.203
# 
# USO:
#   cd /var/www/laundrypro
#   bash deploy_vps.sh
# ═══════════════════════════════════════════════════════════════════════════

set -e

VERDE='\033[0;32m'
ROSSO='\033[0;31m'
GIALLO='\033[1;33m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   BIOLavaTU LaundryPro — Deploy VPS Aruba                   ║"
printf "║   %-58s ║\n" "$(date '+%d/%m/%Y %H:%M:%S')"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. GIT PULL ──────────────────────────────────────────────────────────────
echo -e "${GIALLO}▶ [1/6] Aggiornamento codice da GitHub...${NC}"
git fetch origin main
BEHIND=$(git rev-list HEAD..origin/main --count)
if [ "$BEHIND" = "0" ]; then
    echo -e "   ${VERDE}✅ Già aggiornato — nessun nuovo commit${NC}"
else
    echo -e "   📦 $BEHIND nuovo/i commit da scaricare"
    git pull origin main
    echo -e "   ${VERDE}✅ Codice aggiornato${NC}"
fi
echo ""

# ── 2. DIPENDENZE PYTHON ──────────────────────────────────────────────────────
echo -e "${GIALLO}▶ [2/6] Verifica dipendenze Python...${NC}"
venv/bin/pip install -q -r requirements.txt
echo -e "   ${VERDE}✅ Dipendenze OK${NC}"
echo ""

# ── 3. MIGRATION DATABASE — colonne nuove ────────────────────────────────────
echo -e "${GIALLO}▶ [3/6] Migration database...${NC}"
if [ -f "migrate_investitore.py" ]; then
    venv/bin/python3 migrate_investitore.py
else
    echo -e "   ${GIALLO}⚠️  migrate_investitore.py non trovato — skip${NC}"
fi
echo ""

# ── 4. AGGIORNAMENTO SETTINGS DB ─────────────────────────────────────────────
echo -e "${GIALLO}▶ [4/6] Aggiornamento dati aziendali nel DB...${NC}"
if [ -f "update_settings.py" ]; then
    venv/bin/python3 update_settings.py
else
    echo -e "   ${GIALLO}⚠️  update_settings.py non trovato — skip${NC}"
fi
echo ""

# ── 5. ASSET STATICI ─────────────────────────────────────────────────────────
echo -e "${GIALLO}▶ [5/6] Verifica asset statici...${NC}"
mkdir -p static/img
if [ -f "static/img/biolavatu_logo.png" ]; then
    SIZE=$(du -h static/img/biolavatu_logo.png | cut -f1)
    echo -e "   ${VERDE}✅ Logo BIOLavaTU presente ($SIZE)${NC}"
else
    echo -e "   ${ROSSO}❌ Logo non trovato in static/img/ — necessario per i PDF${NC}"
fi
echo ""

# ── 6. RIAVVIO SERVIZIO ───────────────────────────────────────────────────────
echo -e "${GIALLO}▶ [6/6] Riavvio servizio laundrypro...${NC}"
systemctl restart laundrypro
sleep 3

STATUS=$(systemctl is-active laundrypro)
if [ "$STATUS" = "active" ]; then
    echo -e "   ${VERDE}✅ Servizio attivo${NC}"
else
    echo -e "   ${ROSSO}❌ Servizio NON attivo — controlla:${NC}"
    echo "      journalctl -u laundrypro -n 50 --no-pager"
    exit 1
fi
echo ""

# ── RIEPILOGO ─────────────────────────────────────────────────────────────────
COMMIT=$(git log -1 --format="%h — %s" 2>/dev/null || echo "N/D")
echo "╔══════════════════════════════════════════════════════════════╗"
echo -e "║  ${VERDE}✅  DEPLOY COMPLETATO${NC}                                       ║"
echo "║                                                              ║"
printf "║  Commit:  %-51s ║\n" "$COMMIT"
echo "║  URL:     https://laundryproplatform.it                      ║"
echo "║  Log:     journalctl -u laundrypro -f                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
