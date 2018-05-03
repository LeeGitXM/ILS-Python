'''
Created on May 31, 2017

@author: phass
'''

import system, os
from ils.sfc.recipeData.hierarchyWithBrowser import fetchHierarchy, getChildren
from ils.sfc.recipeData.core import fetchChartPathFromChartId
from ils.common.config import getDatabaseClient
log=system.util.getLogger("com.ils.sfc.recipeBrowser")

def exportCallback(event):
    db = getDatabaseClient()
    log.infof("In %s.exportCallback()...", __name__)
    treeWidget = event.source.parent.getComponent("Tree View")
    
    # First get the last node in the path
    chartPath = treeWidget.selectedPath
    log.infof("The raw selected path is: <%s>", chartPath)
    chartPath = chartPath[chartPath.rfind("/")+1:]
    
    # Now replace ":" with "/"
    chartPath = chartPath.replace('\\', '/')
    log.infof("The selected chart path is <%s>", chartPath)
    if chartPath == "" or chartPath == None:
        return
    
    SQL = "select chartId from SfcChart where chartPath = '%s'" % (chartPath)
    chartId = system.db.runScalarQuery(SQL) 
    log.infof("Fetched chart id: %s", str(chartId))
    if chartId == None:
        return
    
    rootContainer = event.source.parent.parent
    folder = rootContainer.importExportFolder
    filename = folder + "/recipeExport.xml"
    filename = system.file.saveFile(filename, "xml", "name of xml export file")
    if filename == None:
        return
    
    folder = os.path.dirname(filename)
    print "The folder is: ", folder
    rootContainer.importExportFolder = folder
    
    sfcRecipeDataShowProductionOnly = False
    hierarchyPDS = fetchHierarchy(sfcRecipeDataShowProductionOnly)
    log.tracef("Selected %d chart hierarchy records...", len(hierarchyPDS))
    
    chartPDS = system.db.runQuery("Select ChartId, ChartPath from SfcChart order by ChartId", db)
    log.tracef("Selected info for %d charts...", len(chartPDS))
    
    ''' Export any keys that are used by keyed arrays or matrices. '''
    keyTxt = exportKeysForTree(chartId, hierarchyPDS, chartPDS, db)
    
    ''' Export the tree (Charts, steps, and recipe data) '''
    txt, structureTxt = exportTree(chartId, hierarchyPDS, chartPDS, db)
    
    txt = "<data>\n" + keyTxt + txt + structureTxt + "</data>"
    system.file.writeFile(filename, txt, False)


def exportKeysForTree(chartId, hierarchyPDS, chartPDS, db):
    log.infof("Exporting keys for chart Id: %d", chartId)
    
    chartIds = [chartId]
    newKids = True
    
    while newKids:
        newKids = False
        for chartId in chartIds:
            newChildren, aList = fetchChildren(chartId, chartIds, [], hierarchyPDS, chartPDS)
            if len(newChildren) > 0:
                log.tracef("Found that %d had new kids: %s", chartId, str(newChildren))
                newKids = True
                chartIds = chartIds + newChildren
    
    log.tracef("The chart ids are: %s", str(chartIds))
    
    txt = ""
    keys = []
    for chartId in chartIds:
        SQL = "select RecipeDataId from SfcRecipeDataView where chartId = %d and RecipeDataType = 'Matrix'" % (chartId)
        pds = system.db.runQuery(SQL, db)
        
        for record in pds:
            print "Found matrix id: ", record["RecipeDataId"]
            SQL = "select RowIndexKeyId, ColumnIndexKeyId from SfcRecipeDataMatrix where RecipeDataId = %d" % (record["RecipeDataId"])
            keyPds = system.db.runQuery(SQL, db)
            for record in keyPds:
                if record["RowIndexKeyId"] != None and record["RowIndexKeyId"] not in keys:
                    print "Found a new Matrix row key: ", record["RowIndexKeyId"]
                    keys.append(record["RowIndexKeyId"])
                if record["ColumnIndexKeyId"] != None and record["ColumnIndexKeyId"] not in keys:
                    print "Found a new matrix column key: ", record["ColumnIndexKeyId"]
                    keys.append(record["ColumnIndexKeyId"])
        
        SQL = "select RecipeDataId from SfcRecipeDataView where chartId = %d and RecipeDataType = 'Array'" % (chartId)
        pds = system.db.runQuery(SQL, db)
        
        for record in pds:
            print "Found array id: ", record["RecipeDataId"]
            SQL = "select IndexKeyId from SfcRecipeDataArray where RecipeDataId = %d and IndexKeyId is not null" % (record["RecipeDataId"])
            keyPds = system.db.runQuery(SQL, db)
            for record in keyPds:
                if record["IndexKeyId"] not in keys:
                    print "Found a new Array key: ", record["IndexKeyId"]
                    keys.append(record["IndexKeyId"])
        
#        txt = txt + exportKeysForChart(chartId, db)
    print "The referenced keys are: ", keys
    
    for key in keys:
        SQL = "select * from SfcRecipeDataKeyView where KeyId = %d order by KeyIndex" % (key)
        pds = system.db.runQuery(SQL, db)
        row = 1
        for record in pds:
            if row == 1:
                txt = txt + "<key name='%s'>\n" % (record["KeyName"])
            txt = txt + "<element value='%s' index='%d'/>\n" % (record["KeyValue"], record["KeyIndex"])
            row = row + 1
        txt = txt + "</key>\n"
    
    print "The key XML is: ", txt
    return txt


def getChartPathFromPDS(chartId, chartPDS):
    for chart in chartPDS:
        if chart["ChartId"] == chartId:
            return chart["ChartPath"]
    return ""


def exportTree(chartId, hierarchyPDS, chartPDS, db):
    log.infof("Exporting chart Id: %d", chartId)
    
    chartIds = [chartId]
    parentChildList = []
    newKids = True
    
    while newKids:
        newKids = False
        for chartId in chartIds:
            newChildren, parents = fetchChildren(chartId, chartIds, parentChildList, hierarchyPDS, chartPDS)
            if len(newChildren) > 0:
                log.tracef("Found that %d had new kids: %s", chartId, str(newChildren))
                newKids = True
                chartIds = chartIds + newChildren

    log.tracef("The chart ids are: %s", str(chartIds))
    
    txt = ""
    
    for chartId in chartIds:
        txt = txt + exportChart(chartId, db)
    
    hierarchyXML = ""
    print "The parents are:"
    for record in parentChildList:
        print record
        parentChartPath = getChartPathFromPDS(record["parent"], chartPDS)
        childChartPath = getChartPathFromPDS(record["child"], chartPDS)
        hierarchyXML = hierarchyXML + "<parentChild parent=\"%s\" child=\"%s\" stepName=\"%s\" />\n" % (parentChartPath, childChartPath, record["stepName"])

    return txt, hierarchyXML


def fetchChildren(chartId, visitedCharts, parentChildList, hierarchyPDS, chartPDS):
    log.tracef("Looking for the children of chart %d", chartId)
    
    children = []
    hierarchyXML = ""
    log.tracef("Getting the children of chart: %s", str(chartId))
    for record in hierarchyPDS:
        if record["ChartId"] == chartId and record["ChildChartId"] not in children:
            d = {"parent":record["ChartId"], "child": record["ChildChartId"], "stepName": record["StepName"]}
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


def exportChart(chartId, db):
    print "Exporting ", chartId
    
    stepTxt = exportChartSteps(chartId, db)
    
    chartPath = fetchChartPathFromChartId(chartId)
    txt = "<chart chartId=\"%d\" chartPath=\"%s\" >\n" % (chartId, chartPath)
    txt = txt + stepTxt
    txt = txt + "</chart>\n\n"
    
    return txt


def exportChartSteps(chartId, db):
    print "Exporting ", chartId
    
    SQL = "select stepId, stepName, stepUUID, stepType from SfcStepView where chartId = %d" % (chartId)
    pds = system.db.runQuery(SQL, db)
    
    stepTxt = ""
    
    for record in pds:
        stepId = record["stepId"]
        recipeDataTxt = exportRecipeDataForStep(stepId, db)
        stepTxt = stepTxt + "<step stepName='%s' stepType='%s' stepUUID='%s' >\n" % (record["stepName"], record["stepType"], record["stepUUID"])
        stepTxt = stepTxt + recipeDataTxt
        stepTxt = stepTxt + "</step>\n\n"
    
    return stepTxt


def exportRecipeDataForStep(stepId, db):
    print "Exporting recipe data for step ", stepId
    
    def fetchFirstRecord(SQL, db):
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        return record
    
    SQL = "select recipeDataId, recipeDataKey, recipeDataType, label, description, units from SfcRecipeDataView where stepId = %d" % (stepId)
    pds = system.db.runQuery(SQL, db)
    
    recipeDataTxt = ""
    
    for record in pds:
        recipeDataId = record["recipeDataId"]
        recipeDataType = record["recipeDataType"]
        recipeDataKey = record["recipeDataKey"]
        
        print "Found recipe data %s - %s " % (recipeDataKey, recipeDataType)
        
        baseTxt = "<recipe recipeDataKey='%s' recipeDataType='%s' label='%s' description='%s' units='%s' " % (recipeDataKey, recipeDataType, record["label"], record["description"], record["units"])
        
        if recipeDataType == "Simple Value":
            SQL = "select valueType, floatValue, integerValue, stringValue, booleanValue from SfcRecipeDataSimpleValueView where RecipeDataId = %d" % (recipeDataId)
            record = fetchFirstRecord(SQL, db)
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
                print "****** Unknown simple value data type: ", valueType

        elif recipeDataType == "Recipe":
            SQL = "select presentationOrder, storeTag, compareTag, ModeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit from SfcRecipeDataRecipeView where RecipeDataId = %d" % (recipeDataId)
            record = fetchFirstRecord(SQL, db)
            recipeDataTxt = recipeDataTxt + baseTxt + " presentationOrder='%s' storeTag='%s' compareTag='%s' ModeAttribute='%s' modeValue='%s' changeLevel='%s' recommendedValue='%s' lowLimit='%s' highLimit='%s' />" %\
                (str(record['presentationOrder']), str(record['storeTag']), str(record['compareTag']), str(record['ModeAttribute']), str(record['modeValue']),\
                 str(record['changeLevel']), str(record['recommendedValue']), str(record['lowLimit']), str(record['highLimit']))

        elif recipeDataType == "Timer":
            '''
            All of the other properties for a Timer are transient and get set at runtime.
            '''
            recipeDataTxt = recipeDataTxt + baseTxt + " />"

        elif recipeDataType == "Output":
            SQL = "select tag, valueType, outputType, download, timing, maxTiming, writeConfirm, outputFloatValue, outputIntegerValue, outputStringValue, outputBooleanValue "\
                " from SfcRecipeDataOutputView where RecipeDataId = %d" % (recipeDataId)
            record = fetchFirstRecord(SQL, db)
            
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
                print "****** Unknown output value data type: ", valueType
                
            recipeDataTxt = recipeDataTxt + baseTxt + " tag='%s' valueType='%s' outputType='%s' download='%s' timing='%s' maxTiming='%s' writeConfirm='%s' value='%s' />" %\
                (str(record['tag']), str(record['valueType']), str(record['outputType']), str(record['download']), str(record['timing']), str(record['maxTiming']), \
                 str(record['writeConfirm']), val )

        elif recipeDataType == "Output Ramp":
            SQL = "select tag, valueType, outputType, download, timing, maxTiming, writeConfirm, outputFloatValue, outputIntegerValue, outputStringValue, outputBooleanValue, "\
                " rampTimeMinutes, updateFrequencySeconds "\
                " from SfcRecipeDataOutputRampView where RecipeDataId = %d" % (recipeDataId)
            record = fetchFirstRecord(SQL, db)
            
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
                print "****** Unknown output value data type: ", valueType
                
            recipeDataTxt = recipeDataTxt + baseTxt + " tag='%s' valueType='%s' outputType='%s' download='%s' timing='%s' maxTiming='%s' writeConfirm='%s' value='%s' "\
                " rampTimeMinutes='%s' updateFrequencySeconds='%s' />" %\
                (str(record['tag']), str(record['valueType']), str(record['outputType']), str(record['download']), str(record['timing']), str(record['maxTiming']), \
                str(record['writeConfirm']), val, str(record['rampTimeMinutes']), str(record['updateFrequencySeconds']) )

        elif recipeDataType == "Input":
            SQL = "select tag, valueType from SfcRecipeDataInputView where RecipeDataId = %d" % (recipeDataId)
            record = fetchFirstRecord(SQL, db)
            recipeDataTxt = recipeDataTxt + baseTxt + " tag='%s' valueType='%s' />" %\
                (str(record['tag']), str(record['valueType']))
        
        elif recipeDataType == "Array":
            SQL = "select valueType, keyName from SfcRecipeDataArrayView where RecipeDataId = %d" % (recipeDataId)
            record = fetchFirstRecord(SQL, db)
            valueType = record["valueType"]
            indexKey = record["keyName"]
            recipeDataTxt = recipeDataTxt + baseTxt + " valueType='%s' indexKey='%s' >" % (valueType, indexKey)
            
            '''
            The indexKey is just another array - hopefully it is in the same scope as this.  The order of export/import doesn't matter because the array data is still stored the same, 
            the index key is only used as a convenience in the UI and API.
            '''
            
            SQL = "select arrayIndex, floatValue, integerValue, stringValue, booleanValue from SfcRecipeDataArrayElementView where RecipeDataId = %d" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
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
                    print "****** Unknown array value data type: ", valueType

            recipeDataTxt = recipeDataTxt + "</recipe>\n"
            
            
        elif recipeDataType == "Matrix":
            SQL = "select valueType, rows, columns, rowIndexKeyName, columnIndexKeyName from SfcRecipeDataMatrixView where RecipeDataId = %d" % (recipeDataId)
            record = fetchFirstRecord(SQL, db)
            valueType = record["valueType"]
            recipeDataTxt = recipeDataTxt + baseTxt + " valueType='%s' rows='%d' columns='%d' rowIndexKey='%s' columnIndexKey='%s' >" % \
                (valueType, record["rows"], record["columns"], record["rowIndexKeyName"], record["columnIndexKeyName"])
            
            '''
            The index is just another array.  The order of export/import doesn't matter because the array data is still stored the same, 
            the index key is only used as a convenience in the UI and API.
            '''
            
            SQL = "select rowIndex, columnIndex, floatValue, integerValue, stringValue, booleanValue from SfcRecipeDataMatrixElementView where RecipeDataId = %d" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
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
                    print "****** Unknown array value data type: ", valueType

            recipeDataTxt = recipeDataTxt + "</recipe>\n"
            
            
        else:
            print "***** Unsupported recipe data type: ", recipeDataType
#recipeDataTxt = recipeDataTxt + "</recipe>\n\n"
    return recipeDataTxt
