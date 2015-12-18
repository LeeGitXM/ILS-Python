'''
Created on Dec 10, 2015

@author: Pete
'''
import system, string

def configureChart(rootContainer):
    import system.ils.blt.diagram as diagram
    sqcDiagnosisName=rootContainer.sqcDiagnosisName
    sqcDiagnosisId=rootContainer.blockId
    
    chartInfo=getSqcInfoFromDiagram(sqcDiagnosisName, sqcDiagnosisId)
    labValueName=getLabValueNameFromDiagram(sqcDiagnosisName, sqcDiagnosisId)
    rootContainer.valueName=labValueName

    # Get the SQC limits out of the chartInfo
    highLimits=[]
    lowLimits=[]
    violatedRules=[]
    for info in chartInfo:
        if info['limitType'] == 'HIGH' and info['limit'] >= 0.5:
            highLimits.append(info['limit'])
        if info['limitType'] == 'LOW' and info['limit'] >= 0.5:
            lowLimits.append(info['limit'])
            
        if string.upper(info['state']) == 'SET':
            rule="%s %s of %s" % (info["limitType"], str(info["minimumOutOfRange"]), str(info["sampleSize"]))
            violatedRules.append([rule])

    # Create a dataset from the violated rules and put it in the rootContainer which will drive the table of violated rules
    ds=system.dataset.toDataSet(["rule"], violatedRules)
    rootContainer.violatedRules=ds

    # Each block dictionary has target and standard deviation, but they should all be the same
    target=info['target']
    standardDeviation=info['standardDeviation']
    
    highLimits.sort()
    lowLimits.sort()
    print "The high limits are: ", highLimits
    print "The low limits are: ", lowLimits
    
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
    
    print "Fetching chart info..."
    #Now get the SQC observation blocks
    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
    blocks=diagram.listBlocksUpstreamOf(diagramId, sqcBlockName)
    print "Found blocks: ", blocks
    sqcInfo=[]
    for block in blocks:
        print "Found a block..."
        if block.getClassName() == "com.ils.block.SQC":
            print "   ... it is a SQC block..."
            blockId=block.getIdString()
            print "Id: ", blockId
            
            # First get block properties
            blockName=diagram.getPropertyValue(diagramId, blockId, 'BlockName')
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
            attributes = block.getInternalStatus().getAttributes()
            print "Attributes: ", attributes
            target=diagram.getPropertyValue(diagramId, blockId, 'Target')
            standardDeviation=diagram.getPropertyValue(diagramId, blockId, 'StandardDeviation')
                
            sqcInfo.append({
                            "target": target,
                            "standardDeviation": standardDeviation,
                            "limitType": str(limitType),
                            "sampleSize": sampleSize,
                            "minimumOutOfRange": 1,
                            "numberOfStandardDeviations": numberOfStandardDeviations,
                            "state": state
                            })
    
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
