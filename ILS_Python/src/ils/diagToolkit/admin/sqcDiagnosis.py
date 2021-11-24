'''
Created on Dec 12, 2016

@author: phass
'''

import system
from ils.io.util import readTag
from ils.common.util import getDate, formatDateTime

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()"
    database=readTag("[Client]Database").value

    print "The database is: ", database
    
    SQL = "select ApplicationName, FamilyName, SQCDiagnosisName, Status, LastResetTime, SQCDiagnosisUUID, DiagramUUID, ' ' State "\
        " from DtSQCDiagnosisView "\
        " order by ApplicationName, FamilyName, SQCDiagnosisName"
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
        sqcBlockName = record["SQCDiagnosisName"]
        sqcDiagnosisUUID = record["SQCDiagnosisUUID"]
    
        print "Getting SQC info for SQC Diagnosis named: <%s> with id: <%s>" % (sqcBlockName, sqcDiagnosisUUID)
        
        try:
            if sqcDiagnosisUUID in [None, ""]:
                status="Incomplete"
            else:
                diagramDescriptor=diagram.getDiagramForBlock(sqcDiagnosisUUID)
                if diagramDescriptor == None:
                    status="Unable to locate the diagram"
                else:
                    diagramId=diagramDescriptor.getId()
                    print "Fetching upstream block info for chart <%s> ..." % (str(diagramId))
        
                    # Now get the SQC observation blocks (There must be SQC observations upstream of a SQC diagnosis)
                    blocks=diagram.listBlocksUpstreamOf(diagramId, sqcBlockName)
                    if len(blocks) == 0:
                        status = "No upstream blocks found"
                    else:
                        status = "Success"
        except:
            status = "Error"

        ds= system.dataset.setValue(ds, row, "State", status)
        row = row + 1

    table.data = ds
