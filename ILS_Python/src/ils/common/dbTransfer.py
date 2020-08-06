'''
Created on Aug 5, 2020

@author: phass
'''

import system
from system.ils.sfc import getDatabaseName
log = system.util.getLogger("com.ils..common.dbTransfer")

config = [
    {"table": "DtApplication", "view": "DtApplicationView", "orderBy": "ApplicationName", "columnsToCompare": ["Post", "UnitName", "ApplicationName", "Description"]},
    {"table": "DtFamily", "view": "DtFamily", "orderBy": "FamilyName", "columnsToCompare": []},
    {"table": "DtQuantOutput", "view": "DtQuantOutputDefinitionView", "orderBy": "ApplicationName, QuantOutputName", "columnsToCompare": []}
    ]

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()", __name__)
    
    tables = []
    for tableDict in config:
        tableName = tableDict.get("table", None)
        if tableName <> None:
            tables.append([tableName])
            
    ds = system.dataset.toDataSet(["tableName"], tables)
    
    tableList = rootContainer.getComponent("Table List")
    tableList.selectedIndex = -1
    tableList.data = ds
    
    ''' Get both the production and client database names and store them in rootContainer properties. '''
    isolationDatabase = getDatabaseName(True)
    rootContainer.isolationDatabase = isolationDatabase
    
    productionDatabase = getDatabaseName(False)
    rootContainer.productionDatabase = productionDatabase

    
def rowSelected(event):
    log.tracef("In %s.rowSelected()", __name__)
    
    rootContainer = event.source.parent
    
    productionDatabase = rootContainer.productionDatabase
    isolationDatabase = rootContainer.isolationDatabase
    
    selectedIndex = event.newValue
    
    if selectedIndex < 0:
        return
    
    tableList = event.source
    tableStructure = getSelectedTableStructure(tableList)
    view = tableStructure.get("view", None)
    orderBy = tableStructure.get("orderBy", None)

    ''' We usually display the contents of a view which expands the ids into values for lookups '''
    
    SQL = "select * from %s" % (view)
    if orderBy <> None:
        SQL = "%s order by %s" % (SQL, orderBy)
    
    log.tracef("SQL: %s", SQL)
    
    pds = system.db.runQuery(SQL, productionDatabase)
    table = rootContainer.getComponent("Production Table")
    table.data = pds
    
    pds = system.db.runQuery(SQL, isolationDatabase)
    table = rootContainer.getComponent("Isolation Table")
    table.data = pds
    
    
def compareCallback(event):
    log.tracef("In %s.compareCallback()", __name__)
    
    rootContainer = event.source.parent
    
    tableList = event.source
    tableStructure = getSelectedTableStructure(tableList)
    table = tableStructure.get("table", None)
    columnsToCompare = tableStructure.get("columnsToCompare", None)
    
    table = rootContainer.getComponent("Production Table")
    dsProduction = table.data
    
    table = rootContainer.getComponent("Isolation Table")
    dsIsolation = table.data
    
    numRows = dsProduction.getRowCount()
    
    dataIsTheSame = True
    for row in range(numRows):
        for column in columnsToCompare:
            log.tracef("Row: %d, Column: %s",  row, column)
            
            productionValue = dsProduction.getValueAt(row, column)
            isolationValue = dsIsolation.getValueAt(row, column)
            
            log.tracef("   comparing %s to %s...", str(productionValue), str(isolationValue))
            if isolationValue <> productionValue:
                dataIsTheSame = False

    if dataIsTheSame:
        system.gui.messageBox("The production and isolation data match!")
    else:
        system.gui.warningBox("The production and isolation data DO NOT match!")

def getSelectedTableStructure(tableList):
    ds = tableList.data
    selectedIndex = tableList.selectedIndex
    tableName = ds.getValueAt(selectedIndex, 0)
    
    log.tracef("The user selected %s", tableName)
    
    for tableDict in config:
        if tableName == tableDict.get("table", None):
            log.tracef("The structure is: %s", str(tableDict))
            return tableDict

    return None