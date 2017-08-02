'''
Created on Nov 3, 2014

@author: rforbes
'''
import system, string

''' 
We need to get the queue name out of the unit procedure and use that as the default message queue, but
unlike in the old system, where we ran a unit procedure, here we are running a chart, and the chart had
better have a unit procedure on the top chart.  However all this method has is a chart path, it has no
way of knowing about the unit procedure block.  So when the unit procedure block runs we will update the 
record in the SfcControlParameter table. 
'''
def startChart(chartPath, controlPanelName, project, originator, isolationMode):
    from ils.sfc.common.constants import ISOLATION_MODE, CONTROL_PANEL_ID, CONTROL_PANEL_NAME, PROJECT, ORIGINATOR, MESSAGE_QUEUE
    from system.ils.sfc.common.Constants import DEFAULT_MESSAGE_QUEUE
    from ils.common.config import getDatabaseClient
    
    controlPanelId = system.db.runScalarQuery("select controlPanelId from SfcControlPanel where controlPanelName = '%s'" % (controlPanelName))
    print "Found id %s for control panel %s" % (str(controlPanelId), controlPanelName)
    
    initialChartParams = dict()
    initialChartParams[PROJECT] = project
    initialChartParams[ISOLATION_MODE] = isolationMode
    initialChartParams[CONTROL_PANEL_NAME] = controlPanelName
    initialChartParams[CONTROL_PANEL_ID] = controlPanelId
    initialChartParams[ORIGINATOR] = originator
    initialChartParams[MESSAGE_QUEUE] = DEFAULT_MESSAGE_QUEUE
    runId = system.sfc.startChart(chartPath, initialChartParams)
    if isolationMode:
        isolationFlag = 1
    else:
        isolationFlag = 0
    
    db = getDatabaseClient()
    updateSql = "Update SfcControlPanel set chartRunId = '%s', originator = '%s', project = '%s', isolationMode = %d where controlPanelId = %s" % (runId, originator, project, isolationFlag, str(controlPanelId))
    system.db.runUpdateQuery(updateSql, database=db)
    return runId

def readFile(filepath):
    '''
    Read the contents of a file into a string
    '''
    import StringIO
    out = StringIO.StringIO()
    fp = open(filepath, 'r')
    line = "dummy"
    while line != "":
        line = fp.readline()
        out.write(line)
    fp.close()
    result = out.getvalue()
    out.close()
    return result   

def boolToBit(bool):
    if bool:
        return 1
    else:
        return 0

def substituteHistoryProvider(chartProperties, tagPath):
    from ils.sfc.gateway.api import getHistoryProviderName
    '''alter the given tag path to reflect the isolation mode provider setting'''

    # Get the history tag provider 
    historyProvider=getHistoryProviderName(chartProperties)
    
    rbIndex = tagPath.find(']')
    if rbIndex >= 0:
        return '[' + historyProvider + ']' + tagPath[rbIndex+1:len(tagPath)]
    else:
        return '[' + historyProvider + ']' + tagPath

def substituteProvider(chartProperties, tagPath):
    from ils.sfc.gateway.api import getProviderName
    '''alter the given tag path to reflect the isolation mode provider setting'''
    if tagPath.startswith('[Client]') or tagPath.startswith('[System]'):
        return tagPath
    else:
        provider = getProviderName(chartProperties)
        rbIndex = tagPath.find(']')
        if rbIndex >= 0:
            return '[' + provider + ']' + tagPath[rbIndex+1:len(tagPath)]
        else:
            return '[' + provider + ']' + tagPath
    

def isEmpty(str):
    return str == None or str.strip() == ""

def callMethod(methodPath, stringLiteral=""):
    '''given a fully qualified package.method name, call the method and return the result'''
    lastDotIndex = methodPath.rfind(".")
    packageName = methodPath[0:lastDotIndex]
    globalDict = dict()
    localDict = dict()
    exec("import " + packageName + "\nresult = " + methodPath + "(" + stringLiteral + ")\n", globalDict, localDict)
    result = localDict['result']
    return result

def callMethodWithParams(methodPath, keys, values):
    '''given a fully qualified package.method name, call the method and return the result'''
    lastDotIndex = methodPath.rfind(".")
    packageName = methodPath[0:lastDotIndex]
    paramCount = 0
    paramLiterals = ""
    globalDict = dict()
    for i in range(len(keys)):
        key = keys[i]
        value = values[i]
        globalDict[key] = value
        if paramCount > 0:
            paramLiterals = paramLiterals + ", " 
        paramLiterals = paramLiterals + key
        paramCount = paramCount + 1
    localDict = dict()
    execString = "import " + packageName + "\nresult = " + methodPath + "(" + paramLiterals + ")\n"
    exec(execString, globalDict, localDict)
    result = localDict['result']
    return result

def getHoursMinutesSeconds(floatTotalSeconds):
    '''break a floating point seconds value into integer hours, minutes, seconds (round to nearest second)'''
    import math
    intHours = int(math.floor(floatTotalSeconds/3600))
    floatSecondsRemainder = floatTotalSeconds - intHours * 3600
    intMinutes = int(math.floor(floatSecondsRemainder/60))
    floatSecondsRemainder = floatSecondsRemainder - intMinutes * 60
    intSeconds = int(round(floatSecondsRemainder))
    return intHours, intMinutes, intSeconds

def formatTime(epochSecs):
    '''given an epoch time, return a formatted time in the local time zone'''
    import time
    return time.strftime("%d %b %Y %I:%M:%S %p", time.localtime(epochSecs))

def getMinutesSince(epochSecs):
    '''get the elapsed time in minutes since the given epoch time'''
    import time
    return (time.time() - epochSecs) / 60.

def printDataset(dataset):
    for row in range(dataset.rowCount):
        print ''
        for col in range(dataset.columnCount):
            value = dataset.getValueAt(row, col)
            print value

def doNothing():
    '''a minimal function useful for timing tests on java-to-python calls'''
    return 1


def splitPath(path):
    '''split the path at the last slash'''
    slashIndex = path.rfind('/')
    if slashIndex == -1:
        return path, ''
    else:
        prefix = path[0 : slashIndex]
        suffix = path[slashIndex + 1 : len(path)]
        return prefix, suffix
    
def isString(value):
    '''check if the given value is a string'''
    return isinstance(value, str)

def getChartStatus(runId):
    '''Get the status of a running chart. Returns None if the run is not found'''
    from system.sfc import getRunningCharts
    runningCharts = getRunningCharts()
    status = None
    for row in range(runningCharts.rowCount):
        rowRunId = runningCharts.getValueAt(row, 'instanceId')
        if rowRunId == runId:
            chartState = runningCharts.getValueAt(row, 'chartState')
            status = str(chartState)
    return status

def chartIsRunning(chartPath):
    '''Check if the given chart is running. '''
    from system.sfc import getRunningCharts
    runningCharts = getRunningCharts()
    for row in range(runningCharts.rowCount):
        if chartPath == runningCharts.getValueAt(row, 'chartPath'):
            chartState = runningCharts.getValueAt(row, 'chartState')
            if not chartState.isTerminal():
                return True
    return False

def logExceptionCause(contextMsg, logger=None):
    '''
    Attempt to get a root cause message for the exception, and log/print it--
    '''
    import sys
    exception = sys.exc_info()[1]    
    fullMsg = contextMsg + ": " + str(exception)
    
    # Get a traceback as well:
    tracebackMsg = None
    try:
        import traceback
        tracebackMsg = traceback.format_exc()
    except:
        pass

    javaCauseMsg = None    
    # for Java exceptions, get the cause
    try:
        javaCauseMsg = exception.getCause().getMessage()
    except:
        # no cause
        pass
       
    # Log or print the error message
    '''
    The log utility is really stupid when it comes to embedded '%' characters.  It interprets them all as format characters.
    So be shure to escape the '%' as '%%' for the logger.  But I don't want to do that with the error messages that I return which will
    ultimately be sent to the client and displayed in a vision window.  One of the common causes of error is in a log or irint statement 
    that uses the '%' character.  Prior to escaping these this error trapping routine would throw an error.
    '''
    if logger != None:
        logger.errorf(string.replace(fullMsg, "%", "%%"))
        if javaCauseMsg != None:
            logger.errorf(string.replace(javaCauseMsg, "%", "%%"))
        logger.errorf(string.replace(tracebackMsg, "%", "%%"))
    else:
        print fullMsg
        if javaCauseMsg != None:
            print javaCauseMsg
        print tracebackMsg
 
    return fullMsg, tracebackMsg, javaCauseMsg
