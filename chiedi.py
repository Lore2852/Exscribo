"""Fai domande a un PDF dei tuoi appunti, dal Terminale.

Esempi:
    python chiedi.py esempi/appunti_biologia.pdf
    python chiedi.py esempi/appunti_biologia.pdf "Quali sono le fasi della mitosi?"
    python chiedi.py esempi/appunti_biologia.pdf --debug
"""

import argparse
import sys
from pathlib import Path

from exscribo.config import carica_config
from exscribo.modelli import ErroreOllama
from exscribo.pdf import dividi_in_brani
from exscribo.rag import rispondi
from exscribo.ricerca import Indice


PAROLE_PER_USCIRE = {"esci", "stop", "quit", "exit"}


def stampa_risposta(domanda, indice, config, debug):
    risposta = rispondi(domanda, indice, config)
    if debug:
        print("\nBrani trovati (numero, punteggio, pagina, inizio del testo):")
        for numero, (brano, punteggio) in enumerate(risposta.brani, start=1):
            print(f"  [{numero}]  {punteggio:.3f}  p.{brano.pagina}  {brano.testo[:70]}...")
    print(f"\n{risposta.testo}")

    if risposta.fonti:
        print("\nFonti:")
        for fonte in risposta.fonti:
            numeri = "".join(f"[{n}]" for n in fonte.estratti)
            print(f"  {numeri} {fonte.file}, pagina {fonte.pagina}")
    else:
        pagine = sorted({brano.pagina for brano, _ in risposta.brani})
        print(f"\nFonti: nessuna fonte verificata (pagine consultate: {', '.join(map(str, pagine))})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fai domande a un PDF dei tuoi appunti.")
    parser.add_argument("pdf", type=Path, help="percorso del file PDF")
    parser.add_argument("domanda", nargs="?", help="la domanda (se manca, puoi farne quante vuoi)")
    parser.add_argument("--debug", action="store_true", help="mostra i brani trovati e il loro punteggio")
    args = parser.parse_args()

    if not args.pdf.is_file():
        print(f"File non trovato: {args.pdf}", file=sys.stderr)
        return 1

    config = carica_config()
    try:
        print(f"Leggo {args.pdf.name}...")
        brani = dividi_in_brani(args.pdf)
        if not brani:
            print("Non ho trovato testo nel PDF (forse è una scansione, cioè un'immagine?).", file=sys.stderr)
            return 1
        print(f"Ho diviso il testo in {len(brani)} brani. Li indicizzo con {config.modello_embedding}...")
        indice = Indice.costruisci(brani, config)

        if args.domanda:
            stampa_risposta(args.domanda, indice, config, args.debug)
            return 0

        print("Pronto! Scrivi una domanda e premi Invio (per uscire: riga vuota oppure 'esci').")
        while True:
            try:
                domanda = input("\nDomanda: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not domanda or domanda.lower() in PAROLE_PER_USCIRE:
                break
            stampa_risposta(domanda, indice, config, args.debug)
    except ErroreOllama as errore:
        print(f"\nErrore: {errore}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
