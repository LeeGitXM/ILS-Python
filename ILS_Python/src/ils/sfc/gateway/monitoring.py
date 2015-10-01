'''
Code related to managing info for clients that are monitoring downloads

If the Monitor Downloads step executes, a MonitoringMgr is created. It lives
for the lifetime of the top-level chart execution, and supports client
requests for monitoring status

see the G2 procedures S88-RECIPE-INPUT-DATA__S88-MONITOR-PV.txt and S88-RECIPE-OUTPUT-DATA__S88-MONITOR-PV.txt

Created on Jun 17, 2015
@author: rforbes
'''

from ils.sfc.common.constants import STEP_PENDING, STEP_APPROACHING, STEP_DOWNLOADING, STEP_SUCCESS, STEP_FAILURE, \
    PV_MONITORING, PV_WARNING, PV_OK_NOT_PERSISTENT, PV_OK, PV_BAD_NOT_CONSISTENT, PV_ERROR, PV_NOT_MONITORED, \
    SETPOINT_OK, SETPOINT_PROBLEM


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
            
    def  __init__(self, _chartScope, _stepScope, _recipeLocation, _config, _timer, _timerAttribute, _logger, _providerName):
        from ils.sfc.gateway.api import getIsolationMode
        self.chartScope = _chartScope
        self.config = _config
        self.timer = _timer
        self.timerAttribute = _timerAttribute
        self.logger =_logger
        self.monitoringInfos = []
        self.providerName = _providerName
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
        from system.ils.sfc.common.Constants import DATA, DATA_ID, TIME, CLASS, \
        DOWNLOAD_STATUS, STEP_TIME, STEP_TIMESTAMP, TIMING, DESCRIPTION, \
        FAILURE, PENDING, VALUE, PV_MONITOR_STATUS, PV_MONITOR_ACTIVE, PV_VALUE, TAG_PATH, VALUE_TYPE, TIMEOUT

        from ils.sfc.common.constants import PV_MONITORING, PV_WARNING, PV_OK_NOT_PERSISTENT, PV_OK, \
        PV_BAD_NOT_CONSISTENT, PV_ERROR, PV_NOT_MONITORED
        
        from ils.sfc.gateway.util import getTopChartRunId
        from ils.sfc.common.util import formatTime
        from ils.sfc.gateway.api import  sendMessageToClient
        from ils.sfc.common.constants import INSTANCE_ID, UNITS
        import time
        
#        print "In monitoring.sendClientUpdate()..."

        # the meaning of the columns:
        #header = ['RawTiming', 'Timing', 'DCS Tag ID', 'Setpoint', 'Description', 'Step Time', 'PV', 'setpointColor', 'stepTimeColor', 'pvColor']    
        timerStart = self.getTimerStart()
        providerName = self.providerName
        formattedStart = formatTime(timerStart)
        rows = []
        rows.append([-1.0,'', '', '', '', formattedStart, '', STEP_PENDING, PV_MONITORING, SETPOINT_OK])
        for info in self.monitoringInfos:
            # Note: the data can be an Input or an Output, which are both subclasses of IO
            # oddly enough, Inputs do not have any additional attributes vs IO
            # get common IO attributes and set some defaults:
            description = info.inout.get(DESCRIPTION)
            tagPath = info.inout.get(TAG_PATH)
#
            # This block shouldn't read from a tag, the PV monitoring block should read the tag and set 
            # the recipe data, so this block is independent of our I/O implemention
            pv = info.inout.get(PV_VALUE)
            monitorActive = info.inout.get(PV_MONITOR_ACTIVE)
            if pv == None:
                formattedPV = ""
            elif monitorActive == True:
                formattedPV = "%.2f" % pv
            else:
                formattedPV = "%.2f*" % pv
            
            # Determine the DCS Tag ID - this can either be the name of the tag/UDT or the item id
            import ils.io.api as api
            displayName = api.getDisplayName(providerName, tagPath, info.inout.get(VALUE_TYPE),info.configRow.labelAttribute)
            
            units = info.inout.get(UNITS)
            if units != "":
                description = "%s (%s)" % (description, units)

            #TODO: convert to units if GUI units specified

            stepStatus='unknown'
            pvStatus='unknown'
            setpointStatus='unknown'
            
            #
            # THE SETPOINT STATUS HAS TO HAVE MEMORY - CAN'T DETERMINE THIS AT A POINT IN TIME, ONCE
            # SET IT SHOULDN't BE UNSET
            #

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
                if stepTime != None and stepTime != "" and timeNow < stepTime and downloadStatus == STEP_PENDING:
                    pendingTime = stepTime - 30
                    if timeNow < pendingTime:
                        stepStatus = STEP_PENDING
                    else:
                        stepStatus = STEP_APPROACHING
                else:
                    if downloadStatus == None:
                        stepStatus = STEP_PENDING
                    else:
                        stepStatus = downloadStatus

            else:
                formattedTiming = ''
                stepTimestamp = ''
                # an Input knows nothing about step timing, so step timing fields are blank
                # we know nothing about pending setpoints, but can at least reflect the current one:
                setpoint = info.io.getSetpoint()
                formattedSetpoint = "%.2f" % setpoint
            
            pvStatus = info.inout.get(PV_MONITOR_STATUS)
#TODO Clean this up
            # reference S88-PV-MONITOR-STATUS-COLOR-DECODER.txt
            # SUCCESS, WARNING, MONITORING, NOT_PERSISTENT, NOT_CONSISTENT, OUT_OF_RANGE, ERROR, TIMEOUT
#            if monitorStatus == MONITORING or  monitorStatus == None:
#                pvStatus = PV_MONITORING
#            elif monitorStatus == WARNING:    
#                pvStatus = PV_WARNING
#            elif monitorStatus == NOT_PERSISTENT:    
#                pvStatus = PV_OK_NOT_PERSISTENT
#            elif monitorStatus == SUCCESS:    
#                pvStatus = PV_OK
#            elif monitorStatus == NOT_CONSISTENT:    
#                pvStatus = PV_BAD_NOT_CONSISTENT
#            elif monitorStatus == ERROR or monitorStatus == TIMEOUT:    
#                pvStatus = PV_ERROR
            
            # THIS ISN'T RIGHT - THIS NEEDS TO LATCH (PETE)
            if pvStatus == PV_ERROR:
                setpointStatus = SETPOINT_PROBLEM
            else:
                setpointStatus = SETPOINT_OK

            rows.append([timing, formattedTiming, displayName, formattedSetpoint, description, stepTimestamp, formattedPV, stepStatus, pvStatus, setpointStatus])

        # The client will sort this by timing
         
        payload = dict()
        payload[TIME] = timerStart
        payload[INSTANCE_ID] = getTopChartRunId(self.chartScope)
        payload[DATA_ID] = self.getTimerId()
        payload[DATA] = rows
        sendMessageToClient(self.chartScope, 'sfcUpdateDownloads', payload) 
 
def createMonitoringMgr(chartScope, stepScope, recipeLocation, timer, timerAttribute, monitorDownloadsConfig, logger, provider):
    '''Create the manager and store it in the dropbox. When the top-level chart 
    finishes, the dropbox will automatically delete the manager'''
    from system.ils.sfc import dropboxPut
    from ils.sfc.gateway.util import getTopChartRunId

    mgr = MonitoringMgr(chartScope, stepScope, recipeLocation, monitorDownloadsConfig, timer, timerAttribute, logger, provider)
    topChartRunId = getTopChartRunId(chartScope)
    dropboxPut(topChartRunId, mgr.getTimerId(), mgr)
    return mgr

def getMonitoringMgr(chartRunId, timerId):
    '''Get the given Monitoring Mgr for the given timer. If None is returned, the top-level 
    chart execution has ended'''
    from system.ils.sfc import dropboxGet
    mgr = dropboxGet(chartRunId, timerId)
    return mgr
        