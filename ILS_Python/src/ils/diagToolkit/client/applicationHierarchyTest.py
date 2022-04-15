'''
Created on Apr 12, 2022

@author: ils
'''
import system

APPLICATION_ICON = "Custom/sfcLibrary.png"
FAMILY_ICON = "Custom/sfc.png"
DIAGRAM_ICON = "Custom/sfcCycle.png"
FINAL_DIAGNOSIS_ICON = "default"
WHITE = "color(255,255,255,255)"
BLACK = "color(0,0,0,255)"
MUSTARD = "color(250,214,138,255)"

def resetDatabase():
    tables = ["DtTextRecommendation", "DtDiagnosisEntry", "DtRecommendation", "DtRecommendationDefinition", "DtSQCDiagnosis", "DtFinalDiagnosis", "DtDiagram", "DtFamily", "DtApplication"]
    for table in tables:
        SQL = "delete from %s" % (table)
        rows = system.db.runUpdateQuery(SQL)
        print "Deleted %d rows from %s" % (rows, table)

def insertFlatDiagramNames():
    diagrams = ["DiagA", "DiagB", "DiagC", "DiagD", "DiagE", "DiagF", "DiagG"]
    for diagram in diagrams:
        SQL = "insert into DtDiagram (DiagramName) values ('%s')" % (diagram)
        system.db.runUpdateQuery(SQL)
    print "Inserted %d flat diagram names!" % (len(diagrams))

def insertTreeDiagramNames():
    diagrams = ["App1/Fam1_1/DiagA", "App1/Fam1_1/DiagB", "App1/Fam1_1/DiagC", "App1/Fam1_2/DiagD", "App2/Fam2_1/DiagE", "App2/Fam2_1/DiagF", "App2/Fam2_2/DiagG"]
    for diagram in diagrams:
        SQL = "insert into DtDiagram (DiagramName) values ('%s')" % (diagram)
        system.db.runUpdateQuery(SQL)
    print "Inserted %d flat diagram names!" % (len(diagrams)) 
    
    
def insertHierarchy():
    unitId = system.db.runScalarQuery("Select min(UnitId) from TkUnit")
    print "Fetched unit id: ", unitId
    
    applications = {}
    for applicationName in ["Application 1", "Application 2", "Application 3"]:
        SQL = "Insert into DtApplication(ApplicationName, UnitId) values ('%s', %d)" % (applicationName, unitId)
        applicationId = system.db.runUpdateQuery(SQL, getKey=1)
        applications[applicationName] = applicationId
    
    print "Applications: ", applications
    
    families = {}
    FAMILY_PRIORITY = 3.7
    for family in ["Application 1:Family1_1", "Application 1:Family1_2", "Application 1:FamilyX", "Application 2:Family2_1", "Application 2:Family2_2", "Application 2:FamilyX"]:
        applicationName = family[:family.find(":")]
        applicationId = applications.get(applicationName)
        familyName = family[family.find(":")+1:]
        SQL = "Insert into DtFamily(FamilyName, ApplicationId, FamilyPriority) values ('%s', %d, %f)" % (familyName, applicationId, FAMILY_PRIORITY)
        familyId = system.db.runUpdateQuery(SQL, getKey=1)
        families[familyName] = familyId
    
    print "Families: ", families
    
def refreshHierarchyTreeTest(rootContainer, db=""):
    rows = []
    
    rows.append(["","A", APPLICATION_ICON,WHITE,BLACK,"A","","",APPLICATION_ICON,MUSTARD,BLACK,"",""])
    rows.append(["A","B", FAMILY_ICON,WHITE,BLACK,"A","","",FAMILY_ICON,MUSTARD,BLACK,"",""])
    rows.append(["A/B","C", DIAGRAM_ICON,WHITE,BLACK,"A","","",DIAGRAM_ICON,MUSTARD,BLACK,"",""])
    rows.append(["A/B/C","D", FINAL_DIAGNOSIS_ICON,WHITE,BLACK,"A","","",FINAL_DIAGNOSIS_ICON,MUSTARD,BLACK,"",""])

    header = ["path", "text", "icon", "background", "foreground", "tooltip", "border", "selectedText", "selectedIcon", "selectedBackground", "selectedForeground", "selectedTooltip", "selectedBorder"]
    ds = system.dataset.toDataSet(header, rows)
    treeWidget = rootContainer.getComponent("Hierarchy Tree")
    treeWidget.data = ds