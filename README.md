# BIOLavaTU — LaundryPro AI Platform

Piattaforma commerciale per lavanderie self-service con AI integrata, geolocalizzazione Google Maps e generazione PDF professionale.

## Stack
- **Backend**: Flask + SQLAlchemy + Flask-Login
- **Database**: PostgreSQL (Railway) / SQLite (locale)
- **AI**: Claude claude-sonnet-4-20250514 (Anthropic)
- **Mappe**: Google Maps API (Geocoding, Places, Street View)
- **PDF**: ReportLab
- **Deploy**: Railway

---

## Setup locale

```bash
# 1. Clone e installa
pip install -r requirements.txt

# 2. Crea .env (copia da .env.example)
cp .env.example .env
# Imposta le variabili:
#   SECRET_KEY=...
#   GMAPS_KEY=AIza...
#   ANTHROPIC_API_KEY=sk-ant-...

# 3. Avvia
python app.py
```

Apri `http://localhost:5000`

---

## Deploy su Railway

```bash
# 1. Installa Railway CLI
npm i -g @railway/cli

# 2. Login e crea progetto
railway login
railway init

# 3. Aggiungi PostgreSQL
railway add --database postgres

# 4. Imposta variabili d'ambiente su Railway dashboard:
#    SECRET_KEY
#    GMAPS_KEY
#    ANTHROPIC_API_KEY

# 5. Deploy
railway up
```

---

## Variabili d'ambiente richieste

| Variabile | Descrizione |
|-----------|-------------|
| `SECRET_KEY` | Chiave segreta Flask (min 32 caratteri) |
| `GMAPS_KEY` | Google Maps API Key (Geocoding + Places + Street View) |
| `ANTHROPIC_API_KEY` | Anthropic API Key per Claude AI |
| `DATABASE_URL` | PostgreSQL URL (fornito da Railway automaticamente) |

### Google Maps API — servizi da abilitare
1. Geocoding API
2. Places API (Nearby Search)
3. Street View Static API
4. Maps JavaScript API

---

## Credenziali default

| Email | Password | Ruolo |
|-------|----------|-------|
| fabrizio@rotondigroup.it | BioLava2024! | Admin |
| agente@rotondigroup.it | Vendite2024! | Sales |

**Cambia le password dal pannello Admin dopo il primo accesso.**

---

## Struttura progetto

```
biolavatu/
├── app.py              # Flask app factory
├── models/
│   ├── user.py         # Utenti e login
│   ├── cliente.py      # Anagrafica clienti
│   ├── pratica.py      # Preventivi/pratiche
│   └── settings.py     # Impostazioni globali
├── routes/
│   ├── auth.py         # Login/logout
│   ├── dashboard.py    # Home
│   ├── preventivo.py   # Wizard preventivo + AI
│   ├── pratiche.py     # Gestione pratiche
│   ├── clienti.py      # Gestione clienti
│   ├── geo.py          # Google Maps + OSM
│   ├── pdf.py          # Generazione PDF
│   └── admin.py        # Admin panel
├── services/
│   └── pdf_service.py  # ReportLab PDF completo
├── templates/
│   ├── base.html       # Layout master responsive
│   ├── login.html      # Login page
│   ├── preventivo.html # Wizard 5-step con Google Maps
│   └── ...
├── requirements.txt
├── Procfile
└── railway.toml
```

---

## Funzionalità

### Preventivo AI (5 step)
1. **Cliente** — selezione da DB o creazione al momento
2. **Sede & Geo** — geocodifica Google Maps, mappa interattiva, isocrone 3/5 min, concorrenti Google Places, Street View, analisi AI zona completa (demografica, reddito, ownership lavatrice/asciugatrice, potenziale mercato)
3. **Macchine** — configuratore con suggerimento AI automatico
4. **Analisi AI** — cashflow 36 mesi, 3 scenari, business plan Claude, analisi rischi Claude
5. **Contratto** — 11 clausole blindate + clausole AI personalizzate, generazione PDF

### PDF Professionale (4 pagine)
- **Copertina** dark gradient con badge score
- **Analisi Zona** — parti, KPI geo, competitor table
- **Macchine + Business Plan** — tabella CAPEX, proiezione economica, AI analysis
- **Contratto** — 11 articoli in 2 colonne, clausole AI, firme con doppia sottoscrizione ex art. 1341-1342 c.c.
