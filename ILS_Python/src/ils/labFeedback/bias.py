'''
Created on Mar 11, 2017

@author: phass

When implementing the write enabled flag we only protect write to OPC tags (or other external systems).  Writing to memory tags are 
allowed.
'''

import system
from ils.common.cast import toBit
from ils.common.config import getHistoryProvider
from ils.common.error import catchError
from ils.common.util import substituteProvider
from ils.io.util import readTag, writeTag
from ils.queue.message import insert as insertMessage
from ils.queue.constants import QUEUE_INFO, QUEUE_ERROR, QUEUE_WARNING
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

MESSAGE_QUEUE_KEY = "LABFEEDBACK"

def manualOverride(tagPath, previousValue, biasValue, initialchange): 
    try:
        # Find tag provider and the root of the tag by stripping off LabData
        tagProvider=tagPath[tagPath.find("[") + 1:tagPath.find("]")]
        tagRoot=tagPath.rstrip('/manualOverride')
        
        # Strip off the path and get just the name of the UDT
        biasName = tagRoot[:len(tagRoot)]
        biasName = biasName[biasName.rfind('/') + 1:]
        
        if initialchange:
            log.tracef("Skipping lab bias manual override for %s because this was an initial change.", biasName)
            return
        
        ''' I think that manual overrides should not be subject to the updatePermitted tag, but I could be convinced to go either way '''
       
        '''
        updatePermitted = readTag(tagRoot + '/updatePermitted').value
        if not(updatePermitted):
            log.tracef("Skipping lab bias exponential updates for %s because updates are not permitted.", biasName)
            return
        '''
        
        if not(biasValue.quality.isGood()):
            log.warnf("Skipping lab bias manual override updates for %s because the new lab value is bad.", biasName)
            return
        
        biasValue = biasValue.value
        
        if biasValue == None:
            log.warnf("Skipping lab bias manual override updates for %s because the new lab value is None.", biasName)
            return
        
        log.infof("Writing the manual override bias value for %s (%s)", biasName, tagRoot)
    
        writeTag(tagRoot + '/biasValue', biasValue)
    
        # Write this nicely calculated value to either the DCS or the PHD historian
        writeBiasToExternalSystem(tagProvider, tagRoot, biasName, biasValue, system.date.now())
        
    except:
        txt=catchError("exponentialFilter", "Caught an error calculating an exponential filter bias for %s" % (tagPath))
        log.error(txt)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, txt)


def exponentialFilter(tagPath, previousValue, newValue, initialchange): 
    try:
        # Find tag provider and the root of the tag by stripping off LabData
        tagProvider=tagPath[tagPath.find("[") + 1:tagPath.find("]")]
        tagRoot=tagPath.rstrip('/labValue')
        
        # Strip off the path and get just the name of the UDT
        biasName = tagRoot[:len(tagRoot)]
        biasName = biasName[biasName.rfind('/') + 1:]
        
        if initialchange:
            log.tracef("Skipping lab bias exponential updates for %s because this was an initial change.", biasName)
            return
        
        updatePermitted = readTag(tagRoot + '/updatePermitted').value
        if not(updatePermitted):
            log.tracef("Skipping lab bias exponential updates for %s because updates are not permitted.", biasName)
            return
        
        if not(newValue.quality.isGood()):
            log.warnf("Skipping lab bias exponential updates for %s because the new lab value is bad.", biasName)
            return
        
        newValue = newValue.value
        
        if newValue == None:
            log.warnf("Skipping lab bias exponential updates for %s because the new lab value is None.", biasName)
            return
        
        log.infof("Calculating an exponentially filtered bias for %s (%s)", biasName, tagRoot)
        valueOk, rawBias = validateConditions(tagRoot, newValue, biasName)
        if not(valueOk):
            return
        
        sampleTime = readTag(tagRoot + '/labSampleTime').value
        filterConstant = readTag(tagRoot + '/filterConstant').value
        lastBiasValue = readTag(tagRoot + '/biasValue').value
        if lastBiasValue == None:
            log.error("Unable to calculate a bias value for %s because the bias has not been initialized." % (tagPath))
            return
    
        log.tracef("...the last Bias was %f", lastBiasValue)
    
        # Calculate the exponentially filtered bias
        biasValue = filterConstant * rawBias + (1.0 - filterConstant) * lastBiasValue
        log.infof("...calculated the new biased value <%f> from <%f> and <%f> using a filter constant of <%f> for %s", biasValue, newValue, lastBiasValue, filterConstant, biasName)
    
        writeTag(tagRoot + '/biasValue', biasValue)
    
        # Write this nicely calculated value to either the DCS or the PHD historian
        writeBiasToExternalSystem(tagProvider, tagRoot, biasName, biasValue, sampleTime)
        
    except:
        txt=catchError("exponentialFilter", "Caught an error calculating an exponential filter bias for %s" % (tagPath))
        log.error(txt)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, txt)
        
def initializaExponentialFilter(tagPath, initialValue=1.0): 
    try:
        # Find tag provider and the root of the tag by stripping off LabData
        tagProvider=tagPath[tagPath.find("[") + 1:tagPath.find("]")]
        tagRoot=tagPath.rstrip('/labValue')
        
        # Strip off the path and get just the name of the UDT
        biasName = tagRoot[:len(tagRoot)]
        
        # Initialize the bias
        biasValue = initialValue
        log.infof("...initializing the bias value to <%f> for %s", biasValue, biasName)
    
        ''' This writes to the bias UDT in Ignition which is NOT an OPC tag.  I'm not sure if I should send this to an external system.  '''
        writeTag(tagRoot + '/biasValue', biasValue)
    except:
        txt=catchError("exponentialFilter", "Caught an error initializing an exponential filter bias for %s" % (tagPath))
        log.error(txt)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, txt)


def pidFilter(tagPath, previousValue, newValue, initialchange):
    try:
        newValue = newValue.value
        
        # Find tag provider and the root of the tag by stripping off LabData
        tagProvider=tagPath[tagPath.find("[") + 1:tagPath.find("]")]
        tagRoot=tagPath.rstrip('/labValue') 
        
        # Strip off the path and get just the name of the UDT
        biasName = tagRoot[:len(tagRoot)]
        biasName = biasName[biasName.rfind('/') + 1:]
        
        if initialchange:
            log.tracef("Skipping lab bias PID updates for %s because this was an initial change.", biasName)
            return
        
        updatePermitted = readTag(tagRoot + '/updatePermitted').value
        if not(updatePermitted):
            log.tracef("Skipping lab bias PID updates for %s because updates are not permitted.", biasName)
            return
        
        log.tracef("Calculating a PID bias for %s...", biasName)
        
        valueOk, rawBias = validateConditions(tagRoot, newValue, biasName)
        if not(valueOk):
            return
        
        proportionalGain = readTag(tagRoot + '/proportionalGain').value
        integralGain = readTag(tagRoot + '/integralGain').value
        previousError = readTag(tagRoot + '/previousError').value
        sampleTime = readTag(tagRoot + '/sampleTime').value
        lastBiasValue = readTag(tagRoot + '/biasValue').value
        log.tracef("  Last Bias: %s", str(lastBiasValue))
        
        if lastBiasValue == None:
            log.errorf("Unable to calculate a bias value for %s because the bias has not been initialized.", tagPath)
            return
        
        biasValue = proportionalGain * (newValue - previousError) + integralGain * sampleTime * newValue + lastBiasValue
        log.infof("Calculated the new biased value as: %f from %f and %f", biasValue, newValue, lastBiasValue)
        
        writeTag(tagRoot + '/biasValue', biasValue)
        writeTag(tagRoot + '/previousError', newValue)
        
        # Write this nicely calculated value to either the DCS or the PHD historian
        writeBiasToExternalSystem(tagProvider, tagRoot, biasName, biasValue, sampleTime)

    except:
        txt=catchError("pidFilter", "Caught an error calculating an PID filter bias for %s" % (tagPath))
        log.error(txt)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, txt)


def validateConditions(tagRoot, labValue, biasName):
    '''
    This was formerly the bias-update() methods for the root class bias-value.
    It basically makes sure that the conditions are OK to calculate a new bias.
    '''
    historyProvider = getHistoryProvider()
    rateOfChangeLimit = readTag(tagRoot + '/rateOfChangeLimit')
    if not (rateOfChangeLimit.quality.isGood()) or rateOfChangeLimit.value == None:
        msg = "The rate of change limit is either bad or does not have a value.  The validity of the lab sample <%s> cannot be verified, aborting new bias calculations." % (biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return False, 0.0

    '''
    Fetch the model value from history.  Get the value of the model at the time that the lab data sample was collected
    '''
    modelDeadTimeMinutes = readTag(tagRoot + '/modelDeadTimeMinutes')
    if not (modelDeadTimeMinutes.quality.isGood()) or modelDeadTimeMinutes.value < 0.0:
        msg = "The Model dead time for <%s> is either bad or less than 0.0.  Overriding with 0.0 minutes." % (biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        modelDeadTimeMinutes = 0.0
    else:
        modelDeadTimeMinutes = modelDeadTimeMinutes.value
    deadTime = round(modelDeadTimeMinutes * 60.0)
    
    averageWindowMinutes = readTag(tagRoot + '/averageWindowMinutes')
    if not (averageWindowMinutes.quality.isGood()) or averageWindowMinutes.value <= 0.0:
        msg = "The average window for <%s> is either bad or less than 0.0.  Overriding with 0.0 minutes." % (biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        averageWindowMinutes = 0.0
    else:
        averageWindowMinutes = averageWindowMinutes.value
        
    # Convert to seconds and divide by two so the history interval is the window size divided by 2.
    averageWindow = round( averageWindowMinutes * 60.0 / 2.0)
    
    sampleTime = readTag(tagRoot + '/labSampleTime')
    if not (sampleTime.quality.isGood()):
        msg = "The sample time for <%s> is bad.  Aborting new bias calculations." % (biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return False, 0.0
    sampleTime = sampleTime.value
    
    # Now we have all of the parameters we need to query the model value.  We either get the model value at the time of the sample or get the 
    # average model value during a time window centered around the sample time.
    modelTagPath="%s/modelValue" % (tagRoot)
    modelTagPath = substituteProvider(modelTagPath, historyProvider)
    if averageWindow == 0:      
        ds = system.tag.queryTagHistory(paths=[modelTagPath], startDate=sampleTime, rangeMinutes=1, aggregationMode="SimpleAverage", ignoreBadQuality=True, noInterpolation=True, returnSize=1)
        if ds.rowCount == 0:
            msg = "Unable to acquire a value for the model <%s> at <%s> for bias value %s." % (modelTagPath, str(sampleTime), biasName)
            log.warn(msg)
            insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
            return False, 0.0
        modelValue = ds.getValueAt(0,1)
        log.tracef("Reading the value of the model from <%s> at the time of the sample <%s> was <%f>",modelTagPath, str(sampleTime), modelValue)
    else:
        startDate = system.date.addSeconds(sampleTime, int(-1 * (averageWindow + deadTime)))
        endDate  = system.date.addSeconds(sampleTime, int(averageWindow - deadTime))
        ds = system.tag.queryTagHistory(paths=[modelTagPath], startDate=startDate, endDate=endDate, aggregationMode="SimpleAverage", ignoreBadQuality=True, noInterpolation=True, returnSize=1)
        if ds.rowCount == 0:
            msg = "Unable to acquire an average value for the model <%s> from <%s> to <%s> for bias value %s." % (modelTagPath, str(startDate), str(endDate), biasName)
            log.warn(msg)
            insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
            return False, 0.0
        modelValue = ds.getValueAt(0,1)
        log.tracef("The average value of the model <%s> from <%s> to <%s> was <%f>", modelTagPath, str(startDate), str(endDate), modelValue)

    if modelValue == None:
        msg = "Unable to process model value None for model tag <%s> for bias value %s." % (modelTagPath, biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return False, 0.0
    
    '''
    Check if this bias should be multiplicative
    '''
    multiplicative = readTag(tagRoot + '/multiplicative').value
    if multiplicative:
        #TODO call DB-SPECIAL-VAL-CHK
        rawBias = labValue / modelValue
    else:
        rawBias = labValue - modelValue
    
    '''
    The final check is to check the rate of change
    '''
    oldRawBias = readTag(tagRoot + '/rawBias')
    if not (oldRawBias.quality.isGood()) or oldRawBias.value == None:
        msg = "The old raw bias or <%s> is either bad or does not have a value.  Aborting new bias calculations." % (biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return False, 0.0
    oldRawBias = oldRawBias.value
    
    if abs(rawBias - oldRawBias) > rateOfChangeLimit:
        msg = "Last lab sample for %s is suspicious.  Raw bias is %f and the old raw bias is %f.  Aborting new bias calculations." % (biasName, rawBias, oldRawBias)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return False, rawBias
    
    log.trace("...the data is consistent, it is OK to calculate a new bias!")
    writeTag(tagRoot + '/rawBias', rawBias)
    return True, rawBias

def biasControlInUse():
    return True


def writeBiasToExternalSystem(tagProvider, tagRoot, biasName, biasValue, sampleTime):
    from ils.common.config import getTagProvider
    productionProviderName = getTagProvider()   # Get the Production tag provider
    
    log.tracef("Writing %s for %s", str(biasValue), biasName)
    writeEnabled = readTag("[" + tagProvider + "]Configuration/LabFeedback/labFeedbackWriteEnabled").value
    if tagProvider == productionProviderName and not(writeEnabled):
        msg = "Unable to write bias value <%f> for <%s> because writes are inhibited for Lab Bias Feedback." % (biasValue, biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return
    
    writeEnabled = readTag("[" + tagProvider + "]Configuration/Common/writeEnabled").value
    if tagProvider == productionProviderName and not(writeEnabled):
        msg = "Unable to write bias value <%f> for <%s> because all writes are globally inhibited." % (biasValue, biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return

    serverType = readTag(tagRoot + '/biasTargetServerType')
    if not (serverType.quality.isGood()) or (serverType.value not in ["OPC", "HDA"]):
        msg = "Unable to write bias value <%f> for <%s> because the Target Server Type is bad or not one of OPC or HDA" % (biasValue, biasName)
        log.error(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, msg)
        return
    serverType = serverType.value
    
    serverName = readTag(tagRoot + '/biasTargetServerName')
    if not (serverName.quality.isGood()) or serverName.value == None:
        msg = "Unable to write bias value <%f> for <%s> because the Target Server name is bad or not specified" % (biasValue, biasName)
        log.error(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, msg)
        return
    serverName = serverName.value
    
    itemId = readTag(tagRoot + '/biasTargetItemId')
    if not (itemId.quality.isGood()) or itemId.value == None:
        msg = "Unable to write bias value <%f> for <%s> because the Target Item-Id is bad or not specified" % (biasValue, biasName)
        log.error(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, msg)
        return
    itemId = itemId.value
    
    log.tracef("...writing to %s %s (%s)", serverName, itemId, serverType)
    if serverType == "HDA":
        returnQuality = system.opchda.insert(serverName, itemId, biasValue, sampleTime, 192)
        if returnQuality.isGood():
            txt = "Successfully wrote bias value <%f> at <%s> to <%s> via OPC-HDA for <%s>." % (biasValue, str(sampleTime), itemId, biasName)
            insertMessage(MESSAGE_QUEUE_KEY, QUEUE_INFO, txt)
        else:
            txt = "Error writing bias value <%f> at <%s> to <%s> via OPC-HDA for <%s>." % (biasValue, str(sampleTime), itemId, biasName)
            insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, txt)
    else:
        returnQuality = system.opc.writeValue(serverName, itemId, biasValue)
        if returnQuality.isGood():
            txt = "Successfully wrote bias value <%f> to <%s> for <%s>." % (biasValue, itemId, biasName)
            insertMessage(MESSAGE_QUEUE_KEY, QUEUE_INFO, txt)
        else:
            txt = "Error writing bias value <%f> to <%s> for <%s>." % (biasValue, itemId, biasName)
            insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, txt)


def setUpdatePermitted(tagPath, updatePermitted):
    log.infof("...setting the updatePermitted for %s to %s", tagPath, updatePermitted)
    
    updatePermittedBit = toBit(updatePermitted)
    tagPath = tagPath + "/updatePermitted"
    status = writeTag(tagPath, updatePermittedBit)
    if status == 0:
        log.errorf("Setting the updatePermitted of %s to %s failed", tagPath, str(updatePermitted))