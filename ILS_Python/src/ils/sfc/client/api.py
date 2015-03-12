'''
Created on Nov 13, 2014

@author: rforbes
'''
DELAY_NOTIFICATION_WINDOW_PATH = 'SFC/SFCNotification'

def showDelayNotification(chartRunId, message, ackRequired, messageId):
    from ils.sfc.client.controlPanel import getController
    from ils.sfc.common.constants import CHART_RUN_ID, MESSAGE, MESSAGE_ID, WINDOW_ID, ACK_REQUIRED
    import system.nav
    print 'show delay notification'
    windowProps = dict()
    windowProps[ACK_REQUIRED] = ackRequired
    windowProps[MESSAGE] = message
    windowProps[MESSAGE_ID] = messageId
    windowProps[CHART_RUN_ID]  = chartRunId
    windowProps[WINDOW_ID]  = messageId
    # ACK_REQUIRED is not used in this case
    window = system.nav.openWindowInstance(DELAY_NOTIFICATION_WINDOW_PATH, windowProps)
    window.closable = False # only close under programmatic control
    if ackRequired:
        window.getRootContainer().getComponent('ackButton').visible = True
    controlPanel = getController(chartRunId)
    label = 'Delay'
    if controlPanel != None:
        controlPanel.addWindow(label, DELAY_NOTIFICATION_WINDOW_PATH, window, messageId)
    else:
        print 'couldnt find control panel for run ', chartRunId

def removeDelayNotifications(chartRunId):
    from ils.sfc.client.controlPanel import getController
    controlPanel = getController(chartRunId)
    controlPanel.removeWindows(DELAY_NOTIFICATION_WINDOW_PATH)

def removeDelayNotification(chartRunId, windowId):
    from ils.sfc.client.controlPanel import getController
    controlPanel = getController(chartRunId)
    controlPanel.removeWindow(windowId)
