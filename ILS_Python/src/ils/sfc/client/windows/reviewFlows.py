'''
Created on Sep 22, 2015

@author: rforbes
'''

import system
from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.core import setRecipeData
from ils.sfc.client.windows.reviewData import setAdviceVisibiity

def internalFrameOpened(rootContainer):
    database = getDatabaseClient()
    
    print "In %s.internalFrameOpened()" % (__name__)

    windowId = rootContainer.windowId
    
    tabs = rootContainer.getComponent("tabs")
    tabs.selectedTab = "primary"
    
    title = system.db.runScalarQuery("Select title from SfcWindow where windowId = '%s'" % (windowId), database)
    rootContainer.title = title
    
    pds = system.db.runQuery("select * from SfcReviewFlows where windowId = '%s'" % (windowId), database)
    record = pds[0]
    rootContainer.targetStepUUID = record["targetStepUUID"]
    rootContainer.responseKey = record["responseKey"]
    heading1 = record["heading1"]
    heading2 = record["heading2"]
    heading3 = record["heading3"]
    primaryTabLabel = record["primaryTabLabel"]
    secondaryTabLabel = record["secondaryTabLabel"]

    ds = tabs.tabData
    ds = system.dataset.setValue(ds, 0, "DISPLAY_NAME", primaryTabLabel)
    ds = system.dataset.setValue(ds, 1, "DISPLAY_NAME", secondaryTabLabel)
    tabs.tabData = ds
    
    print "Setting the table column headings..."
    table = rootContainer.getComponent("Primary Table")
    
    i = 1
    ds = table.columnAttributesData
    for heading in [heading1, heading2, heading3]:
        key = "data%d" % (i)
        for row in range(ds.rowCount):
            if ds.getValueAt(row, "name") == key:
                ds = system.dataset.setValue(ds, row, 'label', heading)
        i = i + 1
    table.columnAttributesData = ds
    
    print "Populating the primary table..."
    SQL = "select prompt, advice, data1, data2, data3, units from SfcReviewFlowsTable where windowId = '%s' and isPrimary = 1 order by rowNum" % (windowId)
    pds = system.db.runQuery(SQL, database)
    table.data = pds
    
    print "Populating the secondary table..."
    SQL = "select prompt, data1 as value, units from SfcReviewFlowsTable where windowId = '%s' and isPrimary = 0 order by rowNum" % (windowId)
    pds = system.db.runQuery(SQL, database)
    table = rootContainer.getComponent("Secondary Table")
#    setAdviceVisibiity(table, showAdvice, columnWidths)
    table.data = pds
    
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
