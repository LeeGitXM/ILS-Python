'''
Created on Aug 27, 2014

@author: ILS
'''

def getJFChart(chart):
#    jfChart=None
#    from app.scriptmodel import findJFChart
    print "Finding the J Free Chart..."
    try:
        print "Done 1"
        # return (chart.chart)
    except:
        print "Pass 1"
    try:
        for x in range(chart.componentCount):
            try:
                comp=chart.getComponent(x)
                print "Component: ", comp
                print " this component has ", comp.componentCount, " components"
                print "---"
            except:
                print "Pass 2"
    except:
        print "Pass 3"

    print "Done 2"

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