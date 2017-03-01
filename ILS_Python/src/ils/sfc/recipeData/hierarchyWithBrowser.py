'''
Created on Feb 10, 2017

@author: phass
'''
import system
from ils.common.windowUtil import clearTable
log =system.util.getLogger("com.ils.sfc.recipeBrowser")

# The chart path is passed as a property when the window is opened.  Look up the chartId, refresh the Steps table and clear the RecipeData Table
def internalFrameOpened(rootContainer, db):
    print "In internalFrameOpened"
    updateSfcTree(rootContainer, db)
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    clearTable(stepTable)
    recipeDataTable = rootContainer.getComponent("Recipe Data Container").getComponent("Recipe Data")
    clearTable(recipeDataTable)

# This is called whenever the windows gains focus.  his happens as part of the noral workflow of creating or editing recipe data
# so update the recipe data table to reflect the edit.
def internalFrameActivated(rootContainer, db):
    print "In internalFrameActivated"
#    refreshSteps(rootContainer, db)
    updateRecipeData(rootContainer, db)

def updateSfcTree(rootContainer, db):
    log.info("Updating the SFC Tree Widget...")
    hierarchyPDS = fetchHierarchy(db)
    chartPDS = fetchCharts(db)
    trees = fetchSfcTree(chartPDS, hierarchyPDS, db)
    
    chartDict = {}
    for record in chartPDS:
        chartId=record["ChartId"]
        chartPath=record["ChartPath"]
        
        # Chart Paths use the '/' to indicate the path structure, but the tree widget interprets that as a child.  I want to treat
        # the chart path as the name so replace "/" with ":"
        chartDict[chartId] = chartPath.replace('/',':')

    log.trace("The chart dictionary is %s" % (str(chartDict)))    
    rows=[]
    for tree in trees:
        row = expandRow(tree, chartDict)
        rows.append(row)

    header = ["path", "text", "icon", "background", "foreground", "tooltip", "border", "selectedText", "selectedIcon", "selectedBackground", "selectedForeground", "selectedTooltip", "selectedBorder"]
    ds = system.dataset.toDataSet(header, rows)
    treeWidget=rootContainer.getComponent("Tree Container").getComponent("Tree View")
    treeWidget.data = ds
    
def expandRow(tree, chartDict): 
    log.trace("Expanding: %s" % (str(tree)))
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
    log.trace("The expanded row is: %s" % (str(row)))
    return row

def fetchCharts(db):
    SQL = "select * from SfcChart order by ChartPath"
    pds = system.db.runQuery(SQL, db)
    return pds

def fetchHierarchy(db):
    SQL = "select * from SfcHierarchyView order by ChartPath"
    pds = system.db.runQuery(SQL, db)
    return pds

def getChildren(chartId, hierarchyPDS):
    children = []
    log.trace("Getting the children of chart: %s" % (str(chartId)))
    for record in hierarchyPDS:
        if record["ChartId"] == chartId:
            children.append(record["ChildChartId"])
    log.trace("The children of %s are %s" % (chartId, str(children)))
    return children

# This version traverses and creates a list of strings
def fetchSfcTree(chartPDS, hierarchyPDS, db):
    
    def depthSearch(trees, depth, hierarchyPDS):
        log.trace("------------")
        log.trace("Searching depth %i, the trees are %s" % (depth, str(trees)))

        foundChild = False
        newTrees = []
        for tree in trees:
            log.trace("The tree is: %s" % (str(tree)))
            ids = tree.split(",")
            node = ids[-1]
            log.trace("The last node is: %s" % (node))
            children=getChildren(int(node), hierarchyPDS)
            if len(children) == 0:
                log.trace("...there are no children!")
                newTrees.append(tree)
            else:
                log.trace("The children are: %s" % (str(children)))
                for child in children:
                    foundChild = True
                    newTree = "%s,%s" % (tree, child)
                    newTrees.append(newTree)
        log.trace("The new trees are: %s" % (str(newTrees)))
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
    log.trace("...the root nodes are: %s" % (str(trees)))

    foundChild = True
    depth = 0
    while foundChild:
        trees, foundChild = depthSearch(trees, depth, hierarchyPDS)
        depth = depth + 1
    log.trace("The trees are: %s" % (str(trees)))
    
    return trees

'''
These methods have to do with the list of steps
'''
def refreshSteps(rootContainer, db):
    print "Updating the list of steps..."
    treeWidget = rootContainer.getComponent("Tree Container").getComponent("Tree View")
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    
    # First get the last node in the path
    chartPath = treeWidget.selectedPath
    chartPath = chartPath[chartPath.rfind("/")+1:]
    
    # Now replace ":" with "/"
    chartPath = chartPath.replace(':', '/')
    print "The selected chart path is <%s>" % chartPath
    if chartPath == "" or chartPath == None:
        clearTable(stepTable)
        return
    
    SQL = "select chartId from SfcChart where chartPath = '%s'" % (chartPath)
    chartId = system.db.runScalarQuery(SQL) 
    print "Fetched chart id: ", chartId
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

def updateRecipeData(rootContainer, db):
    print "Updating the recipe data table..."
    stepTable = rootContainer.getComponent("Step Container").getComponent("Steps")
    recipeDataTable = rootContainer.getComponent("Recipe Data Container").getComponent("Recipe Data")
    
    if stepTable.selectedRow < 0:
        clearTable(recipeDataTable)
    else:
        ds = stepTable.data
        stepId = ds.getValueAt(stepTable.selectedRow, "StepId")
        
        SQL = "select * from SfcRecipeDataView where StepId = %s order by RecipeDataKey" % (str(stepId))
        print SQL
        pds = system.db.runQuery(SQL, db)
        recipeDataTable.data = pds

def deleteRecipeData(rootContainer, db):
    print "Deleting a recipe data..."

    recipeDataTable = rootContainer.getComponent("Recipe Data Container").getComponent("Recipe Data")
    
    if recipeDataTable.selectedRow < 0:
        system.gui.messageBox("Please select a row from the Recie Data table.")
        return
    
    ds = recipeDataTable.data
    recipeDataId = ds.getValueAt(recipeDataTable.selectedRow, "RecipeDataId")
    
    recipeDataType = ds.getValueAt(recipeDataTable.selectedRow, "RecipeDataType")
    
    # Get the value ids before we delete the data
    valueIds = []
    if recipeDataType == "Simple Value":
        SQL = "select ValueId from SfcRecipeDataSimpleValue where recipeDataId = %d" % (recipeDataId)
        valueId = system.db.runScalarQuery(SQL, db)
        valueIds.append(valueId)
    elif recipeDataType == "Output":
        SQL = "select OutputValueId, TargetValueId, PVValueId from SfcRecipeDataOutput where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueIds.append(record["OutputValueId"])
        valueIds.append(record["TargetValueId"])
        valueIds.append(record["PVValueId"])
    elif recipeDataType == "Input":
        SQL = "select TargetValueId, PVValueId from SfcRecipeDataInput where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueIds.append(record["TargetValueId"])
        valueIds.append(record["PVValueId"])
    elif recipeDataType == "Array":
        SQL = "select ValueId from SfcRecipeDataArrayElement where recipeDataId = %d" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        for record in pds:
            valueIds.append(record["ValueId"])
    
    # The recipe data tables all have cascade delete foreign keys so we just need to delete from the main table
    SQL = "delete from SfcRecipeData where RecipeDataId = %d" % (recipeDataId)
    print SQL
    system.db.runUpdateQuery(SQL, db)
    
    # Now delete the values
    for valueId in valueIds:
        SQL = "delete from SfcRecipeDataValue where ValueId = %d" % (valueId)
        system.db.runUpdateQuery(SQL, db)
    
    # Update the table
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