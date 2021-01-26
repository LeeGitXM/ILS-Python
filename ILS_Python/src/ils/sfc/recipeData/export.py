'''
Created on May 31, 2017

@author: phass
'''

import system, os, string
from ils.sfc.recipeData.hierarchyWithBrowser import fetchHierarchy, getChildren
from ils.common.config import getDatabaseClient
from ils.common.error import catchError, notifyError
log=system.util.getLogger(__name__)

def exportCallback(event):
    '''
    This is called by the button on the SFC recipe data browser. 
    '''
    try:
        db = getDatabaseClient()
        log.infof("In %s.exportCallback()...", __name__)
        treeWidget = event.source.parent.getComponent("Tree View")
        
        # First get the last node in the path
        chartPath = treeWidget.selectedPath
        log.tracef("The raw selected path is: <%s>", chartPath)
        chartPath = chartPath[chartPath.rfind("/")+1:]
        log.tracef("The selected chart path is <%s>", chartPath)
        
        # Now replace " / " with "/"
        chartPath = chartPath.replace(' \ ', '/')
        log.infof("The selected chart path is <%s>", chartPath)
        if chartPath == "" or chartPath == None:
            return
        
        rootContainer = event.source.parent.parent
        folder = rootContainer.importExportFolder
        filename = folder + "/recipeExport.xml"
        filename = system.file.saveFile(filename, "xml", "name of xml export file")
        if filename == None:
            return
        
        folder = os.path.dirname(filename)
        rootContainer.importExportFolder = folder
        
        deep = True
        exporter = Exporter(db)
        txt = exporter.export(chartPath, deep)
        
        system.file.writeFile(filename, txt, False)
        system.gui.messageBox("Chart and recipe were successfully exported!")
    except:
        notifyError("%s.exportCallback()" % (__name__), "Check the console log for details.")
        
class Exporter():
    sfcRecipeDataShowProductionOnly = False
    db = None
    hierarchyPDS = None
    chartPDS = None
    deep = None

    def __init__(self, db):
        self.db = db
        
        self.hierarchyPDS = fetchHierarchy("%", self.sfcRecipeDataShowProductionOnly, self.db)
        log.tracef("Selected all %d chart hierarchy records...", len(self.hierarchyPDS))
        
        self.chartPDS = system.db.runQuery("Select ChartId, ChartPath from SfcChart order by ChartId", self.db)
        log.tracef("Selected info for all %d charts...", len(self.chartPDS))
        
        SQL = "Select * from SfcRecipeDataFolder"
        self.folderPDS = system.db.runQuery(SQL, self.db)

    def export(self, chartPath, deep):
        self.chartPath = chartPath
        self.deep = deep
        log.infof("In %s.export()", __name__)
        
        SQL = "select chartId from SfcChart where chartPath = '%s'" % (self.chartPath)
        self.chartId = system.db.runScalarQuery(SQL, self.db) 
        log.tracef("...fetched chart id: %s", str(self.chartId))
        if self.chartId == None:
            return ""

        ''' Export any keys that are used by keyed arrays or matrices. '''
        keyTxt = self.exportKeysForTree()
        
        ''' Export the tree (Charts, steps, and recipe data) '''
        txt, structureTxt = self.exportTree()

        txt = "<data>\n" + keyTxt + txt + structureTxt + "</data>"
        return txt
    

    def exportKeysForTree(self):
        log.tracef("=====================================")
        log.tracef("Exporting recipe data keys...")
        log.tracef("=====================================")
        
        chartIds = [self.chartId]
        newKids = True
    
        while self.deep and newKids:
            newKids = False
            for chartId in chartIds:
                newChildren, aList = self.fetchChildren(chartId, chartIds, [])
                if len(newChildren) > 0:
                    log.tracef("Found that %d had new kids: %s", chartId, str(newChildren))
                    newKids = True
                    chartIds = chartIds + newChildren
        
        log.tracef("The chart ids are: %s", str(chartIds))
        
        log.tracef("--- Exporting Matrix and Array Keys ---")
        txt = ""
        keys = []
        for chartId in chartIds:
            SQL = "select RecipeDataId from SfcRecipeDataView where chartId = %d and RecipeDataType = 'Matrix'" % (chartId)
            pds = system.db.runQuery(SQL, self.db)
            
            for record in pds:
                log.tracef("Found matrix id: %s", str(record["RecipeDataId"]))
                SQL = "select RowIndexKeyId, ColumnIndexKeyId from SfcRecipeDataMatrix where RecipeDataId = %d" % (record["RecipeDataId"])
                keyPds = system.db.runQuery(SQL, self.db)
                for record in keyPds:
                    if record["RowIndexKeyId"] != None and record["RowIndexKeyId"] not in keys:
                        log.tracef("Found a new Matrix row key: %s", str(record["RowIndexKeyId"]))
                        keys.append(record["RowIndexKeyId"])
                    if record["ColumnIndexKeyId"] != None and record["ColumnIndexKeyId"] not in keys:
                        log.tracef("Found a new matrix column key: %s", str(record["ColumnIndexKeyId"]))
                        keys.append(record["ColumnIndexKeyId"])
            
            SQL = "select RecipeDataId from SfcRecipeDataView where chartId = %d and RecipeDataType = 'Array'" % (chartId)
            pds = system.db.runQuery(SQL, self.db)
            
            for record in pds:
                log.tracef("Found array id: %s", str(record["RecipeDataId"]))
                SQL = "select IndexKeyId from SfcRecipeDataArray where RecipeDataId = %d and IndexKeyId is not null" % (record["RecipeDataId"])
                keyPds = system.db.runQuery(SQL, self.db)
                for record in keyPds:
                    if record["IndexKeyId"] not in keys:
                        log.tracef("Found a new Array key: %s", str(record["IndexKeyId"]))
                        keys.append(record["IndexKeyId"])
            
    #        txt = txt + exportKeysForChart(chartId, db)
        log.tracef("The referenced keys are: %s", str(keys))
        
        cnt = 0
        for key in keys:
            SQL = "select * from SfcRecipeDataKeyView where KeyId = %d order by KeyIndex" % (key)
            pds = system.db.runQuery(SQL, self.db)
            row = 1
            for record in pds:
                if row == 1:
                    txt = txt + "<key name='%s'>\n" % (record["KeyName"])
                txt = txt + "<element value='%s' index='%d'/>\n" % (record["KeyValue"], record["KeyIndex"])
                row = row + 1
                cnt = cnt + 1
            txt = txt + "</key>\n"
        
        log.tracef("The key XML is: %s", txt)
        log.infof("Exported %d array keys", cnt)
        return txt

    def exportTree(self):
        log.tracef("===========================================================================")
        log.tracef("Exporting steps and recipe data for chart hierarchy rooted at %s (Id: %d)", self.chartPath, self.chartId)
        log.tracef("===========================================================================")
        
        chartIds = [self.chartId]
        parentChildList = []
        newKids = True
        
        while self.deep and newKids:
            newKids = False
            for chartId in chartIds:
                newChildren, parents = self.fetchChildren(chartId, chartIds, parentChildList)
                if len(newChildren) > 0:
                    log.tracef("Found that %d had new kids: %s", chartId, str(newChildren))
                    newKids = True
                    chartIds = chartIds + newChildren
    
        log.tracef("The chart ids that will be exported are: %s", str(chartIds))
        
        txt = ""
        
        for chartId in chartIds:
            txt = txt + self.exportChart(chartId)
        
        hierarchyXML = ""
        for record in parentChildList:
            parentChartPath = self.getChartPathFromPDS(record["parent"])
            childChartPath = self.getChartPathFromPDS(record["child"])
            hierarchyXML = hierarchyXML + "<parentChild parent=\"%s\" child=\"%s\" stepName=\"%s\" />\n" % (parentChartPath, childChartPath, record["stepName"])
    
        return txt, hierarchyXML

    def getChartPathFromPDS(self, chartId):
        for chart in self.chartPDS:
            if chart["ChartId"] == chartId:
                return chart["ChartPath"]
        return ""


    def fetchChildren(self, chartId, visitedCharts, parentChildList):
        log.tracef("Looking for the children of chart %d", chartId)
        
        children = []
        hierarchyXML = ""
        log.tracef("Getting the children of chart: %s", str(chartId))
        for record in self.hierarchyPDS:
            if record["ChartId"] == chartId and record["ChildChartId"] not in children:
                d = {"parent":record["ChartId"], "child": record["ChildChartId"], "stepName": record["StepName"], "parentChartPath": record["ChartPath"], "childChartPath": record["ChildChartPath"]}
                if d not in parentChildList:
                    parentChildList.append(d)
                children.append(record["ChildChartId"])
        log.tracef("The children of %s are %s", chartId, str(children))
    
        newChildren = []
        for child in children:
            if child not in visitedCharts:
                log.tracef("Found a new child: %d", child)
                newChildren.append(child)
                
        return newChildren, parentChildList
    
    
    def exportChart(self, chartId):
        chartPath = self.findChartPathFromId(chartId)
        log.infof("Exporting chart %s (%s)", chartPath, str(chartId))
        
        stepTxt = self.exportChartSteps(chartId, chartPath)
        
        txt = "<chart chartId=\"%d\" chartPath=\"%s\" >\n" % (chartId, chartPath)
        txt = txt + stepTxt
        txt = txt + "</chart>\n\n"
        
        return txt


    def exportChartSteps(self, chartId, chartPath):
        log.infof("...exporting chart steps...")
        
        SQL = "select stepId, stepName, stepUUID, stepType from SfcStepView where chartId = %d" % (chartId)
        pds = system.db.runQuery(SQL, self.db)
        
        stepTxt = ""
        
        for record in pds:
            stepId = record["stepId"]
            stepName = record["stepName"]
            recipeFolderTxt = self.exportRecipeDataFoldersForStep(stepId, stepName)
            recipeDataTxt = self.exportRecipeDataForStep(stepId, stepName)
            stepTxt = stepTxt + "<step stepName='%s' stepType='%s' stepUUID='%s' >\n" % (record["stepName"], record["stepType"], record["stepUUID"])
            stepTxt = stepTxt + recipeFolderTxt + recipeDataTxt
            stepTxt = stepTxt + "</step>\n\n"
        
        return stepTxt

    def exportRecipeDataFoldersForStep(self, stepId, stepName):
        log.infof("   ...exporting recipe data folders for step %s - %s", stepName, str(stepId))
        txt = ""
    
        SQL = "Select RecipeDataKey, RecipeDataFolderId, ParentRecipeDataFolderId, Description, Label from SfcRecipeDataFolder where stepId = %d" % (stepId)
        pds = system.db.runQuery(SQL, self.db)
        
        for record in pds:
            txt = txt + "<recipeFolder recipeDataKey='%s' folderId='%s' parentFolderId='%s' description='%s' label='%s'/>\n" % \
                (record["RecipeDataKey"], record["RecipeDataFolderId"], record["ParentRecipeDataFolderId"], record["Description"], record["Label"])
    
        return txt

    def exportRecipeDataForStep(self, stepId, stepName):
        log.infof("   ...exporting recipe data for step %s - %s", stepName, str(stepId))
        
        def fetchFirstRecord(SQL):
            pds = system.db.runQuery(SQL, self.db)
            record = pds[0]
            return record
        
        SQL = "select chartPath, stepName, recipeDataId, recipeDataKey, recipeDataType, label, description, advice, units, recipeDataFolderId from SfcRecipeDataView where stepId = %d" % (stepId)
        pds = system.db.runQuery(SQL, self.db)
        
        recipeDataTxt = ""
        
        for record in pds:
            chartPath = record["chartPath"]
            stepName = record["stepName"]
            recipeDataId = record["recipeDataId"]
            recipeDataType = record["recipeDataType"]
            recipeDataKey = record["recipeDataKey"]
            folderId = record["recipeDataFolderId"]
            
            label = record["label"]
            if label == None or string.upper(str(label)) == 'NONE':
                label = ''
                
            description = record["description"]
            if description == None and string.upper(str(description)) == 'NONE':
                description = ''
            
            advice = record['advice']
            if advice == None or string.upper(str(advice)) == 'NONE':
                advice = ''
            
            parentFolder = self.findParent(folderId)
            log.tracef("      ...processing recipe data %s - %s - %d (%s - %s)", recipeDataKey, recipeDataType, recipeDataId, chartPath, stepName)
            
            baseTxt = "<recipe recipeDataKey='%s' recipeDataType='%s' label='%s' description='%s' advice='%s' units='%s' parent='%s'" % \
                (recipeDataKey, recipeDataType, label, description, advice, record["units"], parentFolder)
            
            if recipeDataType == "Simple Value":
                SQL = "select valueType, floatValue, integerValue, stringValue, booleanValue from SfcRecipeDataSimpleValueView where RecipeDataId = %d" % (recipeDataId)
                record = fetchFirstRecord(SQL)
                valueType = record["valueType"]
                if valueType == "Float":
                    recipeDataTxt = recipeDataTxt + baseTxt + " valueType='%s' value='%s' />" % (valueType, str(record['floatValue']))
                elif valueType == "Integer":
                    recipeDataTxt = recipeDataTxt + baseTxt + " valueType='%s' value='%s' />" % (valueType, str(record['integerValue']))
                elif valueType == "String":
                    recipeDataTxt = recipeDataTxt + baseTxt + " valueType='%s' value='%s' />" % (valueType, str(record['stringValue']))
                elif valueType == "Boolean":
                    recipeDataTxt = recipeDataTxt + baseTxt + " valueType='%s' value='%s' />" % (valueType, str(record['booleanValue']))
                else:
                    log.errorf("****** Unknown simple value data type: %s", valueType)
    
            elif recipeDataType == "Recipe":
                SQL = "select presentationOrder, storeTag, compareTag, ModeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit from SfcRecipeDataRecipeView where RecipeDataId = %d" % (recipeDataId)
                record = fetchFirstRecord(SQL)
                recipeDataTxt = recipeDataTxt + baseTxt + " presentationOrder='%s' storeTag='%s' compareTag='%s' modeAttribute='%s' modeValue='%s' changeLevel='%s' recommendedValue='%s' lowLimit='%s' highLimit='%s' />" %\
                    (str(record['presentationOrder']), str(record['storeTag']), str(record['compareTag']), str(record['ModeAttribute']), str(record['modeValue']),\
                     str(record['changeLevel']), str(record['recommendedValue']), str(record['lowLimit']), str(record['highLimit']))
                    
            elif recipeDataType == "SQC":
                SQL = "select lowLimit, targetValue, highLimit from SfcRecipeDataSQCView where RecipeDataId = %d" % (recipeDataId)
                record = fetchFirstRecord(SQL)
                recipeDataTxt = recipeDataTxt + baseTxt + " lowLimit='%s' targetValue='%s' highLimit='%s'  />" %\
                    (str(record['lowLimit']), str(record['targetValue']), str(record['highLimit']) )
    
            elif recipeDataType == "Timer":
                '''
                All of the other properties for a Timer are transient and get set at runtime.
                '''
                recipeDataTxt = recipeDataTxt + baseTxt + " />"
    
            elif recipeDataType == "Output":
                SQL = "select tag, valueType, outputType, download, timing, maxTiming, writeConfirm, outputFloatValue, outputIntegerValue, outputStringValue, outputBooleanValue "\
                    " from SfcRecipeDataOutputView where RecipeDataId = %d" % (recipeDataId)
                record = fetchFirstRecord(SQL)
                
                valueType = record["valueType"]
                if valueType == "Float":
                    val = str(record['outputFloatValue'])
                elif valueType == "Integer":
                    val = str(record['outputIntegerValue'])
                elif valueType == "String":
                    val = str(record['outputStringValue'])
                elif valueType == "Boolean":
                    val = str(record['outputBooleanValue'])
                else:
                    log.errorf("****** Unknown output value data type: %s", valueType)
                    
                recipeDataTxt = recipeDataTxt + baseTxt + " tag='%s' valueType='%s' outputType='%s' download='%s' timing='%s' maxTiming='%s' writeConfirm='%s' value='%s' />" %\
                    (str(record['tag']), str(record['valueType']), str(record['outputType']), str(record['download']), str(record['timing']), str(record['maxTiming']), \
                     str(record['writeConfirm']), val )
    
            elif recipeDataType == "Output Ramp":
                SQL = "select tag, valueType, outputType, download, timing, maxTiming, writeConfirm, outputFloatValue, outputIntegerValue, outputStringValue, outputBooleanValue, "\
                    " rampTimeMinutes, updateFrequencySeconds "\
                    " from SfcRecipeDataOutputRampView where RecipeDataId = %d" % (recipeDataId)
                record = fetchFirstRecord(SQL)
                
                valueType = record["valueType"]
                if valueType == "Float":
                    val = str(record['outputFloatValue'])
                elif valueType == "Integer":
                    val = str(record['outputIntegerValue'])
                elif valueType == "String":
                    val = str(record['outputStringValue'])
                elif valueType == "Boolean":
                    val = str(record['outputBooleanValue'])
                else:
                    log.errorf("****** Unknown output value data type: %s", valueType)
                    
                recipeDataTxt = recipeDataTxt + baseTxt + " tag='%s' valueType='%s' outputType='%s' download='%s' timing='%s' maxTiming='%s' writeConfirm='%s' value='%s' "\
                    " rampTimeMinutes='%s' updateFrequencySeconds='%s' />" %\
                    (str(record['tag']), str(record['valueType']), str(record['outputType']), str(record['download']), str(record['timing']), str(record['maxTiming']), \
                    str(record['writeConfirm']), val, str(record['rampTimeMinutes']), str(record['updateFrequencySeconds']) )
    
            elif recipeDataType == "Input":
                SQL = "select tag, valueType from SfcRecipeDataInputView where RecipeDataId = %d" % (recipeDataId)
                record = fetchFirstRecord(SQL)
                recipeDataTxt = recipeDataTxt + baseTxt + " tag='%s' valueType='%s' />" %\
                    (str(record['tag']), str(record['valueType']))
            
            elif recipeDataType == "Array":
                SQL = "select valueType, keyName from SfcRecipeDataArrayView where RecipeDataId = %d" % (recipeDataId)
                record = fetchFirstRecord(SQL)
                valueType = record["valueType"]
                indexKey = record["keyName"]
                recipeDataTxt = recipeDataTxt + baseTxt + " valueType='%s' indexKey='%s' >" % (valueType, indexKey)
                
                '''
                The indexKey is just another array - hopefully it is in the same scope as this.  The order of export/import doesn't matter because the array data is still stored the same, 
                the index key is only used as a convenience in the UI and API.
                '''
                SQL = "select arrayIndex, floatValue, integerValue, stringValue, booleanValue from SfcRecipeDataArrayElementView where RecipeDataId = %d" % (recipeDataId)
                pds = system.db.runQuery(SQL, self.db)
                for record in pds:
                    if valueType == "Float":
                        recipeDataTxt = recipeDataTxt + "<element arrayIndex='%d' value='%s'/>\n" % (record["arrayIndex"], str(record['floatValue']))
                    elif valueType == "Integer":
                        recipeDataTxt = recipeDataTxt + "<element arrayIndex='%d' value='%s'/>\n" % (record["arrayIndex"], str(record['integerValue']))
                    elif valueType == "String":
                        recipeDataTxt = recipeDataTxt + "<element arrayIndex='%d' value='%s'/>\n" % (record["arrayIndex"], str(record['stringValue']))
                    elif valueType == "Boolean":
                        recipeDataTxt = recipeDataTxt + "<element arrayIndex='%d' value='%s'/>\n" % (record["arrayIndex"], str(record['booleanValue']))
                    else:
                        log.errorf("****** Unknown array value data type: %s", valueType)
    
                recipeDataTxt = recipeDataTxt + "</recipe>\n"
    
            elif recipeDataType == "Matrix":
                SQL = "select valueType, rows, columns, rowIndexKeyName, columnIndexKeyName from SfcRecipeDataMatrixView where RecipeDataId = %d" % (recipeDataId)
                record = fetchFirstRecord(SQL)
                valueType = record["valueType"]
                recipeDataTxt = recipeDataTxt + baseTxt + " valueType='%s' rows='%d' columns='%d' rowIndexKey='%s' columnIndexKey='%s' >" % \
                    (valueType, record["rows"], record["columns"], record["rowIndexKeyName"], record["columnIndexKeyName"])
                
                '''
                The index is just another array.  The order of export/import doesn't matter because the array data is still stored the same, 
                the index key is only used as a convenience in the UI and API.
                '''
                SQL = "select rowIndex, columnIndex, floatValue, integerValue, stringValue, booleanValue from SfcRecipeDataMatrixElementView where RecipeDataId = %d" % (recipeDataId)
                pds = system.db.runQuery(SQL, self.db)
                for record in pds:
                    if valueType == "Float":
                        recipeDataTxt = recipeDataTxt + "<element rowIndex='%d' columnIndex='%d' value='%s'/>\n" % (record["rowIndex"], record["columnIndex"], str(record['floatValue']))
                    elif valueType == "Integer":
                        recipeDataTxt = recipeDataTxt + "<element rowIndex='%d' columnIndex='%d' value='%s'/>\n" % (record["rowIndex"], record["columnIndex"], str(record['integerValue']))
                    elif valueType == "String":
                        recipeDataTxt = recipeDataTxt + "<element rowIndex='%d' columnIndex='%d' value='%s'/>\n" % (record["rowIndex"], record["columnIndex"], str(record['stringValue']))
                    elif valueType == "Boolean":
                        recipeDataTxt = recipeDataTxt + "<element rowIndex='%d' columnIndex='%d' value='%s'/>\n" % (record["rowIndex"], record["columnIndex"], str(record['booleanValue']))
                    else:
                        log.errorf("****** Unknown array value data type: %s", valueType)
    
                recipeDataTxt = recipeDataTxt + "</recipe>\n"
                            
            else:
                log.errorf("***** Unsupported recipe data type: %s", recipeDataType)
        
        return recipeDataTxt

    def findParent(self, folderId):
        '''
        Given a specific folder, and a dataset of the entire folder hierarchy, find the full path for a given folder.
        '''
        if folderId == "":
            return ""
        
        log.tracef("------------------")
        path = ""
        log.tracef("Finding the path for folder %d", folderId)
        
        while folderId != None:
            
            for record in self.folderPDS:
                if record["RecipeDataFolderId"] == folderId:
                    log.tracef("...found the parent")
                    if path == "":
                        path = record["RecipeDataKey"]
                    else:
                        path = "%s/%s" % (record["RecipeDataKey"], path)
                    folderId = record["ParentRecipeDataFolderId"]
                    log.tracef("...the new parent id is: %s", str(folderId))
    
        log.tracef("The path is: %s", path)
        return path

    def findChartPathFromId(self, chartId):
        '''
        Given a specific chart id, and a dataset of the every chart, find the chart path for a given id.
        '''
        for record in self.chartPDS:
            if record["ChartId"] == chartId:
                return record["ChartPath"]
    
        log.errorf("Error in findChartPathFromId(), Unable to find chart id: %d in the chart dataset", chartId)
        return "NOT FOUND"