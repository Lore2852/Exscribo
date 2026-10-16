"""Il cuore dell'app: cerca i brani giusti e chiede al modello di rispondere."""

from dataclasses import dataclass

from exscribo.citazioni import Fonte, sistema_citazioni, trova_fonti, verifica_citazioni
from exscribo.config import Config
from exscribo.modelli import genera_risposta
from exscribo.pdf import Brano
from exscribo.ricerca import Indice

MESSAGGIO_NON_TROVATO = "Non l'ho trovato nei tuoi appunti."

# La "parola d'ordine" con cui il modello segnala che la risposta non c'è.
# Una parola fissa è molto più facile da riconoscere di una frase libera.
SEGNALE_NON_TROVATO = "NON_TROVATO"

ISTRUZIONI = f"""Sei un assistente che aiuta uno studente a ripassare i suoi appunti.
Ti verranno dati alcuni estratti numerati degli appunti e una domanda.

Regole:
- Rispondi in italiano usando SOLO le informazioni contenute negli estratti.
- Non usare conoscenze esterne e non inventare nulla.
- Alla fine di ogni frase scrivi tra parentesi quadre il numero dell'estratto da cui viene l'informazione.
- Se gli estratti non contengono la risposta, scrivi soltanto: {SEGNALE_NON_TROVATO}
- Rispondi in modo chiaro e conciso."""

# Esempi svolti ("few-shot"): finte domande con la risposta corretta.
# I modelli piccoli imitano un esempio concreto meglio di quanto seguano una regola.
# L'argomento è volutamente diverso dagli appunti, così il modello non lo confonde con essi.
ESTRATTI_ESEMPIO = """Estratti dagli appunti:

[1]
Il Po è il fiume più lungo d'Italia: nasce dal Monviso e sfocia nel mare Adriatico dopo circa 652 km.

[2]
Il lago di Garda è il lago più grande d'Italia, con una superficie di circa 370 km quadrati."""

ESEMPI = [
    # Esempio 1: la risposta c'è, con le citazioni al posto giusto
    (f"{ESTRATTI_ESEMPIO}\n\nDomanda: Quanto è lungo il Po e dove sfocia?",
     "Il Po è lungo circa 652 km [1]. Sfocia nel mare Adriatico [1]."),
    # Esempio 2: la risposta NON c'è (anche se il modello la conosce: il Monte Bianco)
    (f"{ESTRATTI_ESEMPIO}\n\nDomanda: Qual è la montagna più alta d'Italia?",
     SEGNALE_NON_TROVATO),
]


@dataclass
class Risposta:
    testo: str
    fonti: list[Fonte]
    brani: list[tuple[Brano, float]]  # i brani passati al modello, con il punteggio
    trovata: bool = True
    motivo: str = ""  # se non trovata: quale difesa è scattata e perché
    testo_modello: str = ""  # cosa aveva scritto il modello (utile per capire gli errori)


def costruisci_messaggi(domanda: str, brani: list[tuple[Brano, float]]) -> list[dict]:
    """Prepara i messaggi per il modello: istruzioni, esempi svolti, estratti e domanda."""
    messaggi = [{"role": "system", "content": ISTRUZIONI}]
    for domanda_esempio, risposta_esempio in ESEMPI:
        messaggi.append({"role": "user", "content": domanda_esempio})
        messaggi.append({"role": "assistant", "content": risposta_esempio})

    estratti = "\n\n".join(f"[{numero}]\n{brano.testo}" for numero, (brano, _) in enumerate(brani, start=1))
    messaggi.append({"role": "user", "content": f"Estratti dagli appunti:\n\n{estratti}\n\nDomanda: {domanda}"})
    return messaggi


def non_trovata(brani: list[tuple[Brano, float]], motivo: str, testo_modello: str = "") -> Risposta:
    return Risposta(
        testo=MESSAGGIO_NON_TROVATO, fonti=[], brani=brani,
        trovata=False, motivo=motivo, testo_modello=testo_modello,
    )


def rispondi(domanda: str, indice: Indice, config: Config, quanti: int = 4) -> Risposta:
    brani = indice.cerca(domanda, config, quanti)

    # Difesa 1: se nemmeno il brano migliore è abbastanza pertinente, la domanda
    # è fuori tema. Non chiediamo nulla al modello, così non può inventare.
    punteggio_migliore = brani[0][1]
    if punteggio_migliore < config.soglia_pertinenza:
        return non_trovata(
            brani,
            f"punteggio del brano migliore ({punteggio_migliore:.3f}) "
            f"sotto la soglia ({config.soglia_pertinenza})",
        )

    testo_modello = genera_risposta(costruisci_messaggi(domanda, brani), config)

    # Difesa 2: il modello stesso dice che gli estratti non contengono la risposta.
    # Accettiamo anche "NON TROVATO" con lo spazio, per tolleranza.
    if SEGNALE_NON_TROVATO in testo_modello.upper().replace(" ", "_"):
        return non_trovata(brani, "il modello ha segnalato che gli estratti non contengono la risposta", testo_modello)

    testo = verifica_citazioni(sistema_citazioni(testo_modello, len(brani)), brani)
    fonti = trova_fonti(testo, brani)

    # Difesa 3: se nessuna frase della risposta è supportata dagli estratti,
    # la risposta probabilmente viene dalla "memoria" del modello: la scartiamo.
    if not fonti:
        return non_trovata(brani, "nessuna frase della risposta è supportata dagli estratti", testo_modello)

    return Risposta(testo=testo, fonti=fonti, brani=brani, testo_modello=testo_modello)
