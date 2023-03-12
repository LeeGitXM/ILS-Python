'''
Created on Dec 12, 2016

@author: phass
'''

import system

from ils.log import getLogger
log = getLogger(__name__)

from ils.io.util import readTag
from ils.common.util import getDate, formatDateTime

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()", __name__)
    database=readTag("[Client]Database").value

    log.infof("The database is: %s", database)
    
    SQL = "select ApplicationName, FamilyName, DiagramName, FinalDiagnosisName, FamilyPriority, FinalDiagnosisPriority, Constant, "\
        " Active, LastRecommendationTime, TimeOfMostRecentRecommendationImplementation, ' ' State "\
        " from DtFinalDiagnosisView "\
        " order by ApplicationName, FamilyName, DiagramName, FinalDiagnosisName"
    pds = system.db.runQuery(SQL, database)
    
    table = rootContainer.getComponent("Power Table")
    table.data = pds
    
    rootContainer.getComponent("Last Updated").text = formatDateTime(getDate(),'MM/dd/yyyy HH:mm:ss')

def runTest(rootContainer):
    from ils.blt.api import getBlockState
       
    log.infof("In %s.runTest()", __name__)

    table = rootContainer.getComponent("Power Table")
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    
    row = 0
    for record in pds:
        diagramName = record["DiagramName"]
        fdName = record["FinalDiagnosisName"]
    
        log.infof("Getting info for Final Diagnosis <%s> on <%s>", fdName, diagramName)
        blockState = getBlockState(diagramName, fdName)
        log.infof("...%s", blockState)
        
        ds = system.dataset.setValue(ds, row, "State", blockState)
        row = row + 1

    table.data = ds
