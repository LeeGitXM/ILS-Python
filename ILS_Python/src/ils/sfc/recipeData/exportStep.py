'''
Created on May 10, 2021

@author: phass
'''

import system
import xml.etree.ElementTree as ET
from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.export import Exporter
from ils.sfc.recipeData.importer import Importer

def exportCallback(event):
    db, chartPath, chartId, stepName, stepId = getInfo(event)
    if chartPath == "" or stepName == "":
        return
    
    filename = system.file.saveFile("", "xml", "name of xml export file")
    if filename == None:
        return
    
    exporter = Exporter(db)

    ''' Export any keys that are used by keyed arrays or matrices. '''
    keyTxt = exportKeysForChart(chartId, db)
    recipeFolderTxt = exporter.exportRecipeDataFoldersForStep(stepId, stepName)
    recipeDataTxt = exporter.exportRecipeDataForStep(stepId, stepName)
    
    txt = "<data>\n" + keyTxt + recipeFolderTxt + recipeDataTxt + "</data>"
    
    system.file.writeFile(filename, txt, False)
    system.gui.messageBox("Chart and recipe were successfully exported!")

    
def clearCallback(event):
    db, chartPath, chartId, stepName, stepId = getInfo(event)
    if chartPath == "" or stepName == "":
        return
    
    print "In %s.clearCallback()..." %  (__name__)
    SQL = "delete from sfcRecipeData where stepId = %d" % (stepId)
    rows = system.db.runUpdateQuery(SQL, database=db)
    system.gui.messageBox("Successfully deleted %d rows" % (rows))
    
def importCallback(event):
    print "Importing..."
    db, chartPath, chartId, stepName, stepId = getInfo(event)
    if chartPath == "" or stepName == "":
        return
    
    filename = system.file.saveFile("", "xml", "name of xml export file")
    if filename == None:
        return
    
    importer = Importer(db)
    importer.stepTypes = importer.sql.loadStepTypes()
    importer.recipeDataTypes = importer.sql.loadRecipeDataTypes()
    importer.valueTypes = importer.sql.loadValueTypes()
    importer.outputTypes = importer.sql.loadOutputTypes()
    importer.sql.loadRecipeDataArrayKeys()
    
    tree = ET.parse(filename)
    root = tree.getroot()
    
    '''
    Load the matrix and array keys if there are any new ones.
    '''
    print "Importing array keys..."
    cnt = importer.sql.insertNewRecipeDataArrayKeys(root)
    importer.sql.commit()
    print "Successfully imported %d array / matrix keys!" % (cnt)
    
    '''
    Unfortunately the following code was in the middle of a big long method.
    It should be refactored to allow this to be called without a massive copy and paste
    '''
    
    ''' Insert Folders '''
    print "Checking for recipe folders..."
    importer.parseFolders(root, stepId)
                    
    ''' Insert recipe data '''
    recipeDataCounter = 0
    for recipe in root.findall("recipe"):
        folderId = None
        recipeDataType = recipe.get("recipeDataType")
        recipeDataTypeId = importer.recipeDataTypes.get(recipeDataType, -99)
        recipeDataKey = recipe.get("recipeDataKey")
        label = recipe.get("label")
        description = recipe.get("description")
        advice = recipe.get("advice")
        parent = recipe.get("parent")
        print "%s - <%s>" % (recipeDataKey, parent) 
        
        if parent not in ["", None]:
            folderId = importer.findFolder(parent)
        
        if recipeDataType == "Simple Value":
            valueType = recipe.get("valueType")
            valueTypeId = importer.valueTypes.get(valueType, -99)
            val = recipe.get("value")
            units = recipe.get("units", "")
            recipeDataId = importer.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
            importer.sql.insertSimpleRecipeData(recipeDataId, valueType, valueTypeId, val)
            recipeDataCounter = recipeDataCounter + 1
        
        elif recipeDataType in ["Output", "Output Ramp"]:
            valueType = recipe.get("valueType")
            valueTypeId = importer.valueTypes.get(valueType, -99)
            val = recipe.get("value")
            units = recipe.get("units", "")
            outputType = recipe.get("outputType", "")
            outputTypeId = importer.outputTypes.get(outputType, -99)
            tag = recipe.get("tag", "")
            download = recipe.get("download", "True")
            timing = recipe.get("timing", "0.0")
            maxTiming = recipe.get("maxTiming", "0.0")
            writeConfirm = recipe.get("writeConfirm", "True")
            
            recipeDataId = importer.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
            importer.sql.insertOutputRecipeData(recipeDataId, valueType, valueTypeId, outputType, outputTypeId, tag, download, timing, maxTiming, val, writeConfirm)
            recipeDataCounter = recipeDataCounter + 1
            
            if recipeDataType == "Output Ramp":
                rampTimeMinutes = recipe.get("rampTimeMinutes", "0.0")
                updateFrequencySeconds = recipe.get("updateFrequencySeconds", "0.0")
                importer.sql.insertOutputRampRecipeData(recipeDataId, rampTimeMinutes, updateFrequencySeconds)
    
        elif recipeDataType in ["Input"]:
            valueType = recipe.get("valueType")
            valueTypeId = importer.valueTypes.get(valueType, -99)
            units = recipe.get("units", "")
            tag = recipe.get("tag", "")
    
            recipeDataId = importer.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
            importer.sql.insertInputRecipeData(recipeDataId, valueType, valueTypeId, tag)
            recipeDataCounter = recipeDataCounter + 1
    
        elif recipeDataType == "Array":
            valueType = recipe.get("valueType")
            valueTypeId = importer.valueTypes.get(valueType, -99)
            units = recipe.get("units", "")
            indexKey = recipe.get("indexKey", None)
            print "The array index key is: %s" % (indexKey)
            recipeDataId = importer.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
            importer.sql.insertArray(recipeDataId, valueType, valueTypeId, indexKey)
            recipeDataCounter = recipeDataCounter + 1
            
            for element in recipe.findall("element"):
                arrayIndex = element.get("arrayIndex")
                val = element.get("value")
                importer.sql.insertArrayElement(recipeDataId, valueType, valueTypeId, arrayIndex, val)
    
        elif recipeDataType == "Matrix":
            valueType = recipe.get("valueType")
            valueTypeId = importer.valueTypes.get(valueType, -99)
            units = recipe.get("units", "")
            rows = recipe.get("rows", "")
            columns = recipe.get("columns", "")
            
            rowIndexKey = recipe.get("rowIndexKey", None)
            columnIndexKey = recipe.get("columnIndexKey", None)
                
            recipeDataId = importer.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
            importer.sql.insertMatrix(recipeDataId, valueType, valueTypeId, rows, columns, rowIndexKey, columnIndexKey)
            recipeDataCounter = recipeDataCounter + 1
            
            for element in recipe.findall("element"):
                rowIndex = element.get("rowIndex")
                columnIndex = element.get("columnIndex")
                val = element.get("value")
                importer.sql.insertMatrixElement(recipeDataId, valueType, valueTypeId, rowIndex, columnIndex, val)
        
        elif recipeDataType == "Timer":
            units = recipe.get("units", "")
            recipeDataId = importer.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
            importer.sql.insertTimerRecipeData(recipeDataId)
            recipeDataCounter = recipeDataCounter + 1
        
        elif recipeDataType == "Recipe":
            units = recipe.get("units", "")
            presentationOrder = recipe.get("presentationOrder", "0")
            storeTag = recipe.get("storeTag", "")
            compareTag = recipe.get("compareTag", "")
            modeAttribute = recipe.get("modeAttribute", "")
            modeValue = recipe.get("modeValue", "")
            changeLevel = recipe.get("changeLevel", "")
            recommendedValue = recipe.get("recommendedValue", "")
            lowLimit = recipe.get("lowLimit", "")
            highLimit = recipe.get("highLimit", "")
            
            recipeDataId = importer.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
            importer.sql.insertRecipeRecipeData(recipeDataId, presentationOrder, storeTag, compareTag, modeAttribute, modeValue, changeLevel, recommendedValue, lowLimit, highLimit)
            recipeDataCounter = recipeDataCounter + 1
            
        elif recipeDataType == "SQC":
            lowLimit = recipe.get("lowLimit", "")
            highLimit = recipe.get("highLimit", "")
            targetValue = recipe.get("targetValue", "")
            
            print "Inserting SQC recipe data with HL: %s, Target: %s, LL: %s " % (str(lowLimit), str(targetValue), str(highLimit))
            
            recipeDataId = importer.sql.insertRecipeData(stepId, recipeDataKey, recipeDataType, recipeDataTypeId, label, description, advice, units, folderId)
            importer.sql.insertSqcRecipeData(recipeDataId, lowLimit, targetValue, highLimit)
            
        else:
            txt = "Error: Unable to import recipe data type: %s with key %s for step %s on chart %s" % (recipeDataType, recipeDataKey, stepName, chartPath)
            print txt
            importer.sql.rollbackAndClose()
            system.gui.errorBox(txt)
            return
    
    # Do this at the very end
    importer.sql.commitAndClose()

    
def getInfo(event):
    db = getDatabaseClient()

    chartList = event.source.parent.getComponent("Chart Table")
    chartPath = chartList.selectedChart
    chartId = chartList.selectedChartId
    if chartPath == "":
        system.gui.warningBox("Select a chart")
        return db, "", "", "", -1
    
    stepTable = event.source.parent.getComponent("Step Table")
    stepName = stepTable.selectedStep
    if stepName == "":
        system.gui.warningBox("Select a step")
        return "", "", "", -1
    
    selectedRow = stepTable.selectedRow
    ds = stepTable.data
    stepId = ds.getValueAt(selectedRow, 0)
    
    return db, chartPath, int(chartId), stepName, stepId

def exportKeysForChart(chartId, db):
        print "====================================="
        print "Exporting Matrix and Array keys..."
        print"====================================="
        
        txt = ""
        keys = []

        SQL = "select RecipeDataId from SfcRecipeDataView where chartId = %d and RecipeDataType = 'Matrix'" % (chartId)
        pds = system.db.runQuery(SQL, db)
        
        for record in pds:
            print "Found matrix id: %s" % (str(record["RecipeDataId"]))
            SQL = "select RowIndexKeyId, ColumnIndexKeyId from SfcRecipeDataMatrix where RecipeDataId = %d" % (record["RecipeDataId"])
            keyPds = system.db.runQuery(SQL, db)
            for record in keyPds:
                if record["RowIndexKeyId"] != None and record["RowIndexKeyId"] not in keys:
                    print "Found a new Matrix row key: %s" % (str(record["RowIndexKeyId"]))
                    keys.append(record["RowIndexKeyId"])
                if record["ColumnIndexKeyId"] != None and record["ColumnIndexKeyId"] not in keys:
                    print "Found a new matrix column key: %s" % (str(record["ColumnIndexKeyId"]))
                    keys.append(record["ColumnIndexKeyId"])
        
        SQL = "select RecipeDataId from SfcRecipeDataView where chartId = %d and RecipeDataType = 'Array'" % (chartId)
        pds = system.db.runQuery(SQL, db)
        
        for record in pds:
            print "Found array id: %s" % (str(record["RecipeDataId"]))
            SQL = "select IndexKeyId from SfcRecipeDataArray where RecipeDataId = %d and IndexKeyId is not null" % (record["RecipeDataId"])
            keyPds = system.db.runQuery(SQL, db)
            for record in keyPds:
                if record["IndexKeyId"] not in keys:
                    print "Found a new Array key: %s" % (str(record["IndexKeyId"]))
                    keys.append(record["IndexKeyId"])
            
    #        txt = txt + exportKeysForChart(chartId, db)
        print "The referenced keys are: %s" % (str(keys))
        
        cnt = 0
        for key in keys:
            SQL = "select * from SfcRecipeDataKeyView where KeyId = %d order by KeyIndex" % (key)
            pds = system.db.runQuery(SQL, db)
            row = 1
            for record in pds:
                if row == 1:
                    txt = txt + "<key name='%s'>\n" % (record["KeyName"])
                txt = txt + "<element value='%s' index='%d'/>\n" % (record["KeyValue"], record["KeyIndex"])
                row = row + 1
                cnt = cnt + 1
            txt = txt + "</key>\n"
        
        print "The key XML is: %s" % (txt)
        print "Exported %d array keys" % (cnt)
        return txt
