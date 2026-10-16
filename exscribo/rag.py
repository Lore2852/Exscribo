"""Il cuore dell'app: cerca i brani giusti e chiede al modello di rispondere."""

from dataclasses import dataclass

from exscribo.citazioni import Fonte, sistema_citazioni, trova_fonti, verifica_citazioni
from exscribo.config import Config
from exscribo.modelli import genera_risposta
from exscribo.pdf import Brano
from exscribo.ricerca import Indice

ISTRUZIONI = """Sei un assistente che aiuta uno studente a ripassare i suoi appunti.
Ti verranno dati alcuni estratti numerati degli appunti e una domanda.

Regole:
- Rispondi in italiano usando SOLO le informazioni contenute negli estratti.
- Non usare conoscenze esterne e non inventare nulla.
- Alla fine di ogni frase scrivi tra parentesi quadre il numero dell'estratto da cui viene l'informazione.
- Rispondi in modo chiaro e conciso."""

# Un esempio svolto ("few-shot"): una finta domanda con la risposta corretta.
# I modelli piccoli imitano un esempio concreto meglio di quanto seguano una regola.
# L'argomento è volutamente diverso dagli appunti, così il modello non lo confonde con essi.
ESEMPIO_DOMANDA = """Estratti dagli appunti:

[1]
Il Po è il fiume più lungo d'Italia: nasce dal Monviso e sfocia nel mare Adriatico dopo circa 652 km.

[2]
Il lago di Garda è il lago più grande d'Italia, con una superficie di circa 370 km quadrati.

Domanda: Quanto è lungo il Po e dove sfocia?"""

ESEMPIO_RISPOSTA = "Il Po è lungo circa 652 km [1]. Sfocia nel mare Adriatico [1]."


@dataclass
class Risposta:
    testo: str
    fonti: list[Fonte]
    brani: list[tuple[Brano, float]]  # i brani passati al modello, con il punteggio


def costruisci_messaggi(domanda: str, brani: list[tuple[Brano, float]]) -> list[dict]:
    """Prepara i messaggi per il modello: istruzioni, esempio svolto, estratti e domanda."""
    estratti = "\n\n".join(f"[{numero}]\n{brano.testo}" for numero, (brano, _) in enumerate(brani, start=1))
    return [
        {"role": "system", "content": ISTRUZIONI},
        {"role": "user", "content": ESEMPIO_DOMANDA},
        {"role": "assistant", "content": ESEMPIO_RISPOSTA},
        {"role": "user", "content": f"Estratti dagli appunti:\n\n{estratti}\n\nDomanda: {domanda}"},
    ]


def rispondi(domanda: str, indice: Indice, config: Config, quanti: int = 4) -> Risposta:
    brani = indice.cerca(domanda, config, quanti)
    testo = genera_risposta(costruisci_messaggi(domanda, brani), config)
    testo = sistema_citazioni(testo, len(brani))
    testo = verifica_citazioni(testo, brani)
    return Risposta(testo=testo, fonti=trova_fonti(testo, brani), brani=brani)
