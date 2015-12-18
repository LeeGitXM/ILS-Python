'''
Created on Aug 27, 2014

@author: ILS
'''
# Utilities for charts using XYSeriesCollection as the dataset

# Initialize a plot (clears any existing datasets)
def initPlot(jfchart, plotIndex):
    from org.jfree.data.xy import XYSeriesCollection
    from org.jfree.chart.renderer.xy import XYLineAndShapeRenderer
    from ils.jChart.common import getPlot
    
    print "Initializing plot ", plotIndex
    plot = getPlot(jfchart, plotIndex)
    plot.setRenderer(XYLineAndShapeRenderer())
    
    # This is a little bit of a hack - I'm not sure how many axis there actually are, there probably won't be more than 10
    # and this is a pretty fast operation (I think)
    for axisIndex in range(0,10):
        plot.setDataset(axisIndex,XYSeriesCollection())

# Create JFreeChart XYSeries object(s) from an Ignition dataset
def addSeriesFromIgDataset(chart, plotIndex, axisIndex, key, igDataset):
    from org.jfree.data.xy import XYSeries
    from ils.jChart.common import getPlot

    print "---------------\nAdding series"
    print "Ignition dataset: ", igDataset
    print "            plot: ", plotIndex
    print "            axis: ", axisIndex
    print "             Key: ", key
    # create series using names from igDataset header:
    xySeries = range(igDataset.columnCount)
    
    for col in range(1, igDataset.columnCount):
        colName = key
        xySeries.insert(col, XYSeries(colName))
        print "Inserting column ", colName

    # Transfer the data points:
    for row in range(igDataset.rowCount):
        x = igDataset.getValueAt(row, 0)
        
        for col in range(1, igDataset.columnCount):
            y = igDataset.getValueAt(row, col)
            xySeries[col].add(x, y)

    # Add the new jF datasets to the plot
    plot = getPlot(chart, plotIndex)
    for col in range(1, igDataset.columnCount):
#        print "Adding Dataset: ", plot.getDataset().getClass().getName()
        plot.getDataset(axisIndex).addSeries(xySeries[col])

# Add a single x,y data point to an existing series
def addPointToSeries(chart, plotIndex, seriesIndex, x, y):
    from ils.jChart.common import getPlot
    
    plot = getPlot(chart, plotIndex)
    plot.getDataset().getSeries(seriesIndex).add(x,y)