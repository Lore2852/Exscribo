"""Gestione e verifica delle citazioni [1], [2], ... nelle risposte del modello.

I modelli piccoli non sono affidabili nel citare: a volte dimenticano la
citazione, a volte ne mettono una sbagliata. Per questo non ci fidiamo
ciecamente: per ogni frase controlliamo che le sue parole importanti
compaiano davvero nell'estratto citato.
"""

import re
from dataclasses import dataclass

from exscribo.pdf import Brano

# Riconosce le citazioni nel testo del modello: [1], [1, 2] e anche [Estratto 1],
# perché i modelli piccoli non sempre rispettano il formato alla lettera.
# Solo numeri di 1-2 cifre: così, per esempio, un anno come [2006] non viene toccato.
CITAZIONE = re.compile(r"\[(?:estratto\s*)?(\d{1,2}(?:\s*,\s*\d{1,2})*)\]", re.IGNORECASE)

# Quota minima di parole importanti di una frase che devono trovarsi nell'estratto
# perché la citazione sia considerata valida (0.5 = almeno la metà).
SOGLIA_SUPPORTO = 0.5

# Parole molto comuni che non dicono nulla sul contenuto di una frase
PAROLE_VUOTE = {
    "che", "per", "con", "del", "della", "delle", "dei", "degli", "dal", "dalla", "dai",
    "nel", "nella", "nelle", "nei", "negli", "sul", "sulla", "sui", "una", "uno", "gli",
    "non", "sono", "alla", "alle", "agli", "allo", "come", "anche", "più", "questo",
    "questa", "questi", "queste", "quello", "quella", "ogni", "tra", "fra", "suo", "sua",
    "loro", "essere", "viene", "vengono", "hanno", "cui", "dove", "quando", "quale",
    "quali", "circa", "mentre", "però", "infatti", "inoltre", "cioè", "ovvero",
}


@dataclass
class Fonte:
    """Una pagina citata nella risposta."""

    file: str
    pagina: int
    estratti: list[int]  # i numeri degli estratti citati che vengono da questa pagina


def sistema_citazioni(testo: str, quanti_estratti: int) -> str:
    """Uniforma le citazioni a [1][2] e toglie quelle con numeri inesistenti."""

    def sostituisci(corrispondenza: re.Match) -> str:
        numeri = [int(n) for n in corrispondenza.group(1).split(",")]
        validi = [n for n in numeri if 1 <= n <= quanti_estratti]
        return "".join(f"[{n}]" for n in validi)

    testo = CITAZIONE.sub(sostituisci, testo)
    # Sposta prima del punto le citazioni messe dopo: "frase. [1]" -> "frase [1]."
    # Un'eventuale punteggiatura ripetuta dopo la citazione ("frase... [1].") viene tolta.
    testo = re.sub(r"([.!?]+)[ \t]*((?:\[\d{1,2}\])+)[.!?]*", r" \2\1", testo)
    return pulisci_spazi(testo)


def pulisci_spazi(testo: str) -> str:
    testo = re.sub(r"(?<=\S) {2,}", " ", testo)  # doppi spazi in mezzo alla riga
    testo = re.sub(r" +$", "", testo, flags=re.MULTILINE)  # spazi a fine riga
    return re.sub(r" +([.,;:!?])", r"\1", testo)  # spazio prima della punteggiatura


def parole_chiave(testo: str) -> set[str]:
    """Le parole che contano in un testo, ridotte alle prime 6 lettere.

    Tagliare a 6 lettere fa coincidere forme diverse della stessa parola
    ("molecola" e "molecole" diventano entrambe "moleco").
    """
    parole = re.findall(r"\w+", testo.lower())
    return {
        parola[:6]
        for parola in parole
        if (len(parola) >= 3 and parola not in PAROLE_VUOTE) or any(c.isdigit() for c in parola)
    }


def supporto(frase: set[str], estratto: set[str]) -> float:
    """Che frazione delle parole chiave della frase compare nell'estratto (da 0 a 1)."""
    return len(frase & estratto) / len(frase) if frase else 0.0


def verifica_frase(frase: str, parole_estratti: list[set[str]]) -> str:
    """Tiene solo le citazioni che reggono, e ne aggiunge una se manca."""
    citati = list(dict.fromkeys(int(n) for n in re.findall(r"\[(\d{1,2})\]", frase)))
    nuda = pulisci_spazi(re.sub(r"\[\d{1,2}\]", "", frase))
    parole = parole_chiave(nuda)
    if not parole:
        return nuda

    punteggi = {numero: supporto(parole, p) for numero, p in enumerate(parole_estratti, start=1)}
    validi = [n for n in citati if punteggi[n] >= SOGLIA_SUPPORTO]
    # Se il modello non ha citato nulla di valido, cerchiamo noi l'estratto giusto,
    # ma solo per frasi con almeno 2 parole chiave: una parola sola è un indizio troppo debole.
    if not validi and len(parole) >= 2:
        migliore = max(punteggi, key=punteggi.get)
        if punteggi[migliore] >= SOGLIA_SUPPORTO:
            validi = [migliore]
    if not validi:
        return nuda

    # Rimette le citazioni prima della punteggiatura finale della frase
    corpo, finale = re.match(r"(.*?)([.!?:;]*)$", nuda, flags=re.DOTALL).groups()
    return f"{corpo} " + "".join(f"[{n}]" for n in validi) + finale


def verifica_citazioni(testo: str, brani: list[tuple[Brano, float]]) -> str:
    """Applica verifica_frase a ogni frase della risposta, riga per riga."""
    parole_estratti = [parole_chiave(brano.testo) for brano, _ in brani]
    righe = []
    for riga in testo.split("\n"):
        frasi = re.split(r"(?<=[.!?])\s+", riga)
        righe.append(" ".join(verifica_frase(frase, parole_estratti) for frase in frasi))
    return "\n".join(righe)


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
