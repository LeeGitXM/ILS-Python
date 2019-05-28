'''
Created on Sep 10, 2014

@author: Pete
'''

import system, string
log = system.util.getLogger("com.ils.common.util")
from ils.common.config import getTagProvider
from system.date import secondsBetween

def stripHTML(msg):
    msg=string.replace(msg, "<br>", " ")
    msg=string.replace(msg, "<HTML>", "")
    msg=string.replace(msg, "<html>", "")
    msg=string.replace(msg, "<b>", "")
    msg=string.replace(msg, "</b>", "")
    return msg

def getSiteName(db=""):
    siteName = system.db.runScalarQuery("select SiteName from TkSite", database=db)
    return siteName

def okToPrint():
    from javax.print import PrintServiceLookup as PSL

    printerList = PSL.lookupPrintServices(None, None)
    defaultPrinter = PSL.lookupDefaultPrintService()

    if defaultPrinter in [None, ""]:
        return False
    
    if len(printerList) == 0:
        return False
    
    return True

def isUserConnected(userName):
    sessions = system.util.getSessionInfo()
    for session in sessions:
        if string.upper(session["username"]) == string.upper(userName) and session["isDesigner"] == False:
            print "The user IS connected"
            return True
        print session

    print "The user is NOT connected"
    return False

def isWarmboot():
    '''
    This is called by many (all) of the toolkits during startup.  It is ok that we are using the production tag provider here since a 
    warmboot is a warmboot regardless of tag provider.
    '''
    tagProvider = getTagProvider()
    runHours = getRunHours(tagProvider)
    
    if runHours > 5.0 / 60.0:
        return True
    
    return False
        
def getRunHours(tagProvider):
    tagPath = "[%s]Site/Watchdogs/Ignition Uptime Minutes" % (tagProvider)
    exists = system.tag.exists(tagPath)
    if exists:
        runMinutes = system.tag.read(tagPath).value
        if runMinutes == None:
            runHours = 0.0
        else:
            runHours = runMinutes / 60.0
    else:
        runHours = 0.0
        print "WARNING: the Ignition uptime counter tag (%s) does not exist!" % (tagPath)
    return runHours
    
def checkIfPrintingAllowed(providerName):
    tagPath="[%s]Configuration/Common/printingAllowed" % (providerName)
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        printingAllowed = system.tag.read(tagPath).value
    else:
        printingAllowed = True
    
    return printingAllowed

def listSum(numList):
    theSum = 0.0
    for num in numList:
        theSum = theSum + num
    return theSum

def listMin(numList):
    theMin = 1000000000
    for num in numList:
        if num < theMin:
            theMin = num
    return theMin

def scalerMultiply(array, scaler):
    result = []
    for val in array:
        result.append(val * scaler)
    return result

def isText(val):

    try:
        val = float(val)
        isText = False
    except:
        isText = True

    return isText


# Check if the val is one of the special values, NaN, None....
def isaValidNumber(val):
    sval = str(val)
    
    if sval in ['nan', 'NaN', 'NAN', 'NONE']:
        return False

    try:
        val = float(val)
        isFloat = True
    except:
        isFloat = False
    
    return isFloat


def unixTime(theTime=system.date.now()):
    epoch = system.date.getDate(1970,0,1)
    epoch = system.date.setTime(epoch, 0, 0, 0)
    unixTime = system.date.secondsBetween(epoch, theTime)
    return unixTime


def getDate(database = ""):
    SQL = "select getdate()"
    theDate = system.db.runScalarQuery(SQL, database)
    return theDate

# Find the root container component that is, or is the parent
# of the specified component.
def getRootContainer(component):
    while component != None:
        if component.name == "Root Container":
            break
        component = component.parent
    return component

def formatDate(theDate, format = 'MM/dd/yy'):
    theDate = system.db.dateFormat(theDate, format)
    return theDate

    
def formatDateTime(theDate, format = 'MM/dd/yy HH:mm'):
    if theDate == None:
        theDate = ""
    else:
        theDate = system.db.dateFormat(theDate, format)
    return theDate

'''
String representation of a date time that is accepted by SQLServer
'''
def formatDateTimeForDatabase(theDate):
    theDate = formatDateTime(theDate, 'yyyy-MM-dd HH:mm:ss')
    return theDate

# Returns the m and b constants from the equation y = mx + b
def equationOfLine(x1, y1, x2, y2):
    
    # Found a horizontal line
    if (y2 - y1) == 0:
        return 0.0, y1
    
    # Found a vertical line which isn't handled very well
    if (x2 - x1) == 0:
        return 999999.0, 0.0
    
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1
    
    return m, b

# Calculate the Y value for a line given an X value and the slope and y-Intercept
def calculateYFromEquationOfLine(x, m, b):
    y = x * m + b
    return y

# Calculate the Y value for a line given an X value and the slope and y-Intercept
def calculateXFromEquationOfLine(y, m, b):
    x = (y - b) / m
    return x

def escapeSqlQuotes(txt):
    txt = string.replace(txt, "'", "''")
    return txt

def substituteProvider(tagPath, provider):
    '''alter the given tag path to reflect the supplied provider'''
    
    rbIndex = tagPath.find(']')
    if rbIndex >= 0:
        return '[' + provider + ']' + tagPath[rbIndex+1:len(tagPath)]
    else:
        return '[' + provider + ']' + tagPath

'''
A little utility for a one liner that I can never remember.  Clear a dataset keeping the header intact.
'''
def clearDataset(ds):
    ds = system.dataset.deleteRows(ds, range(ds.rowCount))
    return ds

'''
return a dataset with one row.  The first column is a timestamp and each subsequent column is a tags aggregated value, one value for each tag.
It also returns a flag that indicates if any one of the tags is Nan, or None.  This query does not return a quality.
I've gone back and forth on how to use queryTagHistory, it seems like Ignition should know which tag provider to use given the tag, but as of today's
testing in Baton Rouge, I need to specify the history tag provider.  This might work differently when called from a SFC in global scope and from a client
in project scope.
'''
def queryHistory(tagPaths, historyTagProvider, tagProvider, timeIntervalMinutes, aggregationMode, log):
    
    # This function tests over the past n minutes, so make sur ethe time interval is negative
    if timeIntervalMinutes > 0:
        timeIntervalMinutes = -1 * timeIntervalMinutes

    fullTagPaths = []
    for tagPath in tagPaths:
        fullTagPaths.append("[%s/.%s]%s" % (historyTagProvider, tagProvider, tagPath))
    
    endDate = system.date.addMinutes(system.date.now(), -1)
    
    log.tracef("Calculating the %s for %s over the past %s minutes", aggregationMode, str(fullTagPaths), str(timeIntervalMinutes))
    
    ds = system.tag.queryTagHistory(
        paths=fullTagPaths, 
        endDate=endDate, 
        rangeMinutes=timeIntervalMinutes, 
        aggregationMode=aggregationMode, 
        returnSize=1, 
        ignoreBadQuality=True
        )
    
    badValue = False
    for i in range(0,len(tagPaths)):
        isGood = ds.getQualityAt(0, i + 1).isGood()
        if not(isGood):
            badValue = True
            log.warnf("Unable to collect average value for %s", tagPaths[i])

    return badValue, ds

'''
return a dataset with one row.  The first column is a timestamp and each subsequent column is a tags aggregated value, one value for each tag.
It also returns a flag that indicates if any one of the tags is Nan, or None.  This query does not return a quality.
I've gone back and forth on how to use queryTagHistory, it seems like Ignition should know which tag provider to use given the tag, but as of today's
testing in Baton Rouge, I need to specify the history tag provider.  This might work differently when called from a SFC in global scope and from a client
in project scope.
'''
def queryHistoryBetweenDates(tagPaths, historyTagProvider, tagProvider, startDate, endDate, aggregationMode, log):

    fullTagPaths = []
    for tagPath in tagPaths:
        fullTagPaths.append("[%s/.%s]%s" % (historyTagProvider, tagProvider, tagPath))
    
    log.tracef("Calculating the %s for %s between %s and %s", aggregationMode, str(fullTagPaths), str(startDate), str(endDate))
    
    ds = system.tag.queryTagHistory(
        paths=fullTagPaths,
        startDate=startDate, 
        endDate=endDate, 
        aggregationMode=aggregationMode, 
        returnSize=1, 
        ignoreBadQuality=True
        )
    
    badValue = False
    for i in range(0,len(tagPaths)):
        isGood = ds.getQualityAt(0, i + 1).isGood()
        if not(isGood):
            badValue = True
            log.warnf("Unable to collect average value for %s", tagPaths[i])

    return badValue, ds

'''
Return a list of qualified values and a flag that indicates if any one of the tags is bad or None
'''
def readInstantaneousValues(tagPaths, tagProvider, log):
    fullTagPaths = []
    for tagPath in tagPaths:
        fullTagPaths.append("[%s]%s" % (tagProvider, tagPath))
    
    qvs = system.tag.readAll(fullTagPaths)
    
    badValue = False
    for i in range(0,len(tagPaths)):
        qv = qvs[i]
        if not(qv.quality.isGood()):
            badValue = True
            log.warnf("Read a bad value for %s - %s", tagPaths[i], str(qv))

    return badValue, qvs

'''
Return a the average of the current values of a list of tags. 
'''
def averageTags(tagPaths, tagProvider, log):
    fullTagPaths = []
    for tagPath in tagPaths:
        fullTagPaths.append("[%s]%s" % (tagProvider, tagPath))
    
    qvs = system.tag.readAll(fullTagPaths)
    vals = []
    badValue = False
    for i in range(0,len(tagPaths)):
        qv = qvs[i]
        print "Instantaneous value for %s is %s" % (tagPaths[i], qv)
        if not(qv.quality.isGood()):
            badValue = True
            log.warnf("Read a bad value for %s - %s", tagPaths[i], str(qv))
        else:
            vals.append(qv.value)
    
    theMean = float(sum(vals)) / max(len(vals), 1)
    
    return badValue, theMean

'''
Return the rate of change per minute for the requested tag.
This is calculated by(firstValue - lastValue) / number of minutes from first value to last value
'''
def rateOfChangePerMinute(historyTagProvider, tagProvider, tagPath, startDate, endDate):
    minutesBetween = system.date.minutesBetween(startDate, endDate)
    fullTagPath = "[%s/.%s]%s" % (historyTagProvider, tagProvider, tagPath)
    paths = [fullTagPath]
    print paths
    ds = system.tag.queryTagHistory(paths=paths, startDate=startDate, endDate=endDate, returnSize=0)
    
    firstVal = ds.getValueAt(0,1)
    lastVal = ds.getValueAt(ds.rowCount - 1,1)
    
    print "First value: ", firstVal
    print "Last value: ", lastVal
    
    roc = (lastVal - firstVal) / minutesBetween
    
    return roc

def isNaN(num):
    return num != num

'''
Return the integral (area under the curve) of the tag.
TimeInterval is one of second, minute, hour, or day
'''
def integralOverTime(historyTagProvider, tagProvider, tagPath, startDate, endDate, timeInterval):
    
    #---------------------------------------------------------------
    def getTimeSpan(startTime, endTime, timeInterval):
        timeSpan = system.date.secondsBetween(startTime, endTime)
        
        if string.upper(timeInterval) in ["MINUTE", "MINUTES"]:
            timeSpan = timeSpan / 60.0
        elif string.upper(timeInterval) in ["DAY", "DAYS"]:
            timeSpan = timeSpan / 60.0 / 60.0 / 24.0
        elif string.upper(timeInterval) in ["HOUR", "HOURS"]:
            timeSpan = timeSpan / 60.0 / 60.0
        
        return timeSpan
    #---------------------------------------------------------------
                
    integral = 0.0
    
    fullTagPath = "[%s/.%s]%s" % (historyTagProvider, tagProvider, tagPath)
    paths = [fullTagPath]
    log.tracef("Calculating the integral for %s from %s to %s over %s", fullTagPath, str(startDate), str(endDate), timeInterval)
    
    ds = system.tag.queryTagHistory(paths=paths, startDate=startDate, endDate=endDate, includeBoundingValues=True, returnSize=0)
    log.tracef("History returned %d points...", ds.rowCount)
    
    lastTime = None
    lastValue = None
    
    for row in range(ds.rowCount):
        currentTime = ds.getValueAt(row, 0)
        currentValue = ds.getValueAt(row, 1)
        currentQuality = ds.getQualityAt(row, 1)

        if lastTime != None and currentQuality.isGood() and not(isNaN(currentValue)):
            timeSpan = getTimeSpan(lastTime, currentTime, timeInterval)
            area = (lastValue + currentValue) / 2.0 * timeSpan
            integral = integral + area
            log.tracef("Calculating the area of slice from %s to %s", str(lastTime), str(currentTime))
            log.tracef("  using values %s and %s over timespan %s...", str(lastValue), str(currentValue), str(timeSpan))
            log.tracef("  the area is %s and the total area so far is %s", str(area), str(integral))
        else:
            log.tracef("Skipping calculation for first point...")

        lastValue = currentValue
        lastTime = currentTime
        
    '''
    Add in the final slice - queryTagHistory doesn't seem to report a value at the end timer.
    The history system seems to work slightly differently in a client versus the gateway.  In the client we need to add in this final slice, but
    in the gateway we don't, possibly because in the gateway the last value is often a NaN.  In any event, the precision generally is not significantly
    affected even if we miss the last slice.
    '''
    timeSpan = getTimeSpan(lastTime, endDate, timeInterval)
    if timeSpan > 0 and not(isNaN(lastValue)):
        log.tracef("...adding area of final slice...")
        area = lastValue * timeSpan
        integral = integral + area

    log.tracef("The total integral is: %s", str(integral))
    
    return integral

def timeStringToSeconds(timeString):
    '''  Assumes a time string in the format: HH:MM:SS.sssss '''

    txt = timeString[0:timeString.find(":")]
    secs = int(txt) * 60 * 60
    timeString = timeString[timeString.find(":")+1:] 
    txt = timeString[0:timeString.find(":")]
    secs = secs + int(txt) * 60
    timeString = timeString[timeString.find(":")+1:] 
    txt = timeString[0:timeString.find(".")]
    secs = secs + int(txt)
    
    return secs

'''
This is a test of querying history to determine if we should use the tag provider name or the history tag provider name
(This should prove that we should use the tagProvider).
'''
def test():
    log = system.util.getLogger("Test")
    tagPaths=[]
#    tagPaths.append("SFC IO/Rate Change/VRF9101Z/value")  #POLY-RATE
    tagPaths.append("SFC IO/Rate Change/VRF402Z-1/value") #MAIN-C2-RATE
    tagPaths.append("SFC IO/Rate Change/VRF403R-3/value") #MAIN-C3-TO-C2-RATIO
    tagPaths.append("SFC IO/Rate Change/VCF000R-3/value") #VA-TO-C2-RATIO
    tagPaths.append("SFC IO/Rate Change/VRG401Z-1/value") #CEMENT-CONCENTRATION
    tagPaths.append("SFC IO/Cold Stick General/VRT701S-1/value") #RX-INLET-TEMP-PV
    tagPaths.append("SFC IO/Cold Stick General/VRT700S-3/value") #OUTLET-TEMP-PV
    tagPaths.append("SFC IO/Cold Stick General/VCF262R-2/value") #AL-TO-VA

    badValue, ds = queryHistory(tagPaths, "XOMhistory", "XOM", 30, "Average", log)
    print "Reading historic average, isBad = ", badValue
    
    badValue, qvs = readInstantaneousValues(tagPaths, "XOM", log)
    print "Reading current values, isBad = ", badValue

def mathTest():
    import math
    x = math.ceil(10.01)
    print x
    
#    from apache.commons.org import XYTextAnnotation