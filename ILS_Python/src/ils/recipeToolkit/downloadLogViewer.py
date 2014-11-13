'''
Created on Nov 9, 2014

@author: Pete
'''

import system

def internalFrameOpened(rootContainer):
    print "internalFrameOpened"

def internalFrameActivated(rootContainer):
    print "internalFrameActivated"
    refreshMaster(rootContainer)

# Query the master table and update the table with the dataset.
def refreshMaster(rootContainer):
    print "Refreshing the master table..."

    masterTable = rootContainer.getComponent('MasterTable')

    SQL = "SELECT DM.Id, DM.UnitId, UR.FamilyName, DM.Grade, DM.Version, DM.DownloadStartTime, DM.DownloadEndTime, " \
        " DM.Status, DM.TotalDownloads, DM.PassedDownloads, DM.FailedDownloads" \
        " FROM RtDownloadMaster DM, RtUnitRoot UR" \
        " WHERE DM.UnitId = UR.UnitId" \
        " ORDER BY DM.DownloadStartTime DESC"
    
    print SQL
    
    pds = system.db.runQuery(SQL)
    masterTable.data = pds
    masterTable.selectedRow = -1

            
# Update the detail table for the row selected in the master table
def refreshDetail(rootContainer):
    print "Refreshing the master table..."

    masterTable = rootContainer.getComponent('MasterTable')
    selectedRow = masterTable.selectedRow
    if selectedRow < 0:
        downloadId = -1
    else:
        ds = masterTable.data
        downloadId = ds.getValueAt(selectedRow, "Id")
        
    detailTable = rootContainer.getComponent('DetailTable')

    SQL = "SELECT DD.Id, DD.Timestamp, DD.Tag, DD.Success,DD.OutputValue, DD.StoreValue, DD.CompareValue, DD.RecommendedValue," \
        "  DD.Reason, DD.Error" \
        " FROM rtDownloadDetail DD " \
        " WHERE DownloadId = %i" \
        " ORDER BY DD.Id" % (downloadId)
    
    print SQL
    
    pds = system.db.runQuery(SQL)
    detailTable.data = pds                        