'''
Created on Feb 23, 2020

@author: phass
'''

import system
from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.hierarchyWithBrowser import deleteRecipeData
log=system.util.getLogger("com.ils.sfc.recipeViewer")

def editCallback(event):
    log.infof("In %s.editCallback()...", __name__)
    stepId, recipeDataType, recipeDataId, recipeDataKey, recipeDataFolderId = getSelectedInfo(event)
    window = system.nav.openWindowInstance('SFC/RecipeDataEditor', {'stepId':stepId, 'recipeDataType':recipeDataType, 'recipeDataId':recipeDataId, 'recipeDataKey':recipeDataKey, "recipeDataFolderId":recipeDataFolderId})
    system.nav.centerWindow(window)
    
def deleteCallback(event):
    log.infof("In %s.deleteCallback()...", __name__)
    db = getDatabaseClient()
    stepId, recipeDataType, recipeDataId, recipeDataKey, recipeDataFolderId = getSelectedInfo(event)
    deleteRecipeData(recipeDataType, recipeDataId, db)
    refreshCallback(event)
    
def refreshCallback(event):
    container = event.source.parent
    table = container.getComponent("Recipe Data Table")
    system.db.refresh(table, "data")
    
def getSelectedInfo(event):
    container = event.source.parent
    table = container.getComponent("Recipe Data Table")
    selectedRow = table.selectedRow
    ds = table.data
    
    stepId = ds.getValueAt(selectedRow,"StepId")
    recipeDataType = ds.getValueAt(selectedRow,"RecipeDataType")
    recipeDataId = ds.getValueAt(selectedRow,"RecipeDataId")
    recipeDataKey = ds.getValueAt(selectedRow,"RecipeDataKey")
    recipeDataFolderId = ds.getValueAt(selectedRow,"RecipeDataFolderId")
    
    log.infof("    %s %s, %s %s %s", str(stepId), recipeDataType, str(recipeDataId), recipeDataKey, str(recipeDataFolderId))
    
    return stepId, recipeDataType, recipeDataId, recipeDataKey, recipeDataFolderId