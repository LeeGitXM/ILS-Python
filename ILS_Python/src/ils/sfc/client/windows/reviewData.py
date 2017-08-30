'''
Created on Jan 14, 2015

@author: rforbes
'''

import system, time
from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.core import setRecipeData

def internalFrameOpened(rootContainer):
    database = getDatabaseClient()
    
    windowId = rootContainer.windowId
    
    print "In %s.internalFrameOpened(), the windowId is: <%s>" % (__name__, windowId)
    
    title = system.db.runScalarQuery("Select title from SfcWindow where windowId = '%s'" % (windowId), database)
    rootContainer.title = title
    
    tabs = rootContainer.getComponent("tabs")
    tabs.selectedTab = "primary"
    
    pds = system.db.runQuery("select showAdvice, targetStepUUID, responseKey, primaryTabLabel, secondaryTabLabel from SfcReviewData where windowId = '%s'" % (str(windowId)), database)
    print "Fetched %d records from sfcReviewData" % (len(pds))
    
    record = pds[0]
    showAdvice = record["showAdvice"]
    rootContainer.targetStepUUID = record["targetStepUUID"]
    rootContainer.responseKey = record["responseKey"]
    primaryTabLabel = record["primaryTabLabel"]
    secondaryTabLabel = record["secondaryTabLabel"]
    
    tabStrip = rootContainer.getComponent("tabs")
    ds = tabStrip.tabData
    ds = system.dataset.setValue(ds, 0, "DISPLAY_NAME", primaryTabLabel)
    ds = system.dataset.setValue(ds, 1, "DISPLAY_NAME", secondaryTabLabel)
    tabStrip.tabData = ds
    
    if showAdvice:
        columnWidths = {"prompt": 215, "advice": 215, "value": 100, "units": 60}
    else:
        columnWidths = {"prompt": 430, "advice": 0, "value": 100, "units": 60}
    
    print "Populating the primary table..."
    SQL = "select prompt, advice, value, units from SfcReviewDataTable where windowId = '%s' and isPrimary = 1 order by rowNum" % (windowId)
    pds = system.db.runQuery(SQL, database)
    table = rootContainer.getComponent("Primary Table")
    setAdviceVisibiity(table, showAdvice, columnWidths)
    table.data = pds
    
    print "Populating the secondary table..."
    SQL = "select prompt, advice, value, units from SfcReviewDataTable where windowId = '%s' and isPrimary = 0 order by rowNum" % (windowId)
    pds = system.db.runQuery(SQL, database)
    table = rootContainer.getComponent("Secondary Table")
    setAdviceVisibiity(table, showAdvice, columnWidths)
    table.data = pds

    if len(pds) > 0:
        rootContainer.hasSecondary = True
    else:
        rootContainer.hasSecondary = False

    print "...finished"
 
def okActionPerformed(event):
    actionPerformed(event, "OK")
  
def cancelActionPerformed(event):
    actionPerformed(event, "CANCEL")

def actionPerformed(event, response):
    db = getDatabaseClient()
    window=system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    targetStepUUID = rootContainer.targetStepUUID
    responseKey = rootContainer.responseKey
    setRecipeData(targetStepUUID, responseKey, "value", response, db)
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