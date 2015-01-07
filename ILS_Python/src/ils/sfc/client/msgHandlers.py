'''
All SFC Client Message Handlers
'''
import system.gui
from system.print import createPrintJob

from ils.sfc.common.constants import MESSAGE, PROMPT, INPUT, SERVER, RESPONSE, DATA, FILEPATH, WINDOW
from ils.sfc.common.constants import COMPUTER, INSTANCE_ID, FILENAME, PRINT_FILE, VIEW_FILE, LABEL
import ils.sfc.common.util
from ils.sfc.client.util import sendResponse 
from ils.sfc.client.controlPanel import ControlPanel
from ils.sfc.common.util import getChartRunId

def sfcCloseWindow(payload):
    from ils.sfc.client.controlPanel import getController
    windowPath = payload[WINDOW] 
    system.nav.closeWindow(windowPath)
    controlPanel = getController(payload[INSTANCE_ID])
    if controlPanel != None:
        controlPanel.removeWindows(windowPath)

def sfcDialogMessage(payload):
    from ils.sfc.common.constants import WINDOW_ID, CHART_RUN_ID, DIALOG, METHOD, MESSAGE, MESSAGE_ID, ACK_REQUIRED, POSITION, SCALE
    from ils.sfc.client.util import openWindow
    from ils.sfc.client.controlPanel import getController
    from ils.sfc.common.util import createUniqueId
   #Todo: is special dialog needed?
    chartRunId = payload[CHART_RUN_ID]
    dialog = payload[DIALOG]
    # ? what is method used for ?
    method = payload[METHOD]
    # do we care about ack? I thnk it just holds up step execution if true
    position = payload[POSITION]
    scale = payload[SCALE]
    windowProps = dict()
    windowProps[ACK_REQUIRED] = payload[ACK_REQUIRED]
    windowProps[MESSAGE_ID] = payload[MESSAGE_ID]
    windowProps[MESSAGE] = payload[MESSAGE]
    windowProps[CHART_RUN_ID]  = chartRunId
    windowId = createUniqueId()
    windowProps[WINDOW_ID]  = windowId
    window = openWindow(dialog, position, scale, windowProps, windowId)
    controlPanel = getController(chartRunId)
    #TODO: what should label be? unique?
    label = "Notification"
    if controlPanel != None:
       controlPanel.addWindow(label, dialog, window)
    else:
        print 'couldnt find control panel for run ', chartRunId

def sfcEnableDisable(payload):
    from ils.sfc.client.controlPanel import getController
    from ils.sfc.common.constants import ENABLE_PAUSE, ENABLE_RESUME, ENABLE_CANCEL
    chartRunId = getChartRunId(payload)
    controlPanel = getController(chartRunId)
    controlPanel.setCommandMask(payload[ENABLE_PAUSE], payload[ENABLE_RESUME], payload[ENABLE_CANCEL])

def sfcInput(payload):
    prompt = payload[PROMPT]
    response = system.gui.inputBox(prompt, INPUT)
    sendResponse(payload, response)

def sfcLimitedInput(payload):
    prompt = payload[PROMPT]
    response = system.gui.inputBox(prompt, INPUT)
    sendResponse(payload, response)

def sfcPrintFile(payload):
    computer = payload[COMPUTER]
    filepath = payload[FILENAME]
    viewFile = payload[VIEW_FILE]
    printFile = payload[PRINT_FILE]
    if computer == SERVER:
        message = payload[MESSAGE]
    else:
        message = ils.sfc.common.util.readFile(filepath)
    window = system.nav.openWindow('SaveData')
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
        printJob = None # system.print.createPrintJob(window)
        printJob.showPrintDialog = showPrintDialog
        printJob.print()
        
def sfcSaveData(payload):
    data = payload[DATA]
    viewFile = payload[VIEW_FILE]
    printFile = payload[PRINT_FILE]
    filepath = payload[FILEPATH]
    #ils.sfc.util.printObj(props, 0)
    window = system.nav.openWindow('SaveData')
    window.title = filepath
    textArea = window.getRootContainer().getComponent("textArea")
    textArea.text = data
    if printFile:
        printJob = createPrintJob(textArea) 
        printJob.print()
    
def sfcSelectInput(payload):
    window = system.nav.openWindow('SelectInput', payload)

def sfcShowQueue(payload):
    system.nav.openWindow('Queue/Message Queue')

def sfcShowWindow(payload):
    from ils.sfc.client.util import openWindow
    from ils.sfc.client.controlPanel import getController
    from ils.sfc.common.util import createUniqueId
    from ils.sfc.common.constants import POSITION, SCALE, WINDOW, INSTANCE_ID
    windowPath = payload[WINDOW]
    label = payload[LABEL]
    position = payload[POSITION]
    scale = payload[SCALE]
    windowProperties = dict()
    window = openWindow(windowPath, position, scale, windowProperties)
    chartRunId = payload[INSTANCE_ID]
    controlPanel = getController(chartRunId)
    windowId = createUniqueId()
    if controlPanel != None:
        controlPanel.addWindow(label, windowPath, window, windowId)
    else:
        print 'couldnt find control panel for run ', chartRunId

def sfcPostDelayNotification(payload):
    from ils.sfc.common.constants import WINDOW_ID, CHART_RUN_ID
    from ils.sfc.client.api import showDelayNotification
    showDelayNotification(payload[CHART_RUN_ID], payload[MESSAGE], False, payload[WINDOW_ID])

def sfcDeleteDelayNotifications(payload):
    from ils.sfc.common.constants import CHART_RUN_ID
    from ils.sfc.client.api import removeDelayNotifications
    removeDelayNotifications(payload[CHART_RUN_ID])

def sfcDeleteDelayNotification(payload):
    from ils.sfc.common.constants import CHART_RUN_ID, WINDOW_ID
    from ils.sfc.client.api import removeDelayNotification
    removeDelayNotification(payload[CHART_RUN_ID], payload[WINDOW_ID])
        
def sfcYesNo(payload):
    prompt = payload[PROMPT]
    response = system.gui.confirm(prompt, 'Input', False)
    
    # Send the response message:
    replyPayload = dict()
    replyPayload[RESPONSE] = response
    sendResponse(payload, replyPayload)

def sfcUnexpectedError(payload):
    from ils.sfc.common.util import handleUnexpectedClientError
    message = payload[MESSAGE]
    handleUnexpectedClientError(message)

def sfcUpdateControlPanel(payload):
    from ils.sfc.client.controlPanel import updateControlPanels 
    updateControlPanels()

def sfcUpdateChartStatus(payload):
    from ils.sfc.client.controlPanel import updateChartStatus 
    updateChartStatus(payload)
