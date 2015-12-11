'''
Created on Aug 27, 2014

@author: ILS  
'''

def add(chart, plotIndex, txt, x, y):
    from org.jfree.chart.annotations import XYTextAnnotation
    from ils.jChart.common import getPlot

    plot = getPlot(chart, plotIndex)    
    plot.addAnnotation(XYTextAnnotation(txt, x, y))


def addPointer(chart, plotIndex, txt, x, y):
    from org.jfree.chart.annotations import XYPointerAnnotation
    from org.jfree.chart.annotations import XYTextAnnotation
    from ils.jChart.common import getPlot
            
    plot = getPlot(chart, plotIndex)
        
    # An "X" is a poor man's shape.  The center of the X appears at the exact coordinate
    plot.addAnnotation(XYTextAnnotation("X", x, y))    
    plot.addAnnotation(XYPointerAnnotation(txt, x, y, 45.0))


# This adds a filled shape and should add a hollow shape.  Also need to scale the X and Y so that this draws a 
# circle and not an ellipse.
def addOpenShape(chart, plotIndex, x, y):
    from org.jfree.chart.annotations import XYShapeAnnotation
    from java.awt.geom import Ellipse2D
    from java.awt import BasicStroke
    from java.awt import Color
    from ils.jChart.common import getPlot
    
    plot = getPlot(chart, plotIndex)
    
    stroke = BasicStroke(3)
    circle = Ellipse2D.Float(x, y, 0.01, 2)
    annotation = XYShapeAnnotation(circle, stroke, Color.GREEN, Color.GREEN)
    plot.addAnnotation(annotation)

# See comments above.
def addFilledShape(chart, plotIndex, x, y):
    from org.jfree.chart.annotations import XYShapeAnnotation
    from java.awt.geom import Ellipse2D
    from java.awt import BasicStroke
    from java.awt import Color
    from ils.jChart.common import getPlot

    plot = getPlot(chart, plotIndex)
    
    stroke = BasicStroke(3)
    circle = Ellipse2D.Float(x, y, 0.01, 2)
    annotation = XYShapeAnnotation(circle, stroke, Color.GREEN, Color.GREEN)
    plot.addAnnotation(annotation)


def clear(chart, plotIndex):
    from ils.jChart.common import getPlot

    plot = getPlot(chart, plotIndex)
    plot.clearAnnotations()