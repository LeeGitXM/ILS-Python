'''
Created on Aug 27, 2014

@author: ILS
'''
import system

def assignToAxis(chart, plotIndex, seriesIndex, axisIndex):
    from ils.jChart.common import getPlot
    
    print "Assigning  the series #%i to axis #%i" % (seriesIndex, axisIndex)
    plot = getPlot(chart, plotIndex)
    plot.mapDatasetToRangeAxis(seriesIndex, axisIndex)

def getAxisAssignment(chart, plotIndex, seriesIndex):
    from ils.jChart.common import getPlot
    
    print "Fetching the dataset for series #%i..." % (seriesIndex)
    plot = getPlot(chart, plotIndex)
    axisIndex = plot.getRangeAxisForDataset(seriesIndex)
    print "  is assigned to axis #", axisIndex
    
# Set the color of an individual series.  Color is specified as a comma separated string of the RGB values
def setColor(chart, plotIndex, axisIndex, seriesIndex, color, weight, style):
    from java.awt import BasicStroke
    import string
    from ils.jChart.common import getPlot
    
    print "Setting the color of dataset ", seriesIndex, " to ", color
    plot = getPlot(chart, plotIndex)
    
    # Added axisIndex here - Pete 10/31/2014
    r = plot.getRenderer(axisIndex)
    
    theColor = system.gui.color(color)
    r.setSeriesPaint(seriesIndex, theColor)

    # Configure a stroke
    style = string.upper(style)        
    if style == 'DASH' or style == 'DASHED':
        stroke = BasicStroke(float(weight), BasicStroke.CAP_BUTT, BasicStroke.JOIN_ROUND, 1.0, [6, 6], 1.0)
    elif style == 'DASH DOT' or style == 'DASH DOT DASH':
        stroke = BasicStroke(float(weight), BasicStroke.CAP_BUTT, BasicStroke.JOIN_ROUND, 1.0, [6, 3, 3, 3], 1.0)
    else:
        stroke = BasicStroke(float(weight))

    # set the stroke
    r.setSeriesStroke(seriesIndex, stroke)

    # Turn off all shapes
    r.setSeriesShapesVisible(seriesIndex, False)

def hide(chart, plotIndex, axisIndex, seriesIndex):
    from ils.jChart.common import getPlot
    
    print "Hiding series: ", seriesIndex
    plot = getPlot(chart, plotIndex)
    r = plot.getRenderer(axisIndex)
    r.setSeriesLinesVisible(seriesIndex, False)
    
def show(chart, plotIndex, axisIndex, seriesIndex):
    from ils.jChart.common import getPlot

    print "Showing series: ", seriesIndex
    plot = getPlot(chart, plotIndex)
    r = plot.getRenderer(axisIndex)    
    r.setSeriesLinesVisible(seriesIndex, True)

# Remove one series from the plot.  It is generally preferred to Hide, rather than delete a series
def remove(chart, plotIndex, seriesIndex):
    from ils.jChart.common import getPlot
    
    plot = getPlot(chart, plotIndex)
    plot.getDataset().removeSeries(seriesIndex)

# Remove all series from a plot
def removeAll(chart, plotIndex):
    from ils.jChart.common import getPlot
    
    plot = getPlot(chart, plotIndex)
    plot.getDataset().removeAllSeries()