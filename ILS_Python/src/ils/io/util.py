'''
Created on Dec 3, 2014

@author: Pete
'''

import system, string, time
from java.util import Date
from ils.common.util import isText
from ils.common.config import getTagProvider, getIsolationTagProvider,  getDatabase, getIsolationDatabase
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def runChecks():
    for tagPath in [
            "DiagnosticToolkit/CRX/CRX-BLOCK-POLYMER-FLAG",
            "Data Pump/data",
            "SFC IO/Fast Scan Data",
            "SFC IO/Fast Scan Data/VRF006Z",
            "SFC IO/Fast Scan Data/VRF006Z/permissiveValue"
            ]:

        providers = []
        providers.append(getTagProvider())
        providers.append(getIsolationTagProvider())

        for provider in providers:
            fullTagPath = provider + tagPath
            print "-------------------------"
            print "Checking ", fullTagPath
            
            for strategy in ["TAGTYPE", "BROWSETAGS", "BROWSETAGSSIMPLE", "PYTHONCLASS"]:
                isUDT = isUDTorFolder(fullTagPath, strategy)
                print "Check 1: ", isUDT

def getUDTProperty(fullTagPath, prop):
    '''
    IA has made it annoyingly difficult to get the value of a custom property out of an instance of a UDT.  
    This is a utility to get the value of a property.
    '''
    log.tracef("Getting %s from %s...", prop, fullTagPath)
    
    path = "%s.ExtendedProperties" % fullTagPath
    props = system.tag.read(path)
    if props.value is not None:
            for p in props.value:
                if p.getProperty().name.lower() == prop.lower():
                    return p.value

    return None

'''
Try and figure out if the thing is a UDT or a folder (the folder support is for I/O in isolation where
UDTs are replaced by folders).  Return True if the tag path is a UDT or a folder, false otherwise.
I have tried lot's of different approaches to crack this nut and none of them seem to work to well.
I have left them in here because something might change in Ignition at some point that will change the way they work,
or maybe I am calling one of the APIs incorrectly.  The goal is to find one approach that works quickly and 
reliably in all scopes.
'''
def isUDTorFolder(fullTagPath, strategy="PYTHONCLASS"):
    log.tracef("Checking if %s is a UDT or a folder...", fullTagPath)
    
    '''
    This strategy uses system.tag.read(tagPath + ".TagType") this returns an integer enumeration whose return values
    are undocumented (I'm sure it is documented somewhere, but I don't know where).  The problem with this strategy is that 
    I get deifferent results in client scope than I do in gateway scope. In client scope, a folder is a 6 and an opc tag is a 0
    In gateway scope, a folder is 0 and an opc tag is a 0
    '''
    if strategy == "TAGTYPE":
        tagType = system.tag.read(fullTagPath + ".TagType").value
        log.tracef("...is of type %s", str(tagType))
        if tagType in [6, 10]:
            return True
    
    # This strategy uses the browseTags() API to get a browseTag object which has a great isUDT() and isFolder() method.
    elif strategy == "BROWSETAGS":
        parentPath = fullTagPath[0:fullTagPath.rfind("/")]
        tagPath = fullTagPath[fullTagPath.rfind("/")+1:]
        browseTags = system.tag.browseTags(parentPath, "*", recursive=False)
        for browseTag in browseTags:
            if browseTag.fullPath == fullTagPath:
                if browseTag.isUDT():
                    return True
                elif browseTag.isFolder():
                    return True
                else:
                    return False
    
    # This strategy uses the browseTagsSimple() API to get a browseTag object which has a great isUDT() and isFolder() method.
    elif strategy == "BROWSETAGSSIMPLE":
        parentPath = fullTagPath[0:fullTagPath.rfind("/")]
        tagPath = fullTagPath[fullTagPath.rfind("/")+1:]
        browseTags = system.tag.browseTagsSimple(parentPath, "ASC")
        for browseTag in browseTags:
            if browseTag.fullPath == fullTagPath:
                if browseTag.isUDT():
                    return True
                elif browseTag.isFolder():
                    return True
                else:
                    return False

    # This implements a strategy that may work for ILS I/O but is not at all general purpose.  It relies on the
    # conventiion that UDTs have a memory tag named "pythonClass".  This tag is copied to isolation when we make 
    # isolation tags. 
    elif strategy == "PYTHONCLASS":
        tagExists = system.tag.exists(fullTagPath + "/pythonClass")
        if tagExists:
            return True
        else:
            return False
    else:
        print "Unexpected strategy"
   
    return False

# Try and figure out if the thing is a UDT. Return True if the tag path is a UDT, false otherwise.
# There is possibly an easier way to do this and avoid the whole broseTag API issues of 
# having to put a wild card in front of the tagPath.  I could use system.tag.read(tagPath + ".TagType.
# but I don't know how to decode the integer enumeration that is returned.   
def isUDT(fullTagPath):
    log.tracef("Checking if %s is a UDT...", fullTagPath)
    try:
        isUDT = False
        parentPath, tagPath = splitTagPath(fullTagPath)
        log.tracef("Parent: <%s>, Tag: <%s>", parentPath, tagPath)
#        tags = system.tag.browseTags(parentPath=parentPath, tagPath="*"+tagPath)
#        for tag in tags:
#            log.tracef("Checking <%s> vs <%s>", tag.fullPath, fullTagPath)
#            if tag.fullPath == fullTagPath:
#                log.tracef(" --names match--")
#                isUDT = tag.isUDT()
#                log.tracef("  isUDT: %s", str(isUDT)) 
        tags = system.tag.browseTagsSimple(parentPath, "ASC")
        for tag in tags:
            log.tracef("Checking <%s> vs <%s>", tag.fullPath, fullTagPath)
            if tag.fullPath == fullTagPath:
                log.tracef(" --names match--")
                isUDT = tag.isUDT()
                log.tracef("  isUDT: %s", str(isUDT)) 
                return isUDT
    except:
        log.errorf("Error attempting to determine if <%s> is a UDT, parent: %s, tag path: %s", fullTagPath, parentPath, tagPath)
        isUDT = False  
    return isUDT

def getOutputForTagPath(tagProvider, tagPath, outputType):
    isolationMode = False
    if tagProvider == getIsolationTagProvider():
        isolationMode = True
    
    if isUDT(tagPath) or isolationMode:
        '''
        I have not figured out a good way of reading the type of a UDT.  So instead I will read the pythonClass memory tag
        which I have embedded in each of our I/O UDTs.  Then I could create a method to get the output path fri the UDT, but 
        instead I did the cheap and cheerful case statement.  It would be more robust to take the OO method approach.
        '''
        pythonClass = system.tag.read(tagPath + "/pythonClass").value
        if pythonClass in ["PKSController", "PKSACEController", "PKSRampController"]:
            tagPath = "%s/%s/value" % (tagPath, outputType)
        elif pythonClass in ["OPCOutput", "OPCTag"]:
            tagPath = "%s/value" % (tagPath)
        else:
            raise ValueError, "Unexpected python I/O class <%s> for <%s> in %s" % (pythonClass, tagPath, __name__)
        
    return tagPath

# This is the easier method but I need to know how to decode the tagTypoe integer
#def ___isUDTNew(fullTagPath):
#    isUDT = False
#    tagType = system.tag.read(fullTagPath + ".TagType")
#    print tagType       
#    return isUDT


def isFolder(fullTagPath):
    log.tracef("Checking if %s is a folder...", fullTagPath)
    isFolder = False
    parentPath, tagPath = splitTagPath(fullTagPath)
    log.tracef("Parent: <%s>, Tag: <%s>", parentPath, tagPath)
    
    tags = system.tag.browseTagsSimple(parentPath, "ASC")
    for tag in tags:
        log.tracef("Checking <%s> vs <%s>", tag.fullPath, fullTagPath)
        if tag.fullPath == fullTagPath:
            log.tracef(" --names match--")
            isFolder = tag.isFolder()
            log.tracef("  isFolder: %s", str(isFolder)) 
            return isFolder    
    
    return isFolder

def getTagScript(fullTagPath):
    log.tracef("Looking for a tag change script for: %s", fullTagPath)
    tagConfigurations = system.tag.browseConfiguration(fullTagPath, False)
    for tagConfig in tagConfigurations:
        tagType = tagConfig.getTagType()
        log.tracef("Tag type: <%s>", str(tagType))
        if str(tagType) in ["DB", "OPC"]:
            log.tracef("Checking properties...")
            props = tagConfig.getProperties()
            for prop in props:
                log.tracef("%s %s", str(prop),  tagConfig.get(prop)) 
                if str(prop) == "eventScripts":
                    log.tracef("  --- found a tag change script ---")
                    return tagConfig.get(prop)
    log.tracef("    Did not find a tag script!")
    return None

def isExpressionTag(fullTagPath):
    tagConfigurations = system.tag.browseConfiguration(fullTagPath, False)
    for tagConfig in tagConfigurations:
        tagType = tagConfig.getTagType()
        if str(tagType) == "DB":
            props = tagConfig.getProperties()
            for prop in props: 
                if str(prop) == "expressionType":   
                    if str(tagConfig.get(prop)) == "Expression":
                        return True
                    else:
                        return False
    return False

def isQueryTag(fullTagPath):
    tagConfigurations = system.tag.browseConfiguration(fullTagPath, False)
    for tagConfig in tagConfigurations:
        tagType = tagConfig.getTagType()
        if str(tagType) == "DB":
            props = tagConfig.getProperties()
            for prop in props:
                if str(prop) == "expressionType": 
                    if str(tagConfig.get(prop)) == "SQL_Query":
                        return True
                    else:
                        return False
    return False

def getTagExpression(fullTagPath):
    tagConfigurations = system.tag.browseConfiguration(fullTagPath, False)
    for tagConfig in tagConfigurations:
        props = tagConfig.getProperties()
        for prop in props:
            log.tracef("%s: %s", str(prop), tagConfig.get(prop))
            if str(prop) == "expression":
                return tagConfig.get(prop)
    return None

def getTagSQL(fullTagPath):
    tagConfigurations = system.tag.browseConfiguration(fullTagPath, False)
    for tagConfig in tagConfigurations:
        props = tagConfig.getProperties()
        for prop in props:
            if str(prop) == "expression":
                return tagConfig.get(prop)
    return None

'''
A controller is a complicated UDT with embedded UDTs.  Often we are given one of the inner UDTs, for the setpoint or mode for example and we want to 
find the controller.  So we start at the root of the path and walk the tag path until we get a UDT.
'''
def getOuterUDT(fullTagPath):
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

def getInnerUDT(fullTagPath):
    # Strip off the provider
    UDTType=None
    
    if fullTagPath.find("]")>=0:
        provider=fullTagPath[:fullTagPath.find("]") + 1]
        tagPath=fullTagPath[fullTagPath.find("]") + 1:]
    else:
        provider="[]"
        tagPath=fullTagPath
    
#    print "Provider: <%s>, tag path: <%s>" % (provider, tagPath)

    # Before we start walking up the tag path, check if the tag itself is a UDT
    tp = provider + tagPath
    if isUDT(tp):
        UDTType=getUDTType(tp)
        return UDTType 
    
    tokens=tagPath.split('/')
    
    # Now walk up the tagpath until we find a UDT
    tokens.reverse()
    for token in tokens:
        tp=provider + tagPath[:tagPath.rfind(token)]
        if tp[len(tp) - 1] == "/":
            tp = tp[:len(tp) - 1]
        
#        print "Checking if <%s> is a UDT: " % (tp)
        if isUDT(tp):
            UDTType=getUDTType(tp)
            return UDTType 

#    print "There must not be a UDT in the tag path..."
    return UDTType

def getUDTType(fullTagPath):
    # Strip off the provider
#    print "Getting the type of UDT for tagpath: ", fullTagPath
    UDTType = system.tag.read(fullTagPath + '.UDTParentType').value
    return UDTType

#    UDTType=None
#    parentPath, tagPath = splitTagPath(fullTagPath)
#    tags = system.tag.browseTags(parentPath=parentPath, tagPath="*"+tagPath)
#    for tag in tags:
#        if tag.fullPath == fullTagPath:
#            print tag.type, tag.dataType, tag.UDTParentType
#    return UDTType
    
            
# Try and figure out if the thing is a controller, we should already know that it is a UDT.
# If it has a tag PythonClass, and the Python class contains the word controller then it is a controller, 
# otherwise it is NOT a controller.
def checkIfController(fullTagPath):
    tagPath=fullTagPath + '/pythonClass'
    exists=system.tag.exists(tagPath)
    if not(exists):
        return False

    pythonClass=system.tag.read(tagPath).value
#    print "Checking if <%s> contains <CONTROLLER>" % (pythonClass)
    if pythonClass.upper().find('CONTROLLER') > -1:
        return True

    return False

# Compare two tag values taking into account that a float may be disguised as a text string and also
# calling two floats the same if they are almost the same.
def equalityCheck(val1, val2, recipeMinimumDifference, recipeMinimumRelativeDifference):
#    if (val1 == None and val2 != None) or (val1 != None and val2 == None):
#        print "Failed the initial check..."
#        return False
 
    val1IsText = isText(val1)
    val2IsText = isText(val2)
    
    # 7/20/18 - Added Nnne to check below.  If item-id for tags is wrong, or tag doesn't exist in OPC server, then the value will Be None with
    #           a quality of config error. 

    # When we write a NaN we read back a Null value which looks like a '' - Treat these as equal
    if val1 == None or val2 == None or string.upper(str(val1)) == "NAN" or string.upper(str(val2)) == "NAN":
        print "One of the values is NAN or None..."
        val1 = string.upper(str(val1))
        val2 = string.upper(str(val2))
        print "Now comparing: ", val1, val2
        if (val1 == 'NAN' or val1 == '' or val1 == 'NONE' or val1 == None) and (val2 == 'NAN' or val2 == '' or val2 == 'NONE' or val2 == None):
            print " EQUAL "
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
 
    startTime = Date().getTime()
    delta = (Date().getTime() - startTime) / 1000
    
    while (delta < timeout):
        qv = system.tag.read(tagPath)
        log.trace("%s - %s: comparing <%s> (%s) to <%s>" % (__name__, tagPath, str(qv.value), str(qv.quality), str(val)))
        if string.upper(str(val)) == "NAN":
            if qv.value == None:
                return True, ""
        else:
            if string.upper(str(qv.quality)) == 'GOOD':
                if qv.value == val:
                    return True, ""
                if equalityCheck(qv.value, val, 0.0001, 0.0001):
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
        writeStatus = system.tag.read(tagRoot + "/writeStatus").value
        if string.upper(writeStatus) in ["SUCCESS", "FAILURE"]:
            writeConfirmed = writeStatus = system.tag.read(tagRoot + "/writeConfirmed").value
            writeErrorMessage = writeStatus = system.tag.read(tagRoot + "/writeErrorMessage").value
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
        writeStatus = system.tag.read(tagRoot + "/writeStatus").value
        if string.upper(writeStatus) == "SUCCESS":
            return True, ""
        elif string.upper(writeStatus) == "FAILURE":
            writeErrorMessage = system.tag.read(tagRoot + "/writeErrorMessage").value
            return False, writeErrorMessage

        # Time in seconds
        time.sleep(frequency)
        delta = (Date().getTime() - startTime) / 1000

    log.error("Timed out waiting for write complete of %s!" % (tagRoot))
    return False, "Timed out waiting for write complete"

def getDatabaseFromTagPath(tagPath):
    '''
    This parses a full tagpath, which includes the provider at the beginning in square brackets, and returns the 
    provider without the brackets.  If a tag provider is not included in the tag path then the production tag provider is returned.
    '''
    provider = getProviderFromTagPath(tagPath)
    productionProvider = getTagProvider()
    
    if provider == productionProvider:
        db = getDatabase()
    else:
        db = getIsolationDatabase()

    return db


def getProviderFromTagPath(tagPath):
    '''
    This parses a full tagpath, which includes the provider at the beginning in square brackets, and returns the 
    provider without the brackets.  If a tag provider is not included in the tag path then the production tag provider is returned.
    '''
    if tagPath.find("[") < 0 or tagPath.find("]") < 0:
        provider = getTagProvider()
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
    
    if tagProvider == productionTagProvider:
        db = getDatabase()
    else:
        db = getIsolationDatabase()

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

    productionProviderName = getTagProvider()   # Get the Production tag provider
    providerName = getProviderFromTagPath(tagPath)
    globalWriteEnabled = system.tag.read("[" + providerName + "]/Configuration/Common/writeEnabled").value
    
#    print "----------"
#    print "Tag:                 ", tagPath
#    print "Production Provider: ", productionProviderName
#    print "This tag provider:   ", providerName
#    print "Global Write Enabled:", globalWriteEnabled
#    print "----------"
    
    if providerName == productionProviderName and not(globalWriteEnabled):
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