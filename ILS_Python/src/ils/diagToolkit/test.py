'''
Created on Jun 14, 2016

@author: ils
'''
'''
Created on Apr 1, 2016

@author: ils
'''

import system

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()"
    database=system.tag.read("[Client]Database").value

    print "The database is: ", database
    
    # Populate the list of all consoles - the selected console is passed from the console window and should be in the list
    SQL = "select ApplicationName, FamilyName, FinalDiagnosisName, FamilyPriority, FinalDiagnosisPriority, " \
        " Constant, Active, LastRecommendationTime, TimeOfMostRecentRecommendationImplementation, UUId, DiagramUUID,  ' ' Status "\
        " from DtFinalDiagnosisView "\
        " order by ApplicationName, FamilyName, FinalDiagnosisName"
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
        blockName = record["FinalDiagnosisName"]
        blockId = record["UUId"]
    
        print "Getting info for Final Diagnosis named: <%s> with id: <%s>" % (blockName, blockId)
   
        diagramDescriptor=diagram.getDiagramForBlock(blockId)
        if diagramDescriptor == None:
            status="Unable to locate the diagram"
        else:
            diagramId=diagramDescriptor.getId()
            print "Fetched diagram Id: %s ..." % (str(diagramId))

            # Now get the SQC observation blocks
            if diagramId == record["DiagramUUID"]:
                status = "Success"
            else:
                status = "The diagram UUID from the diagram does not match the database"

        ds= system.dataset.setValue(ds, row, "Status", status)
        row = row + 1

    table.data = ds