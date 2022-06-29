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
    
    SQL = "select ApplicationName, FamilyName, FinalDiagnosisName, FamilyPriority, FinalDiagnosisPriority, Constant, "\
        " Active, LastRecommendationTime, TimeOfMostRecentRecommendationImplementation, DiagramUUID, FinalDiagnosisUUID, "\
        " ' ' State "\
        " from DtFinalDiagnosisView "\
        " order by ApplicationName, FamilyName, FinalDiagnosisName"
    pds = system.db.runQuery(SQL, database)
    
    table = rootContainer.getComponent("Power Table")
    table.data = pds
    
    rootContainer.getComponent("Last Updated").text = formatDateTime(getDate(),'MM/dd/yyyy HH:mm:ss')

def runTest(rootContainer):
    import system.ils.blt.diagram as diagram
    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
       
    log.infof("In %s.runTest()", __name__)

    table = rootContainer.getComponent("Power Table")
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    
    row = 0
    for record in pds:
        fdName = record["FinalDiagnosisName"]
        fdUUID = record["FinalDiagnosisUUID"]
    
        log.infof("Getting info for Final Diagnosis named: <%s> with id: <%s>", fdName, fdUUID)
   
        diagramDescriptor=diagram.getDiagramForBlock(fdUUID)
        if diagramDescriptor == None:
            status="Unable to locate the diagram"
        else:
            diagramId=diagramDescriptor.getId()
            status = "Success"

        ds= system.dataset.setValue(ds, row, "State", status)
        row = row + 1

    table.data = ds
