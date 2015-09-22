'''
Created on Sep 22, 2015

@author: rforbes
'''

def defaultPostingMethod(window, dataTable):
    dataTableComponent = window.getRootContainer().getComponent('dataTable') 
    dataTableComponent.data = dataTable
    
def okActionPerformed(event):
    from ils.sfc.client.windowUtil import windowClosed
    windowClosed(event, True)
  
def cancelActionPerformed(event):
    from ils.sfc.client.windowUtil import windowClosed
    windowClosed(event, False) 