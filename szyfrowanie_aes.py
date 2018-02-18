from Crypto.Cipher import AES
from Crypto import Random

import os
import struct

class Block_AES:

##################################################################################################################################################################################################
    def __init__(self, klucz):
        self.klucz = klucz

##################################################################################################################################################################################################
    def szyfrowanie(self, plik_wejsciowy, plik_wyjsciowy = None, rozmiar_bloku=64*1024):

        if not plik_wyjsciowy:
            plik_wyjsciowy = os.path.splitext(plik_wejsciowy)[0] + '.enc'

        iv = Random.get_random_bytes(16)
        encryptor = AES.new(self.klucz, AES.MODE_CBC, iv)
        rozmiar_pliku = os.path.getsize(plik_wejsciowy)

        with open(plik_wejsciowy, 'rb') as wejsciowy:
            with open(plik_wyjsciowy, 'wb') as wyjsciowy:
                wyjsciowy.write(struct.pack('<Q', rozmiar_pliku)) # zapisanie do pliku informacji o rozmiarze pliku, aby przy deszyfrowaniu wrocic do jego poczatkowego stanu
                wyjsciowy.write(iv) # zapisanie wektora inicjalizujacego do pliku

                while True:
                    blok = wejsciowy.read(rozmiar_bloku)

                    if len(blok) == 0:
                        break
                    elif len(blok) % 16 != 0:
                        blok = blok + ' '.encode() * (16 - len(blok)%16) # padding - dodaje spacje, aby uzyskac 16 bajtów
                        wyjsciowy.write(encryptor.encrypt(blok))

##################################################################################################################################################################################################
    def deszyfrowanie(self, plik_wejsciowy, plik_wyjsciowy = None, rozmiar_bloku = 24*1024):
        if not plik_wyjsciowy:
            plik_wyjsciowy = os.path.splitext(plik_wejsciowy)[0] + '.txt'

        with open(plik_wejsciowy, 'rb') as wejsciowy:
            rozmiar_pliku = struct.unpack('<Q', wejsciowy.read(struct.calcsize('Q')))[0] # wczytanie rozmiaru pliku
            iv = wejsciowy.read(16) # wczytanie wektora
            decryptor = AES.new(self.klucz, AES.MODE_CBC, iv)

            with open(plik_wyjsciowy, 'wb') as wyjsciowy:
                while True:
                    blok = wejsciowy.read(rozmiar_bloku)
                    
                    if len(blok) == 0:
                        break
                    
                    wyjsciowy.write(decryptor.decrypt(blok))

                wyjsciowy.truncate(rozmiar_pliku) # powrót do oryginalnego rozmiaru
