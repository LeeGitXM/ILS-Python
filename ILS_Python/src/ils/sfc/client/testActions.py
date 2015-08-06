'''
client-side methods to support particular unit tests

methods should return True if they were able to complete the action,
otherwise return False to be retried later

@author: rforbes
'''

def controlPanelAcknowledge(testName, chartRunId):
    '''mimic a user pressing the Acknowledge button on the control panel'''
    from ils.sfc.client.controlPanel import getController
    controlPanel = getController(chartRunId)
    if controlPanel == None or controlPanel.messageIndex == None:
        return False
    else:
        controlPanel.doAcknowledge() 
        return True
    
    