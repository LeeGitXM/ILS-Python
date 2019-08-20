'''
Created on Aug 16, 2019

@author: phass

This is common to the unit procedure and operation.
This updates the run log for collecting SFC KPI statistics.
'''

import system, time
from ils.common.util import formatDateTimeForDatabase
RUNNING = "Running"
STARTING = "Starting"
PAUSING = "Pausing" 
PAUSED = "Paused"
RESUMING = "Resuming"

CANCELING = "Canceling"
CANCELED = "Canceled"
ABORTING = "Aborting"
ABORTED = "Aborted"

def monitorCalledChart(runId, chartPath, db):
    '''
    This uses the system.sfc.getRunningCharts to detrermine when a chart completes.  Luckily the chart record sticks around for a minute or two after the chart completes.
    '''
    def worker(runId=runId, chartPath=chartPath, db=db):
        ''' Give the running chart structure time to get set up '''
        time.sleep(1)
        
        '''
        Assuming that we aren't starting the same chart in very quick succession which isn't really typical for
        unit procedures or operations, the data for the running chart that we just started will be the last one in the dataset.  
        Read it now, get the UUID of the running chart and then use it for the rest of the monitor.
        '''
        ds = system.sfc.getRunningCharts(chartPath)
        instanceId = ds.getValueAt(ds.getRowCount() - 1, "instanceId")

        chartState = RUNNING
        while chartState in [STARTING, RUNNING, PAUSING, PAUSED, RESUMING]:
            time.sleep(1)
            chartState = None
            ds = system.sfc.getRunningCharts(chartPath)

            for row in range(ds.getRowCount()):
                if ds.getValueAt(row, "instanceId") == instanceId:
                    chartState = str(ds.getValueAt(row, "chartState"))
            
        '''
        If we got this far then the chart is no longer running, so it either completed naturally or it was cancelled.  
        If it was cancelled, then the cancel method will have already been called.
        '''
        now = system.date.now()
        endTime = formatDateTimeForDatabase(now)
        
        if chartState in [CANCELING, CANCELED]:
            status = "Cancelled"
        elif chartState in [ABORTING, ABORTED]:
            status = "Aborted"
        else:
            status = "Success"
        
        SQL = "Update SfcRunLog set EndTime = '%s', Status = '%s' where runId = %d" % (endTime, status, runId)
        system.db.runUpdateQuery(SQL, db)
        
    system.util.invokeAsynchronous(worker)