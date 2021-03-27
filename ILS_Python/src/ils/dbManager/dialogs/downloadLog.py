'''
Created on Mar 21, 2017

@author: phass
'''

import system

# Called from the client startup script: View menu
def showWindow():
    window = "DBManager/DownloadLog"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)