'''
Created on May 27, 2016

@author: ils
'''

import system

def showDetails(theText, theTitle=""):
    window=system.nav.openWindow("Common/Message Details Popup", {"theText": theText,"theTitle": theTitle})
    system.nav.centerWindow(window)