'''
Created on Apr 12, 2022

@author: ils
'''
import system
from ils.common.util import parseResourcePath
from ils.common.config import getDatabaseClient
#from ils.diagToolkit.common import fetchApplicationId, fetchFamilyId

from ils.log import getLogger
log = getLogger(__name__)

ROOT_NODE = "Symbolic Ai"

SYMBOLIC_AI_ICON = "Block/icons/navtree/symbolicAi.png"
APPLICATION_ICON = "Block/icons/navtree/application.png"
FAMILY_ICON = "Block/icons/navtree/family.png"
DIAGRAM_ICON = "Block/icons/navtree/diagram.png"
FINAL_DIAGNOSIS_ICON = "Block/icons/navtree/finalDiagnosis.png"

WHITE = "color(255,255,255,255)"
BLACK = "color(0,0,0,255)"
MUSTARD = "color(250,214,138,255)"

APPLICATION_TYPE = "Application"
FAMILY_TYPE = "Family"
FINAL_DIAGNOSIS_TYPE = "Final Diagnosis"

def refreshDiagramTree(rootContainer, db=""):
    log.infof("In %s.refreshDiagramTree()...", __name__)
    
    SQL = "select DiagramName from DtDiagram where FamilyId is NULL"
    pds = system.db.runQuery(SQL, database=db)
    
    rows = []
    for record in pds:
        fullDiagramName = record["DiagramName"]
        parent, diagramName = parseResourcePath(fullDiagramName) 
        icon = "default"
        row = [parent,diagramName,icon,"color(255,255,255,255)","color(0,0,0,255)",fullDiagramName,"","",icon,"color(250,214,138,255)","color(0,0,0,255)","",""]
        rows.append(row)
        
    header = ["path", "text", "icon", "background", "foreground", "tooltip", "border", "selectedText", "selectedIcon", "selectedBackground", "selectedForeground", "selectedTooltip", "selectedBorder"]
    ds = system.dataset.toDataSet(header, rows)
    treeWidget = rootContainer.getComponent("Diagram Tree")
    treeWidget.data = ds

def refreshHierarchyTree(rootContainer, db=""):
    rows = []
    rows.append(["", "Symbolic Ai", SYMBOLIC_AI_ICON, WHITE, BLACK, "A", "", "", SYMBOLIC_AI_ICON, MUSTARD, BLACK, "", ""])
    
    applications = fetchApplications(db)
    for application in applications:
        applicationName = application["ApplicationName"]
        rows.append([ROOT_NODE, applicationName, APPLICATION_ICON, WHITE, BLACK, "A", "", "", APPLICATION_ICON, MUSTARD, BLACK, "", ""])
        
    families = fetchFamilies(db)
    for family in families:
        applicationName = ROOT_NODE + "/" + family["ApplicationName"]
        familyName = family["FamilyName"]
        rows.append([applicationName, familyName, FAMILY_ICON, WHITE, BLACK, "A", "", "", FAMILY_ICON, MUSTARD, BLACK, "", ""])
        
    

#    rows.append(["A","B", FAMILY_ICON,WHITE,BLACK,"A","","",FAMILY_ICON,MUSTARD,BLACK,"",""])
#    rows.append(["A/B","C", DIAGRAM_ICON,WHITE,BLACK,"A","","",DIAGRAM_ICON,MUSTARD,BLACK,"",""])
#    rows.append(["A/B/C","D", FINAL_DIAGNOSIS_ICON,WHITE,BLACK,"A","","",FINAL_DIAGNOSIS_ICON,MUSTARD,BLACK,"",""])

    header = ["path", "text", "icon", "background", "foreground", "tooltip", "border", "selectedText", "selectedIcon", "selectedBackground", "selectedForeground", "selectedTooltip", "selectedBorder"]
    ds = system.dataset.toDataSet(header, rows)
    treeWidget = rootContainer.getComponent("Hierarchy Tree")
    treeWidget.data = ds
    
def determineNodeType(event):
    '''
    We could also just look at the icon to determine the node type 
    '''
    print "...determine node type..."
    tree = event.source
    selectedItem = event.newValue
    
    if selectedItem == -1:
        tree.selectedNodeType = None
    elif selectedItem == 0:
        tree.selectedNodeType = "Root"
    else:
        selectedPath = tree.selectedPath
        tokens = selectedPath.split("/")
        if len(tokens) == 2:
            tree.selectedNodeType = APPLICATION_TYPE
        elif len(tokens) == 3:
            tree.selectedNodeType = FAMILY_TYPE
        else:
            tree.selectedNodeType = "Unknown"

def addCallback(event):
    log.infof("In %s.addCallback()", __name__)
    
def deleteCallback(event):
    log.infof("In %s.deleteCallback()", __name__) 
    
def editCallback(event):
    log.infof("In %s.editCallback()", __name__)
    db = getDatabaseClient()
    rootContainer = event.source.parent
    tree = rootContainer.getComponent("Hierarchy Tree")
    selectedPath = tree.selectedPath
    tokens = selectedPath.split("/")
    nodeType = tree.selectedNodeType
    print nodeType, selectedPath
    
    if nodeType == APPLICATION_TYPE:
        print "Selected an application"
        applicationName = tokens[1]
        applicationId = fetchApplicationId(applicationName, db)
        window = system.nav.openWindowInstance("DiagToolkit/Application Editor", {"applicationId": applicationId})
        system.nav.centerWindow(window)

    elif nodeType == FAMILY_TYPE:
        print "Selected a family"
        applicationName = tokens[1]
        familyName = tokens[2]
        familyId = fetchFamilyId(applicationName, familyName, db)
        window = system.nav.openWindowInstance("DiagToolkit/Family Editor", {"familyId": familyId})
        system.nav.centerWindow(window)

    elif nodeType == FINAL_DIAGNOSIS_TYPE:
        print "Selected a final diagnosis"
        window = system.nav.openWindowInstance("DiagToolkit/Final Diagnosis Editor")
        system.nav.centerWindow(window)

    else:
        print "Selected an unknown type: ", nodeType
    
def insertDiagramCallback(event):
    log.infof("In %s.insertDiagramCallback()", __name__)
    db = getDatabaseClient()
    rootContainer = event.source.parent
    diagramTreeWidget = rootContainer.getComponent("Diagram Tree")
    row = diagramTreeWidget.selectedItem
    
    ''' The full diagram path is in the tooltip.  Because I don't use any intermediate nodes while building this Tree, I can go directly from the selected Item into the dataset '''
    ds = diagramTreeWidget.data
    diagramName = ds.getValueAt(row, "tooltip")
    diagramId = fetchIdForDiagram(diagramName, db)
    log.infof("User selected diagram: %s - %s", diagramName, str(diagramId))
    
    hierarchyTreeWidget = rootContainer.getComponent("Hierarchy Tree")
    row = hierarchyTreeWidget.selectedItem
    ds = hierarchyTreeWidget.data
    familyName = ds.getValueAt(row, "text")
    path = ds.getValueAt(row, "path")
    applicationName = path[path.find("/")+1:]
    log.infof("User selected family <%s> in application <%s>", familyName, applicationName)
    


def removeDiagramCallback(event):
    log.infof("In %s.removeDiagramCallback()", __name__)
    
'''
Database Utilities
'''
def fetchApplications(db):
    pds = system.db.runQuery("Select ApplicationName from DtApplication order by ApplicationName", database=db)
    log.infof("Fetched %d applications." % (len(pds)))
    return pds

def fetchFamilies(db):
    pds = system.db.runQuery("Select ApplicationName, FamilyName from DtApplicationFamilyView order by ApplicationName, FamilyName", database=db)
    log.infof("Fetched %d applications." % (len(pds)))
    return pds

def fetchIdForDiagram(diagramName, db):
    diagramId = system.db.runScalarQuery("select DiagramId from DtDiagram where DiagramName = '%s'" % (diagramName), database=db)
    return diagramId

'''
******************************************************************************
**** Move these back to common.py once the blt module is back and working ****
******************************************************************************
'''

def fetchApplicationId(applicationName, database=""):
    SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (applicationName)
    log.tracef("%s.fetchApplicationId(): %s", __name__, SQL)
    applicationId = system.db.runScalarQuery(SQL, database)
    return applicationId

def fetchFamilyId(applicationName, familyName, database=""):
    SQL = "select F.FamilyId from DtApplication A, DtFamily F "\
        "where A.ApplicationId = F.ApplicationId and A.ApplicationName = '%s' and F.FamilyName = '%s'" % (applicationName, familyName)
    log.tracef("%s.fetchFamilyId(): %s", __name__, SQL)
    familyId = system.db.runScalarQuery(SQL, database)
    return familyId