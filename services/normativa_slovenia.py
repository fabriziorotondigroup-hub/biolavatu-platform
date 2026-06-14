"""
services/normativa_slovenia.py — BIOLavaTU LaundryPro
Normativa apertura lavanderia self-service in Slovenia. Bilingue IT/SL. ISOLATO.
"""
NORMATIVA_SI = {
    'it': {
        'titolo': 'Normativa apertura lavanderia self-service in Slovenia',
        'sezioni': [
            {'id':'piva','titolo':'1. Costituzione società / davčna številka','colore':'#3b82f6','icona':'DO',
             'voci':[
                ('d.o.o. (Družba z omejeno odgovornostjo)','Equivalente alla Srl italiana. Capitale minimo: 7.500 EUR. Tra le più alte dell\'area ex-Jugoslavia.'),
                ('Registrazione AJPES','Agenzia della Repubblica di Slovenia per i Registri Pubblici. Online su e-vem.gov.si. Tempi: 1-3 giorni.'),
                ('Davčna številka','Numero fiscale aziendale — assegnato automaticamente dall\'AJPES alla registrazione.'),
                ('SKD 9601','Codice attività: "Pranje in kemično čiščenje tekstilnih in krznih izdelkov". Da dichiarare.'),
                ('Conto bancario aziendale','Obbligatorio. Principali banche: NLB, Nova KBM, Abanka, SKB (Société Générale).'),
                ('Registrazione FURS','Finančna uprava RS (Agenzia delle Entrate slovena) — entro 8 giorni dall\'avvio per DDV (IVA).'),
             ]},
            {'id':'autorizzazioni','titolo':'2. Autorizzazioni comunali e sanitarie','colore':'#f59e0b','icona':'DO',
             'voci':[
                ('Odločba o ustreznosti poslovnega prostora','Delibera idoneità locale commerciale — rilasciata dall\'Upravna enota (Unità Amministrativa) competente.'),
                ('Uporabno dovoljenje','Certificato di agibilità — verifica conformità strutturale e destinazione d\'uso.'),
                ('Sanitarno soglasje NIJZ','Autorizzazione sanitaria del NIJZ (Istituto Nazionale Sanità Pubblica). Obbligatoria per praone.'),
                ('Okoljsko dovoljenje ARSO','Valutazione ambientale dell\'ARSO (Agenzia Ambiente Slovenia) per scarichi idrici.'),
                ('ZVOP-2 compliance','Adeguamento Legge Protezione Dati Personali (ZVOP-2, 2022) — equivalente GDPR.'),
             ]},
            {'id':'antincendio','titolo':'3. Sicurezza antincendio','colore':'#ef4444','icona':'PO',
             'voci':[
                ('Elaborat varstva pred požarom','Studio antincendio obbligatorio per locali > 200 mq. Firmato da incaricato abilitato.'),
                ('Soglasje Uprave RS za zaščito in reševanje','Approvazione dell\'Amministrazione per la Protezione Civile e i Soccorsi. Obbligatoria.'),
                ('Gasilni aparati in oznake','Estintori ABC ogni 200 mq, segnaletica uscite, rilevatori fumo, piano evacuazione.'),
                ('Letni pregled','Revisione annuale estintori e impianti rilevazione incendi.'),
             ]},
            {'id':'reflui','titolo':'4. Scarichi idrici e rifiuti','colore':'#10b981','icona':'VO',
             'voci':[
                ('Pogodba o odvajanju odpadnih voda','Contratto scarico acque reflue con gestore locale (comunità idriche locali, jp Vodovod).'),
                ('Lovilec maščob','Separatore grassi e detersivi — obbligatorio per praone a monte dello scarico.'),
                ('Vodno dovoljenje','Autorizzazione idrica ARSO se scarico supera soglie di legge.'),
                ('Pogodba o odvažanju odpadkov','Contratto raccolta rifiuti con operatore autorizzato. Obbligatorio.'),
             ]},
            {'id':'imposte','titolo':'5. Imposte e tasse','colore':'#8b5cf6','icona':'PO',
             'voci':[
                ('DDPO (davek od dohodkov pravnih oseb): 19%','Imposta sul reddito delle società: aliquota flat 19%. Dichiarazione annuale.'),
                ('DDV (IVA): 22%','Aliquota standard. Registrazione obbligatoria sopra 50.000 EUR/anno. Dichiarazione mensile.'),
                ('Davek na dividende: 25%','Ritenuta alla fonte sui dividendi. Aliquota 25%.'),
                ('Nadomestilo za uporabo stavbnega zemljišča','Tassa comunale sugli immobili commerciali. Variabile per Občina.'),
                ('Prispevek za ZPIZ in ZZZS','Contributi previdenziali e sanitari anche per titolari/soci attivi nell\'impresa.'),
             ]},
            {'id':'dipendenti','titolo':'6. Contributi dipendenti (se presenti)','colore':'#06b6d4','icona':'ZA',
             'voci':[
                ('Minimalna plača 2024: 1.253,90 EUR/mese','Tra i salari minimi più alti dell\'Europa dell\'Est. Spesso non necessario personale fisso.'),
                ('PIZ (pensione): 8,85% datore + 15,5% dipendente','Contributi pensionistici versati all\'ZPIZ.'),
                ('ZZ (sanità): 6,56% datore + 6,36% dipendente','Contributi sanitari versati all\'ZZZS.'),
                ('Brezposelnost: 0,06% + 0,14%','Contributo disoccupazione — molto basso in Slovenia.'),
                ('Dohodnina (IRE): 16-50%','Aliquote progressive. Datore trattiene e versa mensilmente al FURS.'),
                ('Prijava pri ZPIZ in ZZZS','Iscrizione obbligatoria entro 8 giorni dall\'inizio del rapporto.'),
             ]},
        ],
        'note_finali':[
            'La Slovenia è nell\'UE dal 2004 e nell\'Eurozona dal 2007 — mercato stabile.',
            'Tempi medi per tutte le autorizzazioni: 20-45 giorni (tra i più rapidi della regione).',
            'Il portale e-VEM (e-Vstopna točka za podjetnike) semplifica moltissime pratiche.',
            'Salario minimo alto (1.253 EUR) — conviene puntare su piena automazione senza personale.',
            'DDV 22%: inferiore a Croazia (25%) e più vicino alla media UE.',
        ],
    },
    'sl': {
        'titolo': 'Predpisi za odprtje samopostrežne pralnice v Sloveniji',
        'sezioni': [
            {'id':'piva','titolo':'1. Ustanovitev podjetja / davčna številka','colore':'#3b82f6','icona':'DO',
             'voci':[
                ('d.o.o.','Priporočena pravna oblika. Minimalni osnovni kapital: 7.500 EUR. Registracija prek e-VEM.'),
                ('Registracija AJPES','Agencija RS za javnopravne evidence. Online registracija v 1-3 dneh.'),
                ('Davčna številka','Samodejno dodeljena pri registraciji.'),
                ('SKD 9601','"Pranje in kemično čiščenje tekstilnih in krznih izdelkov" — obvezno prijaviti.'),
                ('Poslovni bančni račun','Obvezen. Priporočene banke: NLB, Nova KBM, Abanka, SKB.'),
                ('Registracija pri FURS','Finančna uprava RS — v 8 dneh od začetka poslovanja za DDV.'),
             ]},
            {'id':'autorizzazioni','titolo':'2. Dovoljenja in soglasja','colore':'#f59e0b','icona':'DO',
             'voci':[
                ('Odločba o ustreznosti prostora','Izda pristojna Upravna enota.'),
                ('Uporabno dovoljenje','Potrdilo o skladnosti poslovnega prostora.'),
                ('Sanitarno soglasje NIJZ','Obvezno za pralnice perila. Inšpekcija na kraju samem.'),
                ('Okoljsko dovoljenje ARSO','Za dejavnosti z odvajanjem odpadnih voda.'),
                ('ZVOP-2 skladnost','Zakon o varstvu osebnih podatkov — enakovredno GDPR.'),
             ]},
            {'id':'antincendio','titolo':'3. Varstvo pred požarom','colore':'#ef4444','icona':'PO',
             'voci':[
                ('Elaborat VPP','Obvezen za prostore >200 m2. Podpiše pooblaščeni strokovnjak.'),
                ('Soglasje UZRS','Uprava RS za zaščito in reševanje. Obvezno pred odprtjem.'),
                ('Gasilna oprema','Aparati ABC na vsakih 200 m2, oznake izhodov, detektorji dima, načrt evakuacije.'),
                ('Letni pregled','Letni pregled aparatov in naprav.'),
             ]},
            {'id':'reflui','titolo':'4. Odpadne vode in odpadki','colore':'#10b981','icona':'VO',
             'voci':[
                ('Pogodba o odvajanju vode','Z lokalnim upravljavcem (npr. JP Vodovod-Kanalizacija).'),
                ('Lovilec maščob','Obvezen pred priključkom na kanalizacijo.'),
                ('Vodno dovoljenje','Zahtevano, če odvajanje presega zakonske mejne vrednosti (ARSO).'),
                ('Pogodba o odvozu odpadkov','Z pooblaščenim zbiralcem komunalnih odpadkov.'),
             ]},
            {'id':'imposte','titolo':'5. Davki in prispevki','colore':'#8b5cf6','icona':'PO',
             'voci':[
                ('DDPO: 19%','Davek od dohodkov pravnih oseb. Letna napoved.'),
                ('DDV: 22%','Obvezna registracija nad 50.000 EUR/leto. Mesečna oddaja.'),
                ('Davek na dividende: 25%','Odtegljaj pri izplačilu dividend.'),
                ('Nadomestilo NUSZ','Lokalna taksa za poslovne prostore — variabilna po Občini.'),
             ]},
            {'id':'dipendenti','titolo':'6. Prispevki za zaposlene (če je)','colore':'#06b6d4','icona':'ZA',
             'voci':[
                ('Minimalna plača 2024: 1.253,90 EUR/mes.','Med najvišjimi v vzhodni Evropi. Samopostrežne pralnice pogosto delujejo brez stalnega osebja.'),
                ('PIZ: 8,85% delodajalec + 15,5% delavec','Pokojninski prispevki ZPIZ.'),
                ('ZZ: 6,56% delodajalec + 6,36% delavec','Zdravstveni prispevki ZZZS.'),
                ('Brezposelnost: 0,06% + 0,14%','Zelo nizek prispevek za primer brezposelnosti.'),
                ('Dohodnina: 16-50%','Progresivna lestvica. Delodajalec mesečno odteguje akontacijo.'),
                ('Prijava ZPIZ/ZZZS','V roku 8 dni od nastopa dela.'),
             ]},
        ],
        'note_finali':[
            'Slovenija je v EU od 2004 in v evroobmočju od 2007 — stabilen trg.',
            'Povprečni čas za vse dovoljenja: 20-45 dni.',
            'Portal e-VEM (e-Vstopna točka za podjetnike) poenostavlja večino postopkov.',
            'Visoka minimalna plača — priporoča se popolna avtomatizacija brez stalnega osebja.',
        ],
    },
}
