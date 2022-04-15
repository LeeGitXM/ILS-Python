'''
Created on Mar 27, 2017

@author: phass
'''

import system

def client():
    print "Starting up a DB Manager client"
    
    # Initialize the client tags
    system.tag.writeAsync(
        ["[Client]Active Only", "[Client]Family", "[Client]Grade", "[Client]Version"], 
        [True, "<Family>", "<Grade>", "<Version>"]
        )
    
    def doit():
        windows = system.gui.getOpenedWindows()
        print 'There are %d windows open' % len(windows)
        for window in windows:
            print window.getPath()
                
        # In operator mode we need to remove some menu selections
        from ils.common.menuBar import getMenuBar
        menubar = getMenuBar(window)
        
        from ils.common.menuBar import removeUnwantedMenus
        removeUnwantedMenus(menubar, "dbManager")
        
    system.util.invokeLater(doit, 1000)