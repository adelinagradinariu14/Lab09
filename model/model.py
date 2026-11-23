from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO
from model import escursione
from model.escursione import Escursione


class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        # TODO
        # Il DAO restituisce una lista di dizionari, uno per ogni riga della
        # tabella ponte: {"id_escursione": ..., "id_punto_interesse": ...}

        relazioni = EscursioneDAO.get_escursioni_punti_interesse()
        if relazioni: # cosi gestisco nel caso il database non giri -> None
            for riga in relazioni:
                # l'id preso dalla riga fa da chiave per il dizionario corrispondente
                escursione = self.escursioni_map[riga["id_escursione"]]
                punto_interesse = self.punti_interesse_map[riga["id_punto_interesse"]]

                # Collegamento nelle due direzioni (relazione N:N)
                # 1) il punto di interesse "sa" in quali escursioni compare
                punto_interesse.escursioni.add(escursione)
                # 2) l'escursione "sa" quali punti di interesse include
                escursione.punti_interesse.add(punto_interesse)


    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        # 1. RESET DELLE SOLUZIONI OTTIME
        # Fondamentale: ogni volta che l'utente clicca il bottone nell'interfaccia,
        # azzero i risultati della ricerca precedente prima di far partire la nuova.

        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        # TODO

        # I parametri max_giorni e max_budget sono variabili locali di genera_pacchetto.
        # salvo i limiti come attributi di self per renderli accessibili a _ricorsione
        self._max_giorni = max_giorni
        self._max_budget = max_budget

        # filtro i dati prendendo solo le escursioni del parco scelto
        self._lista_escursioni_per_parco = []                         # 1) lista vuota prima del ciclo
        for escursione in self.escursioni_map.values():     # 2) scorro gli OGGETTI, non le chiavi
            if escursione.id_parco == id_parco:           # 3) guardo un attributo dell'oggetto
                self._lista_escursioni_per_parco.append(escursione)   # 4) tengo solo quelli giusti

        # chiamata iniziale alla ricorsione con parametri di partenza a zero / vuoti
        self._ricorsione(0, [], 0, 0.0, 0, set())

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""
        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno

        # 🟤 A - ISTRUZIONI SEMPRE ESEGUITE (Aggiornamento soluzione ottima)
        # ogni volta che entro in _ricorsione, pacchetto_parziale è già una combinazione VALIDA
        # (perché i vincoli li controllo prima della chiamata).
        # Verifico se il punteggio attuale batte il record salvato finora:
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            # OBBLIGATORIO .copy(): pacchetto_parziale viene modificato e svuotato dal backtracking (.pop()).
            # Senza .copy() copierei solo il riferimento e alla fine self._pacchetto_ottimo risulterebbe vuoto
            self._pacchetto_ottimo = pacchetto_parziale.copy()
            self._costo = costo_corrente  # salvataggio del costo del pacchetto migliore

        # 🟢 B - CONDIZIONE TERMINALE
        # non serve un if di uscita esplicito perchè quando start_index raggiunge la lunghezza
        # della lista, il ciclo for non esegue iterazioni e la ricorsione risale naturalmente.

        # CICLO SULLE SCELTE POSSIBILI (combinazioni senza ripetizioni)
        # parto da start_index (e non da 0) per esplorare solo le escursioni successive a quelle
        # già valutate -> così evito duplicati della stessa escursione e non genero gli stessi
        # pacchetti in ordine diverso (es. [A, B] e [B, A]).

        for i in range(start_index, len(self._lista_escursioni_per_parco)): # uso gli indici al posto di scorrere gli elementi
            e = self._lista_escursioni_per_parco[i]

            # 🟡 C - CONTROLLO DEI VINCOLI
            # gestione limiti None
            # se self._max_giorni is None è True, Python non valuta la seconda parte ed evita il TypeError.
            ok_giorni = (self._max_giorni is None) or (durata_corrente + e.durata_giorni <= self._max_giorni)
            ok_budget = (self._max_budget is None) or (costo_corrente + e.costo <= self._max_budget)

            if ok_giorni and ok_budget:
                # Controllo punti di interesse unici tramite insiemi (set):
                # .intersection() restituisce un set con gli elementi in comune
                # in Python un set vuoto vale False, mentre un set con almeno un elemento vale True.
                # -> 'not ...intersection(...)' è True solo se NON ci sono punti di interesse in comune.
                if not punti_usati.intersection(e.punti_interesse): # oppure len(punti_usati.intersection(e.punti_interesse)) == 0
                    # 🔵 D - CALCOLO NUOVO STATO PARZIALE
                    # calcolo il punteggio portato dai punti di interesse dell'escursione 'e'

                    voto_e = 0
                    for p in e.punti_interesse:
                        voto_e += p.voto_visitatori

                    # creo un NUOVO set con .union() invece di modificare punti_usati sul posto:
                    # in questo modo ogni ramo della ricorsione ha il suo insieme indipendente
                    # e non devo fare manualmente backtracking sul set
                    nuovi_punti = punti_usati.union(e.punti_interesse)

                    pacchetto_parziale.append(e)

                    # 🔴 E - CHIAMATA RICORSIVA
                    # passo i + 1 (NON start_index + 1!) per proseguire solo con le escursioni
                    # successive a quella appena scelta in posizione i
                    self._ricorsione(
                        i+1,
                        pacchetto_parziale,
                        durata_corrente + e.durata_giorni,
                        costo_corrente + e.costo,
                        valore_corrente + voto_e,
                        nuovi_punti)

                    # 🟣 F - BACKTRACKING
                    # rimuovo l'ultima escursione aggiunta per "pulire" pacchetto_parziale
                    # prima di provare la prossima escursione nel ciclo for
                    pacchetto_parziale.pop()



