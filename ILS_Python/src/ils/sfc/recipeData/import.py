'''
Created on Feb 17, 2018

@author: phass
'''

import xml.etree.ElementTree as ET
import system, os
from ils.common.config import getDatabaseClient
from ils.common.error import catchError, notifyError
log=system.util.getLogger("com.ils.sfc.import")

def importRecipeDataCallback(event):
    db = getDatabaseClient()
    rootContainer = event.source.parent.parent
    folder = rootContainer.importExportFolder
    filename = system.file.openFile(".xml", folder)
    if filename != None:
        importRecipeData(filename, db)
        folder = os.path.basename(filename)
        print "The folder is: ", folder
        rootContainer.importExportFolder = folder
        
def buildFolderPath(recipeDataKey, oldParentFolderId, folderPaths):
    print "Building a folder path from: ", recipeDataKey, oldParentFolderId, folderPaths
    folderPath = recipeDataKey
    return folderPath

class Importer():
    db = None
    sql = None
    root = None
    stepTypes = None
    recipeDataTypes = None
    valueTypes = None
    outputTypes = None
    
    def __init__(self, db):
        self.db = db
        self.sql = Sql(db)
        
    def importFromFile(self, filename):
        log.infof("In %s,importFromFile() with %s", __name__, filename)
        tree = ET.parse(filename)
        root = tree.getroot()
        self.importTree(root)

    def importFromString(self, txt):
        log.infof("In %s.importString()", __name__)
        print "txt: ", txt
        root = ET.fromstring(txt)
        print "Parsed tree!"
        self.importTree(root)
        
    def importTree(self, root):
        print "...importing..."
        self.root = root
        
        self.sql.loadRecipeDataArrayKeys()
        self.stepTypes = self.sql.loadStepTypes()
        self.recipeDataTypes = self.sql.loadRecipeDataTypes()
        self.valueTypes = self.sql.loadValueTypes()
        self.outputTypes = self.sql.loadOutputTypes()
        
        '''
        The import file is a list of charts, it does not contain the hierarchy.  The import is flat, i.e, not nested.
        Before we import, we need to delete.  Hopefully there are enough cascade deletes that all we have to do is delete the chart
        and the steps and recipe data will follow.
        **************************************************************************************************************
        *** This is deleting the recipe data, NOT The charts - I'm not sure if this is intentional or an oversight ***
        **************************************************************************************************************
        '''
        try:
            chartPath = ""
            chartCount = 0
            recipeDataCount = 0
            for chart in self.root.findall("chart"):
                chartPath = chart.get("chartPath")
                log.tracef("Deleting recipe data for Chart: %s", chartPath)
                rows = self.sql.deleteRecipeDataForChart(chartPath) 
                chartCount = chartCount + 1
                recipeDataCount = recipeDataCount + rows
            
            self.sql.commit()
            log.infof("Deleted %d rows of recipe data for %d charts!", recipeDataCount, chartCount) 
        except:
            print "Caught an error deleting recipe data - rolling back and closing the transaction"
            self.sql.rollbackAndClose()
            notifyError(__name__ + ".importRecipeData.py", "Deleting recipe data for chart: %s" % (str(chartPath)))
            return
    
        '''
        Load the matrix and array keys if there are any new ones.
        '''
        try:
            cnt = self.sql.insertNewRecipeDataArrayKeys(self.root)
            self.sql.commit()
            log.infof("Successfully imported %d array / matrix keys!", cnt)
        except:
            print "Caught an error inserting recipe data - rolling back and closing the transaction"
            self.sql.rollbackAndClose()
            notifyError(__name__ + ".importRecipeData.py", "Importing array and matrix keys")
            return
    
        '''
        Now insert charts, steps, and recipe data
        '''    
        try:
            self.sql.loadRecipeDataArrayKeys()      # Reload to capture the newly added ones
            chartCounter = 0
            stepCounter = 0
            recipeDataCounter = 0
            chartPath = ""
            stepName = ""
            
            for chart in self.root.findall("chart"):
                chartPath = chart.get("chartPath")
                chartId = self.sql.insertChart(chartPath)
                chartCounter = chartCounter + 1
                
                for step in chart.findall("step"):
                    stepName = step.get("stepName")
                    stepUUID = step.get("stepUUID")
                    stepType = step.get("stepType")
                    stepTypeId = self.stepTypes.get(stepType, -99)
                    if stepTypeId == -99:
                        log.errorf("Unable to import step type: %s", stepType)
                        self.sql.rollbackAndClose()
                        system.gui.errorBox("Error: Unable to import step %s, of unknown type: %s for chart %s" % (stepName, stepType, chartPath))
                        return
        
                    stepId = self.sql.insertStep(chartId, stepUUID, stepName, stepTypeId)
                    stepCounter = stepCounter + 1
                    
                    ''' Insert Folders '''
                    folderIds = {}
                    folderKeys = {}
                    folderPaths = {}
                    print "  Checking for recipe folders..."
                    for folder in step.findall("recipeFolder"):
                        print "  --------------"
    
                        recipeDataKey = folder.get("recipeDataKey")
                        oldFolderId = folder.get("folderId")
                        oldParentFolderId = folder.get("parentFolderId")
                        label = folder.get("label", "")
                        description = folder.get("description", "")
                        folderPaths[recipeDataKey] = {'id': oldFolderId, 'parentId': oldParentFolderId}
                        print "  Looking at ", recipeDataKey, oldFolderId, oldParentFolderId, label, description
                        print "    Folder Ids: ", folderIds
                        
                        if oldParentFolderId != "None":
                            parentFolderId = folderIds[oldParentFolderId]
                            print "  Mapped old folder id %s to new folder id %s" % (oldParentFolderId, parentFolderId)
                        else:
                            parentFolderId = None
    
                        folderId = self.sql.insertRecipeDataFolder(stepId, recipeDataKey, description, label, parentFolderId)
                        print "  Inserted %s with new id: %s" % (recipeDataKey, str(folderId))
                        folderIds[oldFolderId] = folderId
                        folderKeys[recipeDataKey] = folderId
                        folderPath = buildFolderPath(recipeDataKey, oldParentFolderId, folderPaths)
                    
                        print "  The folder id dictionary is: ", folderIds
                        print "  The folder keys dictionary is: ", folderKeys
                
                    ''' Insert Recipe Data '''
                    log.debugf("**********************")
                    log.debugf("  Checking for recipe data...")
                    log.debugf("**********************")
                    for recipe in step.findall("recipe"):
                        folderId = None
                        recipeDataType = recipe.get("recipeDataType")
                        recipeDataTypeId = self.recipeDataTypes.get(recipeDataType, -99)
                        recipeDataKey = recipe.get("recipeDataKey")
                        label = recipe.get("label")
                        description = recipe.get("description")
                        parent = recipe.get("parent")
                        print "%s - <%s>" % (recipeDataKey, parent) 
                        
                        if parent not in ["", None]:
                            if parent[len(parent)-1] == '/':
                                print "  -- stripping trailing / --"
                                parent = parent[:len(parent)-1]
                            print "  Parent <%s>" % (parent)
                            tokens = parent.split("/")
                            print "  The tokens are: ", tokens
                            folder = tokens[len(tokens)-1]
                            print "  The terminal folder is: ", folder
                           
                            print "The id for ", folder
                            folderId = folderKeys[folder]
                            print "   is ", folderId
                            
                        
                        if recipeDataType == "Simple Value":
                            valueType = recipe.get("valueType")
                            valueTypeId = self.valueTypes.get(valueType, -99)
                            val = recipe.get("value")
                            units = recipe.get("units", "")
                            recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, folderId)
                            self.sql.insertSimpleRecipeData(recipeDataId, valueType, valueTypeId, val)
                            recipeDataCounter = recipeDataCounter + 1
                        
                        elif recipeDataType in ["Output", "Output Ramp"]:
                            valueType = recipe.get("valueType")
                            valueTypeId = self.valueTypes.get(valueType, -99)
                            val = recipe.get("value")
                            units = recipe.get("units", "")
                            outputType = recipe.get("outputType", "")
                            outputTypeId = self.outputTypes.get(outputType, -99)
                            tag = recipe.get("tag", "")
                            download = recipe.get("download", "True")
                            timing = recipe.get("timing", "0.0")
                            maxTiming = recipe.get("maxTiming", "0.0")
                            writeConfirm = recipe.get("writeConfirm", "True")
                            
                            recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, folderId)
                            self.sql.insertOutputRecipeData(recipeDataId, valueType, valueTypeId, outputType, outputTypeId, tag, download, timing, maxTiming, val, writeConfirm)
                            recipeDataCounter = recipeDataCounter + 1
                            
                            if recipeDataType == "Output Ramp":
                                rampTimeMinutes = recipe.get("rampTimeMinutes", "0.0")
                                updateFrequencySeconds = recipe.get("updateFrequencySeconds", "0.0")
                                self.sql.insertOutputRampRecipeData(recipeDataId, rampTimeMinutes, updateFrequencySeconds)
        
                        elif recipeDataType in ["Input"]:
                            valueType = recipe.get("valueType")
                            valueTypeId = self.valueTypes.get(valueType, -99)
                            units = recipe.get("units", "")
                            tag = recipe.get("tag", "")
        
                            recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, folderId)
                            self.sql.insertInputRecipeData(recipeDataId, valueType, valueTypeId, tag)
                            recipeDataCounter = recipeDataCounter + 1
        
                        elif recipeDataType == "Array":
                            valueType = recipe.get("valueType")
                            valueTypeId = self.valueTypes.get(valueType, -99)
                            units = recipe.get("units", "")
                            indexKey = recipe.get("indexKey", None)
                            print "The array index key is: ", indexKey
                            recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, folderId)
                            self.sql.insertArray(recipeDataId, valueType, valueTypeId, indexKey)
                            recipeDataCounter = recipeDataCounter + 1
                            
                            for element in recipe.findall("element"):
                                arrayIndex = element.get("arrayIndex")
                                val = element.get("value")
                                self.sql.insertArrayElement(recipeDataId, valueType, valueTypeId, arrayIndex, val)
              
                        elif recipeDataType == "Matrix":
                            valueType = recipe.get("valueType")
                            valueTypeId = self.valueTypes.get(valueType, -99)
                            units = recipe.get("units", "")
                            rows = recipe.get("rows", "")
                            columns = recipe.get("columns", "")
                            
                            rowIndexKey = recipe.get("rowIndexKey", None)
                            columnIndexKey = recipe.get("columnIndexKey", None)
                                
                            recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, folderId)
                            self.sql.insertMatrix(recipeDataId, valueType, valueTypeId, rows, columns, rowIndexKey, columnIndexKey)
                            recipeDataCounter = recipeDataCounter + 1
                            
                            for element in recipe.findall("element"):
                                rowIndex = element.get("rowIndex")
                                columnIndex = element.get("columnIndex")
                                val = element.get("value")
                                self.sql.insertMatrixElement(recipeDataId, valueType, valueTypeId, rowIndex, columnIndex, val)
                        
                        elif recipeDataType == "Timer":
                            units = recipe.get("units", "")
                            recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, folderId)
                            self.sql.insertTimerRecipeData(recipeDataId)
                            recipeDataCounter = recipeDataCounter + 1
                        
                        elif recipeDataType == "Recipe":
                            units = recipe.get("units", "")
                            presentationOrder = recipe.get("presentationOrder", "0")
                            storeTag = recipe.get("storeTag", "")
                            compareTag = recipe.get("compareTag", "")
                            modeAttribute = recipe.get("modeAttribute", "")
                            changeLevel = recipe.get("changeLevel", "")
                            recommendedValue = recipe.get("recommendedValue", "")
                            lowLimit = recipe.get("lowLimit", "")
                            highLimit = recipe.get("highLimit", "")
                            
                            recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, units, folderId)
                            self.sql.insertRecipeRecipeData(recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, changeLevel, recommendedValue, lowLimit, highLimit)
                            recipeDataCounter = recipeDataCounter + 1
                            
                        else:
                            txt = "Error: Unable to import recipe data type: %s with key %s for step %s on chart %s" % (recipeDataType, recipeDataKey, stepName, chartPath)
                            print txt
                            log.errorf(txt)
                            self.sql.rollbackAndClose()
                            system.gui.errorBox(txt)
                            return
                            
            self.sql.commit()
            
            '''
            Now insert the chart hierarchy
            '''
            self.sql.loadCharts()
            
            log.tracef("Looking for parent/child relationships...")
            for parentChild in self.root.findall("parentChild"):
                parentChartPath = parentChild.get("parent")
                childChartPath = parentChild.get("child")
                stepName = parentChild.get("stepName")
                self.sql.insertHierarchy(parentChartPath, stepName, childChartPath)

            '''
            We are done, commit and close the transaction!
            '''
            log.tracef("Done!")
            self.sql.commitAndClose()
            system.gui.messageBox("Successfully imported %d charts, %d steps, and %d recipe datums!" % (chartCounter, stepCounter, recipeDataCounter))
        except:
            print "Caught an error inserting recipe data - rolling back and closing the transaction"
            self.sql.rollbackAndClose()
            notifyError(__name__ + ".importRecipeData.py", "Importing recipe data for chart %s step %s" % (str(chartPath), str(stepName)))


class Sql():
    txId = None
    db = None
    recipeDataArrayKeys = None
    chartPDS = None
    
    def __init__(self, db):
        txId = system.db.beginTransaction(db)
        self.txId = txId
        self.db = db

    def commit(self):
        system.db.commitTransaction(self.txId)
        
    def commitAndClose(self):
        system.db.commitTransaction(self.txId)
        system.db.closeTransaction(self.txId)
        
    def rollbackAndClose(self):
        system.db.rollbackTransaction(self.txId)
        system.db.closeTransaction(self.txId)
        
    def deleteRecipeDataForChart(self, chartPath):
        log.infof("      Deleting recipe data for chart:  %s...", chartPath)
        SQL = "select RecipeDataId "\
            "from SfcChart C, SfcStep S, SfcRecipeData RD "\
            "where C.ChartPath = '%s' "\
            "and C.ChartId = S.ChartId "\
            "and S.StepId = RD.StepId" % (chartPath)
            
        totalRows = 0
        pds = system.db.runQuery(SQL, tx=self.txId)
        for record in pds:
            recipeDataId = record["RecipeDataId"]
            SQL = "delete from SfcRecipeData where RecipeDataId = %s" % (recipeDataId)
            rows = system.db.runUpdateQuery(SQL, tx=self.txId)
            totalRows = totalRows + rows
        
        log.infof("      ...deleted %d rows", totalRows)
        return totalRows
    
    def loadCharts(self):
        log.tracef("Loading charts...")
        self.chartPDS = system.db.runQuery("Select ChartId, ChartPath from SfcChart order by ChartId", tx=self.txId)
        log.tracef("...loaded %d charts!", len(self.chartPDS))

    def loadRecipeDataArrayKeys(self):
        SQL = "select KeyName, KeyId from SfcRecipeDataKeyMaster"
        pds = system.db.runQuery(SQL, self.db)
        
        recipeDataArrayKeys = {}
        for record in pds:
            recipeDataArrayKeys[record["KeyName"]] = record["KeyId"]
        
        log.tracef("The existing recipe data array keys are: %s", str(recipeDataArrayKeys))
        self.recipeDataArrayKeys = recipeDataArrayKeys
        
    def loadRecipeDataTypes(self):
        SQL = "select RecipeDataTypeId, RecipeDataType from SfcRecipeDataType"
        pds = system.db.runQuery(SQL, self.db)
        
        recipeDataTypes = {}
        for record in pds:
            recipeDataTypes[record["RecipeDataType"]] = record["RecipeDataTypeId"]
        
        return recipeDataTypes
    
    def loadValueTypes(self):
        SQL = "select ValueTypeId, ValueType from SfcValueType"
        pds = system.db.runQuery(SQL, self.db)
        
        valueTypes = {}
        for record in pds:
            valueTypes[record["ValueType"]] = record["ValueTypeId"]
        
        return valueTypes
        
    def loadStepTypes(self):
        SQL = "select StepTypeId, StepType from SfcStepType order by stepType"
        pds = system.db.runQuery(SQL, self.db)
        
        stepTypes = {}
        for record in pds:
            stepTypes[record["StepType"]] = record["StepTypeId"]
        
        log.infof("The step types are: %s", str(stepTypes))
        return stepTypes
    
    def loadOutputTypes(self):
        SQL = "select OutputTypeId, OutputType from SfcRecipeDataOutputType"
        pds = system.db.runQuery(SQL, self.db)
        
        recipeOutputTypes = {}
        for record in pds:
            recipeOutputTypes[record["OutputType"]] = record["OutputTypeId"]
        
        return recipeOutputTypes

        
    def insertNewRecipeDataArrayKeys(self, root):
        cnt = 0
        
        for key in root.findall("key"):
            keyName = key.get("name")
            
            if keyName not in self.recipeDataArrayKeys:
                log.tracef("Inserting Key: %s...", keyName)
                cnt = cnt + 1
                
                SQL = "Insert into SfcRecipeDataKeyMaster (KeyName) values ('%s')" % (keyName)
                keyId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
                log.tracef("   ...inserted key with id: %d", keyId)
                
                for element in key.findall("element"):
                    val = element.get("value")
                    idx = element.get("index")
                    
                    log.tracef("%s - %s - %s", keyName, str(val), str(idx))
                    SQL = "Insert into SfcRecipeDataKeyDetail (KeyId, KeyValue, KeyIndex) values (%d, '%s', %s)" % (keyId, val, idx)
                    system.db.runUpdateQuery(SQL, tx=self.txId)
            else:
                log.tracef("Key: %s already exists.", keyName)
            
        return cnt

    def insertHierarchy(self, parentChartPath, stepName, childChartPath, chartPDS):
        
        def getChartIdFromPath(chartPath, chartPDS):
            for chart in chartPDS:
                if chart["ChartPath"] == chartPath:
                    return chart["ChartId"]
            return -1
    
        log.tracef("Inserting parent: <%s> and child <%s> into chart hierarchy...", parentChartPath, childChartPath)
        parentChartId = getChartIdFromPath(parentChartPath, chartPDS)
        childChartId = getChartIdFromPath(childChartPath, chartPDS)
        SQL = "Select stepId from SfcStep where ChartId = %s and StepName = '%s'" % (str(parentChartId), stepName)
        stepId = system.db.runScalarQuery(SQL, tx=self.txId)
        
        SQL = "insert into SfcHierarchy (StepId, ChartId, ChildChartId) values (%s, %s, %s)" % (str(stepId), str(parentChartId), str(childChartId))
        system.db.runUpdateQuery(SQL, tx=self.txId)
    
    def insertChart(self, chartPath):
        log.infof("Inserting chart: %s...", chartPath)
        
        SQL = "Select chartId from SfcChart where chartPath = '%s'" % (chartPath)
        chartId = system.db.runScalarQuery(SQL, tx=self.txId)
        
        if chartId == None:
            SQL = "insert into SfcChart (ChartPath) values ('%s')" % (chartPath)
            chartId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
            log.infof("   ...inserted chart with id: %d", chartId)
        else:
            log.infof("   ...chart already exists with id: %d", chartId)
            
        return chartId
    
    def insertStep(self, chartId, stepUUID, stepName, stepTypeId):
        log.infof("   Inserting step: %s - type: %d...", stepName, stepTypeId)
        
        SQL = "select stepId from SfcStep where StepUUID = '%s'" % (stepUUID)
        stepId = system.db.runScalarQuery(SQL, tx=self.txId)
        
        if stepId == None:
            SQL = "insert into SfcStep (StepUUID, StepName, StepTypeId, ChartId) values ('%s', '%s', %s, %s)" % (stepUUID, stepName, str(stepTypeId), str(chartId))
            stepId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
            log.infof("      ...inserted step with id: %d", stepId)
        else:
            log.infof("      ...step already exists with id: %d", stepId)
            
        return stepId
    
    def insertRecipeDataFolder(self, stepId, recipeDataKey, description, label, parentFolderId):
        if parentFolderId == None:
            SQL = "insert into SfcRecipeDataFolder (RecipeDataKey, StepId, Description, Label) values ('%s', %d, '%s', '%s')" % (recipeDataKey, stepId, description, label)
        else:
            SQL = "insert into SfcRecipeDataFolder (RecipeDataKey, StepId, Description, Label, ParentRecipeDataFolderId) "\
                " values ('%s', %d, '%s', '%s', %d)" % (recipeDataKey, stepId, description, label, parentFolderId)
        folderId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
        return folderId
    
    def insertRecipeData(self, stepId, key, recipeDataType, recipeDataTypeId, label, description, units, folderId):
        log.infof("      Inserting recipe data key:  %s, a %s...", key, recipeDataType)
        if folderId == None:
            SQL = "insert into SfcRecipeData (StepID, RecipeDataKey, RecipeDataTypeId, Label, Description, Units) values (%d, '%s', %d, '%s', '%s', '%s')" % \
                (stepId, key, recipeDataTypeId, label, description, units)
        else:
            SQL = "insert into SfcRecipeData (StepID, RecipeDataKey, RecipeDataTypeId, Label, Description, RecipeDataFolderId, Units) values (%d, '%s', %d, '%s', '%s', %d, '%s')" % \
                (stepId, key, recipeDataTypeId, label, description, folderId, units)
        recipeDataId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
        return recipeDataId
    
    def insertSimpleRecipeData(self, recipeDataId, valueType, valueTypeId, val):
        log.tracef("          Inserting a Simple Value: %s, a %s...", str(val), str(valueType))
        valueId = self.insertRecipeDataValue(recipeDataId, valueType, val)
        SQL = "insert into SfcRecipeDataSimpleValue (recipeDataId, valueTypeId, ValueId) values (%d, %d, %d)" % (recipeDataId, valueTypeId, valueId)
        system.db.runUpdateQuery(SQL, tx=self.txId)
    
    def insertOutputRecipeData(self, recipeDataId, valueType, valueTypeId, outputType, outputTypeId, tag, download, timing, maxTiming, val, writeConfirm):
            log.tracef("          Inserting an Output recipe data...")
            outputValueId = self.insertRecipeDataValue(recipeDataId, valueType, val)
            targetValueId = self.insertRecipeDataValue(recipeDataId, valueType, 0.0)
            pvValueId = self.insertRecipeDataValue(recipeDataId, valueType, 0.0)
            SQL = "insert into SfcRecipeDataOutput (recipeDataId, valueTypeId, outputTypeId, tag, download, timing, maxTiming, outputValueId, targetValueId, pvValueId, writeConfirm) "\
                "values (%d, %d, %d, '%s', '%s', %s, %s, %d, %d, %d, '%s')" % \
                (recipeDataId, valueTypeId, outputTypeId, tag, download, str(timing), str(maxTiming), outputValueId, targetValueId, pvValueId, writeConfirm)
            system.db.runUpdateQuery(SQL, tx=self.txId)

    def insertOutputRampRecipeData(self, recipeDataId, rampTimeMinutes, updateFrequencySeconds):
        log.tracef("          Inserting an Output Ramp recipe data...")
        SQL = "insert into SfcRecipeDataOutputRamp (recipeDataId, rampTimeMinutes, updateFrequencySeconds) values (%d, %s, %s)" % \
            (recipeDataId, str(rampTimeMinutes), str(updateFrequencySeconds))
        system.db.runUpdateQuery(SQL, tx=self.txId)
        
    def insertInputRecipeData(self, recipeDataId, valueType, valueTypeId, tag):
        log.tracef("          Inserting an Input recipe data...")
        targetValueId = self.insertRecipeDataValue(recipeDataId, valueType, 0.0)
        pvValueId = self.insertRecipeDataValue(recipeDataId, valueType, 0.0)
        SQL = "insert into SfcRecipeDataInput (recipeDataId, valueTypeId, tag, pvValueId, targetValueId) values (%d, %d, '%s', %d, %d)" % \
            (recipeDataId, valueTypeId, tag, pvValueId, targetValueId)
        system.db.runUpdateQuery(SQL, tx=self.txId)
        
    def insertArray(self, recipeDataId, valueType, valueTypeId, indexKey):
        log.tracef("          Inserting an array...")
        if indexKey in [None, 'None']:
            log.tracef("          Inserting an array...")
            SQL = "insert into SfcRecipeDataArray (recipeDataId, valueTypeId) values (%d, %d)" % (recipeDataId, valueTypeId)
        else:
            log.tracef("          Inserting a KEYED array...")
            indexKeyId = self.recipeDataArrayKeys.get(indexKey,"ERROR")
            SQL = "insert into SfcRecipeDataArray (recipeDataId, valueTypeId, indexKeyId) values (%d, %d, %d)" % (recipeDataId, valueTypeId, indexKeyId)
        system.db.runUpdateQuery(SQL, tx=self.txId)
        
    def insertArrayElement(self, recipeDataId, valueType, valueTypeId, arrayIndex, val):
        log.tracef("          Inserting an array element...")
        valueId = self.insertRecipeDataValue(recipeDataId, valueType, val)
        SQL = "insert into SfcRecipeDataArrayElement (recipeDataId, arrayIndex, ValueId) values (%d, %d, %d)" % (recipeDataId, int(arrayIndex), valueId)
        system.db.runUpdateQuery(SQL, tx=self.txId)

    def insertMatrix(self, recipeDataId, valueType, valueTypeId, rows, columns, rowIndexKey, columnIndexKey, arrayIndexKeys):
        log.tracef("          Inserting a matrix...")
        
        if rowIndexKey == None:
            rowIndexKeyId = 'NULL'
        else:
            rowIndexKeyId = arrayIndexKeys.get(rowIndexKey, 'NULL')
    
        if columnIndexKey == None:
            columnIndexKeyId = 'NULL'
        else:
            columnIndexKeyId = arrayIndexKeys.get(columnIndexKey, 'NULL')
        
        SQL = "insert into SfcRecipeDataMatrix (recipeDataId, valueTypeId, rows, columns, rowIndexKeyId, columnIndexKeyId) values (%d, %d, %d, %d, %s, %s)" % (recipeDataId, valueTypeId, int(rows), int(columns), rowIndexKeyId, columnIndexKeyId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=self.txId)
    
    def insertMatrixElement(self, recipeDataId, valueType, valueTypeId, rowIndex, columnIndex, val):
        log.tracef("          Inserting a matrix element...")
        valueId = self.insertRecipeDataValue(recipeDataId, valueType, val)
        SQL = "insert into SfcRecipeDataMatrixElement (recipeDataId, rowIndex, columnIndex, ValueId) values (%d, %d, %d, %d)" % (recipeDataId, int(rowIndex), int(columnIndex), valueId)
        system.db.runUpdateQuery(SQL, tx=self.txId)
    
    def insertTimerRecipeData(self, recipeDataId):
        log.tracef("          Inserting a Timer...")
        SQL = "insert into SfcRecipeDataTimer (recipeDataId) values (%d)" % (recipeDataId)
        system.db.runUpdateQuery(SQL, tx=self.txId)
    
    def insertRecipeRecipeData(self, recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, changeLevel, recommendedValue, lowLimit, highLimit):
        log.tracef("          Inserting a RECIPE recipe data...")
        SQL = "insert into SfcRecipeDataRecipe (recipeDataId, PresentationOrder, StoreTag, CompareTag, ModeAttribute, ChangeLevel, RecommendedValue, LowLimit, HighLimit) "\
            " values (%d, %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
            (recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, changeLevel, recommendedValue, lowLimit, highLimit)
        system.db.runUpdateQuery(SQL, tx=self.txId)
    
    def insertRecipeDataValue(self, recipeDataId, valueType, val):
        log.tracef("        Inserting a recipe data value (type: %s, value: %s)...", valueType, val)
        
        if val in [None, 'None']:
            SQL = "insert into SfcRecipeDataValue (RecipeDataId, StringValue) values (%d, NULL)" % (recipeDataId)   
        elif valueType == "String":
            SQL = "insert into SfcRecipeDataValue (RecipeDataId, StringValue) values (%d, '%s')" % (recipeDataId, val)
        elif valueType == "Integer":
            SQL = "insert into SfcRecipeDataValue (RecipeDataId, IntegerValue) values (%d, %d)" % (recipeDataId, int(val))
        elif valueType == "Float":
            SQL = "insert into SfcRecipeDataValue (RecipeDataId, FloatValue) values (%d, %f)" % (recipeDataId, float(val))
        elif valueType == "Boolean":
            SQL = "insert into SfcRecipeDataValue (RecipeDataId, BooleanValue) values (%d, '%s')" % (recipeDataId, val)
        
        valueId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
        return valueId