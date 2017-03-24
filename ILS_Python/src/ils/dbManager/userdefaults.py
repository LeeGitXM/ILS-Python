'''
Created on Mar 21, 2017

@author: phass

Preferences are user choices that we persist in the user's
permanent storage. This is the way that we allow one screen's
selection to be the starting point of the next - as well as
providing a starting place when we restart.  Use the Java
methods.
'''

import system
from java.util.prefs import Preferences

log = system.util.getLogger("com.ils.recipe.userdefaults")
PreferenceName = "recipetoolkit"

# These are the well-known keys:
# DATABASE - the current recipe database in use
# UNIT - the current procesing unit (or ALL)
def get(key):
    pref = Preferences.userRoot().node(PreferenceName)
    result = pref.get(key,"")
    log.trace("userdefaults.get %s = %s" % (key,result))
    return result

#
def set(key,value):
    pref = Preferences.userRoot().node(PreferenceName)
    log.trace("userdefaults.set %s = %s" % (key,str(value)))
    return pref.put(key,str(value))  