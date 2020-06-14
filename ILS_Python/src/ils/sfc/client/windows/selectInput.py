'''
Created on Jan 15, 2015

@author: rforbes
'''
import system
from ils.sfc.recipeData.api import s88GetFromStep
from ils.common.config import getDatabaseClient
from ils.sfc.client.util import setClientDone, setClientResponse
log =system.util.getLogger("com.ils.sfc.client.selectInput")

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()", __name__)
    db = getDatabaseClient()
    rootContainer = event.source.rootContainer
    windowId = rootContainer.windowId

    title = system.db.runScalarQuery("select title from sfcWindow where windowId = '%s'" % (windowId), db)
    rootContainer.title = title
    
    SQL = "select windowId, prompt, choicesStepId, choicesKey, responseLocation, targetStepId, keyAndAttribute, chartId, stepId from SfcSelectInput where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, db)
    record = pds[0]
    prompt = record["prompt"]
    choicesStepId = record["choicesStepId"]
    choicesKey = record["choicesKey"]

    choices = s88GetFromStep(choicesStepId, choicesKey + ".value", db)
    log.tracef("The choices are: %s", str(choices))
    data = []
    for choice in choices:
        data.append([choice])
    
    log.tracef("The data is: %s", str(data))
    choices = system.dataset.toDataSet(["choices"], data)
    rootContainer.choices = choices
    rootContainer.prompt = prompt
    rootContainer.targetStepId = record["targetStepId"]
    rootContainer.keyAndAttribute = record["keyAndAttribute"]
    rootContainer.chartId = record["chartId"]
    rootContainer.stepId = record["stepId"]
    rootContainer.responseLocation = record["responseLocation"]

def okActionPerformed(event):
    log.infof("In %s.okActionPerformed", __name__)
    rootContainer = event.source.parent

    dropdown = rootContainer.getComponent('choices')
    response = dropdown.selectedStringValue
    
    if response == "":
        system.gui.warningBox("Please select a value and press OK!")
        return
    
    setClientResponse(rootContainer, response)
    setClientDone(rootContainer)