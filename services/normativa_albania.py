"""
services/normativa_albania.py — BIOLavaTU LaundryPro
Normativa apertura lavanderia self-service in Albania.
Bilingue IT/AL. ISOLATO.
"""

NORMATIVA_AL = {
    'it': {
        'titolo': 'Normativa apertura lavanderia self-service in Albania',
        'sezioni': [
            {
                'id': 'piva',
                'titolo': '1. Costituzione società / NIPT fiscale',
                'colore': '#3b82f6',
                'icona': 'SH',
                'voci': [
                    ('SHPK (Shoqëri me Përgjegjësi të Kufizuar)', 'Equivalente alla Srl italiana. Capitale minimo: 100 ALL (circa 1 EUR). Forma più comune per lavanderie.'),
                    ('Registrazione QKB', 'Qendra Kombëtare e Biznesit — Registro Nazionale delle Imprese. Tempo: 1-3 giorni lavorativi. Procedura online disponibile.'),
                    ('NIPT (Numri i Identifikimit të Personit Tatimor)', 'Codice fiscale aziendale — equivalente alla P.IVA italiana. Rilasciato automaticamente alla registrazione QKB.'),
                    ('Codice NACE 9601', 'Attività: "Lavaggio e pulitura di articoli tessili e pellicce" — da dichiarare al QKB.'),
                    ('Conto bancario aziendale', 'Obbligatorio. Principali banche: Raiffeisen Bank Albania, BKT, Credins Bank, OTP Bank.'),
                    ('Registrazione DPT', 'Drejtoria e Përgjithshme e Tatimeve — Agenzia delle Entrate Albania. Entro 15 giorni dall\'avvio attività.'),
                ],
            },
            {
                'id': 'autorizzazioni',
                'titolo': '2. Autorizzazioni comunali e sanitarie',
                'colore': '#f59e0b',
                'icona': 'AU',
                'voci': [
                    ('Leje ushtrimi veprimtarie', 'Licenza esercizio attività commerciale. Rilasciata dal Bashkia (Comune) competente per territorio.'),
                    ('Çertifikatë e përdorimit', 'Certificato di agibilità del locale — verifica conformità strutturale e destinazione d\'uso.'),
                    ('Autorizim sanitar', 'Autorizzazione sanitaria dell\'ISHP (Istituto di Salute Pubblica). Obbligatoria. Ispezione in loco.'),
                    ('Autorizim mjedisor', 'Valutazione ambientale dell\'AKM (Agenzia per l\'Ambiente). Per lavanderie: procedura semplificata Categoria C.'),
                    ('Regjistrimi AKEP', 'Per attività che utilizzano apparecchiature elettriche ad alto consumo: notifica all\'autorità energetica.'),
                    ('Plani i emergjencës', 'Piano di emergenza e evacuazione obbligatorio, approvato dalla struttura locale dei Vigili del Fuoco.'),
                ],
            },
            {
                'id': 'antincendio',
                'titolo': '3. Norme antincendio',
                'colore': '#ef4444',
                'icona': 'ZJ',
                'voci': [
                    ('Projekt mbrojtje nga zjarri', 'Progetto tecnico antincendio obbligatorio, firmato da ingegnere abilitato e approvato dalla Drejtoria e Zjarrfikësve.'),
                    ('Leje mbrojtje nga zjarri', 'Autorizzazione antincendio della Drejtoria e Përgjithshme e Zjarrfikësve. Obbligatoria prima dell\'apertura.'),
                    ('Dotazione minima obbligatoria', 'Estintori polvere ABC ogni 150 mq, segnaletica vie di uscita, rilevatori di fumo, mappa evacuazione esposta.'),
                    ('Ispezione periodica', 'Ispezione annuale della struttura antincendio. Documentazione da conservare per almeno 5 anni.'),
                    ('Formazione dipendenti', 'Se presenti dipendenti: formazione base antincendio obbligatoria (almeno un addetto per turno).'),
                ],
            },
            {
                'id': 'reflui',
                'titolo': '4. Smaltimento reflui e acque di scarico',
                'colore': '#10b981',
                'icona': 'UJ',
                'voci': [
                    ('Leje lidhje kanalizim', 'Autorizzazione allaccio fognatura comunale. Rilasciata dall\'operatore locale (UKT Tiranë, o operatori locali).'),
                    ('Separator dhjamrash', 'Separatore di grassi e detersivi obbligatorio a monte dello scarico in fognatura. Dimensionato per numero macchine.'),
                    ('Kontratë heqje mbetjeve', 'Contratto raccolta rifiuti solidi con operatore autorizzato comunale. Obbligatorio.'),
                    ('Analiza ujërave të ndotura', 'Per lavanderie con più di 5 macchine: analisi periodiche acque reflue richieste dall\'Inspektorati i Mjedisit.'),
                    ('Konformitet VKM 177/2005', 'Le acque scaricate devono rispettare il VKM nr. 177, datë 31.3.2005 (normativa qualità reflui in fognatura).'),
                ],
            },
            {
                'id': 'imposte',
                'titolo': '5. Imposte societarie',
                'colore': '#8b5cf6',
                'icona': 'TA',
                'voci': [
                    ('Tatimi mbi fitimin: 15%', 'Imposta sul reddito delle società. Aliquota flat 15%. Per piccole imprese (fatturato < 14 milioni ALL): imposta semplificata 0%.'),
                    ('TVSH (IVA): 20%', 'Aliquota standard. Registrazione IVA obbligatoria sopra 10 milioni ALL/anno (~100.000 EUR). Dichiarazione mensile.'),
                    ('Tatimi mbi dividendët: 8%', 'Ritenuta sui dividendi distribuiti ai soci. Aliquota 8%.'),
                    ('Taksa vendore', 'Imposta comunale sull\'attività: variabile per comune. Tirana: ~15.000-50.000 ALL/anno per attività commerciale.'),
                    ('Tatimi i thjeshtuar', 'Per fatturati tra 5-14 milioni ALL: imposta semplificata del 5% sul fatturato. Eliminazione progressiva dal 2024.'),
                    ('Kontributi mjedisor', 'Contributo ambientale per utilizzo di detersivi e consumo acqua. Dichiarazione annuale all\'AKM.'),
                ],
            },
            {
                'id': 'dipendenti',
                'titolo': '6. Contributi dipendenti (se presenti)',
                'colore': '#06b6d4',
                'icona': 'PU',
                'voci': [
                    ('Paga minimale 2024: 40.000 ALL/mese', 'Salario minimo nazionale (~406 EUR/mese). Lavanderie self-service spesso operano senza personale fisso.'),
                    ('Sigurimet shoqërore (pensione): 9,5%', 'A carico del datore di lavoro. Versato mensilmente alla DPT.'),
                    ('Sigurimet shëndetësore (sanità): 1,7%', 'Contributo sanitario a carico del datore. Versato mensile.'),
                    ('Tatimi mbi të ardhurat personale: 0-23%', 'Imposta sul reddito lavoratori: 0% fino a 30.000 ALL/mese, 13% fino a 150.000, 23% oltre.'),
                    ('Kontributi i punonjësit shoqëror: 9,5%', 'Contributo pensione a carico del dipendente, trattenuto dal datore.'),
                    ('Regjistrim kontratë pune', 'Ogni contratto di lavoro va registrato all\'Ispettorato del Lavoro entro 24 ore dall\'inizio rapporto.'),
                    ('Vizita mjekësore', 'Visita medica preventiva obbligatoria prima dell\'assunzione.'),
                ],
            },
        ],
        'note_finali': [
            'L\'Albania ha semplificato notevolmente le procedure con il Vendosje e Biznesit (sportello unico online su e-albania.al).',
            'Tempi medi per ottenere tutte le autorizzazioni: 30-60 giorni (più rapido rispetto alla Romania).',
            'Costo medio consulenza legale/fiscale per apertura SHPK: 500-1.000 EUR.',
            'L\'Albania è in processo di adesione all\'UE: normative in progressivo allineamento europeo.',
            'Vantaggio fiscale: nessuna imposta sul reddito per piccole imprese < 14 milioni ALL (~140.000 EUR).',
        ],
    },

    'al': {
        'titolo': 'Rregullativa per hapjen e lavanderisë vetë-shërbim në Shqipëri',
        'sezioni': [
            {
                'id': 'piva',
                'titolo': '1. Regjistrimi i shoqërisë / NIPT',
                'colore': '#3b82f6',
                'icona': 'SH',
                'voci': [
                    ('SHPK (Shoqëri me Përgjegjësi të Kufizuar)', 'Forma juridike e rekomanduar. Kapital minimal: 100 ALL. Procedim: 1-3 ditë pune.'),
                    ('Regjistrim QKB', 'Qendra Kombëtare e Biznesit. Disponibël online në qkb.gov.al. Tarifa: falas ose minimale.'),
                    ('NIPT', 'Numri i Identifikimit të Personit Tatimor — lëshohet automatikisht me regjistrimin QKB.'),
                    ('Kodi NACE 9601', '"Larje dhe pastrimi i artikujve tekstilë dhe gëzofit" — të deklarohet në QKB.'),
                    ('Llogari bankare e shoqërisë', 'E detyrueshme. Bankat kryesore: Raiffeisen, BKT, Credins, OTP Bank.'),
                    ('Regjistrim DPT', 'Drejtoria e Përgjithshme e Tatimeve — brenda 15 ditëve nga fillimi i veprimtarisë.'),
                ],
            },
            {
                'id': 'autorizzazioni',
                'titolo': '2. Lejet komunale dhe sanitare',
                'colore': '#f59e0b',
                'icona': 'AU',
                'voci': [
                    ('Leje ushtrimi veprimtarie', 'Lëshuar nga Bashkia kompetente. E nevojshme për çdo veprimtari tregtare me publikun.'),
                    ('Certifikatë përdorimi', 'Verifikohet pajtueshmëria strukturore dhe destinimi i lokalit.'),
                    ('Autorizim sanitar', 'Nga ISHP (Instituti i Shëndetit Publik). I detyrueshëm. Inspektim në vend.'),
                    ('Autorizim mjedisor', 'Nga AKM (Agjencia Kombëtare e Mjedisit). Për lavanderi: procedurë e thjeshtëzuar Kategoria C.'),
                    ('Plan emergjence', 'Plan evakuimi i miratuar nga Drejtoria e Zjarrfikësve lokale.'),
                ],
            },
            {
                'id': 'antincendio',
                'titolo': '3. Normat e mbrojtjes nga zjarri',
                'colore': '#ef4444',
                'icona': 'ZJ',
                'voci': [
                    ('Projekt mbrojtje nga zjarri', 'Dokumentacion teknik i detyrueshëm, nënshkruar nga inxhinier i licencuar.'),
                    ('Leje mbrojtje nga zjarri', 'Nga Drejtoria e Përgjithshme e Zjarrfikësve. E detyrueshme para hapjes. Kohëzgjatja: 15-30 ditë.'),
                    ('Pajisje minimale', 'Shingëzues ABC çdo 150 m2, sinjalistikë rrugësh largimi, sensorë tymi, plan evakuimi i ekspozuar.'),
                    ('Inspektim periodik', 'Inspektim vjetor i strukturës anti-zjarr.'),
                ],
            },
            {
                'id': 'reflui',
                'titolo': '4. Trajtimi i ujërave të ndotura',
                'colore': '#10b981',
                'icona': 'UJ',
                'voci': [
                    ('Leje lidhje kanalizim', 'Lëshuar nga operatori lokal (UKT Tiranë etj.). E detyrueshme.'),
                    ('Separator dhjamrash', 'I detyrueshëm para shkarkimit në kanalizim. Dimensionuar sipas numrit të makinerive.'),
                    ('Kontratë heqje mbetjesh', 'Me operator të autorizuar komunal për mbetjet e ngurta.'),
                    ('Analiza ujërave', 'Për > 5 makina: analiza periodike të kërkuara nga Inspektorati i Mjedisit.'),
                    ('Konformitet VKM 177/2005', 'Ujërat e shkarkuara duhet të respektojnë normativën e cilësisë për kanalizim publik.'),
                ],
            },
            {
                'id': 'imposte',
                'titolo': '5. Taksat dhe detyrimet fiskale',
                'colore': '#8b5cf6',
                'icona': 'TA',
                'voci': [
                    ('Tatimi mbi fitimin: 15%', 'Normë standarde. Ndërmarrjet e vogla (qarkullim < 14 mln ALL): tatim i thjeshtëzuar 0%.'),
                    ('TVSH: 20%', 'Regjistrim TVSH i detyrueshem mbi 10 mln ALL/vit. Deklaratë mujore.'),
                    ('Tatimi mbi dividendët: 8%', 'Mbajtur në burim gjatë shpërndarjes.'),
                    ('Taksa vendore', 'Variabël sipas bashkisë. Tiranë: ~15.000-50.000 ALL/vit.'),
                ],
            },
            {
                'id': 'dipendenti',
                'titolo': '6. Kontributet e punonjësve (nëse ka)',
                'colore': '#06b6d4',
                'icona': 'PU',
                'voci': [
                    ('Paga minimale 2024: 40.000 ALL/muaj', 'Paga minimale kombëtare (~406 EUR/muaj). Lavanderitë self-service shpesh funksionojnë pa staf fiks.'),
                    ('Sigurime shoqërore punëdhënës: 9,5%', 'Kontribut pensioni nga punëdhënësi.'),
                    ('Sigurime shëndetësore: 1,7%', 'Kontribut shëndetësor nga punëdhënësi.'),
                    ('Tatimi mbi të ardhurat: 0-23%', '0% deri 30.000 ALL/muaj, 13% deri 150.000, 23% mbi.'),
                    ('Regjistrim kontrate', 'Çdo kontratë pune të regjistrohet pranë Inspektoratit të Punës brenda 24 orëve.'),
                    ('Vizitë mjekësore', 'E detyrueshme para fillimit të punës.'),
                ],
            },
        ],
        'note_finali': [
            'Shqipëria ka thjeshtëzuar procedurat me platformën e-albania.al (sporteli unik dixhital).',
            'Koha mesatare për të gjitha lejet: 30-60 ditë.',
            'Asnjë taksë mbi fitimin për ndërmarrjet me qarkullim nën 14 milionë ALL (~140.000 EUR).',
            'Shqipëria është në proces anëtarësimi në BE: normat po harmonizohen gradualisht.',
        ],
    },
}
