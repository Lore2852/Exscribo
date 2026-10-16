# Exscribo — Chiedi ai tuoi appunti

> 🚧 **Progetto in costruzione.** Questo README verrà completato alla fine dello sviluppo.

Exscribo è un'app che risponde alle tue domande **usando solo i tuoi appunti e le tue slide in PDF**.
Ogni risposta indica **il file e la pagina** da cui proviene. Se la risposta non è nei documenti,
l'app dice chiaramente *"Non l'ho trovato nei tuoi appunti"* invece di inventare.

Tutto gira **in locale sul tuo computer**: nessun server, nessun abbonamento, nessun costo.
I tuoi PDF non lasciano mai il tuo Mac.

## Come funziona (in breve)

L'app usa una tecnica chiamata **RAG** (*Retrieval-Augmented Generation*):

1. legge i PDF pagina per pagina e li divide in brevi brani;
2. quando fai una domanda, cerca i brani più pertinenti;
3. passa domanda e brani a un modello linguistico locale ([Ollama](https://ollama.com)),
   che risponde basandosi solo su quei brani e citando le fonti.

## Requisiti

- macOS con chip Apple (M1 o successivi) — dovrebbe funzionare anche su Linux
- Python 3.10 o più recente
- [Ollama](https://ollama.com) installato

## Installazione

```bash
# 1. Scarica il progetto
git clone https://github.com/Lore2852/exscribo.git
cd exscribo

# 2. Crea e attiva un ambiente virtuale Python
python3 -m venv .venv
source .venv/bin/activate

# 3. Installa le librerie
pip install -r requirements.txt

# 4. Crea il file di configurazione
cp .env.example .env

# 5. Scarica i modelli (vedi .env per la scelta in base alla RAM)
ollama pull qwen2.5:3b   # scrive le risposte
ollama pull bge-m3       # trova i brani pertinenti

# 6. Controlla che sia tutto a posto
python verifica_ambiente.py
```

## Interfaccia web

```bash
streamlit run app.py
```

Si apre il browser su `http://localhost:8501`. Dalla barra laterale puoi caricare
nuovi PDF (vengono salvati in `documenti/`), scegliere in quali cartelle cercare
e attivare la modalità debug. Cliccando su una fonte si legge l'estratto esatto
da cui viene la risposta.

L'app gira **solo sul tuo computer**: la configurazione in `.streamlit/config.toml`
la rende raggiungibile solo da `localhost`, disattiva le statistiche d'uso di
Streamlit e nasconde il pulsante per pubblicarla online. Avviala dalla cartella
del progetto, altrimenti questa configurazione non viene letta.
Per fermarla, premi `Ctrl+C` nel Terminale.

## Uso da Terminale

```bash
# Tutti i PDF di una cartella (anche nelle sottocartelle)
python chiedi.py documenti/

# Più cartelle e file insieme
python chiedi.py documenti/ esempi/appunti_storia.pdf

# Una sola domanda
python chiedi.py esempi/ "Chi guidò la spedizione dei Mille?"

# Mostra anche i brani trovati e il loro punteggio di somiglianza
python chiedi.py esempi/ --debug
```

La prima volta che legge un PDF, l'app calcola gli embedding e li salva nella
cartella `indice/` (esclusa da Git). Le volte successive li rilegge da lì, e li
ricalcola solo per i PDF nuovi o modificati. La cartella `indice/` si può
cancellare in qualsiasi momento: verrà ricreata.

Esempio di risposta:

```
Le fasi della mitosi sono profase, metafase, anafase e telofase [1].

Fonti:
  [1] appunti_biologia.pdf, pagina 5
```

Il modello indica solo il numero dell'estratto usato (`[1]`); file e pagina
vengono aggiunti dal programma, così non possono essere inventati.
Il programma inoltre verifica ogni citazione: se le parole chiave della frase non
compaiono nell'estratto citato la scarta, e se una frase non ha citazioni
cerca l'estratto che la contiene.

## Quando la risposta non c'è

Se la risposta non è negli appunti, l'app risponde sempre
**"Non l'ho trovato nei tuoi appunti."** invece di inventare. Tre controlli, in ordine:

1. **Pertinenza:** se nessun brano supera la soglia `SOGLIA_PERTINENZA` (nel `.env`),
   la domanda è fuori tema e il modello non viene nemmeno interpellato.
2. **Segnale del modello:** il modello è istruito a rispondere `NON_TROVATO` quando
   gli estratti non contengono la risposta.
3. **Verifica delle fonti:** se nessuna frase della risposta è supportata dagli
   estratti, la risposta viene scartata.

Con `--debug` l'app mostra quale controllo è scattato e cosa aveva scritto il modello.

## Struttura del progetto

```
exscribo/
├── exscribo/             # il codice dell'app
│   ├── config.py         #   legge la configurazione (.env)
│   ├── archivio.py       #   costruisce l'indice da più PDF e lo salva su disco
│   ├── pdf.py            #   estrae il testo dai PDF e lo divide in brani
│   ├── modelli.py        #   parla con Ollama (embedding e risposte)
│   ├── ricerca.py        #   trova i brani più simili alla domanda
│   ├── citazioni.py      #   verifica le citazioni e le trasforma in file e pagina
│   └── rag.py            #   mette insieme ricerca e risposta
├── esempi/               # PDF di esempio (contenuto inventato, pubblico)
├── indice/               # embedding salvati (generata, esclusa da Git)
├── documenti/            # i TUOI PDF (esclusi da Git)
├── app.py                # interfaccia web (Streamlit)
├── chiedi.py             # interfaccia da Terminale
├── .streamlit/           # configurazione dell'interfaccia web
├── verifica_ambiente.py  # controlla che l'ambiente sia pronto
├── .env.example          # modello di configurazione (copialo in .env)
└── requirements.txt      # librerie Python necessarie
```

## Privacy

I file `.env`, la cartella `documenti/`, qualsiasi file PDF (tranne quelli di esempio in `esempi/`)
e l'indice generato dai documenti sono esclusi da Git tramite `.gitignore`.
