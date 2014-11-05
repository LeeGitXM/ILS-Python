'''
All SFC Client Message Handlers
'''
import system.nav
import system.gui
from system.print import createPrintJob

from ils.sfc.common.constants import MESSAGE, PROMPT, INPUT, SERVER, RESPONSE, DATA, FILEPATH
from ils.sfc.common.constants import COMPUTER, FILENAME, PRINT_FILE, VIEW_FILE
import ils.sfc.common.util
from ils.sfc.client.util import sendResponse 
from ils.sfc.client.controlPanel import ControlPanel

def sfcCloseWindow(payload):
    windowPath = payload[MESSAGE] 
    system.nav.closeWindow(windowPath)
    # TODO: hide/remove button from Control Panel

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
    windowPath = payload['message']
    security = payload['security']
    label = payload['label']
    position = payload['position']
    scale = payload['scale']

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



