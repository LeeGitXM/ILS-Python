'''
Created on Sep 29, 2020

@author: phass
'''

def configureChart(chart, jChart):
    from org.jfree.chart.annotations import XYTextAnnotation
    from ils.jChart.common import getPlot

    print "In %s.configureChart" % (__name__)
    #plot = getPlot(chart, plotIndex)    
    #plot.addAnnotation(XYTextAnnotation(txt, x, y))


from org.jfree.chart.annotations import AbstractXYItemRenderer 
class myRenderer ():
     
    def __init__(self,path):
        print "Initializing a new renderer!"
