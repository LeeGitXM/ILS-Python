'''
Created on Sep 18, 2016

@author: Pete
'''

import system, string
import system.ils.blt.diagram as diagram
from ils.common.error import catchError

from ils.log import getLogger
log=getLogger(__name__)

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

        # Fetch all of the diagrams for the application
        try:
            descriptorList = diagram.listDescriptorsForApplication(applicationName) 
        except:
            errorText = catchError("%s.resetApplication for application %s" % (__name__, applicationName))
            log.error(errorText)
            descriptorList = []
        else:
            log.tracef("Found %d descriptors for application %s", len(descriptorList), applicationName)
            
        for descriptor in descriptorList:
            descriptorId=descriptor.getId()
            descriptorName=descriptor.getName()
            descriptorType=descriptor.getType()

            log.trace("Checking:  %s - %s - %s" % (str(descriptorId), descriptorName, descriptorType))
    
            if descriptorType in ["blt.diagram"]:
                # Fetch all of the blocks on the diagram
                try:
                    tBlocks=diagram.listBlocksInDiagram(descriptorId)
                except:
                    errorText = catchError("%s.resetApplication listing blocks in diagram %s" % (__name__, descriptorName))
                    log.error(errorText)
                    tBlocks=[]
                    
                for block in tBlocks:
                    if block not in blocks:
                        blocks.append(block)

    log.info("...there are %i unique blocks to consider..." % (len(blocks)))

    # We now have a list of all blocks, now look through the list for SQC Diagnosis and Trend Diagnosis blocks and 
    # collect the blocks downstream of them.
    log.info("...resetting SQC diagnosis and trend diagnosis blocks")
    downstreamBlocks=[]
    for block in blocks:
        blockName=block.getName()
        blockClass=stripPrefix(block.getClassName())
        blockUUID=block.getIdString()
        parentUUID=block.getAttributes().get("parent")  # The parent of a block is the diagram it is on
        log.trace("    Found a %s - %s " % (blockName, blockClass))
        
        if blockClass in ["SQCDiagnosis", "TrendDiagnosis"]:
            log.info("   ...resetting %s, a %s <%s>..." % (blockName, blockClass, parentUUID))

            resetAndPropagate(block)
            
            # Collect all of the blocks upstream of this final diagnosis
            log.trace("      ...collecting blocks downstream from it ...")
            try:
                tBlocks = diagram.listBlocksGloballyDownstreamOf(parentUUID, blockName)
            except:
                errorText = catchError("%s.resetApplication listing blocks downstream of %s" % (__name__, blockName))
                log.error(errorText)
                tBlocks = []
                
            for tBlock in tBlocks:
                if tBlock not in downstreamBlocks:
                    downstreamBlocks.append(tBlock)
                    
        elif blockClass in ["SQC"]:
            log.info("   ...resetting %s, a %s <%s>..." % (blockName, blockClass, parentUUID))
            resetAndPropagate(block)
        
        elif blockClass in ["Inhibitor"]:
            log.info("   ...resetting %s, a %s <%s>..." % (blockName, blockClass, parentUUID))
            system.ils.blt.diagram.sendSignal(parentUUID, blockName, "inhibit", "Grade Change")

    # Now reset Final diagnosis downstream from an SQC diagnosis or a trend diagnosis and collect all of the 
    # blocks upstream of them.
    log.info("...resetting non-constant final diagnosis that are downstream of SQC diagnosis blocks (there are %i downstream blocks)..." % (len(downstreamBlocks)))
    upstreamBlocks=[]
    for block in downstreamBlocks:
        blockClass=stripPrefix(block.getClassName())
        blockName=block.getName()
        
        if blockClass in ["FinalDiagnosis"]:
            blockUUID=block.getIdString()
            blockName=block.getName()
              
            # We only want to reset FDs that are not a CONSTANT type of FD.  Constant FDs are typically
            # plant status diagrams that update quickly in real time and do not make recommendations.
            # (I'm not sure how a constant FD would ever get in this list because we started from a SQC diagnosis.) 
            SQL = "Select constant from DtFinalDiagnosis where FinalDiagnosisUUID = '%s'" % (blockUUID)
            constant = system.db.runScalarQuery(SQL, database)

            if constant == 0:
                log.info("   ... resetting Final Diagnosis: %s with id: %s on diagram: %s..." % (blockName, blockUUID, parentUUID))
                
                parentUUID=block.getAttributes().get("parent")
                resetAndPropagate(block)
                
                # Collect all of the blocks upstream of this final diagnosis
                log.trace("   ... collecting blocks upstream from it ...")
                try:
                    tBlocks = diagram.listBlocksGloballyUpstreamOf(parentUUID, blockName)
                except:
                    errorText = catchError("%s.resetApplication listing blocks upstream of %s" % (__name__, blockName))
                    log.error(errorText)
                    tBlocks = []
                
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
    were required in the old platform due to some idiosyncrosy with GDA, since symbolic ai is fundamentally 
    different in how data propagates, we may not need to do the same thing when the grade changes!  We do know that we
    need to twiddle the truth pulse objects. 
    '''    
    
    log.info("...touching TruthValuePulse blocks...")
    for block in upstreamBlocks:
        blockClass=stripPrefix(block.getClassName())
        blockName=block.getName()
        
        log.trace("      looking at %s - %s" % (blockName, blockClass))

        if blockClass in ["TruthValuePulse"]:
            parentUUID=block.getAttributes().get("parent")

            log.info("   ...resetting a %s named: %s on diagram: %s..." % (blockClass, blockName, parentUUID))
            system.ils.blt.diagram.sendSignal(parentUUID, blockName, "reset", "Grade Change")

    return

'''
Reset a block, set the block state and propagate it's state.
'''
def resetAndPropagate(block):
    blockName=block.getName()
    blockUUID=block.getIdString()
    parentUUID=block.getAttributes().get("parent")
    
    try:
        system.ils.blt.diagram.resetBlock(parentUUID, blockName)
        system.ils.blt.diagram.setBlockState(parentUUID, blockName, "UNKNOWN")
        system.ils.blt.diagram.propagateBlockState(parentUUID, blockUUID)
    except:
        errorText = catchError("%s.resetAndPropagate() for block: %s" % (__name__, blockName))
        log.error(errorText)


'''
Remove latched blocks and blocks upstream of latched blocks from the list of blocks
'''
def removeLatchedBlocks(upstreamBlocks):
    log.info("   ...removing blocks upstream of latches...")
    blocksUpstreamOfLatches=[]
    for block in upstreamBlocks:
        blockClass=stripPrefix(block.getClassName())
        
        if blockClass in ["LogicLatch"]:
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

def stripPrefix(className):
    return className[className.rfind("."):]