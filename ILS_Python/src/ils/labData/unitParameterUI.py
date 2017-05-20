'''
Created on May 16, 2017

@author: phass
'''

import system
from ils.common.config import getDatabaseClient

# Open transaction when window is opened
def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()..."
    refresh(rootContainer)

    
def refresh(rootContainer):
    print "...refreshing..."
    db = getDatabaseClient()
    SQL = "select * from TkUnitParameter order by UnitParameterTagName"
    pds = system.db.runQuery(SQL, database=db)

    table = rootContainer.getComponent("Unit Parameter Power Table")
    table.data = pds

def updateBufferTable(unitParameterTable, rowIndex):
    db = getDatabaseClient()
    rootContainer = unitParameterTable.parent
    
    ds = unitParameterTable.data
    unitParameterId = ds.getValueAt(rowIndex, "UnitParameterId")
    print "Selected Unit Parameter: ", unitParameterId
    
    SQL = "select * from TkUnitParameterBuffer where UnitParameterId = %d" % (unitParameterId)
    pds = system.db.runQuery(SQL, database=db)
    table = rootContainer.getComponent("Unit Parameter Buffer Table")
    table.data = pds

def clearBufferTable(rootContainer):
    table = rootContainer.getComponent("Unit Parameter Buffer Table")
    ds = table.data
    from ils.common.util import clearDataset
    ds = clearDataset(ds)
    table.data = ds