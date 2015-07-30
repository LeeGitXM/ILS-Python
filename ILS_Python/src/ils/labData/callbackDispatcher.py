'''
Created on Jul 10, 2015

@author: Pete
'''

# The callbacks dispatched from this module may be in external (generally xom or ils), shared or project,
# Keep in mind that project scope cannot be called from a tagChange trhread, it can be called frobutm a timer script however, 
# which runs in the gateway  is attached to a project.

# This import will show an error, but it is required to handle calculation methods that are in project scope.
import shared, system, sys, string, traceback
log = system.util.getLogger("com.ils.labData")
derivedLog = system.util.getLogger("com.ils.labData.derivedValues")
customValidationLog = system.util.getLogger("com.ils.labData.customValidation")

def customValidate(valueName, rawValue, validationProcedure):
    customValidationLog.trace("There is a custom validation procedure <%s> for %s" % (valueName, validationProcedure))
    
    # If they specify shared or project scope, then we don't need to do this
    if not(string.find(validationProcedure, "project") == 0 or string.find(validationProcedure, "shared") == 0):
        # The method contains a full python path, including the package, module, and function name
        separator=string.rfind(validationProcedure, ".")
        packagemodule=validationProcedure[0:separator]
        separator=string.rfind(packagemodule, ".")
        package = packagemodule[0:separator]
        module  = packagemodule[separator+1:]
        customValidationLog.trace("Using External Python, the package is: <%s>.<%s>" % (package,module))
        exec("import %s" % (package))
        exec("from %s import %s" % (package,module))
        
    try:
        customValidationLog.trace("Calling validation procedure %s" % (validationProcedure))
        isValid = eval(validationProcedure)(valueName, rawValue)
        customValidationLog.trace("The value returned from the validation procedure is: %s" % (str(isValid)))
                
    except:
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 500)
        customValidationLog.error("Caught an exception calling calculation method named %s... \n%s" % (validationProcedure, errorTxt) )
        isValid = False
    
    return isValid


def derivedValueCallback(callback, dataDictionary):
    if not(string.find(callback, "project") == 0 or string.find(callback, "shared") == 0):
        # The method contains a full python path, including the method name
        separator=string.rfind(callback, ".")
        packagemodule=callback[0:separator]
        separator=string.rfind(packagemodule, ".")
        package = packagemodule[0:separator]
        module  = packagemodule[separator+1:]
        derivedLog.trace("Using External Python, the package is: <%s>.<%s>" % (package,module))
        exec("import %s" % (package))
        exec("from %s import %s" % (package,module))
        
    derivedLog.trace("Calling %s and passing %s" % (callback, str(dataDictionary)))
    newVal = eval(callback)(dataDictionary)
    
    return newVal
