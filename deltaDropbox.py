import sys
import ast

DELTAS = 'dropbox_delta.txt'

class DeltaDropbox(object):
    def __init__(self):
        self.delta = {}
        self.plik_delta = DELTAS

    def WczytajZPliku(self):
        delta_file = open(self.plik_delta)
        self.delta = ast.literal_eval(delta_file.read())
        delta_file.close()

    def ZapiszDoPliku(self):
        delta_file = open(self.plik_delta,'w')
        delta_file.write("%s" % (self.delta))
        delta_file.close()
        
