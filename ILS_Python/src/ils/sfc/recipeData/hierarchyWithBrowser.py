'''
Created on Feb 10, 2017 

@author: phass
'''
import system
from ils.common.config import getDatabaseClient
from ils.common.windowUtil import clearTable, clearTree
from ils.io.util import readTag, writeTag
from ils.sfc.recipeData.constants import ARRAY, GROUP, INPUT, MATRIX, OUTPUT, SIMPLE_VALUE
from ils.common.config import getTagProviderClient
from sys import path
from __builtin__ import True
from ils.sfc.common.constants import SQL
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

#treeMode = "chartName"
treeMode = "fullPath"

LIBRARY_ICON = "Custom/sfcLibrary.png"
CHART_ICON = "Custom/sfc.png"
TREE_MODE = 0
LIST_MODE = 1


def internalFrameOpened(rootContainer, db):
    '''
    Populate the left pane which has the logical view of the SFC call tree, clear the other two panes.   
    '''
    log.infof("In %s.internalFrameOpened()", __name__)
    
    rootContainer.initializationComplete = False
    rootContainer.synchronize = False
    tree = rootContainer.getComponent("Tree Container").getComponent("Tree View")
    table = rootContainer.getComponent("Tree Container").getComponent("Power Table")
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    
    ''' Try to restore whatever they were looking at the last time the window was open '''
    viewMode = readTag("[Client]SFC Browser/Chart View State").value
    selectedChartPath = readTag("[Client]SFC Browser/Selected Chart Path").value
    selectedChartRow = readTag("[Client]SFC Browser/Selected Chart Row").value
    selectedStep = readTag("[Client]SFC Browser/Selected Step").value
    log.debugf("The selected chart path is: %s", selectedChartPath)
    log.debugf("The selected chart row is: %d", selectedChartRow)
    log.debugf("The selected step is: %s", selectedStep)
    
    def setTableRow(table=table, tree=tree, stepTable=stepTable, selectedChartRow=selectedChartRow, selectedChartPath=selectedChartPath, selectedStep=selectedStep):
        ''' Select the node of the tree or the row of the table.  I'm not sure why I have to call this in its own thread but I do. '''
        table.selectedRow = selectedChartRow
        tree.selectedPath = selectedChartPath
        ''' This doesn't work because the steps above cause the table to refresh '''
        #stepTable.selectedRow = selectedStep
    
    rootContainer.chartViewState = viewMode
    updateSfcs(rootContainer, db)    

    if selectedChartPath <> "" or selectedChartRow >= 0:
        log.debugf("...there is a previously selected path (or table row)...")    
        
        ''' I'd like to set the selected row of the chart table here, but for some reason it doesn't do anything, or is undone by something else. '''
        system.util.invokeLater(setTableRow, 250)

        ''' Normally this is done from an event handler, but we need the steps in the table before we set the selected step. '''
        # refreshSteps(rootContainer, db)
    else:
        log.debugf("...there is NOT a previously selected path...")
        stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
        clearTable(stepTable)
        recipeDataTree = rootContainer.getComponent("Recipe Data Container").getComponent("Tree View")
        clearTree(recipeDataTree)
        
    rootContainer.initializationComplete = True
    log.debugf("DONE in internalFrameOpened!")


def internalFrameActivated(rootContainer, db):
    '''
    This is called whenever the windows gains focus.  this happens as part of the normal workflow of creating or editing recipe data
    so update the recipe data table to reflect the edit.
    '''
    log.debugf("In %s.internalFrameActivated()", __name__)
    updateRecipeDataTree(rootContainer, db)


def viewStateChanged(rootContainer):
    '''
    When they change the view from Tree to List then clear the other two panes AND unselect anything that was selected in the tree and the table.
    '''
    log.debugf("In %s.viewStateChanged(), detected a change in the view state...", __name__)
    
    if not(rootContainer.initializationComplete):
        log.debugf("...exiting because initialization is not complete...")
        return
    
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    clearTable(stepTable)
    recipeDataTree = rootContainer.getComponent("Recipe Data Container").getComponent("Tree View")
    clearTree(recipeDataTree)
    
    tree = rootContainer.getComponent("Tree Container").getComponent("Tree View")
    tree.selectedItem = -1
    table = rootContainer.getComponent("Tree Container").getComponent("Power Table")
    table.selectedRow = -1


def updateSfcs(rootContainer, db):
    log.debugf("In %s.updateSfcs(), Updating the SFC Tree and Table Widgets...", __name__)
    tagProvider = getTagProviderClient()
    sfcRecipeDataShowProductionOnly = readTag("[%s]Configuration/SFC/sfcRecipeDataShowProductionOnly" % (tagProvider)).value
    chartPath = "%"
    updateSfcTable(rootContainer, sfcRecipeDataShowProductionOnly, chartPath, db)
    updateSfcTree(rootContainer, sfcRecipeDataShowProductionOnly, chartPath, db)


def updateSfcTable(rootContainer, sfcRecipeDataShowProductionOnly, chartPath, db):
    log.debugf("In %s.updateSfcTable(), Updating the SFC Table Widget...", __name__)
    
    SQL = "select chartId, chartPath from SfcChart where chartPath like '%s' order by chartPath" % (chartPath)
    ds = system.db.runQuery(SQL, database=db)
    table=rootContainer.getComponent("Tree Container").getComponent("Power Table")
    table.data = ds

    
def updateSfcTree(rootContainer, sfcRecipeDataShowProductionOnly, chartPath, db):
    log.debugf("In %s.updateSfcTree(), updating the SFC Tree Widget...", __name__)

    hierarchyPDS = fetchHierarchy(chartPath, sfcRecipeDataShowProductionOnly, db)
    hierarchyHandlerPDS = fetchHierarchyHandler(chartPath, sfcRecipeDataShowProductionOnly, db)
    chartPDS = fetchCharts(chartPath, sfcRecipeDataShowProductionOnly, db)
    trees = makeSfcTree(chartPDS, hierarchyPDS, hierarchyHandlerPDS)
    
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
        log.tracef("%s", str(tree))
        rows = expandTree(rows, tree, chartDict, hierarchyPDS, hierarchyHandlerPDS)

    header = ["path", "text", "icon", "background", "foreground", "tooltip", "border", "selectedText", "selectedIcon", "selectedBackground", "selectedForeground", "selectedTooltip", "selectedBorder"]
    ds = system.dataset.toDataSet(header, rows)
    treeWidget=rootContainer.getComponent("Tree Container").getComponent("Tree View")
    treeWidget.data = ds

    
def expandTree(rows, tree, chartDict, hierarchyPDS, hierarchyHandlerPDS):
    
    def isNew(rows, parent, chartPath):
        for row in rows:
            if row[0] == parent and row[1] == chartPath:
                return False
        return True

    log.tracef("Expanding: %s", str(tree))
    tokens = tree.split(",")
    logicalPath=""
    '''
    for index in range(len(tokens)-1):
        token = tokens[index]
    '''
    for token in tokens:
        log.tracef("  Token: ", token)
        chartPath = chartDict.get(int(token),"Unknown")

        if logicalPath == "":
            parent = ""
            logicalPath = chartPath
        else:
            parent = logicalPath
            logicalPath = "%s/%s" % (logicalPath, chartPath)
        log.tracef("   Logical Path: %s", logicalPath)
        
        refs = countChartReferences(int(token), hierarchyPDS, hierarchyHandlerPDS)
        log.tracef(" **** %s has %d references ****", chartPath, refs)
        if refs > 1:
            icon = LIBRARY_ICON
        else:
            icon = CHART_ICON
        
        chartName = chartPath[chartPath.rfind("\\")+1:]
        log.tracef("   %s  --  %s  --  %s", logicalPath, chartPath, chartName)
        
        if isNew(rows, parent, chartPath):
            if treeMode == "fullPath":
                row = [parent, chartPath, icon,"color(255,255,255,255)","color(0,0,0,255)",chartPath,"","",icon,"color(250,214,138,255)","color(0,0,0,255)","",""]
            else:
                row = [parent,chartName,icon,"color(255,255,255,255)","color(0,0,0,255)",chartPath,"","",icon,"color(250,214,138,255)","color(0,0,0,255)","",""]
            
            log.tracef("The expanded row is: %s", str(row))
            rows.append(row)
        else:
            log.tracef("  Parent: %s, chartPath %s are already in the dataset", parent, chartPath)    
    return rows


def countChartReferences(token, hierarchyPDS, hierarchyHandlerPDS):
    refs = 0
    for record in hierarchyPDS:
        if record["ChildChartId"] == token:
            refs = refs + 1

    return refs


def fetchCharts(chartPath, sfcRecipeDataShowProductionOnly, db):
    log.debugf("Fetching the charts...")
    
    if sfcRecipeDataShowProductionOnly:
        SQL = "select ChartId, ChartPath, ChartResourceId from SfcChart where IsProduction = 1 and chartPath like '%s' order by ChartPath" % (chartPath)
    else:
        SQL = "select ChartId, ChartPath, ChartResourceId from SfcChart where chartPath like '%s' order by ChartPath" % (chartPath)
        
    pds = system.db.runPrepQuery(SQL, [], db)
    log.debugf("Fetched %d charts from SfcChart...", len(pds))
    return pds


def fetchHierarchy(chartPath, sfcRecipeDataShowProductionOnly, db=""):
    if sfcRecipeDataShowProductionOnly:
        SQL = "select * from SfcHierarchyView where IsProduction = 1 and chartPath like '%s' order by ChartPath" % (chartPath)
    else:
        SQL = "select * from SfcHierarchyView where chartPath like '%s' order by ChartPath" % (chartPath)

    log.tracef("%s", SQL)
    pds = system.db.runQuery(SQL, db)
    log.tracef("...fetched %d charts from SfcHierarchyView", len(pds))
    return pds


def fetchHierarchyHandler(chartPath, sfcRecipeDataShowProductionOnly, db=""):
    if sfcRecipeDataShowProductionOnly:
        SQL = "select * from SfcHierarchyHandlerView where IsProduction = 1 and chartPath like '%s' order by ChartPath"  % (chartPath)
    else:
        SQL = "select * from SfcHierarchyHandlerView where chartPath like '%s' order by ChartPath"  % (chartPath)

    pds = system.db.runQuery(SQL, db)
    log.tracef("...fetched %d charts from SfcHierarchyHandlerView", len(pds))
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
def makeSfcTree(chartPDS, hierarchyPDS, hierarchyHandlerPDS):
    
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
    log.tracef("In %s.makeSfcTree() - Getting the root nodes...", __name__)
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

def setChartViewState(viewState):
    writeTag("[Client]SFC Browser/Chart View State", viewState)

def setSelectedChartPath(selectedPath):
    writeTag("[Client]SFC Browser/Selected Chart Path", selectedPath)

def setSelectedChartRow(selectedRow):
    writeTag("[Client]SFC Browser/Selected Chart Row", selectedRow)
    
def setSelectedStep(selectedRow):
    writeTag("[Client]SFC Browser/Selected Step", selectedRow)

'''
These methods have to do with the list of steps
'''
def refreshSteps(rootContainer, db):
    '''
    This gets called in response to a node being selected in the SFC Chart Hierarchy tree.
    '''
    log.debugf("In %s.refreshSteps() - Updating the list of steps...", __name__)
    treeWidget = rootContainer.getComponent("Tree Container").getComponent("Tree View")
    chartTable = rootContainer.getComponent("Tree Container").getComponent("Power Table")
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    
    if rootContainer.chartViewState == TREE_MODE:
        log.debugf("...window is in tree mode...")
        chartId = getChartIdForSelectedNode(treeWidget, db)
        if chartId == None:
            clearTable(stepTable)
            return
    else:
        selectedRow = chartTable.selectedRow
        log.debugf("...window is in table mode, the selectedRow is %d...", selectedRow)
        if selectedRow == -1:
            clearTable(stepTable)
            return
        ds = chartTable.data
        chartId = ds.getValueAt(selectedRow, 0)
    
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
    log.debugf("The raw selected path is: <%s>", chartPath)
    chartPath = chartPath[chartPath.rfind("/")+1:]
    
    # Now replace ":" with "/"
    chartPath = chartPath.replace(' \\ ', '/')
    log.debugf("The selected chart path is <%s>", chartPath)
    if chartPath == "" or chartPath == None:
        return None
    
    SQL = "select chartId from SfcChart where chartPath = '%s'" % (chartPath)
    chartId = system.db.runScalarQuery(SQL, db) 
    log.debugf("Fetched chart id: %s", str(chartId))
    if chartId == None:
        return None
    
    return chartId


def tooltipFormatter(desc, lineLen=80):
    '''
    This is used to format the tooltip for the Recipe Data table.  The description can get really long and I 
    decided that the tooltop for the row should be the description, but if it is really long it needs to be word
    wrapped.  The tooltip supports HTML.
    '''
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
        log.tracef("Clearing the recipe data tree...")
        clearTree(recipeDataTree)
        setTreeButtons(recipeDataTree, False, False, False)
    else:
        startTime = system.date.now()
        log.tracef("In %s.updateRecipeDataTree() - Updating the recipe data tree...", __name__)
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
        
        step1CompleteTime = system.date.now()
        
        simpleValuePDS, timerPDS, recipePDS, sqcPDS, outputPDS, outputRampPDS, inputPDS = fetchDescriptions(stepId, db)
        
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
            desc = getRecipeDataDescription(record, simpleValuePDS, timerPDS, recipePDS, sqcPDS, outputPDS, outputRampPDS, inputPDS, db)
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
        completeTime = system.date.now()
        ''' I made these info messages so that excessive trace messages wouldn't sque the numbers '''
        log.tracef("Initial query took %s ms", str(system.date.millisBetween(startTime, step1CompleteTime)))
        log.tracef("Description query and tree update time took: %s ms for %d items", str(system.date.millisBetween(step1CompleteTime, completeTime)), len(pds) )

def setTreeButtons(recipeDataTree, editState, addState, deleteState):
    log.tracef("In %s.setTreeButtons...", __name__)
    recipeDataTree.enableEditButton = editState
    recipeDataTree.enableAddButton = addState
    recipeDataTree.enableDeleteButton = deleteState


def findRecipeParent(parentId, key, folderPDS):
    '''
    Given a specific folder, and a dataset of the entire folder hierarchy, find the full path for a given folder.
    '''
    log.tracef("=====================")
    log.tracef("Finding the full path for %s - %d", key, parentId)
    path = ""
    iMax = 100
    i = 0

    while parentId != None and i < iMax:
        
        for record in folderPDS:
            i = i + 1
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


def findParent(folderPDS, record):
    '''
    Given a specific folder, and a dataset of the entire folder hierarchy, find the full path for a given folder.
    '''
    log.tracef("------------------")
    path = record["RecipeDataKey"]
    parent = record["ParentRecipeDataFolderId"]
    log.tracef("Finding the path for %s - %s", path, str(parent))
    
    while parent != None:
        
        ''' If we look through all of the records and we don't find the parent then give up '''
        found = False
        for record in folderPDS:
            if record["RecipeDataFolderId"] == parent:
                log.tracef("Found the parent")
                path = "%s/%s" % (record["RecipeDataKey"], path)
                parent = record["ParentRecipeDataFolderId"]
                log.tracef("The new parent id is: %s", parent)
                found = True

        if not(found):
            log.errorf("ERROR: Did not find a parent for: %s", str(parent))
            return path

    log.tracef("The path is: %s", path)
    return path


def scrubPaths(paths, pathsUsedByData):
    '''
    Scrub the list of paths to remove paths that are wholly contained in another path.
    '''
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


def fetchDescriptions(stepId, db):
    '''
    This fetches all of descriptions at once and we will sort out it all out as we go through the individual recipe items one at a time.
    '''
    SQL = "select * from SfcRecipeDataSimpleValueView where stepId = %d" % (stepId)
    simpleValuePDS = system.db.runQuery(SQL, db)
    
    SQL = "Select * from SFcRecipeDataTimerView where stepId = %d" % (stepId)
    timerPDS = system.db.runQuery(SQL, db)
    
    SQL = "Select * from SFcRecipeDataRecipeView where stepId = %d" % (stepId)
    recipePDS = system.db.runQuery(SQL, db)
    
    SQL = "Select * from SFcRecipeDataSQCView where stepId = %d" % (stepId)
    sqcPDS = system.db.runQuery(SQL, db)
    
    SQL = "select * from SfcRecipeDataOutputView where stepId = %d" % (stepId)
    outputPDS = system.db.runQuery(SQL, db)
    
    SQL = "select * from SfcRecipeDataOutputRampView where stepId = %d" % (stepId)
    outputRampPDS = system.db.runQuery(SQL, db)
    
    SQL = "select * from SfcRecipeDataInputView where stepId = %d" % (stepId)
    inputPDS = system.db.runQuery(SQL, db)
            
    return simpleValuePDS, timerPDS, recipePDS, sqcPDS, outputPDS, outputRampPDS, inputPDS

def getRecipeDataDescription(record, simpleValuePDS, timerPDS, recipePDS, sqcPDS, outputPDS, outputRampPDS, inputPDS, db):
    try:
        desc = record["Description"]
        recipeDataId = record["RecipeDataId"]
        recipeDataType = record["RecipeDataType"]
        
        if recipeDataType == "Simple Value":
            for valueRecord in simpleValuePDS:
                if recipeDataId == valueRecord["RecipeDataId"]:
                    desc = getSimpleValueDescription(valueRecord, desc)
                    break

        elif recipeDataType == "Matrix":
            desc = getMatrixDescription(recipeDataId, desc, db)
            
        elif recipeDataType == "Array":
            desc = getArrayDescription(recipeDataId, desc, db)
            
        elif recipeDataType == "Timer":
            for valueRecord in timerPDS:
                if recipeDataId == valueRecord["RecipeDataId"]:
                    desc = getTimerDescription(valueRecord, desc)
                    break

        elif recipeDataType == "Recipe":
            for valueRecord in recipePDS:
                if recipeDataId == valueRecord["RecipeDataId"]:
                    desc = getRecipeDescription(valueRecord, desc)
                    break

        elif recipeDataType == "SQC":
            for valueRecord in sqcPDS:
                if recipeDataId == valueRecord["RecipeDataId"]:
                    desc = getSqcDescription(valueRecord, desc)
                    break

        elif recipeDataType == "Output":
            for valueRecord in outputPDS:
                if recipeDataId == valueRecord["RecipeDataId"]:
                    desc = getOutputDescription(record, valueRecord, desc)
                    break
                
        elif recipeDataType == "Output Ramp":
            for valueRecord in outputRampPDS:
                if recipeDataId == valueRecord["RecipeDataId"]:
                    desc = getOutputRampDescription(record, valueRecord, desc)
                    break
                
        elif recipeDataType == "Input":
            for valueRecord in inputPDS:
                if recipeDataId == valueRecord["RecipeDataId"]:
                    desc = getInputDescription(record, valueRecord, desc)
                    break

    except:
        desc = ""
        
    return desc

    
def getMatrixDescription(recipeDataId, desc, db):
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


def getTimerDescription(valueRecord, desc):
    txt = "State: %s, Start time: %s" % (valueRecord["TimerState"], valueRecord["StartTime"])
    
    if desc == "":
        desc = "a timer, %s" % (txt)
    else:
        desc = "a timer, %s, %s" % (desc, txt)    

    return desc


def getRecipeDescription(valueRecord, desc):
    txt = "Tag: %s, Value: %s" % (valueRecord["StoreTag"], str(valueRecord["RecommendedValue"]))

    if desc == "":
        desc = "a recipe, %s" % (txt)
    else:
        desc = "a recipe, %s, %s" % (desc, txt)    

    return desc 


def getSqcDescription(valueRecord, desc):
    label = valueRecord["Label"]

    txt = "Target: %s, Low: %s, High: %s" % (str(valueRecord["TargetValue"]), str(valueRecord["LowLimit"]), str(valueRecord["HighLimit"]))

    if label == "":
        desc = "a SQC, %s" % (txt)
    else:
        desc = "a SQC, %s, %s" % (label, txt)    

    return desc 


def getSimpleValueDescription(record, desc):
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
def getOutputDescription(record, valueRecord, desc):
    tag = valueRecord["Tag"]
    tag = tag[tag.rfind('/') + 1:]
    timing = valueRecord["Timing"]
    outputType = valueRecord["OutputType"]
    
    if desc == "":
        desc = "Tag: %s, Type: %s, Timing: %s" % (tag, outputType, str(timing))
    else:
        desc = "%s, Tag: %s, Type: %s, Timing: %s" % (desc, tag, outputType, str(timing))
        
    desc = getValueDescription(valueRecord, desc, OUTPUT, "an output")
    return desc

def getOutputRampDescription(record, valueRecord, desc):
    tag = valueRecord["Tag"]
    tag = tag[tag.rfind('/') + 1:]
    timing = valueRecord["Timing"]
    outputType = valueRecord["OutputType"]
    rampTime = valueRecord["RampTimeMinutes"]
    
    if desc == "":
        desc = "Tag: %s, Type: %s, Timing: %s, Ramp Time: %s" % (tag, outputType, str(timing), str(rampTime))
    else:
        desc = "%s, Tag: %s, Type: %s, Timing: %s, Ramp Time: %s" % (desc, tag, outputType, str(timing), str(rampTime))
        
    desc = getValueDescription(valueRecord, desc, OUTPUT, "an output ramp")

    return desc

def getInputDescription(record, valueRecord, desc):
    tag = valueRecord["Tag"]
    tag = tag[tag.rfind('/') + 1:]

    if desc == "":
        desc = "Tag: %s" % (tag)
    else:
        desc = "%s, Tag: %s" % (desc, tag)
    
    desc = getValueDescription(valueRecord, desc, INPUT, "an input")
    return desc
    
def getValueDescription(record, desc, recipeType, recipeDesc):
    valueType = record["ValueType"]
    units = record["Units"]
    
    if valueType == "String":
        if recipeType == OUTPUT:
            val = record["OutputStringValue"]
        else:
            val = record["PVStringValue"]
    elif valueType == "Float":
        if recipeType == OUTPUT:
            val = record["OutputFloatValue"]
        else:
            val = record["PVFloatValue"]
    elif valueType == "Integer":
        if recipeType == OUTPUT:
            val = record["OutputIntegerValue"]
        else:
            val = record["PVIntegerValue"]
    elif valueType == "Boolean":
        if recipeType == OUTPUT:
            val = record["OutputBooleanValue"]
        else:
            val = record["PVBooleanValue"]
            
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


def deleteCallback(event):
    log.tracef("Deleting a recipe data...")
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
        log.tracef("Deleting a recipe data folder with id: %d", folderId)
        SQL = "delete from SfcRecipeDataFolder where RecipeDataFolderId = %d" % (folderId)
        system.db.runUpdateQuery(SQL, db)

def fetchEmbeddedFolders(recipeDataFolderId, db):
    newFolderIds = recipeDataFolderId
    folderIds = [recipeDataFolderId]
    while newFolderIds != "":
        log.tracef("Looking for subfolders of <%s>...", str(newFolderIds)) 
        SQL = "select RecipeDataFolderId from SfcRecipeDataFolder where ParentRecipeDataFolderId in (%s)" % (newFolderIds)
        log.tracef(SQL)
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
        log.tracef("Deleted %d rows from SfcRecipeDataArrayElement...", rows)
    elif recipeDataType == MATRIX:
        SQL = "select ValueId from SfcRecipeDataMatrixElement where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        for record in pds:
            valueIds.append(record["ValueId"])
        SQL = "delete from SfcRecipeDataMatrixElement where RecipeDataId = %d" % (recipeDataId)
        rows = system.db.runUpdateQuery(SQL, db)
        log.tracef("Deleted %d rows from SfcRecipeDataMatrixElement...", rows)
    
    # The recipe data tables all have cascade delete foreign keys so we just need to delete from the main table
    log.tracef("Deleting a %s with id: %d", recipeDataType, recipeDataId)
    SQL = "delete from SfcRecipeData where RecipeDataId = %d" % (recipeDataId)
    system.db.runUpdateQuery(SQL, db)
    
    # Now delete the values
    for valueId in valueIds:
        SQL = "delete from SfcRecipeDataValue where ValueId = %d" % (valueId)
        system.db.runUpdateQuery(SQL, db)


def editCallbackForDoubleClick(event):
    editCallback(event)

            
def editCallback(event):
    db = getDatabaseClient()
    container = event.source.parent
    tree = container.getComponent("Tree View")
    path = tree.selectedPath
    
    log.tracef("In %s.editCallback() - The path is: %s", __name__, path)
    
    stepTable = container.parent.getComponent("Step Container").getComponent("Steps")
    selectedRow = stepTable.selectedRow
    log.tracef("The selected row is: %s", str(selectedRow))
    stepDs = stepTable.data
    stepId = stepDs.getValueAt(selectedRow,"StepId")
    log.tracef("The step id is: %s", str(stepId))
    
    recipeDataKey, recipeDataType, recipeDataId = fetchRecipeInfo(stepId, path, db)
    recipeDataFolderId = -1
    
    log.tracef("The recipe data id is: %s", str(recipeDataId))
    window = system.nav.openWindowInstance('SFC/RecipeDataEditor', {'stepId':stepId, 'recipeDataType':recipeDataType, 'recipeDataId':recipeDataId, 'recipeDataKey':recipeDataKey, "recipeDataFolderId":recipeDataFolderId})
    system.nav.centerWindow(window)            

def addCallback(event):
    log.tracef("In %s.addCallback()...", __name__)
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
            log.errorf("ERROR: expected the path to reference a folder (%s)", SQL)
    else:
        recipeDataFolderId = -99

    window = system.nav.openWindow('SFC/RecipeDataTypeChooser', {'stepId' : stepId, 'recipeDataFolderId':recipeDataFolderId})
    system.nav.centerWindow(window)

def fetchRecipeInfo(stepId, path, db):
    log.tracef("Fetching recipe info for: %s", path)
    pos = path.find(" :: ")
    if pos > 0:
        path = path[:path.find(" :: ")]
        log.tracef("The stripped path is <%s>", path)
    
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
                log.errorf("****** ERROR ********")
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
                log.errorf("ERROR: %d rows were returned for %s where exactly one was expected.", len(pds), SQL)
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
    ''' Only post the popup on the right mouse button '''
    if int(event.button) <> 3:
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

        window = system.nav.openWindowInstance("SFC/Chart Callers",{"chartId": chartId})
        system.nav.centerWindow(window)
        
    def expandCallback(event):
        '''
        This is the callback from the popup menu
        '''
        log.infof("In %s.expandCallback()...", __name__)
        treeComponent = event.source
        from javax.swing.tree import TreePath
        tree = treeComponent.viewport.view
        model = tree.model
        
        def expand(path):
            tree.expandPath(path)
            node = path.lastPathComponent;
            for i in range(model.getChildCount(node)):
                child = model.getChild(node, i)
                childPath = TreePath(model.getPathToRoot(child))
                expand(childPath)
        
        selectedPath = tree.getSelectionPath()
        if selectedPath != None:
            expand(selectedPath)

    
    menu = system.gui.createPopupMenu(["Show Chart Callers","Expand"], [showChartCallerCallback, expandCallback])
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