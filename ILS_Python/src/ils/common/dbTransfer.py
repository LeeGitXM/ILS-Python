'''
Created on Aug 5, 2020

@author: phass
'''

import system
from system.ils.sfc import getDatabaseName
from ils.common.util import clearDataset

log = system.util.getLogger("com.ils..common.dbTransfer")

PRODUCTION = "production"
ISOLATION = "isolation"

''' Column data types '''
STRING = "string"
LOOKUP = "lookup"
BOOLEAN = "boolean"
FLOAT = "float"
INTEGER = "integer"


config = [
    {
        "table": "DtApplication", 
        "selectQueryName": "DB Transfer/DtApplication", 
        "primaryKey": "ApplicationId",
        "columnsToCompareAndUpdate": [
                {"columnName": "ApplicationName", "dataType": STRING},
                {"columnName": "UnitName", "dataType": LOOKUP},
                {"columnName": "Description", "dataType": STRING},
                {"columnName": "IncludeInMainMenu", "dataType": BOOLEAN},
                {"columnName": "GroupRampMethod", "dataType": LOOKUP},
                {"columnName": "QueueKey", "dataType": LOOKUP},
                {"columnName": "NotificationStrategy", "dataType": STRING},
                {"columnName": "Managed", "dataType": BOOLEAN}
                ],
        "uniqueColumns": ["ApplicationName"]
        },
          
    {
        "table": "DtFamily", 
        "selectQueryName": "DB Transfer/DtFamily",
        "primaryKey": "FamilyId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ApplicationName", "dataType": LOOKUP},
            {"columnName": "FamilyName", "dataType": STRING},
            {"columnName": "FamilyPriority", "dataType": FLOAT},
            {"columnName": "Description", "dataType": STRING}
            ],
        "uniqueColumns": ["ApplicationName", "FamilyName"]
        },
          
    {
        "table": "DtFinalDiagnosis", 
        "selectQueryName": "DB Transfer/DtFinalDiagnosis",
        "primaryKey": "FinalDiagnosisId",
        "columnsToCompareAndUpdate": [
            {"columnName": "FamilyName", "dataType": LOOKUP},
            {"columnName": "FinalDiagnosisName", "dataType": STRING},
            {"columnName": "FinalDiagnosisLabel", "dataType": STRING},
            {"columnName": "FinalDiagnosisPriority", "dataType": FLOAT},
            {"columnName": "CalculationMethod", "dataType": STRING},
            {"columnName": "Constant", "dataType": BOOLEAN},
            {"columnName": "PostTextRecommendation", "dataType": BOOLEAN},
            {"columnName": "PostProcessingCallback", "dataType": STRING},
            {"columnName": "RefreshRate", "dataType": INTEGER},
            {"columnName": "Comment", "dataType": STRING},
            {"columnName": "TextRecommendation", "dataType": STRING},
            {"columnName": "Explanation", "dataType": STRING},
            {"columnName": "TrapInsignificantRecommendations", "dataType": BOOLEAN},
            {"columnName": "ManualMoveAllowed", "dataType": BOOLEAN},
            {"columnName": "ShowExplanationWithRecommendation", "dataType": BOOLEAN}
            ],
        "uniqueColumns": ["ApplicationName", "FamilyName", "FinalDiagnosisName"]
        },
    
    {
        "table": "DtQuantOutput", 
        "selectQueryName": "DB Transfer/DtQuantOutput",
        "primaryKey": "QuantOutputId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ApplicationName", "dataType": LOOKUP},
            {"columnName": "QuantOutputName", "dataType": STRING},
            {"columnName": "TagPath", "dataType": STRING},
            {"columnName": "MostNegativeIncrement", "dataType": FLOAT},
            {"columnName": "MostPositiveIncrement", "dataType": FLOAT},
            {"columnName": "MinimumIncrement", "dataType": FLOAT},
            {"columnName": "IgnoreMinimumIncrement", "dataType": BOOLEAN},
            {"columnName": "SetpointHighLimit", "dataType": FLOAT},
            {"columnName": "SetpointLowLimit", "dataType": FLOAT},
            {"columnName": "IncrementalOutput", "dataType": BOOLEAN},
            {"columnName": "FeedbackMethod", "dataType": LOOKUP}
            ],
        "uniqueColumns": ["ApplicationName", "QuantOutputName"]
        },
          
    {
        "table": "DtRecommendationDefinition", 
        "selectQueryName": "DB Transfer/DtRecommendationDefinition",
        "primaryKey": "RecommendationDefinitionId",
        "columnsToCompareAndUpdate": [
            {"columnName": "FinalDiagnosisName", "dataType": LOOKUP},
            {"columnName": "QuantOutputName", "dataType": LOOKUP}
            ],
        "uniqueColumns": ["FinalDiagnosisName", "QuantOutputName"]
        }
          
    ]


lookups = [       
        {
        "name": "ApplicationName",
        "sql": "select applicationId from DtApplication where ApplicationName = ",
        "idColumnName": "ApplicationId"
        },
           
        {
        "name": "FamilyName",
        "sql": "select familyId from DtFamily where FamilyName = ",
        "idColumnName": "FamilyId"
        },
           
        {
        "name": "FeedbackMethod",
        "sql": "select LookupId from Lookup where LookupTypeCode = 'FeedbackMethod' and LookupName = ",
        "idColumnName": "FeedbackMethodId"
        },
           
        {
        "name": "FinalDiagnosisName",
        "sql": "select finalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName = ",
        "idColumnName": "FinalDiagnosisId"
        },
    
        {
        "name": "GroupRampMethod",
        "sql": "select LookupId from Lookup where LookupTypeCode = 'GroupRampMethod' and LookupName = ",
        "idColumnName": "GroupRampMethodId"
        },
   
        {
        "name": "QuantOutputName",
        "sql": "select QuantOutputId from DtQuantOutput where QuantOutputName = ",
        "idColumnName": "QuantOutputId"
        },

        {
        "name": "QueueKey",
        "sql": "select queueId from QueueMaster where QueueKey = ",
        "idColumnName": "MessageQueueId"
        },
           
        {
        "name": "UnitName",
        "sql": "select unitId from TkUnit where unitName = ",
        "idColumnName": "UnitId"
        }
    
    ]


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
    dbIsolation = getDatabaseName(True)
    rootContainer.isolationDatabase = dbIsolation
    
    dbProduction = getDatabaseName(False)
    rootContainer.productionDatabase = dbProduction

    
def rowSelected(event):
    log.tracef("In %s.rowSelected()", __name__)
    
    rootContainer = event.source.parent.parent
    
    dbProduction = rootContainer.productionDatabase
    dbIsolation = rootContainer.isolationDatabase
    
    selectedIndex = event.newValue
    
    if selectedIndex < 0:
        return
    
    tableList = event.source
    updatePowerTables(rootContainer, tableList, dbProduction, dbIsolation)
    
def updatePowerTables(rootContainer, tableList, dbProduction, dbIsolation):
    tableStructure = getSelectedTableStructure(tableList)
    selectQueryName = tableStructure.get("selectQueryName", None)
    log.tracef("Using named query named: %s", selectQueryName)
    
    pds = system.db.runNamedQuery(selectQueryName, {"database": dbProduction})
    table = rootContainer.getComponent("Production Container").getComponent("Production Table")
    table.data = pds
    
    ds = table.badCells
    ds = clearDataset(ds)
    table.badCells = ds
    
    ds = table.extraRows
    ds = clearDataset(ds)
    table.extraRows = ds
    
    
    pds = system.db.runNamedQuery(selectQueryName, {"database":dbIsolation})
    table = rootContainer.getComponent("Isolation Container").getComponent("Isolation Table")
    table.data = pds
    
    ds = table.badCells
    ds = clearDataset(ds)
    table.badCells = ds
    
    ds = table.extraRows
    ds = clearDataset(ds)
    table.extraRows = ds
    
    
def compareCallback(event):
    log.tracef("In %s.compareCallback()", __name__)
    
    rootContainer = event.source.parent
    
    tableList = rootContainer.getComponent("Table Container").getComponent("Table List")
    tableStructure = getSelectedTableStructure(tableList)
    
    if tableStructure == None:
        return
    
    table = tableStructure.get("table", None)
    columnsToCompare = tableStructure.get("columnsToCompareAndUpdate", None)
    
    dsProduction, numProductionRows = getTableData(rootContainer, PRODUCTION)
    dsIsolation, numIsolationRows = getTableData(rootContainer, ISOLATION)
    
    if numProductionRows <> numIsolationRows:
        system.gui.warningBox("The production and isolation tables have different numbers of rows!")
        extraProductionRows, extraIsolationRows = compareExtraRows(tableStructure, dsProduction, numProductionRows, dsIsolation, numIsolationRows)
        
        dsExtraRows = system.dataset.toDataSet(["row"], extraProductionRows)
        table = rootContainer.getComponent("Production Container").getComponent("Production Table")
        table.extraRows = dsExtraRows
        table.data = table.data     # This causes the configureCell extension function to run on each cell that animates the background
        
        dsExtraRows = system.dataset.toDataSet(["row"], extraIsolationRows)
        table = rootContainer.getComponent("Isolation Container").getComponent("Isolation Table")
        table.extraRows = dsExtraRows
        table.data = table.data     # This causes the configureCell extension function to run on each cell that animates the background
        return
    
    dataIsTheSame = True
    badRows = []
    badCells = []
    for row in range(numProductionRows):
        for columnDict in columnsToCompare:
            column = columnDict.get("columnName", None)
            log.tracef("Row: %d, Column: %s",  row, column)
            
            productionValue = dsProduction.getValueAt(row, column)
            isolationValue = dsIsolation.getValueAt(row, column)
            
            log.tracef("   comparing %s to %s...", str(productionValue), str(isolationValue))
            if isolationValue <> productionValue:
                log.tracef("      *** MISMATCH ***")
                badCells.append([row, column])
                dataIsTheSame = False
                if row + 1 not in badRows:
                    badRows.append(row + 1)

    dsBadCells = system.dataset.toDataSet(["row", "columnName"],badCells)
    table = rootContainer.getComponent("Production Container").getComponent("Production Table")
    table.badCells = dsBadCells
    table.data = table.data     # This causes the configureCell extension function to run on each cell that animates the background
    
    table = rootContainer.getComponent("Isolation Container").getComponent("Isolation Table")
    table.badCells = dsBadCells
    table.data = table.data     # This causes the configureCell extension function to run on each cell that animates the background

    if dataIsTheSame:
        system.gui.messageBox("The production and isolation data match!")
    else:
        system.gui.warningBox("The production and isolation data DO NOT match!  Rows %s do not match" % str(badRows))


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


def getSelectedTableStructure(tableList):
    ds = tableList.data
    selectedIndex = tableList.selectedIndex
    if selectedIndex < 0:
        return None
    
    tableName = ds.getValueAt(selectedIndex, 0)
    
    log.tracef("The user selected %s", tableName)
    
    for tableDict in config:
        if tableName == tableDict.get("table", None):
            log.tracef("The structure is: %s", str(tableDict))
            return tableDict

    return None


def getTableData(rootContainer, dbType):
    if dbType == PRODUCTION:
        table = rootContainer.getComponent("Production Container").getComponent("Production Table")
    else:
        table = rootContainer.getComponent("Isolation Container").getComponent("Isolation Table")
    
    ds = table.data
    numRows = ds.getRowCount()
    
    return ds, numRows


def updateCallback(event):
    log.tracef("In %s.updateIsolationFromProductionCallback()", __name__)
    
    rootContainer = event.source.parent
    dbProduction = rootContainer.productionDatabase
    dbIsolation = rootContainer.isolationDatabase
    tableList = rootContainer.getComponent("Table Container").getComponent("Table List")
    tableStructure = getSelectedTableStructure(tableList)
    
    if tableStructure == None:
        return
    
    dsProduction, numProductionRows = getTableData(rootContainer, PRODUCTION)
    dsIsolation, numIsolationRows = getTableData(rootContainer, ISOLATION)
    
    if event.source.name == "Update Isolation From Production Button":
        updateTable(tableStructure, dsProduction, numProductionRows, dbProduction, dsIsolation, numIsolationRows, dbIsolation)
    else:
        updateTable(tableStructure, dsIsolation, numIsolationRows, dbIsolation, dsProduction, numProductionRows, dbProduction)
    
    updatePowerTables(rootContainer, tableList, dbProduction, dbIsolation)


def updateTable(tableStructure, dsSource, numSourceRows, dbSource, dsDestination, numDestinationRows, dbDestination):
    tableName = tableStructure.get("table", None)
    if tableName == None:
        system.gui.errorBox("Unknown table name!")
        return

    log.tracef("In %s.updateTable() updating %s from %s to %s...", __name__, tableName, dbSource, dbDestination)
    primaryKey = tableStructure.get("primaryKey", None)
    if primaryKey == None:
        system.gui.errorBox("Unknown primary Key!")
        return
    
    columnsToUpdate = tableStructure.get("columnsToCompareAndUpdate", None)
    if columnsToUpdate == None:
        system.gui.errorBox("Unknown columns to update!")
        return
    
    ''' First get the number of rows in sync '''
    extraSourceRows, extraDestinationRows = compareExtraRows(tableStructure, dsSource, numSourceRows, dsDestination, numDestinationRows)
    
    if len(extraSourceRows) > 0 or len(extraDestinationRows) > 0:
        for el in extraSourceRows:
            row = el[0]
            columnNames = []
            columnValues = []
    
            log.tracef("Inserting extra row %d", row)
            for columnDict in columnsToUpdate:
                columnName = columnDict.get("columnName", None)
                dataType = columnDict.get("dataType", None)
                if columnName == None or dataType == None:
                    system.gui.errorBox("Invalid columnsToUpdate structure: %s" % (str(columnDict)))
                    return
                
                log.tracef("    Column: %s, Data Type: %s",  columnName, dataType)
                
                sourceValue = dsSource.getValueAt(row, columnName)
                
                if dataType == STRING:
                    columnNames.append(columnName)
                    if sourceValue == None:
                        columnValues.append("NULL")
                    else:
                        columnValues.append("'%s'" % (sourceValue))
                elif dataType in [FLOAT, INTEGER]:
                    columnNames.append(columnName)
                    columnValues.append("%s" % (str(sourceValue)))
                elif dataType == BOOLEAN:
                    columnNames.append(columnName)
                    if sourceValue == None:
                        columnValues.append("NULL")
                    elif sourceValue == True:
                        columnValues.append("1")
                    else:
                        columnValues.append("0")
                elif dataType == LOOKUP:
                    lookupId, idColumnName = getLookupId(columnName, sourceValue, dbDestination)
                    if lookupId == None:
                        system.gui.errorBox("Unable to find %s, a %s, in %s" % (sourceValue, columnName, dbDestination))
                        return
                    columnNames.append(idColumnName)
                    columnValues.append("%s" % (str(lookupId)))
                else:
                    system.gui.errorBox("Unsupported column datatype: %s" % (dataType))
                    return 
                    
            ''' Now put together an insert statement '''
            SQL = "INSERT into %s (%s) values (%s)" % (tableName, ",".join(columnNames), ",".join(columnValues))
            print SQL
            system.db.runUpdateQuery(SQL, database=dbDestination)
    
        system.gui.warningBox("Rows have been copied between databases - run compare and update again!")
        return
   
    ''' Now compare the values of each row '''
    for sourceRow in range(numSourceRows):
        destinationRow = sourceRow
        dataIsTheSame = True
        columnValues = []
        for columnDict in columnsToUpdate:
            columnName = columnDict.get("columnName", None)
            dataType = columnDict.get("dataType", None)
            if columnName == None or dataType == None:
                system.gui.errorBox("Invalid columnsToUpdate structure: %s" % (str(columnDict)))
                return
            
            log.tracef("Row: %d, Column: %s, Data Type: %s",  sourceRow, columnName, dataType)
            
            sourceValue = dsSource.getValueAt(sourceRow, columnName)
            destinationValue = dsDestination.getValueAt(destinationRow, columnName)
            
            log.tracef("   comparing %s to %s...", str(sourceValue), str(destinationValue))
            if sourceValue <> destinationValue:
                dataIsTheSame = False
                log.tracef("  *** Found a mismatch ***")
                if dataType == STRING:
                    if sourceValue == None:
                        columnValues.append("%s = NULL" % (columnName))
                    else:
                        columnValues.append("%s = '%s'" % (columnName, sourceValue))
                elif dataType in [FLOAT, INTEGER]:
                    columnValues.append("%s = %s" % (columnName, str(sourceValue)))
                elif dataType == BOOLEAN:
                    if sourceValue == None:
                        columnValues.append("%s = NULL" % (columnName))
                    elif sourceValue == True:
                        columnValues.append("%s = 1" % (columnName))
                    else:
                        columnValues.append("%s = 0" % (columnName))
                elif dataType == LOOKUP:
                    lookupId, idColumnName = getLookupId(columnName, sourceValue, dbDestination)
                    if lookupId == None:
                        system.gui.errorBox("Unable to find %s, a %s, in %s" % (sourceValue, columnName, dbDestination))
                        return
                    columnValues.append("%s = '%s'" % (idColumnName, lookupId))
                else:
                    system.gui.errorBox("Unsupported column datatype: %s" % (dataType))
                    return 
    
            if not(dataIsTheSame):
                primaryKeyValue = dsDestination.getValueAt(destinationRow, primaryKey)
                vals = ",".join(columnValues)
                SQL = "update %s set %s where %s = %d" % (tableName, vals, primaryKey, primaryKeyValue)
                print SQL
                system.db.runUpdateQuery(SQL, database=dbDestination)


def getLookupId(lookupName, lookupValue, db):
    ''' Lookup the value from the source database and get the id from the destination database for the the same value. ''' 
    log.tracef("Looking up %s, a %s, in %s", lookupValue, lookupName, db)
    for lookup in lookups:
        if lookupName == lookup.get("name", None):
            idColumnName = lookup.get('idColumnName', None)
            SQL = lookup.get('sql', None)
            SQL = "%s '%s' " % (SQL, lookupValue)
            lookupId = system.db.runScalarQuery(SQL, database=db)
            log.tracef("   --- found %d ---", lookupId)
            return lookupId, idColumnName
    
    log.errorf("Didn't find the lookup: %s!", lookupName)

    return None, None

def deleteExtraRowsCallback(event):
    log.tracef("In %s.deleteExtraRowsCallback()", __name__)
    
    #--------------------------------------------------------------------------
    def deleteRows(tableStructure, extraRows, ds, numRows, db):
        tableName = tableStructure.get("table", None)
        primaryKey = tableStructure.get("primaryKey", None)
        
        log.tracef("Removing extra rows: %s", str(extraRows))
        
        i = 0
        for el in extraRows:
            row = el[0]
            primaryKeyVal = ds.getValueAt(row, primaryKey)
            SQL = "delete from %s where %s = %d" % (tableName, primaryKey, primaryKeyVal)
            system.db.runUpdateQuery(SQL, database=db)
            i = i + 1
            
        log.tracef("Deleted %d rows", i)
    #-------------------------------------------------------------------------
        
    rootContainer = event.source.parent.parent
    dbProduction = rootContainer.productionDatabase
    dbIsolation = rootContainer.isolationDatabase
    tableList = rootContainer.getComponent("Table List")
    tableStructure = getSelectedTableStructure(tableList)
    
    if tableStructure == None:
        return
    
    dsProduction, numProductionRows = getTableData(rootContainer, PRODUCTION)
    dsIsolation, numIsolationRows = getTableData(rootContainer, ISOLATION)
    
    extraProductionRows, extraIsolationRows = compareExtraRows(tableStructure, dsProduction, numProductionRows, dsIsolation, numIsolationRows)
    
    if event.source.name == "Delete Extra Production Rows Button":
        deleteRows(tableStructure, extraProductionRows, dsProduction, numProductionRows, dbProduction)
    else:
        deleteRows(tableStructure, extraIsolationRows, dsIsolation, numIsolationRows, dbIsolation)
    
    updatePowerTables(rootContainer, tableList, dbProduction, dbIsolation)