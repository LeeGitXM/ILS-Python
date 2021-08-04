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

controllerRequestHandler = ControllerRequestHandler.getInstance()
pythonHandler = diagram.getHandler()
DEBUG = True

def delete(diagramUUID):
    from ils.log.LogRecorder import LogRecorder
    log = LogRecorder(__name__ + ".delete")
    
    log.infof("Deleting diagram with UUID %s", __name__, diagramUUID)
    
    database = controllerRequestHandler.getDatabaseForUUID(diagramUUID)
    
    if (DEBUG): log.infof("...deleting Final Diagnosis on diagram %s...", diagramUUID)
    SQL = "delete from DtFinalDiagnosis where DiagramUUID = '%s' " % (str(diagramUUID))
    rows=system.db.runUpdateQuery(SQL, database)
    if (DEBUG): log.infof("   ...deleted %d rows!", rows)
    
    if (DEBUG): log.infof("...deleting SQC Diagnosis on diagram %s...", diagramUUID)
    SQL = "delete from DtSQCDiagnosis where DiagramUUID = '%s' " % (str(diagramUUID))
    rows=system.db.runUpdateQuery(SQL, database)
    if (DEBUG): log.infof("   ...deleted %d rows!", rows)
    
    if (DEBUG): log.infof("...leaving %s.delete()", __name__)
    

def getAux(uuid,aux,db):
    from ils.log.LogRecorder import LogRecorder
    log = LogRecorder(__name__ + ".getAux")
    log.infof("nothing to do")

# UUID is a string representation of the diagram's iD
def save(diagramUUID):
    from ils.log.LogRecorder import LogRecorder
    log = LogRecorder(__name__ + ".save")
    
    log.infof("Saving diagram with UUID %s", diagramUUID)
    diagram = controllerRequestHandler.getDiagram(diagramUUID)
    applicationName  = controllerRequestHandler.getApplicationName(diagramUUID)
    familyName = controllerRequestHandler.getFamilyName(diagramUUID)
    if (DEBUG): log.infof("  Application Name: %s", applicationName)
    if (DEBUG): log.infof("  Family Name: %s", familyName)
    
    if not(diagram == None):
        diagramName=diagram.getName()

        if (DEBUG): log.infof("...saving diagram  <%s> <%s>", diagramName, diagramUUID)
        database = controllerRequestHandler.getDatabaseForUUID(diagramUUID)
        
        # A database of NONE indicates that the diagram is disabled
        if not(database == "NONE"):   
            blocks = controllerRequestHandler.listBlocksInDiagram(diagramUUID)
            for block in blocks:
                className = common.stripClassPrefix(block.getClassName())
                
                if className == "SQCDiagnosis":
                    blockId = block.getIdString()
                    blockName = block.getName()

                    if (DEBUG): log.infof("  ...updating SQC Diagnosis named %s", blockName)
                    SQL = "update DtSQCDiagnosis set SQCDiagnosisUUID = '%s', DiagramUUID = '%s' where SQCDiagnosisName = '%s'" % (str(blockId), str(diagramUUID), blockName)
                    rows=system.db.runUpdateQuery(SQL, database)
                    if rows > 0:
                        if (DEBUG): log.infof("Updated block Id for SQC diagnosis named <%s> on <%s>", blockName, diagramName)
                    else:
                        familyName = pythonHandler.getFamily(diagramUUID).getName()
                        familyId = common.fetchFamilyId(familyName, database)
                        SQL = "insert into DtSQCDiagnosis (SQCDiagnosisName, Status, FamilyId, SQCDiagnosisUUID, DiagramUUID) "\
                            "values ('%s', 'New', %s, '%s', '%s')" % (blockName, str(familyId), str(blockId), str(diagramUUID) )
                        rows=system.db.runUpdateQuery(SQL, database)
                        if rows > 0:
                            if (DEBUG): log.infof("...success, a new SQC Diagnosis was inserted!")
                        else:
                            log.warnf("Unable to insert a new SQC diagnosis named <%s> on diagram <%s>", blockName, diagramName)
              
                elif className == "FinalDiagnosis":
                    print "Block: ", block
                    blockId = block.getIdString()
                    blockName = block.getName()
                    if (DEBUG): log.infof("  ...updating Final Diagnosis named %s", blockName)
                    SQL = "update DtFinalDiagnosis set FinalDiagnosisUUID = '%s', DiagramUUID = '%s' where FinalDiagnosisName = '%s'" % (str(blockId), str(diagramUUID), blockName)
                    rows=system.db.runUpdateQuery(SQL, database)
                    if rows > 0:
                        if (DEBUG): log.infof("Updated UUID and diagram UUID for final diagnosis named <%s> on <%s>", blockName, diagramName)
                    else:
                        if (DEBUG): log.infof("...unable to update an existing final diagnosis, inserting a new one...")
                        familyName = pythonHandler.getFamily(diagramUUID).getName()
                        if (DEBUG): log.infof("      Family Name: %s", familyName)
                        familyId = common.fetchFamilyId(familyName, database)
                        if familyId == None:
                            log.warnf("Unable to insert the Final Diagnosis because the family has not been defined in the database.")
                        else:
                            if (DEBUG): log.infof("      Family Id: %s", str(familyId))
                            SQL = "insert into DtFinalDiagnosis (FinalDiagnosisName, FamilyId, FinalDiagnosisPriority, Active,  FinalDiagnosisUUID, DiagramUUID, ShowExplanationWithRecommendation, PostTextRecommendation, "\
                                " refreshRate, TimeOfMostRecentRecommendationImplementation) "\
                                "values ('%s', %s, 0, 0, '%s', '%s', 0, 0, 0, '01/01/1900')" % (blockName, str(familyId), str(blockId), str(diagramUUID))
                            if (DEBUG): log.infof("    SQL: <%s>", SQL)
                            rows=system.db.runUpdateQuery(SQL, database)
                            if rows > 0:
                                if (DEBUG): log.infof("...success, a new Final diagnosis was inserted!")
                            else:
                                log.warnf("Unable to insert a new final diagnosis named <%s> on diagram <%s>", blockName, diagramName)

    else:
        log.warnf("Diagram not found for diagram UUID: <%s>!", str(diagramUUID) ) 
    
# Not used
def setAux(uuid,aux,db):
    from ils.log.LogRecorder import LogRecorder
    log = LogRecorder(__name__ + ".setAux")
    log.infof("nothing to do")