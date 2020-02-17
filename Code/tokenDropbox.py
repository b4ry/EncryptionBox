import sys

TOKENS = 'dropbox_token.txt'

class TokenDropbox(object):
    def __init__(self):
        self.acces_token = {}
        self.plik_tokens = 'dropbox_token.txt'

    def WczytajZPliku(self):
        token_file = open(self.plik_tokens)
        token_key,token_secret = token_file.read().split('|')
        token_file.close()
        self.acces_token=token_key
        #print(self.acces_token)
