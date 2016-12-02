'''
Created on Nov 30, 2016

@author: phassler

This runs in the designer or a client
'''
import system
log =system.util.getLogger("com.ils.sfc.treeViewer")

def update(treeWidget, db=""):
    log.info("Updating the SFC Tree Widget...")
    hierarchyPDS = fetchHierarchy(db)
    chartPDS = fetchCharts(db)
    trees = fetchSfcTree(chartPDS, hierarchyPDS, db)
    
    chartDict = {}
    for record in chartPDS:
        chartId=record["ChartId"]
        chartPath=record["ChartPath"]
        chartDict[chartId] = chartPath

    log.trace("The chart dictionary is %s" % (str(chartDict)))    
    rows=[]
    for tree in trees:
        row = expandRow(tree, chartDict)
        rows.append(row)

    header = ["path", "text", "icon", "background", "foreground", "tooltip", "border", "selectedText", "selectedIcon", "selectedBackground", "selectedForeground", "selectedTooltip", "selectedBorder"]
    ds = system.dataset.toDataSet(header, rows)
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
    SQL = "select * from SfcChart"
    pds = system.db.runQuery(SQL, db)
    return pds

def fetchHierarchy(db):
    SQL = "select * from SfcHierarchyView"
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
def fetchSfcTree(chartPDS, hierarchyPDS, db=""):
    
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
