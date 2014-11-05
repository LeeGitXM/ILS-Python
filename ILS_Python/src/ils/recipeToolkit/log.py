'''
Created on Sep 10, 2014

@author: Pete
'''

import system

# I Need to pass the table because in a project with multiple consoles I have two diffferent download tables
def logMaster(unitId, grade, version):

    print "Logging"
    SQL = "insert into RtDownloadMaster (UnitId, Grade, Version, DownloadStartTime) " \
        " values (?, ?, ?, getdate())"
    print SQL
    logId = system.db.runPrepUpdate(SQL, args=[unitId, grade, version], getKey=True)
    return logId

# I Need to pass the table because in a project with multiple consoles I have two diffferent download tables
def logDetail(downloadId, tagParam, output, status, store, compare, recommend, reason):

    print "Logging"
#    SQL = "insert into RtDownloadDetail (TAG_PARAM, OUTPUT, STATUS, STORE, COMPARE, RECOMMEND, REASON, " \
#        "TIME_STAMP) values (?, ?, ?, ?, ?, ?, ?, getdate())"
#    print SQL
#    system.db.runPrepUpdate(SQL, [tagParam, output, status, store, compare, recommend, reason])


# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requeryMaster(rootContainer ):
    print "Refreshing the master table..."

    masterTable = rootContainer.getComponent('MasterTable')
    database = rootContainer.getComponent('DatabaseDropdown').selectedStringValue
    unit = rootContainer.getComponent('UnitDropdown').selectedStringValue

    SQL = "SELECT DM.Id, DM.Unit, DM.Grade, DM.Version, DM.DownloadStartTime, DM.DownloadEndTime" \
        " FROM DownloadMaster DM " \
        + getWhereExtension(unit) + \
        " ORDER BY DM.DownloadStartTime DESC"
    
    print SQL
    
    if len(database)>0:
        pds = system.db.runQuery(SQL,database)
        masterTable.data = pds
            
    else:
        print "recipe.dialogs.definition.refresh: Database not found"

#
# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requeryDetail(rootContainer):
    print "Refreshing the master table..."

    masterTable = rootContainer.getComponent('MasterTable')
    selectedRow = masterTable.selectedRow
    if selectedRow < 0:
        downloadId = -1
    else:
        ds = masterTable.data
        downloadId = ds.getValueAt(selectedRow, "Id")
        
    detailTable = rootContainer.getComponent('DetailTable')
    database = rootContainer.getComponent('DatabaseDropdown').selectedStringValue

    SQL = "SELECT DD.Id, DD.Timestamp, DD.Tag, DD.OutputValue, DD.Success, DD.Reason" \
        " FROM DownloadDetail DD " \
        " WHERE DownloadId = %i" \
        " ORDER BY DD.Id" % (downloadId)
    
    print SQL
    
    if len(database)>0:
        pds = system.db.runQuery(SQL,database)
        detailTable.data = pds
            
    else:
        print "recipe.dialogs.definition.refresh: Database not found"
    
# Enhance the joining where clause with the selection
# from the processing unit dropdown.
def getWhereExtension(unit):
    where = ""
    if unit != "ALL":
        where = " WHERE DM.Unit = '"+unit+"'"
    return where
    
# When the screen is first displayed, set widgets for user defaults
def initialize(rootContainer):
    dropdown = rootContainer.getComponent("DatabaseDropdown")
    print "NEED SOME HELP HERE"
#    dropdown.setSelectedStringValue(project.recipe.userdefaults.get("DATABASE"))
    dropdown = rootContainer.getComponent("UnitDropdown")
#    dropdown.setSelectedStringValue(project.recipe.userdefaults.get("UNIT"))

                            
