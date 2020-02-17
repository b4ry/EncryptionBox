import sys
import os.path
import threading
from drzewoPlikow import DrzewoPlikow
from watcher import Watcher

class MainDirectory(object):
    def __init__(self):
        self.sciezka = os.path.expanduser('~')+'\szyfrBox'
        self.drzewo = DrzewoPlikow(self.sciezka)
        self.funkcjeWeb = {}
        self.straznik = Watcher(self.sciezka, self.AktualizujDrzewo)
        threading.Thread(target=self.straznik.start).start() # wątek obserwujacy katalog lokalny
        

    def wyswietlSciezke(self):
        print(self.sciezka)

    def zmienSciezke(self, sciezka):    # dorobic opcje w GUI
        self.sciezka=sciezka

    def stworzNaDysku(self):
        if not os.path.exists(self.sciezka):
            os.makedirs(self.sciezka)
            print('stworzono folder '+ self.sciezka)
        else:
            print('folder ' + self.sciezka + ' istnieje na dysku')
        
    def AktualizujDrzewo(self, akcja, sciezka):
        self.drzewo.aktualizuj(akcja, sciezka)

    def WyslijFunkcjeWeb(self, funkcje):
        self.drzewo.odbierzFunkcjeWeb(funkcje)
    
if __name__ == "__main__":

    x= MainDirectory()

