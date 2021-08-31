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
    
    SQL = "select FinalDiagnosisId, ApplicationName, FamilyName, FinalDiagnosisName, FamilyPriority, FinalDiagnosisPriority, Constant, "\
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

    
def deleteRow(event):
    print "In deleteRow()"
    
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    row = table.selectedRow
    finalDiagnosisId = ds.getValueAt(row, "FinalDiagnosisId")
    finalDiagnosisName = ds.getValueAt(row, "FinalDiagnosisName")

    okToDelete = system.gui.confirm("Are you sure that you want to delete Final Diagnosis named: %s?" % (finalDiagnosisName))
    if okToDelete:
        print "Delete it..."
        database=system.tag.read("[Client]Database").value
        SQL = "delete from DtFinalDiagnosis where FinalDiagnosisId = %d" % (finalDiagnosisId)
        rows = system.db.runUpdateQuery(SQL, database)
        print "Deleted %d rows!" % (rows)
        internalFrameOpened(rootContainer)