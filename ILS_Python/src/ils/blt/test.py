'''
Created on Mar 11, 2023

@author: ils

This module implements the message handler used to test the blt gateway interface.
There is a vision window that dispatches messages to the gateway message handler named 
bltApiTester which calls this function.

The reason for this is to provide a way to test the blt functions in gateway scope, which is where
they run for the managing problems.  

Monitor the wrapper log or the diagram itself, depending on the function.
'''

from ils.log import getLogger
log = getLogger(__name__)

def messageHandler(payload):
    log.infof("In %s.messageHandler() with ", __name__, str(payload))
    test = payload.get("test", None)
    
    if test == "clearWatermark":
        diagramName = payload.get("diagramName", None)
        from ils.blt.api import clearWatermark
        clearWatermark(diagramName)
        
    elif test == "getExplanation":
            diagramName = payload.get("diagramName", None)
            blockName = payload.get("blockName", None)
            from ils.blt.api import getExplanation
            explanation = getExplanation(diagramName, blockName)
            log.infof("The explanation is: %s", explanation)
            
    elif test == "listBlocksUpstreamOf":
        diagramName = payload.get("diagramName", None)
        blockName = payload.get("blockName", None)
        from ils.blt.api import listBlocksGloballyUpstreamOf
        upstreamBlocks = listBlocksGloballyUpstreamOf(diagramName, blockName)
        log.infof("The upstream blocks are: %s", str(upstreamBlocks))
        print "Upstream blocks: "
        for block in upstreamBlocks:
            parentDiagramName = ""
            print "Block: ", block
            print "Block name: ", block.getName()
            print "Block class: ", block.getClassName()
            blockAttributes = block.getAttributes()
            print "Attributes: ", blockAttributes
            print "Properties: ", block.getProperties()
            
            parentDiagramName = blockAttributes.get("parent", None)
            print "Parent Diagram Name: %s" % (parentDiagramName)
            
            project = blockAttributes.get('project', None)
            print "Project: %s" % (project)
            
            print "-------"
        
    elif test == "propagateBlockState":
        diagramName = payload.get("diagramName", None)
        blockName = payload.get("blockName", None)
        from ils.blt.api import propagateBlockState
        propagateBlockState(diagramName, blockName)
    
    elif test == "resetBlock":
        diagramName = payload.get("diagramName", None)
        blockName = payload.get("blockName", None)
        from ils.blt.api import resetBlock
        resetBlock(diagramName, blockName)
    
    elif test == "setBlockState":
        diagramName = payload.get("diagramName", None)
        blockName = payload.get("blockName", None)
        blockState = payload.get("blockState", None)
        from ils.blt.api import setBlockState
        setBlockState(diagramName, blockName, blockState)
        
    elif test == "getBlockState":
        diagramName = payload.get("diagramName", None)
        blockName = payload.get("blockName", None)
        from ils.blt.api import getBlockState
        blockState = getBlockState(diagramName, blockName)
        log.infof("The state of %s on %s is %s", blockName, diagramName, blockState)
    
    elif test == "setWatermark":
        diagramName = payload.get("diagramName", None)
        from ils.blt.api import setWatermark
        setWatermark(diagramName)
    
    else:
        log.errorf("Unexpected test: %s", test)
