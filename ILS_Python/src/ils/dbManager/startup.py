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
    
    from ils.common.menuBar import removeUnwantedMenus
    removeUnwantedMenus(menubar, "dbManager")
    
    # Initialize the client tagSelector
    system.tag.write("[Client]Active Only", True)
    system.tag.write("[Client]Family", "<Family>")
    system.tag.write("[Client]Grade", "<Grade>")
    system.tag.write("[Client]Version", "<Version>")