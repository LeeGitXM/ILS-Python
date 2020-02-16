'''
Created on Feb 12, 2020

@author: phass
'''

import system
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
    key = container.getComponent("Key Field").text
    
    SQL = "select ChartPath, StepName, RecipeDataType from SfcRecipeDataView where RecipeDataKey = '%s' order by ChartPath, StepName " % (key)
    pds = system.db.runQuery(SQL)
    
    table = container.getComponent("Power Table")
    table.data = pds
    
    
def listRecipeDataCallback(container):
    log.infof("In %s.listRecipeDataCallback", __name__)
    
    SQL = "select RecipeDataKey, ChartPath, StepName, RecipeDataType from SfcRecipeDataView order by RecipeDataKey "
    pds = system.db.runQuery(SQL)
    
    table = container.getComponent("Power Table")
    table.data = pds