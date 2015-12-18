'''
Created on Aug 27, 2014

@author: ILS
'''
#
# These are close to working but aren't quite there.  I eliminated the need for this by adding two 
# charts to the root container, one single and one stacked.
# I'm going to leave this here in case we ever want to use it, but it needs a little more polishing.
#

# Initialize a plot (clears any existing datasets)
def add(chart):
    from ils.BatchExpert.jChart.common import getPlot
    
    print "Adding a plot"
    plotIndex = 0
    weight = 1

    # Get a subplot, which we will add back to the plot container
    subPlot = getPlot(chart, plotIndex)

    # Get the container / list of plat that are inside the jChart
    combinedPlot = chart.getChart().getPlot()

    combinedPlot.add(subPlot, weight)


# This seems to work on one of the original subplots, but seems to throw an error if I try to remove 
# a dataset that I added.
def remove(chart, plotIndex):
    from ils.BatchExpert.jChart.common import getPlot

    subPlot = getPlot(chart, plotIndex)
    combinedPlot = chart.getChart().getPlot()
    combinedPlot.remove(subPlot)
    print "Removed"