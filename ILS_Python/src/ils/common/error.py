'''
Created on Jul 7, 2016

@author: ils
'''
import system, traceback


def notifyError(source="", contextMsg=""):
    txt = catchError(source, contextMsg)
    system.gui.errorBox(txt)

def catchError(source="", contextMsg=""):    
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

    txt = "Caught an error in %s.\n%s\n\n%s:%s:%s" % \
        (source, contextMsg, exception, tracebackMsg, cause)

    return txt
    