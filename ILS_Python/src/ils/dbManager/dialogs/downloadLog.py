'''
Created on Mar 21, 2017

@author: phass
'''

# Copyright 2014. ILS Automation. All rights reserved.
#
# Scripts in support of the "Recipe Output" table.
#
import system
log = system.util.getLogger("com.ils.recipe.ui")

# Called from the client startup script: View menu
def showWindow():
    window = "DBManager/DownloadLog"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)