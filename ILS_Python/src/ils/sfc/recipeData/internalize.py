'''
Created on Jul 23, 2019

@author: phass

A lot of this code was copied and modified from ils.sfc.recipeData.export.py.
I didn't want to modify that code and possibly break it.  Also that module will eventually be obsolete so I 
didn't want any dependencies on it.
'''

import system, os, string
import xml.etree.ElementTree as ET
from ils.sfc.recipeData.hierarchyWithBrowser import fetchHierarchy, getChildren
from ils.common.config import getDatabaseClient
from ils.common.error import catchError, notifyError
from ils.common.util import escapeJSON

log=system.util.getLogger("com.ils.sfc.recipeData.internalize")

# Use this to limit the scope during testing
WHERE = "where chartId >= 769 and chartId <= 773 or chartId = 801 or chartId = 805"
WHERE = "where chartId = 805 or chartId = 801 "
WHERE = "where chartId > 800 "
AND_WHERE = " and chartId > 800 "
WHERE = ""
AND_WHERE = ""

'''
This is called from the Tools menu and the designer hook
'''
def internalize(chartPath, chartXML):
    log.infof("***************  PYTHON  *******************")
    log.infof("In %s.internalize() for chart: %s", __name__, chartPath)
    log.tracef("The initial chart XML is: %s", chartXML)
    db = getDatabaseClient()
    chartInfo, chartPaths, folderInfo = getChartInfo(db)
    chartXML = internalizeRecipeDataForChart(chartPath, chartXML, chartPaths, chartInfo, folderInfo, db)
    
    return chartXML

'''
This is meant to be called from a Vision window for debugging and simulates the call from the Tools menu and the designer hook
'''
def internalizeCallback(chartPath, chartXML):
    log.infof("In %s.internalizeCallback() with %s", __name__, chartPath)
    
    db = getDatabaseClient()
    chartInfo, chartPaths, folderInfo = getChartInfo(db)
    chartXML = internalizeRecipeDataForChart(chartPath, chartXML, chartPaths, chartInfo, folderInfo, db)
    return chartXML

def getChartInfo(db):
    chartInfoTimestamp = system.util.getGlobals().get("ChartInfoTimestamp", None)
    
    if chartInfoTimestamp == None or abs(system.date.secondsBetween(system.date.now(), chartInfoTimestamp)) > 60:
        ''' Refresh the chart info '''
        log.info("Refreshing the chart info...")
        chartInfo, chartPaths = fetchChartInfo(db)
        chartInfo, folderInfo = fetchAllRecipeData(chartInfo, db)
        system.util.getGlobals()["ChartInfoTimestamp"] = system.date.now()
        system.util.getGlobals()["ChartInfo"] = chartInfo
        system.util.getGlobals()["FolderInfo"] = folderInfo
        system.util.getGlobals()["ChartPaths"] = chartPaths
    else:
        log.infof("Using stored chart info...")
        chartInfo = system.util.getGlobals()["ChartInfo"]
        folderInfo = system.util.getGlobals()["FolderInfo"]
        chartPaths = system.util.getGlobals()["ChartPaths"]
        
    return chartInfo, chartPaths, folderInfo

def fetchChartInfo(db):
    chartInfo = {}
    chartPaths = {}
    
    '''
    Fetch a record for each chart and make a dictionary entry for each chart with the chartPath as the key
    '''
    log.tracef("Fetching chart paths...")
    
    if WHERE <> "":
        print "*******************************"
        print "*  LIMITING SFCCHART QUERY TO %s", WHERE
        print "*******************************"
    SQL = "select ChartPath, ChartId from SfcChart " + WHERE
    pds = system.db.runQuery(SQL, db)
    log.tracef("...fetched %d records!", len(pds))
    for record in pds:
        chartPath = record["ChartPath"]
        chartId = record["ChartId"]
        chartInfo[chartId] = {"chartPath": chartPath, "stepInfo": {}}
        
        chartPaths[chartPath] = chartId
    
    log.tracef("Chart Paths: %s", str(chartPaths))
    
    SQL = "select ChartId, StepId, StepName from SfcStep " + WHERE + " order by ChartId, StepId "
    log.tracef("Fetching chart info...")
    pds = system.db.runQuery(SQL, db)
    log.tracef("...fetched %d records!", len(pds))
    for record in pds:
        chartId = record["ChartId"]
        stepId = record["StepId"]
        stepName = record["StepName"]
        
        chartDict = chartInfo[chartId]
        stepInfo = chartDict["stepInfo"]
        stepInfo[stepName] = {"stepId": stepId, "recipeData": []}
        chartDict["stepInfo"] = stepInfo
        chartInfo[chartId] = chartDict
        
    log.tracef("Chart Info: %s", str(chartInfo))
    
    return chartInfo, chartPaths


def fetchAllRecipeData(chartInfo, db):
    
    def fetchFolderInfo(db):
        folderInfo = {}
        SQL = "select * from SfcRecipeDataFolderView " + WHERE
        pds = system.db.runQuery(SQL, db)
        
        processedIds = []
        skipped = False
        i = 0
        while (i == 0 or skipped) and i < 10:
            skipped = False
            i = i + 1
            for record in pds:
                folderId = record["RecipeDataFolderId"]
                parentId = record['ParentRecipeDataFolderId']
                folderKey = record['RecipeDataKey']
                
                if parentId in [None]:
                    folderInfo[folderId] = {"key":folderKey, "path":folderKey}
                    processedIds.append(folderId)
                else:
                    parentDict = folderInfo.get(parentId, None)
                    if parentDict == None:
                        skipped = True
                    else:
                        path = parentDict.get("path", "") + "/" + folderKey
                        folderInfo[folderId] = {"key": folderKey, "path": path}
                        processedIds.append(folderId)
                    skipped = True

        log.tracef("Folder Info: %s", str(folderInfo))
        return folderInfo
             
    
    def updateChartInfo(chartInfo, chartId, stepName, record):
        log.tracef("Updating chart recipe data for chart %d, step %s - %s", chartId, stepName, record)
        chartDict = chartInfo[chartId]
        #print "Chart Dictionary: ", chartDict
        stepInfo = chartDict["stepInfo"]
        #print "Step Info (before): ", stepInfo
        step = stepInfo[stepName]
        
        recipeData = step["recipeData"]
        recipeData.append(record)
        #print "The recipe data list is: ", str(recipeData)
        
        step["recipeData"] = recipeData
        stepInfo[stepName] = step
        #print "Step Info (after): ", stepInfo
        chartDict["stepInfo"] = stepInfo
        log.tracef("  updated step info: %s", str(stepInfo))
        return chartInfo
    
    def fetcher(chartInfo, folderInfo, SQL, recipeType, db):    
        pds = system.db.runQuery(SQL, db)
        log.infof("...processing %d %s recipe data entities...", len(pds), recipeType)
    
        for record in pds:
            chartId = record["ChartId"]
            stepName = record["StepName"]
            chartInfo = updateChartInfo(chartInfo, chartId, stepName, record)

        return chartInfo

    log.infof("=====================================")
    log.infof("Fetching ALL data")
    log.infof("=====================================")
    folderInfo = fetchFolderInfo(db)
    log.tracef("ChartInfo (before): %s", str(chartInfo))
    chartInfo = fetcher(chartInfo, folderInfo, "select * from SfcRecipeDataArrayView " + WHERE, "array", db)
    chartInfo = fetcher(chartInfo, folderInfo, "select * from SfcRecipeDataFolderView " + WHERE, "folder", db)
    chartInfo = fetcher(chartInfo, folderInfo, "select * from SfcRecipeDataInputView " + WHERE, "input", db)
    chartInfo = fetcher(chartInfo, folderInfo, "select * from SfcRecipeDataMatrixView " + WHERE, "matrix", db)
    chartInfo = fetcher(chartInfo, folderInfo, "select * from sfcRecipeDataOutputRampView " + WHERE, "outputRamp", db)
    chartInfo = fetcher(chartInfo, folderInfo, "select * from sfcRecipeDataOutputView where RecipeDataType = 'Output' " + AND_WHERE, "output", db)
    chartInfo = fetcher(chartInfo, folderInfo, "select * from SfcRecipeDataRecipeView " + WHERE, "recipe", db)
    chartInfo = fetcher(chartInfo, folderInfo, "select * from sfcRecipeDataSimpleValueView " + WHERE, "simple value", db)
    chartInfo = fetcher(chartInfo, folderInfo, "select * from sfcRecipeDataSQCView " + WHERE, "SQC", db)
    chartInfo = fetcher(chartInfo, folderInfo, "select * from sfcRecipeDataTimerView " + WHERE, "Timer", db)
    
    log.tracef("ChartInfo (after embedding recipe data): %s", str(chartInfo))
    
    return chartInfo, folderInfo

def internalizeRecipeDataForChart(chartPath, chartXML, chartPaths, chartInfo, folderInfo, db):
    '''
    Insert the recipe data into the associated-data slot for each step.  The chart XML is in XML, which is basically text.
    If I use XML tools to insert the recipe data into the chart XML then A) I have less control, and B) ET inserts all sort of 
    escape characters making it harder to read, which is the whole point of using XML.  So I am going to use text string
    manipulation to add things in. 
    '''
    
    #---------------------------------------------------
    def splitChartXML(chartXML):
        '''
        Split the XML for a chart into 3 parts: the preamble, the postamble, and the middle - which contains the steps.
        This makes it easy to put back together at the end.  We are going to insert recipe data into the steps part, but the pre and 
        post parts remain unchanged.
        '''
        log.tracef("------------------ SPLITTING XML ---------------------")
        steps =  []
        start = chartXML.find("<step")
        end = chartXML.rfind("</step>") + 7
        preamble = chartXML[:start]
        middle = chartXML[start:end]
        postamble = chartXML[end:]

        while len(middle) > 0:
            stepStart = middle.find("<step")
            stepEnd = middle.find("</step>") + 7
            stepTxt = middle[stepStart:stepEnd]
            log.tracef("")
            log.tracef("Step: %s", stepTxt)
            log.tracef("")
            associatedDataStart = stepTxt.find("<associated-data>")
            associatedDataEnd = stepTxt.rfind("</associated-data>") + 18
            
            if associatedDataStart > 0 and associatedDataEnd > 0:
                stepTxt = stepTxt[:associatedDataStart] + stepTxt[associatedDataEnd:]
                log.tracef("Step AFTER removing old associated data: %s", stepTxt)
    
            steps.append(stepTxt)
            middle = middle[stepEnd:]
        
        log.tracef("----------------------------------------------------------")
        return preamble, postamble, steps
    #----------------------------------------------------
    
    log.infof("=====================================")
    log.infof("Processing recipe data for chart: %s", chartPath)
    log.infof("=====================================")
    
    log.tracef("Chart Info: %s", str(chartInfo))
    
    chartId = chartPaths[chartPath]
    log.tracef("The chart Id is: %d", chartId)
    
    chartDict = chartInfo[chartId]
    log.tracef("The chart dictionary is: %s", str(chartDict))
    
    stepInfo = chartDict['stepInfo']
    log.tracef("The step info is: %s", str(stepInfo))
    
    preamble, postamble, steps = splitChartXML(chartXML)

    chartXML = preamble
    for step in steps:
        log.tracef(" ")
        log.tracef("Processing: %s", str(step))

        stepName = step[step.find("name=")+6:]
        stepName = stepName[:stepName.find("\"")]
        log.tracef("  StepName: <%s>", stepName)
        log.tracef("  Looking for recipe data for step: <%s>", stepName)
        stepDict = stepInfo.get(stepName, None)
        log.tracef("  Step Dictionary: %s", str(stepDict))
        recipeDataList = stepDict.get("recipeData", [])
        log.tracef("  Recipe data for Step: %s", str(recipeDataList))

        recipe = []
        for record in recipeDataList:
            log.tracef("           Inserting the recipe data...")
            
            recipeDataType = record["RecipeDataType"]
            if recipeDataType == "Folder":                
                recipeDataKey = record["RecipeDataKey"]
                log.infof("      ...processing FOLDER recipe data %s...", recipeDataKey)
                
                ''' For a folder, I want the path of the parent '''
                folderId = record["ParentRecipeDataFolderId"]
                log.tracef("Parent Recipe Data Folder Id: %s", str(folderId))
                
                if folderId in [None, "null", "None"]:
                    path = None
                else:
                    path = folderInfo.get(folderId).get("path")
                    
                rd = {}
                rd["recipeDataKey"] = recipeDataKey
                rd["recipeDataType"] = recipeDataType
                rd["label"] = escapeJSON(record["Label"])
                rd["description"] = escapeJSON(record["Description"])
                rd["path"] = path

            else:
                recipeDataId = record["RecipeDataId"]
                recipeDataKey = record["RecipeDataKey"]
                log.infof("      ...processing a <%s> recipe data with key: %s - %d (%s - %s)", recipeDataType, recipeDataKey, recipeDataId, chartPath, stepName)
                
                rd = {}
                rd["recipeDataKey"] = recipeDataKey
                rd["recipeDataType"] = recipeDataType
                rd["label"] = escapeJSON(record["Label"])
                rd["description"] = escapeJSON(record["Description"])
                rd["units"] = record["Units"]
                
                folderKey = record["FolderKey"]
                if folderKey in [None, "null"]:
                    rd["path"] = None
                else:
                    folderId = record["FolderId"]
                    path = folderInfo.get(folderId).get("path")
                    rd["path"] = path
                
                if recipeDataType == "Simple Value":
                    valueType = record["ValueType"]
                    rd["valueType"] = valueType
                    
                    if valueType == "Float":
                        rd["value"] = str(record['FloatValue'])
                    elif valueType == "Integer":
                        rd["value"] =str(record['IntegerValue'])
                    elif valueType == "String":
                        rd["value"] = escapeJSON(str(record['StringValue']))
                    elif valueType == "Boolean":
                        rd["value"] =str(record['BooleanValue'])
                    else:
                        log.errorf("****** Unknown simple value data type: %s", valueType)
                        rd["value"] = "Unknown value type: %s" % (valueType)
        
                elif recipeDataType == 'Array':
                    valueType = record["ValueType"]
                    rd["valueType"] = valueType
                    rd["indexKey"] = record["KeyName"]
                    
                    '''
                    The indexKey is just another array - hopefully it is in the same scope as this.  The order of export/import doesn't matter because the array data is still stored the same, 
                    the index key is only used as a convenience in the UI and API.
                    '''
                    SQL = "select arrayIndex, floatValue, integerValue, stringValue, booleanValue from SfcRecipeDataArrayElementView where RecipeDataId = %d" % (recipeDataId)
                    pds = system.db.runQuery(SQL, db)
                    
                    vals = []
                    for record in pds:
                        if valueType == "Float":
                            vals.append(record['floatValue'])
                        elif valueType == "Integer":
                            vals.append(record['integerValue'])
                        elif valueType == "String":
                            vals.append(record['stringValue'])
                        elif valueType == "Boolean":
                            vals.append(record['booleanValue'])
                        else:
                            log.errorf("****** Unknown array value data type: %s", valueType)
                            
                    rd["vals"] = vals
                    
                elif recipeDataType == "Input":
                    valueType = record["ValueType"]
                    rd["valueType"] = valueType                
                    rd["tag"] = str(record['Tag'])
        
                elif recipeDataType == "Matrix":
                    valueType = record["ValueType"]
                    rd["valueType"] = valueType
                    rd["rows"] = record["Rows"]
                    rd["columns"] = record["Columns"]
                    rd["rowIndexKey"] = record["RowIndexKeyName"]
                    rd["columnIndexKey"] = record["ColumnIndexKeyName"]
                    
                    '''
                    The index is just a string array (NOT RECIPE DATA).  Hopefully the array key will already exist on the target system.  The order of export/import doesn't matter because 
                    the array data is still stored the same, the index key is only used as a convenience in the UI and API.
                    '''
                    SQL = "select rowIndex, columnIndex, floatValue, integerValue, stringValue, booleanValue from SfcRecipeDataMatrixElementView where RecipeDataId = %d order by rowIndex, columnIndex" % (recipeDataId)
                    pds = system.db.runQuery(SQL, db)
                    
                    vals = []
                    for record in pds:
                        if valueType == "Float":
                            vals.append(record['floatValue'])
                        elif valueType == "Integer":
                            vals.append(record['integerValue'])
                        elif valueType == "String":
                            vals.append(record['stringValue'])
                        elif valueType == "Boolean":
                            vals.append(str(record['booleanValue']))
                        else:
                            log.errorf("****** Unknown matrix value data type: %s", valueType)
                            
                    rd["vals"] = vals
    
                elif recipeDataType in ["Output", "Output Ramp"]:
                    valueType = record["ValueType"]
                    rd["valueType"] = valueType
                    rd["tag"] =record['Tag'] 
                    rd["outputType"] = record['OutputType'] 
                    rd["download"] = record['Download'] 
                    rd["timing"] = record['Timing'] 
                    rd["maxTiming"] = record['MaxTiming'] 
                    rd["writeConfirm"] = record['WriteConfirm']
                    
                    if valueType == "Float":
                        rd["outputValue"] = record['OutputFloatValue']
                        rd["targetValue"] = record['TargetFloatValue']
                    elif valueType == "Integer":
                        rd["outputValue"] = record['OutputIntegerValue']
                        rd["targetValue"] = record['TargetIntegerValue']
                    elif valueType == "String":
                        rd["outputValue"] = escapeJSON(str(record['OutputStringValue']))
                        rd["targetValue"] = escapeJSON(str(record['TargetStringValue']))
                    elif valueType == "Boolean":
                        rd["outputValue"] = str(record['OutputBooleanValue'])
                        rd["targetValue"] = str(record['TargetBooleanValue'])
                    else:
                        log.errorf("****** Unknown output value data type: %s", valueType)
                        
                    if recipeDataType == "Output Ramp":
                        rd["rampTimeMinutes"] = record['RampTimeMinutes']
                        rd["updateFrequencySeconds"] = record['UpdateFrequencySeconds']
        
                elif recipeDataType == "Recipe":
                    rd["presentationOrder"] =record['PresentationOrder'] 
                    rd["storeTag"] =record['StoreTag'] 
                    rd["compareTag"] = record['CompareTag'] 
                    rd["modeAttribute"] = record['ModeAttribute'] 
                    rd["modeValue"] = record['ModeValue'] 
                    rd["changeLevel"] = record['ChangeLevel'] 
                    rd["recommendedValue"] = record['RecommendedValue']
                    rd["lowLimit"] =record['LowLimit'] 
                    rd["highLimit"] =record['HighLimit'] 
                    
                elif recipeDataType == "SQC":
                    rd["lowLimit"] =record['LowLimit'] 
                    rd["targetValue"] =record['TargetValue'] 
                    rd["highLimit"] = record['HighLimit'] 
            
                elif recipeDataType == "Timer":
                    '''
                    All of the other properties for a Timer are transient and get set at runtime.
                    '''
                else:
                    print "***************************************************************"
                    print "*****  ERROR: Unexpected recipe data type: ", recipeDataType
                    print "***************************************************************"
    
            log.tracef("Appending the structure to the list...")
            recipe.append(rd)
    
        if len(recipe) > 0:
            log.tracef("There is recipe data, inserting it into the XML...")
            recipeTxtJson = system.util.jsonEncode(recipe)
            recipeTxt ='<associated-data> {"recipe": ' + recipeTxtJson + "} </associated-data> "
        
            step = step[:len(step) - 7]
            step = step + recipeTxt + " </step>" 
            log.tracef( "   Step After: %s", step)
            
        chartXML = chartXML + step
        
    chartXML = chartXML + postamble
    
    log.tracef("Chart After: %s", str(chartXML))
    return chartXML

def internalizeRecipeDataForChartText(chartPath, chartXML, chartPaths, chartInfo, folderInfo, db):
    '''
    Insert the recipe data into the associated-data slot for each step.  The chart XML is in XML, which is basically text.
    If I use XML tools to insert the recipe data into the chart XML then A) I have less control, and B) ET inserts all sort of 
    escape characters making it harder to read, which is the whole point of using XML.  So I am going to use text string
    manipulation to add things in. 
    '''
    
    #---------------------------------------------------
    def splitChartXML(chartXML):
        '''
        Split the XML for a chart into 3 parts: the preamble, the postamble, and the middle - which contains the steps.
        This makes it easy to put back together at the end.  We are going to insert recipe data into the steps part, but the pre and 
        post parts remain unchanged.
        '''
        steps =  []
        start = chartXML.find("<step")
        end = chartXML.rfind("</step>") + 7
        preamble = chartXML[:start]
        middle = chartXML[start:end]
        postamble = chartXML[end:]

        while len(middle) > 0:
            stepStart = middle.find("<step")
            stepEnd = middle.find("</step>") + 7
            stepTxt = middle[stepStart:stepEnd]
            steps.append(stepTxt)
            middle = middle[stepEnd:]
        
        return preamble, postamble, steps
    #----------------------------------------------------
    
    log.infof("=====================================")
    log.infof("Processing recipe data for chart: %s", chartPath)
    log.infof("=====================================")
    
    log.tracef("Chart Info: %s", str(chartInfo))
    
    chartId = chartPaths[chartPath]
    log.tracef("The chart Id is: %d", chartId)
    
    chartDict = chartInfo[chartId]
    log.tracef("The chart dictionary is: %s", str(chartDict))
    
    stepInfo = chartDict['stepInfo']
    log.tracef("The step info is: %s", str(stepInfo))
    
    preamble, postamble, steps = splitChartXML(chartXML)

    chartXML = preamble
    for step in steps:
        log.tracef(" ")
        log.tracef("Processing: %s", str(step))

        stepName = step[step.find("name=")+6:]
        stepName = stepName[:stepName.find("\"")]
        log.tracef("  StepName: <%s>", stepName)
        log.tracef("  Looking for recipe data for step: <%s>", stepName)
        stepDict = stepInfo.get(stepName, None)
        log.tracef("  Step Dictionary: %s", str(stepDict))
        recipeDataList = stepDict.get("recipeData", [])
        log.tracef("  Recipe data for Step: %s", str(recipeDataList))
        
        recipeTxt = ""
        recipe = []
        for record in recipeDataList:
            log.tracef("           Inserting the recipe data...")
            
            recipeDataType = record["RecipeDataType"]
            if recipeDataType == "Folder":
                print "**************************************"
                print "**  NEED TO PROCESS A FOLDER  **"
                print "**************************************"
                
                recipeDataKey = record["RecipeDataKey"]
                log.infof("      ...processing FOLDER recipe data %s...", recipeDataKey)
                
                folderId = record["RecipeDataFolderId"]
                path = folderInfo.get(folderId).get("path")
                
                txt = ' "recipeDataKey"="%s", ' % (recipeDataKey)
                txt += ' "recipeDataType"="%s", ' % (recipeDataType) 
                txt += ' "label"="%s", ' % (escapeJSON(record["Label"]))
                txt += ' "description"="%s", ' % (escapeJSON(record["Description"]))
                txt += ' "folderId"="%s", ' % (str(record["RecipeDataFolderId"]))
                txt += ' "parentFolderId"="%s", ' % (str(record["ParentRecipeDataFolderId"]))
                txt += ' "path"="%s" ' % (path)
 
                ''' TODO - I might need the parent folder key when it comes time to import '''
            else:
                recipeDataId = record["RecipeDataId"]
                recipeDataKey = record["RecipeDataKey"]
                log.infof("      ...processing recipe data %s - %s - %d (%s - %s)", recipeDataKey, recipeDataType, recipeDataId, chartPath, stepName)
                
                folderId = record["FolderId"]
                folderKey = record["FolderKey"]
                
                baseTxt = ' "recipeDataKey"="%s", "recipeDataType"="%s", "label"="%s", "description"="%s", "units"="%s", "parent"="%s", "folderId"="%s" '  % \
                    (recipeDataKey, recipeDataType, escapeJSON(record["Label"]), escapeJSON(record["Description"]), record["Units"], folderKey, str(folderId))
                
                rd = {}
                rd["recipeDataKey"] = recipeDataKey
                rd["recipeDataType"] = recipeDataType
                rd["label"] = escapeJSON(record["Label"])
                rd["description"] = escapeJSON(record["Description"])
                rd["units"] = record["Units"]
                rd["parent"] = folderKey
                rd["folderId"] = str(folderId)
        
                if recipeDataType == 'Array':
                    valueType = record["ValueType"]
                    txt = baseTxt + ', "valueType"="%s", ' % (valueType)
                    txt += ' "indexKey"="%s", ' % (record["KeyName"])
                    
                    '''
                    The indexKey is just another array - hopefully it is in the same scope as this.  The order of export/import doesn't matter because the array data is still stored the same, 
                    the index key is only used as a convenience in the UI and API.
                    '''
                    SQL = "select arrayIndex, floatValue, integerValue, stringValue, booleanValue from SfcRecipeDataArrayElementView where RecipeDataId = %d" % (recipeDataId)
                    pds = system.db.runQuery(SQL, db)
                    txt += ' "rows"="%d" ' % (len(pds))
                    for record in pds:
                        if valueType == "Float":
                            txt += ' ,"element%d"="%s" ' % (record['arrayIndex'], str(record['floatValue']))
                        elif valueType == "Integer":
                            txt += ' ,"element%d"="%s" ' % (record['arrayIndex'], str(record['integerValue']))
                        elif valueType == "String":
                            txt += ' ,"element%d"="%s" ' % (record['arrayIndex'], record['stringValue'])
                        elif valueType == "Boolean":
                            txt += ' ,"element%d"="%s" ' % (record['arrayIndex'], str(record['booleanValue']))
                        else:
                            log.errorf("****** Unknown array value data type: %s", valueType)
                    
                elif recipeDataType == "Input":
                    valueType = record["ValueType"]
                    txt = baseTxt + ', "valueType"="%s", ' % (valueType)                
                    txt += ' "tag"="%s" ' % (str(record['Tag']))
        
                elif recipeDataType == "Matrix":
                    valueType = record["ValueType"]
                    txt = baseTxt + ', "valueType"="%s", ' % (valueType)
                    txt += ' "rows"="%d", ' % (record["Rows"])
                    txt += ' "columns"="%d", ' % (record["Columns"])
                    txt += ' "rowIndexKey"="%s", ' % (record["RowIndexKeyName"])
                    txt += ' "columnIndexKey"="%s" ' % (record["ColumnIndexKeyName"])
                    
                    '''
                    The index is just a string array (NOT RECIPE DATA).  Hopefully the array key will already exist on the target system.  The order of export/import doesn't matter because 
                    the array data is still stored the same, the index key is only used as a convenience in the UI and API.
                    '''
                    SQL = "select rowIndex, columnIndex, floatValue, integerValue, stringValue, booleanValue from SfcRecipeDataMatrixElementView where RecipeDataId = %d" % (recipeDataId)
                    pds = system.db.runQuery(SQL, db)
                    for record in pds:
                        if valueType == "Float":
                            txt += ' ,"element_%d_%d"="%s" ' % (record["rowIndex"], record["columnIndex"], str(record['floatValue']))
                        elif valueType == "Integer":
                            txt += ' ,"element_%d_%d"="%s" ' % (record["rowIndex"], record["columnIndex"], str(record['integerValue']))
                        elif valueType == "String":
                            txt += ' ,"element_%d_%d"="%s" ' % (record["rowIndex"], record["columnIndex"], str(record['stringValue']))
                        elif valueType == "Boolean":
                            txt += ' ,"element_%d_%d"="%s" ' % (record["rowIndex"], record["columnIndex"], str(record['booleanValue']))
                        else:
                            log.errorf("****** Unknown array value data type: %s", valueType)
    
                elif recipeDataType == "Output":
                    valueType = record["ValueType"]
                    txt = baseTxt + ', "valueType"="%s", ' % (valueType)
                    
                    txt += ' "tag"="%s", ' % (str(record['Tag'])) 
                    txt += ' "outputType"="%s", ' % (str(record['OutputType'])) 
                    txt += ' "download"="%s", ' % (str(record['Download'])) 
                    txt += ' "timing"="%s", ' % (str(record['Timing'])) 
                    txt += ' "maxTiming"="%s", ' % (str(record['MaxTiming'])) 
                    txt += ' "writeConfirm"="%s", ' % (str(record['WriteConfirm']))
                    
                    if valueType == "Float":
                        txt += ' "value"="%s" ' % (str(record['OutputFloatValue']))
                    elif valueType == "Integer":
                        txt += ' "value"="%s" ' % (str(record['OutputIntegerValue']))
                    elif valueType == "String":
                        txt += ' "value"="%s" ' % (escapeJSON(str(record['OutputStringValue'])))
                    elif valueType == "Boolean":
                        txt += ' "value"="%s" ' % (str(record['OutputBooleanValue']))
                    else:
                        log.errorf("****** Unknown output value data type: %s", valueType)
                        txt = ""
                        
                elif recipeDataType == "Output Ramp":
                    valueType = record["ValueType"]
                    txt = baseTxt + ', "valueType"="%s", ' % (valueType)
                    txt += ' "tag"="%s", ' % (str(record['Tag'])) 
                    txt += ' "outputType"="%s", ' % (str(record['OutputType'])) 
                    txt += ' "download"="%s", ' % (str(record['Download'])) 
                    txt += ' "timing"="%s", ' % (str(record['Timing'])) 
                    txt += ' "maxTiming"="%s", ' % (str(record['MaxTiming'])) 
                    txt += ' "writeConfirm"="%s", ' % (str(record['WriteConfirm']))
                    txt += ' "rampTimeMinutes"="%s", ' % (str(record['RampTimeMinutes']))
                    txt += ' "updateFrequencySeconds"="%s", ' % (str(record['UpdateFrequencySeconds']))
                    
                    if valueType == "Float":
                        txt += ' "value"="%s" ' % (str(record['OutputFloatValue']))
                    elif valueType == "Integer":
                        txt += ' "value"="%s" ' % (str(record['OutputIntegerValue']))
                    elif valueType == "String":
                        txt += ' "value"="%s" ' % (escapeJSON(str(record['OutputStringValue'])))
                    elif valueType == "Boolean":
                        txt += ' "value"="%s" ' % (str(record['OutputBooleanValue']))
                    else:
                        log.errorf("****** Unknown output ramp value data type: %s", valueType)
                        txt = ""
        
                elif recipeDataType == "Recipe":
                    txt = baseTxt + ' ,"presentationOrder"="%s", ' % (str(record['PresentationOrder']))
                    txt += ' "storeTag"="%s", ' % (str(record['StoreTag']))
                    txt += ' "compareTag"="%s", ' % (str(record['CompareTag'])) 
                    txt += ' "ModeAttribute"="%s", ' % (str(record['ModeAttribute']))
                    txt += ' "modeValue"="%s", ' % (str(record['ModeValue']))
                    txt += ' "changeLevel"="%s", ' % (str(record['ChangeLevel']))
                    txt += ' "recommendedValue"="%s", ' % (str(record['RecommendedValue'])) 
                    txt += ' "lowLimit"="%s", ' % (str(record['LowLimit']))
                    txt += ' "highLimit"="%s" ' % (str(record['HighLimit']))
            
                elif recipeDataType == "Simple Value":
                    valueType = record["ValueType"]
                    
                    txt = baseTxt + ' ,"valueType"="%s", ' % (valueType)
                    
                    if valueType == "Float":
                        txt += ' "value"="%s" ' % (str(record['FloatValue']))
                    elif valueType == "Integer":
                        txt += ' "value"="%s" ' % (str(record['IntegerValue']))
                    elif valueType == "String":
                        txt += ' "value"="%s" ' % (escapeJSON(str(record['StringValue'])))
                    elif valueType == "Boolean":
                        txt += ' "value"="%s" ' % (str(record['BooleanValue']))
                    else:
                        log.errorf("****** Unknown simple value data type: %s", valueType)
                        txt = ""
            
                elif recipeDataType == "Timer":
                    '''
                    All of the other properties for a Timer are transient and get set at runtime.
                    '''
                    txt = baseTxt
        
                else:
                    print "***************************************************************"
                    print "*****  ERROR: Unexpected recipe data type: ", recipeDataType
                    print "***************************************************************"
    
            if recipeTxt == "":
                recipeTxt = "{" + txt + "}"
            else:
                recipeTxt = recipeTxt + ",{" + txt + "}"
                
                
    
        if recipeTxt <> "":
            recipeTxtJson = system.util.jsonEncode(recipeTxt)
            recipeTxt ='<associated-data> {"recipe": [' + recipeTxt + "]} </associated-data> "
        
        step = step[:len(step) - 7]
        step = step + recipeTxt + " </step>" 
        log.tracef( "   Step After: %s", step)
        chartXML = chartXML + step
        
    chartXML = chartXML + postamble
    
    log.tracef("Chart After: %s", str(chartXML))
    return chartXML