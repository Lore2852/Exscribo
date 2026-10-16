"""Il cuore dell'app: cerca i brani giusti e chiede al modello di rispondere."""

import re
from dataclasses import dataclass

from exscribo.config import Config
from exscribo.modelli import genera_risposta
from exscribo.pdf import Brano
from exscribo.ricerca import Indice

ISTRUZIONI = """Sei un assistente che aiuta uno studente a ripassare i suoi appunti.
Ti verranno dati alcuni estratti numerati degli appunti e una domanda.

Regole:
- Rispondi in italiano usando SOLO le informazioni contenute negli estratti.
- Non usare conoscenze esterne e non inventare nulla.
- Dopo ogni informazione indica tra parentesi quadre il numero dell'estratto da cui proviene, ad esempio [1] oppure [2][3].
- Rispondi in modo chiaro e conciso.

Esempio di formato: "Prima informazione [1]. Seconda informazione [3]." """

# Riconosce le citazioni nel testo del modello: [1], [1, 2] e anche [Estratto 1],
# perché i modelli piccoli non sempre rispettano il formato alla lettera.
# Solo numeri di 1-2 cifre: così, per esempio, un anno come [2006] non viene toccato.
CITAZIONE = re.compile(r"\[(?:estratto\s*)?(\d{1,2}(?:\s*,\s*\d{1,2})*)\]", re.IGNORECASE)


@dataclass
class Fonte:
    """Una pagina citata nella risposta."""

    file: str
    pagina: int
    estratti: list[int]  # i numeri degli estratti citati che vengono da questa pagina


@dataclass
class Risposta:
    testo: str
    fonti: list[Fonte]
    brani: list[tuple[Brano, float]]  # i brani passati al modello, con il punteggio


def costruisci_messaggi(domanda: str, brani: list[tuple[Brano, float]]) -> list[dict]:
    """Prepara i messaggi per il modello: istruzioni, estratti numerati e domanda."""
    estratti = "\n\n".join(f"[{numero}]\n{brano.testo}" for numero, (brano, _) in enumerate(brani, start=1))
    return [
        {"role": "system", "content": ISTRUZIONI},
        {"role": "user", "content": f"Estratti dagli appunti:\n\n{estratti}\n\nDomanda: {domanda}"},
    ]


def sistema_citazioni(testo: str, quanti_estratti: int) -> str:
    """Uniforma le citazioni a [1][2] e toglie quelle con numeri inesistenti."""

    def sostituisci(corrispondenza: re.Match) -> str:
        numeri = [int(n) for n in corrispondenza.group(1).split(",")]
        validi = [n for n in numeri if 1 <= n <= quanti_estratti]
        return "".join(f"[{n}]" for n in validi)

    testo = CITAZIONE.sub(sostituisci, testo)
    # Ripulisce gli spazi rimasti dove abbiamo tolto una citazione
    testo = re.sub(r"(?<=\S) {2,}", " ", testo)  # doppi spazi in mezzo alla riga
    testo = re.sub(r" +$", "", testo, flags=re.MULTILINE)  # spazi a fine riga
    return re.sub(r" +([.,;:])", r"\1", testo)  # spazio prima della punteggiatura


def trova_fonti(testo: str, brani: list[tuple[Brano, float]]) -> list[Fonte]:
    """Trasforma i numeri citati nel testo in file e pagina, nell'ordine in cui compaiono.

    File e pagina vengono dai nostri dati, mai dal modello: così non possono essere inventati.
    """
    fonti: dict[tuple[str, int], Fonte] = {}  # un dizionario ricorda l'ordine di inserimento
    for numero in (int(n) for n in re.findall(r"\[(\d{1,2})\]", testo)):
        brano = brani[numero - 1][0]
        fonte = fonti.setdefault((brano.file, brano.pagina), Fonte(brano.file, brano.pagina, []))
        if numero not in fonte.estratti:
            fonte.estratti.append(numero)
    return list(fonti.values())


def rispondi(domanda: str, indice: Indice, config: Config, quanti: int = 4) -> Risposta:
    brani = indice.cerca(domanda, config, quanti)
    testo = genera_risposta(costruisci_messaggi(domanda, brani), config)
    testo = sistema_citazioni(testo, len(brani))
    return Risposta(testo=testo, fonti=trova_fonti(testo, brani), brani=brani)
