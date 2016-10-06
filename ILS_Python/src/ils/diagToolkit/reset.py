'''
Created on Sep 18, 2016

@author: Pete
'''

import system
import system.ils.blt.diagram as diagram
log = system.util.getLogger("com.ils.diagToolkit.reset")

'''
Reset all of the applications for a unit - this is called for a grade change.  There is
a less severe resetApplication in the setpointSpreadsheet module for resetting a diagram 
after a download. 
I'm not sure how generic this is, but it followed the pattern of RESET_FD-GDA.
The idea here is to:
    Fetch all of the diagnostic applications for a unit
        Fetch all of the diagnostic diagrams for each application
            Fetch of of the blocks on each diagram
'''
def resetApplication(unit, database, tagProvider):
    log.info("Resetting applications for unit: %s" % (unit)) 

    # Fetch all of the diagnostic applications for a unit.
    SQL = "select A.ApplicationName "\
        " from DtApplication A, TkUnit U"\
        " where U.UnitId = A.UnitId "\
        " and U.UnitName = '%s'" % (unit)
    pds = system.db.runQuery(SQL, database)
    log.info("Fetched %i applications" % (len(pds)))
    
    descriptorList=[]
    blocks=[]
    for record in pds:
        applicationName = record['ApplicationName']
        log.info("Fetching descriptors for %s" % (applicationName))

        # Fetch all of the diagnostio diagrams for the application
        descriptorList = diagram.listDescriptorsForApplication(applicationName) 
        for descriptor in descriptorList:
            descriptorId=descriptor.getId()
            descriptorName=descriptor.getName()
            descriptorType=descriptor.getType()

            log.trace("Checking:  %s - %s - %s" % (str(descriptorId), descriptorName, descriptorType))
    
            if descriptorType in ["blt.diagram"]:
                # Fetch all of the blocks on the diagram
                tBlocks=diagram.listBlocksInDiagram(descriptorId)
                for block in tBlocks:
                    if block not in blocks:
                        blocks.append(block)

    log.info("...there are %i unique blocks to consider..." % (len(blocks)))

    # We now have a list of all blocks, now look through the list for SQC Diagnosis and Trend Diagnosis blocks and 
    # collect the blocks downstream of them.
    log.info("...resetting SQC diagnosis and trend diagnosis blocks")
    downstreamBlocks=[]
    for block in blocks:
        blockId=block.getIdString()
        blockName=block.getName()
        blockClass=block.getClassName()
        parentUUID=block.getAttributes().get("parent")  # The parent of a block is the diagram it is on
        log.trace("    Found a %s - %s " % (blockName, blockClass))
        
        if blockClass in ["xom.block.sqcdiagnosis.SQCDiagnosis", "xom.block.trenddiagnosis.TrendDiagnosis"]:
            log.info("   ...resetting %s, a %s <%s>..." % (blockName, blockClass, parentUUID))

            system.ils.blt.diagram.resetBlock(parentUUID, blockName)
            
            # Collect all of the blocks upstream of this final diagnosis
            log.trace("      ...collecting blocks downstream from it ...")
            tBlocks = diagram.listBlocksGloballyDownstreamOf(parentUUID, blockName)
            for tBlock in tBlocks:
                if tBlock not in downstreamBlocks:
                    downstreamBlocks.append(tBlock)
                    
        elif blockClass in ["com.ils.block.SQC"]:
            log.info("   ...resetting %s, a %s <%s>..." % (blockName, blockClass, parentUUID))
            system.ils.blt.diagram.resetBlock(parentUUID, blockName)
        
        elif blockClass in ["com.ils.block.Inhibitor"]:
            log.info("   ...resetting %s, a %s <%s>..." % (blockName, blockClass, parentUUID))
            system.ils.blt.diagram.sendSignal(parentUUID, blockName, "inhibit", "Grade Change")

    # Now reset Final diagnosis downstream from an SQC diagnosis or a trend diagnosis and collect all of the 
    # blocks upstream of them.
    log.info("...resetting non-constant final diagnosis that are downstream of SQC diagnosis blocks (there are %i downstream blocks)..." % (len(downstreamBlocks)))
    upstreamBlocks=[]
    for block in downstreamBlocks:
        blockClass=block.getClassName()
        blockName=block.getName()
        
        if blockClass in ["xom.block.finaldiagnosis.FinalDiagnosis"]:
            blockId=block.getIdString()
              
            # We only want to reset FDs that are not a CONSTANT type of FD.  Constant FDs are typically
            # plant status diagrams that update quickly in real time and do not make recommendations.
            # (I'm not sure how a constant FD would ever get in this list because we started from a SQC diagnosis.) 
            SQL = "Select constant from DtFinalDiagnosis where UUID = '%s'" % (blockId)
            constant = system.db.runScalarQuery(SQL, database)

            if constant == 0:
                log.info("   ... resetting Final Diagnosis: %s with id: %s on diagram: %s..." % (blockName, blockId, parentUUID))
                blockName=block.getName()
                parentUUID=block.getAttributes().get("parent")
                
                system.ils.blt.diagram.resetBlock(parentUUID, blockName)
                
                # Collect all of the blocks upstream of this final diagnosis
                log.trace("   ... collecting blocks upstream from it ...")
                tBlocks = diagram.listBlocksGloballyUpstreamOf(parentUUID, blockName)
                for tBlock in tBlocks:
                    if tBlock not in upstreamBlocks:
                        upstreamBlocks.append(tBlock)
            else:
                log.info("   ... skipping a constant final diagnosis: %s..." % (blockName))


    log.trace("...collected %i blocks upstream of unit %s final diagnosis..." % (len(upstreamBlocks), unit))

    # Remove latched blocks and blocks upstream of the latched blocks from our list of blocks. 
    log.info("There are %i upstream blocks..." % (len(upstreamBlocks)))
    upstreamBlocks = removeLatchedBlocks(upstreamBlocks)
    log.info("   ...there are %i upstream blocks after removing upstream blocks..." % (len(upstreamBlocks)))
    
    '''
    Now that we have the list of blocks upstream from all of the non-constant final diagnosis that are not upstream of a 
    latch block the million dollar question is what do we need to do to them.  The difficult thing is to sort out things that
    were required in the old platform due to some idiosyncrosy with GDA, since the diagnostic toolkit is fundamentally 
    different in how data propagates, we may not need to do the same thing when the grade changes!  We do know that we
    need to twiddle the truth pulse objects. 
    '''    
    
    log.info("...touching TruthValuePulse blocks...")
    for block in upstreamBlocks:
        blockClass=block.getClassName()
        blockName=block.getName()
        
        log.trace("      looking at %s - %s" % (blockName, blockClass))

        if blockClass in ["com.ils.block.TruthValuePulse"]:
            parentUUID=block.getAttributes().get("parent")

            log.info("   ...resetting a %s named: %s on diagram: %s..." % (blockClass, blockName, parentUUID))
            system.ils.blt.diagram.sendSignal(parentUUID, blockName, "reset", "Grade Change")
            
    return


'''
Remove latched blocks and blocks upstream of latched blocks from the list of blocks
'''
def removeLatchedBlocks(upstreamBlocks):
    log.info("   ...removing blocks upstream of latches...")
    blocksUpstreamOfLatches=[]
    for block in upstreamBlocks:
        blockClass=block.getClassName()
        
        if blockClass in ["com.ils.block.LogicLatch"]:
            blockName=block.getName()
            log.info("      Found a latch named %s..." % (blockName))
            parentUUID=block.getAttributes().get("parent")
            blocks=diagram.listBlocksGloballyUpstreamOf(parentUUID, blockName)
            log.info("      ...there are %i blocks upstream of it..." % (len(blocks)))
            for block in blocks:
                if block not in blocksUpstreamOfLatches:
                    log.trace("         Removing an upstream %s named %s" % (blockClass, blockName))
                    blocksUpstreamOfLatches.append(block)

    log.info("There are a total of %i blocks upstream of latches..." % (len(blocksUpstreamOfLatches)))

    # Remove the blocks upstream latches from the list of all upstream blocks
    for block in blocksUpstreamOfLatches:
        if block in upstreamBlocks:
            upstreamBlocks.remove(block)
    
    return upstreamBlocks