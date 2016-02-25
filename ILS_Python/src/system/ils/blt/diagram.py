'''
  Entries for the Block-language Toolkit

@author: chuckc
'''

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
def getPropertyValue(diagramId, blockId, property):
    '''Get the diagram serializable block state descriptor'''
    
def getRequestHandler():
    '''Get the controller request handler'''
    
def getToolkitProperty(name):
    return name

def listBlocksUpstreamOf(diagramId, sqcBlockName):
    '''Get a list of serializable block state descriptor all of the upstream blocks'''

def resetBlock(diagId, blockName):
    '''Reset the specified block'''
     
def resetDiagram(diagid):
    '''Reset the specified diagram'''

def sendSignal(diagramUUID, blockName, signal, message):
    '''Send a signal to the named block on the specified diagram'''
    
def setDiagramState(diagid,state):
    '''Set the state of the specified diagram'''

def setState(diagId, blockName, state):
    '''Set the state of the named block on the specified diagram'''
