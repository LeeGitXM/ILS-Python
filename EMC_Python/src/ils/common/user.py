'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def isOperator():    
    roles = system.security.getRoles()
    if 'Operator' in roles:
        return True
    
    return False

def isAE():
    roles = system.security.getRoles()
    if 'AE' in roles:
        return True

    return False