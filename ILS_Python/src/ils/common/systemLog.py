'''
Created on Aug 25, 2015

@author: Pete

This module implements the "System log" function which basically writes messages to a file.
'''

import system

def write(logger, txt):
    print "Writing <%s> to system logger <%s>" % (txt, logger)
    filename=getFilenameForLogger(logger)
    system.file.writeFile(filename, txt, True)

def getFilenameForLogger(logger):
    filename="c:/temp/" + logger + ".log"
    return filename