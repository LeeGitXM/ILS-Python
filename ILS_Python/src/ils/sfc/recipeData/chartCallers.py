'''
Created on Dec 17, 2019

@author: phass
'''
import system
from ils.common.config import getDatabaseClient
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()", __name__) 
    db = getDatabaseClient()
    chartId = rootContainer.chartId
    
    chartPath = system.db.runScalarQuery("select chartPath from SfcChart where ChartId = %d" % (chartId), db)
    rootContainer.getComponent("Chart Path Field").text = chartPath
    
    log.tracef("Looking for callers of: %s", str(chartId))
    SQL = "Select distinct ChartPath from SfcHierarchyView where ChildChartId = %d" % (chartId)
    pds = system.db.runQuery(SQL, db)
    rootContainer.getComponent("Direct Caller List").data = pds

    log.tracef("Looking for abort handler callers of: %s", str(chartId))
    SQL = "Select distinct ChartPath from SfcHierarchyHandlerView where HandlerChartId = %d" % (chartId)
    pds = system.db.runQuery(SQL, db)
    rootContainer.getComponent("End Handler Caller List").data = pds