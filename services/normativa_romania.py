"""
services/normativa_romania.py — BIOLavaTU LaundryPro
Normativa apertura lavanderia self-service in Romania.
Bilingue IT/RO. ISOLATO.
"""

NORMATIVA_RO = {
    'it': {
        'titolo': 'Normativa apertura lavanderia self-service in Romania',
        'sezioni': [
            {
                'id': 'piva',
                'titolo': '1. Costituzione società / Partita IVA',
                'colore': '#3b82f6',
                'icona': '🏢',
                'voci': [
                    ('SRL (Societate cu Răspundere Limitată)', 'Equivalente alla Srl italiana. Capitale minimo: 200 RON (~40€). Forma più comune per lavanderie.'),
                    ('Registrazione ONRC', 'Ufficio Nazionale del Registro del Commercio. Tempo medio: 3-5 giorni lavorativi. Costo: ~200 RON.'),
                    ('Codice CUI', 'Codice Unico di Identificazione fiscale — equivalente alla P.IVA italiana. Obbligatorio.'),
                    ('Codice CAEN 9601', 'Codice attività: "Spălarea și curățarea articolelor textile și de blănărie" — lavaggio biancheria. Da dichiarare all\'ONRC.'),
                    ('Apertura conto bancario aziendale', 'Obbligatorio prima di iniziare l\'attività. Principali banche: BCR, BRD, ING, Raiffeisen.'),
                    ('Registrazione ANAF', 'Agenzia Nazionale Amministrazione Fiscale — equivalente all\'Agenzia delle Entrate. Entro 30 giorni dall\'avvio.'),
                ],
            },
            {
                'id': 'autorizzazioni',
                'titolo': '2. Autorizzazioni comunali',
                'colore': '#f59e0b',
                'icona': '📋',
                'voci': [
                    ('Aviz de funcționare', 'Autorizzazione comunale all\'esercizio dell\'attività. Si ottiene dalla Primărie (Comune) del luogo.'),
                    ('Certificat de urbanism', 'Certificato urbanistico — verifica compatibilità zona con attività commerciale.'),
                    ('Autorizație de construire', 'Se si fanno lavori strutturali o cambio destinazione d\'uso. Richiede progetto firmato da architetto abilitato.'),
                    ('Aviz sanitar', 'Autorizzazione sanitaria della DSP (Direzione Sanità Pubblica). Obbligatoria. Include ispezione locale.'),
                    ('Aviz de mediu', 'Valutazione ambientale della APM (Agenzia Protezione Ambiente). Per lavanderie: procedura semplificata.'),
                    ('Înregistrare la ANPC', 'Registro Autorità Nazionale Protezione Consumatori — per attività a contatto con il pubblico.'),
                ],
            },
            {
                'id': 'antincendio',
                'titolo': '3. Norme antincendio (PSI)',
                'colore': '#ef4444',
                'icona': '🔥',
                'voci': [
                    ('Scenariul de securitate la incendiu', 'Documento tecnico obbligatorio redatto da esperto abilitato. Descrive misure antincendio specifiche del locale.'),
                    ('Aviz ISU', 'Autorizzazione dell\'Ispettorato per Situazioni di Emergenza. Obbligatorio prima dell\'apertura. Tempi: 30-60 giorni.'),
                    ('Dotare PSI obbligatoria', 'Estintori classe ABC ogni 150 mq, segnaletica vie d\'uscita, rilevatori fumo, piano evacuazione esposto.'),
                    ('Capacità massima affollamento', 'Il locale deve avere vie d\'uscita dimensionate per la capienza massima. Per lavanderie: 1 persona ogni 4 mq.'),
                    ('Revisioni periodiche', 'Estintori: revisione annuale. Impianto rilevazione incendi: semestrale. Documentazione da conservare.'),
                ],
            },
            {
                'id': 'reflui',
                'titolo': '4. Smaltimento reflui e acque di scarico',
                'colore': '#10b981',
                'icona': '💧',
                'voci': [
                    ('Aviz de racordare la rețeaua de canalizare', 'Autorizzazione allaccio fognatura — rilasciata dall\'operatore locale (es. Apa Nova, RAJA). Obbligatorio.'),
                    ('Separator de grăsimi și detergent', 'Separatore di grassi/detersivi obbligatorio per scarichi lavanderie. Dimensionato in base al numero macchine.'),
                    ('Contract de salubrizare', 'Contratto smaltimento rifiuti solidi. Obbligatorio con operatore autorizzato comunale.'),
                    ('Monitorizare ape uzate', 'Per lavanderie > 5 macchine: analisi periodica acque reflue richiesta da APM. Frequenza: annuale.'),
                    ('Conformitate NTPA 002', 'Le acque scaricate devono rispettare NTPA 002/2002 (normativa qualità reflui in fognatura pubblica).'),
                ],
            },
            {
                'id': 'imposte',
                'titolo': '5. Imposte societarie',
                'colore': '#8b5cf6',
                'icona': '💰',
                'voci': [
                    ('Imposta pe profit: 16%', 'Aliquota standard sul reddito d\'impresa. Per microimprese (fatturato < 500.000€): 1% o 3% sul fatturato.'),
                    ('TVA (IVA): 19%', 'Aliquota standard. Registrazione TVA obbligatoria sopra 88.500 RON/anno (~17.800€). Dichiarazione mensile o trimestrale.'),
                    ('Imposta pe dividende: 8%', 'Ritenuta sui dividendi distribuiti ai soci. Dal 2023: 8% (ridotta dal precedente 5%).'),
                    ('Impozit pe clădiri', 'Imposta municipale sugli immobili: 0,2%-1,3% del valore catastale annuo. Se in affitto: a carico del proprietario.'),
                    ('Taxa de salubrizare', 'Tassa rifiuti comunale: variabile per comune, mediamente 50-150 RON/mese per attività commerciale.'),
                    ('Contribuție la mediu', 'Contributo ambientale: se si usano imballaggi/detersivi. Dichiarazione annuale all\'AFM.'),
                ],
            },
            {
                'id': 'dipendenti',
                'titolo': '6. Contributi dipendenti (se presenti)',
                'colore': '#06b6d4',
                'icona': '👥',
                'voci': [
                    ('Salariul minim brut 2024', '3.300 RON/mese (~660€) — salario minimo nazionale. Per lavanderie self-service spesso non necessario personale fisso.'),
                    ('CAS (pensione): 25%', 'Contributo pensione — a carico del dipendente. Il datore lo trattiene e versa all\'ANAF.'),
                    ('CASS (sanità): 10%', 'Contributo sanitario — a carico del dipendente. Versato mensile all\'ANAF.'),
                    ('Imposta pe venit: 10%', 'Imposta sul reddito dei dipendenti — trattenuta dal datore. Aliquota flat 10%.'),
                    ('Contribuție angajator: 2,25%', 'Contributo a carico del datore: assicurazione accidenti sul lavoro (variabile per settore).'),
                    ('Registrare Revisal', 'Obbligatorio registrare ogni contratto di lavoro nel Registro Elettronico del Lavoro (ReviSal) entro il giorno precedente l\'inizio.'),
                    ('Medicina muncii', 'Visita medica obbligatoria per ogni dipendente prima dell\'assunzione e periodicamente (annuale).'),
                ],
            },
        ],
        'note_finali': [
            'Per lavanderie self-service completamente automatizzate (senza personale) i contributi dipendenti non si applicano.',
            'Tempi medi totali per ottenere tutte le autorizzazioni: 60-120 giorni.',
            'Costo medio consulenza legale/fiscale per apertura SRL in Romania: 800-1.500 RON.',
            'Alcuni comuni offrono sportello unico (ghișeu unic) per concentrare le pratiche.',
        ],
    },

    'ro': {
        'titolo': 'Normativa deschidere spălătorie self-service în România',
        'sezioni': [
            {
                'id': 'piva',
                'titolo': '1. Înregistrare societate / CUI fiscal',
                'colore': '#3b82f6',
                'icona': '🏢',
                'voci': [
                    ('SRL (Societate cu Răspundere Limitată)', 'Forma juridică recomandată. Capital minim: 200 RON. Procesare: 3-5 zile lucrătoare.'),
                    ('Înregistrare la ONRC', 'Oficiul Național al Registrului Comerțului. Taxa: ~200 RON. Se poate face online sau fizic.'),
                    ('Cod CUI', 'Codul Unic de Identificare — obligatoriu pentru orice activitate comercială.'),
                    ('Cod CAEN 9601', '"Spălarea și curățarea articolelor textile și de blănărie" — de declarat la ONRC.'),
                    ('Cont bancar al societății', 'Obligatoriu înainte de începerea activității. Bănci recomandate: BCR, BRD, ING, Raiffeisen.'),
                    ('Înregistrare la ANAF', 'Agenția Națională de Administrare Fiscală — în termen de 30 zile de la deschidere.'),
                ],
            },
            {
                'id': 'autorizzazioni',
                'titolo': '2. Autorizații comunale',
                'colore': '#f59e0b',
                'icona': '📋',
                'voci': [
                    ('Aviz de funcționare', 'Eliberat de Primărie. Necesar pentru orice activitate comercială cu public.'),
                    ('Certificat de urbanism', 'Verifică compatibilitatea zonei cu activitatea comercială planificată.'),
                    ('Autorizație de construire', 'Necesară dacă se fac lucrări structurale. Proiect semnat de arhitect autorizat.'),
                    ('Aviz sanitar DSP', 'Eliberat de Direcția de Sănătate Publică. Include inspecție la fața locului.'),
                    ('Aviz de mediu APM', 'Agenția pentru Protecția Mediului. Procedură simplificată pentru spălătorii.'),
                    ('Înregistrare ANPC', 'Autoritatea Națională pentru Protecția Consumatorilor.'),
                ],
            },
            {
                'id': 'antincendio',
                'titolo': '3. Norme PSI (Prevenire și Stingere Incendii)',
                'colore': '#ef4444',
                'icona': '🔥',
                'voci': [
                    ('Scenariu de securitate la incendiu', 'Document tehnic obligatoriu redactat de specialist atestat IGSU.'),
                    ('Aviz ISU', 'Inspectoratul pentru Situații de Urgență. Obligatoriu înainte de deschidere. Durată: 30-60 zile.'),
                    ('Dotare PSI minimă', 'Stingătoare ABC la fiecare 150 mp, marcaj căi evacuare, detectoare fum, plan evacuare afișat.'),
                    ('Capacitate maximă', '1 persoană la 4 mp suprafață utilă.'),
                    ('Verificări periodice', 'Stingătoare: anual. Instalație detecție incendiu: semestrial.'),
                ],
            },
            {
                'id': 'reflui',
                'titolo': '4. Evacuare ape uzate',
                'colore': '#10b981',
                'icona': '💧',
                'voci': [
                    ('Aviz racordare canalizare', 'Eliberat de operatorul local (Apa Nova, RAJA etc.). Obligatoriu.'),
                    ('Separator grăsimi/detergenți', 'Obligatoriu pentru evacuările spălătoriilor. Dimensionat în funcție de numărul mașinilor.'),
                    ('Contract salubrizare', 'Contract cu operator autorizat pentru deșeuri solide.'),
                    ('Monitorizare ape uzate', 'Pentru >5 mașini: analize periodice solicitate de APM.'),
                    ('Conformitate NTPA 002/2002', 'Apele evacuate trebuie să respecte normele de calitate pentru canalizare publică.'),
                ],
            },
            {
                'id': 'imposte',
                'titolo': '5. Impozite și taxe',
                'colore': '#8b5cf6',
                'icona': '💰',
                'voci': [
                    ('Impozit pe profit: 16%', 'Cota standard. Microîntreprinderi (CA < 500.000€): 1% sau 3% aplicat la cifra de afaceri.'),
                    ('TVA: 19%', 'Înregistrare TVA obligatorie peste 88.500 RON/an. Declarație lunară sau trimestrială.'),
                    ('Impozit dividende: 8%', 'Reținut la sursă la distribuirea dividendelor.'),
                    ('Impozit pe clădiri', '0,2%-1,3% din valoarea impozabilă. Dacă în chirie: în sarcina proprietarului.'),
                    ('Taxă salubrizare', 'Variabilă pe municipiu: 50-150 RON/lună pentru activități comerciale.'),
                ],
            },
            {
                'id': 'dipendenti',
                'titolo': '6. Contribuții angajați (dacă există personal)',
                'colore': '#06b6d4',
                'icona': '👥',
                'voci': [
                    ('Salariu minim brut 2024: 3.300 RON', 'Salariu minim național (~660€/lună). Spălătoriile self-service funcționează adesea fără personal fix.'),
                    ('CAS (pensie): 25%', 'Contribuție pensie — din salariul angajatului.'),
                    ('CASS (sănătate): 10%', 'Contribuție asigurări sănătate — din salariul angajatului.'),
                    ('Impozit pe venit: 10%', 'Cotă unică reținută de angajator.'),
                    ('Contribuție angajator: 2,25%', 'Asigurare accidente de muncă — variabilă pe sector.'),
                    ('Înregistrare ReviSal', 'Obligatoriu înregistrarea contractului în Registrul Electronic înainte de prima zi de muncă.'),
                    ('Medicina muncii', 'Examen medical obligatoriu înainte de angajare și periodic (anual).'),
                ],
            },
        ],
        'note_finali': [
            'Spălătoriile complet automatizate (fără personal) nu necesită contribuții angajați.',
            'Timp mediu total pentru obținerea tuturor autorizațiilor: 60-120 zile.',
            'Cost mediu consultanță juridică/fiscală pentru deschidere SRL: 800-1.500 RON.',
            'Unele municipii oferă ghișeu unic pentru concentrarea procedurilor administrative.',
        ],
    }
}
