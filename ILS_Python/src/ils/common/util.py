'''
Created on Sep 10, 2014

@author: Pete
'''

import system
 
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


def getDate(database = ""):
    SQL = "select getdate()"
    theDate = system.db.runScalarQuery(SQL, database)
    return theDate


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

'''
Simulate a word wrap by converting a text string to HTML and inserting <br> tokens into the 
text string at the requested line length
'''
def formatHTML(txt, lineLength):
    tokens = txt.split(" ")
    txt = ""
    line = ""
    for token in tokens:
        line = "%s%s " % (line, token)
        if len(line) > lineLength:
            if txt == "":
                txt = line
            else:
                txt = "%s<br>%s" % (txt, line)
            line = ""
    txt = "<HTML>%s<br>%s" % (txt, line)
    return txt


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

def escapeSqlQuotes(string):
    return string.replace("'", "''")

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
'''
def readAverageValues(tagPaths, tagProvider, timeIntervalMinutes, log):
    fullTagPaths = []
    for tagPath in tagPaths:
        fullTagPaths.append("[%s]%s" % (tagProvider, tagPath))
    
    ds = system.tag.queryTagHistory(
        paths=fullTagPaths, 
        endDate=system.date.now(), 
        rangeMinutes=-1*timeIntervalMinutes, 
        aggregationMode="Average", 
        returnSize=1, 
        ignoreBadQuality=True
        )
    
    badValue = False
    for i in range(0,len(tagPaths)):
        isGood = ds.getQualityAt(0, i + 1).isGood()
        print "Average value for %s isGood %s" % (tagPaths[i], str(isGood))
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
        print "Instantaneous value for %s is %s" % (tagPaths[i], qv)
        if not(qv.quality.isGood()):
            badValue = True
            log.warnf("Read a bad value for %s - %s", tagPaths[i], str(qv))
            
    return badValue, qvs

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

    badValue, ds = readAverageValues(tagPaths, "XOMhistory", 30, log)
    print "Reading historic average, isBad = ", badValue
    
    badValue, qvs = readInstantaneousValues(tagPaths, "XOM", log)
    print "Reading current values, isBad = ", badValue
    