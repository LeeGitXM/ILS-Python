'''
Created on Dec 3, 2014

@author: Pete
'''

import system, string, time
from java.util import Date
from ils.common.util import isText
from ils.config.common import getTagProvider, getIsolationTagProvider,  getDatabase, getIsolationDatabase
from ils.log import getLogger
log = getLogger(__name__)


def checkIfController(fullTagPath):
    '''
    Try and figure out if the thing is a controller, we should already know that it is a UDT.
    If it has a tag PythonClass, and the Python class contains the word controller then it is a controller, 
    otherwise it is NOT a controller.
    (I don't think this is used - PAH 2/6/2022)
    '''
    tagPath=fullTagPath + '/pythonClass'
    exists=system.tag.exists(tagPath)
    if not(exists):
        return False

    pythonClass=readTag(tagPath).value
    if pythonClass.upper().find('CONTROLLER') > -1:
        return True

    return False

def getOuterUDT(fullTagPath):
    '''
    A controller is a complicated UDT with embedded UDTs.  Often we are given one of the inner UDTs, for the setpoint or mode for example and we want to 
    find the controller.  So we start at the root of the path and walk the tag path until we get a UDT.
    '''
    
    # Strip off the provider   
    if fullTagPath.find("]")>=0:
        provider=fullTagPath[:fullTagPath.find("]") + 1]
        tagPath=fullTagPath[fullTagPath.find("]") + 1:]
    else:
        provider="[]"
        tagPath=fullTagPath
    
#    print "Provider: <%s>, tag path: <%s>" % (provider, tagPath)

    tokens=tagPath.split('/')
    
    tp = ""
    for token in tokens:
        if tp == "":
            tp=provider + token
        else:
            tp=tp + '/' + token
        
#        print "Checking if <%s> is a UDT: " % (tp)
        if isUDT(tp):
            UDTType=getUDTType(tp)
            return UDTType, tp 

#        print "There must not be a UDT in the tag path..."
    return None, tagPath



def getOutputForTagPath(tagProvider, tagPath, outputType):
    '''
    Given a UDT path and an output type, return the tagpath of the desired target tag.
    For example, if the UDT is a controller and the output type is setpoint then return root/setpoint/value;
    if the UDT is a controller and the output type is output then return root/output/value.
    If the udt is an OPCTag or OPCOutput then return root/value.
    
    Note: The tagProvider argument is no longer used.  It used to help determine if we were in Isolation mode, but
    that was before I implemented a distinct set of isolation UDTs. 
    '''
    log.tracef("Tag Provider: %s", tagProvider)
    log.tracef("Tag Path: %s", tagPath)
    log.tracef("Output Type: %s", outputType)
    
    if isUDT(tagPath):
        pythonClass = getUDTProperty(tagPath, "pythonClass")
        if pythonClass in ["PKSController", "PKSACEController", "PKSRampController"]:
            tagPath = "%s/%s/value" % (tagPath, outputType)
        elif pythonClass in ["OPCOutput", "OPCTag"]:
            tagPath = "%s/value" % (tagPath)
        else:
            raise ValueError, "Unexpected python I/O class <%s> for <%s> in %s" % (pythonClass, tagPath, __name__)
        
    return tagPath


def getTagExpression(fullTagPath):
    ''' Get the expression for an expression tag '''
    try:
        if not(isExpressionTag(fullTagPath)):
            log.warnf("Tag <%s> is not an expression tag!", fullTagPath)
            return None
        
        config = system.tag.getConfiguration(fullTagPath, False)
        expr = config[0]['expression']

        return expr
                
    except:
        log.errorf("Error attempting to get the expression for <%s>.", fullTagPath)  
        
    return False


def getTagScript(fullTagPath):
    ''' Get the tag script - there are a lot of handlers, I guess get any and all.  Any type of tag can have a tag script '''
    try:        
        config = system.tag.getConfiguration(fullTagPath, False)
        script = config[0].get('eventScripts', None)
        return script
                
    except:
        log.errorf("Error attempting to get the event scripts for <%s>.", fullTagPath)  
        
    return None


def getTagSQL(fullTagPath):
    ''' Get the SQL for a query tag '''
    try:
        if not(isQueryTag(fullTagPath)):
            log.warnf("Tag <%s> is not a query tag!", fullTagPath)
            return None
        
        config = system.tag.getConfiguration(fullTagPath, False)
        print config
        sql = config[0].get('query', None)
        return sql
                
    except:
        log.errorf("Error attempting to get the SQL for <%s>.", fullTagPath)  
        
    return None


def getUDTProperty(fullTagPath, propertyName):
    '''  
    Get the value of a UDT property.
    '''
    log.tracef("Getting %s from %s...", propertyName, fullTagPath)
    
    if not(isUDT(fullTagPath)):
        log.warnf("Unable to find the UDT property <%s> in <%s> because it is NOT a UDT", propertyName, fullTagPath)
        return None
    
    config = system.tag.getConfiguration(fullTagPath, False)
    udtParameters = config[0]['parameters']
    prop = udtParameters.get(propertyName, None)
    if prop == None:
        log.warnf("Unable to find property <%s> in UDT <%s>", propertyName, fullTagPath)
        return None
    
    propertyValue = prop.value
    return propertyValue


def getUDTType(fullTagPath):
    '''
    Return the UDT type for the specified tag.  Return None if the tag is not a UDT instance.
    '''
    try:
        config = system.tag.getConfiguration(fullTagPath, False)
        tagType = config[0]['tagType']
    
        if str(tagType) in ['UdtInstance']:
            udtType = config[0]['typeId']
            return udtType
        else:
            log.warnf("Tag <%s> is not a UDT instance", fullTagPath)
            return None
                
    except:
        log.errorf("Error attempting to determine the UDT type for <%s>.", fullTagPath)  
        
    return None


def isExpressionTag(fullTagPath):
    ''' Determine if the referenced tag is an expression tag '''
    try:
        config = system.tag.getConfiguration(fullTagPath, False)
        tagType = config[0]['tagType']
    
        if str(tagType) in ['AtomicTag']:
            valueSource = config[0]['valueSource']
            if str(valueSource) == 'expr':
                return True
            else:
                return False

        return False
                
    except:
        log.errorf("Error attempting to determine if <%s> is an expression tag.", fullTagPath)  
        
    return False


def isFolder(fullTagPath):
    '''
    Determine if the referenced tag is a Folder. Return True if the tag path is a Folder, false otherwise.
    '''
    try:
        config = system.tag.getConfiguration(fullTagPath, False)
        tagType = config[0]['tagType']
    
        if str(tagType) in ['Folder']:
            return True

        return False
                
    except:
        log.errorf("Error attempting to determine if <%s> is a folder.", fullTagPath)

    return False
    

def isQueryTag(fullTagPath):
    ''' Determine if the referenced tag is a query tag. '''
    try:
        config = system.tag.getConfiguration(fullTagPath, False)
        tagType = config[0]['tagType']
    
        if str(tagType) in ['AtomicTag']:
            valueSource = config[0]['valueSource']
            if str(valueSource) == 'db':
                return True
            else:
                return False

        return False
                
    except:
        log.errorf("Error attempting to determine if <%s> is a Query tag.", fullTagPath)  
        
    return False

def isMemoryTag(fullTagPath):
    ''' Determine if the referenced tag is a query tag. '''
    try:
        config = system.tag.getConfiguration(fullTagPath, False)
        tagType = config[0]['tagType']
    
        if str(tagType) in ['AtomicTag']:
            valueSource = config[0]['valueSource']

            if str(valueSource) == 'memory':
                return True
            else:
                return False

        return False
    except:
        log.errorf("Error attempting to determine if <%s> is a Memory tag.", fullTagPath)  
        
    return False
    
def isReferenceTag(fullTagPath):
    ''' Determine if the referenced tag is a query tag. '''
    try:
        config = system.tag.getConfiguration(fullTagPath, False)
        tagType = config[0]['tagType']
    
        if str(tagType) in ['AtomicTag']:
            valueSource = config[0]['valueSource']

            if str(valueSource) == 'reference':
                return True
            else:
                return False

        return False
                
    except:
        log.errorf("Error attempting to determine if <%s> is a Reference tag.", fullTagPath)  
        
    return False

def isOpcTag(fullTagPath):
    ''' Determine if the referenced tag is a query tag. '''
    try:
        config = system.tag.getConfiguration(fullTagPath, False)
        tagType = config[0]['tagType']
    
        if str(tagType) in ['AtomicTag']:
            valueSource = config[0]['valueSource']

            if str(valueSource) == 'opc':
                return True
            else:
                return False

        return False
    
    except:
        log.errorf("Error attempting to determine if <%s> is an OPC.", fullTagPath)  
        
    return False

def isUDT(fullTagPath):
    '''
    Determine if the referenced tag is a UDT. Return True if the tag path is a UDT, false otherwise.
    '''
    try:
        config = system.tag.getConfiguration(fullTagPath, False)
        tagType = config[0]['tagType']
    
        if str(tagType) in ['UdtInstance']:
            return True

        return False
                
    except:
        log.errorf("Error attempting to determine if <%s> is a UDT.", fullTagPath)  
        
    return False


def isUDTorFolder(fullTagPath):
    '''
    Try and figure out if the thing is a UDT or a folder (the folder support is for I/O in isolation where
    UDTs are replaced by folders).  Return True if the tag path is a UDT or a folder, false otherwise.
    '''
    log.tracef("Checking if %s is a UDT or a folder...", fullTagPath)
    
    config = system.tag.getConfiguration(fullTagPath, False)
    tagType = config[0]['tagType']

    if str(tagType) in ['UdtInstance', 'Folder']:
        return True

    return False


def equalityCheck(val1, val2, recipeMinimumDifference, recipeMinimumRelativeDifference):
    '''
    Compare two tag values taking into account that a float may be disguised as a text string and also
    calling two floats the same if they are almost the same.
    '''

    val1IsText = isText(val1)
    val2IsText = isText(val2)
    
    # 7/20/18 - Added Nnne to check below.  If item-id for tags is wrong, or tag doesn't exist in OPC server, then the value will Be None with
    #           a quality of config error. 

    # When we write a NaN we read back a Null value which looks like a '' - Treat these as equal
    if val1 == None or val2 == None or string.upper(str(val1)) == "NAN" or string.upper(str(val2)) == "NAN":
        log.tracef("One of the values is NAN or None...")
        val1 = string.upper(str(val1))
        val2 = string.upper(str(val2))
        log.tracef("Now comparing %s and %s ", str(val1), str(val2))
        if (val1 == 'NAN' or val1 == '' or val1 == 'NONE' or val1 == None) and (val2 == 'NAN' or val2 == '' or val2 == 'NONE' or val2 == None):
            log.tracef(" EQUAL ")
            return True
        else:
            return False
        
    elif val1IsText and val2IsText:
        if string.upper(val1) == string.upper(val2):
            return True
        else:
            return False

    else:
        # They aren't both text, so if only one is text, then they don't match 
        if val1IsText or val2IsText:
            return False
        else:
            minThreshold = abs(recipeMinimumRelativeDifference * float(val1))
            if minThreshold < recipeMinimumDifference:
                minThreshold = recipeMinimumDifference

            if abs(float(val1) - float(val2)) < minThreshold:
                return True
            else:
                return False


# Verify that val2 is the same data type as val1.  Make sure to treat special values such as NaN as a float
def dataTypeMatch(val1, val2):
    val1IsFloat = isText(val1)
    val2IsFloat = isText(val2)
    
    if val1IsFloat != val2IsFloat:
        return False
    
    return True


# Implement a simple write confirmation.  We know the value that we tried to write, read the tag for a
# reasonable amount of time.  As soon as we read the value back we are done.  The tagPath must be the full path to the 
# OPC tag that we are confirming, not the UDT that contains it. 
def confirmWrite(tagPath, val, timeout=60.0, frequency=1.0): 
    log.trace("%s - Confirming the write of <%s> to %s..." % (__name__, str(val), tagPath))
 
    provider = getProviderFromTagPath(tagPath)
    recipeMinimumDifference = readTag("[" + provider + "]/Configuration/Common/ioMinimumDifference").value
    recipeMinimumRelativeDifference = readTag("[" + provider + "]/Configuration/Common/ioMinimumRelativeDifference").value
    
    startTime = Date().getTime()
    delta = (Date().getTime() - startTime) / 1000
    
    while (delta < timeout):
        qv = readTag(tagPath)
        log.trace("%s - %s: comparing <%s> (%s) to <%s>" % (__name__, tagPath, str(qv.value), str(qv.quality), str(val)))
        if string.upper(str(val)) == "NAN":
            if qv.value == None:
                return True, ""
        else:
            if string.upper(str(qv.quality)) == 'GOOD':
                if qv.value == val:
                    return True, ""
                if equalityCheck(qv.value, val, recipeMinimumDifference, recipeMinimumRelativeDifference):
                    return True, ""

        # Time in seconds
        time.sleep(frequency)
        delta = (Date().getTime() - startTime) / 1000

    log.info("Write of <%s> to %s was not confirmed!" % (str(val), tagPath))
    return False, "Value %s was not confirmed" % (str(val))  

# This waits for a pending write / confirmation to complete and then reports back the results.  This does not perform 
# any value comparison or have any output specific knowledge.  There is another thread running, generally in the gateway,
# that is methodized on the class of object performing the write that does the actual write comparison.  This probably should 
# keep checking as long as the write method is still running, as indicated by a NULL writeStatus, but I have implemented a 
# timeout just to prevent it from running forever. 
def waitForWriteConfirm(tagRoot, timeout=60, frequency=1):
    log.trace("Waiting for write confirmation for <%s>..." % (tagRoot))
 
    startTime = Date().getTime()
    delta = (Date().getTime() - startTime) / 1000

    while (delta < timeout):
        writeStatus = readTag(tagRoot + "/writeStatus").value
        if string.upper(writeStatus) in ["SUCCESS", "FAILURE"]:
            writeConfirmed = writeStatus = readTag(tagRoot + "/writeConfirmed").value
            writeErrorMessage = writeStatus = readTag(tagRoot + "/writeErrorMessage").value
            return writeConfirmed, writeErrorMessage

        # Time in seconds
        time.sleep(frequency)
        delta = (Date().getTime() - startTime) / 1000

    log.error("Timed out waiting for write confirmation of %s!" % (tagRoot))
    return False, "Timed out waiting for write confirmation"
   
# This waits for a pending write to complete and then reports back the results of the write.  This does not do a write 
# confirm in the sense that it compares the value we wrote to the actual value.  It is generally used with a WriteWithNoCheck.
# It will check the basics of tag configuration and report that back.  It will also report if the OPC write was successful. 
# It determines if a write is complete by checking for SUCCESS or FAILURE in the writeStatus tag.
def waitForWriteComplete(tagRoot, timeout=60, frequency=1): 
    log.trace("Waiting for write completion for <%s>..." % (tagRoot))
 
    startTime = Date().getTime()
    delta = (Date().getTime() - startTime) / 1000

    while (delta < timeout):
        writeStatus = readTag(tagRoot + "/writeStatus").value
        if string.upper(writeStatus) == "SUCCESS":
            return True, ""
        elif string.upper(writeStatus) == "FAILURE":
            writeErrorMessage = readTag(tagRoot + "/writeErrorMessage").value
            return False, writeErrorMessage

        # Time in seconds
        time.sleep(frequency)
        delta = (Date().getTime() - startTime) / 1000

    log.error("Timed out waiting for write complete of %s!" % (tagRoot))
    return False, "Timed out waiting for write complete"

def getDatabaseFromTagPath(tagPath):
    '''
    There isn't a generic way to get a database from a tag path.
    In the previous architecture where there was only production / isolation set of interfaces, it was possible but now in Ignition 8
    where we are embracing multiple projects (like every Ignition gateway), each with their own set of production and isolation providers
    this is impossible.  Since this thread is generally called from a UDT, the suggested upgrade is to add a "database property / tag to the UDT
    and then configure each UDT with the database name.
    '''
    db = ""
    return db


def getProviderFromTagPath(tagPath):
    '''
    This parses a full tagpath, which includes the provider at the beginning in square brackets, and returns the 
    provider without the brackets.  If a tag provider is not included in the tag path then this will return the default provider which
    doesn't have any meaning in gateway scope.
    '''
    if tagPath.find("[") < 0 or tagPath.find("]") < 0:
        provider = "[]"
    else:
        provider=tagPath[1:tagPath.find(']')]
    return provider


def getProviderAndDatabaseFromTagPath(tagPath):
    '''
    This parses a full tagpath, which includes the provider at the beginning in square brackets, and returns the 
    provider without the brackets.  If a tag provider is not included in the tag path then the production tag provider is returned.
    '''
    tagProvider = getProviderFromTagPath(tagPath)
    productionTagProvider = getTagProvider()
    
    # TODO resolve hardcode
    projectName = "XOM_Dev"
    if tagProvider == productionTagProvider:
        db = getDatabase(projectName)
    else:
        db = getIsolationDatabase(projectName)

    return tagProvider, db


def splitTagPath(tagPath):
    '''
    Convert a full tag path to just the tag name.
    Full tag paths are always used internally, but just the tag name is used for display purposes.
    '''
    if tagPath.find('/') < 0:
        # There isn't a folder, so we either have a root folder or a tag at the root level.  
        # Return the provider as the parent and the rest as the tag
        if tagPath.find(']') < 0:
            parentPath = "[]"
            tagName = tagPath
        else:
            parentPath=tagPath[:string.rfind(tagPath, ']') + 1]
            tagName=tagPath[string.rfind(tagPath, ']') + 1:]
    else:
        parentPath = tagPath[:string.rfind(tagPath, '/')]
        tagName = tagPath[string.rfind(tagPath, '/') + 1:]
#    print "Split <%s> into <%s> and <%s>" % (tagPath, parentPath, tagName)
    return parentPath, tagName


def stripProvider(tagPath):
    '''
    Strip the tag provider from the full tagPath.
    '''

    if tagPath.find(']') >= 0:
        tagPath=tagPath[string.rfind(tagPath, ']') + 1:]

    return tagPath


# Check for the existence of the tag and that the global write enabled flag is set (only for production tags).
def checkConfig(tagPath):
    log.trace("In util.checkConfig()...")
    # Check that the tag exists
    reason = ""
    tagExists = system.tag.exists(tagPath)
    if not(tagExists):
        reason = "Tag %s does not exist!" % tagPath
        log.error(reason)
        return False, reason

    providerName = getProviderFromTagPath(tagPath)
    globalWriteEnabled = readTag("[" + providerName + "]/Configuration/Common/writeEnabled").value
    
#    print "----------"
#    print "Tag:                 ", tagPath
#    print "This tag provider:   ", providerName
#    print "Global Write Enabled:", globalWriteEnabled
#    print "----------"
    
    if not(globalWriteEnabled):
        log.info('Write bypassed for %s because writes are inhibited!' % (tagPath))
        return False, 'Writing is currently inhibited'
    
    # TODO: Check if there is an item ID and an OPC server.  
    # TODO: Should I read the current value and see if quality is good?  If the tag is bad is there any way a write could succeed?
                                           
    return True, ""

def getTagSuffix(tagName):
    '''
    Parse the tagname and return the suffix (PV, SP, MODE, etc.) in uppercase 
    '''
    log.tracef("Parsing %s...", tagName)
    if len(tagName) == 0:
        return ""

    period = tagName.rfind('.')
    if period < 0:
        return ""
    
    suffix = string.upper(tagName[period+1:])
    return suffix

def readTag(tagPath):
    '''
    This reads a single tag using a blocking read and returns a single qualified value.
    This just saves the caller the task of packing and unpacking the results when migrating
    to Ignition 8. 
    '''
    qvs = system.tag.readBlocking([tagPath])
    qv = qvs[0]
    return qv

def writeTag(tagPath, val):
    '''
    This writes a single value to a single tag using an asynchronous write without confirmation or status return.
    This just saves the caller the task of packing the arguments when migrating to Ignition 8. 
    '''
    if str(val) == "nan":        
        if isMemoryTag(tagPath):
            log.tracef("In %s.writeTag(): Writing a NaN (converting NaN to None) to the memory tag: %s", __name__, tagPath)
            system.tag.writeAsync([tagPath], [None])
        elif isOpcTag(tagPath):
            log.tracef("In %s.writeTag(): Writing a NaN to the OPC tag: %s", __name__, tagPath)
            writeNaN(tagPath)
        else:
            log.errorf("Unable to write a NaN to tag <%s>, which is not an OPC or memory tag!", tagPath)
    else:
        log.tracef("In %s.writeTag(): writing <%s> to <%s>....", __name__, str(val), tagPath)
        system.tag.writeAsync([tagPath], [val])
        
def isNaN(qv):
    '''
    I tried to use math.isnan() here but it didn't work very well.  
    It seems brittle to check for this very specific quality string, but all I could get to work 
    '''
    log.tracef("In %s.isNaN(), checking %s...", __name__, str(qv))
    if "Invalid value: Tag value is Infinity or NaN" in str(qv.quality):
        return True
    else:
        return False
        
def writeNaN(tagPath):
    '''
    Write a NaN to an OPC tag
    '''
    log.infof("In %s.writeNaN(), writing a NaN to %s", __name__, tagPath)
    
    try:
        vals = system.tag.readBlocking([tagPath + ".OpcServer", tagPath + ".OpcItemPath"])
        server = vals[0].value
        itemId = vals[1].value
        system.opc.writeValue(server, itemId, float("NaN"))
    except:
        log.errorf("Error writing NaN to %s", tagPath)
    
def writeTagSync(tagPath, val):
    '''
    This reads a single value to a single tag using a blocking write without confirmation or status return.
    This just saves the caller the task of packing the arguments when migrating to Ignition 8. 
    '''
    system.tag.writeBlocking([tagPath], [val])