"""Ricerca dei brani più pertinenti a una domanda."""

import numpy as np

from exscribo.config import Config
from exscribo.modelli import calcola_embedding
from exscribo.pdf import Brano


class Indice:
    """Tiene insieme i brani e i loro vettori, e permette di cercarli."""

    def __init__(self, brani: list[Brano], vettori: np.ndarray):
        self.brani = brani
        self.vettori = vettori  # una riga per brano, nello stesso ordine

    def cerca(self, domanda: str, config: Config, quanti: int = 4) -> list[tuple[Brano, float]]:
        """Restituisce i `quanti` brani più simili alla domanda, con il loro punteggio.

        Il punteggio è la "similarità del coseno": va da -1 a 1, e più è alto
        più il brano parla della stessa cosa della domanda.
        """
        vettore_domanda = calcola_embedding([domanda], config)[0]
        # Con vettori normalizzati, la similarità del coseno è un prodotto scalare:
        # questa riga confronta la domanda con tutti i brani in un colpo solo.
        punteggi = self.vettori @ vettore_domanda
        migliori = np.argsort(punteggi)[::-1][:quanti]
        return [(self.brani[i], float(punteggi[i])) for i in migliori]
