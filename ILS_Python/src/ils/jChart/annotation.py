'''
Created on Aug 27, 2014

@author: ILS  
'''

from ils.jChart.common import getJFChart, getPlot
from org.jfree.chart.annotations import XYTextAnnotation, XYPointerAnnotation

def clear(chart, plotIndex=0):
    jFChart = getJFChart(chart)
    plot = getPlot(jFChart, plotIndex)
    plot.clearAnnotations()
    

def add(chart, txt, x, y, plotIndex=0):
    jFChart = getJFChart(chart)
    plot = getPlot(jFChart, plotIndex)    
    plot.addAnnotation(XYTextAnnotation(txt, x, y))


def addPointer(chart, txt, x, y, plotIndex=0):
    jFChart = getJFChart(chart)
    plot = getPlot(jFChart, plotIndex)
        
    # An "X" is a poor man's shape.  The center of the X appears at the exact coordinate
    plot.addAnnotation(XYTextAnnotation("X", x, y))    
    plot.addAnnotation(XYPointerAnnotation(txt, x, y, 45.0))


# This adds a filled shape and should add a hollow shape.  Also need to scale the X and Y so that this draws a 
# circle and not an ellipse.  This doesn't quite work, it adds a shape, but it isn't hollow (open)
def addOpenShape(chart, x, y, plotIndex=0):
    from org.jfree.chart.annotations import XYShapeAnnotation
    from java.awt.geom import Ellipse2D
    from java.awt import BasicStroke
    from java.awt import Color
    
    jFChart = getJFChart(chart)
    plot = getPlot(jFChart, plotIndex)
    
    stroke = BasicStroke(1)
    circle = Ellipse2D.Float(x, y, 0.01, 2)
    annotation = XYShapeAnnotation(circle, stroke, Color.GREEN, Color.GREEN)
    plot.addAnnotation(annotation)

# See comments above.
def addFilledShape(chart, x, y, plotIndex=0):
    from org.jfree.chart.annotations import XYShapeAnnotation
    from java.awt.geom import Ellipse2D
    from java.awt import BasicStroke
    from java.awt import Color

    jFChart = getJFChart(chart)
    plot = getPlot(jFChart, plotIndex)
    
    stroke = BasicStroke(3)
    circle = Ellipse2D.Float(x, y, 0.01, 2)
    annotation = XYShapeAnnotation(circle, stroke, Color.GREEN, Color.GREEN)
    plot.addAnnotation(annotation)


