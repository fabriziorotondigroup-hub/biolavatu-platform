"""
services/i18n.py — BIOLavaTU LaundryPro
Traduzioni IT/RO per tutta la piattaforma.
"""

TRADUZIONI = {
    # ── Navigazione ────────────────────────────────────────────────────────────
    'dashboard':          {'it': 'Dashboard',           'ro': 'Panou de control'},
    'pratiche':           {'it': 'Pratiche',             'ro': 'Dosare'},
    'nuova_pratica':      {'it': 'Nuova Pratica',        'ro': 'Dosar nou'},
    'clienti':            {'it': 'Clienti',              'ro': 'Clienți'},
    'impostazioni':       {'it': 'Impostazioni',         'ro': 'Setări'},
    'logout':             {'it': 'Esci',                 'ro': 'Deconectare'},
    'benvenuto':          {'it': 'Benvenuto',            'ro': 'Bun venit'},

    # ── Wizard step labels ─────────────────────────────────────────────────────
    'step_cliente':       {'it': 'Cliente',              'ro': 'Client'},
    'step_sede':          {'it': 'Sede',                 'ro': 'Locație'},
    'step_zona':          {'it': 'Analisi Zona',         'ro': 'Analiză zonă'},
    'step_macchine':      {'it': 'Macchine',             'ro': 'Utilaje'},
    'step_bp':            {'it': 'Business Plan',        'ro': 'Plan de afaceri'},
    'step_riepilogo':     {'it': 'Riepilogo',            'ro': 'Rezumat'},

    # ── Campi form ─────────────────────────────────────────────────────────────
    'nome':               {'it': 'Nome',                 'ro': 'Nume'},
    'cognome':            {'it': 'Cognome',              'ro': 'Prenume'},
    'azienda':            {'it': 'Azienda',              'ro': 'Companie'},
    'email':              {'it': 'Email',                'ro': 'Email'},
    'telefono':           {'it': 'Telefono',             'ro': 'Telefon'},
    'indirizzo':          {'it': 'Indirizzo',            'ro': 'Adresă'},
    'citta':              {'it': 'Città',                'ro': 'Oraș'},
    'cap':                {'it': 'CAP',                  'ro': 'Cod poștal'},
    'provincia':          {'it': 'Provincia',            'ro': 'Județ'},
    'superficie':         {'it': 'Superficie (mq)',      'ro': 'Suprafață (mp)'},
    'affitto':            {'it': 'Affitto mensile',      'ro': 'Chirie lunară'},
    'tipo_zona':          {'it': 'Tipo di zona',         'ro': 'Tipul zonei'},

    # ── Tipo zona ──────────────────────────────────────────────────────────────
    'zona_residenziale':  {'it': 'Residenziale',         'ro': 'Rezidențial'},
    'zona_universitaria': {'it': 'Universitaria',        'ro': 'Universitar'},
    'zona_turistica':     {'it': 'Turistica estiva',     'ro': 'Turistic estival'},
    'zona_mista':         {'it': 'Mista / Commerciale',  'ro': 'Mixt / Comercial'},

    # ── Analisi zona ───────────────────────────────────────────────────────────
    'pop_3min':           {'it': 'Pop. 3 min a piedi',   'ro': 'Pop. 3 min pe jos'},
    'pop_5min':           {'it': 'Pop. 5 min a piedi',   'ro': 'Pop. 5 min pe jos'},
    'pop_10min':          {'it': 'Pop. 10 min a piedi',  'ro': 'Pop. 10 min pe jos'},
    'concorrenti_500m':   {'it': 'Concorrenti 500m',     'ro': 'Concurenți 500m'},
    'score_zona':         {'it': 'Score Zona',           'ro': 'Scor zonă'},
    'analisi_zona':       {'it': 'Analisi di zona',      'ro': 'Analiză de zonă'},

    # ── Business plan ──────────────────────────────────────────────────────────
    'investimento':       {'it': 'Investimento',         'ro': 'Investiție'},
    'incasso_mensile':    {'it': 'Incasso mensile',      'ro': 'Încasări lunare'},
    'costi_mensili':      {'it': 'Costi mensili',        'ro': 'Costuri lunare'},
    'utile_netto':        {'it': 'Utile netto',          'ro': 'Profit net'},
    'payback':            {'it': 'Payback stimato',      'ro': 'Recuperare investiție'},
    'scenario_pess':      {'it': 'Pessimistico',         'ro': 'Pesimist'},
    'scenario_real':      {'it': 'Realistico',           'ro': 'Realist'},
    'scenario_ott':       {'it': 'Ottimistico',          'ro': 'Optimist'},

    # ── PDF ────────────────────────────────────────────────────────────────────
    'progetto_lav':       {'it': 'Progetto Lavanderia Self-Service',
                           'ro': 'Proiect Spălătorie Self-Service'},
    'ecocompatibile':     {'it': 'ECOCOMPATIBILE',       'ro': 'ECOCOMPATIBIL'},
    'preparato_per':      {'it': 'Preparato per',        'ro': 'Pregătit pentru'},
    'cgv_titolo':         {'it': 'Condizioni Generali di Vendita',
                           'ro': 'Condiții Generale de Vânzare'},
    'firme_titolo':       {'it': 'Sottoscrizione del Contratto',
                           'ro': 'Semnarea Contractului'},
    'il_fornitore':       {'it': 'Il Fornitore',         'ro': 'Furnizorul'},
    'il_cliente':         {'it': 'Il Cliente',           'ro': 'Clientul'},

    # ── Valuta ─────────────────────────────────────────────────────────────────
    'valuta_it':          {'it': '€ (Euro)',              'ro': 'RON (Leu românesc)'},
    'iva':                {'it': 'IVA 22%',               'ro': 'TVA 19%'},
    'totale_iva':         {'it': 'TOTALE IVA INCLUSA',   'ro': 'TOTAL CU TVA INCLUS'},

    # ── Messaggi ───────────────────────────────────────────────────────────────
    'salva':              {'it': 'Salva',                 'ro': 'Salvează'},
    'avanti':             {'it': 'Avanti',                'ro': 'Înainte'},
    'indietro':           {'it': 'Indietro',             'ro': 'Înapoi'},
    'analizza':           {'it': 'Analizza zona',         'ro': 'Analizează zona'},
    'genera_pdf':         {'it': 'Genera PDF',           'ro': 'Generează PDF'},
    'caricamento':        {'it': 'Caricamento...',       'ro': 'Se încarcă...'},
    'errore':             {'it': 'Errore',               'ro': 'Eroare'},
    'successo':           {'it': 'Salvato con successo', 'ro': 'Salvat cu succes'},
    'doc_riservato':      {'it': 'Documento riservato e confidenziale',
                           'ro': 'Document confidențial'},
}

def t(chiave: str, lingua: str = 'it') -> str:
    """
    Traduce una chiave nella lingua specificata.
    Uso: t('dashboard', 'ro') → 'Panou de control'
    """
    entry = TRADUZIONI.get(chiave, {})
    return entry.get(lingua, entry.get('it', chiave))

def get_all(lingua: str = 'it') -> dict:
    """Ritorna tutte le traduzioni per una lingua — per passarle al template JS."""
    return {k: v.get(lingua, v.get('it', k)) for k, v in TRADUZIONI.items()}
