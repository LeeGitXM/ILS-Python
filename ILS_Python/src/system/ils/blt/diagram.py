'''
  Entries for the Block-language Toolkit

@author: chuckc
'''

def clearWatermark(diagId):
    '''Clear the watermark from the diagram'''
    
def getBlockId(diagramId, blockName):
    '''Get the ID of a block'''

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
def getPropertyValue(diagId, blockId, prop):
    '''Get the diagram serializable block state descriptor'''
    
def getRequestHandler():
    '''Get the controller request handler'''
    
def getToolkitProperty(name):
    return name

def listBlocksConnectedAtPort(diagId, blockId,port):
    '''Return a list of serializable block state descriptors connected to the named port'''
    
def listBlocksUpstreamOf(diagId, blockName):
    '''Return a list of serializable block state descriptors of the upstream blocks'''

def listBlocksDownstreamOf(diagId, blockName):
    '''Return a list of serializable block state descriptors of the downstream blocks'''

def listBlocksForTag(tagpath):
    '''Return a list of serializable block state descriptors that reference the specified tag'''

def listBlocksGloballyDownstreamOf(diagramId,blockName):
    '''Return a list of serializable block state descriptors of blocks downstream on this and connected diagrams'''  

def listBlocksGloballyUpstreamOf(diagramId,blockName):
    '''Return a list of serializable block state descriptors of blocks upstream on this and connected diagrams'''  
    
def listDiagramBlocksOfClass(diagramId,className):
     '''Return a list of serializable block state descriptors of blocks in this diagram that belong to the specified class''' 
    
def listBlocksInDiagram(diagramId):
    '''Return a list of serializable block state descriptors that reference blocks the specified diagram'''
  
def listSinksForSource(diagramId,blockName):
    '''Return a list of serializable block state descriptors corresponding to sinks associated with the named source'''
    
def listSourcesForSink(diagramId,blockName):
    '''Return a list of serializable block state descriptors corresponding to source associated with the named sink'''

def pathForBlock(diagid,bname):
     '''Return a nav-tree path for the named block '''
     
def propagateBlockState(diagId,blockId):
    '''Tell the block to propagate its latest values '''
     
def resetBlock(diagId, blockName):
    '''Reset the specified block'''

def restartBlock(diagId, blockName):
    '''Reset the specified block'''
       
def resetDiagram(diagid):
    '''Reset the specified diagram'''

def sendLocalSignal(diagid,command,message,arg):
    '''Send a signal to the named block on the specified diagram'''
    
def sendSignal(diagId, blockName, signal, message):
    '''Send a signal to the named block on the specified diagram'''

def sendTimestampedSignal(diagid,command,message,arg,ts):
    '''Send a signal to the named block on the specified diagram'''

def setBlockState(diagId, blockName, blockState):
    '''Set the internal state of a block, states are TRUE, FALSE, UNKNOWN, UNSET'''
    
def setDiagramState(diagId,state):
    '''Set the state of the specified diagram'''

def setState(diagId, blockName, state):
    '''Set the state of the named block on the specified diagram'''
    
def setWatermark(diagId, txt):
    '''Add a watermark with desired text to the diagram'''
    
