'''
All SFC Client Message Handlers
'''
import system.gui
from system.print import createPrintJob

import ils.sfc.common.util
from ils.sfc.client.util import sendResponse 
from ils.sfc.client.controlPanel import ControlPanel
from ils.sfc.client.util import getTopChartRunId 

def sfcCloseWindow(payload):
    from ils.sfc.client.controlPanel import getController
    from ils.sfc.common.constants import WINDOW, INSTANCE_ID
    windowPath = payload[WINDOW]  
    system.nav.closeWindow(windowPath)
    controlPanel = getController(payload[INSTANCE_ID])
    if controlPanel != None:
        controlPanel.removeWindows(windowPath)
 
def sfcDialogMessage(payload):
    from ils.sfc.common.constants import METHOD, MESSAGE, MESSAGE_ID, ACK_REQUIRED
    from ils.sfc.client.windowUtil import createPositionedWindow
     
    # ? what is method used for ?
    method = payload[METHOD]
    
    windowProps = dict()
    windowProps[ACK_REQUIRED] = payload[ACK_REQUIRED]
    windowProps[MESSAGE_ID] = payload[MESSAGE_ID]
    windowProps[MESSAGE] = payload[MESSAGE]
    
    createPositionedWindow(payload, windowProps)

def sfcEnableDisable(payload):
    from ils.sfc.client.controlPanel import getController
    from ils.sfc.common.constants import ENABLE_PAUSE, ENABLE_RESUME, ENABLE_CANCEL
    chartRunId = getTopChartRunId(payload)
    controlPanel = getController(chartRunId)
    controlPanel.setCommandMask(payload[ENABLE_PAUSE], payload[ENABLE_RESUME], payload[ENABLE_CANCEL])

def sfcInput(payload):
    from ils.sfc.common.constants import PROMPT, INPUT, MESSAGE_ID
        
    response = system.gui.inputBox(payload[PROMPT], INPUT)
    sendResponse(payload[MESSAGE_ID], response)

def sfcLimitedInput(payload):
    from ils.sfc.common.constants import PROMPT, INPUT, MESSAGE_ID
        
    response = system.gui.inputBox(payload[PROMPT], INPUT)
    sendResponse(payload[MESSAGE_ID], response)

def sfcPrintFile(payload):
    from ils.sfc.common.constants import COMPUTER, FILENAME, VIEW_FILE, PRINT_FILE, SERVER, MESSAGE
    from system.ils.sfc.common.Constants import SFC_SAVE_DATA_WINDOW
    computer = payload[COMPUTER]
    filepath = payload[FILENAME]
    viewFile = payload[VIEW_FILE]
    printFile = payload[PRINT_FILE]
    if computer == SERVER:
        message = payload[MESSAGE]
    else:
        message = ils.sfc.common.util.readFile(filepath)
    window = system.nav.openWindow(SFC_SAVE_DATA_WINDOW)
    window.title = filepath
    textArea = window.getRootContainer().getComponent("textArea")
    textArea.text = message
    if printFile:
        printJob = createPrintJob(textArea) 
        printJob.print()
        
def sfcPrintWindow(payload):
    windowName = payload['window']
    showPrintDialog = payload['showPrintDialog']
    windows = system.gui.findWindow(windowName)
    for window in windows:
        printJob = system.print.createPrintJob(window)
        printJob.showPrintDialog = showPrintDialog
        printJob.print()
        
def sfcSaveData(payload):
    from ils.sfc.common.constants import DATA, VIEW_FILE, PRINT_FILE, FILEPATH
    from system.ils.sfc.common.Constants import SFC_SAVE_DATA_WINDOW
    data = payload[DATA]
    viewFile = payload[VIEW_FILE]
    printFile = payload[PRINT_FILE]
    filepath = payload[FILEPATH]
    #ils.sfc.util.printObj(props, 0)
    window = system.nav.openWindow(SFC_SAVE_DATA_WINDOW)
    window.title = filepath
    textArea = window.getRootContainer().getComponent("textArea")
    textArea.text = data
    if printFile:
        printJob = createPrintJob(textArea) 
        printJob.print()
    
def sfcSelectInput(payload):
    from system.ils.sfc.common.Constants import SFC_SELECT_INPUT_WINDOW
    system.nav.openWindow(SFC_SELECT_INPUT_WINDOW, payload)

def sfcShowQueue(payload):
    from ils.sfc.common.constants import MESSAGE_QUEUE
    from system.ils.sfc.common.Constants import MESSAGE_QUEUE_WINDOW
    initialProps = dict()
    initialProps['key'] = payload[MESSAGE_QUEUE]
    initialProps['useCheckpoint'] = True
    system.nav.openWindowInstance(MESSAGE_QUEUE_WINDOW, initialProps)

def sfcShowWindow(payload):
    from ils.sfc.client.windowUtil import createPositionedWindow
    createPositionedWindow(payload)
 
def sfcPostDelayNotification(payload):
    from ils.sfc.common.constants import WINDOW_ID, CHART_RUN_ID, END_TIME, MESSAGE
    from ils.sfc.client.notification import showDelayNotification
    endTimeOrNone = payload.get(END_TIME, None)
   # chartName = payload[CHART_NAME]
    title = 'Delay Notification'
    showDelayNotification(payload[CHART_RUN_ID], payload[MESSAGE], False, payload[WINDOW_ID], endTimeOrNone, title)

def sfcDeleteDelayNotifications(payload):
    from ils.sfc.common.constants import CHART_RUN_ID
    from ils.sfc.client.notification import removeDelayNotifications
    removeDelayNotifications(payload[CHART_RUN_ID])

def sfcDeleteDelayNotification(payload):
    from ils.sfc.common.constants import CHART_RUN_ID, WINDOW_ID
    from ils.sfc.client.notification import removeDelayNotification
    removeDelayNotification(payload[CHART_RUN_ID], payload[WINDOW_ID])
        
def sfcYesNo(payload):
    from ils.sfc.common.constants import PROMPT, MESSAGE_ID, TIMEOUT, INSTANCE_ID
    from ils.sfc.client.windowUtil import createWindow
    print "In msgHandlers.sfcYesNo()...", payload
    
    prompt = payload[PROMPT]
    timeoutSecs = payload[TIMEOUT]
    messageId = payload[MESSAGE_ID]
    chartRunId = payload[INSTANCE_ID]
    print "The message id is:", messageId    
    createWindow("SFC/YesNo", "", chartRunId, {"prompt": prompt, "timeoutSecs": timeoutSecs, "messageId": messageId})


def sfcUnexpectedError(payload):
    from ils.sfc.common.util import handleUnexpectedClientError
    from ils.sfc.common.constants import MESSAGE, DATA
    msg = payload[MESSAGE]
    handleUnexpectedClientError(msg)

def sfcUpdateControlPanel(payload):
    from ils.sfc.client.controlPanel import updateControlPanels 
    updateControlPanels()

def sfcUpdateChartStatus(payload):
    from ils.sfc.client.controlPanel import updateChartStatus 
    updateChartStatus(payload)

def sfcUpdateCurrentOperation(payload):
    from ils.sfc.client.controlPanel import updateCurrentOperation 
    updateCurrentOperation(payload)

def sfcReviewData(payload):
    from ils.sfc.common.constants import MESSAGE_ID, PRIMARY_CONFIG, SECONDARY_CONFIG, POSTING_METHOD, PRIMARY_TAB_LABEL, SECONDARY_TAB_LABEL
    from ils.sfc.client.windowUtil import createPositionedWindow
    from ils.sfc.common.util import callMethodWithParams
    windowProperties = dict()
    windowProperties[MESSAGE_ID] = payload[MESSAGE_ID]
    window = createPositionedWindow(payload, windowProperties)
    postingMethod = payload[POSTING_METHOD]
    primaryDataTable = payload[PRIMARY_CONFIG]
    primaryTabLabel = payload[PRIMARY_TAB_LABEL]
    secondaryTabLabel = payload[SECONDARY_TAB_LABEL]
    secondaryDataTable = payload[SECONDARY_CONFIG]
    keys = ['window', 'primaryDataTable', 'primaryTabLabel', 'secondaryDataTable',  'secondaryTabLabel']
    values = [window, primaryDataTable, primaryTabLabel, secondaryDataTable, secondaryTabLabel]
    callMethodWithParams(postingMethod, keys, values)

def sfcReviewFlows(payload):
    from ils.sfc.common.constants import MESSAGE_ID, POSTING_METHOD, DATA
    from ils.sfc.client.windowUtil import createPositionedWindow
    from ils.sfc.common.util import callMethodWithParams
    from system.ils.sfc.common.Constants import HEADING1, HEADING2, HEADING3
    windowProperties = dict()
    windowProperties[MESSAGE_ID] = payload[MESSAGE_ID]
    window = createPositionedWindow(payload, windowProperties)
    postingMethod = payload[POSTING_METHOD]
    dataTable = payload[DATA]
    heading1 = payload[HEADING1]
    heading2 = payload[HEADING2]
    heading3 = payload[HEADING3]
    keys = ['window', 'dataTable', 'heading1', 'heading2', 'heading3']
    values = [window, dataTable, heading1, heading2, heading3]
    callMethodWithParams(postingMethod, keys, values)

def sfcTestAddAction(payload):
    from ils.sfc.common.constants import CHART_NAME, COMMAND, INSTANCE_ID
    from ils.sfc.client.test import addAction
    addAction(payload[COMMAND], payload[CHART_NAME], payload[INSTANCE_ID])
    
def sfcMonitorDownloads(payload):
    from system.ils.sfc.common.Constants import DATA_ID
    from ils.sfc.client.windowUtil import createPositionedWindow
    windowProperties = dict()
    windowProperties['timerId'] = payload[DATA_ID]
    createPositionedWindow(payload, windowProperties)

def sfcUpdateDownloads(payload):
    from system.ils.sfc.common.Constants import DATA_ID, DATA, TIME, INSTANCE_ID
    from ils.sfc.client.windows import monitorDownloads
    chartRunId = payload[INSTANCE_ID]
    timerId = payload[DATA_ID]
    rows = payload[DATA]
    timerStart = payload[TIME]
    downloadsWindow = monitorDownloads.getMonitorDownloadWindow(chartRunId, timerId)
    monitorDownloads.updateTable(downloadsWindow, rows, timerStart)
    
def sfcManualDataEntry(payload):
    from ils.sfc.common.constants import MESSAGE_ID, POSTING_METHOD, DATA, START_TIME, TIMEOUT
    from ils.sfc.client.windowUtil import createPositionedWindow
    from ils.sfc.common.util import callMethodWithParams
    from system.ils.sfc.common.Constants import REQUIRE_ALL_INPUTS
    import time
    windowProperties = dict()
    windowProperties[MESSAGE_ID] = payload[MESSAGE_ID]
    windowProperties[START_TIME] = time.time()
    windowProperties[TIMEOUT] = payload[TIMEOUT]
    window = createPositionedWindow(payload, windowProperties)
    postingMethod = payload[POSTING_METHOD]
    dataset = payload[DATA]
    requireAllInputs = payload[REQUIRE_ALL_INPUTS]
    keys = ['window', 'dataset', 'requireAllInputs']
    values = [window, dataset, requireAllInputs]
    callMethodWithParams(postingMethod, keys, values)

def dispatchMessage(payload):
    from ils.sfc.common.util import callMethodWithParams
    from ils.sfc.common.constants import MESSAGE
    msgName = payload[MESSAGE]
    methodPath = 'ils.sfc.client.msgHandlers.' + msgName
    keys = ['payload']
    values = [payload]
    try:
        callMethodWithParams(methodPath, keys, values)
    except Exception, e:
        try:
            cause = e.getCause()
            errMsg = "Error dispatching client message %s: %s" % (msgName, cause.getMessage())
        except:
            errMsg = "Error dispatching client message %s: %s" % (msgName, str(e))
        system.gui.errorBox(errMsg)

def setMessageQueue(payload):
    from ils.sfc.client.controlPanel import setMessageQueue
    setMessageQueue(payload)

################ New thin client ###################
def sfcSessionStarted(payload):
    '''start or re-establish a session'''
    from ils.sfc.common.constants import SESSION
    from ils.sfc.client.session.controlPanelView import ControlPanelView
    model = payload[SESSION]
    ControlPanelView(model)

def sfcUpdateSession(payload):
    '''update a session'''
    from ils.sfc.common.constants import SESSION
    from ils.sfc.client.session.viewMgr import getControlPanelView
    model = payload[SESSION]
    controlPanelView = getControlPanelView(model.sessionId)
    controlPanelView.updateModel(model)
    
def sfcGetSessionDataResponse(payload):
    '''The response for a sfcRequestChartNames msg'''
    from ils.sfc.common.constants import RESPONSE
    sessionData = payload[RESPONSE]
    window = system.gui.getWindow('Reconnect')
    sessionTable = window.getRootContainer().getComponent("sessionTable")
    sessionTable.data = sessionData
    
