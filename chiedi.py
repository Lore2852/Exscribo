"""Fai domande ai tuoi appunti in PDF, dal Terminale.

Esempi:
    python chiedi.py esempi/
    python chiedi.py documenti/ esempi/appunti_storia.pdf
    python chiedi.py esempi/ "Chi guidò la spedizione dei Mille?"
    python chiedi.py esempi/ --debug
"""

import argparse
import sys
from pathlib import Path

from exscribo.archivio import costruisci_indice, elenca_pdf
from exscribo.config import carica_config
from exscribo.modelli import ErroreOllama
from exscribo.rag import rispondi

PAROLE_PER_USCIRE = {"esci", "stop", "quit", "exit"}


def stampa_risposta(domanda, indice, config, debug):
    risposta = rispondi(domanda, indice, config)
    if debug:
        print("\nBrani trovati (numero, punteggio, file e pagina, inizio del testo):")
        for numero, (brano, punteggio) in enumerate(risposta.brani, start=1):
            print(f"  [{numero}]  {punteggio:.3f}  {brano.file} p.{brano.pagina}  {brano.testo[:50]}...")
    print(f"\n{risposta.testo}")

    if not risposta.trovata:
        if debug:
            print(f"\n(Motivo: {risposta.motivo})")
            if risposta.testo_modello:
                print(f"(Il modello aveva scritto: {risposta.testo_modello})")
        return

    print("\nFonti:")
    for fonte in risposta.fonti:
        numeri = "".join(f"[{n}]" for n in fonte.estratti)
        print(f"  {numeri} {fonte.file}, pagina {fonte.pagina}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fai domande ai tuoi appunti in PDF.")
    parser.add_argument("percorsi", nargs="+", help="file PDF e/o cartelle che contengono PDF")
    parser.add_argument("--domanda", "-d", help="una sola domanda (se manca, puoi farne quante vuoi)")
    parser.add_argument("--debug", action="store_true", help="mostra i brani trovati e il loro punteggio")
    args = parser.parse_args()

    # Per comodità accettiamo anche la domanda scritta in fondo senza --domanda:
    # python chiedi.py esempi/ "Chi guidò la spedizione dei Mille?"
    # Ma se l'ultimo argomento sembra un percorso scritto male, lasciamo che dia errore.
    ultimo = args.percorsi[-1]
    sembra_percorso = ultimo.lower().endswith((".pdf", "/"))
    if not args.domanda and len(args.percorsi) > 1 and not Path(ultimo).exists() and not sembra_percorso:
        args.domanda = args.percorsi.pop()

    try:
        config = carica_config()
        pdf = elenca_pdf([Path(percorso) for percorso in args.percorsi])
    except (ValueError, FileNotFoundError) as errore:
        print(f"Errore: {errore}", file=sys.stderr)
        return 1
    if not pdf:
        print("Non ho trovato nessun PDF nei percorsi indicati.", file=sys.stderr)
        return 1

    try:
        print(f"Preparo {len(pdf)} PDF (modello per gli embedding: {config.modello_embedding}):")
        indice = costruisci_indice(pdf, config)

        if args.domanda:
            stampa_risposta(args.domanda, indice, config, args.debug)
            return 0

        print(f"\nPronto! {len(indice.brani)} brani in totale.")
        print("Scrivi una domanda e premi Invio (per uscire: riga vuota oppure 'esci').")
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
    except ValueError as errore:
        print(f"\nErrore: {errore}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
