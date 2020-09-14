'''
Created on Aug 24, 2020

@author: phass
'''

import system
from ils.dbTransfer.common import escapeSqlQuotes
import ils.dbTransfer.recipeData as recipeData

class Input(recipeData.RecipeData):

    def __init__(self, tableStructure):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        recipeData.RecipeData.__init__(self, tableStructure)
        self.log.tracef("In %s.initialize()...", __name__)

        
    def insert(self, extraSourceRows, dsSource, db):
        self.log.tracef("In %s.insert()...", __name__)
        for row in extraSourceRows: 
            ''' Insert the base record into SfcRecipeData using the inherited insert() method'''
            recipeDataId = recipeData.RecipeData.insert(self, row, dsSource, db)
            
            ''' Now insert a record into the SfcRecipeDataValue table '''
            tag = dsSource.getValueAt(row, "Tag")
            valueType = dsSource.getValueAt(row, "ValueType")
            valueTypeId = self.getValueTypeId(valueType, db)
            pvValueId = self.insertDataValue(recipeDataId, dsSource, valueType, row, attrPrefix="PV", db=db)
            targetValueId = self.insertDataValue(recipeDataId, dsSource, valueType, row, attrPrefix="Target", db=db)
    
            ''' Now insert the record into SfcRecipeDataSimpleValue which holds it all together '''
            SQL = "Insert into SfcRecipeDataInput (RecipeDataId, ValueTypeId, Tag, PVValueId, TargetValueId) values (%d, %d, '%s', %d, %d)" % (recipeDataId, valueTypeId, tag, pvValueId, targetValueId)
            self.log.tracef("SQL: %s", SQL)
            system.db.runUpdateQuery(SQL, db)


    def update(self, numSourceRows, dsSource, dbSource, dsDestination, dbDestination):
        for row in range(numSourceRows):            
            recipeData.RecipeData.update(self, row, dsSource, dbSource, dsDestination, dbDestination)
            recipeData.RecipeData.updateValue(self, row, dsSource, dbSource, dsDestination, dbDestination, "PV")
            recipeData.RecipeData.updateValue(self, row, dsSource, dbSource, dsDestination, dbDestination, "Target")

            ''' There are two attributes in the SfcRecipeDataInput table that needs to be checked / updated. '''
            sourceValueType = dsSource.getValueAt(row, "ValueType")
            destinationValueType = dsDestination.getValueAt(row, "ValueType")
            
            recipeDataId = dsDestination.getValueAt(row, "RecipeDataId")
    
            if sourceValueType <> destinationValueType:
                valueTypeId = self.getValueTypeId(sourceValueType, dbDestination)
                SQL = "Update SfcRecipeDataInput set ValueTypeId = %d where RecipeDataId = %d" % (valueTypeId, recipeDataId)
                self.log.tracef("SQL: %s", SQL)
                system.db.runUpdateQuery(SQL, dbDestination)
                
            sourceTag = dsSource.getValueAt(row, "Tag")
            destinationTag = dsDestination.getValueAt(row, "Tag")
    
            if sourceTag <> destinationTag:
                SQL = "Update SfcRecipeDataInput set Tag = '%s' where RecipeDataId = %d" % (sourceTag, recipeDataId)
                self.log.tracef("SQL: %s", SQL)
                system.db.runUpdateQuery(SQL, dbDestination)


    def delete(self, ds, selectedRow, db):
        self.log.infof("In %s.delete(), deleting row %d...", __name__, selectedRow)
        recipeDataId = ds.getValueAt(selectedRow, "RecipeDataId")
        self.deleteSfcRecipeData(recipeDataId, db)
