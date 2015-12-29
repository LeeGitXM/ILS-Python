'''
Created on Jan 16, 2015

@author: rforbes
'''
'''
Created on Jan 15, 2015

@author: rforbes
'''

from ils.sfc.client.windowUtil import sendWindowResponse
import system.gui

def okActionPerformed(event):
    window=system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    responseField = rootContainer.getComponent('responseField')
    response = responseField.text
    lowLimit = rootContainer.data.getValueAt(0,'lowLimit')
    highLimit = rootContainer.data.getValueAt(0,'highLimit')
    if lowLimit != None:
        # check a float value against limits
        try:
            floatResponse = float(response)
            valueOk = (floatResponse >= lowLimit) and (floatResponse <= highLimit)
        except ValueError:
            valueOk = False
        if valueOk:
            sendWindowResponse(window, floatResponse)
        else:
            system.gui.messageBox('Value must be between %f and %f' % (lowLimit, highLimit))
    else:
        # return the response as a string
        sendWindowResponse(window, response)
  
def cancelActionPerformed(event):
    window=system.gui.getParentWindow(event)
    sendWindowResponse(window, None)
    