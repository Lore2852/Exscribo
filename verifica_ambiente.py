"""Controlla che l'ambiente di lavoro sia pronto.

Uso:  python verifica_ambiente.py

Usa solo la libreria standard di Python, quindi funziona anche
prima di aver installato qualsiasi pacchetto.
"""

import importlib.util
import json
import sys
import urllib.request

from exscribo.config import CARTELLA_PROGETTO, carica_config, leggi_env


def ok(messaggio: str) -> None:
    print(f"  [OK]        {messaggio}")


def problema(messaggio: str, soluzione: str) -> None:
    print(f"  [DA FARE]   {messaggio}")
    print(f"              -> {soluzione}")


def con_tag(nome: str) -> str:
    """Ollama chiama "bge-m3" anche "bge-m3:latest": usiamo sempre la forma completa."""
    return nome if ":" in nome else f"{nome}:latest"


def main() -> int:
    print("Verifica dell'ambiente di Exscribo\n")
    tutto_ok = True

    # 1. Versione di Python
    versione = sys.version_info
    testo_versione = f"{versione.major}.{versione.minor}.{versione.micro}"
    if versione >= (3, 10):
        ok(f"Python {testo_versione}")
    else:
        tutto_ok = False
        problema(
            f"Python {testo_versione} è troppo vecchio (serve 3.10 o più)",
            "installa una versione recente: brew install python@3.12",
        )

    # 2. Ambiente virtuale attivo
    # Dentro un venv, sys.prefix punta al venv e differisce da sys.base_prefix.
    if sys.prefix != sys.base_prefix:
        ok(f"Ambiente virtuale attivo ({CARTELLA_PROGETTO.name}/.venv)")
    else:
        tutto_ok = False
        problema("Nessun ambiente virtuale attivo", "esegui: source .venv/bin/activate")

    # 3. Librerie installate
    mancanti = [nome for nome in ("pypdf", "numpy") if importlib.util.find_spec(nome) is None]
    if not mancanti:
        ok("Librerie Python installate")
    else:
        tutto_ok = False
        problema(f"Librerie mancanti: {', '.join(mancanti)}", "esegui: pip install -r requirements.txt")

    # 4. File .env
    if leggi_env(CARTELLA_PROGETTO / ".env"):
        ok("File .env trovato")
    else:
        tutto_ok = False
        problema("File .env mancante", "esegui: cp .env.example .env")

    # 5. Cartella dei documenti
    if (CARTELLA_PROGETTO / "documenti").is_dir():
        ok("Cartella documenti/ presente")
    else:
        tutto_ok = False
        problema("Cartella documenti/ mancante", "esegui: mkdir documenti")

    # 6. Configurazione leggibile
    try:
        config = carica_config()
    except ValueError as errore:
        problema("Valore non valido nel file .env", str(errore))
        print("\nSistema i punti [DA FARE] e rilancia questo script.")
        return 1

    # 7. Ollama in esecuzione e modelli scaricati
    try:
        # /api/tags restituisce l'elenco dei modelli già scaricati.
        with urllib.request.urlopen(f"{config.ollama_url}/api/tags", timeout=3) as risposta:
            dati = json.load(risposta)
        ok(f"Ollama risponde su {config.ollama_url}")
        scaricati = {con_tag(m["name"]) for m in dati.get("models", [])}
        for modello in (config.modello_chat, config.modello_embedding):
            if con_tag(modello) in scaricati:
                ok(f"Modello {modello} scaricato")
            else:
                tutto_ok = False
                problema(f"Modello {modello} non ancora scaricato", f"esegui: ollama pull {modello}")
    except OSError:
        tutto_ok = False
        problema(
            f"Ollama non risponde su {config.ollama_url}",
            "avvialo aprendo l'app Ollama (o con: ollama serve)",
        )

    print()
    if tutto_ok:
        print("Tutto pronto!")
        return 0
    print("Sistema i punti [DA FARE] e rilancia questo script.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
