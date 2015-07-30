'''
Created on Jul 24, 2015

@author: Joe
'''
import system
from ils.sfc.common.constants import SQL

#open transaction when window is opened
def internalFrameOpened(rootContainer):
    # Keep the transaction open for one hour...
    table = rootContainer.getComponent("Power Table")
    
    SQL = "SELECT QueueId, QueueKey, Title FROM QueueMaster "\
        "ORDER BY QueueKey "
    print SQL
    pds = system.db.runQuery(SQL)
    table.data = pds

def update(rootContainer):
    print "updating..."
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    row = table.selectedRow
    rootContainer.queueKey = ds.getValueAt(row, "QueueKey")