'''
Created on Apr 12, 2022

@author: ils
'''
import system
from ils.common.database import lookupIdFromKey

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
    diagramNames = ["App1/Fam1_1/DiagA", "App1/Fam1_1/DiagB", "App1/Fam1_1/DiagC", "App1/Fam1_1/myDiagram", "App1/Fam1_2/DiagD", "App2/Fam2_1/DiagE", 
                    "App2/Fam2_1/DiagF", "App2/Fam2_2/DiagG", "App2/Fam2_2/myDiagram"]
    diagrams = {}
    for diagramName in diagramNames:
        SQL = "insert into DtDiagram (DiagramName) values ('%s')" % (diagramName)
        diagramId = system.db.runUpdateQuery(SQL, getKey=1)
        diagrams[diagramName] = diagramId
    print "Inserted %d flat diagram names!" % (len(diagrams))

    FD_PRIORITY = 8.61
    CONSTANT = False
    POST_TEXT_RECOMMENDATION = False
    REFRESH_RATE = 300
    ACTIVE = False
    MANUAL_MOVE_ALLOWED = True
    TRAP_INSIGNIFICANT_RECOMMENDATIONS = True
    finalDiagnosisDictionary = {}
    for finalDiagnosis in ["App1/Fam1_1/DiagA:FD_A1", "App1/Fam1_1/DiagA:FD_A2", "App1/Fam1_1/DiagC:FD_C1", "App1/Fam1_1/myDiagram:myFD",
                           "App1/Fam1_2/DiagD:FD_D1", "App1/Fam1_2/DiagD:FD_D2",
                           "App2/Fam2_1/DiagF:FD_F1", 
                           "App2/Fam2_2/DiagG:FD_G1", "App2/Fam2_2/DiagG:FD_G2", "App2/Fam2_2/DiagG:FD_G3", "App2/Fam2_2/myDiagram:myFD"]:
        diagramName = finalDiagnosis[:finalDiagnosis.find(":")]
        diagramId = diagrams.get(diagramName)
        finalDiagnosisName = finalDiagnosis[finalDiagnosis.find(":")+1:]
        SQL = "Insert into DtFinalDiagnosis(FinalDiagnosisName, DiagramId, FinalDiagnosisPriority, Constant, PostTextRecommendation, RefreshRate, "\
            "Active, ManualMoveAllowed, TrapInsignificantRecommendations) "\
            "values (?,?,?,?,?,?,?,?,?)"
        vals = [finalDiagnosisName, diagramId, FD_PRIORITY, CONSTANT, POST_TEXT_RECOMMENDATION, REFRESH_RATE, ACTIVE, MANUAL_MOVE_ALLOWED, TRAP_INSIGNIFICANT_RECOMMENDATIONS]
        finalDiagnosisId = system.db.runPrepUpdate(SQL, vals, getKey=1)
        finalDiagnosisDictionary[finalDiagnosisName] = finalDiagnosisId
    
    print "Final Diagnosis: ", finalDiagnosisDictionary
     
    
    
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
    
    applicationId = applications.get("Application 1", -1)
    feedbackMethodId = lookupIdFromKey("FeedbackMethod", "Average")
    
    SQL = "Insert into DtQuantOutput(ApplicationId, QuantOutputName, TagPath, MostNegativeIncrement, MostPositiveIncrement, "\
        "IgnoreMinimumIncrement, MinimumIncrement, SetpointHighLimit, SetpointLowLimit, FeedbackMethodId, IncrementalOutput) "\
        "values (%d, 'Q100', 'DiagmosticToolkit/TESTAPP1/Outputs/TC100', -20, 20, 0, 0.01, 200.0, 20.0, %d, 0)"\
         % (applicationId, feedbackMethodId)
    system.db.runUpdateQuery(SQL)
    
    SQL = "Insert into DtQuantOutput(ApplicationId, QuantOutputName, TagPath, MostNegativeIncrement, MostPositiveIncrement, "\
        "IgnoreMinimumIncrement, MinimumIncrement, SetpointHighLimit, SetpointLowLimit, FeedbackMethodId, IncrementalOutput) "\
        "values (%d, 'Q101', 'DiagmosticToolkit/TESTAPP1/Outputs/TC101', -20, 20, 0, 0.01, 200.0, 20.0, %d, 0)"\
         % (applicationId, feedbackMethodId)
    system.db.runUpdateQuery(SQL)


    
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