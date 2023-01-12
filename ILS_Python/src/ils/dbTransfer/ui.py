'''
Created on Aug 21, 2020

@author: phass
'''

import system
from ils.config.common import getProductionDatabase, getIsolationDatabase
from ils.dbTransfer.constants import config, FLOAT, STRING
from ils.dbTransfer.common import updateFolderPath, getSelectedTableStructure, createClass, dsToList

from ils.common.util import clearDataset

from ils.log import getLogger
log = getLogger(__name__)

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()", __name__)
    
    tables = []
    for tableDict in config:
        tableName = tableDict.get("table", None)
        if tableName <> None:
            tables.append([tableName])
            
    ds = system.dataset.toDataSet(["tableName"], tables)
    
    tableList = rootContainer.getComponent("Table Container").getComponent("Table List")
    tableList.selectedIndex = -1
    tableList.data = ds
    
    ''' Get both the production and client database names and store them in rootContainer properties. ''' 
    projectName = system.project.getProjectName()
    rootContainer.isolationDatabase = getIsolationDatabase(projectName)
    rootContainer.productionDatabase = getProductionDatabase(projectName)
    
    rootContainer.result = ""

def configureCell(self, value, textValue, selected, rowIndex, colIndex, colName, rowView, colView):
    extra = False
    badCells = self.badCells
    extraRows = self.extraRows
    background = 'white'
    
    if rowIndex == self.selectedRow:
        background = '250,214,138'
    else:
        for row in range(extraRows.getRowCount()):
            extraRow = extraRows.getValueAt(row, "row")
            if extraRow == rowIndex: 
                background = 'red'
        
        if not(extra):
            for row in range(badCells.getRowCount()):
                badRow = badCells.getValueAt(row, "row")
                badColumnName = badCells.getValueAt(row, "columnName")
            
                if badRow == rowIndex and badColumnName == colName: 
                    background = 'yellow'
                    
    return {'background': background}


def rowSelected(event):
    log.tracef("In %s.rowSelected()", __name__)
    
    selectedIndex = event.newValue
    if selectedIndex < 0:
        return
    
    rootContainer = event.source.parent.parent
    refresh(rootContainer)
    

def refreshCallback(event):
    rootContainer = event.source.parent
    refresh(rootContainer)
    
    
def refresh(rootContainer):
    dbProduction = rootContainer.productionDatabase
    dbIsolation = rootContainer.isolationDatabase
    tableList = rootContainer.getComponent("Table Container").getComponent("Table List")
    
    tableStructure = getSelectedTableStructure(tableList)
    productionTable = rootContainer.getComponent("Production Container").getComponent("Production Table")
    isolationTable = rootContainer.getComponent("Isolation Container").getComponent("Isolation Table")
    
    refreshPowerTables(rootContainer, tableList, tableStructure, productionTable, isolationTable, dbProduction, dbIsolation)
    compare(rootContainer, tableList, tableStructure, productionTable, isolationTable)
    

def refreshPowerTables(rootContainer, tableList, tableStructure, productionTable, isolationTable, dbProduction, dbIsolation):
    
    #--------------------------------------------------------------------------------
    def update(tableStructure, table, db):
        log.tracef("In %s.update()...", __name__)
        
        selectQueryName = tableStructure.get("selectQueryName", None)
        tableName = tableStructure.get("table", None)
        selectQuery = tableStructure.get("selectQuery", None)
        log.tracef("   select query name: %s", str(selectQueryName))
        log.tracef("   select query: %s", str(selectQuery))
        
        if selectQueryName <> None:
            ds = system.db.runNamedQuery(selectQueryName, {"database": db})
        else:
            pds = system.db.runQuery(selectQuery, database=db)
            ds = system.dataset.toDataSet(pds)
    
        table.selectedRow = -1
        ds = updateFolderPath(ds, db)
            
        table.data = ds
        table.numberOfRows = ds.getRowCount()
        table.badCells = clearDataset(table.badCells)
        table.extraRows = clearDataset(table.extraRows)
    #------------------------------------------------------------------------------
    
    log.tracef("In %s.refreshPowerTables()...", __name__)
    update(tableStructure, productionTable, dbProduction)
    update(tableStructure, isolationTable, dbIsolation)


def compare(rootContainer, tableList, tableStructure, productionTable, isolationTable):
    log.tracef("In %s.compare()", __name__)
    
    columnsToCompare = tableStructure.get("columnsToCompareAndUpdate", None)
    
    dsProduction = productionTable.data
    numProductionRows = dsProduction.getRowCount()
    
    dsIsolation = isolationTable.data
    numIsolationRows = dsIsolation.getRowCount()
    
    extraProductionRows, extraIsolationRows = compareExtraRows(tableStructure, dsProduction, numProductionRows, dsIsolation, numIsolationRows)
        
    if len(extraProductionRows) > 0 or len(extraIsolationRows) > 0:
        #system.gui.messageBox("The production and isolation tables have different numbers of rows!")
        rootContainer.result = "DIFFERENT"
        
        dsExtraRows = system.dataset.toDataSet(["row"], extraProductionRows)
        productionTable.extraRows = dsExtraRows
        productionTable.data = productionTable.data     # This causes the configureCell extension function to run on each cell that animates the background
        
        dsExtraRows = system.dataset.toDataSet(["row"], extraIsolationRows)
        isolationTable.extraRows = dsExtraRows
        isolationTable.data = isolationTable.data     # This causes the configureCell extension function to run on each cell that animates the background
    
    else:    
        dataIsTheSame = True
        badRows = []
        badCells = []
        for row in range(numProductionRows):
            for columnDict in columnsToCompare:
                column = columnDict.get("columnName", None)
                compare = columnDict.get("compare", True)
                dataType = columnDict.get("dataType", STRING)
                if compare:                    
                    productionValue = dsProduction.getValueAt(row, column)
                    isolationValue = dsIsolation.getValueAt(row, column)
                    if dataType == FLOAT and productionValue != None and isolationValue != None:
                        ''' If the data type is a FLOAT, then we need to accept Java roundoff errors.  I will use a 5% margin or error '''
                        if productionValue < 1.0:
                            errorValue = 0.1
                        else:
                            errorValue = productionValue * 0.05
                        
                        if not(isolationValue > productionValue - errorValue and isolationValue < productionValue + errorValue):
                            log.tracef("      *** MISMATCH ***")
                            badCells.append([row, column])
                            dataIsTheSame = False
                            if row + 1 not in badRows:
                                badRows.append(row + 1)
                    else:
                        if isolationValue <> productionValue:
                            log.tracef("      *** MISMATCH ***")
                            badCells.append([row, column])
                            dataIsTheSame = False
                            if row + 1 not in badRows:
                                badRows.append(row + 1)
    
        dsBadCells = system.dataset.toDataSet(["row", "columnName"],badCells)
        productionTable = rootContainer.getComponent("Production Container").getComponent("Production Table")
        productionTable.badCells = dsBadCells
        productionTable.data = productionTable.data     # This causes the configureCell extension function to run on each cell that animates the background
        
        isolationTable = rootContainer.getComponent("Isolation Container").getComponent("Isolation Table")
        isolationTable.badCells = dsBadCells
        isolationTable.data = isolationTable.data     # This causes the configureCell extension function to run on each cell that animates the background
    
        if dataIsTheSame:
            rootContainer.result = "MATCH"
            #system.gui.messageBox("The production and isolation data match!")
        else:
            rootContainer.result = "DIFFERENT"
            #system.gui.messageBox("Warning: The production and isolation data DO NOT match!  Rows %s do not match" % str(badRows))


def compareExtraRows(tableStructure, dsProduction, numProductionRows, dsIsolation, numIsolationRows):
    
    def compare(ds1, num1Rows, ds2, num2Rows):
        extraRows = []
        
        ''' iterate over the first dataset looking for extra rows that do not exist in 2nd dataset '''
        for row1 in range(num1Rows):
            found = False
            vals1 = []
            for column in uniqueColumns:
                vals1.append(ds1.getValueAt(row1, column))
                
            log.tracef("Looking for row %d - %s", row1, str(vals1))
            for row2 in range(num2Rows):
                vals2=[]
                for column in uniqueColumns:
                    vals2.append(ds2.getValueAt(row2, column))
            
                if vals1 == vals2:
                    log.tracef("   +++ FOUND IT +++")
                    found = True
                    break       # Hopefully just break out of the inner loop
            
            if not(found):
                extraRows.append([row1])
            
        return extraRows
    
    uniqueColumns = tableStructure.get("uniqueColumns", None)

    extraProductionRows = compare(dsProduction, numProductionRows, dsIsolation, numIsolationRows)
    extraIsolationRows = compare(dsIsolation, numIsolationRows, dsProduction, numProductionRows)
    
    log.tracef("The extra production rows are: %s", str(extraProductionRows))
    log.tracef("The extra isolation rows are: %s", str(extraIsolationRows))
    
    return extraProductionRows, extraIsolationRows


def deleteRowsCallback(event):
    log.tracef("In %s.deleteRowsCallback()", __name__)
        
    rootContainer = event.source.parent.parent
    dbProduction = rootContainer.productionDatabase
    dbIsolation = rootContainer.isolationDatabase
    
    tableList = rootContainer.getComponent("Table Container").getComponent("Table List")
    tableStructure = getSelectedTableStructure(tableList)
    if tableStructure == None:
        system.gui.errorBox("Unable to locate the table structure.")
        return
    
    if event.source.name == "Delete Production Rows Button":
        db = dbProduction
        table = event.source.parent.getComponent("Production Table")
    elif event.source.name == "Delete Isolation Rows Button":
        db = dbIsolation
        table = event.source.parent.getComponent("Isolation Table")
    else:
        system.gui.errorBox("Error - could not locate table")
        return
    
    ds = table.data
    selectedRow = table.selectedRow
    if selectedRow < 0:
        system.gui.messageBox("Please select a row!")
        return
    
    log.tracef("Removing row: %d", selectedRow)
    
    dbTable = createClass(tableStructure)
    dbTable.delete(ds, selectedRow, db)
    
    productionTable = rootContainer.getComponent("Production Container").getComponent("Production Table")
    isolationTable = rootContainer.getComponent("Isolation Container").getComponent("Isolation Table")
    refreshPowerTables(rootContainer, tableList, tableStructure, productionTable, isolationTable, dbProduction, dbIsolation)
    compare(rootContainer, tableList, tableStructure, productionTable, isolationTable)
    

def updateCallback(event):
    log.tracef("In %s.updateCallback()", __name__)

    rootContainer = event.source.parent
    dbProduction = rootContainer.productionDatabase
    dbIsolation = rootContainer.isolationDatabase
    tableList = rootContainer.getComponent("Table Container").getComponent("Table List")
    tableStructure = getSelectedTableStructure(tableList)
    
    if tableStructure == None:
        return
    
    tableProduction = rootContainer.getComponent("Production Container").getComponent("Production Table")
    dsProduction = tableProduction.data
    numProductionRows = dsProduction.getRowCount()
    
    tableIsolation = rootContainer.getComponent("Isolation Container").getComponent("Isolation Table")
    dsIsolation = tableIsolation.data
    numIsolationRows = dsIsolation.getRowCount()
    
    if event.source.name == "Update Isolation From Production Button":
        updateDatabaseTable(rootContainer, tableStructure, tableProduction, dsProduction, numProductionRows, dbProduction, tableIsolation, dsIsolation, numIsolationRows, dbIsolation)
    else:
        updateDatabaseTable(rootContainer, tableStructure, tableIsolation, dsIsolation, numIsolationRows, dbIsolation, tableProduction, dsProduction, numProductionRows, dbProduction)
    
    ''' Need to wait for the asynchronous thread to finish before refreshing '''
        
def refreshWatcher(event):
    log.infof("In %s.refreshWatcher() refreshing because the work is done...", __name__)
    rootContainer = event.source
    dbProduction = rootContainer.productionDatabase
    dbIsolation = rootContainer.isolationDatabase
    tableList = rootContainer.getComponent("Table Container").getComponent("Table List")
    tableStructure = getSelectedTableStructure(tableList)
    
    if tableStructure == None:
        return
    
    tableProduction = rootContainer.getComponent("Production Container").getComponent("Production Table") 
    tableIsolation = rootContainer.getComponent("Isolation Container").getComponent("Isolation Table")
    
    refreshPowerTables(rootContainer, tableList, tableStructure, tableProduction, tableIsolation, dbProduction, dbIsolation)
    compare(rootContainer, tableList, tableStructure, tableProduction, tableIsolation)


def updateDatabaseTable(rootContainer, tableStructure, tableSource, dsSource, numSourceRows, dbSource, tableDestination, dsDestination, numDestinationRows, dbDestination):
    
    def worker(rootContainer=rootContainer, tableStructure=tableStructure, tableSource=tableSource, dsSource=dsSource, numSourceRows=numSourceRows, dbSource=dbSource, 
               tableDestination=tableDestination, dsDestination=dsDestination, numDestinationRows=numDestinationRows, dbDestination=dbDestination):
        print "Starting worker asynchronously..."
        rootContainer.result = "WORKING"
        tableName = tableStructure.get("table", None)
        if tableName == None:
            system.gui.errorBox("Unknown table name!")
            return
    
        log.infof("In %s.updateDatabaseTable() updating %s from %s to %s...", __name__, tableName, dbSource, dbDestination)
    
        dbTable = createClass(tableStructure)
        
        if tableName == "SfcRecipeDataFolder":
            system.gui.messageBox("Depending on the nature of the missing folders, it may take several iteations to completely and accurately transfer folders!")
        
        ''' First get the number of rows in sync '''
        extraSourceRows = dsToList(tableSource.extraRows)
        
        print "The extra rows are: ", extraSourceRows 
    
        if len(extraSourceRows) > 0:
            ''' insert a row into the destination for every extra source row ''' 
            dbTable.insert(extraSourceRows, dsSource, dbDestination)
        else:
            ''' Update the values of each row '''
            dbTable.update(numSourceRows, dsSource, dbSource, dsDestination, dbDestination)
        
        rootContainer.result = "DONE"
        print "Finished asynchronous work!"
    
    print "Calling worker() asynchronously..."
    system.util.invokeAsynchronous(worker)
        