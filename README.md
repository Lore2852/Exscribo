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

## Uso

```bash
# Sessione interattiva: fai tutte le domande che vuoi
python chiedi.py esempi/appunti_biologia.pdf

# Una sola domanda
python chiedi.py esempi/appunti_biologia.pdf "Quali sono le fasi della mitosi?"

# Mostra anche i brani trovati e il loro punteggio di somiglianza
python chiedi.py esempi/appunti_biologia.pdf --debug
```

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

## Struttura del progetto

```
exscribo/
├── exscribo/             # il codice dell'app
│   ├── config.py         #   legge la configurazione (.env)
│   ├── pdf.py            #   estrae il testo dai PDF e lo divide in brani
│   ├── modelli.py        #   parla con Ollama (embedding e risposte)
│   ├── ricerca.py        #   trova i brani più simili alla domanda
│   ├── citazioni.py      #   verifica le citazioni e le trasforma in file e pagina
│   └── rag.py            #   mette insieme ricerca e risposta
├── esempi/               # PDF di esempio (contenuto inventato, pubblico)
├── documenti/            # i TUOI PDF (esclusi da Git)
├── chiedi.py             # interfaccia da Terminale
├── verifica_ambiente.py  # controlla che l'ambiente sia pronto
├── .env.example          # modello di configurazione (copialo in .env)
└── requirements.txt      # librerie Python necessarie
```

## Privacy

I file `.env`, la cartella `documenti/`, qualsiasi file PDF (tranne quelli di esempio in `esempi/`)
e l'indice generato dai documenti sono esclusi da Git tramite `.gitignore`.
