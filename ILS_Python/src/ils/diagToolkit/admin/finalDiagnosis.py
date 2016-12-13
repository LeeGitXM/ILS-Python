'''
Created on Dec 12, 2016

@author: phass
'''

import system
from ils.common.util import getDate, formatDateTime

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()"
    database=system.tag.read("[Client]Database").value

    print "The database is: ", database
    
    SQL = "select ApplicationName, FamilyName, FinalDiagnosisName, FamilyPriority, FinalDiagnosisPriority, Constant, "\
        " Active, LastRecommendationTime, TimeOfMostRecentRecommendationImplementation, DiagramUUID, FinalDiagnosisUUID, "\
        " ' ' State "\
        " from DtFinalDiagnosisView "\
        " order by ApplicationName, FamilyPriority, FinalDiagnosisPriority"
    pds = system.db.runQuery(SQL, database)
    
    table = rootContainer.getComponent("Power Table")
    table.data = pds
    
    rootContainer.getComponent("Last Updated").text = formatDateTime(getDate(),'MM/dd/yyyy HH:mm:ss')

def runTest(rootContainer):
    import system.ils.blt.diagram as diagram
    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
       
    print "In runTest()"

    table = rootContainer.getComponent("Power Table")
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    
    row = 0
    for record in pds:
        fdName = record["FinalDiagnosisName"]
        fdUUID = record["FinalDiagnosisUUID"]
    
        print "Getting info for Final Diagnosis named: <%s> with id: <%s>" % (fdName, fdUUID)
   
        diagramDescriptor=diagram.getDiagramForBlock(fdUUID)
        if diagramDescriptor == None:
            status="Unable to locate the diagram"
        else:
            diagramId=diagramDescriptor.getId()
            status = "Success"

        ds= system.dataset.setValue(ds, row, "State", status)
        row = row + 1

    table.data = ds
