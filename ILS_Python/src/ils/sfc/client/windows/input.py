'''
Created on Jan 16, 2015

@author: rforbes

This handles both the GetInput step and the GetInputWithLimits step.
'''

from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.core import splitKey, setRecipeData
import system, time

def internalFrameOpened(event):
    print "In %s.internalFrameOpened()" % (__name__)
    rootContainer = event.source.rootContainer
    database = getDatabaseClient()
    windowId = rootContainer.windowId
    
    SQL = "select * from SfcWindow where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)
    record=pds[0]
    rootContainer.title = record["title"]
    
    SQL = "select * from SfcInput where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database)
    while len(pds) < 1 :
        print "Window was not found, requerying..."    
        time.sleep(1)
        pds = system.db.runQuery(SQL, database)

    record=pds[0]
    
    lowLimit = record["lowLimit"]
    highLimit = record["highLimit"]
    defaultValue = record["defaultValue"]
    print "    High limit: ", lowLimit
    print "     Low Limit: ", highLimit
    print "       Default: ", defaultValue
    
    rootContainer.prompt = record["prompt"]
    rootContainer.lowLimit = lowLimit
    rootContainer.highLimit = highLimit
    rootContainer.targetStepUUID = record["targetStepUUID"]
    rootContainer.keyAndAttribute = record["keyAndAttribute"]
    rootContainer.defaultValue = defaultValue
    
    if lowLimit == None or highLimit == None:
        limitText = ""
    else:
        limitText = "Limits: %s to %s" % (str(lowLimit), str(highLimit))

    rootContainer.limitText = limitText    


def okActionPerformed(event):
    print "%s.okActionPerformed()" % (__name__)
    database = getDatabaseClient()
    window=system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    targetStepUUID = rootContainer.targetStepUUID
    keyAndAttribute = rootContainer.keyAndAttribute
    folder,key,attribute = splitKey(keyAndAttribute)
    responseField = rootContainer.getComponent('responseField')
    response = responseField.text
    if response == "":
        system.gui.warningBox("Please enter a value and press OK!")
        return
    
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
            setRecipeData(targetStepUUID, folder, key, attribute, response, database)
            system.nav.closeParentWindow(event)
        else:
            system.gui.messageBox('Value must be between %f and %f' % (lowLimit, highLimit))
    else:
        # return the response as a string
        setRecipeData(targetStepUUID, folder, key, attribute, response, database)
        system.nav.closeParentWindow(event)
  
def cancelActionPerformed(event):
    window=system.gui.getParentWindow(event)
