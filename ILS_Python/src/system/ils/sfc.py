'''
Created on Nov 4, 2014

@author: rforbes
'''
def getResponse(id):
    pass

def setResponse(payload):
    pass

def getReviewData(chartScope, stepScope, configJson, addAdvice):
    pass

def getReviewFlows(chartScope, stepScope, configJson, addAdvice):
    pass

def getReviewFlowsConfig():
    pass

def getReviewDataConfig():
    pass

def activateStep(className, chartProperties, stepProperties):
    pass

def s88DataExists(chartProperties, stepProperties, ckey, location):
    pass

#TODO: delete this
def s88GetScope(chartProperties, stepProperties, location):
    pass

#TODO: delete this
def s88ScopeChanged(chartProperties, stepProperties):
    pass

def getDatabaseName(isolationMode):
    pass

def getProviderName(isolationMode):
    pass

def getIsolationMode(chartScope):
    pass

def getTimeFactor(isolationMode):
    pass

def getPVMonitorConfig(json):
    pass

def getWriteOutputConfig(json):
    pass

def getMonitorDownloadsConfig(json):
    pass

def getManualDataEntryConfig(json):
    pass

def dropboxPut():
    pass

def dropboxGet():
    pass

def getRecipeDataTagPath(chartScope, stepScope, scopeId):
    pass

def parseValue(str):
    pass

# Methods for unit tests
def initializeTests(reportFile):
    '''clear out any old tests and establish the report file for the new tests'''
    
def startTest(chartPath):
    '''start a test chart'''
    
def assertEqual(chart, step, expected, actual):
    '''Assert that the actual object should equal the expected object. If this is
    not true the test fails immediately.'''

def assertTrue(chart, step, flag, msg): 
    '''Assert that the flag is true. Typically the call to this will pass an expression
    that will be evaluated, e.g. assertTrue(chart, step, 3 < 6, 'should be less'). If this is
    not true the test fails immediately.'''

def failTest(chart):
    '''Fail the test. Typically called when the chart comes to an unhappy ending, e.g. in the
    OnAbort action method of an SFC or in an exception handler.'''
    
def passTest(chart):
    '''Pass the test. Typically called when the chart comes to a happy ending, e.g. in the
    OnStop action method of an SFC.'''

def reportTests():
    '''Print out a report on the current batch of tests, including those in progress. Calling
    this is not necessary, as the report will be automatically produced when the last test is
    complete, however if there is some question about what has finished and what has not it
    can be useful to print the interim report.'''

def setPauseRequested(runId):
    '''indicate ILS code has initiated a pause'''

def setCancelRequested(runId):
    '''indicate ILS code has initiated a cancel'''
    
def getPauseRequested(runId):
    '''check if ILS code has initiated a pause'''
    
def getCancelRequested(runId):
    '''check if ILS code has initiated a cancel'''

def stepState(chartId,name):
    '''return the current state of a chart'''
    
def watchChart(chartId,name):
    '''chart state event handler'''

# new session stuff:
def addClient(client):
    pass

def removeClient(clientId):
    pass

def addSessionListener(sessionId, clientId):
    pass

def removeSessionListener(sessionId, clientId):
    pass

def addSession(session):
    pass

def updateSession(session):
    pass

def getSession(sessionId):
    pass

def removeSession(sessionId):
    pass
    
def getSessionData():
    pass
    
