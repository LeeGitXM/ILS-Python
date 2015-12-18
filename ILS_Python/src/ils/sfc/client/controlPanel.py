'''
Created on Dec 9, 2015

@author: rforbes
'''
from system.gui import getParentWindow
from ils.sfc.client.windowUtil import getRootContainer

def startChart(event):
    from ils.sfc.common.constants import PROJECT, ISOLATION_MODE, CONTROL_PANEL_ID
    import system.util, system.sfc, system.db, system.gui, system.security, system.tag
    rootContainer = getRootContainer(event)
    cpId = rootContainer.controlPanelId
    data = rootContainer.windowData
    #numUpdated = system.db.runUpdateQuery("Update SfcControlPanel set status = 'Locked' where id = %d and status is null" % (cpId));
    #if numUpdated == 1:
    canStart = True
    if canStart:
        chartPath = data.getValueAt(0,'chartPath')
        project = system.util.getProjectName()
        isolationMode = system.tag.read('[Client]/Isolation Mode')
        initialChartParams = dict()
        initialChartParams[PROJECT] = project
        initialChartParams[ISOLATION_MODE] = isolationMode.value
        initialChartParams[CONTROL_PANEL_ID] = cpId
        runId = system.sfc.startChart(chartPath, initialChartParams)
        originator = system.security.getUsername()
        project = system.util.getProjectName
        if isolationMode:
            isolationFlag = 1
        else:
            isolationFlag = 0
        numUpdated = system.db.runUpdateQuery("Update SfcControlPanel set chartRunId = '%s', originator = '%s', project = '%s', isolationMode = %d where controlPanelId = %d" % (runId, originator, project, cpId, isolationFlag));
    else:
        system.gui.warningBox('Chart already running')

def pauseChart(event):
    from system.sfc import pauseChart
    pauseChart(getParentWindow(event).rootContainer.chartRunId)

def resumeChart(event):
    from system.sfc import resumeChart
    resumeChart(getParentWindow(event).rootContainer.chartRunId)

def cancelChart(event):
    from system.sfc import cancelChart
    cancelChart(getParentWindow(event).rootContainer.chartRunId)
       
def getChartStatus(event):
    '''Get the status of this panel's chart run and set the status field appropriately.
       Will show None if the chart is not running.'''
    from ils.sfc.client.util import getChartStatus
    rootContainer = getRootContainer(event)
    statusField = rootContainer.getComponent('statusLabel')
    runId = rootContainer.windowData.getValueAt(0,'chartRunId')
    status = getChartStatus(runId)
    statusField.text = status
