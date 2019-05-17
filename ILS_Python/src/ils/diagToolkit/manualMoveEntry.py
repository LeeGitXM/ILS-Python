'''
Created on Jan 13, 2019

@author: phass
'''

import system
from ils.common.config import getDatabaseClient, getTagProviderClient
from ils.diagToolkit.finalDiagnosis import manageFinalDiagnosis

def internalFrameOpened(rootContainer):
    print "In %s.internalFrameOpened()" % (__name__)

def okAction(event):
    rootContainer = event.source.parent
    print "In %s.okAction()" % (__name__)
    
    db = getDatabaseClient()
    finalDiagnosisId = rootContainer.finalDiagnosisId
    
    SQL = "select ApplicationName, FamilyName from DtFinalDiagnosisView where FinalDiagnosisId = %s" % str(finalDiagnosisId)
    pds = system.db.runQuery(SQL, db)
    record = pds[0]
    
    manualMove = rootContainer.getComponent("Manual Move Field").floatValue
    increase = rootContainer.getComponent("Move Direction Container").getComponent("Radio Button Increase").selected
    if not(increase):
        manualMove = -1.0 * manualMove
    
    if manualMove == 0.0:
        system.gui.messageBox("Please enter a non-zero move!")
        return
    
    print "Updating the final diagnosis in the database..."
    SQL = "update DtFinalDiagnosis set ManualMove = %s where FinalDiagnosisId = %s" % (str(manualMove), str(finalDiagnosisId))
    system.db.runUpdateQuery(SQL, db)
    
    finalDiagnosisName = rootContainer.finalDiagnosisName
    applicationName = record["ApplicationName"]
    familyName = record["FamilyName"]
    database = getDatabaseClient()
    provider = getTagProviderClient()
    
    manageFinalDiagnosis(applicationName, familyName, finalDiagnosisName, database, provider)
    
    system.nav.closeParentWindow(event)
    

'''
This can be called from the gateway in a FD calculation method.
'''
def fetchManualMoveInfo(finalDiagnosisName, db):
    print "In %s.fetchManualMoveInfo()" % (__name__)

    SQL = "select ManualMoveAllowed, ManualMove from DtFinalDiagnosis where FinalDiagnosisName = '%s' " % str(finalDiagnosisName)
    pds = system.db.runQuery(SQL, db)
    record = pds[0]
    
    manualMove = record["ManualMove"]
    manualMoveAllowed = record["ManualMoveAllowed"]

    return manualMove, manualMoveAllowed
