'''
Created on May 13, 2022

@author: ils
'''

from ils.log import getLogger
from compiler.ast import Node


class DirectedGraph():
    event = None
    log = None
    paths = []
    nodes = []
    OPC_LATENCY_TIME = None
    
    def __init__(self, event, paths):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        self.log = getLogger(__name__)
        self.log.infof("In %s.DirectedGraph constructor with %s", __name__, str(paths))
        self.paths = paths
        self.event = event
        self.draw()

    def draw(self):
        self.log.infof("In draw()")
        
        ''' The first step is to determine the depth and width of the graph. '''
        self.calcChartDimensions()
        self.getNodes()
        #self.calcNodeLocations()
        
    def calcChartDimensions(self):
        self.width = len(self.paths)
        self.depth = 0
        for path in self.paths:
            if len(path) > self.depth:
                self.depth = len(path)
        self.log.infof("Graph depth: %d, width: %d", self.depth, self.width)
    
    def getNodes(self):
        ''' Make a list of unique nodes '''
        nodeList = []
        nodes = []
        for path in self.paths:
            for node in path:
                if node not in nodeList:
                    nodeList.append(node)
                    nodes.append({"name":node, "x": 0, "y": 0})
        self.nodes = nodes
        self.log.infof("The list of nodes is: %s", str(self.nodes))
    
    def calcNodeLocations(self):
        i = 0
        for node in self.nodes:
            maxY = 0
            i = i + 1
            for path in self.paths:
                j = 0;
                for aNode in path:
                    j = j + 1
                    if aNode["name"] == Node:
                        if j > maxY:
                            maxY = j
                            x = i 
            node["y"] = maxY 
            node["x"] = x
        self.log.infof("The updated node list is: %s", self.nodes)    
        