'''
Created on Jan 15, 2015

@author: rforbes
'''
import system
from ils.sfc.recipeData.api import s88GetFromStep
from ils.sfc.recipeData.core import splitKey, setRecipeData
from ils.common.config import getDatabaseClient

def internalFrameOpened(event):
    print "In %s.internalFrameOpened()" % (__name__)
    db = getDatabaseClient()
    rootContainer = event.source.rootContainer
    windowId = rootContainer.windowId

    title = system.db.runScalarQuery("select title from sfcWindow where windowId = '%s'" % (windowId), db)
    rootContainer.title = title
    
    SQL = "select * from SfcSelectInput where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, db)
    record = pds[0]
    prompt = record["prompt"]
    choicesStepId = record["choicesStepId"]
    choicesKey = record["choicesKey"]

    choices = s88GetFromStep(choicesStepId, choicesKey + ".value", db)
    print "The choices are: ", choices
    data = []
    for choice in choices:
        data.append([choice])
    
    print "The data is: ", data
    choices = system.dataset.toDataSet(["choices"], data)
    rootContainer.choices = choices
    rootContainer.prompt = prompt
    rootContainer.targetStepId = record["targetStepId"]
    rootContainer.keyAndAttribute = record["keyAndAttribute"]
    

def okActionPerformed(event):
    db = getDatabaseClient()
    window=system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    targetStepId = rootContainer.targetStepId
    keyAndAttribute = rootContainer.keyAndAttribute
    folder,key,attribute = splitKey(keyAndAttribute)
    dropdown = rootContainer.getComponent('choices')
    response = dropdown.selectedStringValue
    if response == "":
        system.gui.warningBox("Please select a value and press OK!")
        return
    
    setRecipeData(targetStepId, folder, key, attribute, response, db)