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

def deleter(path, db=""):
    log.tracef("In %s.deleter() with chart %s...", __name__, path)
    SQL = "delete from DtDiagram where DiagramName = '%s'" % (path)
    log.tracef("...SQL: %s,", SQL)
    rows = system.db.runUpdateQuery(SQL, db)
    log.tracef("...deleted %d rows!", rows)

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
    log.tracef("JSON: %s", json)
    try:
        saver(path, json)
    except:
        txt = catchError(__name__ + ".delete", "Caught an exception while saving")
        log.errorf(txt)
    

def saver(path, json):
    log.tracef("In %s.saver() with chart: %s...", __name__, path)
    db = ""
    diagramId = handleDiagram(path, db)
    x = system.util.jsonDecode(json)
    log.tracef("Decoded JSON: %s", str(x))
    blocks = x.get("blocks", [])
    log.tracef("...found %d blocks", len(blocks))
    fdList = []
    sqcList = []
    for block in blocks:
        blockClass = block.get("className", None)
        blockName = block.get("name", None)
        blockUUID = block.get("id", None)
        log.tracef("  found %s, a %s", blockName, blockClass)
        
        ''' Look for interesting blocks '''
        if blockClass == FINAL_DIAGNOSIS_CLASS:
            log.tracef("...handling a final diagnosis")
            handleFinalDiagnosis(diagramId, blockName, blockUUID, db)
            fdList.append(blockName)
        elif blockClass == SQC_DIAGNOSIS_CLASS:
            log.tracef("...handling a SQC Diagnosis: %s...", str(block))
            handleSQCDiagnosis(diagramId, blockName, blockUUID, db)
            sqcList.append(blockName)
    
    handleDeletedBlocks(diagramId, fdList, sqcList, db)
            
def handleDiagram(path, db):
    SQL = "select DiagramId from DtDiagram where DiagramName = '%s'" % (path)
    diagramId = system.db.runScalarQuery(SQL, db)

    if diagramId == None:
        SQL = "insert into DtDiagram (DiagramName) values ('%s')" % (path)
        log.tracef("...SQL: %s,", SQL)
        diagramId = system.db.runUpdateQuery(SQL, db, getKey=1)
        log.infof("Inserted a new diagram with id: %d", diagramId)

    return diagramId

def handleFinalDiagnosis(diagramId, finalDiagnosisName, finalDiagnosisUUID, db):
    '''
    This handles inserting a new final diagnosis and renaming an existing final diagnosis.
    '''
    SQL = "select FinalDiagnosisId, FinalDiagnosisName, DiagramId "\
        " from DtFinalDiagnosis "\
        " where DiagramId = '%s' "\
        " and FinalDiagnosisUUID = '%s' " % (diagramId, finalDiagnosisUUID)
    pds = system.db.runQuery(SQL, db)
    oldFinalDiagnosisName = system.db.runScalarQuery(SQL, db)

    if len(pds) == 0:
        SQL = "insert into DtFinalDiagnosis (FinalDiagnosisName, FinalDiagnosisUUID, DiagramId, FinalDiagnosisPriority, PostTextRecommendation, "\
            "RefreshRate, Active, ShowExplanationWithRecommendation, Constant, ManualMoveAllowed, TrapInsignificantRecommendations) "\
            "values ('%s', '%s', %d, %f, %d, %d, %d, %d, %d, %d, %d)" % \
            (finalDiagnosisName, finalDiagnosisUUID, diagramId, FINAL_DIAGNOSIS_PRIORITY, POST_TEXT_RECOMMENDATION, REFRESH_RATE, ACTIVE, 
             SHOW_EXPLANATION_WITH_RECOMMENDATION, CONSTANT, MANUAL_MOVE_ALLOWED, TRAP_INSIGNIFICANT_RECOMMENDATIONS)

        log.tracef("...SQL: %s,", SQL)
        finalDiagnosisId = system.db.runUpdateQuery(SQL, db, getKey=1)
        log.infof("Inserted a new Final Diagnosis with id: %d", finalDiagnosisId)
    else:
        record = pds[0]
        finalDiagnosisId = record["FinalDiagnosisId"]
        oldFinalDiagnosisName = record["FinalDiagnosisName"]

        if oldFinalDiagnosisName != finalDiagnosisName:
            ''' This handles the case where they have renamed the Final Diagnosis '''
            SQL = "update DtFinalDiagnosis set FinalDiagnosisName = '%s' where FinalDiagnosisId = %d" % (finalDiagnosisName, finalDiagnosisId)
            log.tracef("...SQL: %s,", SQL)
            system.db.runUpdateQuery(SQL, db)
            log.infof("Renamed an existing Final Diagnosis from %s to %s!", oldFinalDiagnosisName, finalDiagnosisName)
        else:
            log.tracef("...the database is already up to date...")


def handleSQCDiagnosis(diagramId, sqcDiagnosisName, sqcDiagnosisUUID, db):
    '''
    This handles inserting a new SQC diagnosis and renaming an existing SQC diagnosis.
    '''
    SQL = "select SQCDiagnosisId, SQCDiagnosisName, DiagramId "\
        " from DtSQCDiagnosis "\
        " where DiagramId = %s "\
        " and SQCDiagnosisUUID = '%s' " % (diagramId, sqcDiagnosisUUID)
    pds = system.db.runQuery(SQL, db)
    
    if len(pds) == 0:
        SQL = "insert into DtSQCDiagnosis (SQCDiagnosisName, SQCDiagnosisUUID, DiagramId, Status) "\
            " values ('%s', '%s', %d, '%s')" % \
            (sqcDiagnosisName, sqcDiagnosisUUID, diagramId, SQC_STATUS)

        log.tracef("...SQL: %s,", SQL)
        sqcDiagnosisId = system.db.runUpdateQuery(SQL, db, getKey=1)
        log.tracef("Inserted a new SQC Diagnosis with id: %d", sqcDiagnosisId)
    else:
        record = pds[0]
        sqcDiagnosisId = record["SQCDiagnosisId"]
        oldSqcDiagnosisName = record["SQCDiagnosisName"]

        if oldSqcDiagnosisName != sqcDiagnosisName:
            ''' This handles the case where they have renamed the SQC Diagnosis '''
            SQL = "update DtSQCDiagnosis set SQCDiagnosisName = '%s' where SQCDiagnosisId = %d" % (sqcDiagnosisName, sqcDiagnosisId)
            log.tracef("...SQL: %s,", SQL)
            rows = system.db.runUpdateQuery(SQL, db)
            log.tracef("Updated %d rows in DtSQCDiagnosis...", rows)
        else:
            log.tracef("...the database is already up to date...")


def handleDeletedBlocks(diagramId, fdList, sqcList, db):

    ''' 
    --- Handle Final Diagnosis ---
    Select all of the FDs on this diagram in the DB and compare it to the list of FDs on the diagram.
    Anything in the DB but not on the diagram should be deleted.
    '''
    SQL = "select FinalDiagnosisId, FinalDiagnosisName from DtFinalDiagnosis where DiagramId = %d" % (diagramId)
    pds = system.db.runQuery(SQL, db)
    for record in pds:
        fdName = record["FinalDiagnosisName"]
        if fdName not in fdList:
            log.infof("Deleting final diagnosis named: %s" % (fdName))
            fdId = record["FinalDiagnosisId"]
            SQL = "Delete from DtFinalDiagnosis where FinalDiagnosisId = %d" % (fdId)
            rows = system.db.runUpdateQuery(SQL, db)
            log.tracef("...deleted %d rows!", rows)
            
    ''' 
    --- Handle SQC Diagnosis ---
    Select all of the SQC Diagnosis on this diagram in the DB and compare it to the list of SQC Diagnosis on the diagram.
    Anything in the DB but not on the diagram should be deleted.
    '''
    SQL = "select SQCDiagnosisId, SQCDiagnosisName from DtSQCDiagnosis where DiagramId = %d" % (diagramId)
    pds = system.db.runQuery(SQL, db)
    for record in pds:
        sqcName = record["SQCDiagnosisName"]
        if sqcName not in sqcList:
            log.infof("Deleting SQC diagnosis named: %s" % (sqcName))
            sqcId = record["SQCDiagnosisId"]
            SQL = "Delete from DtSQCDiagnosis where SQCDiagnosisId = %d" % (sqcId)
            rows = system.db.runUpdateQuery(SQL, db)
            log.tracef("...deleted %d rows!", rows)

