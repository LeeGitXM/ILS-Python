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
    blocks={}
    diagramCounter = 0
    totalCntr = 0
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
                tBlocks=diagram.listBlocksInDiagram(descriptorId)
                
                cntr = 0
                for block in tBlocks:
                    blocks[block.getIdString()] = {"blockName": block.getName(), "parentUUID": descriptorId, "blockClass":stripClassPrefix(block.getClassName()) }
                    cntr = cntr + 1
                
                totalCntr = totalCntr + cntr
                log.tracef("   ...added %d blocks (total = %d)", cntr, totalCntr)

    log.infof("...there are %d (%d) unique blocks to consider on %d diagrams...", len(blocks), totalCntr, diagramCounter)
    
    '''  Remove latched blocks and blocks upstream of the latched blocks from our list of blocks. ''' 
    blocks = removeLatchedBlocks(blocks)
    log.infof("   ...there are %i blocks after removing latches and blocks upstream of them..." % (len(blocks)))
    
    '''  Remove constant finaldiagnosis and blocks upstream of them . ''' 
    blocks = removeConstantFinalDiagnosisAndUpstreamBlocks(blocks, database)
    log.infof("   ...there are %i blocks after removing constant FDs and blocks upstream of them..." % (len(blocks)))

    '''
    We now have a list of all blocks that should be reset
    '''
    log.infof("***********************************************")
    log.info("* Resetting observations and final diagnosis *")
    log.infof("***********************************************")
    
    for blockUUID in blocks.keys():
        block = blocks[blockUUID]
        blockName=block.get("blockName", "")
        blockClass=block.get("blockClass", "")
        parentUUID=block.get("parentUUID", "")  # The parent of a block is the diagram it is on
        log.tracef("    checking %s, a %s ", blockName, blockClass)
        
        if blockClass in OBSERVATION_BLOCK_LIST:
            log.infof("   ...resetting observation named %s, a %s...", blockName, blockClass)
            resetAndPropagate(blockName, blockUUID, parentUUID)
            
        elif blockClass in ['FinalDiagnosis']:
            log.infof("   ...resetting a %s named %s...", blockClass, blockName)
            resetAndPropagate(blockName, blockUUID, parentUUID)
    
    '''
    Take some special actions on special blocks.
    '''
    log.infof("****************************************************")
    log.info("* Touching TruthValuePulse blocks and inhibitors *")
    log.infof("****************************************************")
    for blockUUID in blocks.keys():
        block = blocks[blockUUID]
        blockName=block.get("blockName", "")
        blockClass=block.get("blockClass", "")
        parentUUID=block.get("parentUUID", "")  # The parent of a block is the diagram it is on
        
        log.trace("      looking at %s - %s" % (blockName, blockClass))

        if blockClass in ["TruthValuePulse"]:
            log.info("   ...resetting a %s named: %s on diagram: %s..." % (blockClass, blockName, parentUUID))
            system.ils.blt.diagram.sendSignal(parentUUID, blockName, "reset", "Grade Change")
        
        elif blockClass in ["Inhibitor"]:
            log.info("   ...resetting %s, a %s <%s>..." % (blockName, blockClass, parentUUID))
            system.ils.blt.diagram.sendSignal(parentUUID, blockName, "inhibit", "Grade Change")

    log.info("Done resetting applications for unit: %s!" % (unit)) 
    return

'''
Reset a block, set the block state and propagate it's state.
'''
def resetAndPropagate(blockName, blockUUID, parentUUID):
    
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
    
    upstreamUUIDs = []
    for blockUUID in blocks.keys():
        block = blocks[blockUUID]
        blockClass=block.get("blockClass", "")
        blockName=block.get("blockName", "")
        
        if blockClass in ["LogicLatch"]:
            latchCount = latchCount + 1
            del blocks[blockUUID]
            log.infof("      Found a latch named %s: %s...", blockName, str(block))
            parentUUID=block.get("parentUUID", "")
            upstreamBlocks=diagram.listBlocksGloballyUpstreamOf(parentUUID, blockName)
            log.tracef("      ...there are %d blocks upstream of it...", len(upstreamBlocks))
            for upstreamBlock in upstreamBlocks:
                if upstreamBlock.getIdString() not in upstreamUUIDs:
                    upstreamBlockName=upstreamBlock.getName()
                    log.tracef("          ...adding new block (%s) to the upstream list", str(upstreamBlockName))
                    upstreamUUIDs.append( upstreamBlock.getIdString() )
                
    '''
    At this point we have a dictionary of dictionaries of all blocks, where the key is the block UUID and
    we have a list of block UUIDs that are upstream of latches.  Remove the blocks that are upstream of latches from the big dictionary.
    '''
    blocks, cntr = removeBlocks(blocks, upstreamUUIDs)

    log.infof("...removed %d latches and %d blocks upstream of them.  Returning %d blocks!", latchCount, cntr, len(blocks))    
    return blocks

def removeConstantFinalDiagnosisAndUpstreamBlocks(blocks, database):
    '''
    We only want to reset FDs that are not a CONSTANT type of FD.  Constant FDs are typically plant status diagrams that update quickly in 
    real time and do not make recommendations.  By removing them from the list they won't get reset.
    '''
    log.infof("...removing constant Final Diagnosis and blocks upstream from them, starting with %d blocks...", len(blocks))
    constantFdCounter = 0
    upstreamUUIDs = []
    
    '''
    If I wanted to optimize performance I would make a single query of all constant FDs, put them in a list and use that list over and over.
    '''
    for blockUUID in blocks.keys():
        block = blocks[blockUUID]
        blockClass=block.get("blockClass", "")
        blockName=block.get("blockName", "")
        parentUUID=block.get("parentUUID", "")
        
        if blockClass =="FinalDiagnosis":
            SQL = "select constant from DtFinalDiagnosis where FinalDiagnosisUUID = '%s'" % (blockUUID)
            constant = system.db.runScalarQuery(SQL, database)

            if constant == 1:
                log.infof("   ... removing a constant Final Diagnosis: %s....", blockName)
                
                del blocks[blockUUID]
                constantFdCounter = constantFdCounter + 1
                
                log.trace("   ... collecting blocks upstream from it ...")
                upstreamBlocks=diagram.listBlocksGloballyUpstreamOf(parentUUID, blockName)
                log.tracef("      ...there are %d blocks upstream of it...", len(upstreamBlocks))
                for upstreamBlock in upstreamBlocks:
                    if upstreamBlock.getIdString() not in upstreamUUIDs:
                        upstreamBlockName=upstreamBlock.getName()
                        log.tracef("          ...adding new block (%s) to the upstream list", str(upstreamBlockName))
                        upstreamUUIDs.append( upstreamBlock.getIdString() )
    
    blocks, cntr = removeBlocks(blocks, upstreamUUIDs)

    log.infof("...removed %d constant FDs and %d blocks upstream of them.  Returning %d blocks!", constantFdCounter, cntr, len(blocks))    
    return blocks


def removeBlocks(blocks, upstreamUUIDs):
    '''
    At this point we have a dictionary of dictionaries of all blocks, where the key is the block UUID and
    we a list of block UUIDs.  Remove the blocks from the big list.
    '''
    log.tracef("   ...reconcile the lists.  There are %d blocks and %d blocks to remove...", len(blocks), len(upstreamUUIDs))
    cntr = 0
    for blockUUID in upstreamUUIDs:
        block =blocks.get(blockUUID, None)
        if block == None:
            log.tracef("   ...did not find %s in the master list of blocks", blockUUID)
        else:
            log.tracef("   ...removed %s -  %s from the master list of blocks", block.get("blockName", ""), blockUUID)
            del blocks[blockUUID]
            cntr = cntr + 1
    
    log.infof("...removed %d blocks, return list with %d blocks...", cntr, len(blocks))
    return blocks, cntr