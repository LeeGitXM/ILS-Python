'''
Created on May 12, 2022

@author: ils
'''

from java.awt import Color
from java.awt import GradientPaint
from java.awt.geom import GeneralPath
from java.awt.geom import Rectangle2D
from java.awt.geom import Ellipse2D
from java.awt.font import TextAttribute

from ils.log import getLogger
log = getLogger(__name__)

from ils.graph.directedGraph import DirectedGraph

def simpleDraw(event):
    print "In simpleDraw()"

    borderColor = Color.BLACK
    textColor = Color.BLACK
    readyColor = Color.WHITE
    ranColor = Color.GREEN
    
    RAN = "Ran"
    READY = "Ready"
    
    radius = 15
    textHeightOffset = 6     # Used for estimating where the text should be placed
    textWidthOffset = 2
    
    g = event.graphics
    g.setColor(Color.GRAY)
    
    milestones = []
    milestones.append([100, 40, "Wash", RAN])
    milestones.append([100, 100, "Fill", RAN])
    milestones.append([100, 160, "Heat", READY])
    milestones.append([100, 220, "  Rx", READY])
    milestones.append([100, 280, "Flush", READY])
    
    lastX = None
    lastY = None
    
    ''' If I draw the arcs first then I can draw from center to center and the shpes will be on top of the lines '''
    for milestone in milestones:
        x = milestone[0]
        y = milestone[1]

        ''' Connect the previous bubble to the current one '''
        if lastX != None:
            line = GeneralPath()
            line.moveTo(lastX,lastY)
            line.lineTo(x,y)
            line.closePath()
            g.draw(line)
        
        lastX = x
        lastY = y
        
    ''' Draw the milestones '''
    for milestone in milestones:
        x = milestone[0]
        y = milestone[1]
        label = milestone[2]
        state = milestone[3]
        
        bubble = Ellipse2D.Float(x - radius, y - radius, radius * 2.0, radius * 2.0)
        
        if state == RAN:
            g.setColor(ranColor)
        else:
            g.setColor(readyColor)
        g.fill(bubble)
        
        g.setColor(borderColor)
        g.draw(bubble)
        
        g.setColor(textColor)
        g.drawString(label, x - radius + textWidthOffset, y + textHeightOffset)

def graph1(event):
    paths = []
    paths.append(["a", "b", "d", "e", "f"])
    #drawGraph(event, paths)
    graph = DirectedGraph(event, paths)
    
def graph2(event):
    paths = []
    paths.append(["a", "b", "d", "e"])
    paths.append(["a", "c", "e"])
    #drawGraph(event, paths)
    graph = DirectedGraph(event, paths)
    
def graph3(event):
    paths = []
    paths.append(["a", "b", "c", "e", "i", "j"])
    paths.append(["a", "b", "d", "f", "g", "h", "i", "j"])
    paths.append(["a", "b", "h", "i", "j"])
    graph = DirectedGraph(event, paths)
    #drawGraph(event, paths)
    
def drawGraph(event, paths):
    log.infof("In %s.drawGraph with %s", __name__, str(paths))
    
    ''' The first step is to determine the depth and width of the graph. '''
    
    width = len(paths)
    depth = 0
    for path in paths:
        if len(path) > depth:
            depth = len(path)
    
    log.infof("Graph depth: %d, width: %d", depth, width)

    nodes = getNodes(paths)