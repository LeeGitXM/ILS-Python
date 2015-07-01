'''
Code related to managing info for clients that are monitoring downloads

If the Monitor Downloads step executes, a MonitoringMgr is created. It lives
for the lifetime of the top-level chart execution, and supports client
requests for monitoring status

Created on Jun 17, 2015
@author: rforbes
'''

class MonitoringInfo:
    '''Info to monitor one input or output object'''    
    def  __init__(self, _chartScope, _stepScope, _location, _configRow, isolationMode):
        from ils.sfc.gateway.abstractSfcIO import getIO
        from ils.sfc.gateway.recipe import RecipeData
        from system.ils.sfc.common.Constants import TAG_PATH
        self.configRow = _configRow
        self.inout = RecipeData(_chartScope, _stepScope, _location, _configRow.key)
        tagPath = self.inout.get(TAG_PATH)
        self.io = getIO(tagPath, isolationMode)


class MonitoringMgr:
    """Manager supporting clients associated with the same MonitorDownloads step"""
            
    def  __init__(self, _chartScope, _stepScope, _recipeLocation, _config, _timer, _timerAttribute, _logger):
        from ils.sfc.common.util import getIsolationMode
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
        DOWNLOAD_STATUS, STEP_TIME, STEP_TIMESTAMP, TIMING, DESCRIPTION, SUCCESS, \
        WRITE_CONFIRMED, FAILURE, PENDING

        import ils.sfc.gateway.abstractSfcIO as abstractSfcIO
        from ils.sfc.common.util import sendMessageToClient, formatTime, getTopChartRunId
        from ils.sfc.common.constants import INSTANCE_ID
        from java.awt import Color
        import time
        # the meaning of the columns:
        #header = ['Timing', 'DCS Tag ID', 'Setpoint', 'Description', 'Step Time', 'PV', 'setpointColor', 'stepTimeColor', 'pvColor']    
        timerStart = self.getTimerStart()
        formattedStart = formatTime(timerStart)
        rows = []
        rows.append(['', '', '', '', formattedStart, '', Color.white, Color.white, Color.white])
        for info in self.monitoringInfos:
            dataType = info.inout.get(CLASS)
            if dataType == 'Output':
                downloadStatus = info.inout.get(DOWNLOAD_STATUS)
                writeConfirmed = info.inout.get(WRITE_CONFIRMED)
                timing = info.inout.get(TIMING)
                if timing < 1000.:
                    formattedTiming = "%.2f" % timing
                else:
                    formattedTiming = ''
                # STEP_TIME and STEP_TIMESTAMP are ABSOLUTE time values written by the 
                # WriteOutput step that reflect the offset from the actual timer start time
                stepTime = info.inout.get(STEP_TIME) 
                stepTimestamp = info.inout.get(STEP_TIMESTAMP) # empty string for event-driven steps
                description = info.inout.get(DESCRIPTION)
                setpoint = info.io.get(abstractSfcIO.SETPOINT)
                formattedSetpoint = "%.2f" % setpoint
                name = info.io.get(info.configRow.labelAttribute)
                #TODO: convert to units if GUI units specified
                
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
                setpointColor = Color.white # don't know anything about target               
                pvColor = Color.white # don't know anything about target    
                rows.append([formattedTiming, name, formattedSetpoint, description, stepTimestamp, '', setpointColor, stepTimeColor, pvColor])
            else: # input
                pass
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
    from ils.sfc.common.util import getTopChartRunId

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
        