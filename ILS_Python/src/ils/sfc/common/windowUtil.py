'''
Created on Jan 28, 2016

@author: rforbes
'''

# All window tables listed in an order that is safe for deletion, i.e. will
# satisfy foreign key constraints
windowTables = [
'SfcDialogMessage',
'SfcReviewFlowsTable',
'SfcReviewFlows',
'SfcReviewDataTable',
'SfcReviewData'
'SfcManualDataEntryTable',
'SfcManualDataEntry',
'SfcTimeDelayNotification',
'SfcInputChoices',
'SfcInput',
'SfcWindow'
]
def cleanupWindows(controlPanelId, database):
    '''remove all database records for persistent windows associated with
       the given control panel'''
    import system.db
    windowIdResults = system.db.runQuery("select windowId from SfcWindow where controlPanelId = %d" % (controlPanelId), database)
    for windowIdResult in windowIdResults:
        windowId = windowIdResult[0]
        for table in windowTables:
            sql = "delete from %s where windowId = '%s'" % (table, windowId)
            system.db.runUpdateQuery(sql)
            
def removeControlPanelRecord(controlPanelId, database):
    '''Remove the database record for the given control panel, and all
       associated window records'''
    import system.db
    cleanupWindows(controlPanelId, database)
    system.db.runUpdateQuery("delete from SfcControlPanel where controlPanelId = '%s'" % (controlPanelId), database)

