'''
Created on Nov 13, 2014

@author: rforbes
'''
DELAY_NOTIFICATION_WINDOW_PATH = 'SFC/Notification'

def showDelayNotification(chartRunId, message, ackRequired, messageId, endTimeOrNone, title):
    from ils.sfc.client.controlPanel import getController
    from ils.sfc.common.constants import CHART_RUN_ID, MESSAGE, MESSAGE_ID, WINDOW_ID, ACK_REQUIRED, END_TIME
    import system.nav
    windowProps = dict()
    windowProps[ACK_REQUIRED] = ackRequired
    windowProps[MESSAGE] = message
    windowProps[MESSAGE_ID] = messageId
    windowProps[CHART_RUN_ID]  = chartRunId
    windowProps[WINDOW_ID]  = messageId
    windowProps[END_TIME]  = endTimeOrNone 
    # ACK_REQUIRED is not used in this case
    window = system.nav.openWindowInstance(DELAY_NOTIFICATION_WINDOW_PATH, windowProps)
    window.closable = False # only close under programmatic control
    window.title = title
    if ackRequired:
        window.getRootContainer().getComponent('ackButton').visible = True
    controlPanel = getController(chartRunId)
    label = 'Delay'
    if controlPanel != None:
        controlPanel.addWindow(label, DELAY_NOTIFICATION_WINDOW_PATH, window, messageId)
    else:
        print 'couldnt find control panel for run ', chartRunId
    updateDelayNotifications()

def removeDelayNotifications(chartRunId):
    from ils.sfc.client.controlPanel import getController
    controlPanel = getController(chartRunId)
    controlPanel.removeWindows(DELAY_NOTIFICATION_WINDOW_PATH)

def removeDelayNotification(chartRunId, windowId):
    from ils.sfc.client.controlPanel import getController
    controlPanel = getController(chartRunId)
    controlPanel.removeWindow(windowId)

def updateDelayNotifications():
    '''update the "time remaining" messages in all delay notification windows'''
    import system
    import time
    from ils.sfc.common.util import getHoursMinutesSeconds
    currentEpochSeconds = time.time()
    for window in system.gui.getOpenedWindows():
        if window.name == 'SFCNotification':
            endTimeEpochSeconds = window.getRootContainer().endTime
            if endTimeEpochSeconds != None:
                remainingEpochSeconds = max(endTimeEpochSeconds - currentEpochSeconds, 0)
                hours, minutes, seconds = getHoursMinutesSeconds(remainingEpochSeconds)
                message = str(hours) + " hours " + str(minutes) + " minutes " + str(seconds) + " seconds remaining"
                textField = window.getRootContainer().getComponent('textField')
                textField.text = message

