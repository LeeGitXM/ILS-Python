'''
Created on Jan 7, 2017

@author: phass
'''

import system.ils.aed.model as model

# ModelControlInterface - an AED scripting interface

# Return the number of model execution cycles since 
# we started
def getExecutionStatus():
    statusDictionary = model.getExecutionStatus()
    print statusDictionary
    return statusDictionary

# Add a model to the set of existing models. The new model
# will execute. The dictionary is a nested set of definitions
# for the new model 
def addModel(key, modelDict):
    print "key: ", key
    print "dict: ", modelDict
    model.addModel(key,modelDict)

# Create a model header with a specified real-time timeout
# rate ~ msecs
def createModelList(rate, projectName):
    modelList = []
    
    from xom.emre.aed.engine.core.header import createHeader
    header = createHeader(rate, projectName)
    
    modelList.append(header)
    return modelList

# Delete the specified model from set of existing models. 
def deleteModel(key,modelId):
    model.deleteModel(key,modelId)
    
# Return a Python list of results. The first dictionary
# in the list contains contains the header sent with
# the original model set definition. The remainder of the 
# dictionaries contain results for individual models.
def getExecutionResults(key):
    resultList = model.getExecutionResults(key)
    return resultList

# Return the number of model execution cycles since 
# we started
def getExecutionCycles(key):
    count = model.getExecutionCycles(key)
    return count

# Return the number of model execution cycles since 
# we started
def getExecutionCycles2(key):
    count = model.getExecutionCycles2(key)
    return count

# Transmit the list from the previous method to the module.
# Presumably some model definitions will have been added 
# in the interim.
def sendModelList(key,models):
#    print "---------------------------------"
#    print "Key: ", key
#    print models
#    print "---------------------------------"
    model.defineModels(key,models)

# Activate the model set indicated by the specified key.
def startExecution(key):
    try:
        model.startModelExecution(key)
    except Exception, err:
        print "EREIAM JH - aed.engine.core.control:EXCEPTION: updateModel ("+str(err)+")"
        print "EREIAM JH - aed.engine.core.control:TRACE: ", traceback.format_exc()
# Deactivate the model set indicated by the specified key.
def stopExecution(key):
    print "Stopping ", key
    model.stopModelExecution(key)

# Update parameters for a running model. The dictionary 
# is a new, complete set of parameters. 
def updateModel(key,modelDict):
    import traceback

    try:
        model.updateModel(key,modelDict)
    except Exception, err:
        print "aed.engine.core.control:EXCEPTION: updateModel ("+str(err)+")"
        print "aed.engine.core.control:TRACE: ", traceback.format_exc()