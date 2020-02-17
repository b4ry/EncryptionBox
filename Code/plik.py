import sys
import os.path

# klasa lokalnej reprezentacji pliku
class Plik(object):
    def __init__(self,isDict,zawartosc, meta={'rev': '0'}, klucz={}): #kolejno sciezka pliku, czy jest folderem, co jest wewnatrz (slownik czy nazwa)
        self.isDict = isDict
        self.zawartosc = zawartosc
        self.meta= meta
        self.klucz = klucz

    def ustalKlucz(self,klucz):
        self.klucz = klucz

    def ustalMeta(self, meta):
        self.meta= meta

    def zmienZawartosc(self, zawartosc):
        self.zawartosc = zawartosc
