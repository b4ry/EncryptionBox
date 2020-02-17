import os

import win32file
import win32con
from collections import OrderedDict





class Watcher(object):
    def __init__(self, sciezka, funkcja):
        self.callback = funkcja
        self.path_to_watch = sciezka
        self.WatcherExitFlag = 0
        self.ACTIONS = {
          1 : "Created",
          2 : "Deleted",
          3 : "Updated",
          4 : "Renamed from something",
          5 : "Renamed to something"
        }
        self.FILE_LIST_DIRECTORY = 0x0001
        self.hDir = win32file.CreateFile (
          self.path_to_watch,
          self.FILE_LIST_DIRECTORY,
          win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
          None,
          win32con.OPEN_EXISTING,
          win32con.FILE_FLAG_BACKUP_SEMANTICS,
          None
        )
    def start(self):
        #while 1:
        while (self.WatcherExitFlag==0):
            tmp_filename = {}
            
            results = win32file.ReadDirectoryChangesW (
                    self.hDir,
                    1024,
                    True,
                    win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                     win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                     win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                     win32con.FILE_NOTIFY_CHANGE_SIZE |
                     win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                     win32con.FILE_NOTIFY_CHANGE_SECURITY,
                    None,
                    None
                  )

##            results2 = win32file.ReadDirectoryChangesW (
##                    self.hDir,
##                    1024,
##                    True,
##                    
##                     
##                     win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
##                     win32con.FILE_NOTIFY_CHANGE_SIZE |
##                     win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
##                     win32con.FILE_NOTIFY_CHANGE_SECURITY,
##                    None,
##                    None
##                  ) 
            
            
            #print('R2: ',results2)

            #print('Rlista: ',list(OrderedDict.fromkeys(results)))

            results=list(OrderedDict.fromkeys(results))
            #print('R1: ',results)
            for action, file in results:
                full_filename = os.path.join (self.path_to_watch, file)
                if action == 4: # jezeli zmiana nazwy z
                    tmp_filename = full_filename
                elif action == 5: # jezeli zmiana nazwy na
                    self.callback(action, [tmp_filename, full_filename])
                else:
                    self.callback(action, [full_filename])
                #print (full_filename, self.ACTIONS.get (action, "Unknown"))
                

if __name__ == "__main__":
        straznik = Watcher("C:/Users/Piotrek/szyfrBox")
        straznik.start()
