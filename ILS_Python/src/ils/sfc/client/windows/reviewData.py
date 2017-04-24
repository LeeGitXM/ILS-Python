'''
Created on Jan 14, 2015

@author: rforbes
'''

import system
from ils.common.config import getDatabaseClient, getTagProviderClient
from ils.sfc.recipeData.core import splitKey, setRecipeData

def internalFrameOpened(rootContainer):
    database = getDatabaseClient()
    
    print "In reviewData.internalFrameOpened()"

    windowId = rootContainer.windowId
    
    title = system.db.runScalarQuery("Select title from SfcWindow where windowId = '%s'" % (windowId), database)
    rootContainer.title = title
    
    tabs = rootContainer.getComponent("tabs")
    tabs.selectedTab = "primary"
    showAdvice = system.db.runScalarQuery("select showAdvice from SfcReviewData where windowId = '%s'" % (windowId), database)
    print "Show Advice: ", showAdvice
    
    if showAdvice:
        columnWidths = {"prompt": 150, "advice": 250, "value": 130, "units": 60}
    else:
        columnWidths = {"prompt": 400, "advice": 0, "value": 130, "units": 60}
    
    
    SQL = "select prompt, advice, value, units from SfcReviewDataTable where windowId = '%s' and isPrimary = 1 order by rowNum" % (windowId)
    pds = system.db.runQuery(SQL, database)
    table = rootContainer.getComponent("Primary Table")
    setAdviceVisibiity(table, showAdvice, columnWidths)
    table.data = pds
    
    SQL = "select prompt, advice, value, units from SfcReviewDataTable where windowId = '%s' and isPrimary = 0 order by rowNum" % (windowId)
    pds = system.db.runQuery(SQL, database)
    table = rootContainer.getComponent("Secondary Table")
    setAdviceVisibiity(table, showAdvice, columnWidths)
    table.data = pds
    
    if len(pds) > 0:
        rootContainer.hasSecondary = True
    else:
        rootContainer.hasSecondary = False

 
def okActionPerformed(event):
    actionPerformed(event, "OK")
  
def cancelActionPerformed(event):
    actionPerformed(event, "CANCEL")

def actionPerformed(event, response):
    db = getDatabaseClient()
    window=system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    targetStepUUID = rootContainer.targetStepUUID
    key = rootContainer.key
    setRecipeData(targetStepUUID, key, "value", response, db)
    system.nav.closeParentWindow(event)


def setAdviceVisibiity(table, showAdvice, columnWidths):
    ds = table.columnAttributesData
    for row in range(ds.rowCount):
        columnName = ds.getValueAt(row,"name")
        if columnName == "advice":
            ds = system.dataset.setValue(ds, row, "hidden", not showAdvice)
        columnWidth = columnWidths.get(columnName, 20)
        ds = system.dataset.setValue(ds, row, "width", columnWidth)
            
    table.columnAttributesData = ds