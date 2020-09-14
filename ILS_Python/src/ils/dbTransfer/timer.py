'''
Created on Aug 21, 2020

@author: phass
'''

import system
from ils.dbTransfer.common import escapeSqlQuotes
import ils.dbTransfer.recipeData as recipeData

class Timer(recipeData.RecipeData):

    def __init__(self, tableStructure):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        recipeData.RecipeData.__init__(self, tableStructure)


    def insert(self, extraSourceRows, dsSource, db):
        self.log.tracef("In %s.insert()...", __name__)
        for row in extraSourceRows:
            ''' Insert the base record into SfcRecipeData '''
            recipeDataId = recipeData.RecipeData.insert(self, row, dsSource, db)
    
            ''' Now insert the record into SfcRecipeDataTimer '''        
            SQL = "Insert into SfcRecipeDataTimer (RecipeDataId) values (%d)" % (recipeDataId)
            self.log.tracef("SQL: %s", SQL)
            system.db.runUpdateQuery(SQL, database=db)
    
    
    def update(self, numSourceRows, dsSource, dbSource, dsDestination, dbDestination):
        for row in range(numSourceRows):            
            recipeData.RecipeData.update(self, row, dsSource, dbSource, dsDestination, dbDestination)
            
        
    def delete(self, ds, selectedRow, db):
        self.log.infof("In %s.delete(), deleting row %d...", __name__, selectedRow)
        recipeDataId = ds.getValueAt(selectedRow, "RecipeDataId")
        self.deleteSfcRecipeData(recipeDataId, db)