import sys
import dropbox
import webbrowser
import os.path
import threading
import time
import shutil

#from PyQt5.QtWidgets import QApplication, QMainWindow, QDirModel
from PyQt5.QtWidgets import *
from ui_mainwindow import Ui_MainWindow
from dialogAutoryzacja import dialogAutoryzacja
from tokenDropbox import TokenDropbox
from deltaDropbox import DeltaDropbox
from mainDirectory import MainDirectory
import szyfrowanie_aes
from plik import Plik

#klucze od dropboksa
app_key = 'rysbak0q8ysrskt'
app_secret = 'bfq6mr2hx8vbhim'

#główne okno aplikacji
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.folder = MainDirectory() # folder aplikacji na dysku (ten zastepujacy dropboksowy)
        self.dialog = dialogAutoryzacja() # okno dialogowe do autoryzacji
        self.token = TokenDropbox() # definicja tokenu
        self.xDelta = DeltaDropbox() # delta , do sprawdzania roznicy na serwerze
        self.clientDropbox = {}
        #self.AES_key = b''
        #self.AES_IV = b''
        self.klucz_AES = ''
        self.odswiezanie = 5
        self.updateThreadExitFlag = 0 # flaga ze czas zakonczyc watek
        self.folder_metadata = {} # meta-dane, struktura plikow na serwerze
        
        
        self.ui.email_haslo.setEchoMode(QLineEdit.Password) # ustawienie maskowania na haslo
        self.ui.SSL_radio.setChecked(True)
    
        self.model = QFileSystemModel() # model drzewka
        
        #sloty
        self.ui.spinBoxOdswiez.valueChanged.connect(self.ustawOdswiezanie)
        self.ui.pushButton.clicked.connect(self.Autoryzacja) # akcja po kliknieciu Autoryzacji
        #self.ui.folderButton.clicked.connect(self.UtworzFolder)
        self.ui.emailWyslij.clicked.connect(self.wyslijEmail)
        self.ui.aesWyslij.clicked.connect(self.wyslijAES)
        self.ui.emailRSAGeneruj.clicked.connect(self.generujRSA)
        self.ui.AESGeneruj.clicked.connect(self.generujAES)
        self.ui.szyfrujRSA.clicked.connect(self.szyfrujRSA)
        self.ui.deszyfrujRSA.clicked.connect(self.deszyfrujRSA)
        self.ui.szyfrowanieAES_button.clicked.connect(self.szyfrujAES)
        self.ui.deszyfrowanieAES_button.clicked.connect(self.deszyfrujAES)
        
        if os.path.isfile(self.token.plik_tokens): # jezeli istnieje plik z tokenem
            self.Pracuj()
            
        else:
            self.ui.textBrowser.setText('Autoryzuj dostęp!')

        #  uklad folderu 
        #folder_metadata = self.clientDropbox.metadata('/')
        #print ("metadata:", folder_metadata)


    def ustawOdswiezanie(self, wartosc): # obsluga rolki od czasu odswiezania (pullowanie info z serwera)
        self.odswiezanie = wartosc
    
    def Pracuj(self) :  # czynnosci po starcie aplikacji i pomyslnej autoryzacji
        self.WczytajToken()
        self.folder.stworzNaDysku() #jezeli folder nie istnieje na dysku, to go stworz

        self.folder.WyslijFunkcjeWeb(self.AktualizujWeb) #wyslij drzewu plikow odnosnik do funkcji updetujacych zawartosc web dropboksa
          
        
        # drzewko katalogów- konfiuracja
        self.model.setRootPath(self.folder.sciezka)
        self.ui.treeView.setModel(self.model) # przypisanie modelu do widoku
        self.ui.treeView.setRootIndex(self.model.index(self.folder.sciezka))
        
        self.folder_metadata=self.clientDropbox.metadata('/') # metadane glownego folderu
        self.StanInicjalizacja()    # uaktualnienie wiedzy na serwerze
        threading.Thread(target=self.updateThread).start() # wątek odswiezajacy 
        #print(self.folder.drzewo.slownikSciezek)


    def closeEvent(self, event): # przeciazanie funkcji zamkniecia okna
        self.xDelta.ZapiszDoPliku() # zapisanie do pliku ostatniej delty
        self.updateThreadExitFlag = 1  # zamkniecie okna ustawia flage konca watku updatu
        self.folder.straznik.WatcherExitFlag = 1 # koniec watku watchera folderu lokalnego
        event.accept() # zamkniecie okna



    def updateThread(self): # funkcja wątku ściągającego zmiany z serwera

        # użyć https://www.dropbox.com/developers/core/docs/python#DropboxClient.delta
        # delta - zmiany miedzy zapytaniami
        
        # 1sze użycie
        if os.path.isfile(self.xDelta.plik_delta): # jezeli istnieje plik z deltą
            self.xDelta.WczytajZPliku()    
        else:
            self.xDelta.delta = self.clientDropbox.delta() # nowa delta
            
        
        self.WypiszZawartoscDelta()
        time.sleep(self.odswiezanie)
        while (self.updateThreadExitFlag==0):
            print('.')
            self.xDelta.delta = self.clientDropbox.delta(self.xDelta.delta['cursor'])
            #self.WypiszZawartoscDelta()
            self.AktualizujLokalnie()
            self.xDelta.ZapiszDoPliku()
            time.sleep(self.odswiezanie)

    def WypiszZawartoscDelta(self):
        for i in range(0,len(self.xDelta.delta['entries'])):
            print(self.xDelta.delta['entries'][i][0])


################ ## Aktualizacja stanu na serwerze na podstawie lokalnego - po wlaczeniu aplikacji

    # po uruchomieniu aplikacji należy sprawdzić, czy w okresie kiedy aplikacja
    # była nieaktywna nie doszło do zmian o których nie wie serwer, a następnie
    # zaktualizować jego stan

    def StanInicjalizacja(self):    # przejrzenie drzewa plikow i wyslanie na serwer to, czeego nie ma
        print ('StanInicjalizacja')
        

################ ## Aktualizacja stanu lokalnego na podstawie zmian na serwerze- na żywo

    ###
    ### PRZED UPDATOWANIEM STANU NA PODSTAWIE DYSKU SPRAWDZIC, CZY NIE BEDZIE DUBLOWANIA
    ### 
            
    def AktualizujLokalnie(self):
        for i in range(0,len(self.xDelta.delta['entries'])):
            #print(self.xDelta.delta['entries'][i])
            self.sprawdz(self.xDelta.delta['entries'][i])

    def sprawdz(self, delta):   # tworzy na dysku nowe foldery z serwera

        fail=0
        metadane= delta[1]
        #adres= delta[0]
        #tmp= adres.split('/')
        #print('tmp : ',tmp)
        pozycja = self.folder.drzewo.slownikSciezek
        sciezka = self.folder.sciezka
        sciezka2 = self.folder.sciezka # z wielkimi literami

        if metadane is None:        # usun lokalnie
            adres= delta[0]
            tmp= (adres.lower()).split('/')
            #print('usuwamy')
            for i in range (1,len(tmp)-1):
                if pozycja.get(tmp[i],0) != 0:
                    pozycja = pozycja[tmp[i]].zawartosc
                    sciezka = sciezka+'\\'+tmp[i]
                else:
                    fail = 1
                    break
            '''if pozycja.get(tmp[len(tmp)-1],0) != 0 and fail != 1:
                pozycja.pop(tmp[len(tmp)-1])
                #print('pop ',tmp[len(tmp)-1])
                sciezka = sciezka+"\\"+tmp[len(tmp)-1]
                #print(sciezka)
                if os.path.exists(sciezka):
                    if len(tmp[len(tmp)-1].split('.'))==1:      # jezeli jest to folder
                        shutil.rmtree(sciezka)
                    else:                                       # jezeli jest to plik
                        os.remove(sciezka)
                #print('pozycja ', pozycja)'''
            
        else:                       # stworz/ aktualizuj lokalnie
            adres=metadane['path']
            tmp= (adres.lower()).split('/') # bez wielkich liter
            tmp2= adres.split('/')  # z wielkimi literami
            for i in range (1,len(tmp)):
                nazwa = tmp[i]
                if pozycja.get(tmp[i],"brak pliku") != "brak pliku" :
                    pozycja = pozycja[tmp[i]].zawartosc
                    sciezka=sciezka+'\\'+tmp[i]
                    sciezka2=sciezka2+'\\'+tmp2[i]
                else:
                    if len(tmp[i].split('.'))==1:            # jezeli jest to folder
                        pusta = {}
                        lista={ nazwa : Plik(1, pusta)}
                        #print('lista:  ', lista)
                        sciezka=sciezka+'\\'+tmp[i]
                        sciezka2=sciezka2+'\\'+tmp2[i]
                        pozycja.update(lista)
                        if not os.path.exists(sciezka):
                            #print(self.folder.drzewo.slownikSciezek)
                            self.folder.drzewo.aktualizujMetadane(adres,metadane)
                            os.makedirs(sciezka2)
                    else:                                   # jezeli jest to plik
                        import shutil
                        
                        lista={ tmp[i] : Plik(0,tmp[i])}
                        sciezka=sciezka+'\\'+tmp[i]
                        sciezka2=sciezka2+'\\'+tmp2[i]
                        pozycja.update(lista)
                        f, metadata = self.clientDropbox.get_file_and_metadata(adres)
                        self.folder.drzewo.aktualizujMetadane(adres,metadane)
                        out = open(sciezka2, 'wb')
                        out.write(f.read())
                        out.close()
                        #shutil.move(sciezka, os.getcwd())
                        if(os.path.splitext(os.path.basename(sciezka))[1] == ".enc"):
                            self.deszyfrujAES(sciezka)

                        
                    print(pozycja[tmp[i]].meta)
                    pozycja = pozycja[tmp[i]].zawartosc
                
        #print(pozycja.meta)
################
################ Funkcje aktualizujace stan na serwerze - na żywo
    def AktualizujWeb(self, akcja, sciezka):
        #print('AktualizujWeb')

        ACTIONS = {                 # odpowiednik switcha
          1 : self.CreateWeb,
          2 : self.DeleteWeb,
          3 : self.UpdateWeb,
          4 : "Renamed from something",
          5 : self.RenameWeb
        }
        
        ACTIONS[akcja](sciezka)


    def CreateWeb(self, sciezka):
        if(os.path.splitext(os.path.basename(sciezka[0]))[1] == ".txt"):
                self.szyfrujAES(sciezka[0])
        if(os.path.splitext(os.path.basename(sciezka[0]))[1] == ".enc" or os.path.splitext(os.path.basename(sciezka[0]))[1] == "" or os.path.splitext(os.path.basename(sciezka[0]))[1] == ".aes"):
            sciezkaWeb = sciezka[0][len(self.folder.sciezka):]

            sciezkaWeb=sciezkaWeb.replace('\\','/')
        
    
            if len(sciezkaWeb.split('.'))==1:            # jezeli jest to folder
                response = self.clientDropbox.file_create_folder(sciezkaWeb)
                self.folder.drzewo.aktualizujMetadane(sciezkaWeb,response)
            else:                                   # jezeli jest to plik
                print(sciezka[0])
                f = open(sciezka[0], 'rb')
                response = self.clientDropbox.put_file(sciezkaWeb, f)
                self.folder.drzewo.aktualizujMetadane(sciezkaWeb,response)
                f.close()
            
        

    def DeleteWeb(self, sciezka):
        if(os.path.splitext(os.path.basename(sciezka[0]))[1] == ".enc" or os.path.splitext(os.path.basename(sciezka[0]))[1] == "" or os.path.splitext(os.path.basename(sciezka[0]))[1] == ".aes"):
            sciezkaWeb = sciezka[0][len(self.folder.sciezka):]
            sciezkaWeb=sciezkaWeb.replace('\\','/')
            response = self.clientDropbox.file_delete(sciezkaWeb)

    def UpdateWeb(self, sciezka):
        if(os.path.splitext(os.path.basename(sciezka[0]))[1] == ".txt"):
            self.szyfrujAES(sciezka[0])
        if(os.path.splitext(os.path.basename(sciezka[0]))[1] == ".enc" or os.path.splitext(os.path.basename(sciezka[0]))[1] == "" or os.path.splitext(os.path.basename(sciezka[0]))[1] == ".aes"):
            print('UpdateWeb')

            sciezkaWeb = sciezka[0][len(self.folder.sciezka):]

            sciezkaWeb=sciezkaWeb.replace('\\','/')

        
            plik = self.folder.drzewo.zwrocPlik(sciezkaWeb)
            metadataWeb = self.clientDropbox.metadata(sciezkaWeb)

            #if plik.meta['rev'] != metadataWeb['rev']:
##            print('inside job')
            if len(sciezkaWeb.split('.'))==1:            # jezeli jest to folder
                update =1 # nic nie rob
            else:                                   # jezeli jest to plik
            #print(sciezka[0])
                f = open(sciezka[0], 'rb')
                response = self.clientDropbox.put_file(sciezkaWeb, f, True) # nadpisz
                self.folder.drzewo.aktualizujMetadane(sciezkaWeb,response)
                f.close()
        
    def RenameWeb(self, sciezka):
        
        sciezkaWeb1 = sciezka[0][len(self.folder.sciezka):]
        sciezkaWeb1=sciezkaWeb1.replace('\\','/')

        sciezkaWeb2 = sciezka[1][len(self.folder.sciezka):]
        sciezkaWeb2=sciezkaWeb2.replace('\\','/')

        response = self.clientDropbox.file_move(sciezkaWeb1,sciezkaWeb2)
        self.folder.drzewo.aktualizujMetadane(sciezkaWeb2,response)
        
#######################    
####################### Uzyskiwanie dostępu do konta
    def Autoryzacja(self): #autoryzuj dropboxa
        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
        authorize_url = flow.start()

        webbrowser.open(authorize_url) # uruchom strone www

        if self.dialog.exec_() == 1:  # uruchom okno dialogowe, jesli wcisnieto accept - dzialaj
            code=self.dialog.Autoryzacja()
            #print(code)
            access_token, user_id = flow.finish(code)

            #TOKENS = 'dropbox_token.txt' # zapisz token do pliku
            token_file = open(self.token.plik_tokens,'w')
            token_file.write("%s|%s" % (access_token, user_id) )
            token_file.close()

            self.Pracuj()

           
    def WczytajToken(self): # wczytaj token z pliku, polacz z klientem
        self.token.WczytajZPliku()
        self.ui.textBrowser.setText('Połączono z Dropboxem')
        self.clientDropbox = dropbox.client.DropboxClient(self.token.acces_token)
        print ('Wczytano użytkownika: ')
        print (self.clientDropbox.account_info()['display_name'])

###########################

    def UtworzFolder(self): # tworzy folder szyfrujacy w folderze aplikacji (tylko jesli takowy nie istnieje)
        import os
        newpath = os.getcwd() + r'\folder_testowy'
        if not os.path.exists(newpath):
            os.makedirs(newpath)
            self.clientDropbox.file_create_folder('/folder_testowy') # trzeba bedzie sprawdzic, czy taki folder istnieje

    def wyslijEmail(self):
        import smtplib
        from email.mime.text import MIMEText

        # pobranie danych
        nadawca = self.ui.email_nadawca.text()
        adresat = self.ui.email_adresat.text()
        haslo = self.ui.email_haslo.text()
        klucz = self.ui.email_klucz.text()

        # budowanie wiadomosci
        msg = MIMEText(klucz)
        msg['From'] = nadawca
        msg['To'] = adresat
        msg['Subject'] = "Klucz publiczny - dropbox.api"

        # laczenie z serwerem - protokol TLS
        server = smtplib.SMTP()
        if(self.ui.TSL_radio.isChecked()):
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            print("TSL")
        elif(self.ui.SSL_radio.isChecked()):
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            print("SSL")
        server.login(nadawca, haslo)

        # wysylanie wiadomosci
        text = msg.as_string()
        server.sendmail(nadawca, adresat, text)

        #konczenie polaczenia z serwerem
        server.quit()
        
    def wyslijAES(self):
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        import email.encoders

        # pobranie danych
        nadawca = self.ui.email_nadawca.text()
        adresat = self.ui.email_adresat.text()
        haslo = self.ui.email_haslo.text()

        # budowanie wiadomosci
        msg = MIMEMultipart()
        msg['From'] = nadawca
        msg['To'] = adresat
        msg['Subject'] = "Klucz AES - dropbox.api"

        msg.attach(MIMEText('test'))
        
        # laczenie z serwerem - protokol TLS
        server = smtplib.SMTP()
        if(self.ui.TSL_radio.isChecked()):
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            print("TSL")
        elif(self.ui.SSL_radio.isChecked()):
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            print("SSL")
        server.login(nadawca, haslo)

        part = MIMEBase('application', "octet-stream")
        part.set_payload(open('testt.txt', 'rb').read())
        email.encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % ('testt.txt'))
        msg.attach(part)
    
        # wysylanie wiadomosci
        server.sendmail(nadawca, adresat, msg.as_string())

        #konczenie polaczenia z serwerem
        server.quit()
        
    def generujRSA(self):
        from Crypto.PublicKey import RSA
        from Crypto import Random

        # zapisanie do pliku
        import os.path

        if not os.path.exists(r'rsa_prywatny.txt' and r'rsa_publiczny.txt'):
            # generowanie klucza
            losowy_generator = Random.new().read
            klucz_prywatny = RSA.generate(1024, losowy_generator) # e = 65537
            klucz_publiczny = klucz_prywatny.publickey()

            self.ui.email_klucz.setText(klucz_publiczny.exportKey().decode())
            
            plik = open('rsa_prywatny.txt', 'w')
            plik1 = open('rsa_publiczny.txt', 'w')
            plik.write(klucz_prywatny.exportKey().decode())
            plik1.write(klucz_publiczny.exportKey().decode())
            plik.close()
            plik1.close()
        else:
            plik1 = open('rsa_publiczny.txt', 'r')
            self.ui.email_klucz.setText(plik1.read())

    def szyfrujRSA(self):
        from Crypto.PublicKey import RSA

        #klucz = self.ui.niezaszyfrowanyRSA.text()

        nazwa_pliku = self.ui.niezaszyfrowanyRSA.text()
        if os.path.exists(nazwa_pliku):
            with open(nazwa_pliku, 'r') as fr:
                klucz_pub_rsa = RSA.importKey(fr.read())

        if os.path.exists("aes_klucz.txt"):
            with open("aes_klucz.txt", 'r') as file:
                klucz = file.read()
            os.remove("aes_klucz.txt")

        plik_zaszyfrowany = 'aes' + self.ui.nazwaUzytkownikaLine.text() + '.aes'        
        plik = open(plik_zaszyfrowany, 'wb')
        plik.write(klucz_pub_rsa.encrypt(klucz.encode(), 32)[0])
        plik.close()
        #self.ui.zaszyfrowanyRSA.setPlainText(klucz_pub_rsa.encrypt(klucz.encode(), 32)[0].decode('iso-8859-2'))

    def deszyfrujRSA(self):
        from Crypto.PublicKey import RSA
        import socket

        if os.path.exists(r'rsa_prywatny.txt'):
            with open(r'rsa_prywatny.txt', 'r') as fr:
                klucz_pry_rsa = RSA.importKey(fr.read())

        sciezkaUzytkownika = "aes" + socket.gethostname() + ".aes" 
        plik = open(sciezkaUzytkownika, 'rb')
        plik1 = open('aes_klucz.txt', 'wb')
        plik1.write(klucz_pry_rsa.decrypt(plik.read()))
        plik.close()
        plik1.close()
        #self.ui.niezaszyfrowanyRSA_2.setText(klucz_pry_rsa.decrypt(klucz).decode('iso-8859-2'))
        
    def generujAES(self):
        from Crypto.Cipher import AES
        from Crypto import Random

        import os.path
        import base64
 
        self.klucz_AES = self.ui.KluczAES_line.text()

        if not os.path.exists(r'aes_klucz.txt'):
            plik = open('aes_klucz.txt', 'w')
            plik.write(self.klucz_AES)
            print(" KLUCZ ")
            print(self.klucz_AES)
            plik.close()
        '''if not os.path.exists(r'aes_klucz.txt' and r'aes_iv.txt'):
            key = Random.get_random_bytes(AES.block_size)
            iv = Random.get_random_bytes(AES.block_size)
            AES_key = AES.new(key, AES.MODE_CBC, iv)

            plik = open('aes_klucz.txt', 'wb')
            plik.write(key)
            print(" KLUCZ ")
            print(key)
            plik.close()

            with open('aes_klucz.txt', 'rb') as f:
                i = 0
                self.AES_key = f.read(1)
                while i < 15:
                    self.AES_key = self.AES_key + f.read(1)
                    print(self.AES_key)
                    i = i + 1

            plik = open('aes_iv.txt', 'wb')
            plik.write(iv)
            print(" IV ")
            print(iv)
            plik.close()

            with open('aes_iv.txt', 'rb') as f:
                i = 0
                self.AES_IV = f.read(1)
                while i < 15:
                    self.AES_IV = self.AES_IV + f.read(1)
                    print(self.AES_IV)
                    i = i + 1
        else:
            with open('aes_klucz.txt', 'rb') as f:
                i = 0
                self.AES_key = f.read(1)
                while i < 15:
                    self.AES_key = self.AES_key + f.read(1)
                    i = i + 1
            print(self.AES_key)

            with open('aes_iv.txt', 'rb') as f:
                i = 0
                self.AES_IV = f.read(1)
                while i < 15:
                    self.AES_IV = self.AES_IV + f.read(1)
                    i = i + 1
            print(self.AES_IV)'''
        
    def szyfrujAES(self, sciezka_do_pliku):
        import shutil, os, socket
        
        sciezka_klucz = os.path.dirname(sciezka_do_pliku)+"\\aes" + socket.gethostname() + ".aes"
        shutil.copy(sciezka_klucz, os.getcwd())

        sciezkaUzytkownika = "aes" + socket.gethostname() + ".aes"    
        if os.path.exists(sciezkaUzytkownika):
            self.deszyfrujRSA()
        plik = open('aes_klucz.txt', 'r')
        aes = szyfrowanie_aes.Block_AES(plik.read())
        plik.close()
        os.remove('aes_klucz.txt')
        os.remove(sciezkaUzytkownika)
        #aes.szyfrowanie(self.ui.nazwaPliku_szyfrowanie.text())
        aes.szyfrowanie(sciezka_do_pliku)

    def deszyfrujAES(self, sciezka_do_pliku):
        import shutil, os, socket

        sciezka_klucz = os.path.dirname(sciezka_do_pliku)+"\\aes" + socket.gethostname() + ".aes"
        shutil.copy(sciezka_klucz, os.getcwd())

        sciezkaUzytkownika = "aes" + socket.gethostname() + ".aes"   
        if os.path.exists(sciezkaUzytkownika):
            self.deszyfrujRSA()
        plik = open('aes_klucz.txt', 'r')
        aes = szyfrowanie_aes.Block_AES(plik.read())
        plik.close()
        os.remove('aes_klucz.txt')
        os.remove(sciezkaUzytkownika)
        aes.deszyfrowanie(sciezka_do_pliku)
