'''
Created on Nov 4, 2014

@author: rforbes
'''

def activateStep(className, chartProperties, stepProperties):
    pass
def addRequestId((windowId, stepId)):
    pass
def chartState(chartId):
    return "running"
def clearRequestResponseMaps():
    pass
def clearStepMonitor():
    pass
def debugChart(path, project, user, isolation):
    pass
def dropboxGet():
    pass
def dropboxPut():
    pass
def getResponse(id):
    pass
def getReviewData(chartScope, stepScope, configJson, addAdvice):
    pass

def getReviewFlows(chartScope, stepScope, configJson, addAdvice):
    pass

def getReviewFlowsConfig():
    pass

def getReviewDataConfig():
    pass


def s88DataExists(chartProperties, stepProperties, ckey, location):
    pass

# TODO: delete this
def s88GetScope(chartProperties, stepProperties, location):
    pass

# TODO: delete this
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

def getConfirmControllersConfig(json):
    pass

def getMonitorDownloadsConfig(json):
    pass

def getManualDataEntryConfig(json):
    pass



def getRecipeDataTagPath(chartScope, stepScope, scopeId):
    pass

def parseValue(str):
    pass

# Methods for unit tests
def initializeTests(reportFile):
    '''clear out any old tests and establish the report file for the new tests'''
def setResponse(payload):
    pass 
def startStepMonitor():
    pass
def stopStepMonitor():
    pass  
def startTest(chartPath):
    '''start a test'''
    
def assertEqual(chartScope, expected, actual):
    '''Assert that the actual object should equal the expected object. If this is
    not true the test fails immediately.'''

def assertTrue(chartScope, flag, msg): 
    '''Assert that the flag is true. Typically the call to this will pass an expression
    that will be evaluated, e.g. assertTrue(chart, step, 3 < 6, 'should be less'). If this is
    not true the test fails immediately.'''

def failTest(chartScope, message):
    '''Fail the test. Typically called when the chart comes to an unhappy ending, e.g. in the
    OnAbort action method of an SFC or in an exception handler.'''

def failTestChart(topChartPath, message):
    '''Like failTest(), but takes the path of the top-level SFC chart'''
    
def passTest(chartScope):
    '''Pass the test. Typically called when the chart comes to a happy ending, e.g. in the
    OnStop action method of an SFC.'''

def timeoutRunningTests():
    '''fail any tests still running with a timeout error'''

def testsAreRunning():
    '''return if any tests are still running'''
        
def reportTests():
    '''Print out a report on the current batch of tests, including those in progress. Calling
    this is not necessary, as the report will be automatically produced when the last test is
    complete, however if there is some question about what has finished and what has not it
    can be useful to print the interim report.'''

def getMatchingCharts(regex):
    '''Get the chart paths that match the regex'''
    
def watchChart(chartId, name):
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

def addSession(session, clientId):
    pass

def updateSession(session):
    pass

def getSession(sessionId):
    pass

def removeSession(sessionId):
    pass
    

