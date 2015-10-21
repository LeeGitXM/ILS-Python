'''
Created on Jul 28, 2015

@author: rforbes
'''

def defaultPostingMethod(window, dataset, requireAllInputs):
    table = window.getRootContainer().getComponent('table') 
    table.data = dataset
    window.getRootContainer().requireAllInputs = requireAllInputs
    
def sendData(window):
    '''Send data to gateway. If configured, check that all values have been entered, and
       don't send and warn if they have not. Return true if data was sent.'''
    from ils.sfc.client.util import sendResponse
    from ils.sfc.common.constants import DATA
    import system.gui.warningBox
    table = window.getRootContainer().getComponent('table')
    dataset = table.data
    requireAllInputs = window.getRootContainer().requireAllInputs
    allInputsOk = True
    if requireAllInputs:
        for row in range(dataset.rowCount):
            value = dataset.getValueAt(row, 1)
            if (value == None) or (len(value.strip()) == 0):
                allInputsOk = False
                break
    if allInputsOk:
        responseId = window.getRootContainer().messageId
        response = {DATA: dataset}
        sendResponse(responseId, response)
        return True
    else:
        system.gui.warningBox("All inputs are required")
        return False
