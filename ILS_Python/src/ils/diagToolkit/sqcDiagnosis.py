'''
Created on June 16, 2015
'''

import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
import system.ils.blt.diagram as script

handler = ControllerRequestHandler.getInstance()

log = LogUtil.getLogger("com.ils.diagToolkit.recommendation")

# Return two lists:
# 1) the names of all of the input blocks in the diagram
# 2) the names of all the SQC diagnosis blocks in the diagram
# This mimics the functionality of the G2 procedure: em-get-input-blocks
def getInputBlocks(diagramPath):
    diagid = getDiagram(diagramPath).getSelf().toString()
    # blocks is a list of SerializableBlockStateDescriptor
    inputs = script.listDiagramBlocksOfClass(diagid,"com.ils.block.Input")
    observations = script.listDiagramBlocksOfClass(diagid,"xom.block.sqcdiagnosis.SQCDiagnosis")
    return inputs,observations 
    
# -------------------------- Helper methods ----------------------
# Return the ProcessDiagram at the specified path
def getDiagram(dpath):
    diagram = None
    # The descriptor paths are :-separated, the input uses /
    # the descriptor path starts with ":root:", 
    # the input starts with the application
    descriptors = script.getDiagramDescriptors()
    handler = script.getHandler()
    for desc in descriptors:
        path = desc.path[6:]
        path = path.replace(":","/")
        #print desc.id, path
        if dpath == path:
            diagram = handler.getDiagram(desc.id)
    return diagram
