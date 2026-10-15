"""Controlla che l'ambiente di lavoro sia pronto.

Uso:  python verifica_ambiente.py

Usa solo la libreria standard di Python, quindi funziona anche
prima di aver installato qualsiasi pacchetto.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

CARTELLA_PROGETTO = Path(__file__).resolve().parent
OLLAMA_URL_PREDEFINITO = "http://localhost:11434"


def leggi_env(percorso: Path) -> dict:
    """Legge un file .env molto semplice (righe CHIAVE=valore)."""
    valori = {}
    if not percorso.exists():
        return valori
    for riga in percorso.read_text(encoding="utf-8").splitlines():
        riga = riga.strip()
        if not riga or riga.startswith("#") or "=" not in riga:
            continue
        chiave, valore = riga.split("=", 1)
        valori[chiave.strip()] = valore.strip()
    return valori


def ok(messaggio: str) -> None:
    print(f"  [OK]        {messaggio}")


def problema(messaggio: str, soluzione: str) -> None:
    print(f"  [DA FARE]   {messaggio}")
    print(f"              -> {soluzione}")


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
        ok(f"Ambiente virtuale attivo ({Path(sys.prefix).name})")
    else:
        tutto_ok = False
        problema(
            "Nessun ambiente virtuale attivo",
            "esegui: source .venv/bin/activate",
        )

    # 3. File .env
    env = leggi_env(CARTELLA_PROGETTO / ".env")
    if env:
        ok("File .env trovato")
    else:
        tutto_ok = False
        problema("File .env mancante", "esegui: cp .env.example .env")

    # 4. Cartella dei documenti
    if (CARTELLA_PROGETTO / "documenti").is_dir():
        ok("Cartella documenti/ presente")
    else:
        tutto_ok = False
        problema("Cartella documenti/ mancante", "esegui: mkdir documenti")

    # 5. Ollama in esecuzione e modello scaricato
    url = env.get("OLLAMA_URL") or os.environ.get("OLLAMA_URL") or OLLAMA_URL_PREDEFINITO
    modello = env.get("OLLAMA_MODEL", "")
    try:
        # /api/tags restituisce l'elenco dei modelli già scaricati.
        with urllib.request.urlopen(f"{url}/api/tags", timeout=3) as risposta:
            dati = json.load(risposta)
        ok(f"Ollama risponde su {url}")
        scaricati = [m["name"] for m in dati.get("models", [])]
        if not modello:
            tutto_ok = False
            problema("OLLAMA_MODEL non impostato nel .env", "aggiungi ad es. OLLAMA_MODEL=qwen2.5:3b")
        elif modello in scaricati:
            ok(f"Modello {modello} scaricato")
        else:
            tutto_ok = False
            problema(
                f"Modello {modello} non ancora scaricato",
                f"esegui: ollama pull {modello}",
            )
    except OSError:
        tutto_ok = False
        problema(
            f"Ollama non risponde su {url}",
            "installalo (brew install ollama) e avvialo (ollama serve, o apri l'app Ollama)",
        )

    print()
    if tutto_ok:
        print("Tutto pronto! Puoi passare al Passo 2.")
        return 0
    print("Sistema i punti [DA FARE] e rilancia questo script.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
