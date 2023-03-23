'''
Created on Dec 10, 2015

@author: Pete
'''
import system, string, math
from ils.config.client import getTagProvider, getDatabase
from ils.io.util import readTag
from ils.log import getLogger
log = getLogger(__name__)

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()", __name__)
    
    tagProvider = getTagProvider()
    db = getDatabase()
    log.tracef("Using database <%s> and tag provider <%s>", db, tagProvider)
    
    # Reset the tab strip so the plot tab is selected
    tabStrip = rootContainer.getComponent("Tab Strip")
    tabStrip.selectedTab="Plot"
    configureChart(rootContainer, db)

def internalFrameActivated(rootContainer):
    log.tracef("In internalFrameActivated()")

def configureChart(rootContainer, db):
    sqcDiagnosisName = rootContainer.sqcDiagnosisName
    diagramName = rootContainer.diagramName
    log.tracef("Configuring a chart for %s on %s using %s", sqcDiagnosisName, diagramName, db)
    
    lastResetTime = fetchLastResetTime(diagramName, sqcDiagnosisName, db)
    chartInfo = getSqcInfoFromDiagram(diagramName, sqcDiagnosisName)
    log.tracef("   ... chart Info: %s", str(chartInfo))
    if chartInfo == None:
        system.gui.errorBox("Unable to get SQC info for SQC Diagnosis named: %s on %s" % (str(sqcDiagnosisName), str(diagramName)))
        clearChart(rootContainer)
        return
    
    unitName, labValueName = getLabValueName(diagramName, sqcDiagnosisName)
    if unitName == None or labValueName == None:
        system.gui.errorBox("Unable to get the lab value for the SQC Diagnosis named: %s on %s" % (str(sqcDiagnosisName), str(diagramName)))
        clearChart(rootContainer)
        return
    
    rootContainer.unitName=unitName
    rootContainer.valueName=labValueName

    # Get the SQC limits out of the chartInfo
    highLimits=[]
    lowLimits=[]
    violatedRules=[]
    log.tracef("   ...determining violated rules...")
    maxSampleSize = -1
    for info in chartInfo:
        log.tracef("      ...checking: %s", str(info))
        if info['limitType'] == 'HIGH' and abs(float(str(info['numberOfStandardDeviations']))) >= 0.5:
            highLimits.append(abs(float(str(info['numberOfStandardDeviations']))))
        if info['limitType'] == 'LOW' and abs(float(str(info['numberOfStandardDeviations']))) >= 0.5:
            lowLimits.append(abs(float(str(info['numberOfStandardDeviations']))))
        
        state=string.upper(str(info['state']))
        if state in ['SET', 'TRUE']:
            log.tracef("         --- found a violated SQC rule ---")
            rule="%s %s of %s" % (info["limitType"], str(info["minimumOutOfRange"]), str(info["sampleSize"]))
            violatedRules.append([rule])

        sampleSize=int(str(info['sampleSize']))
        if sampleSize > maxSampleSize:
            maxSampleSize = sampleSize

    log.tracef("   ...the violated SQC rules are:%s ", str(violatedRules))
    log.tracef("   ...the maximum sample size is: %s", str(maxSampleSize))
    
    # Create a dataset from the violated rules and put it in the rootContainer which will drive the table of violated rules
    ds=system.dataset.toDataSet(["rule"], violatedRules)
    rootContainer.violatedRules=ds

    # Each block dictionary has target and standard deviation, but they should all be the same
    target=info['target']
    standardDeviation=info['standardDeviation']
    log.tracef("   ...Target: %s", str(target))
    log.tracef("   ...Standard Deviation: %s", str(standardDeviation))
    
    highLimits.sort()
    lowLimits.sort()
    log.tracef("   ...The high limits are: %s", str(highLimits))
    log.tracef("   ...The low limits are: %s", str(lowLimits))

    sqcInfo=[]
    
    if target == None or target == "NaN" or standardDeviation == None or standardDeviation == "NaN":
        log.tracef("Unable to completely configure the SQC chart because the target or standard deviation are missisng")
        target=0.0
        standardDeviation=0.0
        upperLimit1=target
        upperLimit2=target
        lowerLimit1=target
        lowerLimit2=target
    else:
        # Configure two upper limit red lines and two lower limit red lines
        upperLimit1=target
        upperLimit2=target
        if len(highLimits) >= 1:
            upperLimit1 = float(target) + float(standardDeviation) * float(highLimits[0])
        if len(highLimits) >= 2:
            upperLimit2 = float(target) + float(standardDeviation) * float(highLimits[1])
        
        lowerLimit1=target
        lowerLimit2=target
        if len(lowLimits) >= 1:
            lowerLimit1 = float(target) - float(standardDeviation) * float(lowLimits[0])
        if len(lowLimits) >= 2:
            lowerLimit2 = float(target) - float(standardDeviation) * float(lowLimits[1])

        log.tracef("   ...formatting the SQC Info...")
        sqcInfo.append(["Target", float(str(target))])
        for info in chartInfo:
            if info['limitType'] == 'HIGH':
                txt="High Limit (%s sigma)" % (str(info['numberOfStandardDeviations']))
                val = float(target) + float(standardDeviation) * float(info['numberOfStandardDeviations'])
                sqcInfo.append([txt, val])
            if info['limitType'] == 'LOW':
                txt="Low Limit (%s sigma)" % (str(info['numberOfStandardDeviations']))
                val = float(target) - float(standardDeviation) * float(info['numberOfStandardDeviations'])
                sqcInfo.append([txt, val])

        log.tracef("      SQC info: %s", str(sqcInfo))
    
    # Create a dataset from SQC Info and put it in the rootContainer which will drive the SQC Info table
    ds=system.dataset.toDataSet(["Limit", "Value"], sqcInfo)
    ds=system.dataset.sort(ds,"Value", False)
    rootContainer.sqcInfo=ds  

    rootContainer.lowerLimit1=lowerLimit1
    rootContainer.lowerLimit2=lowerLimit2
    rootContainer.upperLimit1=upperLimit1
    rootContainer.upperLimit2=upperLimit2
    rootContainer.target=target
    rootContainer.standardDeviation=standardDeviation
    rootContainer.yAxisAutoScaling=True
    
    # Using the number of points that are required, by looking at the n of m configuration of each block, fetch the actual lab data 
    # results and see how far back we need to go to get that number of points.  Some data is arrives hourly, others every 4 hours, etc.
    nHours=determineTimeScale(unitName, labValueName, maxSampleSize, db)
    rootContainer.n = nHours
    
    # Now set the auto Y-axis limits - this will be called automatically from a property change script
    calculateLimitsFromTargetAndSigma(rootContainer)
    
    # Configure the where clause of the database pens which should drive the update of the chart
    configureChartValuePen(rootContainer, unitName, labValueName, lastResetTime, db)


def fetchLastResetTime(diagramName, sqcDiagnosisName, db):
    SQL = "select LastResetTime from DtSQCDiagnosis SQC, DtDiagram D "\
        "where SQC.diagramId = D.diagramId "\
        "and SQC.SQCDiagnosisName = '%s' "\
        "and D.DiagramName = '%s'" % (sqcDiagnosisName, diagramName)
    lastResetTime = system.db.runScalarQuery(SQL, db)
    log.tracef( "The last reset time for %s was: %s", str(sqcDiagnosisName), str(lastResetTime))
    return lastResetTime

# Return the number of hours that are required to obtain the required # of points
def determineTimeScale(unitName, labValueName, maxSampleSize, db):
    log.tracef("...determining how much time is required to display %d points for %s...", maxSampleSize, labValueName) 
    # It is important to not bring back the entire database, so limit the query by sample time
    from java.util import Calendar
    from java.util import Date
    nowTime = Date()
    cal = Calendar.getInstance()
    cal.setTime(nowTime)
    cal.add(Calendar.HOUR, -14 * 24)
    queryStartDate = cal.getTime()
    quertStartDateTxt=system.db.dateFormat(queryStartDate, "yyyy-MM-dd H:mm:ss")
    
    SQL = "select SampleTime, RawValue from LtValueView "\
        " where UnitName = '%s' and ValueName = '%s' and SampleTime > '%s' "\
        " order by SampleTime DESC " % (unitName, labValueName, quertStartDateTxt)

    pds = system.db.runQuery(SQL, db)
    log.tracef("   ...fetched %d lab values...", len(pds))
    
    i = 0
    for record in pds:
        if i >= maxSampleSize - 1:
            sampleTime = record["SampleTime"]
            deltaTime = nowTime.getTime() - sampleTime.getTime()
            numHours = math.ceil(deltaTime / (60.0 * 60.0 * 1000.0))
            log.tracef("   ...the required hours is: %s", str(numHours))
            return numHours
        
        i = i + 1
    log.tracef( "   *** RAN OUT OF POINTS - RETURNING DEFAULT ***")
    return 24 * 7


def clearChart(rootContainer):
    log.tracef("Clearing the chart...")
    
    rootContainer.lowerLimit1 = 0
    rootContainer.lowerLimit2 = 0
    rootContainer.standardDeviation = 0
    rootContainer.target = 0
    rootContainer.upperLimit1 = 0
    rootContainer.upperLimit2 = 0
    rootContainer.violatedRules = system.dataset.toDataSet(["Rules"], [])
    rootContainer.sqcInfo = system.dataset.toDataSet(["Limit","Value"], [])
    

# This sets the where clause of the two DB pens, that stor ethe actual data values.  It also sets the colors of the pens from the 
# configuration tags..
def configureChartValuePen(rootContainer, unitName, labValueName, lastResetTime, db):
    log.tracef("...configuring the where clause of the value pens for %s...", labValueName)
    
    chart=rootContainer.getComponent("Plot Container").getComponent('Easy Chart')
    ds = chart.pens

    freshColor = readTag("/Configuration/LabData/sqcPlotFreshDataColor").value
    staleColor = readTag("/Configuration/LabData/sqcPlotStaleDataColor").value
    
    # Set the color of the current and stale data pens
    ds = system.dataset.setValue(ds, 0, "COLOR", freshColor)
    ds = system.dataset.setValue(ds, 1, "COLOR", staleColor)
    
    # Set the datasource (production or isolation)
    ds = system.dataset.setValue(ds, 0, "DATASOURCE", db)
    ds = system.dataset.setValue(ds, 1, "DATASOURCE", db)
    
    if lastResetTime == None:
        whereClause = "UnitName = '%s' and ValueName = '%s'" % (unitName, labValueName)
        log.tracef("  ...setting the where clause of the first pen: %s", whereClause)
        ds = system.dataset.setValue(ds, 0, "WHERE_CLAUSE", whereClause)
        
        # The second pen is for data that came in before the reset time, since we don't have a reset time we want to disable this pen. 
        log.tracef("  ...disabling the second pen because we do not have a reset time...")
        ds = system.dataset.setValue(ds, 1, "ENABLED", False)
    else:
        lastResetTime=system.db.dateFormat(lastResetTime, "yyyy-MM-dd H:mm:ss")    
        whereClause = "UnitName = '%s' and ValueName = '%s' and SampleTime > '%s'" % (unitName, labValueName, lastResetTime)
        log.tracef("  ...setting the where clause of the first pen: %s", whereClause)
        ds = system.dataset.setValue(ds, 0, "WHERE_CLAUSE", whereClause)
    
        whereClause = "UnitName = '%s' and ValueName = '%s' and SampleTime < '%s'" % (unitName, labValueName, lastResetTime)
        log.tracef("  ...setting the where clause of the second pen: %s", whereClause)
        ds = system.dataset.setValue(ds, 1, "WHERE_CLAUSE", whereClause)
        ds = system.dataset.setValue(ds, 1, "ENABLED", True)
    
    chart.pens = ds


# This sets the target and limit values of a chart.  This is called when any of the limits that
# are properties of the window change and this updates the chart.
def configureChartSQCLimit(rootContainer, limit, value):
    log.tracef("Setting %s to %f...", limit, value)
    chart=rootContainer.getComponent("Plot Container").getComponent('Easy Chart')
    ds = chart.calcPens
    
    for row in range(ds.rowCount):
        if ds.getValueAt(row, "NAME") == limit:
            ds = system.dataset.setValue(ds, row, "FUNCTION_PARAM", value)
    
    chart.calcPens = ds

def setYAxisLimits(rootContainer, limit, value):
    log.tracef("Setting %s to %f...", limit, value)
    chart=rootContainer.getComponent("Plot Container").getComponent('Easy Chart')
    ds = chart.axes
    
    if limit == 'yAxisLowerLimit':
        col = 'LOWER_BOUND'
    else:
        col = 'UPPER_BOUND'
        
    # The SQC chart only has one axis
    row = 0
    ds = system.dataset.setValue(ds, row, col, value)
    
    chart.axes = ds

# This is called from the Reset button at the user's discretion and from a property change 
# script on the target and the standard deviation, which are set when the window is opened.
def calculateLimitsFromTargetAndSigma(rootContainer):
    target=rootContainer.target
    standardDeviation=rootContainer.standardDeviation
    
    upperLimit = target + 6 * standardDeviation
    lowerLimit = target - 6 * standardDeviation
    
    rootContainer.yAxisLowerLimit = lowerLimit
    rootContainer.yAxisUpperLimit = upperLimit

def getSqcInfoFromDiagram(diagramName, sqcDiagnosisName):
    log.tracef("Getting SQC info for SQC Diagnosis named: <%s> with id: <%s>", sqcDiagnosisName, diagramName)
    
    ''' Get all of the upstream blocks '''
    from ils.blt.api import listBlocksGloballyUpstreamOf
    blocks = listBlocksGloballyUpstreamOf(diagramName, sqcDiagnosisName)
    log.tracef("Found blocks: %s", str(blocks))
    
    sqcInfo=[]
    for block in blocks:
        log.tracef("Found a %s block named %s...", block.getClassName(), block.getClassName())
        if block.getClassName() == "com.ils.block.SQC":
            blockName=block.getName()
            log.tracef("SQC Block: %s", blockName)
            
            ''' 
            Every block has a dictionary of attributes.  A Lab Data Entry block has two propeties from which we 
            can get the name that we are after: currentValueSubscription and currentTimeSubscription.  I'll use the 
            currentValueSubscription.  From it I can get the Unit Name and the Value Name just by parsing it.
            '''
            blockAttrs = block.getAttributes()
            #blockProps = block.getProperties()
            
            log.tracef("  Attributes: %s", str(block.getAttributes()))
            #log.tracef("  Properties: %s", str(block.getProperties()))
            
            # Everything we need is in the block attributes
            sampleSize = blockAttrs.get('SampleSize', None)
            numberOfStandardDeviations = blockAttrs.get('Limit ~ std deviations', None)
            state = blockAttrs.get("State", None)
            target = blockAttrs.get('Mean (target)')
            minimumOutOfRange = blockAttrs.get('Minimum Out of Range')
            standardDeviation = blockAttrs.get('StandardDeviation')
            limitType = blockAttrs.get('Limit type')
            
            sqcDictionary = {
                            "target": target,
                            "standardDeviation": standardDeviation,
                            "limitType": str(limitType),
                            "sampleSize": sampleSize,
                            "minimumOutOfRange": minimumOutOfRange,
                            "numberOfStandardDeviations": numberOfStandardDeviations,
                            "state": state
                            }
            sqcInfo.append(sqcDictionary)
            log.tracef(" SQC Dictionary: %s", str(sqcDictionary))
        
    return sqcInfo


def getLabValueName(diagramName, blockName):
    '''
    It sounds easy but it takes a lot of work to get the name of the lab value tag for the SQC chart.
    We start with the SQC diagnosis, because that is the entry point for SQC plotting.  The we go 
    upstream to find a labdata entry block.  Then from that we need to extract the name of the tag
    bound to the value tag path property.  We do some work to strip things off to end up with the 
    lab data name.
    '''
    
    unitName=None
    labValueName=None
    
    log.infof("In %s.getLabValueName() - Getting Lab value name for block named: <%s> on diagram: <%s>", __name__, blockName, diagramName)

    ''' Get all of the upstream blocks '''
    from ils.blt.api import listBlocksGloballyUpstreamOf
    blocks = listBlocksGloballyUpstreamOf(diagramName, blockName)
    log.tracef("Found blocks: %s", str(blocks))

    for block in blocks:
        if block.getClassName() == "com.ils.block.LabData":
            blockName=block.getName()
            
            log.tracef("...found the LabData block named: %s", blockName)

            ''' 
            Every block has a dictionary of attributes.  A Lab Data Entry block has two propeties from which we 
            can get the name that we are after: currentValueSubscription and currentTimeSubscription.  I'll use the 
            currentValueSubscription.  From it I can get the Unit Name and the Value Name just by parsing it.
            '''
            blockAttrs = block.getAttributes()
            valueTagPath = blockAttrs.get("CurrentValueSubscription", None)

            ''' Strip off the trailing /value  '''
            if valueTagPath.endswith("/value"):
                valueTagPath=valueTagPath[:len(valueTagPath) - 6]
            else:
                log.warn("Unexpected lab value tag path - expected path to end with /value")
            
            ''' Now strip off everything (provider and path from the left up to the last "/"  '''
            valueTagPath=valueTagPath[valueTagPath.find("]")+1:]
            unitName=valueTagPath[valueTagPath.find("/")+1:valueTagPath.rfind("/")]
            labValueName=valueTagPath[valueTagPath.rfind("/")+1:]
    
    log.tracef("   Found unit: <%s> - lab value: <%s>", unitName, labValueName)
    return unitName, labValueName


def fetchChartData(unitName, labValueName):
    chartData = []
    chartData.append({"x": 0.0, "y": 7.9})
    chartData.append({"x": 0.0, "y": 7.9})
    
    return chartData

def sync(event):
    sqcWindowPath='SQC/SQC Plot'
    button = event.source
    container = button.parent
    updater = container.getComponent("Realtime Updater")
    n = updater.n
    intervalType = updater.intervalType
    
    log.infof("In %s.sync() - Synchronizing all of the SQC plots to: %s - %s", __name__, intervalType, str(n))
    
    windows = system.gui.getOpenedWindows()
    log.tracef('There are %d windows open', len(windows))
    for window in windows:
        if window.getPath() == sqcWindowPath:
            log.tracef("Found an SQC plot...")
            rootContainer = window.rootContainer
            rootContainer.n = n
            rootContainer.intervalType = intervalType