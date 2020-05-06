'''
Created on Sep 18, 2016

@author: Pete
'''

import system, string
import system.ils.blt.diagram as diagram
from ils.common.error import catchError
from ils.diagToolkit.common import fetchFamilyNameForFinalDiagnosisId, stripClassPrefix
from ils.diagToolkit.constants import OBSERVATION_BLOCK_LIST
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
    '''
    Leave this in for backwards compatability - this is called by Vistalon.
    There is another resetApplication in setpointSpreadsheet.py which really does reset an application.
    This one resets all of the applications for a unit!
    '''
    log.info("Resetting applications for unit: %s" % (unit)) 
    resetUnit(unit, database, tagProvider)
    
    
def resetUnit(unit, database, tagProvider):
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
    diagramCounter = 0
    for record in pds:
        applicationName = record['ApplicationName']
        log.info("Fetching diagrams for application %s" % (applicationName))

        # Fetch all of the diagrams for the application
        try:
            descriptorList = diagram.listDescriptorsForApplication(applicationName) 
        except:
            errorText = catchError("%s.resetApplication for application %s" % (__name__, applicationName))
            log.error(errorText)
            descriptorList = []
        else:
            log.tracef("Found %d diagrams for application %s", len(descriptorList), applicationName)
            
        for descriptor in descriptorList:
            descriptorId=descriptor.getId()
            descriptorName=descriptor.getName()
            descriptorType=descriptor.getType()

            log.trace("Checking:  %s - %s - %s" % (str(descriptorId), descriptorName, descriptorType))
    
            if descriptorType in ["blt.diagram"]:
                diagramCounter = diagramCounter + 1
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

    log.infof("...there are %d unique blocks to consider on %d diagrams...", len(blocks), diagramCounter)
    
    '''  Remove latched blocks and blocks upstream of the latched blocks from our list of blocks. ''' 
    blocks = removeLatchedBlocks(blocks)
    log.infof("   ...there are %i blocks after removing latches and blocks upstream of them..." % (len(blocks)))
    
    '''  Remove constant finaldiagnosis and blocks upstream of them . ''' 
    blocks = removeConstantFinalDiagnosisAndUpstreamBlocks(blocks, database)
    log.infof("   ...there are %i blocks after removing constnat FDs and blocks upstream of them..." % (len(blocks)))

    '''
    We now have a list of all blocks that should be reset
    '''
    log.infof("***********************************************")
    log.info("* Resetting observations and final diagnosis *")
    log.infof("***********************************************")
    
    for block in blocks:
        blockName=block.getName()
        blockClass=stripClassPrefix(block.getClassName())
        parentUUID=block.getAttributes().get("parent")  # The parent of a block is the diagram it is on
        log.tracef("    checking %s, a %s ", blockName, blockClass)
        
        if blockClass in OBSERVATION_BLOCK_LIST:
            log.infof("   ...resetting observation named %s, a %s...", blockName, blockClass)
            resetAndPropagate(block)
            
        elif blockClass in ['FinalDiagnosis']:
            log.infof("   ...resetting a %s named %s...", blockClass, blockName)
            resetAndPropagate(block)
    
    '''
    Take some special actions on special blocks.
    '''
    log.infof("****************************************************")
    log.info("* Touching TruthValuePulse blocks and inhibitors *")
    log.infof("****************************************************")
    for block in blocks:
        blockClass=stripClassPrefix(block.getClassName())
        blockName=block.getName()
        
        log.trace("      looking at %s - %s" % (blockName, blockClass))

        if blockClass in ["TruthValuePulse"]:
            parentUUID=block.getAttributes().get("parent")
            log.info("   ...resetting a %s named: %s on diagram: %s..." % (blockClass, blockName, parentUUID))
            system.ils.blt.diagram.sendSignal(parentUUID, blockName, "reset", "Grade Change")
        
        elif blockClass in ["Inhibitor"]:
            parentUUID=block.getAttributes().get("parent")
            log.info("   ...resetting %s, a %s <%s>..." % (blockName, blockClass, parentUUID))
            system.ils.blt.diagram.sendSignal(parentUUID, blockName, "inhibit", "Grade Change")

    log.info("Done resetting applications for unit: %s!" % (unit)) 
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
def removeLatchedBlocks(blocks):
    log.info("   ...removing blocks upstream of latches...")
    latchCount = 0
    upstreamBlockCount = 0
    
    upstreamUUIDs = []
    for block in blocks:
        blockClass=stripClassPrefix(block.getClassName())
        
        if blockClass in ["LogicLatch"]:
            blockName=block.getName()
            latchCount = latchCount + 1
            log.infof("      Found a latch named %s: %s...", blockName, str(block))
            parentUUID=block.getAttributes().get("parent")
            upstreamBlocks=diagram.listBlocksGloballyUpstreamOf(parentUUID, blockName)
            log.info("      ...there are %i blocks upstream of it..." % (len(upstreamBlocks)))
            for upstreamBlock in upstreamBlocks:
                if upstreamBlock.getIdString() not in upstreamUUIDs:
                    upstreamBlockName=upstreamBlock.getName()
                    log.infof("          ...adding new block (%s) to the upstream list", str(upstreamBlockName))
                    upstreamUUIDs.append( upstreamBlock.getIdString() )
                
    for block in blocks:
        if block.getIdString() in upstreamUUIDs:
            blockClass=stripClassPrefix(block.getClassName())
            blockName=block.getName()
            upstreamBlockCount = upstreamBlockCount + 1
            log.trace("         Removing an upstream %s named %s" % (blockClass, blockName))
            blocks.remove(block)

    log.infof("...removed %d latches and %d blocks upstream of them!", latchCount, upstreamBlockCount)    
    return blocks

def removeConstantFinalDiagnosisAndUpstreamBlocks(blocks, database):
    '''
    We only want to reset FDs that are not a CONSTANT type of FD.  Constant FDs are typically plant status diagrams that update quickly in 
    real time and do not make recommendations.  By removing them from the list they won't get reset.
    '''
    log.infof("...removing constant Final Diagnosis and blocks upstream from them, starting with %d blocks...", len(blocks))
    constantFdCounter = 0
    upstreamBlockCounter = 0
    
    for block in blocks:
        blockClass=stripClassPrefix(block.getClassName())
        blockName=block.getName()
        
        if blockClass =="FinalDiagnosis":
            blockUUID=block.getIdString()
            blockName=block.getName()
         
            SQL = "Select constant from DtFinalDiagnosis where FinalDiagnosisUUID = '%s'" % (blockUUID)
            constant = system.db.runScalarQuery(SQL, database)

            if constant == 1:
                log.infof("   ... removing a constant Final Diagnosis: %s....", blockName)
                blocks.remove(block)
                constantFdCounter = constantFdCounter + 1
                
                parentUUID=block.getAttributes().get("parent")
                log.trace("   ... collecting blocks upstream from it ...")
                try:
                    tBlocks = diagram.listBlocksGloballyUpstreamOf(parentUUID, blockName)
                except:
                    errorText = catchError("%s.resetApplication listing blocks upstream of %s" % (__name__, blockName))
                    log.error(errorText)
                    tBlocks = []
                
                for tBlock in tBlocks:
                    if tBlock in blocks:
                        blocks.remove(tBlock)
                        upstreamBlockCounter = upstreamBlockCounter + 1

    log.infof("...removed %d constant FDs and %d blocks upstream of them...", constantFdCounter, upstreamBlockCounter)
    return blocks