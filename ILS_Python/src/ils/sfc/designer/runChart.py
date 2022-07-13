'''
Created on Apr 29, 2022

@author: ils
'''

import system
from ils.sfc.recipeData.api import s88GetEnclosingCharts
from ils.common.config import getIsolationDatabaseFromInternalDatabase, getIsolationTagProviderFromInternalDatabase, getIsolationTimeFactorFromInternalDatabase, \
    getProductionDatabaseFromInternalDatabase, getProductionTagProviderFromInternalDatabase, getProductionTimeFactorFromInternalDatabase
from ils.sfc.common.constants import INSTANCE_ID
from ils.queue.commons import getQueueId, createQueue
from ils.log import getLogger
log = getLogger(__name__)

def run(chartPath, isolationMode):
    '''
    This is called from a menu choice in the Designer (via a callback in Java).
    There are two menu choices, one for Isolation Mode and one for Production Mode.
    '''
    log.infof("In %s.run() with chart: %s - isolation mode: %s", __name__, chartPath, str(isolationMode))
    projectName = system.util.getProjectName()
    payload = getChartParameters(chartPath, isolationMode, projectName)
    chartRunId = system.sfc.startChart(projectName, chartPath, payload)
    return chartRunId 

def getChartParameters(chartPath, isolationMode, projectName):
    '''
    Use the chart hierarchy stored in the database to mock up the call stack that is passed in 
    as the chart dictionary to the selected chart.  The reason for doing this is to set the Time
    Factor, tag provider, database provider and the superior chart structure so that recipe data at the
    higher scopes will all be intact.  Note that for a chart that has multiple parents it is indeterminater which 
    parent will be chosen.  
    '''
    def getEnclosingStep(lastStepName, lastS88Level):
        enclosingStep = {}
        enclosingStep['name'] = lastStepName
        enclosingStep['runningTime'] = 0.0
        if lastS88Level != None:
            enclosingStep['s88Level'] = lastS88Level
        return enclosingStep

    log.infof("In %s.getChartParameters", __name__)

    if isolationMode:
        tagProvider = getIsolationTagProviderFromInternalDatabase(projectName)
        database = getIsolationDatabaseFromInternalDatabase(projectName)
        timeFactor = getIsolationTimeFactorFromInternalDatabase(projectName)
    else:
        tagProvider = getProductionTagProviderFromInternalDatabase(projectName)
        database = getProductionDatabaseFromInternalDatabase(projectName)
        timeFactor = getProductionTimeFactorFromInternalDatabase(projectName)

    controlPanelName = "Designer"
    from ils.sfc.client.windows.controlPanel import createControlPanel, getControlPanelIdForName
    controlPanelId = getControlPanelIdForName(controlPanelName, database)
    if controlPanelId == None:
        controlPanelId = createControlPanel(controlPanelName, database)

    msgQueueName = "SFC"
    queueId = getQueueId(msgQueueName)
    if queueId == None:
        queueId = createQueue(msgQueueName)

    lastChartParameters = {}
    lastStepName = ""
    lastS88Level = ""
    enclosingCharts = s88GetEnclosingCharts(chartPath)
    log.infof("Fetched %d enclosing steps", enclosingCharts.rowCount)

    row = 0
    for idx in range(enclosingCharts.rowCount - 1, -1, -1):
        log.tracef("Row: %d (idx = %d)", row, idx)
        txt = []
        for attr in ["chartPath", "stepName", "stepUUID", "stepType", "factoryId"]:
            txt.append("%s: %s" % (attr, enclosingCharts.getValueAt(idx, attr)))
        log.tracef("%s", ", ".join(txt))
        
        stepType = enclosingCharts.getValueAt(idx, "stepType")
        if stepType == "Unit Procedure":
            s88Level = "global"
        elif stepType == "Operation":
            s88Level = "operation"
        elif stepType == "Phase":
            s88Level = "phase"
        else:
            s88Level = None
        
        chartParameters = {}
        activeSteps = {'fakeUUID': {'name': enclosingCharts.getValueAt(idx, 'stepName')}}    # I don't think anything I do cares about this
        if row == 0:
            chartParameters['controlParameterId'] = controlPanelId
            chartParameters['project'] = projectName
            chartParameters['originator'] = system.security.getUsername()
            chartParameters['tagProvider'] = tagProvider
            chartParameters['database'] = database
            chartParameters['timeFactor'] = float(timeFactor)
            chartParameters['msgQueue'] = msgQueueName
            chartParameters['activeSteps'] = activeSteps
            chartParameters['chartPath'] = enclosingCharts.getValueAt(idx, "chartPath")
            chartParameters[INSTANCE_ID] = 'mockId'
            
        else:
            chartParameters['parent'] = lastChartParameters
            chartParameters['activeSteps'] = activeSteps
            chartParameters['chartPath'] = enclosingCharts.getValueAt(idx, "chartPath")
            chartParameters['enclosingStep'] = getEnclosingStep(lastStepName, lastS88Level)
        
        lastS88Level = s88Level
        lastStepName = enclosingCharts.getValueAt(idx, "stepName")
        lastChartParameters = chartParameters
        row = row + 1
    
    chartParameters = {}
    chartParameters['parent'] = lastChartParameters
    chartParameters['enclosingStep'] = getEnclosingStep(lastStepName, lastS88Level)
            
    log.tracef("Returning: %s", str(chartParameters))
    return chartParameters