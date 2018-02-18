import sys

from mainwindow import MainWindow
from PyQt5.QtWidgets import QApplication


if __name__ == "__main__":

    app = QApplication(sys.argv)
    myapp = MainWindow()
    myapp.show()
    sys.exit(app.exec_())


# PROBLEMY

#1 problem z tworzeniem nowych plików i kopiowaniem w folderze lokalnym,
#  czasem dziala, czasem nie - nie wiadomo dlaczego! Przeciaganie dziala
#  normalnie...
#
#2 funkcja update (reakcja na zmiane w stanie lokalnym) wywoluje sie zbyt czesto ...
#
#3 skopiowanie katalogu do folderu aplikacji przeniesie cala zawartosc (zawsze?), natomiast
#  przeniesienie nie, jedynie utworzy katalog-korzeń  

# DO ZROBIENIA

#1 synchronizacja po uruchomieniu- lokalne na serwer

