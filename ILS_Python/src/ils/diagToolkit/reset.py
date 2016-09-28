'''
Created on Sep 18, 2016

@author: Pete
'''

import system
log = system.util.getLogger("com.ils.diagToolkit.reset")

def resetApplication(application, database, tagProvider):
    log.info("Resetting application: %s" % (application)) 
    
    # Fetch all of the SQC Diagnosis for this family 
    SQL = "select FD.FinalDiagnosisId, FD.FinalDiagnosisName, FD.FamilyId, FD.FinalDiagnosisPriority, "\
        " FD.CalculationMethod, FD.UUID, FD.DiagramUUID, "\
        " FD.PostTextRecommendation, FD.PostProcessingCallback, FD.RefreshRate, FD.TextRecommendation "\
        " from TkUnit U, DtSQCDiagnosis SD, DtFamily F, DtApplication A"\
        " where U.UnitId = A.UnitId "\
        " and A.ApplicationId = F.ApplicationId "\
        " and SD.FamilyId = F.FamilyId "\
        " and A.ApplicationName = '%s'" % (application)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    log.trace("Fetched %i final diagnosis" % (len(pds)))