# Risultati della valutazione

- Data: 2026-10-16
- Modello per le risposte: `qwen2.5:3b`
- Modello per gli embedding: `bge-m3`
- Documenti: appunti_biologia.pdf, appunti_storia.pdf
- Domande: 15 (9 con risposta negli appunti, 6 senza)
- Tempo medio per domanda: 1.5 secondi

## Riepilogo per soglia di pertinenza

La soglia è il punteggio minimo del brano più pertinente perché la domanda venga passata al modello.
«Migliore sul test» è calcolata automaticamente: più risposte giuste senza invenzioni e, a parità,
la soglia più alta. «In uso» è la soglia scelta nel file `.env`.

| Soglia | Risposte giuste | Invenzioni | Falsi "non trovato" | Fonte sbagliata | Risposta incompleta |
|---|---|---|---|---|---|
| 0.3 | **14/15** | 0 | 0 | 0 | 1 |
| 0.35 | **14/15** | 0 | 0 | 0 | 1 |
| 0.4 (in uso) | **14/15** | 0 | 0 | 0 | 1 |
| 0.45 | **14/15** | 0 | 0 | 0 | 1 |
| 0.5 ⬅ migliore sul test | **14/15** | 0 | 1 | 0 | 0 |

## Dettaglio delle domande (con la soglia in uso: 0.4)

| # | Tipo | Domanda | Punteggio | Esito | Risposta dell'app |
|---|---|---|---|---|---|
| 1 | diretta | Quali sono le fasi della mitosi? | 0.768 | ✅ corretta | Profase, metafase, anafase, telofase [1] — appunti_biologia.pdf p.5 |
| 2 | diretta | Quante molecole di ATP si ottengono da una molecola di glucosio? | 0.716 | ✅ corretta | circa 36-38 molecole di ATP [3] — appunti_biologia.pdf p.4 |
| 3 | diretta | Chi osservò per primo le cellule al microscopio? | 0.608 | ✅ corretta | Robert Hooke [1] — appunti_biologia.pdf p.1 |
| 4 | riformulata | Che cosa ha la cellula vegetale che manca a quella animale? | 0.611 | ✅ corretta | La cellula vegetale ha una parete cellulare di cellulosa, i cloroplasti per la fotosintesi e un grande vacuolo centrale; la cellula animale non ha parete cellulare [1]. — appunti_biologia.pdf p.2 |
| 5 | riformulata | Perché la meiosi aumenta la variabilità genetica? | 0.608 | ✅ corretta | Il crossing-over aumenta la variabilità genetica dei gameti [1]. — appunti_biologia.pdf p.6 |
| 6 | diretta | Chi guidò la spedizione dei Mille? | 0.609 | ✅ corretta | Giuseppe Garibaldi [1] — appunti_storia.pdf p.4 |
| 7 | diretta | In che data fu proclamato il Regno d'Italia? | 0.670 | ✅ corretta | 17 marzo 1861 [1] — appunti_storia.pdf p.5 |
| 8 | diretta | Cosa ottenne il Regno di Sardegna con l'armistizio di Villafranca? | 0.531 | ✅ corretta | Con l'armistizio di Villafranca il Regno di Sardegna ottenne la Lombardia [1]. — appunti_storia.pdf p.3 |
| 9 | due file | Chi formulò la teoria cellulare e chi fondò la Giovine Italia? | 0.459 | ⚠️ risposta incompleta | Matthias Cellulare e Giuseppe Mazzini fondò la Giovine Italia, [2] — appunti_storia.pdf p.1 |
| 10 | fuori tema | Chi ha vinto i mondiali di calcio del 2006? | 0.332 | ✅ non trovato (giusto) | Non l'ho trovato nei tuoi appunti. |
| 11 | fuori tema | Qual è la capitale dell'Australia? | 0.405 | ✅ non trovato (giusto) | Non l'ho trovato nei tuoi appunti. |
| 12 | fuori tema | Come si calcola la derivata di una funzione? | 0.438 | ✅ non trovato (giusto) | Non l'ho trovato nei tuoi appunti. |
| 13 | in tema, senza risposta | A cosa serve il reticolo endoplasmatico? | 0.460 | ✅ non trovato (giusto) | Non l'ho trovato nei tuoi appunti. |
| 14 | in tema, senza risposta | Qual è l'equazione della fotosintesi? | 0.482 | ✅ non trovato (giusto) | Non l'ho trovato nei tuoi appunti. |
| 15 | in tema, senza risposta | In che anno morì Giuseppe Garibaldi? | 0.516 | ✅ non trovato (giusto) | Non l'ho trovato nei tuoi appunti. |

## Legenda degli esiti

- **✅ corretta**: la risposta contiene le informazioni attese e cita le pagine giuste.
- **✅ non trovato (giusto)**: la risposta non era negli appunti e l'app l'ha detto.
- **⚠️ falso 'non trovato'**: la risposta era negli appunti, ma l'app ha detto di non averla trovata.
- **⚠️ fonte sbagliata**: il contenuto è giusto, ma manca almeno una delle pagine attese tra le fonti.
- **⚠️ risposta incompleta**: mancano alcune delle informazioni attese.
- **❌ invenzione**: l'app ha risposto a una domanda la cui risposta non è negli appunti. È l'errore più grave.
