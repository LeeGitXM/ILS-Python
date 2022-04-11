'''
Created on Mar 8, 2022

@author: phass
'''

import system, math
from ils.log import getLogger
from ils.common.config import getDatabaseClient
from ils.common.util import formatDate, formatDateTime
log =getLogger(__name__)

# Dataset column names
START_DATE = "startDate"
INSTANCE_ID = "instanceId"
CHART_PATH = "chartPath"
RUNNING_TIME = "runningTime"
STOP_DATE = "stopDate"
STARTED_BY = "startedBy"
CHART_STATE = "chartState"

RUNNING = "Running"
STOPPED = "Stopped"

CHART_STATE_COLUMN_INDEX = 4

HEADER = [INSTANCE_ID, CHART_PATH, START_DATE, RUNNING_TIME, STOP_DATE, STARTED_BY, CHART_STATE]
CHART_STATE_COLUMN_INDEX = 4

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()", __name__)
    
def initialize(rootContainer):
    ''' Create an empty dataset.  I'm not sure how to specify the datatype of a column other than by putting actual
    values as the first row.  Then I clear the dataset.  '''
    log.infof("Initializing...")
    
    data = ["abc","def", system.date.now(), "00:00", system.date.now(), "ghi", "jkl"]
    ds = system.dataset.toDataSet(HEADER, [data])
    ds = system.dataset.clearDataset(ds)
    rootContainer.monitoredSfcs = ds
    rootContainer.unitProcedureChartName = ""
    rootContainer.unitProcedureStartTime = ""
    
def mousePressHandler(table, rowIndex, colIndex, colName, value, event):
    if rowIndex >= 0:
        viewer = table.parent.getComponent("SFC Monitor")
        ds = table.data
        instanceId = ds.getValueAt(rowIndex, 0)
        chartPath = ds.getValueAt(rowIndex, 1)
        
        ''' I keep a permanent record of the chart instances in the table, so make sure that the selected chart is still running to avoid an error.  
        By supplying the chartPath I will cut down on the runmber of returned charts, but there may still be more than one match. '''
        
        chartDs = system.sfc.getRunningCharts(chartPath)
        found = False
        for row in range(chartDs.rowCount):
            if instanceId == chartDs.getValueAt(row, 0):
                found = True

        if found:
            print "Setting: ", instanceId
            viewer.instanceId = instanceId
        else:
            viewer.instanceId = None
            system.gui.messageBox("The chart has finished and can no longer be viewed!")
    
def formatRunningTime(rt):
    secsBetween = abs(system.date.secondsBetween(system.date.now(), rt))

    hours = math.floor(secsBetween / 3600)
    mins = math.floor((secsBetween - hours * 3600) / 60)
    secs = secsBetween - (hours * 3600) - (mins * 60)
    
    runningTime = "%s:%s:%s" % (str(int(hours)).zfill(2), str(int(mins)).zfill(2), str(int(secs)).zfill(2))
    return runningTime

def fetchUnitProcedure(rootContainer):
    db = getDatabaseClient()
    startDate = system.date.addDays(system.date.now(), -1)
    SQL = "select chartPath, StartTime from SfcRunLog where StepType = 'Unit Procedure' and Status is NULL and startTime > ?"
    pds = system.db.runPrepQuery(SQL, [startDate], database=db)
    
    if len(pds) == 0 or len(pds) > 1:    
        log.tracef("Unable to find a single running unit procedure!")
        return
    
    record = pds[0]
    rootContainer.unitProcedureChartName = record[CHART_PATH]
    rootContainer.unitProcedureStartTime = formatDateTime(record["StartTime"])
    
def update(rootContainer):
    runningDataSet = system.sfc.getRunningCharts()
    if runningDataSet.rowCount == 0:
        return
    
    runningDataSet = system.dataset.sort(runningDataSet, START_DATE)
    
    if rootContainer.unitProcedureChartName == "":
        fetchUnitProcedure(rootContainer)
    
    existingDataSet = rootContainer.monitoredSfcs
    
    ''' Make a list of all of the instance ids of running charts '''
    instanceIds = []
    for row in range(existingDataSet.rowCount):
        instanceId = existingDataSet.getValueAt(row, INSTANCE_ID)
        instanceIds.append(instanceId)
    
    ''' If there are any new running charts than add them to the list, for existing charts, update the dynamic columns '''
    for row in range(runningDataSet.rowCount):
        runningInstanceId = runningDataSet.getValueAt(row, INSTANCE_ID)
        startDate = runningDataSet.getValueAt(row, START_DATE)
        if startDate == None:
            runningTime = formatRunningTime(system.date.now())
        else:
            runningTime = formatRunningTime(startDate)
        chartState = str(runningDataSet.getValueAt(row, CHART_STATE))
            
        if runningInstanceId not in instanceIds:
            log.tracef("Adding a row...")
            instanceIds.append(runningInstanceId)
            data = []
            data.append(runningInstanceId)
            data.append(runningDataSet.getValueAt(row, CHART_PATH))
            data.append(startDate)
            data.append(runningTime)
            data.append(None)
            data.append(runningDataSet.getValueAt(row, "startedBy"))
            data.append(str(chartState))
            existingDataSet = system.dataset.addRow(existingDataSet, data)

        else:
            ''' Update the dynamic values in the view dataset '''
            for row in range(existingDataSet.rowCount):
                existingInstanceId = existingDataSet.getValueAt(row, INSTANCE_ID)
                if existingInstanceId == runningInstanceId:
                    lastChartState = str(existingDataSet.getValueAt(row, CHART_STATE))
                    
                    if chartState == RUNNING:
                        existingDataSet = system.dataset.setValue(existingDataSet, row, RUNNING_TIME, runningTime)
                    
                    existingDataSet = system.dataset.setValue(existingDataSet, row, CHART_STATE, chartState)
                    
                    log.tracef("%s - %s", lastChartState, chartState)
                    if lastChartState == RUNNING and chartState != RUNNING:
                        log.tracef("Found a chart that was running and is now stopped...")
                        existingDataSet = system.dataset.setValue(existingDataSet, row, STOP_DATE, system.date.now())
                        existingDataSet = system.dataset.setValue(existingDataSet, row, RUNNING_TIME, runningTime)
    
    existingDataSet = system.dataset.sort(existingDataSet, START_DATE)
    rootContainer.monitoredSfcs = existingDataSet