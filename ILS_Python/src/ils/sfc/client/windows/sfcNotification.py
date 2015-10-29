'''
Created on Jan 15, 2015

@author: rforbes
'''
    
def updateMessage(window):
    '''update the "time remaining" messages in all delay notification windows'''
    import time
    from ils.sfc.common.util import getHoursMinutesSeconds
    currentEpochSeconds = time.time()
    endTimeEpochSeconds = window.getRootContainer().endTime
    if endTimeEpochSeconds != None:
        remainingEpochSeconds = max(endTimeEpochSeconds - currentEpochSeconds, 0)
        hours, minutes, seconds = getHoursMinutesSeconds(remainingEpochSeconds)
        message = str(hours) + " hours " + str(minutes) + " minutes " + str(seconds) + " seconds remaining"
        textField = window.getRootContainer().getComponent('textField')
        textField.text = message
    