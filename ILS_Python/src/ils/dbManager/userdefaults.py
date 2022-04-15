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

import string
from ils.io.util import readTag, writeTag

from ils.log import getLogger
log = getLogger(__name__)

# These are the well-known keys:
# DATABASE - the current recipe database in use
# UNIT - the current procesing unit (or ALL)
def get(key):
    if string.upper(key) in ["FAMILY", "UNIT"]:
        val = readTag('[Client]Family').value
    elif string.upper(key) == "GRADE":
        val = readTag('[Client]Grade').value
    elif string.upper(key) == "VERSION":
        val = readTag('[Client]Version').value
    elif string.upper(key) == "ACTIVE":
        val = readTag('[Client]Active Only').value
    
    log.trace("userdefaults.get %s = %s" % (key,val))
    return val

#
def set(key,value):
    if string.upper(key) == "FAMILY":
        writeTag('[Client]Family', value)
    elif string.upper(key) == "GRADE":
        writeTag('[Client]Grade', value)
    elif string.upper(key) == "VERSION":
        writeTag('[Client]Version', value)
    elif string.upper(key) == "ACTIVE":
        writeTag('[Client]Active Only', value)