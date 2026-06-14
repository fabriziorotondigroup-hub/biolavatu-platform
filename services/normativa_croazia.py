"""
services/normativa_croazia.py — BIOLavaTU LaundryPro
Normativa apertura lavanderia self-service in Croazia. Bilingue IT/HR. ISOLATO.
"""
NORMATIVA_HR = {
    'it': {
        'titolo': 'Normativa apertura lavanderia self-service in Croazia',
        'sezioni': [
            {'id':'piva','titolo':'1. Costituzione società / OIB fiscale','colore':'#3b82f6','icona':'DR',
             'voci':[
                ('d.o.o. (Društvo s ograničenom odgovornošću)','Equivalente alla Srl italiana. Capitale minimo: 2.500 EUR. Registrazione online su e-tvrtka.hr.'),
                ('Registrazione Sudski registar','Registro Commerciale Tribunale. Tempi: 3-5 giorni. Possibile via notaio o HITRO.HR.'),
                ('OIB (Osobni identifikacijski broj)','Codice fiscale aziendale — equivalente alla P.IVA. Assegnato automaticamente.'),
                ('NKD 9601','Codice attività: "Pranje i kemijsko čišćenje tekstilnih i krznenih proizvoda". Da dichiarare al registro.'),
                ('Conto bancario aziendale','Obbligatorio. Principali banche: Erste Bank, Zagrebačka banka (UniCredit), Privredna banka (Intesa).'),
                ('Registrazione Porezna uprava','Amministrazione Fiscale — entro 8 giorni dall\'avvio. Necessario per PDV (IVA).'),
             ]},
            {'id':'autorizzazioni','titolo':'2. Autorizzazioni e licenze','colore':'#f59e0b','icona':'DO',
             'voci':[
                ('Rješenje o početku obavljanja djelatnosti','Delibera di avvio attività — rilasciata dall\'Ured za gospodarstvo (Ufficio Economia) del Grad/Općina.'),
                ('Uporabna dozvola','Certificato di agibilità del locale. Verifica conformità strutturale e destinazione d\'uso commerciale.'),
                ('Sanitarna suglasnost','Autorizzazione sanitaria dell\'Hrvatska agencija za hranu o istituto locale. Obbligatoria.'),
                ('Rješenje o zaštiti okoliša','Valutazione ambientale per attività con scarichi idrici significativi.'),
                ('Zakon o zaštiti osobnih podataka','Adeguamento GDPR (in Croazia: ZZOP). Registro trattamenti, privacy policy esposta.'),
             ]},
            {'id':'antincendio','titolo':'3. Sicurezza antincendio (ZOP)','colore':'#ef4444','icona':'ZP',
             'voci':[
                ('Elaborat zaštite od požara','Studio antincendio obbligatorio per locali > 200 mq. Firmato da ingegnere antincendio abilitato.'),
                ('Suglasnost Vatrogasne zajednice','Approvazione dei Vigili del Fuoco prima dell\'apertura. Tempi: 15-30 giorni.'),
                ('Vatrogasni aparati i oznake','Estintori ABC ogni 200 mq, segnaletica uscite di emergenza, rilevatori fumo, piano evacuazione.'),
                ('Godišnji pregled','Revisione annuale estintori e impianti. Documentazione obbligatoria.'),
             ]},
            {'id':'reflui','titolo':'4. Scarichi idrici','colore':'#10b981','icona':'VO',
             'voci':[
                ('Ugovor o odvodnji otpadnih voda','Contratto scarico acque reflue con gestore locale (Vodoopskrba i odvodnja, Hrvatske vode).'),
                ('Separator masti i deterdženata','Separatore grassi/detersivi obbligatorio a monte dello scarico.'),
                ('Vodopravna dozvola','Autorizzazione idrica se scarico supera soglie definite dalla Zakon o vodama.'),
                ('Ugovor o odvoženju otpada','Contratto raccolta rifiuti solidi con operatore autorizzato comunale.'),
             ]},
            {'id':'imposte','titolo':'5. Imposte e tasse','colore':'#8b5cf6','icona':'PO',
             'voci':[
                ('Porez na dobit: 10-18%','Aliquota 10% per redditi fino a 1 milione EUR/anno; 18% oltre. Dichiarazione annuale.'),
                ('PDV (IVA): 25%','Aliquota standard. Registrazione obbligatoria sopra 40.000 EUR/anno. Dichiarazione mensile.'),
                ('Porez na dividende: 12%','Ritenuta sui dividendi distribuiti. Aliquota 12% + prirez comunale.'),
                ('Prirez porezu na dohodak','Sovrimposta comunale: 0-18% (Zagreb 18%, altre città meno). Si applica su imposte sui redditi.'),
                ('Komunalna naknada','Tassa comunale servizi: variabile per Grad/Općina. Calcolata su superficie locale commerciale.'),
             ]},
            {'id':'dipendenti','titolo':'6. Contributi dipendenti (se presenti)','colore':'#06b6d4','icona':'ZA',
             'voci':[
                ('Minimalna plaća 2024: 840 EUR/mese','Salario minimo nazionale. Lavanderie self-service spesso senza personale fisso.'),
                ('MIO I. stup (pensione): 15%','Primo pilastro pensionistico — a carico del datore.'),
                ('MIO II. stup (pensione cap.): 5%','Secondo pilastro capitalizzazione — a carico del datore.'),
                ('Zdravstveno osiguranje: 16,5%','Assicurazione sanitaria — a carico del datore.'),
                ('Porez na dohodak radnika: 20-30%','Imposta reddito lavoratore: 20% fino a 50.400 EUR/anno, 30% oltre.'),
                ('Prijava u HZMO i HZZO','Iscrizione obbligatoria al Fondo Pensione (HZMO) e Fondo Sanitario (HZZO) entro 8 giorni.'),
             ]},
        ],
        'note_finali':[
            'La Croazia è nell\'UE dal 2013 e nell\'Eurozona dal gennaio 2023 — nessun rischio cambio.',
            'Tempi medi per tutte le autorizzazioni: 30-60 giorni.',
            'Il portale e-Građani e HITRO.HR semplificano molte pratiche online.',
            'Il turismo stagionale può fortemente aumentare il fatturato in zone costiere (maggio-settembre).',
            'IVA al 25% tra le più alte d\'Europa — attenzione al pricing.',
        ],
    },
    'hr': {
        'titolo': 'Propisi za otvaranje samoposlužne praone rublja u Hrvatskoj',
        'sezioni': [
            {'id':'piva','titolo':'1. Osnivanje društva / OIB','colore':'#3b82f6','icona':'DR',
             'voci':[
                ('d.o.o.','Preporučena pravna forma. Minimalni temeljni kapital: 2.500 EUR. Registracija putem e-tvrtka.hr.'),
                ('Sudski registar','Upis u sudski registar. Rok: 3-5 radnih dana. Moguće putem HITRO.HR.'),
                ('OIB','Osobni identifikacijski broj — dodjeljuje se automatski pri registraciji.'),
                ('NKD 9601','"Pranje i kemijsko čišćenje tekstilnih i krznenih proizvoda" — obvezno prijaviti.'),
                ('Poslovni bankovni račun','Obvezan. Preporučene banke: Erste, Zagrebačka banka, Privredna banka.'),
                ('Registracija Porezna uprava','U roku 8 dana od početka poslovanja za PDV i poreze.'),
             ]},
            {'id':'autorizzazioni','titolo':'2. Dozvole i rješenja','colore':'#f59e0b','icona':'DO',
             'voci':[
                ('Rješenje o obavljanju djelatnosti','Izdaje Ured za gospodarstvo nadležnog Grada/Općine.'),
                ('Uporabna dozvola','Potvrda o ispravnosti poslovnog prostora i namjeni korištenja.'),
                ('Sanitarna suglasnost','Obavezna za praone rublja. Inspekcija na licu mjesta.'),
                ('Zaštita okoliša','Za djelatnosti s ispuštanjem otpadnih voda.'),
             ]},
            {'id':'antincendio','titolo':'3. Zaštita od požara','colore':'#ef4444','icona':'ZP',
             'voci':[
                ('Elaborat zaštite od požara','Obvezan za poslovne prostore >200 m2. Potpisuje ovlašteni inženjer.'),
                ('Suglasnost vatrogasaca','Vatrogasna zajednica mora odobriti objekt prije otvaranja.'),
                ('Protupožarna oprema','Aparati ABC na svakih 200 m2, oznake izlaza, detektori dima, plan evakuacije.'),
                ('Godišnji pregled','Godišnja provjera aparata i instalacija.'),
             ]},
            {'id':'reflui','titolo':'4. Otpadne vode','colore':'#10b981','icona':'VO',
             'voci':[
                ('Ugovor o odvodnji','S lokalnim isporučiteljem vodnih usluga (npr. Vodoopskrba i odvodnja).'),
                ('Separator masti','Obvezan separator masti i deterdženata prije ispuštanja u kanalizaciju.'),
                ('Vodopravna dozvola','Potrebna ako ispuštanje premašuje propisane pragove prema Zakonu o vodama.'),
                ('Odvoz otpada','Ugovor s ovlaštenim sakupljačem komunalnog otpada.'),
             ]},
            {'id':'imposte','titolo':'5. Porezi i naknade','colore':'#8b5cf6','icona':'PO',
             'voci':[
                ('Porez na dobit: 10-18%','10% do 1 mil. EUR prihoda/god; 18% iznad. Godišnja prijava.'),
                ('PDV: 25%','Registracija obvezna iznad 40.000 EUR/god. Mjesečna prijava.'),
                ('Porez na dividende: 12%','Kod isplate dividende. Plus prirez prema sjedištu.'),
                ('Prirez','Gradski prirez: do 18% u Zagrebu. Niži u manjim gradovima.'),
                ('Komunalna naknada','Varijabilna po kvadraturi poslovnog prostora.'),
             ]},
            {'id':'dipendenti','titolo':'6. Doprinosi za zaposlenike (ako postoje)','colore':'#06b6d4','icona':'ZA',
             'voci':[
                ('Minimalna plaća 2024: 840 EUR/mjes.','Samoposlužne praone često rade bez stalnih zaposlenika.'),
                ('MIO I. stup: 15%','Na teret poslodavca.'),
                ('MIO II. stup: 5%','Na teret poslodavca.'),
                ('Zdravstveno: 16,5%','Na teret poslodavca.'),
                ('Porez na dohodak: 20-30%','Obustavlja poslodavac.'),
                ('Prijava HZMO/HZZO','U roku 8 dana od početka rada.'),
             ]},
        ],
        'note_finali':[
            'Hrvatska je u EU od 2013. i u eurozoni od 2023. — nema valutnog rizika.',
            'Prosječno trajanje svih dozvola: 30-60 dana.',
            'Portal e-Građani i HITRO.HR omogućuju mnoge postupke online.',
            'Turistička sezona može značajno povećati prihode u obalnim gradovima.',
        ],
    },
}
