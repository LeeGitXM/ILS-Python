'''
Created on Feb 10, 2017 

@author: phass
'''
import system
from ils.common.windowUtil import clearTable
from ils.sfc.recipeData.constants import ARRAY, INPUT, MATRIX, OUTPUT, SIMPLE_VALUE, TIMER
from ils.common.error import catchError
from ils.common.config import getTagProviderClient
log=system.util.getLogger("com.ils.sfc.recipeBrowser")

'''
Populate the left pane which has the logical view of the SFC call tree, clear the other two panes.
'''
def internalFrameOpened(rootContainer, db):
    log.infof("In %s.internalFrameOpened()", __name__) 
    updateSfcTree(rootContainer, db)
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    clearTable(stepTable)
    recipeDataTable = rootContainer.getComponent("Recipe Data Container").getComponent("Recipe Data")
    clearTable(recipeDataTable)

'''
This is called whenever the windows gains focus.  his happens as part of the noral workflow of creating or editing recipe data
so update the recipe data table to reflect the edit.
'''
def internalFrameActivated(rootContainer, db):
    log.infof("In %s.internalFrameActivated()", __name__)
#    refreshSteps(rootContainer, db)
    updateRecipeData(rootContainer, db)

def updateSfcTree(rootContainer, db):
    log.infof("In %s.updateSfcTree(), Updating the SFC Tree Widget...", __name__)
    tagProvider = getTagProviderClient()
    sfcRecipeDataShowProductionOnly = system.tag.read("[%s]Configuration/SFC/sfcRecipeDataShowProductionOnly" % (tagProvider)).value

    hierarchyPDS = fetchHierarchy(sfcRecipeDataShowProductionOnly, db)
    chartPDS = fetchCharts(sfcRecipeDataShowProductionOnly, db)
    trees = fetchSfcTree(chartPDS, hierarchyPDS)
    
    
    chartDict = {}
    for record in chartPDS:
        chartId=record["ChartId"]
        chartPath=record["ChartPath"]
        
        # Chart Paths use the '/' to indicate the path structure, but the tree widget interprets that as a child.  I want to treat
        # the chart path as the name so replace "/" with ":"
        chartDict[chartId] = chartPath.replace('/','\\')

    log.tracef("The chart dictionary is %s", str(chartDict))    
    rows=[]
    for tree in trees:
        row = expandRow(tree, chartDict)
        rows.append(row)

    header = ["path", "text", "icon", "background", "foreground", "tooltip", "border", "selectedText", "selectedIcon", "selectedBackground", "selectedForeground", "selectedTooltip", "selectedBorder"]
    ds = system.dataset.toDataSet(header, rows)
    treeWidget=rootContainer.getComponent("Tree Container").getComponent("Tree View")
    treeWidget.data = ds

    
def expandRow(tree, chartDict): 
    log.tracef("Expanding: %s", str(tree))
    tokens = tree.split(",")
    path=""
    for index in range(len(tokens)-1):
        token = tokens[index]
        chartName = chartDict.get(int(token),"Unknown")

        if path == "":
            path = chartName
        else:
            path = "%s/%s" % (path, chartName)

    token = tokens[-1]
    node = chartDict.get(int(token),"Unknown")

    row = [path,node,"default","color(255,255,255,255)","color(0,0,0,255)","","","","default","color(250,214,138,255)","color(0,0,0,255)","",""]
    log.tracef("The expanded row is: %s", str(row))
    return row

def fetchCharts(sfcRecipeDataShowProductionOnly, db):
    log.infof("Fetching the charts...")
    
    if sfcRecipeDataShowProductionOnly:
        SQL = "select ChartId, ChartPath, ChartResourceId from SfcChart where IsProduction = 1 order by ChartPath"
    else:
        SQL = "select ChartId, ChartPath, ChartResourceId from SfcChart order by ChartPath"
        
    pds = system.db.runPrepQuery(SQL, [], db)
    log.tracef("Fetched %d chart records...", len(pds))
    return pds

def fetchHierarchy(sfcRecipeDataShowProductionOnly, db=""):
    if sfcRecipeDataShowProductionOnly:
        SQL = "select * from SfcHierarchyView where IsProduction = 1 order by ChartPath"
    else:
        SQL = "select * from SfcHierarchyView order by ChartPath"

    pds = system.db.runQuery(SQL, db)
    return pds
    
def getChildren(chartId, hierarchyPDS):
    children = []
    log.tracef("Getting the children of chart: %s", str(chartId))
    for record in hierarchyPDS:
        if record["ChartId"] == chartId and record["ChildChartId"] not in children:
            children.append(record["ChildChartId"])
    log.tracef("The children of %s are %s", chartId, str(children))
    return children

# This version traverses and creates a list of strings
def fetchSfcTree(chartPDS, hierarchyPDS):
    
    def depthSearch(trees, depth, hierarchyPDS):
        log.tracef("------------")
        log.tracef("Searching depth %d, the trees are %s", depth, str(trees))

        foundChild = False
        newTrees = []
        for tree in trees:
            log.tracef("The tree is: %s", str(tree))
            ids = tree.split(",")
            node = ids[-1]
            log.tracef("The last node is: %s", node)
            children=getChildren(int(node), hierarchyPDS)
            if len(children) == 0 or depth > 100:
                if depth > 100: 
                    log.errorf("Error!, SFC Tree depth has exceeded 100 levels.  Pruning the tree at this level, please investigate for a possible loop in the branches near %s", node)
                    

                log.tracef("...there are no children!")
                newTrees.append(tree)
            else:
                log.tracef("The children are: %s", str(children))
                for child in children:
                    foundChild = True
                    newTree = "%s,%s" % (tree, child)
                    newTrees.append(newTree)
        log.tracef("The new trees are: %s", str(newTrees))
        return newTrees, foundChild
    
    # A root is any chart that is never a child of another chart.
    def isRoot(chartId, hierarchyPDS):
        for record in hierarchyPDS:
            if chartId == record["ChildChartId"]:
                return False
        return True
    # --------------------------
    
    # Get the roots
    log.info("Getting the root nodes...")
    trees = []
    for chartRecord in chartPDS:
        chartId = chartRecord["ChartId"]

        if isRoot(chartId, hierarchyPDS):
            trees.append(str(chartId))

    log.tracef("...the root nodes are: %s", str(trees))

    foundChild = True
    depth = 0
    while foundChild:
        trees, foundChild = depthSearch(trees, depth, hierarchyPDS)
        depth = depth + 1
    log.tracef("The trees are: %s", str(trees))

    return trees

'''
These methods have to do with the list of steps
'''

'''
This gets called in response to a node being selected in the SFC Chart Hierarchy tree.
'''
def refreshSteps(rootContainer, db):
    log.infof("%s.refreshSteps() - Updating the list of steps...", __name__)
    treeWidget = rootContainer.getComponent("Tree Container").getComponent("Tree View")
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    
    # First get the last node in the path
    chartPath = treeWidget.selectedPath
    log.infof("The raw selected path is: <%s>", chartPath)
    chartPath = chartPath[chartPath.rfind("/")+1:]
    
    # Now replace ":" with "/"
    chartPath = chartPath.replace('\\', '/')
    log.infof("The selected chart path is <%s>", chartPath)
    if chartPath == "" or chartPath == None:
        clearTable(stepTable)
        return
    
    SQL = "select chartId from SfcChart where chartPath = '%s'" % (chartPath)
    chartId = system.db.runScalarQuery(SQL) 
    log.infof("Fetched chart id: %s", str(chartId))
    if chartId == None:
        clearTable(stepTable)
        return
    
    SQL = " select S.StepName, T.StepType, S.StepId, "\
        "(select COUNT(*) from SfcRecipeData D where D.StepId = S.StepId) as myRefs "\
        " from SfcStep S, SfcStepType T "\
        " where S.StepTypeId = T.StepTypeId "\
        " and S.ChartId = %s order by stepName" % (str(chartId))
    
    pds = system.db.runQuery(SQL)

    stepTable.data = pds
    stepTable.selectedRow = -1


'''
This is used to format the tooltip for the Recipe Data table.  The description can get really long and I 
decided that the tooltop for the row should be the description, but if it is really long it needs to be word
wrapped.  The tooltip supports HTML.
'''
def tooltipFormatter(desc, lineLen=80):
    lines = []
    for i in xrange(0, len(desc), lineLen):
        lines.append(desc[i:i+lineLen])
    desc = "<HTML>" + "<br>".join(lines)
    return desc    
    
'''
Update the rightmost pane for a selection in the middle pane.
'''
def updateRecipeData(rootContainer, db=""):
    log.infof("Updating the recipe data table (%s)...", db)
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    recipeDataTable = rootContainer.getComponent("Recipe Data Container").getComponent("Recipe Data")
    
    if stepTable.selectedRow < 0:
        clearTable(recipeDataTable)
    else:
        ds = stepTable.data
        stepId = ds.getValueAt(stepTable.selectedRow, "StepId")
        
        SQL = "select * from SfcRecipeDataView where StepId = %s order by RecipeDataKey" % (str(stepId))
        pds = system.db.runQuery(SQL)

        ds = system.dataset.toDataSet(pds)
        row = 0
        for record in pds:
            desc = getRecipeDataDescription(record)
            ds = system.dataset.setValue(ds, row, "Description", desc)        
            row = row + 1
            
        recipeDataTable.data = ds


def getRecipeDataDescription(record):
    try:
        recipeDataId = record["RecipeDataId"]
        recipeDataType = record["RecipeDataType"]
        desc = record["Description"]
        log.tracef("Looking at %s - %s", recipeDataId, recipeDataType)
        
        if recipeDataType == "Simple Value":
            valuePDS = system.db.runQuery("select * from SfcRecipeDataSimpleValueView where recipeDataId = %d" % (recipeDataId))
            if len(valuePDS) == 1:
                valueRecord = valuePDS[0]
                desc = getValueDescriptionFromRecord(valueRecord, desc)
        elif recipeDataType == "Matrix":
            desc = getMatrixDescription(recipeDataId, desc)
        elif recipeDataType == "Array":
            desc = getArrayDescription(recipeDataId, desc)           
        elif recipeDataType == "Timer":
            desc = getTimerDescription(recipeDataId, desc)
        elif recipeDataType == "Recipe":
            desc = getRecipeDescription(recipeDataId, desc)
        elif recipeDataType == "Output":
            valuePDS = system.db.runQuery("select * from SfcRecipeDataOutputView where recipeDataId = %d" % (recipeDataId))
            if len(valuePDS) == 1:
                valueRecord = valuePDS[0]
                tag = valueRecord["Tag"]
                tag = tag[tag.rfind('/') + 1:]
                timing = valueRecord["Timing"]
                outputType = valueRecord["OutputType"]
                
                if desc == "":
                    desc = "Tag: %s, Type: %s, Timing: %s" % (tag, outputType, str(timing))
                else:
                    desc = "%s, Tag: %s, Type: %s, Timing: %s" % (desc, tag, outputType, str(timing))
                    
                desc = getOutputValueDescriptionFromRecord(valueRecord, desc)
        
        elif recipeDataType == "Output Ramp":
            valuePDS = system.db.runQuery("select * from SfcRecipeDataOutputRampView where recipeDataId = %d" % (recipeDataId))
            if len(valuePDS) == 1:
                valueRecord = valuePDS[0]
                tag = valueRecord["Tag"]
                tag = tag[tag.rfind('/') + 1:]
                timing = valueRecord["Timing"]
                outputType = valueRecord["OutputType"]
                rampTime = valueRecord["RampTimeMinutes"]
                
                if desc == "":
                    desc = "Tag: %s, Type: %s, Timing: %s" % (tag, outputType, str(timing))
                else:
                    desc = "%s, Tag: %s, Type: %s, Timing: %s, Ramp Time: %s" % (desc, tag, outputType, str(timing), str(rampTime))
                    
                desc = getOutputValueDescriptionFromRecord(valueRecord, desc)
        
        elif recipeDataType == "Input":
            valuePDS = system.db.runQuery("select * from SfcRecipeDataInputView where recipeDataId = %d" % (recipeDataId))
            if len(valuePDS) == 1:
                valueRecord = valuePDS[0]
                tag = valueRecord["Tag"]
                tag = tag[tag.rfind('/') + 1:]
                
                if desc == "":
                    desc = "Tag: %s" % (tag)
                else:
                    desc = "%s, Tag: %s" % (desc, tag)
                    
                desc = getInputValueDescriptionFromRecord(valueRecord, desc)
    except:
        errorDesc = catchError("%s.getRecipeDataDescription()" % (__name__))
        log.errorf(errorDesc)

    return desc

    
def getMatrixDescription(recipeDataId, desc):
    desc = ""
    pds = system.db.runQuery("Select * from SFcRecipeDataMatrixView where recipeDataId = %d" % (recipeDataId))
    if len(pds) == 1:
        record = pds[0]
        valueType = record["ValueType"]
        rows = record["Rows"]
        columns = record["Columns"]
        rowKey = record["RowIndexKeyName"]
        columnKey = record["ColumnIndexKeyName"]
        matrixDesc = "A %d X %d matrix: " % (rows, columns)
        
        if desc == "":
            desc = matrixDesc
        else:
            desc = "%s, %s" % (desc, matrixDesc)

        SQL = "select * from SfcRecipeDataMatrixElementView where RecipeDataId = %d order by RowIndex, ColumnIndex" % (recipeDataId)
        pdsValues = system.db.runQuery(SQL)
        lastRowIndex = -1
        txt = ""
        for valueRecord in pdsValues:
            rowIndex = valueRecord["RowIndex"]
            if valueType == "Float":
                val = valueRecord["FloatValue"]
                
            if rowIndex <> lastRowIndex:
                if txt == "":
                    txt = "(%s" % (str(val))
                else:
                    txt = "%s), (%s" % (txt, str(val))
            else:
                txt = "%s, %s" % (txt, str(val))
                
            lastRowIndex = rowIndex
        
        desc = desc + txt + ")"
        
        if rowKey != None:
            desc = "%s, row key: %s" % (desc, rowKey)
        
        if columnKey != None:
            desc = "%s, column key: %s" % (desc, columnKey)
    return desc

#
def getArrayDescription(recipeDataId, desc):
    pds = system.db.runQuery("Select * from SFcRecipeDataArrayView where recipeDataId = %d" % (recipeDataId))
    record = pds[0]
    valueType = record["ValueType"]
    key = record["KeyName"]

    SQL = "select * from SfcRecipeDataArrayElementView where RecipeDataId = %d order by ArrayIndex" % (recipeDataId)
    pdsValues = system.db.runQuery(SQL)
    numElements = len(pdsValues)

    txt = ""
    for valueRecord in pdsValues:

        if valueType == "Float":
            val = valueRecord["FloatValue"]
        elif valueType == "String":
            val = valueRecord["StringValue"]
        elif valueType == "Integer":
            val = valueRecord["IntegerValue"]
        elif valueType == "Boolean":
            val = valueRecord["BooleanValue"]
            
        if txt == "":
            txt = "(%s" % (str(val))
        else:
            txt = "%s, %s" % (txt, str(val))
    
    txt = txt + ")"

    if desc == "":
        desc = txt
    else:
        desc = "%s, %s" % (desc, txt)
    
    ''' If the array is keyed then append the name of the key '''    
    if key != None:
        desc = "%s, key: %s" % (desc, key)   

    return desc

#
def getTimerDescription(recipeDataId, desc):
    valuePDS = system.db.runQuery("Select * from SFcRecipeDataTimerView where recipeDataId = %d" % (recipeDataId))
    valueRecord = valuePDS[0]

    txt = "State: %s, Start time: %s" % (valueRecord["TimerState"], valueRecord["StartTime"])
    
    if desc == "":
        desc = txt
    else:
        desc = "%s, %s" % (desc, txt)    

    return desc

#
def getRecipeDescription(recipeDataId, desc):
    valuePDS = system.db.runQuery("Select * from SFcRecipeDataRecipeView where recipeDataId = %d" % (recipeDataId))
    valueRecord = valuePDS[0]

    txt = "Tag: %s, Value: %s" % (valueRecord["StoreTag"], str(valueRecord["RecommendedValue"]))

    if desc == "":
        desc = txt
    else:
        desc = "%s, %s" % (desc, txt)    

    return desc 

def getValueDescriptionFromRecord(record, desc):
    valueType = record["ValueType"]
    units = record["Units"]
    
    if valueType == "String":
        val = record["StringValue"]
    elif valueType == "Float":
        val = record["FloatValue"]
    elif valueType == "Integer":
        val = record["IntegerValue"]
    elif valueType == "Boolean":
        val = record["BooleanValue"]
        if val == 1:
            val = "True"
        else:
            val = "False"
    
    if desc == "":
        desc = "%s" % (str(val))
    else:
        desc = "%s, %s" % (desc, str(val))
    
    if units <> "" and units <> None:
        desc = "%s (%s)" % (desc, units)

    return desc

#
def getOutputValueDescriptionFromRecord(record, desc):
    valueType = record["ValueType"]
    units = record["Units"]
    
    if valueType == "String":
        val = record["OutputStringValue"]
    elif valueType == "Float":
        val = record["OutputFloatValue"]
    elif valueType == "Integer":
        val = record["OutputIntegerValue"]
    elif valueType == "Boolean":
        val = record["OutputBooleanValue"]
        if val == 1:
            val = "True"
        else:
            val = "False"
    
    if desc == "":
        desc = "%s" % (str(val))
    else:
        desc = "%s, %s" % (desc, str(val))
    
    if units <> "" and units <> None:
        desc = "%s (%s)" % (desc, units)

    return desc

#
def getInputValueDescriptionFromRecord(record, desc):
    valueType = record["ValueType"]
    units = record["Units"]
    
    if valueType == "String":
        val = record["PVStringValue"]
    elif valueType == "Float":
        val = record["PVFloatValue"]
    elif valueType == "Integer":
        val = record["PVIntegerValue"]
    elif valueType == "Boolean":
        val = record["PVBooleanValue"]
        if val == 1:
            val = "True"
        else:
            val = "False"
    
    if desc == "":
        desc = "%s" % (str(val))
    else:
        desc = "%s, %s" % (desc, str(val))
    
    if units <> "" and units <> None:
        desc = "%s (%s)" % (desc, units)

    return desc


def deleteRecipeData(rootContainer, db):
    log.infof("Deleting a recipe data...")

    recipeDataTable = rootContainer.getComponent("Recipe Data Container").getComponent("Recipe Data")
    
    if recipeDataTable.selectedRow < 0:
        system.gui.messageBox("Please select a row from the Recie Data table.")
        return
    
    ds = recipeDataTable.data
    recipeDataId = ds.getValueAt(recipeDataTable.selectedRow, "RecipeDataId")
    
    recipeDataType = ds.getValueAt(recipeDataTable.selectedRow, "RecipeDataType")
    
    # Get the value ids before we delete the data
    valueIds = []
    if recipeDataType == SIMPLE_VALUE:
        SQL = "select ValueId from SfcRecipeDataSimpleValue where recipeDataId = %d" % (recipeDataId)
        valueId = system.db.runScalarQuery(SQL)
        valueIds.append(valueId)
    elif recipeDataType == OUTPUT:
        SQL = "select OutputValueId, TargetValueId, PVValueId from SfcRecipeDataOutput where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL)
        record = pds[0]
        valueIds.append(record["OutputValueId"])
        valueIds.append(record["TargetValueId"])
        valueIds.append(record["PVValueId"])
    elif recipeDataType == INPUT:
        SQL = "select TargetValueId, PVValueId from SfcRecipeDataInput where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL)
        record = pds[0]
        valueIds.append(record["TargetValueId"])
        valueIds.append(record["PVValueId"])
    elif recipeDataType == ARRAY:
        SQL = "select ValueId from SfcRecipeDataArrayElement where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL)
        for record in pds:
            valueIds.append(record["ValueId"])
        SQL = "delete from SfcRecipeDataArrayElement where RecipeDataId = %d" % (recipeDataId)
        rows = system.db.runUpdateQuery(SQL)
        log.infof("Deleted %d rows from SfcRecipeDataArrayElement...", rows)
    elif recipeDataType == MATRIX:
        SQL = "select ValueId from SfcRecipeDataMatrixElement where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL)
        for record in pds:
            valueIds.append(record["ValueId"])
        SQL = "delete from SfcRecipeDataMatrixElement where RecipeDataId = %d" % (recipeDataId)
        rows = system.db.runUpdateQuery(SQL)
        log.infof("Deleted %d rows from SfcRecipeDataMatrixElement...", rows)
    
    # The recipe data tables all have cascade delete foreign keys so we just need to delete from the main table
    SQL = "delete from SfcRecipeData where RecipeDataId = %d" % (recipeDataId)
    system.db.runUpdateQuery(SQL)
    
    # Now delete the values
    for valueId in valueIds:
        SQL = "delete from SfcRecipeDataValue where ValueId = %d" % (valueId)
        system.db.runUpdateQuery(SQL)
    
    ''' Update the table '''
    updateRecipeData(rootContainer, db)


'''
This is just a good text book example of recursion.
'''    
def factorial(n):
    print("factorial has been called with n = " + str(n))
    if n == 1:
        return 1
    else:
        res = n * factorial(n-1)
        print("intermediate result for ", n, " * factorial(" ,n-1, "): ",res)
        return res