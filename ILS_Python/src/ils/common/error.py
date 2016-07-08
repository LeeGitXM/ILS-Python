'''
Created on Jul 7, 2016

@author: ils
'''
import system, traceback


def notify(source="", contextMsg=""):
    txt = catch(source, contextMsg)
    system.gui.errorBox(txt)

def catch(source="", contextMsg=""):    
    import sys

    exception = sys.exc_info()[1] 

    # Get a traceback as well:
    tracebackMsg = None
    try:
        tracebackMsg = traceback.format_exc()
    except:
        pass

    cause = ""
    # for Java exceptions, get the cause
    try:
        cause = exception.getCause().getMessage()
    except:
        # This must be a Python exception which doesn't support getCause()
        pass

    txt = "Caught an error %s:%s:%s:%s:%s" % \
        (source, contextMsg, exception, tracebackMsg, cause)

    print txt
    return txt
    