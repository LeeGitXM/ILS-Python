'''
Created on Sep 18, 2016

@author: Pete
'''

import system
log = system.util.getLogger("com.ils.diagToolkit.reset")

# Reset all of the applications for a unit - this is called for a grade change.  There is
# a less severe resetApplication in the setpointSpreadsheet module for resetting a diagram 
# after a download. 
# I'm not sure how generic this is, but it followed the pattern of RESET_FD-GDA.
def resetApplication(unit, database, tagProvider):
    import system.ils.blt.diagram as diagram
    log.info("com.ils.diagToolkit.reset.resetApplication: Resetting applications for unit: %s" % (unit)) 
    
    # Fetch all of the SQC Diagnosis for this Application
    SQL = "select SD.SQCDiagnosisId, SD.SQCDiagnosisName, F.FamilyId, SD.UUID, SD.DiagramUUID "\
        " from DtSQCDiagnosis SD, DtFamily F, DtApplication A, TkUnit U"\
        " where U.UnitId = A.UnitId "\
        " and A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = SD.FamilyId "\
        " and U.UnitName = '%s'" % (unit)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    log.trace("com.ils.diagToolkit.reset.resetApplication: Fetched %i SQC diagnosis" % (len(pds)))
    
    blocks=[]
    for record in pds:
        UUID = record['UUID']
        diagramUUID = record['DiagramUUID']
        sqcDiagnosisName = record['SQCDiagnosisName']
                   
        log.debug("com.ils.diagToolkit.reset.resetApplication: Resetting SQC diagnosis %s on diagram %s" % (sqcDiagnosisName, str(diagramUUID)))

        diagram.resetBlock(diagramUUID, sqcDiagnosisName)

        if diagramUUID != None and UUID != None:
            tBlocks=diagram.listBlocksGloballyDownstreamOf(diagramUUID, sqcDiagnosisName)
            for block in tBlocks:
                if block not in blocks:
                    blocks.append(block)
                    
    
    log.trace("com.ils.diagToolkit.reset.resetApplication: Resetting downstream (non-constant) final diagnosis ...")
    upstreamBlocks=[]
    for block in blocks:
        blockId=block.getIdString()
        blockName=block.getName()
        blockClass=block.getClassName()
        parentUUID=block.getAttributes().get("parent")  # The parent of a block is the diagram it is on

        if blockClass in ["xom.block.finaldiagnosis.FinalDiagnosis"]:
            log.info("com.ils.diagToolkit.reset.resetApplication: resetting a %s named: %s with id: %s on diagram: %s..." % (blockClass, blockName, blockId, parentUUID))
            system.ils.blt.diagram.resetBlock(parentUUID, blockName)
            
            # Collect all of the blocks upstream of this final diagnosis
            tBlocks = diagram.listBlocksGloballyUpstreamOf(parentUUID, blockName)
            for tBlock in tBlocks:
                if tBlock not in upstreamBlocks:
                    upstreamBlocks.append(tBlock)
                
    log.debug("com.ils.diagToolkit.reset.resetApplication:  %i blocks upstream of unit %s final diagnosis..." % (len(upstreamBlocks), unit))

