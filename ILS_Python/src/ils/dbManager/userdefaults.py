'''
Created on Mar 21, 2017

@author: phass

Redesigned this to use client tags rather than the preference system because the preferences
are shared between multiple clients on a single computer.  This may not be an issue in production
but it sure is during testing.
 
Preferences are user choices that we persist in the user's
permanent storage. This is the way that we allow one screen's
selection to be the starting point of the next - as well as
providing a starting place when we restart.  Use the Java
methods.
'''

import system, string
from java.util.prefs import Preferences

from ils.log import getLogger
log =getLogger(__name__)

# These are the well-known keys:
# DATABASE - the current recipe database in use
# UNIT - the current procesing unit (or ALL)
def get(key):
    if string.upper(key) in ["FAMILY", "UNIT"]:
        val = system.tag.read('[Client]Family').value
    elif string.upper(key) == "GRADE":
        val = system.tag.read('[Client]Grade').value
    elif string.upper(key) == "VERSION":
        val = system.tag.read('[Client]Version').value
    elif string.upper(key) == "ACTIVE":
        val = system.tag.read('[Client]Active Only').value
    
    log.trace("userdefaults.get %s = %s" % (key,val))
    return val

#
def set(key,value):
    if string.upper(key) == "FAMILY":
        system.tag.write('[Client]Family', value)
    elif string.upper(key) == "GRADE":
        system.tag.write('[Client]Grade', value)
    elif string.upper(key) == "VERSION":
        system.tag.write('[Client]Version', value)
    elif string.upper(key) == "ACTIVE":
        system.tag.write('[Client]Active Only', value)