"""Comunicazione con Ollama, che fa girare i modelli sul tuo Mac.

Ollama espone una piccola API web su http://localhost:11434: le mandiamo
richieste in formato JSON e ci risponde in JSON. Usiamo solo la libreria
standard di Python (urllib), senza dipendenze aggiuntive.
"""

import json
import urllib.error
import urllib.request

import numpy as np

from exscribo.config import Config


class ErroreOllama(Exception):
    """Un problema nel parlare con Ollama, con un messaggio comprensibile."""


def _chiama_ollama(config: Config, percorso: str, dati: dict) -> dict:
    richiesta = urllib.request.Request(
        f"{config.ollama_url}{percorso}",
        data=json.dumps(dati).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(richiesta, timeout=300) as risposta:
            return json.load(risposta)
    except urllib.error.HTTPError as errore:
        dettaglio = errore.read().decode("utf-8", errors="replace")
        if errore.code == 404:
            raise ErroreOllama(
                f"Il modello '{dati['model']}' non è installato. Esegui: ollama pull {dati['model']}"
            ) from errore
        raise ErroreOllama(f"Ollama ha risposto con l'errore {errore.code}: {dettaglio}") from errore
    except OSError as errore:
        raise ErroreOllama(
            f"Non riesco a contattare Ollama su {config.ollama_url}. È avviato? ({errore})"
        ) from errore


def calcola_embedding(testi: list[str], config: Config) -> np.ndarray:
    """Trasforma ogni testo in un vettore di numeri.

    Restituisce una matrice: una riga per testo. Ogni riga è "normalizzata"
    (lunghezza 1), così la somiglianza tra due testi si calcola con una
    semplice moltiplicazione.
    """
    vettori = []
    # Mandiamo i testi a gruppi di 32 per non fare richieste troppo grandi
    for inizio in range(0, len(testi), 32):
        gruppo = testi[inizio : inizio + 32]
        dati = _chiama_ollama(config, "/api/embed", {"model": config.modello_embedding, "input": gruppo})
        vettori.extend(dati["embeddings"])

    matrice = np.array(vettori, dtype=np.float32)
    return matrice / np.linalg.norm(matrice, axis=1, keepdims=True)


def genera_risposta(messaggi: list[dict], config: Config) -> str:
    """Manda la conversazione al modello di chat e restituisce la sua risposta."""
    dati = _chiama_ollama(
        config,
        "/api/chat",
        {
            "model": config.modello_chat,
            "messages": messaggi,
            "stream": False,  # aspettiamo la risposta completa invece di riceverla a pezzi
            "options": {
                "temperature": 0,  # risposte meno "creative": meno rischio di inventare
                "num_ctx": 4096,  # quanti token di testo il modello può considerare insieme
            },
        },
    )
    return dati["message"]["content"].strip()
