'''
Created on Apr 12, 2022

@author: ils
'''
import system
from ils.common.util import parseResourcePath
from ils.config.client import getDatabase
from ils.diagToolkit.common import fetchApplicationId, fetchFamilyId, fetchApplications, fetchFamilies, fetchDiagrams, fetchFinalDiagnosisList, fetchDiagramId, fetchFinalDiagnosisId

from ils.log import getLogger
log = getLogger(__name__)

ROOT_NODE = "Symbolic Ai"

SYMBOLIC_AI_ICON = "Custom/blt/NavTree/symbolicAi.png"       # "Block/icons/navtree/symbolicAi.png"
APPLICATION_ICON = "Custom/blt/NavTree/application.png"       # "Block/icons/navtree/application.png"
FAMILY_ICON = "Custom/blt/NavTree/family.png"
DIAGRAM_ICON = "Custom/blt/NavTree/diagram.png"           # "Block/icons/navtree/diagram.png"
DIAGRAM_REFERENCED_ICON = "Custom/blt/NavTree/diagramReferenced.png"           # "Block/icons/navtree/diagram.png"
FINAL_DIAGNOSIS_ICON = "Custom/blt/NavTree/finalDiagnosis.png"

WHITE = "color(255,255,255,255)"
BLACK = "color(0,0,0,255)"
MUSTARD = "color(250,214,138,255)"
RED = "color(255,0,0,255)"

ROOT_TYPE = "Root"
APPLICATION_TYPE = "Application"
FAMILY_TYPE = "Family"
DIAGRAM_TYPE = "Diagram"
FINAL_DIAGNOSIS_TYPE = "Final Diagnosis"

CLICK_THRESHOLD = 10

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()...", __name__)
    rootContainer = event.source.rootContainer

    diagramContainer = rootContainer.getComponent("Diagram Container")
    diagramContainer.showAllDiagrams = False

    treeWidget = rootContainer.getComponent("Hierarchy Container").getComponent("Hierarchy Tree")
    treeWidget.selectedNodeType = ""


def internalFrameActivated(event):
    ''' This is called whenever the window regains focus '''
    log.infof("In %s.internalFrameActivated()...", __name__)
    rootContainer = event.source.rootContainer
    db = getDatabase()
    
    # Clearing the selected Node Type makes the tree appear to be unresponsive
    #treeWidget = rootContainer.getComponent("Hierarchy Container").getComponent("Hierarchy Tree")
    #treeWidget.selectedNodeType = ""
    refreshDiagramTree(rootContainer, db)
    refreshHierarchyTree(rootContainer, db)

def refreshDiagramTreeCallback(rootContainer):
    log.infof("In %s.refreshDiagramTreeCallback()...", __name__)
    db = getDatabase()
    refreshDiagramTree(rootContainer, db)

def refreshDiagramTree(rootContainer, db):
    log.infof("In %s.refreshDiagramTree()...", __name__)
    
    diagramContainer = rootContainer.getComponent("Diagram Container")
    showAllDiagrams = diagramContainer.showAllDiagrams
    
    if showAllDiagrams:
        SQL = "select DiagramName, FamilyId from DtDiagram"
        pds = system.db.runQuery(SQL, database=db)
        statusMessage = "%d total diagrams" % (len(pds))
    else:
        SQL = "select DiagramName, FamilyId from DtDiagram where FamilyId is NULL"
        pds = system.db.runQuery(SQL, database=db)
        statusMessage = "%d unreferenced diagrams" % (len(pds))
    
    diagramContainer.statusMessage = statusMessage
    
    rows = []
    rows.append(["", ROOT_NODE, SYMBOLIC_AI_ICON, WHITE, BLACK, "", "", "", SYMBOLIC_AI_ICON, WHITE, BLACK, "", ""])
    for record in pds:
        fullDiagramName = record["DiagramName"]
        familyId = record["FamilyId"]
        parent, diagramName = parseResourcePath(fullDiagramName)
        parent = ROOT_NODE + "/" + parent 
        if familyId == None:
            row = [parent,diagramName,DIAGRAM_ICON,WHITE,BLACK,fullDiagramName,"","",DIAGRAM_ICON,WHITE,BLACK,"",""]
        else:
            row = [parent,diagramName,DIAGRAM_REFERENCED_ICON,WHITE,BLACK,fullDiagramName,"","",DIAGRAM_REFERENCED_ICON,WHITE,BLACK,"",""]
        rows.append(row)
    
    ''' Now add the Final Diagnosis '''
    if showAllDiagrams:
        SQL = "select D.DiagramName, D.FamilyId, FD.FinalDiagnosisName from DtDiagram D, DtFinalDiagnosis FD where D.DiagramId = FD.DiagramId"
        print SQL
        pds = system.db.runQuery(SQL, database=db)
        statusMessage = "%d final diagnosis" % (len(pds))
    else:
        SQL = "select D.DiagramName, D.FamilyId, FD.FinalDiagnosisName from DtDiagram D, DtFinalDiagnosis FD where FamilyId is NULL and D.DiagramId = FD.DiagramId"
        print SQL
        pds = system.db.runQuery(SQL, database=db)
        statusMessage = "%d unreferenced final diagnosis" % (len(pds))
        
    for record in pds:
        fullDiagramName = record["DiagramName"]
        finalDiagnosisName = record["FinalDiagnosisName"]

        row = [ROOT_NODE + "/" +fullDiagramName, finalDiagnosisName, FINAL_DIAGNOSIS_ICON, WHITE, BLACK, fullDiagramName + "-" + finalDiagnosisName, "" ,"" ,FINAL_DIAGNOSIS_ICON, WHITE, BLACK, "", ""]
        rows.append(row)
    
    
    header = ["path", "text", "icon", "background", "foreground", "tooltip", "border", "selectedText", "selectedIcon", "selectedBackground", "selectedForeground", "selectedTooltip", "selectedBorder"]
    ds = system.dataset.toDataSet(header, rows)
    treeWidget = rootContainer.getComponent("Diagram Container").getComponent("Diagram Tree")
    treeWidget.data = ds

def refreshHierarchyTreeCallback(rootContainer, db=""):
    db = getDatabase()
    refreshHierarchyTree(rootContainer, db)
    
def refreshHierarchyTree(rootContainer, db):
    rows = []
    rows.append(["", ROOT_NODE, SYMBOLIC_AI_ICON, WHITE, BLACK, "", "", "", SYMBOLIC_AI_ICON, WHITE, BLACK, "", ""])
    
    applications = fetchApplications(db)
    for application in applications:
        applicationName = application["ApplicationName"]
        rows.append([ROOT_NODE, applicationName, APPLICATION_ICON, WHITE, BLACK, "", "", "", APPLICATION_ICON, WHITE, BLACK, "", ""])
        
    families = fetchFamilies(db)
    for family in families:
        applicationName = family["ApplicationName"]
        familyName = family["FamilyName"]
        familyPriority = family["FamilyPriority"]
        familyTxt = appendPriority(familyName, familyPriority)
        applicationName = ROOT_NODE + "/" + applicationName
        rows.append([applicationName, familyTxt, FAMILY_ICON, WHITE, BLACK, "", "", "", FAMILY_ICON, WHITE, BLACK, "", ""])
        
    diagrams = fetchDiagrams(db)
    for diagram in diagrams:
        applicationName = diagram["ApplicationName"]
        familyName = diagram["FamilyName"]
        familyPriority = diagram["FamilyPriority"]
        familyTxt = appendPriority(familyName, familyPriority)
        
        ''' For diagrams, the name in the databaset is the diagram path in the project tree.  For our display purposes, we just want the 
            name, the full path will be in the tooltip.  '''
        fullDiagramName = diagram["DiagramName"]
        tokens = fullDiagramName.split("/")
        diagramName = tokens[len(tokens)-1]
        rows.append([ROOT_NODE + "/" + applicationName + "/" + familyTxt, diagramName, DIAGRAM_ICON, WHITE, BLACK, fullDiagramName, "", "", DIAGRAM_ICON, WHITE, BLACK, "", ""])

    FDs = fetchFinalDiagnosisList(db)
    for FD in FDs:
        applicationName = FD["ApplicationName"]
        familyName = FD["FamilyName"]
        familyPriority = FD["FamilyPriority"]
        familyTxt = appendPriority(familyName, familyPriority)

        fullDiagramName = FD["DiagramName"]
        tokens = fullDiagramName.split("/")
        diagramName = tokens[len(tokens)-1]
        
        fdName = FD["FinalDiagnosisName"]
        fdPriority = FD["FinalDiagnosisPriority"]
        
        parentNode = ROOT_NODE + "/" + applicationName + "/" + familyTxt + "/" + diagramName
        log.infof("Adding an application with parent: <%s>", parentNode)
        fdText = appendPriority(fdName, fdPriority)
        rows.append([parentNode, fdText, FINAL_DIAGNOSIS_ICON, WHITE, BLACK, fdName, "", "", FINAL_DIAGNOSIS_ICON, WHITE, BLACK, "", ""])

    header = ["path", "text", "icon", "background", "foreground", "tooltip", "border", "selectedText", "selectedIcon", "selectedBackground", "selectedForeground", "selectedTooltip", "selectedBorder"]
    ds = system.dataset.toDataSet(header, rows)
    treeWidget = rootContainer.getComponent("Hierarchy Container").getComponent("Hierarchy Tree")
    treeWidget.data = ds
    
def determineNodeType(event):
    '''
    We could also just look at the icon to determine the node type 
    '''
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
        elif len(tokens) == 4:
            tree.selectedNodeType = DIAGRAM_TYPE
        elif len(tokens) == 5:
            tree.selectedNodeType = FINAL_DIAGNOSIS_TYPE
        else:
            tree.selectedNodeType = "Unknown"

def addCallback(event):
    ''' The add button is used to create a new application or a new family '''
    log.infof("In %s.addCallback()", __name__)
    db = getDatabase()
    rootContainer = event.source.parent.parent
    tree = rootContainer.getComponent("Hierarchy Container").getComponent("Hierarchy Tree")
    selectedPath = tree.selectedPath
    tokens = selectedPath.split("/")
    nodeType = tree.selectedNodeType
    log.infof("%s - %s", nodeType, selectedPath)
    
    if nodeType == ROOT_TYPE:
        log.infof("Selected the root node")
        window = system.nav.openWindowInstance("DiagToolkit/Application Editor", {"applicationId": -1})
        system.nav.centerWindow(window)
        
    elif nodeType == APPLICATION_TYPE:
        log.infof("Selected an application")
        applicationName = tokens[1]
        applicationId = fetchApplicationId(applicationName, db)
        window = system.nav.openWindowInstance("DiagToolkit/Family Editor", {"applicationId": applicationId, "familyId": -1})
        system.nav.centerWindow(window)
    
    else:
        log.infof("Unsupported node type")
    
def deleteCallback(event):
    log.infof("In %s.deleteCallback()", __name__)
    db = getDatabase()
    rootContainer = event.source.parent.parent
    tree = rootContainer.getComponent("Hierarchy Container").getComponent("Hierarchy Tree")
    selectedPath = tree.selectedPath
    tokens = selectedPath.split("/")
    nodeType = tree.selectedNodeType
    log.infof("%s - %s", nodeType, selectedPath)
    
    if nodeType == APPLICATION_TYPE:
        '''
        Not sure if I should just delete the wholle application hierarchy without checking, ask for confirmation, or what...
        There really isn't a right answer, but I think I'll be cautions and force them to delete the family before deleting the application.
        '''
        applicationName = tokens[1]
        applicationId = fetchApplicationId(applicationName, db)
        references = system.db.runScalarQuery("Select count(*) from DtFamily where applicationId = %d" % applicationId)
        if references > 0:
            system.gui.messageBox("There are families that belong to this application - families must be deleted before the application can be deleted!")
            return
        
        SQL = "delete from DtApplication where ApplicationId = %d" % (applicationId)
        rows = system.db.runUpdateQuery(SQL, database=db)
        log.infof("...deleted %d applications!", rows)
        refreshHierarchyTree(rootContainer, db)
        
    elif nodeType == FAMILY_TYPE:
        ''' remove all references to the family, delete the family, update both trees '''
        applicationName = tokens[1]
        familyName = stripPriority(tokens[2])
        familyId = fetchFamilyId(applicationName, familyName, db)
        log.infof("Deleting family named: <%s> with id: %s in application: %s", familyName, familyId, applicationName)
        SQL = "update DtDiagram set FamilyId = NULL where familyId = %d" % (familyId)
        rows = system.db.runUpdateQuery(SQL, database=db)
        log.infof("...cleared %d diagram references to family %s...", rows, familyName)
        
        SQL = "delete from DtFamily where FamilyId = %d" % (familyId)
        rows = system.db.runUpdateQuery(SQL, database=db)
        log.infof("...deleted %d families!", rows)
        
        refreshDiagramTree(rootContainer, db)
        refreshHierarchyTree(rootContainer, db)
        
        
def editCallbackForDoubleClick(event):
    log.infof("In %s.editCallbackForDoubleClick()", __name__)
    editCallback(event)    

    
def editCallback(event):
    log.infof("In %s.editCallback()", __name__)
    db = getDatabase()
    rootContainer = event.source.parent.parent
    tree = rootContainer.getComponent("Hierarchy Container").getComponent("Hierarchy Tree")
    selectedPath = tree.selectedPath
    tokens = selectedPath.split("/")
    nodeType = tree.selectedNodeType
    log.infof("%s - %s", nodeType, selectedPath)
    
    if nodeType == APPLICATION_TYPE:
        log.tracef("Editing an application")
        applicationName = tokens[1]
        applicationId = fetchApplicationId(applicationName, db)
        window = system.nav.openWindowInstance("DiagToolkit/Application Editor", {"applicationId": applicationId})
        system.nav.centerWindow(window)

    elif nodeType == FAMILY_TYPE:
        log.tracef("Editing a family")
        applicationName = tokens[1]
        familyName = tokens[2]
        familyName = stripPriority(familyName)
        familyId = fetchFamilyId(applicationName, familyName, db)
        window = system.nav.openWindowInstance("DiagToolkit/Family Editor", {"familyId": familyId})
        system.nav.centerWindow(window)

    elif nodeType == FINAL_DIAGNOSIS_TYPE:
        log.tracef("Editing a final diagnosis")
        applicationName = tokens[1]
        familyName = tokens[2]
        familyId = fetchFamilyId(applicationName, familyName, db)
        diagramName = getFullDiagramNameForFinalDiagnosis(rootContainer, selectedPath)
        diagramNameShort = tokens[3]
        fdName = tokens[4]
        fdName = stripPriority(fdName)
        log.tracef("   application: %s    ", applicationName)
        log.tracef("   family: %s         ", familyName)
        log.tracef("   family id: %s      ", str(familyId))
        log.tracef("   diagram (short): %s", diagramNameShort)
        log.tracef("   diagram: %s        ", diagramName)
        log.tracef("   final diagnosis: %s", fdName)
        
        finalDiagnosisId = fetchFinalDiagnosisId(diagramName, fdName, db)
        window = system.nav.openWindowInstance("DiagToolkit/Final Diagnosis Editor", {"applicationName": applicationName, "finalDiagnosisId": finalDiagnosisId})
        system.nav.centerWindow(window)

    else:
        log.errorf("Selected an unknown type: %s", nodeType)
        
def getFullDiagramNameForFinalDiagnosis(rootContainer, selectedPath):
    log.infof("Looking for the full diagram path for this FD: <%s>", selectedPath)
    tokens = selectedPath.split("/")
    fdName = tokens.pop(len(tokens)-1)
    diagramName = tokens.pop(len(tokens)-1)
    log.infof("...found %s on diagram %s!", fdName, diagramName)
    parent = "/".join(tokens)
    
    tree = rootContainer.getComponent("Hierarchy Container").getComponent("Hierarchy Tree")
    ds = tree.data
    for row in range(ds.rowCount):
        if ds.getValueAt(row, 0) == parent and ds.getValueAt(row, 1) == diagramName:
            ''' For diagrams, the full name is stored in the tooltip column '''
            diagramPath = ds.getValueAt(row, "tooltip")
            return diagramPath
        
    return None
    
def insertDiagramCallback(event):
    log.infof("In %s.insertDiagramCallback()", __name__)
    db = getDatabase()
    rootContainer = event.source.parent
    diagramTreeWidget = rootContainer.getComponent("Diagram Container").getComponent("Diagram Tree")
    row = diagramTreeWidget.selectedItem
    ds = diagramTreeWidget.data
    selectedDiagramPath = ds.getValueAt(row, "path")
    
    tree = diagramTreeWidget.viewport.view    
    selectedPath = tree.getSelectionPath()
    
    ''' The full diagram path is in the tooltip.  Because I don't use any intermediate nodes while building this Tree, I can go directly from the selected Item into the dataset '''
    ds = diagramTreeWidget.data
    diagramName = ds.getValueAt(row, "tooltip")
    diagramId = fetchDiagramId(diagramName, db)
    log.infof("User selected diagram: %s - %s", diagramName, str(diagramId))
    
    hierarchyTreeWidget = rootContainer.getComponent("Hierarchy Container").getComponent("Hierarchy Tree")
    row = hierarchyTreeWidget.selectedItem
    ds = hierarchyTreeWidget.data
    familyName = ds.getValueAt(row, "text")
    familyName = stripPriority(familyName)
    path = ds.getValueAt(row, "path")
    applicationName = path[path.find("/")+1:]
    log.infof("User selected family <%s> in application <%s>...", familyName, applicationName)
    familyId = fetchFamilyId(applicationName, familyName, db)
    log.infof("...with family id: %s", str(familyId))    
    
    '''
    1) Update the database so that the diagram is a member of the family
    2) Refresh the diagram tree (by fetching  the diagrams from the database)
    3) Refresh the hierarchy tree  (by fetching the data from database)
    '''
    
    SQL = "Update DtDiagram set FamilyId = %d where DiagramId = %d" % (familyId, diagramId)
    system.db.runUpdateQuery(SQL, database=db)
    refreshDiagramTree(rootContainer, db)
    refreshHierarchyTree(rootContainer, db)
    
    '''
    Expand the application hierarchy for the selected family so that the moved diagram shows up 
    '''
    log.infof("Expanding the family in the application hierarchy...")
    from javax.swing.tree import TreePath
    tree = hierarchyTreeWidget.viewport.view    
    selectedPath = tree.getSelectionPath()
    log.tracef("The selected hierarchy path is: %s", selectedPath)
    if selectedPath != None:
        log.tracef("Expanding %s", selectedPath)
        tree.expandPath(selectedPath)

    '''
    Expand the diagram tree for the next diagram in the older or nothing is selected
    '''
    ds = diagramTreeWidget.data
    selectedChart = None
    selectedRow = -1
    for row in range(ds.rowCount):
        log.tracef("Row: %d - path: %s - chart: %s", row, ds.getValueAt(row, "path"), ds.getValueAt(row, "text"))
        if selectedDiagramPath == ds.getValueAt(row, "path"):
            if selectedChart == None or ds.getValueAt(row, "text") < selectedChart:
                selectedRow = row
                selectedChart = ds.getValueAt(row, "text")
    
    if selectedRow == None:
        diagramTreeWidget.selectedItem = -1
    else:
        diagramTreeWidget.selectedItem = selectedRow

        
def removeDiagramCallback(rootContainer):
    ''' This is called from a popup. '''
    
    log.infof("In %s.removeDiagramCallback()", __name__)
    db = getDatabase()
    
    ''' The full diagram name is stored in the tooltip of the  '''
    hierarchyTreeWidget = rootContainer.getComponent("Hierarchy Container").getComponent("Hierarchy Tree")
    row = hierarchyTreeWidget.selectedItem
    ds = hierarchyTreeWidget.data
    diagramName = ds.getValueAt(row, "tooltip")
    SQL = "Update DtDiagram set FamilyId = NULL where DiagramName = '%s'" % (diagramName)
    system.db.runUpdateQuery(SQL, database=db)
    refreshDiagramTree(rootContainer, db)
    refreshHierarchyTree(rootContainer, db)
    
def mouseReleasedCallbackForApplicationHierarchyTree(event):
    '''
    I want to post a popup menu on a right-click because the left-click is used to select a node.      The problem with the 
    right-click is that it doesn't change the selection AND I can't determine what they right-clicked on.  So if the 5th item 
    is selected, and they right-click on the 2md item, the 5th item is still the selected item and I can't determine what item 
    they right-clicked on.  I can get the x and y coordinates, but I find them to be useless...  I can't find a way to translate
    from x, y coordinates to a node in the tree.
    '''
    
    log.infof("In %s.mouseReleasedCallbackForApplicationHierarchyTree() - button: %s, popup: %s, click-count: %d, x: %d, y: %d", 
              __name__, event.button, str(event.popupTrigger), event.clickCount, event.x, event.y)
    
    tree = event.source
    
    if int(event.button) == 1:
        tree.lastSelectedMouseClickY = event.y

    ''' Only post the popup on the right mouse button '''
    if int(event.button) <> 3:
        log.infof("...not a right-click...")
        return

    ''' Things I tried to get the node that they right-clicked on '''
    #tree = event.source
    #print tree
    
    #print "DIR: ", dir(tree)
    
    #swingTree = tree.getComponent()
    #print "Swing Tree: ", swingTree
    
    #components = tree.getComponents()
    #print "Components: ", components
    
    #selectedPath = tree.getPathForLocation(event.x, event.y)
    #print "The selected Path is: ", selectedPath

    if abs(event.y - tree.lastSelectedMouseClickY) > CLICK_THRESHOLD and int(tree.selectedItem) >= 0:
        log.infof("The right-click is not close enough to the last left click")
        return

    #''' Until I figure out how to get the actual thing that they right clicked on, disable POPUPs '''
    #log.infof("...POPUPs are not enabled...")
    #return
    
    ''' Callbacks from the popups '''
    def addApplicationPopupCallback(event):
        window = system.nav.openWindowInstance("DiagToolkit/Application Editor", {"applicationId": -1})
        system.nav.centerWindow(window)

    def addFamilyPopupCallback(event):
        db = getDatabase()
        tree = event.source
        selectedPath = tree.selectedPath
        tokens = selectedPath.split("/")
        nodeType = tree.selectedNodeType
        log.infof("%s - %s", nodeType, selectedPath)
    
        applicationName = tokens[1]
        applicationId = fetchApplicationId(applicationName, db)
        window = system.nav.openWindowInstance("DiagToolkit/Family Editor", {"applicationId": applicationId, "familyId": -1})
        system.nav.centerWindow(window)
        
    def editApplicationPopupCallback(event):
        editCallback(event)
        
    def deleteApplicationPopupCallback(event):
        deleteCallback(event)

    def editFamilyPopupCallback(event):
        editCallback(event)
        
    def deleteFamilyPopupCallback(event):
        deleteCallback(event)

    def disassociateDiagramCallback(event):
        removeDiagramCallback(event.source.parent.parent)

    def editFinalDiagnosisCallback(event):
        editCallback(event)
        
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


    ''' The popup menu depends on the type of node that was selected '''
    tree = event.source            
    selectedNodeType = tree.selectedNodeType
    log.infof("Node type is: %s", selectedNodeType)
    if selectedNodeType == ROOT_TYPE:
        log.infof("Selected the root")
        menu = system.gui.createPopupMenu(["Expand", "Add Application"], [expandCallback, addApplicationPopupCallback])
        menu.show(event)
        
    elif selectedNodeType == APPLICATION_TYPE:
        log.infof("Selected an Application") 
        menu = system.gui.createPopupMenu(["Expand", "Edit Application", "Delete Application", "Add Family"], [expandCallback, editApplicationPopupCallback, deleteApplicationPopupCallback, addFamilyPopupCallback])
        menu.show(event)
    
    elif selectedNodeType == FAMILY_TYPE:
        log.infof("Selected a Family")
        menu = system.gui.createPopupMenu(["Expand", "Edit Family","Delete Family"], [expandCallback, editFamilyPopupCallback, deleteFamilyPopupCallback])
        menu.show(event)
    
    elif selectedNodeType == DIAGRAM_TYPE:
        log.infof("Selected a Diagram") 
        menu = system.gui.createPopupMenu(["Expand", "Remove from Family"], [expandCallback, disassociateDiagramCallback])
        menu.show(event)
        
    elif selectedNodeType == FINAL_DIAGNOSIS_TYPE:
        log.infof("Selected a Final Diagnosis") 
        menu = system.gui.createPopupMenu(["Edit Final Diagnosis"], [editFinalDiagnosisCallback])
        menu.show(event)

    ''' 
    This idea came from IA (Spencer Greco #50776).  It works fine if there isn't a popup!
    As soon as I post a popup it no longer works 
    '''
    #from java.awt import Robot
    #from java.awt.event import KeyEvent
    #from java.awt.event import InputEvent
    
    # Robot function simulates mouse/keyboard events. 
    # add an if statement to check if a left or right click has taken place.

    #print "Simulating a left-click"
    #robot = Robot()
    #robot.mousePress(InputEvent.BUTTON1_DOWN_MASK)
    
    
def mouseReleasedCallbackForDiagramTree(event):
    '''
    I want to post a popup menu on a right-click because the left-click is used to select a node.      The problem with the 
    right-click is that it doesn't change the selection AND I can't determine what they right-clicked on.  So if the 5th item 
    is selected, and they right-click on the 2md item, the 5th item is still the selected item and I can't determine what item 
    they right-clicked on.  I can get the x and y coordinates, but I find them to be useless...  I can't find a way to translate
    from x, y coordinates to a node in the tree.
    '''
    
    log.infof("In %s.mouseReleasedCallbackForDiagramTree() - button: %s, popup: %s, click-count: %d, x: %d, y: %d", 
              __name__, event.button, str(event.popupTrigger), event.clickCount, event.x, event.y)
    
    tree = event.source
    
    if int(event.button) == 1:
        tree.lastSelectedMouseClickY = event.y

    ''' Only post the popup on the right mouse button '''
    if int(event.button) <> 3:
        log.infof("...not a right-click...")
        return

    if abs(event.y - tree.lastSelectedMouseClickY) > CLICK_THRESHOLD and int(tree.selectedItem) >= 0:
        log.infof("The right-click is not close enough to the last left click")
        return

    #''' Until I figure out how to get the actual thing that they right clicked on, disable POPUPs '''
    #log.infof("...POPUPs are not enabled...")
    #return
    
    ''' Callbacks from the popups '''        
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


    ''' The popup menu depends on the type of node that was selected '''
    tree = event.source            

    menu = system.gui.createPopupMenu(["Expand"], [expandCallback])
    menu.show(event)

def propertyChangedForDiagramTree(event):
    print "*** the selected path has changed to: ", event.newValue
    tree = event.source
    if event.newValue == -1:
        tree.selectedDiagramStatus = "Folder"
    elif event.newValue == 0:
        tree.selectedDiagramStatus = "Root"
    else:
        ds = tree.data
        icon = ds.getValueAt(event.newValue, "icon")

        if icon == DIAGRAM_REFERENCED_ICON:
            tree.selectedDiagramStatus = "Referenced"
        elif icon == DIAGRAM_ICON:
            tree.selectedDiagramStatus = "Stand-Alone"
        else:
            tree.selectedDiagramStatus = "FinalDiagnosis"

def appendPriority(txt, priority):
    txtOut = "%s (%.2f)" % (txt, priority)
    return txtOut
       
def stripPriority(txtIn):
    '''
    Strip the trailing < (%f)> from the text string that is passed in.
    '''
    pos = txtIn.rfind(" (")
    txtOut = txtIn[:pos]
    return txtOut