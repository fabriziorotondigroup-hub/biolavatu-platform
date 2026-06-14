"""
services/normativa_polonia.py — BIOLavaTU LaundryPro
Normativa apertura lavanderia self-service in Polonia.
Bilingue IT/PL. ISOLATO.
"""

NORMATIVA_PL = {
    'it': {
        'titolo': 'Normativa apertura lavanderia self-service in Polonia',
        'sezioni': [
            {
                'id': 'piva',
                'titolo': '1. Costituzione società / NIP fiscale',
                'colore': '#3b82f6',
                'icona': 'SP',
                'voci': [
                    ('Sp. z o.o. (Spółka z ograniczoną odpowiedzialnością)', 'Equivalente alla Srl italiana. Capitale minimo: 5.000 PLN (~1.170 EUR). Forma più comune per lavanderie.'),
                    ('Registrazione KRS', 'Krajowy Rejestr Sądowy — Registro Nazionale Giudiziario. Procedura online su portal.s24.gov.pl. Tempi: 1-3 giorni lavorativi.'),
                    ('NIP (Numer Identyfikacji Podatkowej)', 'Codice fiscale aziendale — equivalente alla P.IVA italiana. Assegnato automaticamente alla registrazione.'),
                    ('REGON', 'Numero identificativo statistico — obbligatorio. Rilasciato dall\'Ufficio Centrale di Statistica (GUS) contestualmente al NIP.'),
                    ('Conto bancario aziendale', 'Obbligatorio. Principali banche: PKO BP, Pekao, mBank, ING Bank Śląski, Santander Bank Polska.'),
                    ('Registrazione US (Urząd Skarbowy)', 'Ufficio delle Imposte competente — entro 7 giorni dall\'avvio attività. Necessario per dichiarazioni IVA.'),
                ],
            },
            {
                'id': 'autorizzazioni',
                'titolo': '2. Permessi e autorizzazioni locali',
                'colore': '#f59e0b',
                'icona': 'PZ',
                'voci': [
                    ('Zezwolenie na użytkowanie lokalu', 'Permesso di utilizzo del locale commerciale. Rilasciato dal Powiat (Distretto) o Gmina (Comune) competente.'),
                    ('Decyzja o warunkach zabudowy', 'Decisione sulle condizioni di edificazione/uso — verifica compatibilità con piano urbanistico locale (MPZP).'),
                    ('Pozwolenie na budowę / zgłoszenie', 'Per lavori strutturali o cambio destinazione d\'uso: permesso edilizio o semplice notifica secondo entità lavori.'),
                    ('Decyzja Sanepid', 'Autorizzazione sanitaria della Stacja Sanitarno-Epidemiologiczna (Sanepid). Obbligatoria per attività a contatto con biancheria.'),
                    ('Zgłoszenie do BDO', 'Registrazione nel Database sulla gestione rifiuti — obbligatoria per qualsiasi attività che produce rifiuti.'),
                    ('RODO compliance', 'Adeguamento al GDPR (in Polonia: RODO). Nomina DPO se necessario, registro trattamenti, privacy policy esposta.'),
                ],
            },
            {
                'id': 'antincendio',
                'titolo': '3. Sicurezza antincendio (PSP)',
                'colore': '#ef4444',
                'icona': 'PP',
                'voci': [
                    ('Projekt ochrony przeciwpożarowej', 'Progetto tecnico antincendio obbligatorio per locali > 200 mq o con macchinari ad alta potenza. Firmato da tecnico abilitato.'),
                    ('Odbiór PSP', 'Collaudo antincendio della Państwowa Straż Pożarna (Vigili del Fuoco statali). Obbligatorio prima dell\'apertura.'),
                    ('Gaśnice i oznakowanie', 'Estintori polvere ABC ogni 200 mq, segnaletica vie di uscita, rilevatori fumo, planimetria evacuazione esposta.'),
                    ('Instrukcja bezpieczeństwa pożarowego', 'Istruzione di sicurezza antincendio — obbligatoria per locali > 200 mq o > 50 persone contemporanee.'),
                    ('Przegląd roczny', 'Revisione annuale di estintori e impianti rilevazione. Documentazione da conservare per 5 anni.'),
                ],
            },
            {
                'id': 'reflui',
                'titolo': '4. Scarichi idrici e rifiuti',
                'colore': '#10b981',
                'icona': 'WO',
                'voci': [
                    ('Umowa na odprowadzanie ścieków', 'Contratto scarico acque reflue con gestore locale (np. MPWiK, ZWiK). Obbligatorio prima dell\'avvio.'),
                    ('Separator substancji ropopochodnych', 'Separatore di sostanze inquinanti (grassi, detersivi) obbligatorio a monte dello scarico. Dimensionato per portata macchine.'),
                    ('Pozwolenie wodnoprawne', 'Autorizzazione idrica: obbligatoria se lo scarico supera soglie definite dal Prawo Wodne (Legge sulle Acque, 2017).'),
                    ('Umowa na odbiór odpadów', 'Contratto raccolta rifiuti solidi con operatore autorizzato. Obbligatorio; rifiuti classificati sotto codice 20 03 01.'),
                    ('Ewidencja odpadów', 'Registro rifiuti obbligatorio nel sistema BDO (Baza Danych Odpadowych). Aggiornamento mensile.'),
                ],
            },
            {
                'id': 'imposte',
                'titolo': '5. Imposte e tasse',
                'colore': '#8b5cf6',
                'icona': 'PO',
                'voci': [
                    ('CIT (podatek dochodowy od osób prawnych): 9-19%', 'Aliquota standard 19%. Piccole imprese (fatturato < 2 mln EUR): 9%. Dichiarazione annuale CIT-8.'),
                    ('VAT (podatek od towarów i usług): 23%', 'Aliquota standard. Registrazione VAT obbligatoria sopra 200.000 PLN/anno (~46.700 EUR). Dichiarazione mensile JPK_V7M.'),
                    ('Podatek od dywidend: 19%', 'Ritenuta alla fonte sui dividendi distribuiti ai soci. Aliquota 19%.'),
                    ('Podatek od nieruchomości', 'Imposta comunale sugli immobili: variabile per Gmina, mediamente 20-30 PLN/mq/anno per locali commerciali.'),
                    ('ZUS przedsiębiorcy', 'Contributi previdenziali del titolare: ~1.600-2.000 PLN/mese (forfettari). Versamento mensile all\'ZUS.'),
                    ('Opłata za korzystanie ze środowiska', 'Canone utilizzo ambiente per scarichi idrici e consumo risorse. Dichiarazione semestrale all\'Urząd Marszałkowski.'),
                ],
            },
            {
                'id': 'dipendenti',
                'titolo': '6. Contributi dipendenti (se presenti)',
                'colore': '#06b6d4',
                'icona': 'PR',
                'voci': [
                    ('Płaca minimalna 2024: 4.242 PLN/mese', 'Salario minimo nazionale (~990 EUR/mese). Aumentato a 4.300 PLN da luglio 2024. Lavanderie self-service spesso senza personale fisso.'),
                    ('ZUS emerytalne (pensione): 9,76% + 9,76%', 'Contributo pensione: 9,76% a carico datore + 9,76% a carico dipendente (trattenuto dal datore).'),
                    ('ZUS rentowe (invalidità): 6,5% + 1,5%', 'Contributo invalidità: 6,5% datore + 1,5% dipendente.'),
                    ('ZUS chorobowe (malattia): 2,45%', 'Solo a carico del dipendente. Versato dal datore all\'ZUS.'),
                    ('ZUS wypadkowe (infortuni): 1,67%', 'Solo a carico del datore. Aliquota variabile per settore (1,67% base).'),
                    ('Podatek dochodowy lavoratore: 12-32%', 'Aliquota 12% fino a 120.000 PLN/anno, 32% oltre. Trattenuta mensile dal datore (zaliczka).'),
                    ('Zgłoszenie do ZUS i US', 'Ogni lavoratore va iscritto all\'ZUS entro 7 giorni dall\'inizio rapporto e al Fondo Pensione (OFE o IKE).'),
                ],
            },
        ],
        'note_finali': [
            'La Polonia è nell\'UE: normative allineate agli standard europei (GDPR, direttive ambientali).',
            'Tempi medi per ottenere tutte le autorizzazioni: 30-60 giorni.',
            'Il portale biznes.gov.pl offre uno sportello unico digitale per molte pratiche.',
            'Vantaggio fiscale: CIT al 9% per fatturati sotto 2 milioni EUR/anno (fino a 2 mln EUR).',
            'La Polonia è uno dei mercati self-service più sviluppati in Europa dell\'Est — forte cultura della lavanderia a gettone.',
        ],
    },

    'pl': {
        'titolo': 'Przepisy dotyczące otwarcia samoobsługowej pralni w Polsce',
        'sezioni': [
            {
                'id': 'piva',
                'titolo': '1. Rejestracja spółki / NIP',
                'colore': '#3b82f6',
                'icona': 'SP',
                'voci': [
                    ('Sp. z o.o.', 'Najpopularniejsza forma prawna. Minimalny kapitał zakładowy: 5.000 PLN. Rejestracja przez portal S24.'),
                    ('Wpis do KRS', 'Krajowy Rejestr Sądowy. Online na portal.s24.gov.pl. Czas: 1-3 dni robocze.'),
                    ('NIP', 'Numer Identyfikacji Podatkowej — przyznawany automatycznie przy rejestracji.'),
                    ('REGON', 'Numer statystyczny — obowiązkowy. Nadawany przez GUS łącznie z NIP.'),
                    ('Firmowe konto bankowe', 'Obowiązkowe. Główne banki: PKO BP, Pekao, mBank, ING, Santander.'),
                    ('Rejestracja w US', 'Urząd Skarbowy właściwy miejscowo — w ciągu 7 dni od rozpoczęcia działalności.'),
                ],
            },
            {
                'id': 'autorizzazioni',
                'titolo': '2. Zezwolenia i pozwolenia',
                'colore': '#f59e0b',
                'icona': 'PZ',
                'voci': [
                    ('Zezwolenie na użytkowanie lokalu', 'Wydawane przez właściwy Powiat lub Gminę dla lokalu użytkowego.'),
                    ('Warunki zabudowy / MPZP', 'Weryfikacja zgodności z miejscowym planem zagospodarowania przestrzennego.'),
                    ('Pozwolenie na budowę / zgłoszenie', 'Dla prac budowlanych lub zmiany sposobu użytkowania lokalu.'),
                    ('Decyzja Sanepid', 'Stacja Sanitarno-Epidemiologiczna — obowiązkowa dla pralni. Inspekcja na miejscu.'),
                    ('Rejestracja w BDO', 'Baza Danych Odpadowych — obowiązkowa dla każdej firmy wytwarzającej odpady.'),
                    ('Zgodność z RODO', 'Obowiązek informacyjny, rejestr przetwarzania danych, polityka prywatności.'),
                ],
            },
            {
                'id': 'antincendio',
                'titolo': '3. Bezpieczeństwo pożarowe (PSP)',
                'colore': '#ef4444',
                'icona': 'PP',
                'voci': [
                    ('Projekt ochrony ppoż.', 'Obowiązkowy dla lokali >200 m2 lub z urządzeniami dużej mocy. Podpisany przez uprawnionego rzeczoznawcę.'),
                    ('Odbiór przez PSP', 'Państwowa Straż Pożarna — obowiązkowy odbiór przed otwarciem. Czas: 14-30 dni.'),
                    ('Wyposażenie ppoż.', 'Gaśnice ABC co 200 m2, oznakowanie dróg ewakuacyjnych, czujniki dymu, plan ewakuacji.'),
                    ('Instrukcja bezpieczeństwa pożarowego', 'Obowiązkowa dla lokali >200 m2 lub >50 osób jednocześnie.'),
                    ('Przegląd roczny', 'Coroczny przegląd gaśnic i instalacji detekcji pożaru.'),
                ],
            },
            {
                'id': 'reflui',
                'titolo': '4. Gospodarka wodno-ściekowa',
                'colore': '#10b981',
                'icona': 'WO',
                'voci': [
                    ('Umowa na odprowadzanie ścieków', 'Z lokalnym operatorem (MPWiK, ZWiK itp.). Obowiązkowa przed uruchomieniem.'),
                    ('Separator substancji', 'Separator tłuszczu i detergentów przed odprowadzeniem ścieków. Wymiarowany wg liczby maszyn.'),
                    ('Pozwolenie wodnoprawne', 'Obowiązkowe przy przekroczeniu progów określonych w Prawie Wodnym z 2017 r.'),
                    ('Umowa na odbiór odpadów', 'Z uprawnionym podmiotem. Odpady pod kodem 20 03 01.'),
                    ('Ewidencja odpadów w BDO', 'Miesięczna aktualizacja w systemie BDO.'),
                ],
            },
            {
                'id': 'imposte',
                'titolo': '5. Podatki i opłaty',
                'colore': '#8b5cf6',
                'icona': 'PO',
                'voci': [
                    ('CIT: 9% lub 19%', 'Stawka podstawowa 19%. Mali podatnicy (przychody < 2 mln EUR): 9%. Deklaracja roczna CIT-8.'),
                    ('VAT: 23%', 'Rejestracja VAT obowiązkowa powyżej 200.000 PLN/rok. Miesięczna deklaracja JPK_V7M.'),
                    ('Podatek od dywidend: 19%', 'Pobierany u źródła przy wypłacie dywidendy.'),
                    ('Podatek od nieruchomości', 'Lokalny, średnio 20-30 PLN/m2/rok dla lokali użytkowych.'),
                    ('Składki ZUS przedsiębiorcy', '~1.600-2.000 PLN/mies. (ryczałtowe). Płatne co miesiąc do ZUS.'),
                ],
            },
            {
                'id': 'dipendenti',
                'titolo': '6. Składki pracownicze (jeśli dotyczy)',
                'colore': '#06b6d4',
                'icona': 'PR',
                'voci': [
                    ('Płaca minimalna 2024: 4.242 PLN/mies.', 'Minimalne wynagrodzenie krajowe (~990 EUR). Od lipca 2024: 4.300 PLN. Pralnie self-service często bez stałego personelu.'),
                    ('ZUS emerytalne: 9,76% + 9,76%', 'Po stronie pracodawcy i pracownika (potrącane przez pracodawcę).'),
                    ('ZUS rentowe: 6,5% + 1,5%', 'Renta inwalidzka — pracodawca 6,5%, pracownik 1,5%.'),
                    ('ZUS chorobowe: 2,45%', 'Wyłącznie po stronie pracownika.'),
                    ('ZUS wypadkowe: 1,67%', 'Wyłącznie po stronie pracodawcy.'),
                    ('Podatek dochodowy pracownika: 12-32%', 'Zaliczka miesięczna potrącana przez pracodawcę.'),
                    ('Zgłoszenie do ZUS', 'Pracownika należy zgłosić do ZUS w ciągu 7 dni od podjęcia pracy.'),
                ],
            },
        ],
        'note_finali': [
            'Polska jest w UE: przepisy zgodne ze standardami europejskimi (RODO, dyrektywy środowiskowe).',
            'Średni czas uzyskania wszystkich zezwoleń: 30-60 dni.',
            'Portal biznes.gov.pl oferuje jedno okienko dla wielu formalności.',
            'Polska jest jednym z najbardziej rozwiniętych rynków pralni samoobsługowych w Europie Wschodniej.',
        ],
    },
}
