'''
Created on Aug 6, 2015

@author: Pete
'''

# These lines are used to get information from the gateway about a diagram when all we know is the final 
# diagnosis.  This code needs to run from the client.
import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
handler = ControllerRequestHandler.getInstance()

# Return the name of the application tuat is the parent of this block
# This belongs in a more general environment
def getApplication(blockId):
    ans = None
    diagram = handler.getDiagramForBlock(blockId)
    if diagram != None:
        ans = handler.getApplicationName(diagram.getId())
    return ans
    
# This replaces em-get-target
# Search upstream for a SQC block. 
# Return the value on the target input.
def getUpstreamSQCTargetValue(finalDiagnosisId):
    status = "failure"
    value = -1
    diagram = handler.getDiagramForBlock(finalDiagnosisId)
    # Blocks SerializableBlockStateDescriptor
    blocks = handler.listBlocksUpstreamOf(diagram.getId(), finalDiagnosisId)
    for block in blocks:
        attributes = block.getAttributes()
        if attributes.get("class") == "com.ils.block.SQC":
            value = float(attributes.get("target","0.0"))
            status = "success"
            break
            
    return status, value