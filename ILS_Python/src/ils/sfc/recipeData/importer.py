'''
Created on Feb 17, 2018

@author: phass
'''

import xml.etree.ElementTree as ET
import system, os
from ils.common.config import getDatabaseClient
from ils.common.error import notifyError
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def importRecipeDataCallback(event):
    db = getDatabaseClient()
    rootContainer = event.source.parent.parent
    folder = rootContainer.importExportFolder
    filename = system.file.openFile(".xml", folder)
    if filename != None:
        importer = Importer(db)
        importer.importFromFile(filename)
#        folder = os.path.basename(filename)
#        print "The folder is: ", folder
#        rootContainer.importExportFolder = folder

def importStepRecipeDataCallback(event):
    
    try:
        db = getDatabaseClient()
        log.infof("In %s.importStepRecipeDataCallback()...", __name__)
        
        stepContainer = event.source.parent
        rootContainer = event.source.parent.parent
        treeContainer = rootContainer.getComponent("Tree Container")
        
        chartViewState = rootContainer.chartViewState
        if chartViewState == 0:
            treeWidget = treeContainer.getComponent("Tree View")
        
            # First get the last node in the path
            chartPath = treeWidget.selectedPath
            log.tracef("The raw selected path is: <%s>", chartPath)
            chartPath = chartPath[chartPath.rfind("/")+1:]
            log.tracef("The selected chart path is <%s>", chartPath)
        else:
            table = treeContainer.getComponent("Power Table")
            if table.selectedRow < 0:
                system.gui.messageBox("Please select a chart.")
                return
            ds = table.data
            chartPath = ds.getValueAt(table.selectedRow, "chartPath")
            log.tracef("The selected chart path is <%s>", chartPath)
    
        chartPath = chartPath[chartPath.rfind("/")+1:]
        log.tracef("The selected chart path is <%s>", chartPath)
        
        # Now replace " / " with "/"
        chartPath = chartPath.replace(' \ ', '/')
        log.infof("The selected chart path is <%s>", chartPath)
        if chartPath == "" or chartPath == None:
            return
        
        # Now get the selected step
        stepList = stepContainer.getComponent("Steps")
        selectedRow = stepList.selectedRow
        if selectedRow < 0:
            return
        
        ds = stepList.data
        stepName = ds.getValueAt(selectedRow, 0)
        stepId = ds.getValueAt(selectedRow, 2)
        log.infof("The selected step is <%s> (%d)", stepName, stepId)
    
        folder = rootContainer.importExportFolder
        filename = system.file.openFile("xml", folder)
        if filename == None:
            return
        
        folder = os.path.dirname(filename)
        rootContainer.importExportFolder = folder
        
        importer = Importer(db)
        importer.importStepFromFile(filename, chartPath, stepName, stepId)
        
    except:
        notifyError("%s.importStepRecipeDataCallback()" % (__name__), "Check the console log for details.")



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
    trees = None
    
    def __init__(self, db):
        self.db = db
        self.sql = Sql(db)
        
    def importFromFile(self, filename):
        log.infof("In %s,importFromFile() with %s", __name__, filename)
        tree = ET.parse(filename)
        root = tree.getroot()
        success = self.importTree(root)
        return success

    def importFromString(self, txt):
        log.infof("In %s.importString()", __name__)
        log.tracef("XML to import: %s", txt)
        log.tracef("...parsing XML...")
        root = ET.fromstring(txt)
        log.tracef("...importing the parsed tree...")
        success = self.importTree(root)
        return success
    
    def importStepFromFile(self, filename, chartPath, stepName, stepId):
        log.infof("In %s,importFromFile() with %s", __name__, filename)
        
        try:
            tree = ET.parse(filename)
            
            self.sql.loadRecipeDataArrayKeys()
            self.stepTypes = self.sql.loadStepTypes()
            self.recipeDataTypes = self.sql.loadRecipeDataTypes()
            self.valueTypes = self.sql.loadValueTypes()
            self.outputTypes = self.sql.loadOutputTypes()
            
            step = tree.getroot()
            cntr = self.importStepRecipe(step, chartPath, stepName, stepId)
            
            ''' We are done, commit and close the transaction! '''
            log.tracef("Done!")
            self.sql.commitAndClose()
            system.gui.messageBox("Successfully imported %d recipe datums!" % (cntr))
            
        except:
            log.errorf( "Caught an error inserting recipe data - rolling back and closing the transaction")
            self.sql.rollbackAndClose()
            notifyError("%s.importStepFromFile()" % (__name__), "Check the console log for details.")
        
        return
        
    def importTree(self, root):
        self.root = root
        
        self.sql.loadRecipeDataArrayKeys()
        self.stepTypes = self.sql.loadStepTypes()
        self.recipeDataTypes = self.sql.loadRecipeDataTypes()
        self.valueTypes = self.sql.loadValueTypes()
        self.outputTypes = self.sql.loadOutputTypes()
        
        '''
        The import file is a list of charts, it does not contain the hierarchy.  The import is flat, i.e, not nested.
        Before we import, we need to delete recipe data, steps, charts, and the chart hierarchy. 
        Before we delete, record parents of charts that are outside the scope of the import.  For example, if we are importing
        a single chart, we need to record the parents of the chart, if it already exists, so that the newly imported chart will be related to the same parent. 
        '''
        parents = {}
        for chart in self.root.findall("chart"):
                chartPath = chart.get("chartPath")
                chartParents = self.sql.fetchParentInfo(chartPath)
                parents[chartPath] = chartParents
        log.tracef("The parents are: %s", str(parents))
        
        ''' Now delete '''
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
                self.sql.deleteChartFromHierarchy(chartPath)
            self.sql.commit()
            log.infof("Deleted %d rows of recipe data for %d charts!", recipeDataCount, chartCount) 
        except:
            print "Caught an error deleting recipe data - rolling back and closing the transaction"
            self.sql.rollbackAndClose()
            notifyError(__name__ + ".importRecipeData.py", "Deleting recipe data for chart: %s" % (str(chartPath)))
            return False
        
        '''
        Now make another pass and delete the charts
        '''
        try:
            chartPath = ""
            chartCount = 0
            recipeDataCount = 0
            for chart in self.root.findall("chart"):
                chartPath = chart.get("chartPath")
                log.tracef("Deleting chart: %s", chartPath)
                rows = self.sql.deleteChart(chartPath) 
                chartCount = chartCount + rows
            
            self.sql.commit()
            log.infof("Deleted %d charts!", chartCount) 
        except:
            print "Caught an error deleting charts - rolling back and closing the transaction"
            self.sql.rollbackAndClose()
            notifyError(__name__ + ".importRecipeData.py", "Deleting chart: %s" % (str(chartPath)))
            return False
    
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
            return False
    
        '''
        Now insert charts, steps, and recipe data
        '''    
        try:
            log.infof("Inserting charts, steps, and recipe data...")
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
                        return False
        
                    stepId = self.sql.insertStep(chartId, stepUUID, stepName, stepTypeId)
                    stepCounter = stepCounter + 1
                    
                    ''' Refactored here - Pete 5/13/21 ''' 
                    cntr = self.importStepRecipe(step, chartPath, stepName, stepId)
                    recipeDataCounter += cntr
      
            self.sql.commit()
            
            '''
            Now insert the chart hierarchy - update the chartPDS data structure with the new charts that were added
            '''
            self.sql.loadCharts()
            
            log.tracef("Loading parent/child relationships from the XML data...")
            for parentChild in self.root.findall("parentChild"):
                parentChartPath = parentChild.get("parent")
                childChartPath = parentChild.get("child")
                stepName = parentChild.get("stepName")
                self.sql.insertHierarchy(parentChartPath, stepName, childChartPath)

            '''
            Now restore the parent child relations that were destroyed in the beginning when we deleted the existing charts
            '''
            self.restoreParents(parents)
                
            '''
            We are done, commit and close the transaction!
            '''
            log.tracef("Done!")
            self.sql.commitAndClose()
            system.gui.messageBox("Successfully imported %d charts, %d steps, and %d recipe datums!" % (chartCounter, stepCounter, recipeDataCounter))
            return True
        
        except:
            log.errorf( "Caught an error inserting recipe data - rolling back and closing the transaction")
            self.sql.rollbackAndClose()
            notifyError(__name__ + ".importRecipeData.py", "Importing recipe data for chart %s step %s" % (str(chartPath), str(stepName)))
            return False
    
    def importStepRecipe(self, step, chartPath, stepName, stepId):
        cntr = 0
        
        ''' Insert Folders '''
        log.tracef("  Checking for recipe folders...")
        self.parseFolders(step, stepId)
        
        ''' Insert Recipe Data '''
        log.debugf("**********************")
        log.debugf("  Checking for recipe data...")
        log.debugf("**********************")
        for recipe in step.findall("recipe"):
            print "Recipe: ", recipe
            folderId = None
            recipeDataType = recipe.find("recipeDataType").text
            recipeDataTypeId = self.recipeDataTypes.get(recipeDataType, -99)
            recipeDataKey = recipe.find("recipeDataKey").text
            label = recipe.find("label").text
            description = recipe.find("description").text
            advice = recipe.find("advice").text
            parent = recipe.find("parent").text
            log.tracef( "%s - <%s>, a %s - %s - %s", recipeDataKey, parent, recipeDataType, label, description) 
            
            if parent not in ["", None]:
                folderId = self.findFolder(parent)
            
            if recipeDataType == "Simple Value":
                valueType = recipe.find("valueType").text
                valueTypeId = self.valueTypes.get(valueType, -99)
                val = recipe.find("value").text
                units = recipe.find("units").text
                recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
                self.sql.insertSimpleRecipeData(recipeDataId, valueType, valueTypeId, val)
                cntr += 1
            
            elif recipeDataType in ["Output", "Output Ramp"]:
                valueType = recipe.find("valueType").text
                valueTypeId = self.valueTypes.get(valueType, -99)
                val = recipe.find("value").text
                units = recipe.find("units").text
                outputType = recipe.find("outputType").text
                outputTypeId = self.outputTypes.get(outputType, -99)
                tag = recipe.find("tag").text
                download = recipe.find("download").text
                timing = recipe.find("timing").text
                maxTiming = recipe.find("maxTiming").text
                writeConfirm = recipe.find("writeConfirm").text
                
                recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
                self.sql.insertOutputRecipeData(recipeDataId, valueType, valueTypeId, outputType, outputTypeId, tag, download, timing, maxTiming, val, writeConfirm)
                cntr += 1
                
                if recipeDataType == "Output Ramp":
                    rampTimeMinutes = recipe.find("rampTimeMinutes").text
                    updateFrequencySeconds = recipe.find("updateFrequencySeconds").text
                    self.sql.insertOutputRampRecipeData(recipeDataId, rampTimeMinutes, updateFrequencySeconds)

            elif recipeDataType in ["Input"]:
                valueType = recipe.find("valueType").text
                valueTypeId = self.valueTypes.get(valueType, -99)
                units = recipe.find("units").text
                tag = recipe.find("tag").text

                recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
                self.sql.insertInputRecipeData(recipeDataId, valueType, valueTypeId, tag)
                cntr += 1

            elif recipeDataType == "Array":
                valueType = recipe.find("valueType").text
                valueTypeId = self.valueTypes.get(valueType, -99)
                units = recipe.find("units").text
                indexKey = recipe.find("indexKey").text
                log.tracef( "The array index key is: %s", indexKey)
                recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
                self.sql.insertArray(recipeDataId, valueType, valueTypeId, indexKey)
                cntr += 1
                
                for element in recipe.findall("element"):
                    arrayIndex = element.find("arrayIndex").text
                    val = element.find("value").text
                    self.sql.insertArrayElement(recipeDataId, valueType, valueTypeId, arrayIndex, val)
  
            elif recipeDataType == "Matrix":
                valueType = recipe.find("valueType").text
                valueTypeId = self.valueTypes.get(valueType, -99)
                units = recipe.find("units").text
                rows = recipe.find("rows").text
                columns = recipe.find("columns").text
                
                rowIndexKey = recipe.find("rowIndexKey").text
                columnIndexKey = recipe.find("columnIndexKey").text
                    
                recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
                self.sql.insertMatrix(recipeDataId, valueType, valueTypeId, rows, columns, rowIndexKey, columnIndexKey)
                cntr += 1
                
                for element in recipe.findall("element"):
                    rowIndex = element.find("rowIndex").text
                    columnIndex = element.find("columnIndex").text
                    val = element.find("value").text
                    self.sql.insertMatrixElement(recipeDataId, valueType, valueTypeId, rowIndex, columnIndex, val)
            
            elif recipeDataType == "Timer":
                units = recipe.get("units", "")
                recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
                self.sql.insertTimerRecipeData(recipeDataId)
                cntr += 1
            
            elif recipeDataType == "Recipe":
                units = recipe.find("units").text
                presentationOrder = recipe.find("presentationOrder").text
                storeTag = recipe.find("storeTag").text
                compareTag = recipe.find("compareTag").text
                modeAttribute = recipe.find("modeAttribute").text
                modeValue = recipe.find("modeValue").text
                changeLevel = recipe.find("changeLevel").text
                recommendedValue = recipe.find("recommendedValue").text
                lowLimit = recipe.find("lowLimit").text
                highLimit = recipe.find("highLimit").text
                
                recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
                self.sql.insertRecipeRecipeData(recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit)
                cntr += 1
                
            elif recipeDataType == "SQC":
                units = recipe.find("units").text
                lowLimit = recipe.find("lowLimit").text
                highLimit = recipe.find("highLimit").text
                targetValue = recipe.find("targetValue").text
                
                log.tracef( "Inserting SQC recipe data with HL: %s, Target: %s, LL: %s ", str(lowLimit), str(targetValue), str(highLimit))
                
                recipeDataId = self.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
                self.sql.insertSqcRecipeData(recipeDataId, lowLimit, targetValue, highLimit)
                cntr += 1
                
            else:
                txt = "Error: Unable to import recipe data type: %s with key %s for step %s on chart %s" % (recipeDataType, recipeDataKey, stepName, chartPath)
                raise Exception, txt
#                log.errorf(txt)
#                self.sql.rollbackAndClose()
#                system.gui.errorBox(txt)
#                return 0
            
        return cntr
        
    def restoreParents(self, parents):
        '''
        The import will build parent child relationships for all of the charts within the scope of the import, but can't rebuild parent chart relationships
        for parents that were not imported.  Luckily, we fetched that information at the start of the import and will now restore it.
        '''
        log.infof("Restoring parents...")
        for chart in self.root.findall("chart"):
            childChartPath = chart.get("chartPath")
            log.tracef("Restoring the parents of: %s", str(childChartPath))
            chartParents = parents.get(childChartPath)
            log.tracef("The parents are: %s", str(chartParents))
            for parent in chartParents:
                parentChartPath = parent.get("chartPath", "")
                stepName = parent.get("stepName")
                self.sql.insertHierarchy(parentChartPath, stepName, childChartPath)
        return
        
    def parseFolders(self, step, stepId):
        folders = []
        log.tracef("In parseFolders()")
        for folder in step.findall("recipeFolder"):
            log.tracef("--------------")
            recipeDataKey = folder.get("recipeDataKey")
            log.tracef("Found folder key: %s", recipeDataKey)
            folderId = folder.get("folderId")
            parentFolderId = folder.get("parentFolderId")
            label = folder.get("label", "")
            description = folder.get("description", "")
            
            folders.append( {"key": recipeDataKey, "folderId": folderId, "parentFolderId": parentFolderId, "label": label, "description": description} )
        
        log.tracef("The folders are: %s", str(folders))
        
        ''' Build the tree '''
        i = 0
        trees = []
        max_i = len(folders)
        while len(folders) > 0 and i < max_i:
            log.tracef("Tree building pass #%d", i)
            for folder in folders:
                #if i == 0:
                if folder.get("parentFolderId", 'None') == 'None':
                    log.tracef("Inserting parentless folder named: %s", folder.get('key'))
                    folder["path"] = folder.get('key')
                    trees.append(folder)
                    folders.remove(folder)
                else:
                    folderId = folder.get('parentFolderId')
                    log.tracef("Looking for a parent id: %s", str(folderId))
                    for tree in trees:
                        if tree.get('folderId') == folderId:
                            folder["path"] = tree.get('path') + "/" + folder.get('key')
                            trees.append(folder)
                            folders.remove(folder)
    
            i = i + 1
        
        log.tracef("Trees: %s", str(trees))
        '''
        Now insert the folders and get new Ids
        '''
        log.tracef("  -- Inserting Folders --")
        newTrees = []
        for tree in trees:
            recipeDataKey = tree.get("key", "")
            path = tree.get("path","")
            parentFolderId = tree.get("parentFolderId")
            log.tracef("Processing %s with old parent Id %s", recipeDataKey, str(parentFolderId))
            if parentFolderId == 'None':
                log.tracef("...a root folder!")
                newParentFolderId = None
            else:
                for tempTree in newTrees:
                    log.tracef("...checking: %s", str(tempTree))
                    if tempTree.get("folderId", None) == parentFolderId:
                        newParentFolderId = tempTree.get("newFolderId")
                        log.tracef("---found the new parent: %d", newParentFolderId)
                        break
                
            newFolderId = self.sql.insertRecipeDataFolder(stepId, recipeDataKey, description, label, newParentFolderId)
            log.tracef("Inserted %s (%s) with new id: %s", recipeDataKey, path, str(newFolderId))
            
            log.tracef("  Inserted %s with new id: %s", recipeDataKey, str(folderId))
            tree["newFolderId"] = newFolderId
            newTrees.append(tree)

        log.tracef("Final Trees: %s", str(trees))
        self.trees = newTrees
    
    def findFolder(self, parent):
        log.tracef("Looking for parent: %s", parent)
        for tree in self.trees:
            log.tracef("...checking: %s", tree.get("path", ""))
            if tree.get("path", "") == parent:
                log.tracef("Found the parent id: %d", tree.get("newFolderId"))
                return tree.get("newFolderId")
        log.errorf("Error looking for path: <%s> in %s", parent, str(self.trees))
        return None
        

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
        
    def deleteChart(self, chartPath):
        SQL = "delete from SfcChart where ChartPath = '%s' " % chartPath
        rows = system.db.runUpdateQuery(SQL, tx=self.txId)
        log.tracef("...deleted %d rows from SfcChart...", rows)
        return rows
        
    def deleteChartFromHierarchy(self, chartPath):
        log.tracef("Deleting %s from the chart hierarchy", chartPath)
        SQL = "select chartId from sfcChart where chartPath = '%s' " % (chartPath)
        chartId = system.db.runScalarQuery(SQL, tx=self.txId)
        
        if chartId == None:
            log.tracef("...chart does not exist...")
            return
        
        SQL = "delete from sfcHierarchy where chartId = %d or childChartId = %d" % (chartId, chartId)
        rows = system.db.runUpdateQuery(SQL, tx=self.txId)
        log.tracef("Deleted %d rows from the sfcHierarchy for %s", rows, chartPath)
        
        SQL = "delete from sfcHierarchyHandler where chartId = %d or HandlerChartId = %d" % (chartId, chartId)
        rows = system.db.runUpdateQuery(SQL, tx=self.txId)
        log.tracef("Deleted %d rows from the sfcHierarchyHandler for %s", rows, chartPath)
        
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
    
    def getChartId(self, chartPath):
        SQL = "select chartId from sfcChart where chartpath = '%s' " % chartPath
        chartId = system.db.runScalarQuery(SQL, tx=self.txId) 
        return chartId
    
    def fetchParentInfo(self, childChartPath):
        parents = []
        SQL = "select chartPath, stepName from SfcHierarchyView where childChartPath = '%s' " % (childChartPath)
        pds = system.db.runQuery(SQL, tx=self.txId)
        for record in pds:
            parents.append( {"chartPath": record["chartPath"], "stepName": record["stepName"]} )
        return parents
    
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
        
        log.tracef("The step types are: %s", str(stepTypes))
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

    def insertHierarchy(self, parentChartPath, stepName, childChartPath):
        
        def getChartIdFromPath(chartPath, chartPDS):
            for chart in chartPDS:
                if chart["ChartPath"] == chartPath:
                    return chart["ChartId"]
            return -1
    
        log.tracef("Inserting parent: <%s> and child <%s> into chart hierarchy...", parentChartPath, childChartPath)
        parentChartId = getChartIdFromPath(parentChartPath, self.chartPDS)
        childChartId = getChartIdFromPath(childChartPath, self.chartPDS)
        SQL = "Select stepId from SfcStep where ChartId = %s and StepName = '%s'" % (str(parentChartId), stepName)
        stepId = system.db.runScalarQuery(SQL, tx=self.txId)
        
        SQL = "select count(*) from SfcHierarchy where StepId = %s and ChartId = %s and ChildChartId = %s" % (str(stepId), str(parentChartId), str(childChartId))
        cnt = system.db.runScalarQuery(SQL, tx=self.txId)
        if cnt == 0:
            log.tracef("---inserting---")
            SQL = "insert into SfcHierarchy (StepId, ChartId, ChildChartId) values (%s, %s, %s)" % (str(stepId), str(parentChartId), str(childChartId))
            system.db.runUpdateQuery(SQL, tx=self.txId)
        else:
            log.tracef("--- skipped because this already exists ---")
    
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
        
        SQL = "insert into SfcStep (StepUUID, StepName, StepTypeId, ChartId) values ('%s', '%s', %s, %s)" % (stepUUID, stepName, str(stepTypeId), str(chartId))
        stepId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
        log.infof("      ...inserted step with id: %d", stepId)
            
        return stepId
    
    def insertRecipeDataFolder(self, stepId, recipeDataKey, description, label, parentFolderId):
        log.infof("      Inserting recipe data folder:  %s with parent %d...", recipeDataKey, parentFolderId)
        if parentFolderId == None:
            SQL = "insert into SfcRecipeDataFolder (RecipeDataKey, StepId, Description, Label) values ('%s', %d, '%s', '%s')" % (recipeDataKey, stepId, description, label)
        else:
            SQL = "insert into SfcRecipeDataFolder (RecipeDataKey, StepId, Description, Label, ParentRecipeDataFolderId) "\
                " values ('%s', %d, '%s', '%s', %d)" % (recipeDataKey, stepId, description, label, parentFolderId)

        folderId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
        log.infof("      ...inserted folder with id: %d", folderId)
        return folderId
    
    def insertRecipeData(self, stepId, key, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId):
        log.infof("      Inserting recipe data key:  %s, a %s (%s - %s - %s - %s)...", key, recipeDataType, str(label), (description), str(advice), str(units))
        
        if label == None:
            label=""
        if description == None:
            description = ""
        if advice == None:
            advice = ""
        if units == None:
            units = ""
            
        if folderId == None:
            SQL = "insert into SfcRecipeData (StepID, RecipeDataKey, RecipeDataTypeId, Label, Description, Advice, Units) values (?, ?, ?, ?, ?, ?, ?)"
            args = [stepId, key, recipeDataTypeId, label, description, advice, units]
        else:
            SQL = "insert into SfcRecipeData (StepID, RecipeDataKey, RecipeDataTypeId, Label, Description, Advice, RecipeDataFolderId, Units) values (%d, '%s', %d, '%s', '%s', '%s', %d, '%s')" % \
                (stepId, key, recipeDataTypeId, label, description, advice, folderId, units)
        
        #recipeDataId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
        recipeDataId = system.db.runPrepUpdate(SQL, args, tx=self.txId, getKey=True)
        return recipeDataId
    
    def insertSimpleRecipeData(self, recipeDataId, valueType, valueTypeId, val):
        log.tracef("          Inserting a Simple Value: %s, a %s...", str(val), str(valueType))
        valueId = self.insertRecipeDataValue(recipeDataId, valueType, val)
        SQL = "insert into SfcRecipeDataSimpleValue (recipeDataId, valueTypeId, ValueId) values (?, ?, ?)"
        args = [recipeDataId, valueTypeId, valueId]
        system.db.runPrepUpdate(SQL, args, tx=self.txId)
    
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

    def insertMatrix(self, recipeDataId, valueType, valueTypeId, rows, columns, rowIndexKey, columnIndexKey):
        log.tracef("          Inserting a matrix...")
        
        if rowIndexKey == None:
            rowIndexKeyId = 'NULL'
        else:
            rowIndexKeyId = self.recipeDataArrayKeys.get(rowIndexKey, 'NULL')
    
        if columnIndexKey == None:
            columnIndexKeyId = 'NULL'
        else:
            columnIndexKeyId = self.recipeDataArrayKeys.get(columnIndexKey, 'NULL')
        
        SQL = "insert into SfcRecipeDataMatrix (recipeDataId, valueTypeId, rows, columns, rowIndexKeyId, columnIndexKeyId) values (%d, %d, %d, %d, %s, %s)" % (recipeDataId, valueTypeId, int(rows), int(columns), rowIndexKeyId, columnIndexKeyId)
        system.db.runUpdateQuery(SQL, tx=self.txId)
    
    def insertMatrixElement(self, recipeDataId, valueType, valueTypeId, rowIndex, columnIndex, val):
        log.tracef("          Inserting a matrix element...")
        valueId = self.insertRecipeDataValue(recipeDataId, valueType, val)
        SQL = "insert into SfcRecipeDataMatrixElement (recipeDataId, rowIndex, columnIndex, ValueId) values (%d, %d, %d, %d)" % (recipeDataId, int(rowIndex), int(columnIndex), valueId)
        system.db.runUpdateQuery(SQL, tx=self.txId)
        
    def insertSqcRecipeData(self, recipeDataId, lowLimit, targetValue, highLimit):
        log.tracef("          Inserting a SQC...")
        SQL = "insert into SfcRecipeDataSqc (recipeDataId, LowLimit, TargetValue, HighLimit) values (%d, %f, %f, %f)" % (recipeDataId, float(lowLimit), float(targetValue), float(highLimit))
        system.db.runUpdateQuery(SQL, tx=self.txId)
    
    def insertTimerRecipeData(self, recipeDataId):
        log.tracef("          Inserting a Timer...")
        SQL = "insert into SfcRecipeDataTimer (recipeDataId) values (?)"
        args = [recipeDataId]
        system.db.runPrepUpdate(SQL, args, tx=self.txId)
    
    def insertRecipeRecipeData(self, recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit):
        log.tracef("          Inserting a RECIPE recipe data...")
        SQL = "insert into SfcRecipeDataRecipe (recipeDataId, PresentationOrder, StoreTag, CompareTag, ModeAttribute, ModeValue, ChangeLevel, RecommendedValue, LowLimit, HighLimit) "\
            " values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        args = [recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit]
        system.db.runPrepUpdate(SQL, args, tx=self.txId)
    
    def insertRecipeDataValue(self, recipeDataId, valueType, val):
        log.tracef("        Inserting a recipe data value (type: %s, value: %s)...", valueType, val)
        
        if val in [None, 'None']:
            SQL = "insert into SfcRecipeDataValue (RecipeDataId, StringValue) values (?, NULL)"
            args = [recipeDataId]
        elif valueType == "String":
            SQL = "insert into SfcRecipeDataValue (RecipeDataId, StringValue) values (?, ?)"
            args = [recipeDataId, val]
        elif valueType == "Integer":
            SQL = "insert into SfcRecipeDataValue (RecipeDataId, IntegerValue) values (?, ?)"
            args = [recipeDataId, int(val)]
        elif valueType == "Float":
            SQL = "insert into SfcRecipeDataValue (RecipeDataId, FloatValue) values (?, ?)"
            args = [recipeDataId, float(val)]
        elif valueType == "Boolean":
            SQL = "insert into SfcRecipeDataValue (RecipeDataId, BooleanValue) values (?, ?)"
            args = [recipeDataId, val]
        
        #valueId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
        valueId = system.db.runPrepUpdate(SQL, args, tx=self.txId, getKey=True)
        return valueId