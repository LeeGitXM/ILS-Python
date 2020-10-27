'''
Created on Feb 12, 2020

@author: phass
'''

import system
from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.hierarchyWithBrowser import deleteRecipeData, deleteRecipeDataGroup
from ils.common.util import clearDataset

log = system.util.getLogger("ils.client.ui")

def internalFrameOpened(rootContainer):
    '''
    TODO - the clearDataset call is new to 7.9.7.  Once all of the systems reach this point then uncomment.
    '''
    log.infof("In %s.internalFrameOpened", __name__)
    
    ''' Clear all of the fields and tables and select the Search By Key tab '''
    container = rootContainer.getComponent("Search By Key Container")
    container.getComponent("Key Field").text = ""
    table = container.getComponent("Power Table")

    ds = table.data
    #ds = system.dataset.clearDataset(ds)
    table.data = ds
    
    container = rootContainer.getComponent("List Container")
    table = container.getComponent("Power Table")
    ds = table.data
    #ds = system.dataset.clearDataset(ds)
    table.data = ds
    
    tabStrip = rootContainer.getComponent("Tab Strip")
    tabStrip.selectedTab = "Search by Key"

    
def searchForKeyCallback(container):
    log.infof("In %s.searchForKeyCallback", __name__)
    db = getDatabaseClient()
    key = container.getComponent("Key Field").text
    
    SQL = "select RecipeDataId, StepId, RecipeDataFolderId, RecipeDataKey, ChartPath, StepName, RecipeDataType from SfcRecipeDataView "\
        "where RecipeDataKey like '%s' "\
        "order by RecipeDataKey " % (key)

    pds = system.db.runQuery(SQL, db)
    
    table = container.getComponent("Power Table")
    table.data = pds
    
    system.gui.messageBox("Found %d references" % (len(pds)))
    
    
def refreshRecipeDataListCallback(event):
    log.infof("In %s.listRecipeDataCallback", __name__)
    
    container = event.source.parent
    table = container.getComponent("Power Table")
    system.db.refresh(table, "data")
    
# chartIds are resource Ids of charts to consider
def getSearchResults(chartIds):
    print "Fetching recipe data to be used for searching" 
    recipeData = []
    return recipeData

    
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
    refreshRecipeDataListCallback(event)


def deleteFolderCallback(event):
    log.infof("In %s.deleteFolderCallback()...", __name__)
    db = getDatabaseClient()
    
    container = event.source.parent
    table = container.getComponent("Power Table")
    selectedRow = table.selectedRow
    ds = table.data
    recipeDataFolderId = ds.getValueAt(selectedRow,"RecipeDataFolderId")
    
    deleteRecipeDataGroup(recipeDataFolderId, db)
    refreshRecipeDataListCallback(event)


def clearCallback(event):
    log.infof("In %s.clearCallback()...", __name__)    
    container = event.source.parent
    table = container.getComponent("Power Table")
    ds = table.data
    ds = clearDataset(ds)
    table.data = ds


def getSelectedInfo(event):
    container = event.source.parent
    table = container.getComponent("Power Table")
    selectedRow = table.selectedRow
    ds = table.data
    
    stepId = ds.getValueAt(selectedRow,"StepId")
    recipeDataType = ds.getValueAt(selectedRow,"RecipeDataType")
    recipeDataId = ds.getValueAt(selectedRow,"RecipeDataId")
    recipeDataKey = ds.getValueAt(selectedRow,"RecipeDataKey")
    recipeDataFolderId = ds.getValueAt(selectedRow,"RecipeDataFolderId")
    
    log.infof("    %s %s, %s %s %s", str(stepId), recipeDataType, str(recipeDataId), recipeDataKey, str(recipeDataFolderId))
    
    return stepId, recipeDataType, recipeDataId, recipeDataKey, recipeDataFolderId
    