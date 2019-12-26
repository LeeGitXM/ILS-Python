'''
Created on Feb 10, 2017 

@author: phass
'''
import system
from ils.common.config import getDatabaseClient
from ils.common.windowUtil import clearTable, clearTree
from ils.sfc.recipeData.constants import ARRAY, GROUP, INPUT, MATRIX, OUTPUT, SIMPLE_VALUE, TIMER
from ils.common.error import catchError
from ils.common.config import getTagProviderClient
from sys import path
from __builtin__ import True
from ils.sfc.common.constants import SQL
log=system.util.getLogger("com.ils.sfc.recipeBrowser")

#treeMode = "chartName"
treeMode = "fullPath"

LIBRARY_ICON = "Builtin/icons/16/copy.png"

'''
Populate the left pane which has the logical view of the SFC call tree, clear the other two panes.
'''
def internalFrameOpened(rootContainer, db):
    log.infof("In %s.internalFrameOpened()", __name__) 
    updateSfcTree(rootContainer, db)
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    clearTable(stepTable)
    recipeDataTree = rootContainer.getComponent("Recipe Data Container").getComponent("Tree View")
    clearTree(recipeDataTree)

'''
This is called whenever the windows gains focus.  his happens as part of the noral workflow of creating or editing recipe data
so update the recipe data table to reflect the edit.
'''
def internalFrameActivated(rootContainer, db):
    log.infof("In %s.internalFrameActivated()", __name__)
#    refreshSteps(rootContainer, db)
    updateRecipeDataTree(rootContainer, db)

def updateSfcTree(rootContainer, db):
    log.infof("In %s.updateSfcTree(), Updating the SFC Tree Widget...", __name__)
    tagProvider = getTagProviderClient()
    sfcRecipeDataShowProductionOnly = system.tag.read("[%s]Configuration/SFC/sfcRecipeDataShowProductionOnly" % (tagProvider)).value

    ''' I can use this for testing '''
    chartPath = 'A%'
    chartPath = "%"

    hierarchyPDS = fetchHierarchy(chartPath, sfcRecipeDataShowProductionOnly, db)
    hierarchyHandlerPDS = fetchHierarchyHandler(chartPath, sfcRecipeDataShowProductionOnly, db)
    chartPDS = fetchCharts(chartPath, sfcRecipeDataShowProductionOnly, db)
    trees = fetchSfcTree(chartPDS, hierarchyPDS, hierarchyHandlerPDS)
    
    ''' 
    Create a dictionary of charts where the chartId is the key. Replace the path delimiter (a forward slash) 
    with a backwards slash which needs to be escaped with another backwards slash.
    '''
    chartDict = {}
    for record in chartPDS:
        chartId=record["ChartId"]
        chartPath=record["ChartPath"]
        
        # Chart Paths use the '/' to indicate the path structure, but the tree widget interprets that as a child.  I want to treat
        # the chart path as the name so replace "/" with ":"
        chartDict[chartId] = chartPath.replace('/',' \\ ')

    '''
    Now take the SFC tree model and format it for the tree widget.
    I think the way that we need to prepare data for the tree is widget is that we need a record for each leaf node.
    '''
    log.tracef("The chart dictionary is %s", str(chartDict))    
    rows=[]
    for tree in trees:
        row = expandRow(tree, chartDict, hierarchyPDS, hierarchyHandlerPDS)
        rows.append(row)

    header = ["path", "text", "icon", "background", "foreground", "tooltip", "border", "selectedText", "selectedIcon", "selectedBackground", "selectedForeground", "selectedTooltip", "selectedBorder"]
    ds = system.dataset.toDataSet(header, rows)
    treeWidget=rootContainer.getComponent("Tree Container").getComponent("Tree View")
    treeWidget.data = ds

    
def expandRow(tree, chartDict, hierarchyPDS, hierarchyHandlerPDS): 
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
    fullPath = chartDict.get(int(token),"Unknown")
    
    refs = countChartReferences(int(token), hierarchyPDS, hierarchyHandlerPDS)
    print " **** %s has %d references ****" % (fullPath, refs)
    if refs > 1:
        icon = LIBRARY_ICON
    else:
        icon = "default"
    
    chartName = fullPath[fullPath.rfind("\\")+1:]
    log.tracef("%s  --  %s  --  %s", path, fullPath, chartName)

    if treeMode == "fullPath":
        row = [path,fullPath,icon,"color(255,255,255,255)","color(0,0,0,255)",fullPath,"","",icon,"color(250,214,138,255)","color(0,0,0,255)","",""]
    else:
        row = [path,chartName,icon,"color(255,255,255,255)","color(0,0,0,255)",fullPath,"","",icon,"color(250,214,138,255)","color(0,0,0,255)","",""]
        
    log.tracef("The expanded row is: %s", str(row))
    return row

def countChartReferences(token, hierarchyPDS, hierarchyHandlerPDS):
    refs = 0
    for record in hierarchyPDS:
        if record["ChildChartId"] == token:
            refs = refs + 1

    return refs

def fetchCharts(chartPath, sfcRecipeDataShowProductionOnly, db):
    log.infof("Fetching the charts...")
    
    if sfcRecipeDataShowProductionOnly:
        SQL = "select ChartId, ChartPath, ChartResourceId from SfcChart where IsProduction = 1 and chartPath like '%s' order by ChartPath" % (chartPath)
    else:
        SQL = "select ChartId, ChartPath, ChartResourceId from SfcChart where chartPath like '%s' order by ChartPath" % (chartPath)
        
    pds = system.db.runPrepQuery(SQL, [], db)
    log.tracef("Fetched %d chart records...", len(pds))
    return pds

def fetchHierarchy(chartPath, sfcRecipeDataShowProductionOnly, db=""):
    if sfcRecipeDataShowProductionOnly:
        SQL = "select * from SfcHierarchyView where IsProduction = 1 and chartPath like '%s' order by ChartPath" % (chartPath)
    else:
        SQL = "select * from SfcHierarchyView where chartPath like '%s' order by ChartPath" % (chartPath)

    print SQL
    pds = system.db.runQuery(SQL, db)
    return pds

def fetchHierarchyHandler(chartPath, sfcRecipeDataShowProductionOnly, db=""):
    if sfcRecipeDataShowProductionOnly:
        SQL = "select * from SfcHierarchyHandlerView where IsProduction = 1 and chartPath like '%s' order by ChartPath"  % (chartPath)
    else:
        SQL = "select * from SfcHierarchyHandlerView where chartPath like '%s' order by ChartPath"  % (chartPath)

    pds = system.db.runQuery(SQL, db)
    return pds
    
def getChildren(chartId, hierarchyPDS, hierarchyHandlerPDS):
    children = []
    log.tracef("Getting the children of chart: %s", str(chartId))
    
    for record in hierarchyPDS:
        if record["ChartId"] == chartId and record["ChildChartId"] not in children:
            children.append(record["ChildChartId"])
            
    for record in hierarchyHandlerPDS:
        if record["ChartId"] == chartId and record["HandlerChartId"] not in children:
            children.append(record["HandlerChartId"])
            
    log.tracef("The children of %s are %s", chartId, str(children))
    return children

# This version traverses and creates a list of strings
def fetchSfcTree(chartPDS, hierarchyPDS, hierarchyHandlerPDS):
    
    def depthSearch(trees, depth, hierarchyPDS, hierarchyHandlerPDS):
        log.tracef("------------")
        log.tracef("Searching depth %d, the trees are %s", depth, str(trees))

        foundChild = False
        newTrees = []
        for tree in trees:
            log.tracef("The tree is: %s", str(tree))
            ids = tree.split(",")
            node = ids[-1]
            log.tracef("The last node is: %s", node)
            children=getChildren(int(node), hierarchyPDS, hierarchyHandlerPDS)
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
    def isRoot(chartId, hierarchyPDS, hierarchyHandlerPDS):
        for record in hierarchyPDS:
            if chartId == record["ChildChartId"]:
                return False
            
        for record in hierarchyHandlerPDS:
            if chartId == record["HandlerChartId"]:
                return False

        return True
    # --------------------------
    
    # Get the roots
    log.infof("In %s.fetchSfcTree() - Getting the root nodes...", __name__)
    trees = []
    for chartRecord in chartPDS:
        chartId = chartRecord["ChartId"]

        if isRoot(chartId, hierarchyPDS, hierarchyHandlerPDS):
            trees.append(str(chartId))

    log.tracef("...the root nodes are: %s", str(trees))

    foundChild = True
    depth = 0
    while foundChild:
        trees, foundChild = depthSearch(trees, depth, hierarchyPDS, hierarchyHandlerPDS)
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
    
    chartId = getChartIdForSelectedNode(treeWidget, db)
    if chartId == None:
        clearTable(stepTable)
        return
    
    SQL = " select S.StepName, T.StepType, S.StepId, "\
        "(select COUNT(*) from SfcRecipeData D where D.StepId = S.StepId) as myRefs "\
        " from SfcStep S, SfcStepType T "\
        " where S.StepTypeId = T.StepTypeId "\
        " and S.ChartId = %s order by stepName" % (str(chartId))
    
    pds = system.db.runQuery(SQL, db)

    stepTable.data = pds
    stepTable.selectedRow = -1

def getChartIdForSelectedNode(treeWidget, db):
    # First get the last node in the path
    chartPath = treeWidget.selectedPath
    log.infof("The raw selected path is: <%s>", chartPath)
    chartPath = chartPath[chartPath.rfind("/")+1:]
    
    # Now replace ":" with "/"
    chartPath = chartPath.replace(' \\ ', '/')
    log.infof("The selected chart path is <%s>", chartPath)
    if chartPath == "" or chartPath == None:
        return None
    
    SQL = "select chartId from SfcChart where chartPath = '%s'" % (chartPath)
    chartId = system.db.runScalarQuery(SQL, db) 
    log.infof("Fetched chart id: %s", str(chartId))
    if chartId == None:
        return None
    
    return chartId


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


def updateRecipeDataTree(rootContainer, db=""):
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    recipeDataTree = rootContainer.getComponent("Recipe Data Container").getComponent("Tree View")
    
    ''' Unselect anything that might be selected '''
    recipeDataTree.selectedPath = ""
    
    if stepTable.selectedRow < 0:
        log.infof("Clearing the recipe data tree...")
        clearTree(recipeDataTree)
        setTreeButtons(recipeDataTree, False, False, False)
    else:
        log.infof("In %s.updateRecipeDataTree() - Updating the recipe data tree...", __name__)
        setTreeButtons(recipeDataTree, False, True, False)
        ds = stepTable.data
        stepId = ds.getValueAt(stepTable.selectedRow, "StepId")
        
        '''
        Fetch the folders...
        '''
        log.tracef("Fetching folders...")
        SQL = "Select * from SfcRecipeDataFolder where StepId = %s order by ParentRecipeDataFolderId" % (str(stepId))
        folderPDS = system.db.runQuery(SQL, db)
        folderDataset = system.dataset.toDataSet(folderPDS)

        '''
        Fetch the Recipe Data...
        '''
        log.tracef("Fetching recipe data...")
        SQL = "select * from SfcRecipeDataView where StepId = %s order by RecipeDataKey" % (str(stepId))
        pds = system.db.runQuery(SQL, db)

        ds = system.dataset.toDataSet(pds)
        row = 0
        
        ''' Now update the Tree '''
        icon = "default"
        background = "color(255,255,255,255"
        foreground = "color(0,0,0,255)"
        tooltip = ""
        border = ""
        selectedText = ""
        selectedIcon = "default"
        selectedBackground = "color(250,214,138,255"
        selectedForeground = "color(0,0,0,255)"
        selectedTooltip = ""
        selectedBorder = ""
        closedFolderIcon = "Custom/folderClosed16.png"
        
        vals = []
        header = ["path", "text", "icon", "background", "foreground", "tooltip", "border", "selectedText", "selectedIcon", "selectedBackground", "selectedForeground", 
                  "selectedTooltip", "selectedBorder"]
        
        log.tracef("Adding recipe data to the tree...")
        pathsUsedByData = []
        for record in pds:
            key = record["RecipeDataKey"]
            log.tracef("   Adding %s", key)
            desc = getRecipeDataDescription(record, db)
            key = "%s :: %s" % (key, desc)
            folderId = record["RecipeDataFolderId"]
            if folderId == None:
                log.tracef("   ... this goes in the root folder (not really a folder)")
                val = ["",key,icon,background,foreground,tooltip,border,selectedText,selectedIcon,selectedBackground,selectedForeground,selectedTooltip,selectedBorder]   
            else:
                path = findRecipeParent(folderId, key, folderPDS)
                pathsUsedByData.append(path)
                log.tracef("   ...this is in a folder...")
                val = [path,key,icon,background,foreground,tooltip,border,selectedText,selectedIcon,selectedBackground,selectedForeground,selectedTooltip,selectedBorder]
     
            vals.append(val)
            row = row + 1
        
        log.tracef("Adding folders to the tree...")
        paths = []
        for record in folderPDS:
            path = findParent(folderPDS, record)
            paths.append(path)
        
        ''' Scrub the paths so that wholly contained paths are eliminated '''
        paths = scrubPaths(paths, pathsUsedByData)
        
        '''
        Take the scrubbed paths and add a record to the tree dataset.  If the folder is a root folder, then the tree needs the path to be empty and the folder
        name goes in the txt.  If the folder is a subfolder, then the last folder becomes the txt and the rest is the path.
        '''
        for path in paths:
            tokens = path.split("/")
            if len(tokens) == 1:
                val = ["",path,closedFolderIcon,background,foreground,tooltip,border,selectedText,closedFolderIcon,selectedBackground,selectedForeground,selectedTooltip,selectedBorder]
                vals.append(val)
            else:
                path = "/".join(tokens[:len(tokens)-1])
                txt = tokens[len(tokens)-1]
                val = [path,txt,closedFolderIcon,background,foreground,tooltip,border,selectedText,closedFolderIcon,selectedBackground,selectedForeground,selectedTooltip,selectedBorder]
                vals.append(val)
        
        log.tracef("The tree values are: %s", str(vals))
        ds = system.dataset.toDataSet(header, vals)
        recipeDataTree.data = ds

def setTreeButtons(recipeDataTree, editState, addState, deleteState):
    log.infof("In %s.setTreeButtons...", __name__)
    recipeDataTree.enableEditButton = editState
    recipeDataTree.enableAddButton = addState
    recipeDataTree.enableDeleteButton = deleteState

'''
Given a specific folder, and a dataset of the entire folder hierarchy, find the full path for a given folder.
'''
def findRecipeParent(parentId, key, folderPDS):
    log.tracef("=====================")
    log.tracef("Finding the full path for %s - %d", key, parentId)
    path = ""

    while parentId != None:
        
        for record in folderPDS:
            if record["RecipeDataFolderId"] == parentId:
                log.tracef("Found the parent")
                if path == "":
                    path = record["RecipeDataKey"]
                else:
                    path = "%s/%s" % (record["RecipeDataKey"], path)
                parentId = record["ParentRecipeDataFolderId"]
                log.tracef("The new parent id is: %s", str(parentId))

    log.tracef("The parent path is: %s", path)
    return path

'''
Given a specific folder, and a dataset of the entire folder hierarchy, find the full path for a given folder.
'''
def findParent(folderPDS, record):
    log.tracef("------------------")
    path = record["RecipeDataKey"]
    parent = record["ParentRecipeDataFolderId"]
    log.tracef("Finding the path for %s", path)
    
    while parent != None:
        
        for record in folderPDS:
            if record["RecipeDataFolderId"] == parent:
                log.tracef("Found the parent")
                path = "%s/%s" % (record["RecipeDataKey"], path)
                parent = record["ParentRecipeDataFolderId"]
                log.tracef("The new parent id is: %s", parent)

    log.tracef("The path is: %s", path)
    return path

'''
Scrub the list of paths to remove paths that are wholly contained in another path.
'''
def scrubPaths(paths, pathsUsedByData):
    log.tracef("In %s.scrubPaths() - Scrubbing...", __name__)
    scrubbedPaths = []
    
    for path in paths:
        log.tracef("    %s", path)
        whollyContained = False
        for parentPath in paths:
            if path != parentPath and parentPath.find(path) >= 0:
                log.tracef("       %s is wholly contained by %s", path, parentPath)
                whollyContained = True
                break

        if not(whollyContained):
            scrubbedPaths.append(path)
    
    log.tracef("The scrubbed paths are: %s", str(scrubbedPaths))
    return scrubbedPaths

def getRecipeDataDescription(record, db):
    try:
        recipeDataId = record["RecipeDataId"]
        recipeDataType = record["RecipeDataType"]
        desc = record["Description"]
        log.tracef("Looking at %s - %s", recipeDataId, recipeDataType)
        
        if recipeDataType == "Simple Value":
            SQL = "select * from SfcRecipeDataSimpleValueView where recipeDataId = %d" % (recipeDataId)
            valuePDS = system.db.runQuery(SQL, db)
            if len(valuePDS) == 1:
                valueRecord = valuePDS[0]
                desc = getValueDescriptionFromRecord(valueRecord, desc)
        elif recipeDataType == "Matrix":
            desc = getMatrixDescription(recipeDataId, desc, db)
        elif recipeDataType == "Array":
            desc = getArrayDescription(recipeDataId, desc, db)           
        elif recipeDataType == "Timer":
            desc = getTimerDescription(recipeDataId, desc, db)
        elif recipeDataType == "Recipe":
            desc = getRecipeDescription(recipeDataId, desc, db)
        elif recipeDataType == "Output":
            SQL = "select * from SfcRecipeDataOutputView where recipeDataId = %d" % (recipeDataId)
            valuePDS = system.db.runQuery(SQL, db)
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
                    
                desc = getOutputValueDescriptionFromRecord(valueRecord, desc, "an output")
        
        elif recipeDataType == "Output Ramp":
            SQL = "select * from SfcRecipeDataOutputRampView where recipeDataId = %d" % (recipeDataId)
            valuePDS = system.db.runQuery(SQL, db)
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
                    
                desc = getOutputValueDescriptionFromRecord(valueRecord, desc, "an output ramp")
        
        elif recipeDataType == "Input":
            SQL = "select * from SfcRecipeDataInputView where recipeDataId = %d" % (recipeDataId)
            valuePDS = system.db.runQuery(SQL, db)
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

    
def getMatrixDescription(recipeDataId, desc, db):
    desc = ""
    SQL = "Select * from SFcRecipeDataMatrixView where recipeDataId = %d" % (recipeDataId)
    pds = system.db.runQuery(SQL, db)
    if len(pds) == 1:
        record = pds[0]
        valueType = record["ValueType"]
        rows = record["Rows"]
        columns = record["Columns"]
        rowKey = record["RowIndexKeyName"]
        columnKey = record["ColumnIndexKeyName"]
        matrixDesc = "A %d X %d matrix: " % (rows, columns)
        
        if desc == "":
            desc = "a matrix, %s" % (matrixDesc)
        else:
            desc = "a matrix, %s, %s" % (desc, matrixDesc)

        SQL = "select * from SfcRecipeDataMatrixElementView where RecipeDataId = %d order by RowIndex, ColumnIndex" % (recipeDataId)
        pdsValues = system.db.runQuery(SQL, db)
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
def getArrayDescription(recipeDataId, desc, db):
    SQL = "Select * from SFcRecipeDataArrayView where recipeDataId = %d" % (recipeDataId)
    pds = system.db.runQuery(SQL, db)
    record = pds[0]
    valueType = record["ValueType"]
    key = record["KeyName"]

    SQL = "select * from SfcRecipeDataArrayElementView where RecipeDataId = %d order by ArrayIndex" % (recipeDataId)
    pdsValues = system.db.runQuery(SQL, db)
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
        desc = "an array, %s" % (txt)
    else:
        desc = "an array, %s, %s" % (desc, txt)
    
    ''' If the array is keyed then append the name of the key '''    
    if key != None:
        desc = "%s, key: %s" % (desc, key)   

    return desc

#
def getTimerDescription(recipeDataId, desc, db):
    SQL = "Select * from SFcRecipeDataTimerView where recipeDataId = %d" % (recipeDataId)
    valuePDS = system.db.runQuery(SQL, db)
    valueRecord = valuePDS[0]

    txt = "State: %s, Start time: %s" % (valueRecord["TimerState"], valueRecord["StartTime"])
    
    if desc == "":
        desc = "a timer, %s" % (txt)
    else:
        desc = "a timer, %s, %s" % (desc, txt)    

    return desc

#
def getRecipeDescription(recipeDataId, desc, db):
    SQL = "Select * from SFcRecipeDataRecipeView where recipeDataId = %d" % (recipeDataId)
    valuePDS = system.db.runQuery(SQL, db)
    valueRecord = valuePDS[0]

    txt = "Tag: %s, Value: %s" % (valueRecord["StoreTag"], str(valueRecord["RecommendedValue"]))

    if desc == "":
        desc = "a recipe, %s" % (txt)
    else:
        desc = "a recipe, %s, %s" % (desc, txt)    

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
        desc = "a simple value, %s" % (str(val))
    else:
        desc = "a simple value, %s, %s" % (desc, str(val))
    
    if units <> "" and units <> None:
        desc = "%s (%s)" % (desc, units)

    return desc

#
def getOutputValueDescriptionFromRecord(record, desc, recipeDesc):
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
        desc = "%s, %s" % (recipeDesc, str(val))
    else:
        desc = "%s, %s, %s" % (recipeDesc, desc, str(val))

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
        desc = "an input, %s" % (str(val))
    else:
        desc = "an input, %s, %s" % (desc, str(val))
    
    if units <> "" and units <> None:
        desc = "%s (%s)" % (desc, units)

    return desc


def deleteCallback(event):
    log.infof("Deleting a recipe data...")
    db = getDatabaseClient()
    rootContainer = event.source.parent.parent

    recipeDataTree = rootContainer.getComponent("Recipe Data Container").getComponent("Tree View")
    path = recipeDataTree.selectedPath
    
    if path == "":
        system.gui.messageBox("Please select a row from the Recipe Data tree.")
        return
    
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    selectedRow = stepTable.selectedRow
    log.tracef("The selected row is: %d", selectedRow)
    stepDs = stepTable.data
    stepId = stepDs.getValueAt(selectedRow,"StepId")
    log.tracef("The step id is: %s", str(stepId))
    
    recipeDataKey, recipeDataType, recipeDataId = fetchRecipeInfo(stepId, path, db)
    
    log.tracef("Recipe Data Type: %s, Recipe Data id: %s", recipeDataType, str(recipeDataId))
    
    if recipeDataType == GROUP:
        log.tracef("Deleting a group...")
        deleteRecipeDataGroup(recipeDataId, db)
    else:
        deleteRecipeData(recipeDataType, recipeDataId, db)
    
    ''' Update the recipe data Tree '''
    updateRecipeDataTree(rootContainer, db)


def deleteRecipeDataGroup(recipeDataFolderId, db):
    # Get the value ids before we delete the data
    embeddedFolderIds = fetchEmbeddedFolders(recipeDataFolderId, db)
    log.tracef("The embedded folder ids are: %s", str(embeddedFolderIds))
    
    ''' First delete all of the recipe data in the folders '''
    SQL = "select RecipeDataKey, RecipeDataId, RecipeDataType from SfcRecipeDataView where RecipeDataFolderId in (%s)" % (",".join(str(s) for s in embeddedFolderIds))
    pds = system.db.runQuery(SQL, db)
    
    if len(embeddedFolderIds) > 1 or len(pds) > 0:
        confirmed = system.gui.confirm("This will delete all subfolders and embeded recipe data, are you sure you want to continue?")
        if not(confirmed):
            return
        
    for record in pds:
        log.tracef("Delete %s-%s-%s", record["RecipeDataKey"], record["RecipeDataType"], record["RecipeDataId"])
        deleteRecipeData(record["RecipeDataType"], record["RecipeDataId"], db)
        
    ''' now delete all of the folders '''
    for folderId in embeddedFolderIds:
        log.infof("Deleting a recipe data folder with id: %d", folderId)
        SQL = "delete from SfcRecipeDataFolder where RecipeDataFolderId = %d" % (folderId)
        system.db.runUpdateQuery(SQL, db)

def fetchEmbeddedFolders(recipeDataFolderId, db):
    newFolderIds = recipeDataFolderId
    folderIds = [recipeDataFolderId]
    while newFolderIds != "":
        log.tracef("Looking for subfolders of <%s>...", str(newFolderIds)) 
        SQL = "select RecipeDataFolderId from SfcRecipeDataFolder where ParentRecipeDataFolderId in (%s)" % (newFolderIds)
        print SQL
        pds = system.db.runQuery(SQL, db)
        ids = []
        for record in pds:
            folderIds.append(record["RecipeDataFolderId"])
            ids.append(str(record["RecipeDataFolderId"]))
        newFolderIds = ",".join(ids)
        log.tracef("...the subfolders are <%s>!", newFolderIds)

    return folderIds

def deleteRecipeData(recipeDataType, recipeDataId, db):
    # Get the value ids before we delete the data
    valueIds = []
    if recipeDataType == SIMPLE_VALUE:
        SQL = "select ValueId from SfcRecipeDataSimpleValue where recipeDataId = %d" % (recipeDataId)
        valueId = system.db.runScalarQuery(SQL, db)
        valueIds.append(valueId)
    elif recipeDataType == OUTPUT:
        SQL = "select OutputValueId, TargetValueId, PVValueId from SfcRecipeDataOutput where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueIds.append(record["OutputValueId"])
        valueIds.append(record["TargetValueId"])
        valueIds.append(record["PVValueId"])
    elif recipeDataType == INPUT:
        SQL = "select TargetValueId, PVValueId from SfcRecipeDataInput where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueIds.append(record["TargetValueId"])
        valueIds.append(record["PVValueId"])
    elif recipeDataType == ARRAY:
        SQL = "select ValueId from SfcRecipeDataArrayElement where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        for record in pds:
            valueIds.append(record["ValueId"])
        SQL = "delete from SfcRecipeDataArrayElement where RecipeDataId = %d" % (recipeDataId)
        rows = system.db.runUpdateQuery(SQL, db)
        log.infof("Deleted %d rows from SfcRecipeDataArrayElement...", rows)
    elif recipeDataType == MATRIX:
        SQL = "select ValueId from SfcRecipeDataMatrixElement where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        for record in pds:
            valueIds.append(record["ValueId"])
        SQL = "delete from SfcRecipeDataMatrixElement where RecipeDataId = %d" % (recipeDataId)
        rows = system.db.runUpdateQuery(SQL, db)
        log.infof("Deleted %d rows from SfcRecipeDataMatrixElement...", rows)
    
    # The recipe data tables all have cascade delete foreign keys so we just need to delete from the main table
    log.infof("Deleting a %s with id: %d", recipeDataType, recipeDataId)
    SQL = "delete from SfcRecipeData where RecipeDataId = %d" % (recipeDataId)
    system.db.runUpdateQuery(SQL, db)
    
    # Now delete the values
    for valueId in valueIds:
        SQL = "delete from SfcRecipeDataValue where ValueId = %d" % (valueId)
        system.db.runUpdateQuery(SQL, db)






def editCallbackForDoubleClick(event):
    editCallback(event)
    
    '''
    db = getDatabaseClient()
    container = event.source.parent
    tree = container.getComponent("Tree View")
    path = tree.selectedPath
    
    log.infof("In %s.editCallbackForDoubleClick() - The path is: %s", __name__, path)
    
    stepTable = container.parent.getComponent("Step Container").getComponent("Steps")
    selectedRow = stepTable.selectedRow
    log.infof("The selected row is: %s", str(selectedRow))
    stepDs = stepTable.data
    stepId = stepDs.getValueAt(selectedRow,"StepId")
    log.infof("The step id is: %s", str(stepId))
    
    recipeDataKey, recipeDataType, recipeDataId = fetchRecipeInfo(stepId, path, db)
    recipeDataFolderId = -1
    
    log.infof("The recipe data id is: %s", str(recipeDataId))
    window = system.nav.openWindowInstance('SFC/RecipeDataEditor', {'stepId':stepId, 'recipeDataType':recipeDataType, 'recipeDataId':recipeDataId, 'recipeDataKey':recipeDataKey, "recipeDataFolderId":recipeDataFolderId})
    system.nav.centerWindow(window)
    '''

            
def editCallback(event):
    db = getDatabaseClient()
    container = event.source.parent
    tree = container.getComponent("Tree View")
    path = tree.selectedPath
    
    log.infof("In %s.editCallback() - The path is: %s", __name__, path)
    
    stepTable = container.parent.getComponent("Step Container").getComponent("Steps")
    selectedRow = stepTable.selectedRow
    log.infof("The selected row is: %s", str(selectedRow))
    stepDs = stepTable.data
    stepId = stepDs.getValueAt(selectedRow,"StepId")
    log.infof("The step id is: %s", str(stepId))
    
    recipeDataKey, recipeDataType, recipeDataId = fetchRecipeInfo(stepId, path, db)
    recipeDataFolderId = -1
    
    log.infof("The recipe data id is: %s", str(recipeDataId))
    window = system.nav.openWindowInstance('SFC/RecipeDataEditor', {'stepId':stepId, 'recipeDataType':recipeDataType, 'recipeDataId':recipeDataId, 'recipeDataKey':recipeDataKey, "recipeDataFolderId":recipeDataFolderId})
    system.nav.centerWindow(window)            

def addCallback(event):
    log.infof("In %s.addCallback()...", __name__)
    db = getDatabaseClient()
    rootContainer = event.source.parent.parent
    table = rootContainer.getComponent("Step Container").getComponent("Steps")
    ds = table.data
    row = table.selectedRow
    stepId = ds.getValueAt(row,"StepId")
    
    tree = rootContainer.getComponent("Recipe Data Container").getComponent("Tree View")
    path = tree.selectedPath
    
    if path <> "":
        tokens = path.split("/")
        SQL = "Select * from SfcRecipeDataFolder where StepId = %s order by ParentRecipeDataFolderId" % (str(stepId))
        folderPDS = system.db.runQuery(SQL, db)
        isFolder, recipeDataFolderId = fetchFolderId(folderPDS, tokens)
        
        if not(isFolder):
            print "ERROR: expected the path to reference a folder"
    else:
        recipeDataFolderId = -99

    window = system.nav.openWindow('SFC/RecipeDataTypeChooser', {'stepId' : stepId, 'recipeDataFolderId':recipeDataFolderId})
    system.nav.centerWindow(window)

def fetchRecipeInfo(stepId, path, db):
    print "Fetching recipe info for: ", path
    pos = path.find(" :: ")
    if pos > 0:
        path = path[:path.find(" :: ")]
        print "The stripped path is <%s>" % (path)
    
    tokens = path.split("/")
    
    if len(tokens) == 1:
        log.tracef("The path <%s> has one token, it is either a root folder or data in the root...", path)
        SQL = "select * from SfcRecipeDataView where StepId = %s and RecipeDataKey = '%s' and RecipeDataFolderId is NULL" % (str(stepId), path)
        log.tracef(SQL)
        pds = system.db.runQuery(SQL, db)
        
        if len(pds) == 1:
            log.tracef("...it is DATA!")
            record = pds[0]
            recipeDataKey = path
            recipeDataType = record["RecipeDataType"]
            recipeDataId = record["RecipeDataId"]
        else:
            log.tracef("...it isn't data...")
            SQL = "Select * from SfcRecipeDataFolder where StepId = %s order by ParentRecipeDataFolderId" % (str(stepId))
            folderPDS = system.db.runQuery(SQL, db)

            isFolder, recipeDataFolderId = fetchFolderId(folderPDS, tokens)
        
            if isFolder:
                log.tracef("...it is a FOLDER!")
                recipeDataKey = tokens[len(tokens) - 1]
                recipeDataType = GROUP
                recipeDataId = recipeDataFolderId
            else:
                print "****** ERROR ********"
    else:
        log.tracef("Fetching folders...")
        SQL = "Select * from SfcRecipeDataFolder where StepId = %s order by ParentRecipeDataFolderId" % (str(stepId))
        folderPDS = system.db.runQuery(SQL, db)
        isFolder, recipeDataFolderId = fetchFolderId(folderPDS, tokens)
        
        if isFolder:
            recipeDataKey = tokens[len(tokens) - 1]
            recipeDataType = GROUP
            recipeDataId = recipeDataFolderId
        else:
            recipeDataKey = tokens[len(tokens) - 1]
            SQL = "Select RecipeDataType, RecipeDataId from sfcRecipeDataView where RecipeDataKey = '%s' and RecipeDataFolderId = %s" % (recipeDataKey, recipeDataFolderId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                print "ERROR"
            record = pds[0]
            recipeDataType = record["RecipeDataType"]
            recipeDataId = record["RecipeDataId"]
    
    return recipeDataKey, recipeDataType, recipeDataId

def fetchFolderId(folderPDS, tokens):
    parentRecipeDataFolderId = None
    for token in tokens:
        log.tracef("Looking for %s", token)
        isFolder = False
        for record in folderPDS:
            if token == record["RecipeDataKey"] and record["ParentRecipeDataFolderId"] == parentRecipeDataFolderId:
                parentRecipeDataFolderId = record["RecipeDataFolderId"]
                isFolder = True
    
    if isFolder:
        log.tracef("The last token is a folder")
    else:
        log.tracef("The last token is data")
        
    return isFolder, parentRecipeDataFolderId

def mousePressedCallbackForTree(event):
    print "In mousePressedCallbackForTree....", event.button
    
    ''' Only post the popup on the right mouse button '''
    if int(event.button) <> 3:
        print "Not the right button!"
        return
    
    def showChartCallerCallback(event):
        '''
        This is the callback from the popup menu
        '''
        db = getDatabaseClient()
        treeWidget = event.source
        chartId = getChartIdForSelectedNode(treeWidget, db)
        if chartId == None:
            return

        window = system.nav.openWindow("SFC/Chart Callers",{"chartId": chartId})
        system.nav.centerWindow(window)
    
    print "Creating popup..."
    menu = system.gui.createPopupMenu(["Show Chart Callers"], [showChartCallerCallback])
    menu.show(event)
    
     
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