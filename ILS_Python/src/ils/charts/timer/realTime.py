'''
Created on Nov 28, 2016

@author: phassler
'''
import string, system

def update(rootContainer):
    n = rootContainer.n
    intervalType = rootContainer.intervalType
    intervalType = string.upper(intervalType)
    
    print "Setting the realtime start and end time using %s - %s" % (intervalType, str(n))
    
    now = system.date.now()
    print "Now: ", now

    if intervalType == "MINUTES":
        startTime = system.date.addMinutes(now, -1 * n)
    elif intervalType == "HOURS":
        startTime = system.date.addHours(now, -1 * n)
    elif intervalType == "DAYS":
        startTime = system.date.addDays(now, -1 * n)
    else:
        print "Using the default interval of 8 hours"
        startTime = system.date.addHours(now, -8)
    
    rootContainer.endTime = now
    rootContainer.startTime = startTime