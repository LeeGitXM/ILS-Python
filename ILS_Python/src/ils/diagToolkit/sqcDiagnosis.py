'''
Created on June 16, 2015
'''
import system

from ils.log import getLogger
log = getLogger(__name__)

def getSqcDiagnosisLabelByName(sqcDiagnosisName, db=""):
    SQL = "select sqcDiagnosisLabel from DtSqcDiagnosis where sqcDiagnosisName = '%s'" % (sqcDiagnosisName)
    label = system.db.runScalarQuery(SQL, db)
    return label