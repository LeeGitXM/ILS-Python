'''
Created on Feb 4, 2021

@author: phass
'''

from ils.log import getLogger
log =getLogger(__name__)

def work_ok():
    log.infof("work_ok() is starting...")
    work()
    log.infof("work_ok() is Done!")
    
def work_crash():
    log.infof("work_crash() is starting...")
    work()
    
    '''
    Now create an unhandled error!
    '''
    denom = 0.0
    numer = 7.66
    val = numer / denom
    
    '''
    Should never get here!
    '''
    print "val = ", val
    
    log.infof("work_crash() is Done!")
    
def work():
    print "In work()"
    log.tracef("A trace message #1")
    log.tracef("A trace message #2")
    log.tracef("A trace message #3")
    