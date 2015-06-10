'''
Created on May 29, 2015

@author: rforbes
'''

def defaultPostingMethod(window, properties):
    from ils.sfc.common.constants import DATA
    table = window.getRootContainer().getComponent('table')
    table.data = properties[DATA] 

