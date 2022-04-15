'''
Created on Aug 21, 2020

@author: phass
'''

import system
from ils.dbTransfer.constants import RECIPE_DATA_ID 
from ils.common.util import clearDataset, escapeSqlQuotes

class RecipeData():
    log = None
    tableStructure = None
    columnsToUpdate = None
    tableName = None

    def __init__(self, tableStructure):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        from ils.log import getLogger
        self.log = getLogger(__name__)
        
        self.columnsToUpdate = tableStructure.get("columnsToCompareAndUpdate", None)
        if self.columnsToUpdate == None:
            system.gui.errorBox("Unknown columns to update!")
        
        self.tableName = tableStructure.get("table", None)
        
    def insert(self, row, dsSource, db):
        self.log.tracef("In %s.insert()...", __name__)
        
        chartPath = dsSource.getValueAt(row, "ChartPath")
        stepName = dsSource.getValueAt(row, "StepName")
        stepId = self.getStepId(chartPath, stepName, db)
        folderPath = dsSource.getValueAt(row, "FolderPath")
        folderId = self.lookupFolderforStep(stepId, folderPath, db)
        recipeDataType = dsSource.getValueAt(row, "RecipeDataType")
        recipeDataTypeId = self.getRecipeDataTypeId(recipeDataType, db)
        recipeDataKey = dsSource.getValueAt(row, "RecipeDataKey")
        description = dsSource.getValueAt(row, "Description")
        description = escapeSqlQuotes(description)
        label = dsSource.getValueAt(row, "Label")
        if label == None:
            label = ""
        else:
            label = escapeSqlQuotes(label)
        units = dsSource.getValueAt(row, "Units")
    
        if folderId < 0:
            SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units) "\
                "values (%s, '%s', %d, '%s', '%s', '%s')" % (stepId, recipeDataKey, recipeDataTypeId, description, label, units)
        else:
            SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description, Label, Units, RecipeDataFolderId) "\
                "values (%s, '%s', %d, '%s', '%s', '%s', %s)" % (stepId, recipeDataKey, recipeDataTypeId, description, label, units, folderId)
        self.log.tracef("SQL: %s", SQL)
        recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
        return recipeDataId
    
    
    def insertDataValue(self, recipeDataId, dsSource, valueType, row, attrPrefix, db):
        self.log.tracef("In %s.insertDataValue()...", __name__)

        if valueType == "Float":
            val = dsSource.getValueAt(row, attrPrefix +"FloatValue")
            if val == None:
                SQL = "Insert into SfcRecipeDataValue (RecipeDataId) values (%d)" % (recipeDataId)
            else:
                SQL = "Insert into SfcRecipeDataValue (RecipeDataId, FloatValue) values (%d, %f)" % (recipeDataId, val)
        elif valueType == "Integer":
            val = dsSource.getValueAt(row, attrPrefix +"IntegerValue")
            if val == None:
                SQL = "Insert into SfcRecipeDataValue (RecipeDataId) values (%d)" % (recipeDataId)
            else:
                SQL = "Insert into SfcRecipeDataValue (RecipeDataId, IntegerValue) values (%d, %d)" % (recipeDataId, val)
        elif valueType == "String":
            val = dsSource.getValueAt(row, attrPrefix +"StringValue")
            if val == None:
                SQL = "Insert into SfcRecipeDataValue (RecipeDataId) values (%d)" % (recipeDataId)
            else:
                val = escapeSqlQuotes(val)
                SQL = "Insert into SfcRecipeDataValue (RecipeDataId, StringValue) values (%d, '%s')" % (recipeDataId, val)
        elif valueType == "Boolean":
            val = dsSource.getValueAt(row, attrPrefix +"BooleanValue")
            SQL = "Insert into SfcRecipeDataValue (RecipeDataId, BooleanValue) values (%d, %d)" % (recipeDataId, val)
        
        self.log.tracef("SQL: %s", SQL)
        valueId = system.db.runUpdateQuery(SQL, getKey=True, database=db)
        return valueId
    

    def update(self, row, dsSource, dbSource, dsDestination, dbDestination):
        self.log.tracef("In %s.update()...", __name__)
        columnValues = []
        
        for columnName in ["Description", "Label", "Units"]:
            sourceValue = dsSource.getValueAt(row, columnName)
            destinationValue = dsDestination.getValueAt(row, columnName)
    
            if sourceValue <> destinationValue:        
                sourceValue = escapeSqlQuotes(sourceValue)
                columnValues.append("%s = '%s'" % (columnName, sourceValue))
            
        if len(columnValues) > 0:
            self.log.infof("Updating row %d (%s)", row, str(columnValues))
            recipeDataId = dsDestination.getValueAt(row, RECIPE_DATA_ID)
            vals = ",".join(columnValues)
            SQL = "update SfcRecipeData set %s where RecipeDataId = %d" % (vals, recipeDataId)
            self.log.tracef("SQL: %s", SQL)
            system.db.runUpdateQuery(SQL, database=dbDestination)
    
    
    def updateValue(self, row, dsSource, dbSource, dsDestination, dbDestination, attrPrefix=""):
        self.log.tracef("In %s.updateValue()...", __name__)
        columnValues = []
        
        for columnName in ["FloatValue", "IntegerValue", "StringValue", "BooleanValue"]:
            self.log.tracef("Column: %s", columnName)
            sourceValue = dsSource.getValueAt(row, attrPrefix + columnName)
            destinationValue = dsDestination.getValueAt(row, attrPrefix + columnName)
            self.log.tracef("    Source: %s", str(sourceValue))
            self.log.tracef("    Destin: %s", str(destinationValue))
    
            if sourceValue <> destinationValue:
                self.log.infof("  a difference was found in row %d, column: %s - %s <> %s", row, columnName, str(sourceValue), str(destinationValue))
                if sourceValue == None:
                    columnValues.append("%s = NULL" % (columnName))
                else:
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
            valueId = dsDestination.getValueAt(row, attrPrefix +"ValueId")
            vals = ",".join(columnValues)
            SQL = "update SfcRecipeDataValue set %s where ValueId = %d" % (vals, valueId)
            self.log.tracef("SQL: %s", SQL)
            rows = system.db.runUpdateQuery(SQL, database=dbDestination)
            self.log.tracef("...updated %d rows!", rows)
        
    def delete(self):
        self.log.tracef("In %s.delete()...", __name__)
        
    def deleteSfcRecipeData(self, recipeDataId, db):
        SQL = "delete from SfcRecipeData where RecipeDataId = %d" % recipeDataId
        self.log.tracef("SQL: %s", SQL)
        rows = system.db.runUpdateQuery(SQL, db)
        self.log.tracef("...deleted %d rows!", rows)
    
    '''
    ----- Helper Methods -----
    '''
    
    def getRecipeDataTypeId(self, recipeDataType, db):
        SQL = "select recipeDataTypeId from SfcRecipeDataType where RecipeDataType = '%s' " % (recipeDataType)
        recipeDataTypeId = system.db.runScalarQuery(SQL, db)
        return recipeDataTypeId
    
    def getStepId(self, chartPath, stepName, db):
        SQL = "select stepId from SfcStepView where ChartPath = '%s' and StepName = '%s'" % (chartPath, stepName)
        stepId = system.db.runScalarQuery(SQL, db)
        return stepId

    def getValueTypeId(self, valueType, db):
        SQL = "select valueTypeId from SfcValueType where ValueType = '%s' " % (valueType)
        valueTypeId = system.db.runScalarQuery(SQL, db)
        return valueTypeId
    
    def lookupFolderforStep(self, stepId, folderPath, db):
        self.log.tracef("   ...step: %d, older Path: <%s>", stepId, str(folderPath))
        folderId = None
        
        ''' Now look up that path in the destination system '''
        folders = folderPath.split("/")
        print "Folders: ", folders
        if len(folders) > 0:
            folderId = self.getLeafFolderIdForPath(folders, db, stepId)
            self.log.tracef("   ... found id %s for %s", str(folderId), folderPath)
            
        return folderId
    
    def getLeafFolderIdForPath(self, folders, db, stepId=None):
        self.log.tracef("Looking for the leaf node for: %s", str(folders) )
        
        if stepId == None:
            SQL = "select RecipeDataFolderId, RecipeDataKey, ParentRecipeDataFolderId, ParentFolderName "\
                    "from SfcRecipeDataFolderView  "\
                    "order by RecipeDataFolderId "
        else:
            SQL = "select RecipeDataFolderId, RecipeDataKey, ParentRecipeDataFolderId, ParentFolderName "\
                    "from SfcRecipeDataFolderView  "\
                    "where stepId = %d"\
                    "order by RecipeDataFolderId " % (stepId)
    
        folderPDS = system.db.runQuery(SQL, db)
        self.log.tracef("...fetched %d folders", len(folderPDS))
        
        # The initial parent is the root node, or None
        parent=None
        
        for folder in folders:
            newParent=None
            self.log.tracef("   ... looking for %s with parent id %s...", folder, str(parent))
            for record in folderPDS:
                if record["RecipeDataKey"] == folder and record["ParentRecipeDataFolderId"] == parent:
                    newParent = record["RecipeDataFolderId"]
                    break
                
            if newParent == None:
                self.log.tracef("--- Unable to find the parent folder: %s in %s", folder, str(folders))
                return None
            else:
                parent = newParent
        
        self.log.tracef("Returning leaf id: %s", str(parent))
        return parent