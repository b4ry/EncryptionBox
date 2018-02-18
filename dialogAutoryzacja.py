import sys
import dropbox
from PyQt5.QtWidgets import QApplication, QDialog
from ui_dialogAutoryzacja import Ui_Dialog


class dialogAutoryzacja(QDialog):
    def __init__(self, parent=None):
        super(dialogAutoryzacja, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.textBrowser.setText('Autoryzuj dostęp do konta Dropbox w przeglądarce, wpisz otrzymany kod poniżej.')


    def Autoryzacja(self):

        code=self.ui.lineEdit.text()
        return code
        
