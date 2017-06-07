'''
Created on May 31, 2017

@author: phass
'''

def exportrCallback(event):
    treeWidget = event.source.parent.getcomment("Tree View")
    
def exportTree(parentChartPath):
    print "Exporting: ", parentChartPath
    
def exportChart(chartPath):
    print "Exporting ", chartPath