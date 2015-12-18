'''
  Entries for the Block-language Toolkit

@author: chuckc
'''
def getDiagramDescriptors(diagid):
    return []

def getDiagramState(diagid):
    return "ACTIVE"

def getHandler():
    '''Return a python request handler'''
    
def getToolkitProperty(name):
    return name
   
def resetDiagram(diagid):
    '''Reset the specified diagram'''
    
def setDiagramState(diagid,state):
    '''Set the state of the specified diagram'''
    
def getDiagramForBlock(blockId):
    '''Get the diagram serializable block state descriptor'''

def getBlockState(diagramId, blockName):
    '''Get the internal state of a block'''
    
# I don't think this is correct...
def getPropertyValue(diagramId, blockId, property):
    '''Get the diagram serializable block state descriptor'''

def listBlocksUpstreamOf(diagramId, sqcBlockName):
    '''Get a list of serializable block state descriptor all of the upstream blocks'''