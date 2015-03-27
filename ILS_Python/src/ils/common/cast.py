'''
Created on Sep 10, 2014

@author: Pete
'''

def toBool(txt):

    if txt == "true" or txt == "True" or txt == "TRUE" or txt == True:
        val = True
    else:
        val = False

    return val

def toBit(txt):

    if txt == "true" or txt == "True" or txt == "TRUE" or txt == True:
        val = 1
    else:
        val = 0

    return val