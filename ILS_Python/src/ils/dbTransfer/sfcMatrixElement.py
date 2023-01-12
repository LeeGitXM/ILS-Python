'''
Created on Aug 26, 2020

@author: phass
'''


import system
from ils.dbTransfer.constants import VALUE_ID 
from ils.dbTransfer.common import getIndexKeyId, getRecipeDataId
from ils.common.cast import toBool
from ils.common.util import escapeSqlQuotes

import ils.dbTransfer.recipeData as recipeData

class SfcMatrixElement(recipeData.RecipeData):

    def __init__(self, tableStructure):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        recipeData.RecipeData.__init__(self, tableStructure)
        self.log.tracef("In %s.initialize()...", __name__)

        
    def insert(self, extraSourceRows, dsSource, db):
        self.log.tracef("In %s.insert()...", __name__)
        for row in extraSourceRows:
            chartPath = dsSource.getValueAt(row, "ChartPath")
            stepName = dsSource.getValueAt(row, "StepName")
            recipeDataKey = dsSource.getValueAt(row, "RecipeDataKey")
            rowIndex = dsSource.getValueAt(row, "RowIndex")
            columnIndex = dsSource.getValueAt(row, "ColumnIndex")
            folderPath = dsSource.getValueAt(row, "FolderPath")
            folderKey = dsSource.getValueAt(row, "FolderKey")
        
            recipeDataId = getRecipeDataId(chartPath, stepName, recipeDataKey, folderKey, db)
            
            columns = ""
            values = ""
            val = dsSource.getValueAt(row, "FloatValue")
            if val <> None:
                columns = columns + ", FloatValue" 
                values = values + ", %f " % (val)
                
            val = dsSource.getValueAt(row, "IntegerValue")
            if val <> None:
                columns = columns + ", IntegerValue" 
                values = values + ", %d " % (val)

            val = dsSource.getValueAt(row, "StringValue")
            if val <> None:
                columns = columns + ", StringValue" 
                values = values + ", '%s' " % (val)
                
            val = dsSource.getValueAt(row, "BooleanValue")
            if val <> None:
                columns = columns + ", BooleanValue" 
                values = values + ", %d " % (toBool(val))
            
            SQL = "Insert into SfcRecipeDataValue (RecipeDataId %s) values (%d %s)" % (columns, recipeDataId, values)
            self.log.tracef("SQL: %s", SQL)
            valueId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
        
            SQL = "Insert into SfcRecipeDataMatrixElement (RecipeDataId, RowIndex, ColumnIndex, ValueId) values (%d, %d, %d, %d)" % (recipeDataId, rowIndex, columnIndex, valueId)
            self.log.tracef("SQL: %s", SQL)
            system.db.runUpdateQuery(SQL, database=db)


    def update(self, numSourceRows, dsSource, dbSource, dsDestination, dbDestination):
        self.log.tracef("Entering %s.update()", __name__)
        for row in range(numSourceRows):
            self.log.tracef("...checking row %d", row)
            columnValues = []
            for columnName in ["FloatValue", "IntegerValue", "StringValue", "BooleanValue"]:
                sourceValue = dsSource.getValueAt(row, columnName)
                destinationValue = dsDestination.getValueAt(row, columnName)
        
                if sourceValue <> destinationValue:
                    if columnName == "FloatValue":
                        columnValues.append("%s = %f" % (columnName, sourceValue))
                    elif columnName == "IntegerValue":
                        columnValues.append("%s = %d" % (columnName, sourceValue))
                    elif columnName == "StringValue":
                        sourceValue = escapeSqlQuotes(sourceValue)
                        columnValues.append("%s = '%s'" % (columnName, sourceValue))
                    elif columnName == "BooleanValue":
                        columnValues.append("%s = %d" % (columnName, sourceValue))
                    else:
                        system.gui.errorBox("Unexpected column name: %s" % (columnName))
                        return
            
            if len(columnValues) > 0:            
                valueId = dsDestination.getValueAt(row, VALUE_ID)
                vals = ",".join(columnValues)
                SQL = "update SfcRecipeDataValue set %s where ValueId = %d" % (vals, valueId)
                self.log.tracef("SQL: %s", SQL)
                system.db.runUpdateQuery(SQL, database=dbDestination)
                columnValues = []


    def delete(self, ds, selectedRow, db):
        self.log.infof("In %s.delete(), deleting row %d...", __name__, selectedRow)
        
        recipeDataId = ds.getValueAt(selectedRow, "RecipeDataId")
        rowIndex = ds.getValueAt(selectedRow, "RowIndex")
        columnIndex = ds.getValueAt(selectedRow, "ColumnIndex")
        
        SQL = "delete from SfcRecipeDataMatrixElement where RecipeDataId = %d and RowIndex = %d and ColumnIndex = %d" % (recipeDataId, rowIndex, columnIndex)
        self.log.tracef("SQL: %s", SQL)
        rows = system.db.runUpdateQuery(SQL, db)
        self.log.tracef("...deleted %d rows!", rows)