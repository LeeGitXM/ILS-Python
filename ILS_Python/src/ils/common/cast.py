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