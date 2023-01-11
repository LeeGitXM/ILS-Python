'''
Created on Jul 13, 2022

@author: ils

This module provides an interface for all of the blt functions that can be called from Python.
Unless noted otherwise, all of these functions run from a client
'''

import system
from ils.config.common import getScope

import com.ils.blt.common.ApplicationRequestHandler as ApplicationRequestHandler

from ils.common.constants import GATEWAY, DESIGNER, CLIENT

from com.inductiveautomation.ignition.common.project.resource import ResourceType
from com.inductiveautomation.ignition.common.project.resource import ProjectResourceId

from ils.log import getLogger
log = getLogger(__name__)

MODULE_ID = "block"
TYPE_ID = "blt.diagram"
WATERMARK_TEXT = "Wait For New Data"

    
def sendSignal(diagramName):
    log.infof("In %s.sendSignal() with %s", __name__, diagramName)
    projectResourceId = getProjectResourceId(diagramName)

def clearWatermark(diagramName):
    log.tracef("In %s.clearWatermark() with %s", __name__, diagramName)
    projectResourceId = getProjectResourceId(diagramName)

    scope = getScope()
    if scope == GATEWAY:
        import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
        handler = ControllerRequestHandler.getInstance()
        handler.clearWatermark(projectResourceId)
    else:
        handler = ApplicationRequestHandler()
        handler.clearWatermark(projectResourceId)
    log.tracef("...waterMark has been cleared!")
    

def getExplanation(diagramName, blockName):
    '''
    TODO - I'd like to update this function in the gateway to take the blockName rather than the block UUID 
    to be consistent with all of the other functions. 7/15/2022
    '''
    projectResourceId = getProjectResourceId(diagramName)
    scope = getScope()
    log.infof("In %s.getExplanation() - Getting explanation for %s on %s", __name__, blockName, diagramName)
    if scope == GATEWAY:
        import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
        handler = ControllerRequestHandler.getInstance()
        explanation = handler.getExplanation(projectResourceId, blockName)
    else:
        handler = ApplicationRequestHandler()
        explanation = handler.getExplanation(projectResourceId, blockName)
    return explanation

def fetchSQCRootCause(diagramName, finalDiagnosisName):
    log.infof("In %s.fetchSQCRootCause(), looking for SQC blocks upstream of %s on %s...", __name__, finalDiagnosisName, diagramName)
    blocks = listBlocksGloballyUpstreamOf(diagramName, finalDiagnosisName)
    
    log.tracef("...found %d upstream blocks...", len(blocks))
    sqcRootCauses=[]
    for block in blocks:
        if block.getClassName() == "com.ils.block.SQC":
            blockName=block.getName()            
            blockAttributes = block.getAttributes()
            blockState = blockAttributes.get("State", None)

            log.tracef("Found: %s - %s", str(blockName), str(blockState))
            sqcRootCauses.append(block)

    return sqcRootCauses

def listBlocksGloballyUpstreamOf(diagramName, blockName):
    log.infof("In %s.listBlocksGloballyUpstreamOf() with %s on %s", __name__, blockName, diagramName)
    projectResourceId = getProjectResourceId(diagramName)
    scope = getScope()
    if scope == GATEWAY:
        import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
        handler = ControllerRequestHandler.getInstance()
        blocks=handler.listBlocksGloballyUpstreamOf(projectResourceId, blockName)
    else:
        handler = ApplicationRequestHandler()
        blocks=handler.listBlocksGloballyUpstreamOf(projectResourceId, blockName)
    log.tracef("...found %d blocks!", len(blocks))
    return blocks

def propagateBlockState(diagramName, blockName):
    log.infof("In %s.propagateBlockState() with %s", __name__, diagramName)
    projectResourceId = getProjectResourceId(diagramName)
    scope = getScope()
    if scope == GATEWAY:
        import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
        handler = ControllerRequestHandler.getInstance()
        handler.propagateBlockState(projectResourceId, blockName)
    else:
        handler = ApplicationRequestHandler()
        handler.propagateBlockState(projectResourceId, blockName)

def resetBlock(diagramName, blockName):
    log.infof("In %s.resetBlock() with %s on %s", __name__, blockName, diagramName)
    projectResourceId = getProjectResourceId(diagramName)
    
    scope = getScope()
    if scope == GATEWAY:
        import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
        handler = ControllerRequestHandler.getInstance()
        handler.resetBlock(projectResourceId, blockName)
    else:
        handler = ApplicationRequestHandler()
        handler.resetBlock(projectResourceId, blockName)
    log.tracef("...block has been reset!")
    
def setBlockState(diagramName, blockName, blockState):
    log.infof("In %s.setBlockState() with block: %s, diagram: %s, state: %s", __name__, blockName, diagramName, blockState)
    projectResourceId = getProjectResourceId(diagramName)
    scope = getScope()
    if scope == GATEWAY:
        import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
        handler = ControllerRequestHandler.getInstance()
        handler.setBlockState(projectResourceId, blockName, blockState)
    else:
        handler = ApplicationRequestHandler()
        handler.setBlockState(projectResourceId, blockName, blockState)

def setWatermark(diagramName):
    log.tracef("In %s.setWatermark() with %s", __name__, diagramName)
    projectResourceId = getProjectResourceId(diagramName)
    scope = getScope()
    if scope == GATEWAY:
        import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
        handler = ControllerRequestHandler.getInstance()
        handler.setWatermark(projectResourceId, WATERMARK_TEXT)
    else:    
        handler = ApplicationRequestHandler()
        handler.setWatermark(projectResourceId, WATERMARK_TEXT)
    log.tracef("...waterMark has been set!")

def getDiagramForBlock(blockId):
    log.tracef("In %s.getDiagramForBlock() with %s", __name__, blockId)
    projectResourceId = getProjectResourceId(diagramName)
    scope = getScope()
    if scope == GATEWAY:
        import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
        handler = ControllerRequestHandler.getInstance()
        handler.setWatermark(projectResourceId, WATERMARK_TEXT)
    else:    
        handler = ApplicationRequestHandler()
        handler.setWatermark(projectResourceId, WATERMARK_TEXT)
    log.tracef("...waterMark has been set!")
    
    
'''
Helper functions
'''

def getProjectResourceId(diagramName):
    log.tracef("In %s.getProjectResourceId() for %s...", __name__, diagramName)
    resourceType = ResourceType(MODULE_ID, TYPE_ID)
    projectName = system.util.getProjectName()
    projectResourceId = ProjectResourceId(projectName, resourceType, diagramName)
    return projectResourceId