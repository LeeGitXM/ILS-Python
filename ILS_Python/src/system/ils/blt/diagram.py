'''
  Entries for the Block-language Toolkit

@author: chuckc
'''

def clearWatermark(diagId):
    '''Clear the watermark from the diagram'''
    
def getBlockState(diagramId, blockName):
    '''Get the internal state of a block'''

def getDiagramDescriptors(diagid):
    return []

def getDiagramForBlock(blockId):
    '''Get the diagram serializable block state descriptor'''
    
def getDiagramState(diagid):
    return "ACTIVE"
    
def getHandler():
    '''Return a python request handler'''

# I don't think this is correct...
def getPropertyValue(diagId, blockId, property):
    '''Get the diagram serializable block state descriptor'''
    
def getRequestHandler():
    '''Get the controller request handler'''
    
def getToolkitProperty(name):
    return name

def listBlocksUpstreamOf(diagId, blockName):
    '''Get a list of serializable block state descriptors of the upstream blocks'''

def listBlocksDownstreamOf(diagId, blockName):
    '''Get a list of serializable block state descriptors of the downstream blocks'''

def resetBlock(diagId, blockName):
    '''Reset the specified block'''
     
def resetDiagram(diagid):
    '''Reset the specified diagram'''

def sendSignal(diagId, blockName, signal, message):
    '''Send a signal to the named block on the specified diagram'''

def setBlockState(diagId, blockName, blockState):
    '''Set the internal state of a block, states are TRUE, FALSE, UNKNOWN, UNSET'''
    
def setDiagramState(diagId,state):
    '''Set the state of the specified diagram'''

def setState(diagId, blockName, state):
    '''Set the state of the named block on the specified diagram'''
    
def setWatermark(diagId, txt):
    '''Add a watermark with desired text to the diagram'''
    
