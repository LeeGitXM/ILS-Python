'''
Created on Aug 24, 2020

@author: phass
'''

import system
from ils.dbTransfer.constants import RECIPE_DATA_ID 
from ils.dbTransfer.common import escapeSqlQuotes
import ils.dbTransfer.recipeData as recipeData
from ils.sfc.common.util import boolToBit

class Output(recipeData.RecipeData):

    def __init__(self, tableStructure):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        recipeData.RecipeData.__init__(self, tableStructure)
        self.log.tracef("In %s.initialize()...", __name__)

        
    def insert(self, extraSourceRows, dsSource, db):
        self.log.tracef("In %s.insert()...", __name__)
        for row in extraSourceRows: 
            recipeDataId = self._insert(row, dsSource, db)
            
            
    def _insert(self, row, dsSource, db):
        ''' Insert the base record into SfcRecipeData using the inherited insert() method'''
        recipeDataId = recipeData.RecipeData.insert(self, row, dsSource, db)
        
        ''' Now insert a record into the SfcRecipeDataValue table '''
        tag = dsSource.getValueAt(row, "Tag")
        download = dsSource.getValueAt(row, "Download")
        timing = dsSource.getValueAt(row, "Timing")
        maxTiming = dsSource.getValueAt(row, "MaxTiming")
        writeConfirm = dsSource.getValueAt(row, "WriteConfirm")
        
        valueType = dsSource.getValueAt(row, "ValueType")
        valueTypeId = self.getValueTypeId(valueType, db)
        
        outputType = dsSource.getValueAt(row, "OutputType")
        outputTypeId = self.getOutputTypeId(outputType, db)
        
        outputValueId = self.insertDataValue(recipeDataId, dsSource, valueType, row, attrPrefix="Output", db=db)
        pvValueId = self.insertDataValue(recipeDataId, dsSource, valueType, row, attrPrefix="PV", db=db)
        targetValueId = self.insertDataValue(recipeDataId, dsSource, valueType, row, attrPrefix="Target", db=db)

        ''' Now insert the record into SfcRecipeDataSimpleValue which holds it all together '''
        SQL = "Insert into SfcRecipeDataOutput (RecipeDataId, ValueTypeId, OutputTypeId, Tag, OutputValueId, PVValueId, TargetValueId, Download, timing, maxTiming, writeConfirm) "\
            "values (%d, %d, %d, '%s', %d, %d, %d, %d, %f, %f, %d)" % \
            (recipeDataId, valueTypeId, outputTypeId, tag, outputValueId, pvValueId, targetValueId, download, timing, maxTiming, writeConfirm)
        
        self.log.tracef("SQL: %s", SQL)
        system.db.runUpdateQuery(SQL, db)
        
        return recipeDataId


    def update(self, numSourceRows, dsSource, dbSource, dsDestination, dbDestination):
        for row in range(numSourceRows):            
            recipeData.RecipeData.update(self, row, dsSource, dbSource, dsDestination, dbDestination)
            recipeData.RecipeData.updateValue(self, row, dsSource, dbSource, dsDestination, dbDestination, "Output")
            recipeData.RecipeData.updateValue(self, row, dsSource, dbSource, dsDestination, dbDestination, "PV")
            recipeData.RecipeData.updateValue(self, row, dsSource, dbSource, dsDestination, dbDestination, "Target")

            sourceValueType = dsSource.getValueAt(row, "ValueType")
            destinationValueType = dsDestination.getValueAt(row, "ValueType")
            
            recipeDataId = dsDestination.getValueAt(row, "RecipeDataId")
    
            if sourceValueType <> destinationValueType:
                valueTypeId = self.getValueTypeId(sourceValueType, dbDestination)
                SQL = "Update SfcRecipeDataInput set ValueTypeId = %d where RecipeDataId = %d" % (valueTypeId, recipeDataId)
                self.log.tracef("SQL: %s", SQL)
                system.db.runUpdateQuery(SQL, dbDestination)
                
            columnValues = []
            for columnName in ["Tag", "Download", "Timing", "MaxTiming", "WriteConfirm"]:
                sourceValue = dsSource.getValueAt(row, columnName)
                destinationValue = dsDestination.getValueAt(row, columnName)
        
                if sourceValue <> destinationValue:
                    if columnName in  ["Tag"]:
                        sourceValue = escapeSqlQuotes(sourceValue)
                        columnValues.append("%s = '%s'" % (columnName, sourceValue))
                    elif columnName in ["Download", "WriteConfirm"]:
                        bitVal = boolToBit(sourceValue)
                        columnValues.append("%s = %d" % (columnName, bitVal))
                    else:
                        columnValues.append("%s = %s " % (columnName, sourceValue))
            
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


    def getOutputTypeId(self, outputType, db):
        SQL = "select outputTypeId from SfcRecipeDataOutputType where OutputType = '%s' " % (outputType)
        outputTypeId = system.db.runScalarQuery(SQL, db)
        return outputTypeId