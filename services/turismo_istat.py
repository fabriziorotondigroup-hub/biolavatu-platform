"""
services/turismo_istat.py — BIOLavaTU LaundryPro [ADD-ON]
Indice di vocazione turistica per comune, basato su dati Istat ufficiali
"Movimento dei clienti negli esercizi ricettivi" — Anno 2024.
Fonte: Istat, comunicato stampa 9 marzo 2026, Prospetto 4
(Primi 50 Comuni italiani per presenze negli esercizi ricettivi).

ISOLATO — zero dipendenze da altri file. Da aggiornare manualmente
una volta all'anno quando Istat pubblica i nuovi dati definitivi.

Aggiornamento: dati 2024, pubblicati marzo 2026.
"""

# ── Presenze turistiche 2024 per comune (valori assoluti) ────────────────────
# Fonte: Istat — Prospetto 4, "I flussi turistici - Anno 2024"
PRESENZE_TURISTICHE_2024 = {
    'roma':                           42_705_319,
    'milano':                         14_054_184,
    'venezia':                        13_290_973,
    'firenze':                         9_192_960,
    'rimini':                          6_938_992,
    'cavallino-treporti':              6_761_224,
    'san michele al tagliamento':      5_572_705,
    'jesolo':                          5_496_611,
    'caorle':                          4_426_817,
    'bologna':                         4_146_877,
    'lazise':                          4_052_124,
    'napoli':                          3_862_329,
    'lignano sabbiadoro':              3_618_677,
    'cesenatico':                      3_609_439,
    'torino':                          3_580_221,
    'riccione':                        3_421_764,
    'cervia':                          3_408_137,
    'verona':                          3_103_472,
    'sorrento':                        2_847_463,
    'ravenna':                         2_842_778,
    'peschiera del garda':             2_582_448,
    'bardolino':                       2_487_568,
    'genova':                          2_297_499,
    'fiumicino':                       2_166_080,
    'comacchio':                       2_161_905,
    'bellaria-igea marina':            2_135_560,
    'vieste':                          2_042_567,
    'palermo':                         1_964_765,
    'pisa':                            1_861_048,
    'abano terme':                     1_860_546,
    'castelrotto':                     1_780_424,  # Castelrotto/Kastelruth
    'padova':                          1_764_999,
    'riva del garda':                  1_720_333,
    'livigno':                         1_664_753,
    'chioggia':                        1_651_277,
    'montecatini-terme':               1_562_492,
    'cattolica':                       1_543_275,
    'castiglione della pescaia':       1_452_965,
    'selva di val gardena':            1_435_639,  # Wolkenstein in Gröden
    'assisi':                          1_402_071,
    'grado':                           1_401_767,
    'trieste':                         1_391_122,
    'bari':                            1_372_257,
    'alghero':                         1_314_529,
    'badia':                           1_303_575,  # Badia/Abtei
    'sirmione':                        1_273_116,
    'forio':                           1_262_123,
    'limone sul garda':                1_216_414,
    'merano':                          1_215_574,  # Merano/Meran
    'malcesine':                       1_191_972,
}

TOTALE_PRESENZE_ITALIA_2024 = 466_158_045
FONTE = 'Istat, Movimento dei clienti negli esercizi ricettivi — Anno 2024 (comunicato 9/3/2026)'


def normalizza_nome_comune(nome: str) -> str:
    """Normalizza il nome comune per il matching (minuscolo, senza accenti complessi)."""
    if not nome:
        return ''
    n = nome.strip().lower()
    # Alias comuni per varianti di scrittura frequenti
    alias = {
        'castelrotto/kastelruth': 'castelrotto',
        'kastelruth': 'castelrotto',
        'selva di val gardena/wolkenstein in gröden': 'selva di val gardena',
        'wolkenstein': 'selva di val gardena',
        'badia/abtei': 'badia',
        'abtei': 'badia',
        'merano/meran': 'merano',
        'meran': 'merano',
        'bellaria igea marina': 'bellaria-igea marina',
        'lignano': 'lignano sabbiadoro',
    }
    return alias.get(n, n)


def get_vocazione_turistica(comune: str) -> dict:
    """
    Ritorna l'indice di vocazione turistica per un comune italiano,
    basato sulle presenze turistiche ufficiali Istat 2024.

    Indice 0-100:
      - comuni in top 50 Istat: scala logaritmica sulle presenze assolute
      - comuni non in lista: indice 0, vocazione 'non rilevata'
        (NON significa zero turismo, significa solo che non è tra i 50
         comuni a maggior volume assoluto in Italia — molti comuni più
         piccoli hanno comunque una vocazione turistica locale rilevante,
         semplicemente non emergono nella classifica nazionale per volume)
    """
    nome_norm = normalizza_nome_comune(comune)
    presenze = PRESENZE_TURISTICHE_2024.get(nome_norm)

    if presenze is None:
        return {
            'in_top50_istat': False,
            'presenze_2024': None,
            'indice_vocazione': 0,
            'label': 'Non rilevato in Top 50 nazionale',
            'colore': '#64748b',
            'posizione_classifica': None,
            'fonte': FONTE,
            'nota': ('Il comune non rientra nei 50 comuni italiani a maggior volume '
                     'turistico assoluto. Non implica assenza di turismo locale.'),
        }

    # Posizione in classifica (1-indexed)
    ordinati = sorted(PRESENZE_TURISTICHE_2024.items(), key=lambda x: -x[1])
    posizione = next((i + 1 for i, (n, _) in enumerate(ordinati) if n == nome_norm), None)

    # Indice 0-100 su scala logaritmica (Roma=100, soglia minima top50 ≈ 35)
    import math
    max_presenze = max(PRESENZE_TURISTICHE_2024.values())
    min_presenze = min(PRESENZE_TURISTICHE_2024.values())
    log_p   = math.log10(presenze)
    log_max = math.log10(max_presenze)
    log_min = math.log10(min_presenze)
    indice  = round(35 + (log_p - log_min) / (log_max - log_min) * 65) if log_max > log_min else 50
    indice  = max(0, min(100, indice))

    if   indice >= 80: label, colore = 'Vocazione turistica altissima', '#dc2626'
    elif indice >= 60: label, colore = 'Vocazione turistica alta',      '#f59e0b'
    elif indice >= 40: label, colore = 'Vocazione turistica media',     '#3b82f6'
    else:               label, colore = 'Vocazione turistica presente', '#10b981'

    return {
        'in_top50_istat': True,
        'presenze_2024': presenze,
        'indice_vocazione': indice,
        'label': label,
        'colore': colore,
        'posizione_classifica': posizione,
        'quota_pct_nazionale': round(presenze / TOTALE_PRESENZE_ITALIA_2024 * 100, 2),
        'fonte': FONTE,
        'nota': None,
    }
