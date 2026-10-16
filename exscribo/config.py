"""Lettura della configurazione (file .env e variabili d'ambiente).

Usa solo la libreria standard, così anche verifica_ambiente.py può
importarlo prima che le altre librerie siano installate.
"""

import os
from dataclasses import dataclass
from pathlib import Path

CARTELLA_PROGETTO = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    ollama_url: str
    modello_chat: str  # il modello che scrive le risposte
    modello_embedding: str  # il modello che trasforma i testi in vettori


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


def carica_config() -> Config:
    """Ordine di priorità: variabile d'ambiente, poi file .env, poi valore predefinito."""
    env = leggi_env(CARTELLA_PROGETTO / ".env")

    def valore(chiave: str, predefinito: str) -> str:
        return os.environ.get(chiave) or env.get(chiave) or predefinito

    return Config(
        ollama_url=valore("OLLAMA_URL", "http://localhost:11434").rstrip("/"),
        modello_chat=valore("OLLAMA_MODEL", "qwen2.5:3b"),
        modello_embedding=valore("OLLAMA_EMBED_MODEL", "bge-m3"),
    )
