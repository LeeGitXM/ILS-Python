'''
Created on Dec 10, 2015

@author: Pete
'''
import system, string

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()"
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
    
    labValueName=getLabValueNameFromDiagram(sqcDiagnosisName, sqcDiagnosisId)
    print "Lab Value Name: ", labValueName
    rootContainer.valueName=labValueName

    # Get the SQC limits out of the chartInfo
    highLimits=[]
    lowLimits=[]
    violatedRules=[]
    for info in chartInfo:
        print "Info: ", info
        if info['limitType'] == 'HIGH' and abs(info['numberOfStandardDeviations']) >= 0.5:
            highLimits.append(abs(info['numberOfStandardDeviations']))
        if info['limitType'] == 'LOW' and abs(info['numberOfStandardDeviations']) >= 0.5:
            lowLimits.append(abs(info['numberOfStandardDeviations']))
            
        if string.upper(info['state']) == 'SET':
            rule="%s %s of %s" % (info["limitType"], str(info["minimumOutOfRange"]), str(info["sampleSize"]))
            violatedRules.append([rule])

    print "Violated Rules: ", violatedRules

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
    
    if target == None or target == "NaN" or standardDeviation != None or standardDeviation != "NaN":
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
            upperLimit1 = target + standardDeviation * highLimits[0]
        if len(highLimits) >= 2:
            upperLimit2 = target + standardDeviation * highLimits[1]
        
        lowerLimit1=target
        lowerLimit2=target
        if len(lowLimits) >= 1:
            lowerLimit1 = target - standardDeviation * lowLimits[0]
        if len(lowLimits) >= 2:
            lowerLimit2 = target - standardDeviation * lowLimits[1]

    rootContainer.lowerLimit1=lowerLimit1
    rootContainer.lowerLimit2=lowerLimit2
    rootContainer.upperLimit1=upperLimit1
    rootContainer.upperLimit2=upperLimit2
    rootContainer.target=target
    rootContainer.standardDeviation=standardDeviation
    
    # Now set the auto Y-axis limits
    calculateLimitsFromTargetAndSigma(rootContainer)
    
    # Configure the where clause of the database pens
    configureChartValuePen(rootContainer, labValueName)

# This sets the target and limit values of a chart.  This is called when any of the limits that
# are properties of the window change and this updates the chart.
def configureChartValuePen(rootContainer, labValueName):
    print "Updating the value database pen for %s..." % (labValueName)
    chart=rootContainer.getComponent('Easy Chart')
    ds = chart.pens
    whereClause = "ValueName = '%s'" % labValueName
    ds = system.dataset.setValue(ds, 0, "WHERE_CLAUSE", whereClause)
    chart.pens = ds


# This sets the target and limit values of a chart.  This is called when any of the limits that
# are properties of the window change and this updates the chart.
def configureChartSQCLimit(rootContainer, limit, value):
    print "Setting %s to %f..." % (limit, value)
    chart=rootContainer.getComponent('Easy Chart')
    ds = chart.calcPens
    
    for row in range(ds.rowCount):
        if ds.getValueAt(row, "NAME") == limit:
            print "Setting it"
            ds = system.dataset.setValue(ds, row, "FUNCTION_PARAM", value)
    
    chart.calcPens = ds

def setYAxisLimits(rootContainer, limit, value):
    print "Setting %s to %f..." % (limit, value)
    chart=rootContainer.getComponent('Easy Chart')
    ds = chart.axes
    
    if limit == 'yAxisLowerLimit':
        col = 'LOWER_BOUND'
    else:
        col = 'UPPER_BOUND'
        
    # The SQC chart only has one axis
    row = 0
    ds = system.dataset.setValue(ds, row, col, value)
    
    chart.axes = ds
    
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
    
#    chartInfo=[]
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'HIGH',"sampleSize":1,"minimumOutOfRange":1,"limit":3.0,"state":"Set"})
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'HIGH',"sampleSize":4,"minimumOutOfRange":3,"limit":1.45,"state":"Set"})
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'HIGH',"sampleSize":9,"minimumOutOfRange":9,"limit":0.001,"state":"Unset"})
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'LOW',"sampleSize":9,"minimumOutOfRange":9,"limit":0.001,"state":"Unset"})
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'LOW',"sampleSize":4,"minimumOutOfRange":3,"limit":1.45,"state":"Unset"})
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'LOW',"sampleSize":1,"minimumOutOfRange":1,"limit":3.0,"state":"Unset"})   
#    return chartInfo
    
    diagramDescriptor=diagram.getDiagramForBlock(sqcDiagnosisId)
    if diagramDescriptor == None:
        print "Unable to locate the diagram for block with id: ", sqcDiagnosisId
        return None
    
    print "Diagram Descriptor: ", diagramDescriptor
    diagramId=diagramDescriptor.getId()
    
    print "Fetching upstream block info for chart <%s> ..." % (str(diagramId))
    #Now get the SQC observation blocks
    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
    blocks=diagram.listBlocksUpstreamOf(diagramId, sqcBlockName)
    print "Found blocks: ", blocks
    sqcInfo=[]
    for block in blocks:
        print "Found a %s block..." % (block.getClassName())
        if block.getClassName() == "com.ils.block.SQC":
            print "   ... it is a SQC block..."
            blockId=block.getIdString()
            print "Id: ", blockId
            
            # First get block properties
            blockName=block.getName()
            print "Name: ", blockName
            
            sampleSize=diagram.getPropertyValue(diagramId, blockId, 'SampleSize')
            print "Sample Size: ", sampleSize
            numberOfStandardDeviations=diagram.getPropertyValue(diagramId, blockId, 'NumberOfStandardDeviations')
            print "# of Std Devs: ", numberOfStandardDeviations
            limitType=diagram.getPropertyValue(diagramId, blockId, 'LimitType')
            print "Limit Type: ", limitType
            
            # now the state
            state=diagram.getBlockState(diagramId, blockName)
            print "State: ", state
            
            # now get some block internals
            print "Getting attributes..."
            attributes = block.getAttributes()
            print "Attributes: ", attributes
            target=attributes.get('Mean (target)')
            standardDeviation=attributes.get('StandardDeviation')
                
            sqcInfo.append({
                            "target": target,
                            "standardDeviation": standardDeviation,
                            "limitType": str(limitType),
                            "sampleSize": sampleSize,
                            "minimumOutOfRange": 1,
                            "numberOfStandardDeviations": numberOfStandardDeviations,
                            "state": state
                            })
            print sqcInfo
    
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'HIGH',"sampleSize":1,"minimumOutOfRange":1,"limit":3.0,"state":"Set"})
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'HIGH',"sampleSize":4,"minimumOutOfRange":3,"limit":1.45,"state":"Set"})
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'HIGH',"sampleSize":9,"minimumOutOfRange":9,"limit":0.001,"state":"Unset"})
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'LOW',"sampleSize":9,"minimumOutOfRange":9,"limit":0.001,"state":"Unset"})
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'LOW',"sampleSize":4,"minimumOutOfRange":3,"limit":1.45,"state":"Unset"})
#    chartInfo.append({"target": 7.5,"standardDeviation": 0.5,"limitType":'LOW',"sampleSize":1,"minimumOutOfRange":1,"limit":3.0,"state":"Unset"})
    
    return sqcInfo



def fetchChartData(labDatum):

    chartData = []
    chartData.append({"x": 0.0, "y": 7.9})
    chartData.append({"x": 0.0, "y": 7.9})
    
    return chartData

def getLabValueNameFromDiagram(sqcBlockName, sqcDiagnosisId):
    import system.ils.blt.diagram as diagram
    
    labValueName="MOONEY-LAB-DATA"
    
    return labValueName
