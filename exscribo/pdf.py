"""Lettura dei PDF e divisione del testo in brani."""

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

LUNGHEZZA_BRANO = 800  # caratteri massimi per brano
SOVRAPPOSIZIONE = 150  # caratteri condivisi tra due brani consecutivi della stessa pagina


@dataclass
class Brano:
    """Un pezzo di testo, con l'indicazione di dove si trova."""

    file: str  # nome del file, es. "appunti_biologia.pdf"
    pagina: int  # numero di pagina, contando da 1 come nei lettori PDF
    testo: str


def pulisci(testo: str) -> str:
    """Sistema il testo estratto dal PDF."""
    # Ricongiunge le parole spezzate a fine riga: "mito-\ncondrio" -> "mitocondrio"
    testo = re.sub(r"(\w)-\n(\w)", r"\1\2", testo)
    # Sostituisce a capo e spazi multipli con un solo spazio
    testo = re.sub(r"\s+", " ", testo)
    return testo.strip()


def leggi_pagine(percorso: Path) -> list[tuple[int, str]]:
    """Restituisce una lista di (numero_pagina, testo), saltando le pagine vuote."""
    lettore = PdfReader(percorso)
    pagine = []
    for numero, pagina in enumerate(lettore.pages, start=1):
        testo = pulisci(pagina.extract_text() or "")
        if testo:
            pagine.append((numero, testo))
    return pagine


def dividi_testo(testo: str, lunghezza: int, sovrapposizione: int) -> list[str]:
    """Divide un testo in pezzi di circa `lunghezza` caratteri, senza spezzare le parole.

    Pezzi consecutivi condividono circa `sovrapposizione` caratteri, così una
    frase a cavallo tra due pezzi compare intera in almeno uno dei due.
    """
    if len(testo) <= lunghezza:
        return [testo]

    parole = testo.split(" ")
    pezzi = []
    inizio = 0
    while inizio < len(parole):
        # Aggiunge parole finché il pezzo non supera la lunghezza massima
        fine = inizio
        caratteri = 0
        while fine < len(parole) and caratteri + len(parole[fine]) + 1 <= lunghezza:
            caratteri += len(parole[fine]) + 1
            fine += 1
        fine = max(fine, inizio + 1)  # una parola lunghissima: la prende comunque
        pezzi.append(" ".join(parole[inizio:fine]))
        if fine >= len(parole):
            break

        # Il pezzo successivo riparte qualche parola più indietro (sovrapposizione)
        indietro = 0
        caratteri = 0
        while indietro < fine - inizio - 1 and caratteri < sovrapposizione:
            caratteri += len(parole[fine - 1 - indietro]) + 1
            indietro += 1
        inizio = fine - indietro
    return pezzi


def dividi_in_brani(
    percorso: Path, lunghezza: int = LUNGHEZZA_BRANO, sovrapposizione: int = SOVRAPPOSIZIONE
) -> list[Brano]:
    """Legge un PDF e lo divide in brani.

    Ogni brano appartiene a una sola pagina: così sapremo sempre
    da quale pagina viene un'informazione.
    """
    brani = []
    for numero, testo in leggi_pagine(percorso):
        for pezzo in dividi_testo(testo, lunghezza, sovrapposizione):
            brani.append(Brano(file=percorso.name, pagina=numero, testo=pezzo))
    return brani
