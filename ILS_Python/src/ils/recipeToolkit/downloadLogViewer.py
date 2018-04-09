'''
Created on Nov 9, 2014

@author: Pete
'''

import system
from ils.common.config import getDatabaseClient

def display():
    print "Displaying the download log window"
    window="Recipe/DownloadLogViewer"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)

def internalFrameOpened(rootContainer):
    print "internalFrameOpened"

    refreshMaster(rootContainer)
    refreshDetail(rootContainer)
    
    deferredRowSelection(rootContainer)


def internalFrameActivated(rootContainer):
    print "internalFrameActivated"

# There is no good reason why I need to do this other than it was the only way I could get it to work.
# I call the same code when they press the Refresh button as when the window opens and it worked there, but 
# for some reason selecting the first row doesn't work when I open the window unless I do this wait. 
def deferredRowSelection(rootContainer):
    print "Selecting"
    
    def select(rootContainer=rootContainer):
        masterTable = rootContainer.getComponent('MasterTable')
        masterTable.selectedRow = -1
        
    system.util.invokeLater(select)
        
# Query the master table and update the table with the dataset.
def refreshMaster(rootContainer):
    print "Refreshing the master table..."

    db = getDatabaseClient()
    masterTable = rootContainer.getComponent('MasterTable')

    SQL = "SELECT DM.MasterId, DM.RecipeFamilyId, F.RecipeFamilyName, DM.Grade, DM.Version, DM.Type, DM.DownloadStartTime, DM.DownloadEndTime, " \
        " DM.Status, DM.TotalDownloads, DM.PassedDownloads, DM.FailedDownloads" \
        " FROM RtDownloadMaster DM, RtRecipeFamily F" \
        " WHERE DM.RecipeFamilyId = F.RecipeFamilyId" \
        " ORDER BY DM.DownloadStartTime DESC"
    
    print SQL
    
    pds = system.db.runQuery(SQL, database=db)
    masterTable.data = pds
    masterTable.selectedRow = -1

            
# Update the detail table for the row selected in the master table
def refreshDetail(rootContainer):
    print "Refreshing the detail table..."

    db = getDatabaseClient()
    masterTable = rootContainer.getComponent('MasterTable')
    selectedRow = masterTable.selectedRow
    print "The selected row is ", selectedRow
    if selectedRow < 0:
        masterId = -1
    else:
        ds = masterTable.data
        masterId = ds.getValueAt(selectedRow, "MasterId")
        
    detailTable = rootContainer.getComponent('DetailTable')

    SQL = "SELECT DetailId, Timestamp, Tag, Success, OutputValue, StoreValue, CompareValue, RecommendedValue," \
        "  Reason, Error" \
        " FROM RtDownloadDetail " \
        " WHERE MasterId = %i" \
        " ORDER BY DetailId" % (masterId)
    
    print SQL
    
    pds = system.db.runQuery(SQL, database=db)
    detailTable.data = pds