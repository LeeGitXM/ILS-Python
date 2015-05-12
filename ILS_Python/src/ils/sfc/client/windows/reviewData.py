'''
Created on Jan 14, 2015

@author: rforbes
'''

def okActionPerformed(event):
    windowClosed(event, True)
  
def cancelActionPerformed(event):
    windowClosed(event, False)

def getTableData():
    '''Get the (possibly modified) data from the table and put it back into JSON'''

def defaultPostingMethod(window, dataTable):
    dataTableComponent = window.getRootContainer().getComponent('dataTable') 
    dataTableComponent.data = dataTable

def windowClosed(event, response):
    from ils.sfc.client.util import sendResponse
    from ils.sfc.client.controlPanel import getController
    from ils.sfc.client.windowUtil import getWindowId, getMessageId, getChartRunId
    import system.gui.getParentWindow
    window = system.gui.getParentWindow(event)
        
    messageId = getMessageId(window)
    sendResponse(messageId, response)
    
    chartRunId = getChartRunId(window)
    windowId = getWindowId(window)
    controller = getController(chartRunId)
    controller.removeWindow(windowId)    
    system.nav.closeWindow(window)
