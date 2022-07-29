'''
Created on Jun 15, 2022

@author: ils

These run in the Designer as a result of actions taken in the Designer.  They are called when the project is saved.
'''

import system

from ils.common.error import catchError
from ils.log import getLogger
log = getLogger(__name__)

FINAL_DIAGNOSIS_CLASS = "ils.block.finaldiagnosis.FinalDiagnosis"
SQC_DIAGNOSIS_CLASS = "ils.block.sqcdiagnosis.SQCDiagnosis"

''' Default Values '''
FINAL_DIAGNOSIS_PRIORITY = 0.0
POST_TEXT_RECOMMENDATION = 0
REFRESH_RATE = 300
ACTIVE = 0
SHOW_EXPLANATION_WITH_RECOMMENDATION = 0
CONSTANT = 0
MANUAL_MOVE_ALLOWED = 0
TRAP_INSIGNIFICANT_RECOMMENDATIONS = 0
SQC_STATUS = "UNKNOWN"

def delete(path):
    log.infof("In %s.delete(), chart %s has been deleted", __name__, path)
    try:
        deleter(path)
    except:
        txt = catchError(__name__ + ".delete", "Caught an exception while deleting")
        log.errorf(txt)

def deleter(path):
    log.infof("In %s.deleter(), chart %s has been deleted", __name__, path)

def rename(oldPath, newPath):
    log.infof("In %s.rename(), chart %s has been renamed to %s", __name__, oldPath, newPath)
    
    try:
        renamer()
    except:
        txt = catchError(__name__ + ".delete", "Caught an exception while renaming")
        log.errorf(txt)

def renamer(oldPath, newPath):
    print "***** In renamer"
        

def save(path, json):
    log.infof("In %s.save(), chart %s has been saved", __name__, path)
    log.infof("JSON: %s", json)
    try:
        saver(path, json)
    except:
        txt = catchError(__name__ + ".delete", "Caught an exception while saving")
        log.errorf(txt)
    

def saver(path, json):
    db = ""
    diagramId = handleDiagram(path, db)
    x = system.util.jsonDecode(json)
    print "Decoded JSON: ", x
    blocks = x.get("blocks", [])
    log.infof("Found %d blocks", len(blocks))
    for block in blocks:
        blockClass = block.get("className", None)
        blockName = block.get("name", None)
        blockUUID = block.get("id", None)
        log.infof("  found %s, a %s", blockName, blockClass)
        
        ''' Look for interesting blocks '''
        if blockClass == FINAL_DIAGNOSIS_CLASS:
            print "handling a final diagnosis"
            handleFinalDiagnosis(diagramId, blockName, blockUUID, db)
        elif blockClass == SQC_DIAGNOSIS_CLASS:
            print "handling a SQC Diagnosis"
            print "SQC block: ", str(block)
            handleSQCDiagnosis(diagramId, blockName, blockUUID, db)
            
def handleDiagram(path, db):
    SQL = "select DiagramId from DtDiagram where DiagramName = '%s'" % (path)
    diagramId = system.db.runScalarQuery(SQL, db)

    if diagramId == None:
        SQL = "insert into DtDiagram (DiagramName) values ('%s')" % (path)
        log.infof("...SQL: %s,", SQL)
        diagramId = system.db.runUpdateQuery(SQL, db, getKey=1)
        log.infof("Inserted a new diagram with id: %d", diagramId)

    return diagramId

def handleFinalDiagnosis(diagramId, finalDiagnosisName, finalDiagnosisUUID, db):
    SQL = "select FinalDiagnosisId, FinalDiagnosisName, DiagramId from DtFinalDiagnosis where DiagramId = '%s' "\
        "and FinalDiagnosisUUID = '%s' " % (diagramId, finalDiagnosisUUID)
    pds = system.db.runQuery(SQL, db)
    oldFinalDiagnosisName = system.db.runScalarQuery(SQL, db)

    if len(pds) == 0:
        SQL = "insert into DtFinalDiagnosis (FinalDiagnosisName, FinalDiagnosisUUID, DiagramId, FinalDiagnosisPriority, PostTextRecommendation, "\
            "RefreshRate, Active, ShowExplanationWithRecommendation, Constant, ManualMoveAllowed, TrapInsignificantRecommendations) "\
            "values ('%s', '%s', %d, %f, %d, %d, %d, %d, %d, %d, %d)" % \
            (finalDiagnosisName, finalDiagnosisUUID, diagramId, FINAL_DIAGNOSIS_PRIORITY, POST_TEXT_RECOMMENDATION, REFRESH_RATE, ACTIVE, 
             SHOW_EXPLANATION_WITH_RECOMMENDATION, CONSTANT, MANUAL_MOVE_ALLOWED, TRAP_INSIGNIFICANT_RECOMMENDATIONS)

        log.infof("...SQL: %s,", SQL)
        finalDiagnosisId = system.db.runUpdateQuery(SQL, db, getKey=1)
        log.infof("Inserted a new Final Diagnosis with id: %d", finalDiagnosisId)
    else:
        record = pds[0]
        finalDiagnosisId = record["FinalDiagnosisId"]
        oldFinalDiagnosisName = record["FinalDiagnosisName"]

        if oldFinalDiagnosisName != finalDiagnosisName:
            ''' This handles the case where they have renamed the Final Diagnosis '''
            SQL = "update DtFinalDiagnosis set FinalDiagnosisName = '%s' where FinalDiagnosisId = %d" % (finalDiagnosisName, finalDiagnosisId)
            log.infof("...SQL: %s,", SQL)
            rows = system.db.runUpdateQuery(SQL, db)
            log.infof("Updated %d rows in DtFinalDiagnosis...", rows)
        else:
            log.infof("...the database is already up to date...")


def handleSQCDiagnosis(diagramId, sqcDiagnosisName, sqcDiagnosisUUID, db):

    SQL = "select SQCDiagnosisId, SQCDiagnosisUUID "\
        " from DtSQCDiagnosis where DiagramId = %s "\
        "  and SQCDiagnosisName = '%s' " % (diagramId, sqcDiagnosisName)
    pds = system.db.runQuery(SQL, db)

    '''
    How is a copied SQC Diagnosis handled here?
    '''
    
    if len(pds) == 0:
        SQL = "insert into DtSQCDiagnosis (SQCDiagnosisName, SQCDiagnosisUUID, DiagramId, Status) "\
            " values ('%s', '%s', %d, '%s')" % \
            (sqcDiagnosisName, sqcDiagnosisUUID, diagramId, SQC_STATUS)

        log.infof("...SQL: %s,", SQL)
        finalDiagnosisId = system.db.runUpdateQuery(SQL, db, getKey=1)
        log.infof("Inserted a new Final Diagnosis with id: %d", finalDiagnosisId)
    else:
        record = pds[0]
        oldSqcDiagnosisUUID = record["SQCDiagnosisUUID"]
        
        ''' This handles the case where they have renamed the SQC Diagnosis '''
        '''
        if oldSqcDiagnosisUUID != finalDiagnosisName:
            
            SQL = "update DtFinalDiagnosis set FinalDiagnosisName = '%s' where FinalDiagnosisId = %d" % (finalDiagnosisName, finalDiagnosisId)
            log.infof("...SQL: %s,", SQL)
            rows = system.db.runUpdateQuery(SQL, db)
            log.infof("Updated %d rows in DtFinalDiagnosis...", rows)
        else:
            log.infof("...the database is already up to date...")
        '''            
    return
