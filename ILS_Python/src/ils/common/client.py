'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def startup():    
    print "In common.client.startup()"
    username = system.security.getUsername()
    
    # We need to have some way of determining which console to use - perhaps a role
    # for each console
    
    if username.find("vfu") > 0:
        window = "Vistalon Windows\VFU Console"
        system.nav.openWindow(window)

    elif username.find("rla3") > 0:
        window = "Vistalon Windows\RLA3 Console"
        system.nav.openWindow(window)