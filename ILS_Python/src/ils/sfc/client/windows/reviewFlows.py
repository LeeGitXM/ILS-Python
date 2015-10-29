'''
Created on Sep 22, 2015

@author: rforbes
'''

def defaultPostingMethod(window, data, heading1, heading2, heading3):
    import system.dataset
    dataTable = window.getRootContainer().getComponent('dataTable') 
    dataTable.data = data
    for row in range(dataTable.columnAttributesData.rowCount):
        name = dataTable.columnAttributesData.getValueAt(row, 'name')
        if name == 'flow1':
            dataTable.columnAttributesData = system.dataset.setValue(dataTable.columnAttributesData, row, 'label', heading1)
        elif name == 'flow2':
            dataTable.columnAttributesData = system.dataset.setValue(dataTable.columnAttributesData, row, 'label', heading2)
        elif name == 'flow3':
            dataTable.columnAttributesData = system.dataset.setValue(dataTable.columnAttributesData, row, 'label', heading3)
    
def windowClosed(event, buttonValue, data):
    from ils.sfc.client.windowUtil import responseWindowClosed
    from ils.sfc.common.constants import VALUE, DATA
    from system.gui import getParentWindow
    window = getParentWindow(event)
    payload = dict()
    payload[VALUE] = buttonValue
    payload[DATA] = data   
    responseWindowClosed(window, payload)
