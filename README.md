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

# 5. Scarica il modello linguistico (vedi .env per la scelta in base alla RAM)
ollama pull qwen2.5:3b

# 6. Controlla che sia tutto a posto
python verifica_ambiente.py
```

## Struttura del progetto

```
exscribo/
├── documenti/            # i TUOI PDF (esclusi da Git)
├── .env.example          # modello di configurazione (copialo in .env)
├── requirements.txt      # librerie Python necessarie
├── verifica_ambiente.py  # controlla che l'ambiente sia pronto
└── README.md
```

## Privacy

I file `.env`, la cartella `documenti/`, qualsiasi file PDF (tranne quelli di esempio in `esempi/`)
e l'indice generato dai documenti sono esclusi da Git tramite `.gitignore`.
