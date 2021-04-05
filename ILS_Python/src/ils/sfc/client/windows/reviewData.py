'''
Created on Jan 14, 2015

@author: rforbes

This step caused some problems because of the brilliant decision to have an implied ".value" on the response key
'''

import system, string
from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.api import s88GetStepInfoFromUUID
from ils.sfc.recipeData.core import splitKey, setRecipeData

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
    print "In %s.okActionPerformed()" % (__name__)
    actionPerformed(event, "OK")
  
def cancelActionPerformed(event):
    print "In %s.cancelActionPerformed()" % (__name__)
    actionPerformed(event, "CANCEL")

def actionPerformed(event, response):
    print "In %s.sctionPerformed(), the response is: %s" % (__name__, response)
    db = getDatabaseClient()
    window=system.gui.getParentWindow(event)
    rootContainer = window.getRootContainer()
    targetStepUUID = rootContainer.targetStepUUID
    responseKey = rootContainer.responseKey
    
    '''
    If this is in a library then they will have supplied the attribute, if it isn't in a library then there is an implied ".value"
    '''
    if string.lower(responseKey[len(responseKey) - 6:]) != ".value":
        responseKey = responseKey + ".value"
    print "From the root container properties, targetStepUUID: %s, responseKey: %s" % (targetStepUUID, responseKey)
    folder,key,attribute = splitKey(responseKey)
    chartPath, stepName = s88GetStepInfoFromUUID(targetStepUUID, db)
    setRecipeData(stepName, targetStepUUID, folder, key, attribute, response, db)
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