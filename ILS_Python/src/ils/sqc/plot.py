'''
Created on Dec 10, 2015

@author: Pete
'''
import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.sqc.plot")

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()"
    
    # Reset the tab strip so the plot tab is selected
    tabStrip = rootContainer.getComponent("Tab Strip")
    tabStrip.selectedTab="Plot"
    configureChart(rootContainer)


def internalFrameActivated(rootContainer):
    print "In internalFrameActivated()"


def configureChart(rootContainer):
    import system.ils.blt.diagram as diagram
    sqcDiagnosisName=rootContainer.sqcDiagnosisName
    sqcDiagnosisId=rootContainer.blockId
    
    chartInfo=getSqcInfoFromDiagram(sqcDiagnosisName, sqcDiagnosisId)
    print "Chart Info: ", chartInfo
    if chartInfo == None:
        system.gui.errorBox("Unable to configure an SQC chart for an SQC Diagnosis without a block id")
        return
    
    unitName, labValueName=getLabValueNameFromDiagram(sqcDiagnosisName, sqcDiagnosisId)
    rootContainer.unitName=unitName
    rootContainer.valueName=labValueName

    # Get the SQC limits out of the chartInfo
    highLimits=[]
    lowLimits=[]
    violatedRules=[]
    print "Determining violated rules..."
    for info in chartInfo:
        print "Info: ", info
        if info['limitType'] == 'HIGH' and abs(float(str(info['numberOfStandardDeviations']))) >= 0.5:
            highLimits.append(abs(float(str(info['numberOfStandardDeviations']))))
        if info['limitType'] == 'LOW' and abs(float(str(info['numberOfStandardDeviations']))) >= 0.5:
            lowLimits.append(abs(float(str(info['numberOfStandardDeviations']))))
        
        state=string.upper(str(info['state']))
        if state in ['SET', 'TRUE']:
            rule="%s %s of %s" % (info["limitType"], str(info["minimumOutOfRange"]), str(info["sampleSize"]))
            violatedRules.append([rule])

    print "...violated Rules: ", violatedRules
    
    # Create a dataset from the violated rules and put it in the rootContainer which will drive the table of violated rules
    ds=system.dataset.toDataSet(["rule"], violatedRules)
    rootContainer.violatedRules=ds

    # Each block dictionary has target and standard deviation, but they should all be the same
    target=info['target']
    standardDeviation=info['standardDeviation']
    print "Target: ", target
    print "Standard Deviation:", standardDeviation
    
    highLimits.sort()
    lowLimits.sort()
    print "The high limits are: ", highLimits
    print "The low limits are: ", lowLimits

    sqcInfo=[]
    
    if target == None or target == "NaN" or standardDeviation == None or standardDeviation == "NaN":
        print "Unable to completely configure the SQC chart"
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

        print "Determining SQC Info..."
        sqcInfo.append(["Target", float(str(target))])
        for info in chartInfo:
            print "Info: ", info
    
            if info['limitType'] == 'HIGH':
                txt="High Limit (%s sigma)" % (str(info['numberOfStandardDeviations']))
                val = float(target) + float(standardDeviation) * float(info['numberOfStandardDeviations'])
                sqcInfo.append([txt, val])
            if info['limitType'] == 'LOW':
                txt="Low Limit (%s sigma)" % (str(info['numberOfStandardDeviations']))
                val = float(target) - float(standardDeviation) * float(info['numberOfStandardDeviations'])
                sqcInfo.append([txt, val])

        print "...SQC info:", sqcInfo
    
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
    
    # Now set the auto Y-axis limits - this will be called automatically from a property change script
    calculateLimitsFromTargetAndSigma(rootContainer)
    
    # Configure the where clause of the database pens which should drive the update of the chart
    configureChartValuePen(rootContainer, unitName, labValueName)

# This sets the target and limit values of a chart.  This is called when any of the limits that
# are properties of the window change and this updates the chart.
def configureChartValuePen(rootContainer, unitName, labValueName):
    print "Updating the value database pen for %s..." % (labValueName)
    chart=rootContainer.getComponent("Plot Container").getComponent('Easy Chart')
    ds = chart.pens
    whereClause = "UnitName = '%s' and ValueName = '%s'" % (unitName, labValueName)
    ds = system.dataset.setValue(ds, 0, "WHERE_CLAUSE", whereClause)
    chart.pens = ds


# This sets the target and limit values of a chart.  This is called when any of the limits that
# are properties of the window change and this updates the chart.
def configureChartSQCLimit(rootContainer, limit, value):
    print "Setting %s to %f..." % (limit, value)
    chart=rootContainer.getComponent("Plot Container").getComponent('Easy Chart')
    ds = chart.calcPens
    
    for row in range(ds.rowCount):
        if ds.getValueAt(row, "NAME") == limit:
            print "Setting it"
            ds = system.dataset.setValue(ds, row, "FUNCTION_PARAM", value)
    
    chart.calcPens = ds

def setYAxisLimits(rootContainer, limit, value):
    print "Setting %s to %f..." % (limit, value)
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

def getSqcInfoFromDiagram(sqcBlockName, sqcDiagnosisId):
    import system.ils.blt.diagram as diagram
    
    print "Getting SQC info for SQC Diagnosis named: <%s> with id: <%s>" % (sqcBlockName, sqcDiagnosisId)
   
    diagramDescriptor=diagram.getDiagramForBlock(sqcDiagnosisId)
    if diagramDescriptor == None:
        print "Unable to locate the diagram for block with id: ", sqcDiagnosisId
        return None

    diagramId=diagramDescriptor.getId()
    
    print "Fetching upstream block info for chart <%s> ..." % (str(diagramId))
    #Now get the SQC observation blocks
    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
    blocks=diagram.listBlocksUpstreamOf(diagramId, sqcBlockName)
#    print "Found blocks: ", blocks
    sqcInfo=[]
    for block in blocks:
#        print "Found a %s block..." % (block.getClassName())
        if block.getClassName() == "com.ils.block.SQC":
            print "   ... found a SQC block..."
            blockId=block.getIdString()
            blockName=block.getName()
            
            # First get block properties
            sampleSize=diagram.getPropertyValue(diagramId, blockId, 'SampleSize')
            numberOfStandardDeviations=diagram.getPropertyValue(diagramId, blockId, 'NumberOfStandardDeviations')
            
            # now the state
            state=diagram.getBlockState(diagramId, blockName)
            
            # now get some block internals
            attributes = block.getAttributes()
#            print "Attributes: ", attributes
            target=attributes.get('Mean (target)')
            standardDeviation=attributes.get('StandardDeviation')
            limitType=attributes.get('Limit type')
            
            sqcDictionary = {
                            "target": target,
                            "standardDeviation": standardDeviation,
                            "limitType": str(limitType),
                            "sampleSize": sampleSize,
                            "minimumOutOfRange": 1,
                            "numberOfStandardDeviations": numberOfStandardDeviations,
                            "state": state
                            }
            sqcInfo.append(sqcDictionary)
            print sqcDictionary
        
    return sqcInfo


def getLabValueNameFromDiagram(sqcBlockName, sqcDiagnosisId):
    import system.ils.blt.diagram as diagram
    
    unitName=None
    labValueName=None
    
    print "Getting Lab value name for SQC Diagnosis named: <%s> with id: <%s>" % (sqcBlockName, sqcDiagnosisId)
   
    diagramDescriptor=diagram.getDiagramForBlock(sqcDiagnosisId)
    if diagramDescriptor == None:
        print "Unable to locate the diagram for block with id: ", sqcDiagnosisId
        return unitName, labValueName
    
    diagramId=diagramDescriptor.getId()
    
    print "Fetching upstream block info for chart <%s> ..." % (str(diagramId))

    # Get all of the upstream blocks
    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
    blocks=diagram.listBlocksUpstreamOf(diagramId, sqcBlockName)
#    print "Found blocks: ", blocks

    for block in blocks:
#        print "Found a %s block..." % (block.getClassName())
        if block.getClassName() == "com.ils.block.LabData":
            print "   ... found the LabData block..."
            blockId=block.getIdString()
            blockName=block.getName()
            
            # First get block properties
            
            #********************
            # 2/8/2016
            # Chuck is adding a new scripting function getPropertyBinding which should give me the tagpath rathe rthan the value.
            #********************
            
            valueTagPath=diagram.getPropertyValue(diagramId, blockId, 'ValueTagPath')
            print "valueTagPath: ", valueTagPath
            
            # TODO - This was returning the value of the tag and I want the name of the tag
            print "*****************************************"
            print "* Have C9-LAB-DATA hard coded here      *"
            print "*****************************************"
            valueTagPath="[XOM]LabData/RLA3/C9-LAB-DATA/value"
            
            # Strip off the trailing "/value"
            if valueTagPath.endswith("/value"):
                valueTagPath=valueTagPath[:len(valueTagPath) - 6]
            else:
                log.warn("Unexpected lab value tag path - expected path to end with /value")
            
            # Now strip off everything (provider and path from the left up to the last "/"
            valueTagPath=valueTagPath[valueTagPath.find("]")+1:]
            print valueTagPath
            unitName=valueTagPath[valueTagPath.find("/")+1:valueTagPath.rfind("/")]
            labValueName=valueTagPath[valueTagPath.rfind("/")+1:]
            
            # now get some block internals
#            attributes = block.getAttributes()
#            print "Attributes: ", attributes
    
    print "Found unit: <%s> - lab value: <%s>" % (unitName, labValueName)
    return unitName, labValueName


def fetchChartData(unitName, labValueName):

    chartData = []
    chartData.append({"x": 0.0, "y": 7.9})
    chartData.append({"x": 0.0, "y": 7.9})
    
    return chartData
