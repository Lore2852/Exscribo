"""Misura quanto spesso l'app sbaglia, su un insieme di domande di prova.

Uso:
    python valuta.py
    python valuta.py --domande valutazione/domande.json --soglie 0.3 0.4 0.5

Per ogni domanda il modello viene interrogato UNA volta sola, senza soglia.
La soglia decide solo SE chiamare il modello, quindi l'effetto delle varie
soglie si può poi simulare: se il punteggio del brano migliore è sotto la
soglia, l'esito è "non trovato"; altrimenti è quello ottenuto dal modello.
"""

import argparse
import dataclasses
import json
import sys
import time
from datetime import date
from pathlib import Path

from exscribo.archivio import costruisci_indice, elenca_pdf
from exscribo.config import CARTELLA_PROGETTO, carica_config
from exscribo.modelli import ErroreOllama
from exscribo.rag import Risposta, rispondi

# Gli esiti possibili, con un'etichetta leggibile
CORRETTA = "✅ corretta"
NON_TROVATO_CORRETTO = "✅ non trovato (giusto)"
FALSO_NON_TROVATO = "⚠️ falso 'non trovato'"
FONTE_SBAGLIATA = "⚠️ fonte sbagliata"
RISPOSTA_INCOMPLETA = "⚠️ risposta incompleta"
INVENZIONE = "❌ invenzione"

ESITI_GIUSTI = {CORRETTA, NON_TROVATO_CORRETTO}


def contiene_parole(testo: str, parole: list[list[str]]) -> bool:
    """Ogni gruppo deve comparire nel testo con almeno una delle sue alternative.

    Esempio: [["Schleiden", "Schwann"], ["Mazzini"]] significa
    "(Schleiden oppure Schwann) e anche Mazzini".
    """
    testo = testo.lower()
    return all(any(alternativa.lower() in testo for alternativa in gruppo) for gruppo in parole)


def classifica(attesa: dict, risposta: Risposta, punteggio: float, soglia: float) -> str:
    """Confronta la risposta dell'app con quella attesa."""
    trovata = risposta.trovata and punteggio >= soglia

    if not attesa["risposta_attesa"]:
        return NON_TROVATO_CORRETTO if not trovata else INVENZIONE

    if not trovata:
        return FALSO_NON_TROVATO
    citate = {(fonte.file, fonte.pagina) for fonte in risposta.fonti}
    fonti_ok = all((f["file"], f["pagina"]) in citate for f in attesa["fonti"])
    parole_ok = contiene_parole(risposta.testo, attesa["parole"])
    if fonti_ok and parole_ok:
        return CORRETTA
    if parole_ok:
        return FONTE_SBAGLIATA
    return RISPOSTA_INCOMPLETA


def scegli_soglia(riepiloghi: dict[float, dict[str, int]]) -> float:
    """La soglia con più risposte giuste tra quelle senza invenzioni.

    A parità di risultato preferiamo la soglia più alta, cioè la più prudente.
    """
    senza_invenzioni = [s for s, conteggi in riepiloghi.items() if conteggi.get(INVENZIONE, 0) == 0]
    candidate = senza_invenzioni or list(riepiloghi)
    return max(candidate, key=lambda s: (sum(conteggi_giusti(riepiloghi[s])), s))


def conteggi_giusti(conteggi: dict[str, int]) -> list[int]:
    return [n for esito, n in conteggi.items() if esito in ESITI_GIUSTI]


def scrivi_rapporto(percorso, config, pdf, risultati, soglie, riepiloghi, migliore, durata) -> None:
    in_uso = config.soglia_pertinenza
    totale = len(risultati)
    righe = [
        "# Risultati della valutazione",
        "",
        f"- Data: {date.today().isoformat()}",
        f"- Modello per le risposte: `{config.modello_chat}`",
        f"- Modello per gli embedding: `{config.modello_embedding}`",
        f"- Documenti: {', '.join(p.name for p in pdf)}",
        f"- Domande: {totale} ({sum(r['attesa']['risposta_attesa'] for r in risultati)} con risposta "
        f"negli appunti, {sum(not r['attesa']['risposta_attesa'] for r in risultati)} senza)",
        f"- Tempo medio per domanda: {durata / totale:.1f} secondi",
        "",
        "## Riepilogo per soglia di pertinenza",
        "",
        "La soglia è il punteggio minimo del brano più pertinente perché la domanda venga passata al modello.",
        "«Migliore sul test» è calcolata automaticamente: più risposte giuste senza invenzioni e, a parità,",
        "la soglia più alta. «In uso» è la soglia scelta nel file `.env`.",
        "",
        "| Soglia | Risposte giuste | Invenzioni | Falsi \"non trovato\" | Fonte sbagliata | Risposta incompleta |",
        "|---|---|---|---|---|---|",
    ]
    for soglia in soglie:
        c = riepiloghi[soglia]
        giuste = sum(conteggi_giusti(c))
        segno = (" ⬅ migliore sul test" if soglia == migliore else "") + (" (in uso)" if soglia == in_uso else "")
        righe.append(
            f"| {soglia}{segno} | **{giuste}/{totale}** | {c.get(INVENZIONE, 0)} | {c.get(FALSO_NON_TROVATO, 0)} "
            f"| {c.get(FONTE_SBAGLIATA, 0)} | {c.get(RISPOSTA_INCOMPLETA, 0)} |"
        )

    righe += [
        "",
        f"## Dettaglio delle domande (con la soglia in uso: {in_uso})",
        "",
        "| # | Tipo | Domanda | Punteggio | Esito | Risposta dell'app |",
        "|---|---|---|---|---|---|",
    ]
    for numero, r in enumerate(risultati, start=1):
        esito = classifica(r["attesa"], r["risposta"], r["punteggio"], in_uso)
        trovata = r["risposta"].trovata and r["punteggio"] >= in_uso
        testo = r["risposta"].testo if trovata else "Non l'ho trovato nei tuoi appunti."
        if trovata and r["risposta"].fonti:
            testo += " — " + "; ".join(f"{f.file} p.{f.pagina}" for f in r["risposta"].fonti)
        testo = testo.replace("|", "\\|").replace("\n", " ")
        righe.append(
            f"| {numero} | {r['attesa']['tipo']} | {r['attesa']['domanda']} | {r['punteggio']:.3f} | {esito} | {testo} |"
        )

    righe += [
        "",
        "## Legenda degli esiti",
        "",
        f"- **{CORRETTA}**: la risposta contiene le informazioni attese e cita le pagine giuste.",
        f"- **{NON_TROVATO_CORRETTO}**: la risposta non era negli appunti e l'app l'ha detto.",
        f"- **{FALSO_NON_TROVATO}**: la risposta era negli appunti, ma l'app ha detto di non averla trovata.",
        f"- **{FONTE_SBAGLIATA}**: il contenuto è giusto, ma manca almeno una delle pagine attese tra le fonti.",
        f"- **{RISPOSTA_INCOMPLETA}**: mancano alcune delle informazioni attese.",
        f"- **{INVENZIONE}**: l'app ha risposto a una domanda la cui risposta non è negli appunti. È l'errore più grave.",
        "",
    ]
    percorso.write_text("\n".join(righe), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Valuta l'app su un insieme di domande di prova.")
    parser.add_argument("--domande", type=Path, default=CARTELLA_PROGETTO / "valutazione" / "domande.json")
    parser.add_argument("--uscita", type=Path, default=CARTELLA_PROGETTO / "valutazione" / "risultati.md")
    parser.add_argument("--soglie", type=float, nargs="+", default=[0.3, 0.35, 0.4, 0.45, 0.5])
    args = parser.parse_args()

    insieme = json.loads(args.domande.read_text(encoding="utf-8"))
    config = carica_config()
    # Il modello viene sempre interrogato: le soglie le simuliamo dopo
    config_senza_soglia = dataclasses.replace(config, soglia_pertinenza=float("-inf"))
    soglie = sorted(set(args.soglie) | {config.soglia_pertinenza})

    try:
        pdf = elenca_pdf([CARTELLA_PROGETTO / p for p in insieme["documenti"]])
        print(f"Preparo {len(pdf)} PDF:")
        indice = costruisci_indice(pdf, config)

        risultati = []
        inizio = time.monotonic()
        for numero, attesa in enumerate(insieme["domande"], start=1):
            print(f"[{numero:2}/{len(insieme['domande'])}] {attesa['domanda']}", flush=True)
            risposta = rispondi(attesa["domanda"], indice, config_senza_soglia)
            risultati.append({"attesa": attesa, "risposta": risposta, "punteggio": risposta.brani[0][1]})
        durata = time.monotonic() - inizio
    except (ErroreOllama, FileNotFoundError, ValueError) as errore:
        print(f"\nErrore: {errore}", file=sys.stderr)
        return 1

    riepiloghi = {}
    for soglia in soglie:
        conteggi: dict[str, int] = {}
        for r in risultati:
            esito = classifica(r["attesa"], r["risposta"], r["punteggio"], soglia)
            conteggi[esito] = conteggi.get(esito, 0) + 1
        riepiloghi[soglia] = conteggi
    migliore = scegli_soglia(riepiloghi)

    print("\nSoglia | giuste | invenzioni | falsi 'non trovato' | fonte sbagliata | incomplete")
    for soglia in soglie:
        c = riepiloghi[soglia]
        segno = "  <- migliore sul test" if soglia == migliore else ""
        attuale = "  (in uso, dal tuo .env)" if soglia == config.soglia_pertinenza else ""
        print(
            f" {soglia:<5} | {sum(conteggi_giusti(c)):>2}/{len(risultati)}  | {c.get(INVENZIONE, 0):>10} "
            f"| {c.get(FALSO_NON_TROVATO, 0):>19} | {c.get(FONTE_SBAGLIATA, 0):>15} "
            f"| {c.get(RISPOSTA_INCOMPLETA, 0):>10}{segno}{attuale}"
        )

    args.uscita.parent.mkdir(parents=True, exist_ok=True)
    scrivi_rapporto(args.uscita, config, pdf, risultati, soglie, riepiloghi, migliore, durata)
    print(f"\nRapporto completo salvato in {args.uscita}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
