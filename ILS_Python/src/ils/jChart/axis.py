'''
Created on Aug 27, 2014

@author: ILS
'''

# For a stacked chart, the top plot is index 0

#
# X Axis Manipulations 
#
# I don't ever envision having more than a single X (Domain) axis, I'm not even sure you can,
# but I will allow the axisIndex to be passed in just in case.
def xLimits(chart, lowLimit, highLimit, plotIndex=0, axisIndex=0):
    from ils.jChart.common import getPlot
    plot = getPlot(chart, plotIndex)
    axis = plot.getDomainAxis(axisIndex)
    if axis != None:
        axis.setLowerBound(lowLimit)
        axis.setUpperBound(highLimit)

def xLabel(chart, label, plotIndex=0, axisIndex=0):
    from ils.jChart.common import getPlot
    axisIndex = 0
    plot = getPlot(chart, plotIndex)
    axis = plot.getDomainAxis(axisIndex)
    if axis != None:
        axis.setLabel(label)

#
# Y Axis Manipulations
#

# For a stacked chart, the top plot is index 0
# Each axis has its own dataset and renderer to give complete individual control over each series
def yAdd(chart, plotIndex, axisIndex, label, leftOrRight):
    import string
    from ils.jChart.common import getPlot
    from org.jfree.chart.axis import NumberAxis
    from org.jfree.chart.axis import AxisLocation
    from org.jfree.data.xy import XYSeriesCollection
    from org.jfree.chart.renderer.xy import XYLineAndShapeRenderer
    
    print "Adding a y-axis: %s" % (label)
    plot = getPlot(chart, plotIndex)        
    plot.setRangeAxis(axisIndex, NumberAxis(label))
    axisloc = AxisLocation
    if string.lower(leftOrRight) == 'left':
        location = axisloc.TOP_OR_LEFT
    else:
        location = axisloc.BOTTOM_OR_RIGHT

    plot.setRangeAxisLocation(axisIndex, location)
    plot.setDataset(axisIndex, XYSeriesCollection())
    plot.mapDatasetToRangeAxis(axisIndex, axisIndex)
    
    # Added by Pete 10/31/14
    plot.setRenderer(axisIndex, XYLineAndShapeRenderer())
    


def yOrientation(chart, plotIndex, axisIndex, label, leftOrRight):
    import string
    from ils.jChart.common import getPlot
    from org.jfree.chart.axis import AxisLocation
    
    plot = getPlot(chart, plotIndex)
    axisloc = AxisLocation
    
    if string.lower(leftOrRight) == 'left':
        location = axisloc.TOP_OR_LEFT
    else:
        location = axisloc.BOTTOM_OR_RIGHT

    plot.setRangeAxisLocation(axisIndex, location)

    
def yLabel(chart, plotIndex, axisIndex, label):
    from ils.jChart.common import getPlot
    plot = getPlot(chart, plotIndex)
    axis = plot.getRangeAxis(axisIndex)
    if axis != None:
        axis.setLabel(label)


def yLimits(chart, plotIndex, axisIndex, lowLimit, highLimit):
    from ils.jChart.common import getPlot
    plot = getPlot(chart, plotIndex)        
    axis = plot.getRangeAxis(axisIndex)
    if axis != None:
        axis.setLowerBound(lowLimit)
        axis.setUpperBound(highLimit)


def yAutoRange(chart, plotIndex, axisIndex):
    from ils.jChart.common import getPlot
    plot = getPlot(chart, plotIndex)
    axis = plot.getRangeAxis(axisIndex)
    if axis != None:
        axis.setAutoRangeIncludesZero(False)
        axis.setAutoRange(True)


def yVisibility(chart, plotIndex, axisIndex, visible):
    from ils.jChart.common import getPlot
    plot = getPlot(chart, plotIndex)        
    axis = plot.getRangeAxis(axisIndex)
    if axis != None:
        axis.setVisible(visible)

# TODO - Not sure what the intent of this was...
# Getthe number of y-axis
def yNum(chart):
    print "In yNum"
    plot = chart.getChart().getXYPlot()
    axes = plot.getAxesAtLeft()
    print axes
    
# TODO
def yDelete(chart, axisIndex):
    print "In xAxisLimits"
    axes = chart.getXAxes()

    axis = axes.get('axisName')
    axis.setLowerBound('lowLimit')
    axis.setUpperBound('highLimit')

    chart.setXAxes(axes)

    #Tells the chart to re-fresh itself
    chart.createChart()