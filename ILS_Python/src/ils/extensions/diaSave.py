'''
  Copyright 2016. ILS Automation. All rights reserved.
  Gateway scope extension function that is called whenever a diagram is saved.
  We use this as an opportunity to synchronize our database perception of
  what exists in the Symbolic AI world.
'''
import system
import ils.diagToolkit.common as common
import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
import system.ils.blt.diagram as diagram

log = system.util.getLogger("com.ils.diagToolkit.extensions")
controllerRequestHandler = ControllerRequestHandler.getInstance()
pythonHandler = diagram.getHandler()

def delete(diagramUUID):
    log.tracef("In %s.delete()", __name__)
    

def save(diagramUUID, aux):
    log.tracef("In %s.save()", __name__)
    diagram = controllerRequestHandler.getDiagram(diagramUUID)
    if not(diagram == None):
        diagramName=diagram.getName()
        log.tracef("...saving diagram  <%s> <%s>", diagramName, diagramUUID)
        database = controllerRequestHandler.getDatabaseForUUID(diagramUUID)
        
        # A database of NONE indicates that the diagram is disabled
        if not(database == "NONE"):   
            blocks = controllerRequestHandler.listBlocksInDiagram(diagramUUID)
            for block in blocks:
                className = common.stripClassPrefix(block.getClassName())
                if className == "SQCDiagnosis":
                    blockId = block.getIdString()
                    blockName = block.getName()

                    log.info("  ...updating SQC Diagnosis named %s" % (blockName))
                    SQL = "update DtSQCDiagnosis set SQCDiagnosisUUID = '%s', DiagramUUID = '%s' where SQCDiagnosisName = '%s'" % (str(blockId), str(diagramUUID), blockName)
                    rows=system.db.runUpdateQuery(SQL, database)
                    if rows > 0:
                        log.tracef("Updated block Id for SQC diagnosis named <%s> on <%s>", blockName, diagramName)
                    else:
                        familyName = pythonHandler.getFamily(diagramUUID).getName()
                        familyId = common.fetchFamilyId(familyName, database)
                        SQL = "insert into DtSQCDiagnosis (SQCDiagnosisName, Status, FamilyId, SQCDiagnosisUUID, DiagramUUID) "\
                            "values ('%s', 'New', %s, '%s', '%s')" % (blockName, str(familyId), str(blockId), str(diagramUUID) )
                        rows=system.db.runUpdateQuery(SQL, database)
                        if rows > 0:
                            log.tracef("...success, a new SQC Diagnosis was inserted!")
                        else:
                            log.warnf("Unable to insert a new SQC diagnosis named <%s> on diagram <%s>", blockName, diagramName)
              
                elif className == "FinalDiagnosis":
                    blockId = block.getIdString()
                    blockName = block.getName()
                    log.tracef("  ...updating Final Diagnosis named %s", blockName)
                    SQL = "update DtFinalDiagnosis set FinalDiagnosisUUID = '%s', DiagramUUID = '%s' where FinalDiagnosisName = '%s'" % (str(blockId), str(diagramUUID), blockName)
                    rows=system.db.runUpdateQuery(SQL, database)
                    if rows > 0:
                        log.tracef("Updated UUID and diagram UUID for final diagnosis named <%s> on <%s>", blockName, diagramName)
                    else:
                        log.tracef("...unable to update an existing final diagnosis, inserting a new one...")
                        familyName = pythonHandler.getFamily(diagramUUID).getName()
                        log.tracef("      Family Name: %s", familyName)
                        familyId = common.fetchFamilyId(familyName, database)
                        if familyId == None:
                            log.warnf("Unable to insert the Final Diagnosis because the family has not been defined in the database.")
                        else:
                            log.tracef("      Family Id: %s", str(familyId))
                            SQL = "insert into DtFinalDiagnosis (FinalDiagnosisName, FamilyId, FinalDiagnosisPriority, Active,  FinalDiagnosisUUID, DiagramUUID, ShowExplanationWithRecommendation, PostTextRecommendation, "\
                                " refreshRate, TimeOfMostRecentRecommendationImplementation) "\
                                "values ('%s', %s, 0, 0, '%s', '%s', 0, 0, 0, '01/01/1900')" % (blockName, str(familyId), str(blockId), str(diagramUUID))
                            log.tracef("    SQL: <%s>", SQL)
                            rows=system.db.runUpdateQuery(SQL, database)
                            if rows > 0:
                                log.tracef("...success, a new Final diagnosis was inserted!")
                            else:
                                log.warnf("Unable to insert a new final diagnosis named <%s> on diagram <%s>", blockName, diagramName)

    else:
        log.warnf("Diagram not found for diagram UUID: <%s>!", str(diagramUUID) ) 
    