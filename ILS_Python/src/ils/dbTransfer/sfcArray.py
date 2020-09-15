'''
Created on Aug 25, 2020

@author: phass
'''

import system
from ils.dbTransfer.constants import RECIPE_DATA_ID 
from ils.dbTransfer.common import getIndexKeyId
import ils.dbTransfer.recipeData as recipeData

class SfcArray(recipeData.RecipeData):

    def __init__(self, tableStructure):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        recipeData.RecipeData.__init__(self, tableStructure)
        self.log.tracef("In %s.initialize()...", __name__)

        
    def insert(self, extraSourceRows, dsSource, db):
        self.log.tracef("In %s.insert()...", __name__)
        for row in extraSourceRows:
            ''' Insert the base record into SfcRecipeData using the inherited insert() method'''
            recipeDataId = recipeData.RecipeData.insert(self, row, dsSource, db)
    
            valueType = dsSource.getValueAt(row, "ValueType")
            valueTypeId = self.getValueTypeId(valueType, db)
            
            keyName = dsSource.getValueAt(row, "KeyName")
            if keyName == None:
                SQL = "Insert into SfcRecipeDataArray (RecipeDataId, ValueTypeId) values (%d, %d)" % (recipeDataId, valueTypeId)
            else:
                indexKeyId = getIndexKeyId(keyName, db)
                SQL = "Insert into SfcRecipeDataArray (RecipeDataId, ValueTypeId, IndexKeyId) values (%d, %d, %d)" % (recipeDataId, valueTypeId, indexKeyId)
                
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
            for columnName in ["KeyName"]:
                sourceValue = dsSource.getValueAt(row, columnName)
                destinationValue = dsDestination.getValueAt(row, columnName)
        
                if sourceValue <> destinationValue:
                    indexKeyId = self.getIndexKeyId(sourceValue, dbDestination)
                    columnValues.append("IndexKeyId = %d" % (indexKeyId))
            
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
