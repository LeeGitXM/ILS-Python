'''
Created on Jan 16, 2015

@author: rforbes
'''
'''
Created on Jan 15, 2015

@author: rforbes
'''

from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.core import splitKey, setRecipeData
import system.gui

def okActionPerformed(event):
    db = getDatabaseClient()
    window=system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    targetStepUUID = rootContainer.targetStepUUID
    key = rootContainer.key
    key,attribute = splitKey(key)
    responseField = rootContainer.getComponent('responseField')
    response = responseField.text
    lowLimit = rootContainer.lowLimit
    highLimit = rootContainer.highLimit
    if (lowLimit != None) and (response != None):
        # check a float value against limits
        try:
            floatResponse = float(response)
            valueOk = (floatResponse >= lowLimit) and (floatResponse <= highLimit)
        except ValueError:
            valueOk = False
        if valueOk:
            setRecipeData(targetStepUUID, key, attribute, response, db)
        else:
            system.gui.messageBox('Value must be between %f and %f' % (lowLimit, highLimit))
    else:
        # return the response as a string
        setRecipeData(targetStepUUID, key, attribute, response, db)
  
def cancelActionPerformed(event):
    window=system.gui.getParentWindow(event)
    