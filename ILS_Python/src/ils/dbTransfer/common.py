'''
Created on Aug 21, 2020

@author: phass
'''

import system
from ils.sfc.recipeData.core import getFolderPath
from ils.dbTransfer.constants import config, lookups, PRODUCTION, STRING, INTEGER
from ils.common.util import clearDataset, escapeSqlQuotes

from ils.log import getLogger
log = getLogger(__name__)

def createClass(tableStructure):
    ''' 
    Create a class so that we can methodize the nethods.
    The config structure that drives the whole dbTransfer, if it doesn't contain a class name then use the default.

    This will have an error but it is safe to ignore it.  We need to import each class file! 
    '''
    import ils.dbTransfer
    from ils.dbTransfer.basicTable import BasicTable
    from ils.dbTransfer.input import Input
    from ils.dbTransfer.output import Output
    from ils.dbTransfer.outputRamp import OutputRamp
    from ils.dbTransfer.sfcArray import SfcArray
    from ils.dbTransfer.sfcArrayElement import SfcArrayElement
    from ils.dbTransfer.sfcMatrix import SfcMatrix
    from ils.dbTransfer.sfcMatrixElement import SfcMatrixElement
    from ils.dbTransfer.sfcRecipe import SfcRecipe
    from ils.dbTransfer.sfcSQC import SfcSQC
    from ils.dbTransfer.simpleValue import SimpleValue
    from ils.dbTransfer.timer import Timer

    tableName = tableStructure.get("table", None)
    
    log.tracef("In %s.createClass(), creating an object for a ", __name__, tableName)
    
    if tableName == "SfcRecipeDataSimpleValue":
        dbTable = ils.dbTransfer.simpleValue.SimpleValue(tableStructure)
    elif tableName == "SfcRecipeDataTimer":
        dbTable = ils.dbTransfer.timer.Timer(tableStructure)
    elif tableName == "SfcRecipeDataRecipe":
        dbTable = ils.dbTransfer.sfcRecipe.SfcRecipe(tableStructure)
    elif tableName == "SfcRecipeDataSQC":
        dbTable = ils.dbTransfer.sfcSQC.SfcSQC(tableStructure)
    elif tableName == "SfcRecipeDataInput":
        dbTable = ils.dbTransfer.input.Input(tableStructure)
    elif tableName == "SfcRecipeDataOutput":
        dbTable = ils.dbTransfer.output.Output(tableStructure)
    elif tableName == "SfcRecipeDataOutputRamp":
        dbTable = ils.dbTransfer.outputRamp.OutputRamp(tableStructure)
    elif tableName == "SfcRecipeDataArray":
        dbTable = ils.dbTransfer.sfcArray.SfcArray(tableStructure)
    elif tableName == "SfcRecipeDataArrayElement":
        dbTable = ils.dbTransfer.sfcArrayElement.SfcArrayElement(tableStructure)
    elif tableName == "SfcRecipeDataMatrix":
        dbTable = ils.dbTransfer.sfcMatrix.SfcMatrix(tableStructure)
    elif tableName == "SfcRecipeDataMatrixElement":
        dbTable = ils.dbTransfer.sfcMatrixElement.SfcMatrixElement(tableStructure)
        
    else:
        dbTable = ils.dbTransfer.basicTable.BasicTable(tableStructure)
    
    return dbTable


def createClassX(tableStructure):
    ''' 
    Create a class so that we can methodize the nethods.
    The config structure that drives the whole dbTransfer, if it doesn't contain a class name then use the default.

    This will have an error but it is safe to ignore it.  We need to import each class file! 
    
    This didn't work, but it has the attractive dynamic create method rather than a case statement and hardcoded commands 
    '''
    
    def creater(tableStructure):
        import ils.dbTransfer
        from ils.dbTransfer.basicTable import BasicTable
        from ils.dbTransfer.simpleValue import SimpleValue
    
        className = tableStructure.get("className", "basicTable.BasicTable")
        log.tracef("In %s.createClass(), creating a %s", __name__, className)
        
        cmd = "ils.dbTransfer." + className
        log.trace("Creating an object using: <%s>" % (cmd))
        dbTable = eval(cmd)
        print "...created..."
        return dbTable
    
    print "creating..."
    dbTable = creater(tableStructure)
    print "...calling a method..."
    #dbTable.foo(tableStructure)
    print "...done..."
    return dbTable

def updateFolderPath(ds, db):
    '''
    This is used to update the folderPath field of every row in the table.  It looks up the recipe data folder id,
    which specifies the folder in a folder tree.  It does a single query of the recipe data folder tree and then uses it 
    to determine the full folder path for each recipe data entity.
    '''
    log.tracef("In updateFolderPath for %s", db)
    headersRaw = system.dataset.getColumnHeaders(ds)
    
    ''' Convert from unicode to string '''
    headers = []
    for header in headersRaw:
        headers.append(str(header))
    
    if "RecipeDataFolderId" in headers and "FolderPath" in headers: 
        SQL = "select RecipeDataFolderId, RecipeDataKey, ParentRecipeDataFolderId, ParentFolderName "\
                "from SfcRecipeDataFolderView  "\
                "order by RecipeDataFolderId "
                
        folderPDS = system.db.runQuery(SQL, db)
        
        for row in range(ds.getRowCount()):
            recipeDataFolderId = ds.getValueAt(row, "RecipeDataFolderId")
            if recipeDataFolderId <> None:
                folderPath = getFolderPath(recipeDataFolderId, folderPDS)
                ds = system.dataset.setValue(ds, row, "FolderPath", folderPath)
    else:
        log.tracef("The dataset columns do not contain RecipeDataFolerId or FolderPath!")
        
    return ds


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


def getLookupId(lookupName, lookupValue, db):
    ''' Lookup the value from the source database and get the id from the destination database for the the same value. ''' 
    
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


def getLookupIdWithTwoKeys(lookupName, dsSource, row, db):
    ''' Lookup the value from the source database and get the id from the destination database for the the same value. ''' 
    log.tracef("Looking up a two key lookup %s, in %s", lookupName, db)
    for lookup in lookups:
        if lookupName == lookup.get("name", None):
            idColumnName = lookup.get('idColumnName', None)
            SQL1 = lookup.get('sql1', None)
            key1 = lookup.get('key1', None)
            key1Type = lookup.get('key1Type', STRING)
            key1Value = dsSource.getValueAt(row, key1)
            
            SQL2 = lookup.get('sql2', None)
            key2 = lookup.get('key2', None)
            key2Type = lookup.get('key2Type', STRING)
            key2Value = dsSource.getValueAt(row, key2)
            
            log.tracef("%s  -  %s: %s, %s  -  %s: %s", SQL1, key1, key1Value, SQL2, key2, key2Value)
            
            if key1Type == INTEGER:
                SQL = "%s %d " % (SQL1, key1Value)
            elif key1Type == STRING:
                SQL = "%s '%s' " % (SQL1, key1Value)
            else:
                system.gui.errorBox("Unknown type for key1 (%s): %s", key1, key1Type)
                return None, None
            
            if key2Type == INTEGER:
                SQL = "%s, %s %d " % (SQL, SQL2, key2Value)
            elif key2Type == STRING:
                SQL = "%s %s '%s' " % (SQL, SQL2, key2Value)
            else:
                system.gui.errorBox("Unknown type for key2 (%s): %s", key2, key2Type)
                return None, None
            
            print SQL
            lookupId = system.db.runScalarQuery(SQL, database=db)
            log.tracef("   --- found %d ---", lookupId)
            return lookupId, idColumnName

    return None, None

def getIndexKeyId(keyName, db):
    SQL = "select KeyId from SfcRecipeDataKeyMaster where KeyName = '%s' " % (keyName)
    keyId = system.db.runScalarQuery(SQL, db)
    return keyId

def dsToList(ds):
    ''' Convert a one dimensional dataset to a list of values. '''
    vals = []
    for row in range(ds.getRowCount()):
        vals.append(ds.getValueAt(row,0))
    return vals

def getRecipeDataId(chartPath, stepName, recipeDataKey, folderKey, db):
    ''' This is mostly used by the array and matrix element routines. '''
    if folderKey == None:
        SQL = "select RecipeDataId from SfcRecipeDataView where ChartPath = '%s' and StepName = '%s' and RecipeDataKey = '%s' " % (chartPath, stepName, recipeDataKey)
    else:
        SQL = "select RecipeDataId from SfcRecipeDataView where ChartPath = '%s' and StepName = '%s' and RecipeDataKey = '%s' and folderName = '%s' " % (chartPath, stepName, recipeDataKey, folderKey)

    recipeDataId = system.db.runScalarQuery(SQL, db)
    return recipeDataId