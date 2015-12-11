'''
Created on Aug 27, 2014

@author: ILS
'''
# Return the request plot from a stacked plot or the single plot
def getPlot(jfchart, plotIndex):
    plot = jfchart.getPlot()
    
    # If this is a stacked chart then get the subplot
    plotClass = "%s" % (str(plot))

    if plotClass.find("CombinedDomainXYPlot") > 0:
        print "...getting the subplot..." 
        subplotList = plot.getSubplots()
        plot = subplotList[plotIndex]

#    print "--> Using plot ", plot
    return plot

# Convert a java color into a comma delimiter string of its RGB values
def colorString(theColor):

    red = theColor.getRed()
    green = theColor.getGreen()
    blue = theColor.getBlue()

    colorString = "%i,%i,%i" % (red,green,blue)
    return colorString