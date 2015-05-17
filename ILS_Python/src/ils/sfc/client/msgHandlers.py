'''
All SFC Client Message Handlers
'''
import system.gui
from system.print import createPrintJob

import ils.sfc.common.util
from ils.sfc.client.util import sendResponse 
from ils.sfc.client.controlPanel import ControlPanel
from ils.sfc.common.util import getChartRunId

def sfcCloseWindow(payload):
    from ils.sfc.client.controlPanel import getController
    from ils.sfc.common.constants import WINDOW, INSTANCE_ID
    windowPath = payload[WINDOW] 
    system.nav.closeWindow(windowPath)
    controlPanel = getController(payload[INSTANCE_ID])
    if controlPanel != None:
        controlPanel.removeWindows(windowPath)

def sendTestResponse(payload):
    '''For testing only, short-circuit dialogs etc and send a response back to the gateway'''
    from ils.sfc.common.constants import TEST_RESPONSE, MESSAGE_ID
    testResponse = payload.get(TEST_RESPONSE, None)
    if testResponse == None:
        return False
    print('returning test response ' + testResponse)
    sendResponse(payload[MESSAGE_ID], testResponse)
    return True
 
def sfcDialogMessage(payload):
    from ils.sfc.common.constants import METHOD, MESSAGE, MESSAGE_ID, ACK_REQUIRED
    from ils.sfc.client.windowUtil import createPositionedWindow
     
    if sendTestResponse(payload):
        return

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
    chartRunId = getChartRunId(payload)
    controlPanel = getController(chartRunId)
    controlPanel.setCommandMask(payload[ENABLE_PAUSE], payload[ENABLE_RESUME], payload[ENABLE_CANCEL])

def sfcInput(payload):
    from ils.sfc.common.constants import PROMPT, INPUT, MESSAGE_ID
    if sendTestResponse(payload):
        return
        
    response = system.gui.inputBox(payload[PROMPT], INPUT)
    sendResponse(payload[MESSAGE_ID], response)

def sfcLimitedInput(payload):
    from ils.sfc.common.constants import PROMPT, INPUT, MESSAGE_ID
    if sendTestResponse(payload):
        return
        
    response = system.gui.inputBox(payload[PROMPT], INPUT)
    sendResponse(payload[MESSAGE_ID], response)

def sfcPrintFile(payload):
    from ils.sfc.common.constants import COMPUTER, FILENAME, VIEW_FILE, PRINT_FILE, SERVER, MESSAGE
    computer = payload[COMPUTER]
    filepath = payload[FILENAME]
    viewFile = payload[VIEW_FILE]
    printFile = payload[PRINT_FILE]
    if computer == SERVER:
        message = payload[MESSAGE]
    else:
        message = ils.sfc.common.util.readFile(filepath)
    window = system.nav.openWindow('SFC/SaveData')
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
        print 'printing a', windowName
        printJob = system.print.createPrintJob(window)
        printJob.showPrintDialog = showPrintDialog
        printJob.print()
        
def sfcSaveData(payload):
    from ils.sfc.common.constants import DATA, VIEW_FILE, PRINT_FILE, FILEPATH
    data = payload[DATA]
    viewFile = payload[VIEW_FILE]
    printFile = payload[PRINT_FILE]
    filepath = payload[FILEPATH]
    #ils.sfc.util.printObj(props, 0)
    window = system.nav.openWindow('SFC/SaveData')
    window.title = filepath
    textArea = window.getRootContainer().getComponent("textArea")
    textArea.text = data
    if printFile:
        printJob = createPrintJob(textArea) 
        printJob.print()
    
def sfcSelectInput(payload):
    system.nav.openWindow('SFC/SelectInput', payload)

def sfcShowQueue(payload):
    from ils.sfc.common.constants import QUEUE
    initialProps = dict()
    initialProps['key'] = payload[QUEUE]
    system.nav.openWindow('Queue/Message Queue', initialProps)

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
    from ils.sfc.common.constants import PROMPT, MESSAGE_ID
    if sendTestResponse(payload):
        return
        
    prompt = payload[PROMPT]
    response = system.gui.confirm(prompt, 'Input', False)
    
    # Send the response message:
    sendResponse(payload[MESSAGE_ID], response)

def sfcUnexpectedError(payload):
    from ils.sfc.common.util import handleUnexpectedClientError
    from ils.sfc.common.constants import MESSAGE
    message = payload[MESSAGE]
    handleUnexpectedClientError(message)

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
    from ils.sfc.common.constants import MESSAGE_ID, PRIMARY_CONFIG, SECONDARY_CONFIG, POSTING_METHOD
    from ils.sfc.client.windowUtil import createPositionedWindow
    from ils.sfc.common.util import callMethodWithParams
    if sendTestResponse(payload):
        return        
    windowProperties = dict()
    windowProperties[MESSAGE_ID] = payload[MESSAGE_ID]
    window = createPositionedWindow(payload, windowProperties)
    postingMethod = payload[POSTING_METHOD]
    primaryDataTable = payload[PRIMARY_CONFIG]
    secondaryDataTable = payload[SECONDARY_CONFIG]
    keys = ['window', 'primaryDataTable', 'secondaryDataTable']
    values = [window, primaryDataTable, secondaryDataTable]
    callMethodWithParams(postingMethod, keys, values)

def sfcChartStarted(payload):
    from ils.sfc.client.controlPanel import createControlPanel
    createControlPanel(payload)

def sfcTestAddAction(payload):
    from ils.sfc.common.constants import CHART_NAME, COMMAND, INSTANCE_ID
    from ils.sfc.client.test import addAction
    addAction(payload[COMMAND], payload[CHART_NAME], payload[INSTANCE_ID])
