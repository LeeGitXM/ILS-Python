'''
Created on Dec 12, 2016

@author: phass
'''

import system
from ils.log import getLogger
log = getLogger(__name__)
from ils.blt.api import getBlockState
from ils.io.util import readTag
from ils.common.util import getDate, formatDateTime

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()"
    database=readTag("[Client]Database").value

    print "The database is: ", database
    
    SQL = "select ApplicationName, FamilyName, DiagramName, SQCDiagnosisName, Status, LastResetTime, ' ' State "\
        " from DtSQCDiagnosisView "\
        " order by ApplicationName, FamilyName, DiagramName, SQCDiagnosisName"
    pds = system.db.runQuery(SQL, database)
    
    table = rootContainer.getComponent("Power Table")
    table.data = pds
    
    rootContainer.getComponent("Last Updated").text = formatDateTime(getDate(),'MM/dd/yyyy HH:mm:ss')


def runTest(rootContainer):
    log.infof("In runTest()")

    table = rootContainer.getComponent("Power Table")
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    
    row = 0
    for record in pds:
        sqcBlockName = record["SQCDiagnosisName"]
        diagramName = record["DiagramName"]
    
        log.infof("Getting SQC info for SQC Diagnosis named <%s> on <%s>", sqcBlockName, diagramName)
        blockState = getBlockState(diagramName, sqcBlockName)
        log.infof("...%s", blockState)

        ds= system.dataset.setValue(ds, row, "State", blockState)
        row = row + 1

    table.data = ds
