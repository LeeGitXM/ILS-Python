'''
Created on Sep 7, 2020

@author: phass
'''

import system
from ils.dbTransfer.constants import RECIPE_DATA_ID 
from ils.dbTransfer.common import getIndexKeyId
import ils.dbTransfer.recipeData as recipeData
from ils.dbTransfer.common import escapeSqlQuotes

class SfcSQC(recipeData.RecipeData):

    def __init__(self, tableStructure):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        recipeData.RecipeData.__init__(self, tableStructure)
        self.log.tracef("In %s.initialize()...", __name__)

        
    def insert(self, extraSourceRows, dsSource, db):
        self.log.tracef("In %s.insert()...", __name__)
        for row in extraSourceRows:
            ''' Insert the base record into SfcRecipeData using the inherited insert() method'''
            recipeDataId = recipeData.RecipeData.insert(self, row, dsSource, db)
            
            lowLimit = dsSource.getValueAt(row, "LowLimit")
            targetValue = dsSource.getValueAt(row, "TargetValue")
            highLimit = dsSource.getValueAt(row, "HighLimit")
    
            SQL = "Insert into SfcRecipeDataSQC (RecipeDataId, LowLimit, TargetValue, HighLimit) "\
                " values (%d, %f, %f, %f)" % \
                (recipeDataId, lowLimit, targetValue, highLimit)
                
            self.log.tracef("SQL: %s", SQL)
            system.db.runUpdateQuery(SQL, db)


    def update(self, numSourceRows, dsSource, dbSource, dsDestination, dbDestination):
        for row in range(numSourceRows):            
            recipeData.RecipeData.update(self, row, dsSource, dbSource, dsDestination, dbDestination)
            
            columnValues = []
            for columnName in ["LowLimit", "TargetValue", "HighLimit"]:
                sourceValue = dsSource.getValueAt(row, columnName)
                destinationValue = dsDestination.getValueAt(row, columnName)
        
                if sourceValue <> destinationValue:
                    columnValues.append("%s = %s " % (columnName, str(sourceValue)))                   
            
            if len(columnValues) > 0:            
                recipeDataId = dsDestination.getValueAt(row, RECIPE_DATA_ID)
                vals = ",".join(columnValues)
                SQL = "update SfcRecipeDataSQC set %s where RecipeDataId = %d" % (vals, recipeDataId)
                self.log.tracef("SQL: %s", SQL)
                system.db.runUpdateQuery(SQL, database=dbDestination)


    def delete(self, ds, selectedRow, db):
        self.log.infof("In %s.delete(), deleting row %d...", __name__, selectedRow)
        recipeDataId = ds.getValueAt(selectedRow, "RecipeDataId")
        self.deleteSfcRecipeData(recipeDataId, db)