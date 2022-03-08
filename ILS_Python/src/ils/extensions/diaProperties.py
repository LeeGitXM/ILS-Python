'''
  Copyright 2016. ILS Automation. All rights reserved.
  Gateway scope extension function that is called whenever a diagram is saved.
  We use this as an opportunity to synchronize our database perception of
  what exists in the Symbolic AI world.
'''
import system
import ils.diagToolkit.common as common
import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
import com.ils.blt.gateway.engine.BlockExecutionController as BlockExecutionController
import system.ils.blt.diagram as diagram

from ils.log import getLogger
log =getLogger(__name__)

controllerRequestHandler = ControllerRequestHandler.getInstance()
blockExecutionController = BlockExecutionController.getInstance()
pythonHandler = diagram.getHandler()

def delete(diagramUUID):
    log.infof("Deleting diagram with UUID %s", __name__, diagramUUID)
    
    database = controllerRequestHandler.getDatabaseForUUID(diagramUUID)
    
    log.tracef("...deleting Final Diagnosis on diagram %s...", diagramUUID)
    SQL = "delete from DtFinalDiagnosis where DiagramUUID = '%s' " % (str(diagramUUID))
    rows=system.db.runUpdateQuery(SQL, database)
    log.tracef("   ...deleted %d rows!", rows)
    
    log.tracef("...deleting SQC Diagnosis on diagram %s...", diagramUUID)
    SQL = "delete from DtSQCDiagnosis where DiagramUUID = '%s' " % (str(diagramUUID))
    rows=system.db.runUpdateQuery(SQL, database)
    log.tracef("   ...deleted %d rows!", rows)
    
    log.tracef("...leaving %s.delete()", __name__)
    

def getAux(uuid,aux,db):
    log.tracef("In %s.getAux(), nothing to do", __name__)

# UUID is a string representation of the diagram's iD
def save(diagramUUID):
    from ils.diagToolkit.common import fetchFinalDiagnosisOnDiagram, fetchSqcDiagnosisOnDiagram
    log.infof("In %s.save() - Saving diagram with UUID %s", __name__, diagramUUID)
    
    ''' This returns the actual diagram, from it we can get the process blocks '''
    diagram = blockExecutionController.getDiagram(diagramUUID)
    log.tracef("Diagram: %s - %s", str(diagram), type(diagram).__name__)
    
    applicationName  = controllerRequestHandler.getApplicationName(diagramUUID)
    familyName = controllerRequestHandler.getFamilyName(diagramUUID)
    log.tracef("  Application Name: %s", applicationName)
    log.tracef("  Family Name: %s", familyName)
    
    if not(diagram == None):
        diagramName=diagram.getName()

        log.tracef("...saving diagram  <%s> <%s>", diagramName, diagramUUID)
        database = controllerRequestHandler.getDatabaseForUUID(diagramUUID)
        
        # A database of NONE indicates that the diagram is disabled
        if not(database == "NONE"):   
            blocks = diagram.getBlocks()

            existingFinalDiagnosisList = fetchFinalDiagnosisOnDiagram(diagramUUID, database)
            existingSqcDiagnosisList = fetchSqcDiagnosisOnDiagram(diagramUUID, database)
            
            for block in blocks:
                className = common.stripClassPrefix(block.getClassName())
                log.tracef("%s - %s - %s", className, str(block), type(block).__name__)
                
                if className == "SQCDiagnosis":
                    blockName = block.getName()
                    auxData = block.getAuxiliaryData()
                    
                    from ils.block.sqcdiagnosis import setAuxData as sqcDiagnosisSetAuxData
                    blockId = sqcDiagnosisSetAuxData(block, applicationName, familyName, diagramUUID, blockName, auxData, database)
                    if blockId in existingSqcDiagnosisList: existingSqcDiagnosisList.remove(blockId)
              
                elif className == "FinalDiagnosis":
                    blockName = block.getName()
                    auxData = block.getAuxiliaryData()
                    
                    from ils.block.finaldiagnosis import setAuxData as finalDiagnosisSetAuxData
                    blockId = finalDiagnosisSetAuxData(block, applicationName, familyName, diagramUUID, blockName, auxData, database)
                    if blockId in existingFinalDiagnosisList: existingFinalDiagnosisList.remove(blockId)
                    
            ''' 
            We are done saving every block on the diagram.  We started with a list of diagnosis thought to be on the diagram.  As we process blocks, they
            were removed from the lsist.  If there are any blocks in the list, then they were deleted in Designer and need to be deleted from the database.
            '''
            if len(existingSqcDiagnosisList) > 0:
                log.infof("There are SQC diagnosis to delete...")
                from ils.block.sqcdiagnosis import removeDeletedBlocksFromDatabase as sqcRemoveDeletedBlocksFromDatabase
                sqcRemoveDeletedBlocksFromDatabase(existingSqcDiagnosisList, database)
            
            if len(existingFinalDiagnosisList) > 0:
                log.infof("There are Final diagnosis to delete...")   
                from ils.block.finaldiagnosis import removeDeletedBlocksFromDatabase as finalDiagnosisRemoveDeletedBlocksFromDatabase
                finalDiagnosisRemoveDeletedBlocksFromDatabase(existingFinalDiagnosisList, database)
    else:
        log.warnf("Diagram not found for diagram UUID: <%s>!", str(diagramUUID) ) 
    
# Not used
def setAux(uuid,aux,db):
    log.infof("In %s.setAux() - nothing to do", __name__)