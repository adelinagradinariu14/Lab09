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
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        # TODO
        self._lista_escursioni_per_parco = []                         # 1) lista vuota prima del ciclo
        for escursione in self.escursioni_map.values():     # 2) scorro gli OGGETTI, non le chiavi
            if escursione.id_parco == id_parco:           # 3) guardo un attributo dell'oggetto
                self._lista_escursioni_per_parco.append(escursione)   # 4) tengo solo quelli giusti

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno

        for e in self._lista_escursioni_per_parco:
            if (durata_corrente + e.durata_giorni <= self.max_giorni) and (costo_corrente + e.costo <= self.max_budget):

                voto_e = 0
                for p in e.punti_interesse:
                    voto_e += p.voto_visitatori

                nuovi_punti = punti_usati.union(e.punti_interesse)
                pacchetto_parziale.append(e)
                self._ricorsione(start_index, pacchetto_parziale, durata_corrente + e.durata_giorni, costo_corrente + e.costo, valore_corrente + voto_e, nuovi_punti)
                pacchetto_parziale.pop()



