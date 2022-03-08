'''
Created on Jan 16, 2015

@author: rforbes

This handles both the GetInput step and the GetInputWithLimits step.
'''
import system
from ils.common.config import getDatabaseClient
from ils.sfc.client.util import setClientDone, setClientResponse
from ils.log import getLogger
log =getLogger(__name__)

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()", __name__)
    db = getDatabaseClient()
    rootContainer = event.source.rootContainer
    windowId = rootContainer.windowId
    
    title = system.db.runScalarQuery("select title from sfcWindow where windowId = '%s'" % (windowId), db)
    rootContainer.title = title
    
    SQL = "select * from SfcInput where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, db)
    record=pds[0]
    
    lowLimit = record["lowLimit"]
    highLimit = record["highLimit"]
    defaultValue = record["defaultValue"]
    log.tracef("    High limit: %s", str(lowLimit))
    log.tracef("     Low Limit: %s", str(highLimit))
    log.tracef("       Default: %s", str(defaultValue))
    
    rootContainer.prompt = record["prompt"]
    rootContainer.lowLimit = lowLimit
    rootContainer.highLimit = highLimit
    rootContainer.targetStepId = record["targetStepId"]
    rootContainer.keyAndAttribute = record["keyAndAttribute"]
    rootContainer.defaultValue = defaultValue
    rootContainer.chartId = record["chartId"]
    rootContainer.stepId = record["stepId"]
    rootContainer.responseLocation = record["responseLocation"]
    
    if lowLimit == None or highLimit == None:
        limitText = ""
    else:
        limitText = "Limits: %s to %s" % (str(lowLimit), str(highLimit))

    rootContainer.limitText = limitText    


def okActionPerformed(event):
    print "%s.okActionPerformed()" % (__name__)

    window=system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
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
    else:
        valueOk = True


    if valueOk:
        setClientResponse(rootContainer, response)
        setClientDone(rootContainer)
        system.nav.closeParentWindow(event)
    else:
        system.gui.messageBox('Value must be between %f and %f' % (lowLimit, highLimit))
  
def cancelActionPerformed(event):
    window=system.gui.getParentWindow(event)
