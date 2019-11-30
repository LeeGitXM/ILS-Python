'''
  Copyright 2016. ILS Automation. All rights reserved.
  Gateway scope extension function that is called whenever a diagram is saved.
  We use this as an opportunity to synchronize our database perception of
  what exists in the diagnostic toolkit world.
'''
import system
import ils.diagToolkit.common as common
import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
import system.ils.blt.diagram as diagram
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit.diagSave")

controllerRequestHandler = ControllerRequestHandler.getInstance()
pythonHandler = diagram.getHandler()


def delete(diagramId):
    pass

def save(diagramId,aux):
    log.infof("In %s.save()", __name__)
    diagram = controllerRequestHandler.getDiagram(diagramId)
    if not(diagram == None):
        diagramName=diagram.getName()
        log.info("xom.extensions.diagSave: saving diagram "+diagramId+" is "+diagramName)
        database = controllerRequestHandler.getDatabaseForUUID(diagramId)
        # A database of NONE indicates that the diagram is disabled
        if not(database=="NONE"):   
            blocks = controllerRequestHandler.listBlocksInDiagram(diagramId)
            for block in blocks:
                className = common.stripClassPrefix(block.getClassName())
                if className() == "SQCDiagnosis":
                    blockId = block.getIdString()
                    blockName = block.getName()

                    log.info("  ...updating SQC Diagnosis named %s" % (blockName))
                    SQL = "update DtSQCDiagnosis set SQCDiagnosisUUID = '%s', DiagramUUID = '%s' where SQCDiagnosisName = '%s'" % (str(blockId), str(diagramId), blockName)
                    rows=system.db.runUpdateQuery(SQL, database)
                    if rows > 0:
                        log.trace("Updated block Id for SQC diagnosis named <%s> on <%s>" % (blockName, diagramName))
                    else:
                        familyName = pythonHandler.getFamily(diagramId).getName()
                        familyId = common.fetchFamilyId(familyName, database)
                        SQL = "insert into DtSQCDiagnosis (SQCDiagnosisName, Status, FamilyId, SQCDiagnosisUUID, DiagramUUID) "\
                            "values ('%s', 'New', %s, '%s', '%s')" % (blockName, str(familyId), str(blockId), str(diagramId) )
                        rows=system.db.runUpdateQuery(SQL, database)
                        if rows > 0:
                            print "...success"
                        else:
                            log.warn("Unable to update the id of SQC diagnosis named <%s> on diagram <%s>" % (blockName, diagramName))
              
                elif className == "FinalDiagnosis":
                    blockId = block.getIdString()
                    blockName = block.getName()
                    log.info("  ...updating Final Diagnosis named %s" % (blockName))
                    SQL = "update DtFinalDiagnosis set FinalDiagnosisUUID = '%s', DiagramUUID = '%s' where FinalDiagnosisName = '%s'" % (str(blockId), str(diagramId), blockName)
                    rows=system.db.runUpdateQuery(SQL, database)
                    if rows > 0:
                        log.trace("Updated block Id for final diagnosis named <%s> on <%s>" % (blockName, diagramName))
                    else:
                        log.warn("Unable to update the id of final diagnosis named <%s> on diagram <%s>" % (blockName, diagramName))


    else:
        log.warn("xom.extensions.diagSave: diagram "+diagramId+" NOT FOUND") 
    
#