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
    
    print "Hello"