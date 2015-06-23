'''
Code related to managing info for clients that are monitoring downloads

If the Monitor Downloads step executes, a MonitoringMgr is cached in the same
scope as the timer object. Although we use s88GetScope to get the
timer scope, the MonitoringMgr is transient data--not recipe data.

Created on Jun 17, 2015
@author: rforbes
'''

# the key used to store the MonitoringMgr object:
MONITORING_MGR = '_monitoringMgr'

class MonitoringMgr:
    """Manager supporting clients listening to one set of interacting I/O steps"""
    chartScope = None
    downloadInfos = None
    downloadInfosByInputKey = None
    downloadInfosByOutputKey = None
    monitorDownloadsConfig = None
    
    def  __init__(self, _chartScope, _downloadInfos, _monitorDownloadsConfig):
        self.chartScope = _chartScope
        self.downloadInfos = _downloadInfos
        self.monitorDownloadsConfig = self._monitorDownloadsConfig
        for downloadInfo in self.downloadInfos:
            if downloadInfo.inputKey != None:
                self.downloadInfosByInputKey[downloadInfo.inputKey] = downloadInfo
            if downloadInfo.outputKey != None:
                self.downloadInfosByOutputKey[downloadInfo.ouputKey] = downloadInfo
            
    def getInfoForInput(self, inputKey):
        return self.downloadInfosByInputKey[inputKey]

    def getInfoForOutput(self, outputKey):
        return self.downloadInfosByOutputKey[outputKey]

    def sendClientUpdate(self):
        '''Send the current monitoring information to clients'''
        '''The dataset-building code should really be on the client'''
        from system.dataset import toDataSet
        from system.ils.sfc.common.Constants import DATA
        from ils.sfc.common.util import sendMessageToClient
        # These column headers must agree with the table definition in Vision
        header = ['Timing', 'DCS Tag ID', 'Setpoint', 'Description', 'Step Time', 'PV', 'setpointColor', 'stepTimeColor', 'pvColor']    
        rows = []
        # TODO: add the dummy first row with formatted timer start
        # TODO: sort by timing
        for downloadInfo in self.downloadInfos:
            rows.append(downloadInfo.createTableRow())
        dataset = toDataSet(header, rows)
        payload = dict()
        payload[DATA] = dataset
        sendMessageToClient(self.chartScope, 'sfcUpdateMonitorDownloads', payload)

    def updateClientStepTimeStatus(self, outputKey, status):
        '''Update the step time status for the given output, and update the clients'''
        downloadInfo = self.getInfoForOutput(outputKey)
        if downloadInfo == None:
            # this output is not being monitored
            return
        downloadInfo.stepTimeStatus = status    
        self.sendClientUpdate()
    
    def updateClientPVStatus(self, pv, inputKey, status):
        '''Update the PV status for the given input, and update the clients'''
        downloadInfo = self.getInfoForInput(inputKey)
        if downloadInfo == None:
            # this input is not being monitored
            return
        downloadInfo.pv = pv
        downloadInfo.pvStatus = status    
        self.sendClientUpdate()
        
class DownloadInfo:
    """Model for supporting monitoring of a single input and/or associated output"""
    timing = None
    dcsTagId = None
    setPoint = None
    description = None
    stepTime = None
    pv = None
    setpointStatus = None
    stepTimeStatus = None
    pvStatus = None
    inputKey = None
    outputKey = None
    
    def  __init__(self, _inputKey, _outputKey):
        self.inputKey = _inputKey
        self.outputKey = self._outputKey

def monitor(chartScope, stepScope, recipeLocation, config):
    from ils.sfc.gateway.recipe import RecipeData
    from system.ils.sfc.common.Constants import CLASS, STEP_TIME, PV_VALUE, VALUE

    while True:
        for row in config.rows:
        # header = ['Timing', 'DCS Tag ID', 'Setpoint', 'Description', 'Step Time', 'PV', 'setpointColor', 'stepTimeColor', 'pvColor']    
            inout = RecipeData(chartScope, stepScope, recipeLocation, row.key)
            if inout.get(CLASS) == 'Input':
                pv = inout.get(PV_VALUE)
            else:
                stepTiming = inout.get(STEP_TIME)
                setpoint = inout.get(VALUE)
       
 
def createMonitoringMgr(chartScope, stepScope, timerLocation, monitorDownloadsConfig):
    '''Create the manager and store it in the timer's scope dictionary'''
    from system.ils.sfc import s88GetScope
    downloadInfos = []
    for row in monitorDownloadsConfig.rows:
        downloadInfos.append(DownloadInfo(row.inputKey, row.outputKey))
    timerScope = s88GetScope(chartScope, stepScope, timerLocation)
    monitoringInfo = MonitoringMgr(chartScope, downloadInfos, monitorDownloadsConfig)
    timerScope[MONITORING_MGR] = monitoringInfo

def getMonitoringMgr(chartScope, stepScope, timerLocation):
    '''Get the Monitoring Mgr for a given location. If no Download GUI step has executed,
       this will return None and the caller can omit notifications'''
    from system.ils.sfc import s88GetScope
    timerScope = s88GetScope(chartScope, stepScope, timerLocation)
    return timerScope[MONITORING_MGR]
        