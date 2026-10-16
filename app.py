"""Interfaccia web di Exscribo.

Avvio:  streamlit run app.py
Poi si apre il browser su http://localhost:8501 (solo sul tuo computer).

Come funziona Streamlit: a ogni interazione (un clic, una domanda) rilegge
questo file dall'inizio alla fine e ridisegna la pagina. Per non rifare
ogni volta il lavoro lento usiamo la cache (@st.cache_resource) e
ricordiamo l'ultima risposta in st.session_state.
"""

from pathlib import Path

import streamlit as st

from exscribo.archivio import costruisci_indice, elenca_pdf
from exscribo.config import CARTELLA_PROGETTO, Config, carica_config
from exscribo.modelli import ErroreOllama
from exscribo.rag import MESSAGGIO_NON_TROVATO, rispondi
from exscribo.ricerca import Indice

CARTELLA_DOCUMENTI = CARTELLA_PROGETTO / "documenti"
CARTELLE = {
    "I miei documenti (documenti/)": CARTELLA_DOCUMENTI,
    "Esempi (esempi/)": CARTELLA_PROGETTO / "esempi",
}

st.set_page_config(page_title="Exscribo", page_icon="📚")


@st.cache_resource(show_spinner=False)
def prepara_indice(chiave: tuple, _pdf: list[Path], _config: Config) -> tuple[Indice, list[str]]:
    """Costruisce l'indice e restituisce anche i messaggi di avanzamento.

    Streamlit ricalcola questa funzione solo quando cambia `chiave`, che
    contiene nome, data di modifica e dimensione di ogni PDF: se aggiungi o
    modifichi un file, l'indice viene aggiornato. I parametri che iniziano
    con "_" non fanno parte della chiave.
    """
    messaggi: list[str] = []
    indice = costruisci_indice(_pdf, _config, notifica=lambda testo: messaggi.append(testo.strip()))
    return indice, messaggi


def salva_caricati(file_caricati) -> None:
    """Salva in documenti/ i PDF caricati dal browser."""
    for file in file_caricati:
        # Path(...).name tiene solo il nome del file: un nome malevolo come
        # "../../qualcosa.pdf" non può far scrivere fuori dalla cartella.
        destinazione = CARTELLA_DOCUMENTI / Path(file.name).name
        contenuto = file.getvalue()
        if not destinazione.exists() or destinazione.read_bytes() != contenuto:
            CARTELLA_DOCUMENTI.mkdir(exist_ok=True)
            destinazione.write_bytes(contenuto)


def mostra_risposta(domanda: str, risposta, debug: bool) -> None:
    st.markdown(f"**Domanda:** {domanda}")

    if not risposta.trovata:
        st.warning(MESSAGGIO_NON_TROVATO, icon="🔍")
        if debug:
            st.caption(f"Motivo: {risposta.motivo}")
            if risposta.testo_modello:
                st.caption(f"Il modello aveva scritto: {risposta.testo_modello}")
    else:
        st.success(risposta.testo)
        st.markdown("**Fonti** (clicca per leggere l'estratto)")
        for fonte in risposta.fonti:
            numeri = "".join(f"[{n}]" for n in fonte.estratti)
            with st.expander(f"{numeri} {fonte.file}, pagina {fonte.pagina}"):
                for numero in fonte.estratti:
                    brano = risposta.brani[numero - 1][0]
                    st.markdown(f"> {brano.testo}")

    if debug:
        with st.expander("Debug: brani trovati e punteggi", expanded=True):
            for numero, (brano, punteggio) in enumerate(risposta.brani, start=1):
                st.markdown(f"`[{numero}]` **{punteggio:.3f}** · {brano.file} p.{brano.pagina} · {brano.testo[:80]}…")


# --- Barra laterale: scelta dei documenti ---------------------------------

with st.sidebar:
    st.header("📂 Documenti")
    caricati = st.file_uploader(
        "Carica nuovi PDF (verranno salvati in documenti/)", type="pdf", accept_multiple_files=True
    )
    if caricati:
        salva_caricati(caricati)

    # Di base selezioniamo le cartelle che contengono almeno un PDF
    con_pdf = [nome for nome, cartella in CARTELLE.items() if cartella.is_dir() and elenca_pdf([cartella])]
    scelte = st.multiselect("Cerca in", list(CARTELLE), default=con_pdf)
    debug = st.toggle("Modalità debug", help="Mostra punteggi dei brani e motivi del 'non trovato'")

try:
    config = carica_config()
except ValueError as errore:
    st.error(f"Errore nella configurazione: {errore}")
    st.stop()

pdf = elenca_pdf([CARTELLE[nome] for nome in scelte if CARTELLE[nome].is_dir()])

with st.sidebar:
    if pdf:
        st.caption(f"{len(pdf)} PDF selezionati:")
        st.markdown("\n".join(f"- {p.name}" for p in pdf))

# --- Pagina principale ----------------------------------------------------

st.title("📚 Exscribo")
st.caption("Chiedi ai tuoi appunti: risposte basate solo sui tuoi PDF, con file e pagina.")

if not pdf:
    st.info("Nessun PDF selezionato. Carica dei PDF o scegli una cartella nella barra laterale.")
    st.stop()

chiave = (config.modello_embedding,) + tuple((str(p), p.stat().st_mtime, p.stat().st_size) for p in pdf)
try:
    with st.spinner("Preparo i documenti (la prima volta può volerci un po')..."):
        indice, messaggi = prepara_indice(chiave, pdf, config)
except ErroreOllama as errore:
    st.error(f"Problema con Ollama: {errore}")
    st.stop()
except ValueError as errore:
    st.error(str(errore))
    st.stop()

with st.sidebar.expander("Dettagli indicizzazione"):
    st.text("\n".join(messaggi))

# Un "form" fa partire la domanda sia con il pulsante sia premendo Invio
with st.form("domanda"):
    domanda = st.text_input("La tua domanda", placeholder="Es. Quali sono le fasi della mitosi?")
    inviata = st.form_submit_button("Chiedi", type="primary")

if inviata and domanda.strip():
    try:
        with st.spinner("Cerco negli appunti e preparo la risposta..."):
            st.session_state["ultima"] = (domanda.strip(), rispondi(domanda.strip(), indice, config))
    except ErroreOllama as errore:
        st.error(f"Problema con Ollama: {errore}")

# La risposta resta visibile anche quando cambi un'opzione (es. la modalità debug)
if "ultima" in st.session_state:
    mostra_risposta(*st.session_state["ultima"], debug=debug)
