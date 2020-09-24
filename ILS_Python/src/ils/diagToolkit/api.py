'''
Created on Sep 19, 2014

@author: Pete

This module defines the public interface for the Diagnostic Toolkit.
The functions provided here can be called from anywhere in Ignition including calculation methods for final diagnosis.
Unless otherwise noted, all functions can be called from Gateway or client scope.
'''

import system
from ils.queue.commons import getQueueForDiagnosticApplication
from ils.queue.constants import QUEUE_INFO
from ils.common.util import escapeSqlQuotes

log = system.util.getLogger("com.ils.diagToolkit.common")

def setTextOfRecommendation(applicationName, familyName, finalDiagnosisName, textRecommendation, db):
    ''' Return the ProcessDiagram at the specified path '''
    log.infof("Setting the text of recommendation %s - %s - %s to %s", applicationName, familyName, finalDiagnosisName, textRecommendation)
    
    textRecommendation = escapeSqlQuotes(textRecommendation)
    applicationName = escapeSqlQuotes(applicationName)
    familyName = escapeSqlQuotes(familyName)
    finalDiagnosisName = escapeSqlQuotes(finalDiagnosisName)
    
    SQL = "UPDATE FD "\
        "SET FD.TextRecommendation = '%s' "\
        " FROM DtFinalDiagnosis FD, DtFamily F, DtApplication A "\
        " WHERE F.FamilyId = FD.FamilyId "\
        " and A.ApplicationId = F.ApplicationId "\
        " and A.ApplicationName = '%s' "\
        " and F.FamilyName = '%s'"\
        " and FD.FinalDiagnosisName = '%s' " % (textRecommendation, applicationName, familyName, finalDiagnosisName)
 
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, db)


def insertApplicationQueueMessage(applicationName, message, status=QUEUE_INFO, db=""):
    key = getQueueForDiagnosticApplication(applicationName, db)
    log.infof("Inserting <%s> into %s", message, key)
    from ils.queue.message import insert
    insert(key, status, message, db)


def resetManualMove(finalDiagnosisId, db):
    ''' Reset the Manual Move amount for the FD '''
    log.infof("Resetting the Manual Move amount for FD with id: %d", finalDiagnosisId)
    
    SQL = "Update DtFinalDiagnosis set ManualMove = 0.0 where FinalDiagnosisId = %s" % (str(finalDiagnosisId))
 
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL, db)
    

def getLabValueName(blockName, blockUUID, diagramUUID=""):
    '''
    It sounds easy but it takes a lot of work to get the name of the lab value tag for the SQC chart.
    We start with the SQC diagnosis, because that is the entry point for SQC plotting.  The we go 
    upstream to find a labdata entry block.  Then from that we need to extract the name of the tag
    bound to the value tag path property.  We do some work to strip things off to end up with the 
    lab data name.
    '''
    import system.ils.blt.diagram as diagram
    
    unitName=None
    labValueName=None
    
    log.infof("In %s.getLabValueName() - Getting Lab value name for block named: <%s> with UUID: <%s> on diagram with UUID: <%s>", __name__, blockName, blockUUID, diagramUUID)
   
    if diagramUUID == "":
        diagramDescriptor=diagram.getDiagramForBlock(blockUUID)
        if diagramDescriptor == None:
            log.tracef("   *** Unable to locate the diagram for block with UUID: %s", blockUUID)
            return unitName, labValueName
        
        diagramUUID=diagramDescriptor.getId()
    
    log.tracef("   ... fetching upstream block info for chart <%s> ...", str(diagramUUID))

    ''' Get all of the upstream blocks '''
    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
    blocks=diagram.listBlocksUpstreamOf(diagramUUID, blockName)
    log.tracef("Found blocks: %s", str(blocks))

    for block in blocks:
        if block.getClassName() == "com.ils.block.LabData":
            log.tracef("   ... found the LabData block...")
            blockId=block.getIdString()
            blockName=block.getName()
            
            ''' First get block properties '''
            valueTagPath=diagram.getPropertyBinding(diagramUUID, blockId, 'ValueTagPath')

            ''' Strip off the trailing /value  '''
            if valueTagPath.endswith("/value"):
                valueTagPath=valueTagPath[:len(valueTagPath) - 6]
            else:
                log.warn("Unexpected lab value tag path - expected path to end with /value")
            
            ''' Now strip off everything (provider and path from the left up to the last "/"  '''
            valueTagPath=valueTagPath[valueTagPath.find("]")+1:]
            unitName=valueTagPath[valueTagPath.find("/")+1:valueTagPath.rfind("/")]
            labValueName=valueTagPath[valueTagPath.rfind("/")+1:]
    
    log.tracef("   Found unit: <%s> - lab value: <%s>", unitName, labValueName)
    return unitName, labValueName