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
import system, time

def internalFrameOpened(event):
    print "In internalFrameOpened()"
    rootContainer = event.source.rootContainer
    windowId = rootContainer.windowId
    
    SQL = "select * from SfcWindow where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL)
    record=pds[0]
    rootContainer.title = record["title"]
    
    SQL = "select * from SfcInput where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL)
    while len(pds) < 1 :
        print "Window was not found, requerying..."    
        time.sleep(1)
        pds = system.db.runQuery(SQL)

    record=pds[0]
    
    lowLimit = record["lowLimit"]
    highLimit = record["highLimit"]
    
    rootContainer.prompt = record["prompt"]
    rootContainer.lowLimit = lowLimit
    rootContainer.highLimit = highLimit
    rootContainer.targetStepUUID = record["targetStepUUID"]
    rootContainer.keyAndAttribute = record["keyAndAttribute"]
    
    if lowLimit == None or highLimit == None:
        limitText = ""
    else:
        limitText = "Limits: %s to %s" % (str(lowLimit), str(highLimit))

    rootContainer.limitText = limitText    
    print "-- DONE --"

def okActionPerformed(event):
    db = getDatabaseClient()
    window=system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    targetStepUUID = rootContainer.targetStepUUID
    keyAndAttribute = rootContainer.keyAndAttribute
    key,attribute = splitKey(keyAndAttribute)
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
    