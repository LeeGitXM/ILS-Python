'''
  Entries for the Block-language Toolkit

@author: chuckc
'''

def clearWatermark(diagId):
    '''Clear the watermark from the diagram'''
    
def getBlockId(diagramId, blockName):
    '''Get the ID of a block'''

def getApplicationName(appId):
    '''Get the name of the application by its UUID'''

def getBlockState(diagramId, blockName):
    '''Get the internal state of a block'''

def getControllerState(appId):
    '''Get the current state of the controller'''

def getDatabaseForUUID(uuid):
    '''Get the database associated with a UUID'''

def getDatasourceNames():
    '''Get available database source names'''

def getDiagram(diagramIdid):
    '''Get the descriptor for the diagram that corresponds to the supplied Id'''

def getProductionDatabase():
    return "DATABASE"

def getIsolationDatabase(): 
    return "ISO_DATABASE"

def getProductionTagProvider(): 
    return "PROVIDER"

def getIsolationTagProvider():
    return "ISO_PROVIDER"

def getDiagramDescriptors(diagid):
    return []

def getDiagramForBlock(blockId):
    '''Get the diagram serializable block state descriptor'''
    
def getDiagramState(diagid):
    return "ACTIVE"

def getExplanation(diagid,blockId):
    return "because."

def getFamilyName(uuid):
    '''Get the family name that corresponds to the supplied Id'''

def getHandler():
    '''Return a python request handler'''

def getInternalState(diagid, blockId):
    ''' return the the internal state of a block '''

def getPropertyBinding(diagId, blockId, prop):
    '''Get the binding (tag path) of a specified block property'''
    
# I don't think this is correct...
def getPropertyValue(diagId, blockId, prop):
    '''Get the diagram serializable block state descriptor'''
    
def getRequestHandler():
    '''Get the controller request handler'''
    
def getTimeOfLastBlock(diagId, blockName):
    '''  get the time at which the block last changed its state '''

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
    
def listDescriptorsForApplication(appName):
    '''Return a list of descendants down to the level of a diagram ''' 

def listDiagramBlocksOfClass(diagramId,className):
    '''Return a list of serializable block state descriptors of blocks in this diagram that belong to the specified class''' 

def listBlocksInDiagram(diagramId):
    '''Return a list of serializable block state descriptors that reference blocks the specified diagram'''
  
def listSinksForSource(diagramId,blockId):
    '''Return a list of serializable block state descriptors corresponding to sinks associated with the specified source'''
    
def listSourcesForSink(diagramId,blockId):
    '''Return a list of serializable block state descriptors corresponding to source associated with the specified sink'''

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

def setApplicationState(appName, state):
    '''Change the state of every diagram in the named application to the specified state.'''
    
def setBlockProperty(diagId, blockName, propertyName, value):
    ''' Change the value of a block property in such a way that the block and UI are notified of the change.'''

def setBlockState(diagId, blockName, blockState):
    '''Set the internal state of a block, states are TRUE, FALSE, UNKNOWN, UNSET'''
    
def setDiagramState(diagId,state):
    '''Set the state of the specified diagram'''

def setState(diagId, blockName, state):
    '''Set the state of the named block on the specified diagram'''
    
def setTimeFactor(timeFactor):
    '''Set the time factor'''
    
def setToolkitProperty(propertyName, value):
    ''' Save a value into the HSQL database table associated with the toolkit. The table contains name-value pairs, so any name is allowable.'''
    
def setWatermark(diagId, txt):
    '''Add a watermark with desired text to the diagram'''
    
