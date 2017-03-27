'''
Created on Mar 27, 2017

@author: phass
'''

import system

def client():
    print "Starting up a DB Manager client"

    # Display the About window which is a nice welcome to the application but also so that I have a window from which
    # to get the menubar
    window = system.nav.openWindow('DBManager/About')
    system.nav.centerWindow(window)
            
    # In operator mode we need to remove some menu selections
    from ils.common.menuBar import getMenuBar
    menubar = getMenuBar(window)
    
    from ils.dbManager.menuBar import removeUnwantedMenus
    removeUnwantedMenus(menubar)