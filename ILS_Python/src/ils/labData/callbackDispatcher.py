'''
Created on Jul 10, 2015

@author: Pete
'''

# The callbacks dispatched from this module may be in external (generally xom or ils), shared or project,
# Keep in mind that project scope cannot be called from a tagChange trhread, it can be called frobutm a timer script however, 
# which runs in the gateway  is attached to a project.

# This import will show an error, but it is required to handle calculation methods that are in project scope.
import project, sys, string, traceback
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.labData")
derivedLog = LogUtil.getLogger("com.ils.labData.derivedValues")
customValidationLog = LogUtil.getLogger("com.ils.labData.customValidation")

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


def derivedValueCallback():
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
        
    try:
        derivedLog.trace("Calling %s and passing %s" % (callback, str(dataDictionary)))
        newVal = eval(callback)(dataDictionary)
        derivedLog.trace("The value returned from the calculation method is: %s" % (str(newVal)))
                
        # Use the sample time of the triggerValue and store the value in the database and in the UDT tags
        storeValue(valueId, valueName, newVal, sampleTime, database)
                
        # This updates the Lab Data UDT tags
        writeTags, writeTagValues = updateTags(tagProvider, unitName, valueName, newVal, sampleTime, True, writeTags, writeTagValues)
                
        # Derived lab data also has a target OPC tag that it needs to update - do this immediately
        system.opc.writeValue(resultServerName, resultItemId, newVal)
                
        # Remove this derived variable from the open calculation cache
        del derivedCalculationCache[valueName]
                
    except:
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 500)
        derivedLog.error("Caught an exception calling calculation method named %s... \n%s" % (callback, errorTxt) )

    return writeTags, writeTagValues
