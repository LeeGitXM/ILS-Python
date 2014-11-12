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

def sfcCloseWindow(payload):
    from ils.sfc.client.controlPanel import getController
    windowPath = payload[WINDOW] 
    system.nav.closeWindow(windowPath)
    controlPanel = getController(payload[INSTANCE_ID])
    if controlPanel != None:
        controlPanel.removeToolbarButton(windowPath)

def sfcDeleteDelayNotifications(payload):
    pass

def sfcDialogMessage(payload):
    pass

def sfcEnableDisable(payload):
    pass

def sfcInput(payload):
    prompt = payload[PROMPT]
    response = system.gui.inputBox(prompt, INPUT)
    sendResponse(payload, response)

def sfcLimitedInput(payload):
    prompt = payload[PROMPT]
    response = system.gui.inputBox(prompt, INPUT)
    sendResponse(payload, response)

def sfcPostDelayNotification(payload):
    pass

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
    from ils.sfc.common.constants import POSITION, SCALE, WINDOW, INSTANCE_ID
    windowPath = payload[WINDOW]
    label = payload[LABEL]
    position = payload[POSITION]
    scale = payload[SCALE]
    openWindow(windowPath, position, scale)
    chartRunId = payload[INSTANCE_ID]
    controlPanel = getController(chartRunId)
    if controlPanel != None:
        controlPanel.addToolbarButton(label, windowPath)
    else:
        print 'couldnt find control panel for run ', chartRunId

def sfcTimedDelay(payload):
    pass

def sfcYesNo(payload):
    prompt = payload[PROMPT]
    response = system.gui.confirm(prompt, 'Input', False)
    
    # Send the response message:
    replyPayload = dict()
    replyPayload[RESPONSE] = response
    sendResponse(payload, replyPayload)

def sfcUnexpectedError(payload):
    message = payload[MESSAGE]
    system.gui.errorBox(message, 'Unexpected Error')

def sfcUpdateControlPanel(payload):
    from ils.sfc.client.controlPanel import updateControlPanels 
    updateControlPanels()

def sfcChartStarted(payload):
    from ils.sfc.common.constants import INSTANCE_ID, PROJECT, CHART_NAME, USER, DATABASE
    from ils.sfc.common.sessions import createSession
    from ils.sfc.client.controlPanel import createControlPanel
    chartRunId = payload[INSTANCE_ID] 
    project = payload[PROJECT]
    chartName = payload[CHART_NAME]
    user = payload[USER]
    database = payload[DATABASE]
    createSession(user, chartName, chartRunId, database)
    createControlPanel(payload)


