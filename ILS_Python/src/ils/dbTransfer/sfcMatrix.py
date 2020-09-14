'''
Created on Aug 26, 2020

@author: phass
'''

import system
from ils.dbTransfer.constants import RECIPE_DATA_ID 
from ils.dbTransfer.common import getIndexKeyId
import ils.dbTransfer.recipeData as recipeData

class SfcMatrix(recipeData.RecipeData):

    def __init__(self, tableStructure):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        recipeData.RecipeData.__init__(self, tableStructure)
        self.log.tracef("In %s.initialize()...", __name__)

        
    def insert(self, extraSourceRows, dsSource, db):
        self.log.tracef("In %s.insert()...", __name__)
        for row in extraSourceRows:
            ''' Insert the base record into SfcRecipeData using the inherited insert() method'''
            recipeDataId = recipeData.RecipeData.insert(self, row, dsSource, db)
            
            rows = dsSource.getValueAt(row, "Rows")
            columns = dsSource.getValueAt(row, "Columns")
    
            valueType = dsSource.getValueAt(row, "ValueType")
            valueTypeId = self.getValueTypeId(valueType, db)
            
            keyColumns = ""
            keyValues = ""
            for columnName in ["RowIndexKey", "ColumnIndexKey"]:
                
                keyName = dsSource.getValueAt(row, columnName)
                if keyName <> None:
                    keyColumns = keyColumns + ", " + columnName + "Id"
                    indexKeyId = getIndexKeyId(keyName, db)
                    keyValues = keyValues + ", " + str(indexKeyId)
    
            SQL = "Insert into SfcRecipeDataMatrix (RecipeDataId, ValueTypeId, Rows, Columns %s) values (%d, %d, %d, %d %s)" % (keyColumns, recipeDataId, valueTypeId, rows, columns, keyValues)
                
            self.log.tracef("SQL: %s", SQL)
            system.db.runUpdateQuery(SQL, db)


    def update(self, numSourceRows, dsSource, dbSource, dsDestination, dbDestination):
        for row in range(numSourceRows):            
            recipeData.RecipeData.update(self, row, dsSource, dbSource, dsDestination, dbDestination)

            ''' check / update is the value type. '''
            sourceValueType = dsSource.getValueAt(row, "ValueType")
            destinationValueType = dsDestination.getValueAt(row, "ValueType")
    
            if sourceValueType <> destinationValueType:
                valueTypeId = self.getValueTypeId(sourceValueType, dbDestination)
                recipeDataId = dsDestination.getValueAt(row, "RecipeDataId")
                SQL = "Update SfcRecipeDataSimpleValue set ValueTypeId = %d where RecipeDataId = %d" % (valueTypeId, recipeDataId)
                self.log.tracef("SQL: %s", SQL)
                system.db.runUpdateQuery(SQL, dbDestination)
            
            columnValues = []
            for columnName in ["RowIndexKey", "ColumnIndexKey"]:
                sourceValue = dsSource.getValueAt(row, columnName)
                destinationValue = dsDestination.getValueAt(row, columnName)
        
                if sourceValue <> destinationValue:
                    indexKeyId = self.getIndexKeyId(sourceValue, dbDestination)
                    columnValues.append("%sId = %d" % (columnName, indexKeyId))
            
                if len(columnValues) > 0:            
                    recipeDataId = dsDestination.getValueAt(row, RECIPE_DATA_ID)
                    vals = ",".join(columnValues)
                    SQL = "update SfcRecipeDataOutput set %s where RecipeDataId = %d" % (vals, recipeDataId)
                    self.log.tracef("SQL: %s", SQL)
                    system.db.runUpdateQuery(SQL, database=dbDestination)


    def delete(self, ds, selectedRow, db):
        self.log.infof("In %s.delete(), deleting row %d...", __name__, selectedRow)
        recipeDataId = ds.getValueAt(selectedRow, "RecipeDataId")
        self.deleteSfcRecipeData(recipeDataId, db)
