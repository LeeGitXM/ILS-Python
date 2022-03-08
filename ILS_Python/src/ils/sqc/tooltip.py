'''
Created on Jan 12, 2016

@author: ils
'''

import system
from org.jfree.chart import labels
import java.text.SimpleDateFormat as SimpleDateFormat
import java.util.Date as Date
import java.awt.geom.Ellipse2D.Double as Ellipse
from ils.common.windowUtil import getRootContainer
from ils.log import getLogger
log =getLogger(__name__)

# This class is initialized when a chart is re-configured. 
class ValueTooltipGenerator(labels.XYToolTipGenerator):
    # "root" is the enclosing Root Container.
    def __init__(self,component):
        log.tracef("Initializing the value tooltip generator...")
        self.root  = getRootContainer(component)
        self.formatter = SimpleDateFormat("MM/dd/yy HH:mm:ss")
    
    # This method is called by the chart internals in a tight loop whenever the chart is displayed.
    # Dataset interface is a jfree XYDataset.
    # Series and item are integers
    # see: com.inductiveautomation.factorypmi.application.components.chart.runtime.AutoAnnotateXYPlot$IntervalEmulatingXYDataset
    def generateToolTip(self,dataset,series,item):
#        print "Generating a tooltip for series: ", series
        html = "<html><p style='background:#f0e68c;foreground:black;'>"
        html = "<html>"
        # Value
        val = dataset.getYValue(series, item);
        html = html+"Value: %0.2f<br/>"%(val)
        
        # Sample Time
        msecs = dataset.getXValue(series,item)
        date = Date(long(msecs))
        html=html+"SampleTime: %s<br/>"%(self.formatter.format(date))

        # Grade - fetch the grade for this sample from the LtValueView table
        valueName = self.root.valueName
        SQL = "select grade from LtValueView where ValueName = '%s' and SampleTime = '%s'" % (valueName, str(self.formatter.format(date)))  
        grade = system.db.runScalarQuery(SQL)
        html=html+"Grade: %s<br/>"%(str(grade))
            
        html = html+"</p></html>"
        return html

# This class is initialized when a chart is re-configured. 
class LimitTooltipGenerator(labels.XYToolTipGenerator):
    # "root" is the enclosing Root Container.
    
    def __init__(self,component):
        log.tracef("Initializing the limit tooltip generator...")
        self.root  = getRootContainer(component)
    
    # This method is called by the chart internals in a tight loop whenever the chart is displayed.
    # Dataset interface is a jfree XYDataset.
    # Series and item are integers
    # see: com.inductiveautomation.factorypmi.application.components.chart.runtime.AutoAnnotateXYPlot$IntervalEmulatingXYDataset
    def generateToolTip(self,dataset,series,item):
        html = "<html>"
        val = dataset.getYValue(series, item);
        labels=["Target", "Limit", "Limit", "Limit", "Limit"]
        html = html+"%s: %0.2f"%(labels[series], val)
        
        return html

def setShape(renderer):
    log.tracef("Setting the renderer shape")
    renderer.setSeriesShape(0,Ellipse(-6,-6,12,12))
    renderer.setSeriesShape(1,Ellipse(-6,-6,12,12))