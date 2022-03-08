'''
Created on Nov 28, 2016

@author: phassler
'''
import string, system
from ils.log import getLogger
log =getLogger(__name__)

def update(rootContainer):
    n = rootContainer.n
    intervalType = rootContainer.intervalType
    intervalType = string.upper(intervalType)
    
    log.tracef( "In %s.update()- setting the real-time start and end time using %s - %s", __name__, intervalType, str(n))
    
    now = system.date.now()
    log.tracef("Now: %s", str(now))

    if intervalType == "MINUTES":
        startTime = system.date.addMinutes(now, -1 * n)
    elif intervalType == "HOURS":
        startTime = system.date.addHours(now, -1 * n)
    elif intervalType == "DAYS":
        startTime = system.date.addDays(now, -1 * n)
    else:
        log.tracef("Using the default interval of 8 hours")
        startTime = system.date.addHours(now, -8)
    
    rootContainer.endTime = now
    rootContainer.startTime = startTime