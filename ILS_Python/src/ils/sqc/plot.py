'''
Created on Dec 10, 2015

@author: Pete
'''
import system

# This sets the target and limit values of a chart
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
    
def calculateLimitsFromTargetAndSigma(rootContainer, target, sigma):
    upperLimit = target + 6 * sigma
    lowerLimit = target - 6 * sigma
    
    rootContainer.yAxisLowerLimit = lowerLimit
    rootContainer.yAxisUpperLimit = upperLimit
    

def fetchChartInfo(sqcBlockName, blockId):
    import system.ils.blt.diagram as diagram
#    diagramDescriptor=diagram.getDiagramForBlock(sqcDiagnosisId)
#    diagramId=diagramDescriptor.getId()
    
    #Now get the SQC observation blocks
#    blocks=diagram.listBlocksUpsreamOf(diagramId, sqcBlockName)
#    for block in blocks:
#        if block.getClassName() == "com.ils.block.SQC":
#            print "Found One!"
    
    chartInfo={
          "target": 7.5,
          "standardDeviation": 0.5,
          "upperLimit1": 8.25,
          "upperLimit2": 9.0,
          "lowerLimit1": 7.75,
          "lowerLimit2" : 6.0
          }
    
    return chartInfo


def fetchChartData(labDatum):

    chartData = []
    chartData.append({"x": 0.0, "y": 7.9})
    chartData.append({"x": 0.0, "y": 7.9})
    
    return chartData