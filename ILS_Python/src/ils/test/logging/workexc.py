'''

'''
import time
import system.ils.log.properties as LogProps 
log = LogProps.getLogger('ils.test.logging.work')

def loggedException():
    result = 84
    try:
        result = 12/0
    except ZeroDivisionError:
        log.info("log: division by zero!")
    return result
        
def printException():
    result = 42
    try:
        result = 12/0
    except ZeroDivisionError:
        print("print: division by zero!")
    return result
    
# Get local variable referenced before assignment.  
# Otherwise   
def untrappedException():
    try:
        result = 12/0
    except ZeroDivisionError:
        log.info("log: division by zero!")
    return result


def work():
    print "In %s.work()" % (__name__)
    
    log.trace("A trace message")

    log.debug("A debug message")
    time.sleep(0.1)
    
    log.info("An info message")
    time.sleep(0.1)

    log.warn("A warning")
    time.sleep(0.1)
    
    log.error("An error")
    time.sleep(0.1)
    
    log.info("This is a formatted info message #%d"%(42)) 
    log.info("This is also a formatted info message #{}",43) 
    
    print "Done!"
    
def worktrace():
    print "In %s.workf()" % (__name__)
    
    pi = 3.14159
    
    log.tracef("A trace message, pi = %.3f", pi)
    time.sleep(0.1)

    log.debugf("A debug message, pi = %.3f", pi)
    time.sleep(0.1)
    
    log.infof("An info message, pi = %.3f", pi)
    time.sleep(0.1)

    log.warnf("A warning, pi = %.3f", pi)
    time.sleep(0.1)
    
    log.tracef("Another trace, pi = %.3f", pi)
    time.sleep(0.1)
    print "Done!"