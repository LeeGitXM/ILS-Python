'''
Created on Oct 8, 2014
These are the scripting functions provided
by the ILS SFC module, Gateway scope
@author: rforbes
'''

def cancelChart(chartId):
    pass

def getRunningCharts():
    pass

def getVariables():
    pass

def pauseChart(chartId):
    pass

def resumeChart(chartId):
    pass

def setVariable(chartId, stepId, variable, val):
    pass

def setVariables(chartId, stepId, variableMap):
    pass

def startChart(chartName, payload):
    pass

'''
I think these are in the wrong place
'''
def chartState(chartid):
    pass
def clear(datadict):
    pass
def debugChart(path,project,user, isIsolation):
    return -1
def postResponse(chartPath,stepName,text):
    pass
def requestCount(chartid,stepName):
    pass
def setTimeFactor(factor):
    pass
def start(datadict):
    pass
def stepCount(chartid,stepName):
    pass
def stepState(chartid,stepName):
    pass
def stop(datadict):
    pass