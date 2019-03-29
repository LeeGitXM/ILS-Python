'''
Created on Sep 22, 2015

@author: rforbes

This step caused some problems because of the brilliant decision to have an implied ".value" on the response key
'''

import system, string
from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.core import splitKey, setRecipeData
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
    print "...fetched %d rows for the primary table" % (len(pds))
    table.data = pds
    
    print "Populating the secondary table..."
    SQL = "select prompt, data1 as value, units from SfcReviewFlowsTable where windowId = '%s' and isPrimary = 0 order by rowNum" % (windowId)
    pds = system.db.runQuery(SQL, database)
    print "...fetched %d rows for the secondary table" % (len(pds))
    table = rootContainer.getComponent("Secondary Table")
#    setAdviceVisibiity(table, showAdvice, columnWidths)
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

    folder,key,attribute = splitKey(responseKey)
    setRecipeData(targetStepUUID, folder, key, attribute, response, db)
    system.nav.closeParentWindow(event)