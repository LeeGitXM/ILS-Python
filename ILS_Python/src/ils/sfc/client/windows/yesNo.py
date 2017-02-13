'''
Created on Dec 3, 2015

@author: rforbes
'''

import system
from ils.sfc.common.constants import YES_RESPONSE, NO_RESPONSE
from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.core import splitKey, setRecipeData

def yesActionPerformed(event):
    print "YES was pressed"
    setResponse(event, YES_RESPONSE)
  
def noActionPerformed(event):
    print "NO was pressed"
    setResponse(event, NO_RESPONSE)
    
def setResponse(event, response):
    db = getDatabaseClient()
    rootContainer = event.source.parent
    targetStepUUID = rootContainer.targetStepUUID
    key = rootContainer.key
    key,attribute = splitKey(key)
    setRecipeData(targetStepUUID, key, attribute, response, db)
    system.nav.closeParentWindow(event)