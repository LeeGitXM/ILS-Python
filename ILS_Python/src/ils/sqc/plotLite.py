'''
Created on Jan 4, 2019

@author: phass
'''

import system
from ils.common.config import getDatabaseClient
from ils.sqc.plot import configureChartSQCLimit
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()", __name__)
    db = getDatabaseClient()
    configureChart(rootContainer, db)

def internalFrameActivated(rootContainer):
    log.infof("In %s.internalFrameActivated()", __name__)
    
def configureChart(rootContainer, db):
    log.tracef("In %s.configureChart()...", __name__)
    
    db = getDatabaseClient()
    
    lowerLimit = rootContainer.lowerLimit
    upperLimit = rootContainer.upperLimit
    target = rootContainer.target
    
    log.tracef("Upper limit: %f", upperLimit)
    log.tracef("Target:      %f", target)
    log.tracef("Lower limit: %f", lowerLimit)

    configureChartSQCLimit(rootContainer, "upperLimit", upperLimit)
    configureChartSQCLimit(rootContainer, "lowerLimit", lowerLimit)
    configureChartSQCLimit(rootContainer, "target", target)

    rootContainer.yAxisAutoScaling=True
    
    # Configure the where clause of the database pens which should drive the update of the chart
    ds = rootContainer.labValueNames
    for row in range(ds.getRowCount()):
        log.tracef("Row: %d", row)
        unitName = ds.getValueAt(row, "UnitName")
        labValueName = ds.getValueAt(row, "ValueName")
        log.tracef("%s - %s", unitName, labValueName)
        configureChartValuePen(rootContainer, row, unitName, labValueName, db)
        
    log.tracef("...done with %s.configureChart()!", __name__)
    

def configureChartValuePen(rootContainer, pen, unitName, labValueName, db):
    '''
    This sets the where clause of the two DB pens, that stor ethe actual data values.  It also sets the colors of the pens from the 
    configuration tags..    
    '''
    log.tracef("...configuring the where clause of the value pens for %s...", labValueName)
    
    chart=rootContainer.getComponent("Plot Container").getComponent('Easy Chart')
    ds = chart.pens
    
    # Set the datasource (production or isolation)
    ds = system.dataset.setValue(ds, pen, "DATASOURCE", db)
    
    #TODO This shouldn't be hard-coded
    endTime = system.date.now()
    startTime = system.date.addDays(endTime, -2)
    
    endTimeTxt = system.db.dateFormat(endTime, "yyyy-MM-dd H:mm:ss")
    startTimeTxt = system.db.dateFormat(startTime, "yyyy-MM-dd H:mm:ss")
    
    whereClause = "UnitName = '%s' and ValueName = '%s' and SampleTime > '%s'" % (unitName, labValueName, startTimeTxt)
    log.tracef("  ...setting the where clause of pen %d to %s", pen, whereClause)
    ds = system.dataset.setValue(ds, pen, "WHERE_CLAUSE", whereClause)
    chart.pens = ds    


def configureChartExtensionFunction(self, chart):
    log.tracef("In %s.configureChartExtensionFunction()...", __name__)

    import ils.sqc.tooltip as tt
    # Plot is an AutoAnnotateXYPlot. Have verified it is not a subplot.
    plot = chart.getXYPlot()
    
    '''
    It appears that there is no special order to the datasets.
    However once the pen collection is static, they seem to stay constant.
    '''
    count = chart.getXYPlot().getDatasetCount()
    log.tracef( "Dataset count: (%d)", count)
    
    series = 0
    for index in range(count):
        xyds = plot.getDataset(index)
        seriesCount = xyds.getSeriesCount()
        log.tracef("Dataset %d: %d series", index, seriesCount)
        if index == 0:
            renderer = plot.getRendererForDataset(xyds)
            customGenerator = tt.LimitTooltipGenerator(self)
            renderer.setToolTipGenerator(customGenerator)
            series = series+seriesCount
        elif index == 1:
            renderer = plot.getRendererForDataset(xyds)
            customGenerator = tt.ValueTooltipGenerator(self)
            renderer.setToolTipGenerator(customGenerator)
            series = series+seriesCount

    log.tracef("...done with %s.configureChartExtensionFunction()!", __name__)