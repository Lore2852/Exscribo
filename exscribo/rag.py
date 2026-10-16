"""Il cuore dell'app: cerca i brani giusti e chiede al modello di rispondere."""

from dataclasses import dataclass

from exscribo.config import Config
from exscribo.modelli import genera_risposta
from exscribo.pdf import Brano
from exscribo.ricerca import Indice

ISTRUZIONI = """Sei un assistente che aiuta uno studente a ripassare i suoi appunti.
Rispondi in italiano usando SOLO le informazioni contenute negli estratti forniti.
Non usare conoscenze esterne e non inventare nulla.
Rispondi in modo chiaro e conciso."""


@dataclass
class Risposta:
    testo: str
    brani: list[tuple[Brano, float]]  # i brani passati al modello, con il punteggio


def costruisci_messaggi(domanda: str, brani: list[tuple[Brano, float]]) -> list[dict]:
    """Prepara i messaggi per il modello: istruzioni, estratti e domanda."""
    estratti = "\n\n".join(
        f"[Estratto {numero}]\n{brano.testo}" for numero, (brano, _) in enumerate(brani, start=1)
    )
    return [
        {"role": "system", "content": ISTRUZIONI},
        {"role": "user", "content": f"Estratti dagli appunti:\n\n{estratti}\n\nDomanda: {domanda}"},
    ]


def rispondi(domanda: str, indice: Indice, config: Config, quanti: int = 4) -> Risposta:
    brani = indice.cerca(domanda, config, quanti)
    testo = genera_risposta(costruisci_messaggi(domanda, brani), config)
    return Risposta(testo=testo, brani=brani)
