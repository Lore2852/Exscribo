"""Costruzione dell'indice da più PDF, con un archivio su disco degli embedding.

Calcolare gli embedding è la parte lenta. Per ogni PDF salviamo brani e
vettori in un file dentro indice/, e alle volte successive li rileggiamo
invece di ricalcolarli.

Ogni file salvato ha come nome l'"impronta" (hash) del PDF: un codice
calcolato dal suo contenuto. Se il PDF cambia anche di una virgola,
l'impronta cambia, quindi il vecchio file salvato non viene più usato.
La cartella indice/ si può cancellare in qualsiasi momento: verrà ricreata.
"""

import hashlib
from collections.abc import Callable
from pathlib import Path

import numpy as np

from exscribo.config import CARTELLA_PROGETTO, Config
from exscribo.modelli import calcola_embedding
from exscribo.pdf import LUNGHEZZA_BRANO, SOVRAPPOSIZIONE, Brano, dividi_in_brani
from exscribo.ricerca import Indice

CARTELLA_INDICE = CARTELLA_PROGETTO / "indice"

# Da aumentare se cambiamo il modo di estrarre o dividere il testo:
# così tutti i file salvati con il metodo vecchio vengono ignorati.
VERSIONE_ARCHIVIO = 1


def elenca_pdf(percorsi: list[Path]) -> list[Path]:
    """Trasforma un elenco di file e cartelle nell'elenco dei PDF da leggere.

    Le cartelle vengono esplorate anche nelle sottocartelle.
    """
    trovati = []
    for percorso in percorsi:
        if percorso.is_dir():
            trovati.extend(p for p in sorted(percorso.rglob("*")) if p.suffix.lower() == ".pdf")
        elif percorso.is_file() and percorso.suffix.lower() == ".pdf":
            trovati.append(percorso)
        else:
            raise FileNotFoundError(f"Non è un PDF né una cartella: {percorso}")
    # Toglie i doppioni (lo stesso file indicato due volte), mantenendo l'ordine
    return list({p.resolve(): p for p in trovati}.values())


def impronta(percorso: Path, config: Config) -> str:
    """Codice che identifica il contenuto del PDF e il modo in cui lo elaboriamo."""
    calcolatore = hashlib.sha256()
    impostazioni = f"{VERSIONE_ARCHIVIO}|{config.modello_embedding}|{LUNGHEZZA_BRANO}|{SOVRAPPOSIZIONE}|"
    calcolatore.update(impostazioni.encode("utf-8"))
    calcolatore.update(percorso.read_bytes())
    return calcolatore.hexdigest()


def leggi_salvato(file_salvato: Path, nome_pdf: str) -> tuple[list[Brano], np.ndarray] | None:
    """Rilegge brani e vettori salvati. Restituisce None se il file manca o è rovinato."""
    if not file_salvato.exists():
        return None
    try:
        # allow_pickle=False: rifiuta i formati che potrebbero eseguire codice nascosto
        with np.load(file_salvato, allow_pickle=False) as dati:
            brani = [
                Brano(file=nome_pdf, pagina=int(pagina), testo=str(testo))
                for pagina, testo in zip(dati["pagine"], dati["testi"])
            ]
            return brani, dati["vettori"]
    except (OSError, ValueError, KeyError):
        return None  # file rovinato (es. salvataggio interrotto): lo ricalcoleremo


def salva(file_salvato: Path, brani: list[Brano], vettori: np.ndarray) -> None:
    CARTELLA_INDICE.mkdir(exist_ok=True)
    # Scrive prima in un file temporaneo e poi lo rinomina: se il programma
    # si interrompe a metà, non resta un file salvato incompleto.
    temporaneo = file_salvato.with_suffix(".tmp")
    with open(temporaneo, "wb") as uscita:
        np.savez_compressed(
            uscita,
            vettori=vettori,
            pagine=np.array([brano.pagina for brano in brani]),
            testi=np.array([brano.testo for brano in brani]),
        )
    temporaneo.replace(file_salvato)


def costruisci_indice(
    pdf: list[Path], config: Config, notifica: Callable[[str], None] = print
) -> Indice:
    """Legge tutti i PDF (riusando l'archivio quando possibile) e crea un unico indice.

    `notifica` è la funzione usata per comunicare i progressi: nel Terminale
    è print, nell'interfaccia web sarà un'altra.
    """
    tutti_i_brani: list[Brano] = []
    tutti_i_vettori: list[np.ndarray] = []

    for percorso in pdf:
        file_salvato = CARTELLA_INDICE / f"{impronta(percorso, config)}.npz"
        salvato = leggi_salvato(file_salvato, percorso.name)
        if salvato:
            brani, vettori = salvato
            notifica(f"  {percorso.name}: {len(brani)} brani (già indicizzato)")
        else:
            brani = dividi_in_brani(percorso)
            if not brani:
                notifica(f"  {percorso.name}: nessun testo trovato, lo salto (forse è una scansione?)")
                continue
            notifica(f"  {percorso.name}: {len(brani)} brani, calcolo gli embedding...")
            vettori = calcola_embedding([brano.testo for brano in brani], config)
            salva(file_salvato, brani, vettori)

        tutti_i_brani.extend(brani)
        tutti_i_vettori.append(vettori)

    if not tutti_i_brani:
        raise ValueError("Nessun testo trovato nei PDF indicati.")
    return Indice(tutti_i_brani, np.vstack(tutti_i_vettori))
