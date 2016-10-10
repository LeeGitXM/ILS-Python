'''
Created on Apr 1, 2016

@author: ils
'''

import system

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()"
    database=system.tag.read("[Client]Database").value

    print "The database is: ", database
    
    SQL = "select ApplicationName, FamilyName, SQCDiagnosisName, Status, LastResetTime, SQCDiagnosisUUID, DiagramUUID, ' ' State "\
        " from DtSQCDiagnosisView "\
        " order by ApplicationName, FamilyName, SQCDiagnosisName"
    pds = system.db.runQuery(SQL, database)
    
    table = rootContainer.getComponent("Table")
    table.data = pds

def runTest(rootContainer):
    import system.ils.blt.diagram as diagram
    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
    
    print "In runTest()"

    table = rootContainer.getComponent("Table")
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    
    row = 0
    for record in pds:
        sqcBlockName = record["SQCDiagnosisName"]
        sqcDiagnosisUUID = record["SQCDiagnosisUUID"]
    
        print "Getting SQC info for SQC Diagnosis named: <%s> with id: <%s>" % (sqcBlockName, sqcDiagnosisUUID)
   
        diagramDescriptor=diagram.getDiagramForBlock(sqcDiagnosisUUID)
        if diagramDescriptor == None:
            status="Unable to locate the diagram"
        else:
            diagramId=diagramDescriptor.getId()
            print "Fetching upstream block info for chart <%s> ..." % (str(diagramId))

            # Now get the SQC observation blocks
            blocks=diagram.listBlocksUpstreamOf(diagramId, sqcBlockName)
            if len(blocks) == 0:
                status = "No upstream blocks found"
            else:
                status = "Success"

        ds= system.dataset.setValue(ds, row, "State", status)
        row = row + 1

    table.data = ds
