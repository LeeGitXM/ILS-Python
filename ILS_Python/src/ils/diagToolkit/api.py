'''
Created on Sep 19, 2014

@author: Pete

This module defines the public interface for the Diagnostic Toolkit.
The functions provided here can be called from anywhere in Ignition including calculation methods for final diagnosis.
Unless otherwise noted, all functions can be called from Gateway or client scope.
'''

import system
from ils.queue.commons import getQueueForDiagnosticApplication
from ils.queue.constants import QUEUE_INFO
from ils.common.util import escapeSqlQuotes

log = system.util.getLogger("com.ils.diagToolkit.common")

def setTextOfRecommendation(applicationName, familyName, finalDiagnosisName, textRecommendation, db):
    ''' Return the ProcessDiagram at the specified path '''
    log.infof("Setting the text of recommendation %s - %s - %s to %s", applicationName, familyName, finalDiagnosisName, textRecommendation)
    
    textRecommendation = escapeSqlQuotes(textRecommendation)
    applicationName = escapeSqlQuotes(applicationName)
    familyName = escapeSqlQuotes(familyName)
    finalDiagnosisName = escapeSqlQuotes(finalDiagnosisName)
    
    SQL = "UPDATE FD "\
        "SET FD.TextRecommendation = '%s' "\
        " FROM DtFinalDiagnosis FD, DtFamily F, DtApplication A "\
        " WHERE F.FamilyId = FD.FamilyId "\
        " and A.ApplicationId = F.ApplicationId "\
        " and A.ApplicationName = '%s' "\
        " and F.FamilyName = '%s'"\
        " and FD.FinalDiagnosisName = '%s' " % (textRecommendation, applicationName, familyName, finalDiagnosisName)
 
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, db)


def insertApplicationQueueMessage(applicationName, message, status=QUEUE_INFO, db=""):
    key = getQueueForDiagnosticApplication(applicationName, db)
    from ils.queue.message import insert
    insert(key, status, message)
    
def getManualMove(finalDiagnosisId, db):
    ''' Return the Manual Move amount for the FD which was presumably just entered by the operator at a client'''
    log.infof("Getting the Manual Move amount for FD with id: %d", finalDiagnosisId)
    
    SQL = "SELECT ManualMove from DtFinalDiagnosis where FinalDiagnosisId = %s" % (str(finalDiagnosisId))
 
    log.tracef(SQL)
    manualMove = system.db.runScalarQuery(SQL, db)
    
    if manualMove == None:
        manualMove = 0.0
    
    return manualMove

def resetManualMove(finalDiagnosisId, db):
    ''' Reset the Manual Move amount for the FD '''
    log.infof("Resetting the Manual Move amount for FD with id: %d", finalDiagnosisId)
    
    SQL = "Update DtFinalDiagnosis set ManualMove = 0.0 where FinalDiagnosisId = %s" % (str(finalDiagnosisId))
 
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, db)