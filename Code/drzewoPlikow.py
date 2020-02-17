import sys
import os
import ast
from plik import Plik
import time

class DrzewoPlikow(object):
    slownikSciezek = {}
    def __init__(self):
        korzen = {}
    def __init__(self, sciezka):
        self.korzen = sciezka
        self.stworzDrzewo() # struktura katalogu na dysku
        self.aktualizujWeb = {}

    def stworzDrzewo(self): # funkcja inicjujaca tworzenie struktury katalogu
        self.slownikSciezek=self.slownikP(self.korzen)
        #print(self.slownikSciezek['folder 1'].zawartosc['folder 1_1'].zawartosc['p2.txt'].zawartosc) # przyklad odwolania


    def slownikP(self, sciezka): # funkcja rekurencyjna budujaca strukture katalogu (dicitonary + plik)
        zawartosc=os.listdir(sciezka)
        lista={}
        for i in range (len(zawartosc)):
            if os.path.isdir(sciezka+'\\'+zawartosc[i]):
                lista2={ zawartosc[i].lower() : Plik(1,self.slownikP(sciezka+'\\'+zawartosc[i]))}
                lista.update(lista2)
            else:
                lista2={zawartosc[i].lower() : Plik(0,zawartosc[i])}
                lista.update(lista2)
        return lista

    def aktualizujMetadane(self, sciezka, meta):
        # funkcja ustalajaca metadane dla wybranej sciezki
        plik = self.zwrocPlik(sciezka)
        plik.ustalMeta(meta) # ustawienie metadanych

    def zwrocPlik(self, sciezka):   # zwraca zmienna klasy Plik o okreslonej sciezsce w słowniku
        pozycja = self.slownikSciezek
        sciezka = sciezka.replace('\\','/')
        tmp = (sciezka.lower()).split('/')
        if (tmp[0]==''):
            tmp.pop(0)

        #print('tmp: ',tmp)
        for i in range (0,len(tmp)-1):    # dojscie do odpowiedniego elementu
            if pozycja.get(tmp[i],"brak pliku") != "brak pliku" :
                    pozycja = pozycja[tmp[i]].zawartosc
        pozycja=pozycja[tmp[len(tmp)-1]]
        return pozycja

    def odbierzFunkcjeWeb(self, funkcje):
        self.aktualizujWeb = funkcje
    
    def aktualizuj(self, akcja, sciezka): # funkcja reagujaca na zmiany w katalogu lokalnym

        ACTIONS = {                 # odpowiednik switcha
          1 : self.Created,
          2 : self.Deleted,
          3 : self.Updated,
          4 : "Renamed from something",
          5 : self.Renamed
        }
        
        ACTIONS[akcja](sciezka)

    def Created(self, sciezka):     # stworzenie pliku/ katalogu (lokalnie)

        tmp= (sciezka[0][len(self.korzen)+1:].lower()).split('\\')
        
        nazwa=tmp[len(tmp)-1]
        
        pozycja = self.slownikSciezek
        for i in range (len(tmp)-1):
            pozycja = pozycja[tmp[i]].zawartosc

        if len(nazwa.split('.'))==1:            # jezeli jest to folder
            pusta = {}
            lista={ nazwa : Plik(1, pusta)}
        else:                                   # jezeli jest to plik
            lista={ nazwa : Plik(0,nazwa)}
            
        if pozycja.get(nazwa,0) == 0 :
            pozycja.update(lista)
            time.sleep(0.1) # podejrzewam ze za szybka reakcja po utworzeniu pliku powodowala problem z dostepem, dlatego daje tu sleep
            self.aktualizujWeb(1, sciezka)
        
    def Deleted(self, sciezka):     # usuniecie pliku/katalogu (lokalnie)

        tmp= (sciezka[0][len(self.korzen)+1:].lower()).split('\\')
        
        nazwa=tmp[len(tmp)-1]
        pozycja = self.slownikSciezek
        for i in range (len(tmp)-1):
            pozycja = pozycja[tmp[i]].zawartosc
        if pozycja.get(nazwa,0) != 0:
            pozycja.pop(nazwa)
            self.aktualizujWeb(2, sciezka)
        
    def Updated(self, sciezka):
        #print('U')
        tmp= (sciezka[0][len(self.korzen)+1:].lower()).split('\\')        
        nazwa=tmp[len(tmp)-1]
        if len(nazwa.split('.'))>1:
            self.aktualizujWeb(3, sciezka)
            
    def Renamed(self, sciezka):     # zmiana nazwy pliku/katalogu (lokalnie)

        tmp= (sciezka[0][len(self.korzen)+1:].lower()).split('\\')
        tmp2= (sciezka[1][len(self.korzen)+1:].lower()).split('\\')
        
        stara_nazwa=tmp[len(tmp)-1]
        nowa_nazwa=tmp2[len(tmp2)-1]
        pozycja = self.slownikSciezek

        for i in range (len(tmp)-1):
            pozycja = pozycja[tmp[i]].zawartosc
        pozycja[nowa_nazwa] = pozycja.pop(stara_nazwa)
        self.aktualizujWeb(5, sciezka)

