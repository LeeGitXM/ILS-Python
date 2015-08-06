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

def defaultPostingMethod(window, primaryDataTable, primaryTabLabel, secondaryDataTable, secondaryTabLabel):
    import system.dataset
    primaryDataTableComponent = window.getRootContainer().getComponent('primaryDataTable') 
    primaryDataTableComponent.data = primaryDataTable
    secondaryDataTableComponent = window.getRootContainer().getComponent('secondaryDataTable')
    secondaryDataTableComponent.data = secondaryDataTable
    tabsComponent = window.getRootContainer().getComponent('tabs') 
    tabsComponent.tabData = system.dataset.updateRow(tabsComponent.tabData, 0, {'DISPLAY_NAME' : primaryTabLabel})
    tabsComponent.tabData = system.dataset.updateRow(tabsComponent.tabData, 1, {'DISPLAY_NAME' : secondaryTabLabel})
    
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

def togglePrimary(window):
    primaryTable = window.getRootContainer().getComponent('primaryDataTable') 
    secondaryTable = window.getRootContainer().getComponent('secondaryDataTable') 
    tabStrip = window.getRootContainer().getComponent('tabs') 
    if tabStrip.selectedTab == "primary":
        secondaryTable.visible = False
        primaryTable.visible = True
    else:
        primaryTable.visible = False
        secondaryTable.visible = True
