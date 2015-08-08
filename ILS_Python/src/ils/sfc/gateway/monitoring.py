'''
Code related to managing info for clients that are monitoring downloads

If the Monitor Downloads step executes, a MonitoringMgr is created. It lives
for the lifetime of the top-level chart execution, and supports client
requests for monitoring status

see the G2 procedures S88-RECIPE-INPUT-DATA__S88-MONITOR-PV.txt and S88-RECIPE-OUTPUT-DATA__S88-MONITOR-PV.txt

Created on Jun 17, 2015
@author: rforbes
'''

class MonitoringInfo:
    '''Info to monitor one input or output object'''    
    def  __init__(self, _chartScope, _stepScope, _location, _configRow, isolationMode):
        from ils.sfc.gateway.abstractSfcIO import AbstractSfcIO
        from ils.sfc.gateway.recipe import RecipeData
        from system.ils.sfc.common.Constants import TAG_PATH 
        self.configRow = _configRow
        self.inout = RecipeData(_chartScope, _stepScope, _location, _configRow.key)
        tagPath = self.inout.get(TAG_PATH)
        self.io = AbstractSfcIO.getIO(tagPath, isolationMode)


class MonitoringMgr:
    """Manager supporting clients associated with the same MonitorDownloads step"""
            
    def  __init__(self, _chartScope, _stepScope, _recipeLocation, _config, _timer, _timerAttribute, _logger):
        from ils.sfc.gateway.api import getIsolationMode
        self.chartScope = _chartScope
        self.config = _config
        self.timer = _timer
        self.timerAttribute = _timerAttribute
        self.logger =_logger
        self.monitoringInfos = []
        
        isolationMode = getIsolationMode(_chartScope)

        for row in _config.rows:
            self.monitoringInfos.append(MonitoringInfo(_chartScope, _stepScope, _recipeLocation, row, isolationMode))
            #key, labelAttribute, units
    
    def getTimerId(self):
        from system.ils.sfc.common.Constants import DATA_ID
        return self.timer.get(DATA_ID)
        
    def getTimerStart(self):
        return self.timer.get(self.timerAttribute)
        
    def sendClientUpdate(self):
        '''Send the current monitoring information to clients'''
        '''The dataset-building code should really be on the client'''
        from system.ils.sfc.common.Constants import DATA, DATA_ID, TIME, CLASS, \
        DOWNLOAD_STATUS, STEP_TIME, STEP_TIMESTAMP, TIMING, DESCRIPTION, \
        FAILURE, PENDING, VALUE, PV_MONITOR_STATUS, PV_MONITOR_ACTIVE, \
        SUCCESS, WARNING, MONITORING, NOT_PERSISTENT, NOT_CONSISTENT, ERROR, TIMEOUT

        from ils.sfc.gateway.abstractSfcIO import AbstractSfcIO
        from ils.sfc.gateway.util import getTopChartRunId
        from ils.sfc.common.util import formatTime
        from ils.sfc.gateway.api import  sendMessageToClient
        from ils.sfc.common.constants import INSTANCE_ID, UNITS
        from java.awt import Color
        import time
        # the meaning of the columns:
        #header = ['Timing', 'DCS Tag ID', 'Setpoint', 'Description', 'Step Time', 'PV', 'setpointColor', 'stepTimeColor', 'pvColor']    
        timerStart = self.getTimerStart()
        formattedStart = formatTime(timerStart)
        rows = []
        rows.append(['', '', '', '', formattedStart, '', Color.white, Color.white, Color.white])
        for info in self.monitoringInfos:
            # Note: the data can be an Input or an Output, which are both subclasses of IO
            # oddly enough, Inputs do not have any additional attributes vs IO
            # get common IO attributes and set some defaults:
            description = info.inout.get(DESCRIPTION)
            pv = info.io.getCurrentValue()
            monitorActive = info.inout.get(PV_MONITOR_ACTIVE)
            if monitorActive == True:
                formattedPV = "%.2f" % pv
            else:
                formattedPV = "%.2f*" % pv
            name = info.io.get(info.configRow.labelAttribute)
            units = info.inout.get(UNITS)
            #TODO: convert to units if GUI units specified
            setpointColor = Color.white
            stepTimeColor = Color.white
            pvColor = Color.white
            dataType = info.inout.get(CLASS)
            if dataType == 'Output':
                downloadStatus = info.inout.get(DOWNLOAD_STATUS)
                timing = info.inout.get(TIMING)
                if timing < 1000.:
                    formattedTiming = "%.2f" % timing
                else:
                    formattedTiming = ''
                # STEP_TIME and STEP_TIMESTAMP are ABSOLUTE time values written by the 
                # WriteOutput step that reflect the offset from the actual timer start time
                stepTime = info.inout.get(STEP_TIME) 
                stepTimestamp = info.inout.get(STEP_TIMESTAMP) # empty string for event-driven steps
                # note: we want to reflect the setpoint that WILL be written, even if
                # the current actual setpoint is different
                # ?? not using the WRITE_CONFIRMED value in recipe data
                setpoint = info.inout.get(VALUE)
                formattedSetpoint = "%.2f" % setpoint
                timeNow = time.time()
                if stepTime != None and timeNow < stepTime:
                    pendingTime = stepTime - 30
                    if timeNow < pendingTime:
                        stepTimeColor = Color.white
                    else:
                        stepTimeColor = Color.yellow
                else:
                    if downloadStatus == None:
                        stepTimeColor = Color.white
                    elif downloadStatus == PENDING:
                        stepTimeColor = Color.orange
                    elif downloadStatus == SUCCESS:
                        stepTimeColor = Color.green
                    elif downloadStatus == FAILURE:
                        stepTimeColor = Color.red
            else:
                formattedTiming = ''
                stepTimestamp = ''
                # an Input knows nothing about step timing, so step timing fields are blank
                # we know nothing about pending setpoints, but can at least reflect the current one:
                setpoint = info.io.getSetpoint()
                formattedSetpoint = "%.2f" % setpoint
                
            monitorStatus = info.inout.get(PV_MONITOR_STATUS)
            # reference S88-PV-MONITOR-STATUS-COLOR-DECODER.txt
            # SUCCESS, WARNING, MONITORING, NOT_PERSISTENT, NOT_CONSISTENT, OUT_OF_RANGE, ERROR, TIMEOUT
            if monitorStatus == MONITORING or  monitorStatus == None:
                pvColor = Color.white
            elif monitorStatus == WARNING:    
                pvColor = Color.yellow
            elif monitorStatus == NOT_PERSISTENT:    
                pvColor = Color(154,205,50)
            elif monitorStatus == SUCCESS:    
                pvColor = Color.green
            elif monitorStatus == NOT_CONSISTENT:    
                pvColor = Color.orange
            elif monitorStatus == ERROR or monitorStatus == TIMEOUT: 
                # print 'monitoring: status is', monitorStatus   
                pvColor = Color.red
            if pvColor == Color.red or stepTimeColor == Color.red:
                setpointColor = Color.yellow
            else:
                setpointColor = Color.white
            rows.append([formattedTiming, name, formattedSetpoint, description, stepTimestamp, formattedPV, setpointColor, stepTimeColor, pvColor])
               

        # TODO: sort by timing
         
        payload = dict()
        payload[TIME] = timerStart
        payload[INSTANCE_ID] = getTopChartRunId(self.chartScope)
        payload[DATA_ID] = self.getTimerId()
        payload[DATA] = rows
        sendMessageToClient(self.chartScope, 'sfcUpdateDownloads', payload) 
 
def createMonitoringMgr(chartScope, stepScope, recipeLocation, timer, timerAttribute, monitorDownloadsConfig, logger):
    '''Create the manager and store it in the dropbox. When the top-level chart 
    finishes, the dropbox will automatically delete the manager'''
    from system.ils.sfc import dropboxPut
    from ils.sfc.gateway.util import getTopChartRunId

    mgr = MonitoringMgr(chartScope, stepScope, recipeLocation, monitorDownloadsConfig, timer, timerAttribute, logger)
    topChartRunId = getTopChartRunId(chartScope)
    dropboxPut(topChartRunId, mgr.getTimerId(), mgr)
    return mgr

def getMonitoringMgr(chartRunId, timerId):
    '''Get the given Monitoring Mgr for the given timer. If None is returned, the top-level 
    chart execution has ended'''
    from system.ils.sfc import dropboxGet
    mgr = dropboxGet(chartRunId, timerId)
    return mgr
        