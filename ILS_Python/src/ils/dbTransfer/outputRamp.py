'''
Created on Aug 25, 2020

@author: phass
'''

import system
from ils.dbTransfer.constants import RECIPE_DATA_ID 
from ils.dbTransfer.common import escapeSqlQuotes
import ils.dbTransfer.recipeData as recipeData
import ils.dbTransfer.output as output

class OutputRamp(output.Output):

    def __init__(self, tableStructure):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        output.Output.__init__(self, tableStructure)
        self.log.tracef("In %s.initialize()...", __name__)

        
    def insert(self, extraSourceRows, dsSource, db):
        self.log.tracef("In %s.insert()...", __name__)
        
        for row in extraSourceRows: 
            recipeDataId = self._insert(row, dsSource, db)

            rampTimeMinutes = dsSource.getValueAt(row, "RampTimeMinutes")
            updateFrequencySeconds = dsSource.getValueAt(row, "UpdateFrequencySeconds")
    
            SQL = "Insert into SfcRecipeDataOutputRamp (RecipeDataId, RampTimeMinutes, UpdateFrequencySeconds) "\
                "values (%d, %f, %f)" % (recipeDataId, rampTimeMinutes, updateFrequencySeconds)
            
            self.log.tracef("SQL: %s", SQL)
            system.db.runUpdateQuery(SQL, db)


    def update(self, numSourceRows, dsSource, dbSource, dsDestination, dbDestination):
        self.log.tracef("In %s.update()...", __name__)
        output.Output.update(self, numSourceRows, dsSource, dbSource, dsDestination, dbDestination)
        
        for row in range(numSourceRows):            
                
            columnValues = []
            for columnName in ["RampTimeMinutes", "UpdateFrequencySeconds"]:
                sourceValue = dsSource.getValueAt(row, columnName)
                destinationValue = dsDestination.getValueAt(row, columnName)
        
                if sourceValue <> destinationValue:
                        columnValues.append("%s = %s " % (columnName, str(sourceValue)))
            
                if len(columnValues) > 0:            
                    recipeDataId = dsDestination.getValueAt(row, RECIPE_DATA_ID)
                    vals = ",".join(columnValues)
                    SQL = "update SfcRecipeDataOutputRamp set %s where RecipeDataId = %d" % (vals, recipeDataId)
                    self.log.tracef("SQL: %s", SQL)
                    system.db.runUpdateQuery(SQL, database=dbDestination)
