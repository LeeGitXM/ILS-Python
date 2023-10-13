'''
Created on Nov 3, 2014

@author: rforbes
'''
import system, string
from ils.sfc.common.notify import sfcNotify
from ils.sfc.common.constants import CONTROL_PANEL_ID, \
    CONTROL_PANEL_NAME, \
    CONTROL_PANEL_WINDOW_PATH, \
    DATABASE, \
    DEFAULT_MESSAGE_QUEUE, \
    HANDLER, \
    ISOLATION_MODE, \
    MESSAGE_QUEUE, \
    ORIGINATOR, \
    POSITION, \
    PROJECT, \
    SCALE, \
    POST, \
    TAG_PROVIDER, \
    TIME_FACTOR

log = system.util.getLogger(__name__)

def boolToBit(aBool):
    if aBool:
        return 1
    else:
        return 0

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

def chartIsRunning(chartPath, isolationMode=False):
    '''Check if the given chart is running. '''
    log.infof("In %s.chartIsRunning() - Checking if <%s> is currently running in Isolation Mode: %s...", __name__, chartPath, isolationMode)
    ds = system.sfc.getRunningCharts(chartPath)
    log.tracef("Found %d running <%s> chart(s)", ds.rowCount, chartPath)
    if ds.rowCount == 0:
        log.infof("The chart is NOT already running!")
        return False
    
    ''' We found a running chart, determine if the isolation Mode of the running chart matches the desired isolation mode.'''
    for row in range(ds.rowCount):
        chartState = str(ds.getValueAt(row, "ChartState"))
        log.infof("The chart state is: <%s>", str(chartState))
        if string.upper(chartState) in ["RUNNING", "PAUSED"]:
            instanceId = ds.getValueAt(row, "instanceId")
            log.infof("...found a running chart with instance id: %s", instanceId)
            
            '''
            This is a strange place for a try - except block but Escorez encountered an error on this system call.
            There is no way that this should ever fail!!!  The whole purpose of this call is to determine if the isolation mode of 
            the running chart matches the isolation mode of the client.  I will assume that the isolation mode of the chart is False.
            '''
            
            try:
                chartVars = system.sfc.getVariables(instanceId)
                log.infof("Chart variables: %s", str(chartVars))

                instanceIsolationMode = chartVars.get("isolationMode", None)
                log.infof("Running chart isolation mode: %s", str(instanceIsolationMode))
            except:
                log.infof("Error get chart variables for a running chart instance - assuming that the chart isolation mode is FALSE!")
                instanceIsolationMode = False
            
            if instanceIsolationMode == isolationMode:
                log.infof("The chart IS already running!")
                return True
        
    log.infof("The chart is NOT already running!")
    return False

def doNothing():
    '''a minimal function useful for timing tests on java-to-python calls'''
    return 1

def formatTime(epochSecs):
    '''given an epoch time, return a formatted time in the local time zone'''
    import time
    return time.strftime("%d %b %Y %I:%M:%S %p", time.localtime(epochSecs))

def getChartPathForStepUUID(stepUUID, db):
        
    SQL = "select chartPath "\
        " from sfcChart C, sfcStep S"\
        " where S.ChartId = C.ChartId "\
        " and S.StepUUID = '%s'" % (stepUUID)
        
    chartPath = system.db.runScalarQuery(SQL, db)
    
    return chartPath

def getChartStatus(runId):
    '''Get the status of a running chart. Returns None if the run is not found'''
    runningCharts = system.sfc.getRunningCharts()
    status = None
    for row in range(runningCharts.rowCount):
        rowRunId = runningCharts.getValueAt(row, 'instanceId')
        if rowRunId == runId:
            chartState = runningCharts.getValueAt(row, 'chartState')
            status = str(chartState)
    return status

'''
This is useful for getting the control panel to use when running a chart deep down in the hierarchy from the designer.
Note that chartPath is NOT the root chart which contains the unit procedure
'''
def getControlPanelForChart(chartPath, db):
    from ils.sfc.recipeData.api import s88GetRootForChart
    print "In %s.getControlPanelForChart" % (__name__)
    
    controlPanelName = ""
    controlPanelId = -1
    
    rootChartPath, rootChartId = s88GetRootForChart(chartPath, db)
    
    print "The root chart path is <%s> and the root chart id is <%d>" % (rootChartPath, rootChartId)
    
    SQL = "Select ControlPanelName, ControlPanelId from SfcControlPanel where ChartPath = '%s'" % (rootChartPath)
    pds = system.db.runQuery(SQL, db)
 
    if len(pds) == 0:
        controlPanelName = "Test"
        SQL = "Select ControlPanelId from SfcControlPanel where ControlPanelName = '%s'" % (controlPanelName)
        controlPanelId = system.db.runScalarQuery(SQL, db)
        if controlPanelId == None:
            print "ERROR: Could not find a control panel for <%s> or for Test" % (rootChartPath)
            controlPanelName = ""
            controlPanelId = -1
        else:
            print "Using the control panel for Test because a control panel was not found for <%s>" % (rootChartPath)
    else:
        record = pds[0]
        controlPanelName = record["ControlPanelName"]
        controlPanelId = record["ControlPanelId"]
        print "Found Control panel <%s> with id: %d" % (controlPanelName, controlPanelId)

    return controlPanelName, controlPanelId

def getHoursMinutesSeconds(floatTotalSeconds):
    '''break a floating point seconds value into integer hours, minutes, seconds (round to nearest second)'''
    import math
    intHours = int(math.floor(floatTotalSeconds/3600))
    floatSecondsRemainder = floatTotalSeconds - intHours * 3600
    intMinutes = int(math.floor(floatSecondsRemainder/60))
    floatSecondsRemainder = floatSecondsRemainder - intMinutes * 60
    intSeconds = int(round(floatSecondsRemainder))
    return intHours, intMinutes, intSeconds

def getMinutesSince(epochSecs):
    '''get the elapsed time in minutes since the given epoch time'''
    import time
    return (time.time() - epochSecs) / 60.

def isEmpty(aStr):
    return aStr == None or aStr.strip() == ""

def isString(value):
    '''check if the given value is a string'''
    return isinstance(value, str)

def printDataset(dataset):
    for row in range(dataset.rowCount):
        print ''
        for col in range(dataset.columnCount):
            value = dataset.getValueAt(row, col)
            print value

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

'''
This is designed to be called from a tag change script that will trigger the execution of a SFC.   
An SFC will run just fine without the control panel, even if control panel messages are used.  If the SFC 
is designed assuming that there is a control panel then this will send a message to clients to open a control panel.
'''
def startChartAndOpenControlPanel(chartPath, controlPanelName, project, post, isolationMode, showControlPanel, db, 
                                  controlPanelWindowPath="SFC/ControlPanel", position="LOWER-LEFT", scale=1.0, chartParams={}):
    
    print "In %s.startChartAndOpenControlPanel" % (__name__)
    
    if chartIsRunning(chartPath, isolationMode):
        print "Exiting because the chart is already running!"
        return
    
    if showControlPanel:
        print "Sending message to all clients to open a control panel..."
        
        messageHandler = "sfcOpenControlPanel"
        
        from ils.sfc.client.windows.controlPanel import createControlPanel, getControlPanelIdForName
        controlPanelId = getControlPanelIdForName(controlPanelName, db)
        if controlPanelId == None:
            controlPanelId = createControlPanel(controlPanelName, db)
        
        try:
            originator = system.security.getUsername()
        except:
            originator = "unknown"
        
        payload = {HANDLER: messageHandler, CONTROL_PANEL_NAME: controlPanelName, CONTROL_PANEL_ID: controlPanelId, ORIGINATOR: originator, POST: post, POSITION: position, 
                   SCALE: scale, DATABASE: db, CONTROL_PANEL_WINDOW_PATH: controlPanelWindowPath}

        print payload
        sfcNotify(project, 'sfcMessage', payload, post, controlPanelName, controlPanelId, db)
    
    ''' There should be a vesion of startChart that works from global gateway scope '''
    #startChart(chartPath, controlPanelName, project, post, isolationMode, chartParams)

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

def splitPath(path):
    '''split the path at the last slash'''
    slashIndex = path.rfind('/')
    if slashIndex == -1:
        return path, ''
    else:
        prefix = path[0 : slashIndex]
        suffix = path[slashIndex + 1 : len(path)]
        return prefix, suffix

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
    So be sure to escape the '%' as '%%' for the logger.  But I don't want to do that with the error messages that I return which will
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
