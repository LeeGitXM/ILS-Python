'''
Created on Mar 11, 2017

@author: phass

When implementing the write enabled flag we only protect write to OPC tags (or other external systems).  Writing to memory tags are 
allowed.
'''

import system
log = system.util.getLogger("com.ils.labData.labFeedback")
MESSAGE_QUEUE_KEY = "LABFEEDBACK"
from ils.queue.message import insert as insertMessage
from ils.constants.constants import QUEUE_INFO, QUEUE_ERROR, QUEUE_WARNING
from ils.common.config import getHistoryProvider

def exponentialFilter(tagPath, previousValue, newValue, initialchange): 
    newValue = newValue.value
    
    # Find tag provider and the root of the tag by stripping off LabData
    tagProvider=tagPath[tagPath.find("[") + 1:tagPath.find("]")]
    tagRoot=tagPath.rstrip('/labValue') 
    
    # Strip off the path and get just the name of the UDT
    biasName = tagRoot[:len(tagRoot)]
    biasName = biasName[biasName.rfind('/') + 1:]
    
    log.infof("Calculating an exponentially filtered bias for %s (%s)", biasName, tagRoot)
    valueOk, rawBias = validateConditions(tagRoot, newValue, biasName)
    if not(valueOk):
        return
    
    sampleTime = system.tag.read(tagRoot + '/labSampleTime').value
    filterConstant = system.tag.read(tagRoot + '/filterConstant').value
    lastBiasValue = system.tag.read(tagRoot + '/biasValue').value
    if lastBiasValue == None:
        log.error("Unable to calculate a bias value for %s because the bias has not been initialized." % (tagPath))
        return

    log.tracef("...the last Bias was %f", lastBiasValue)

    # Calculate the exponentially filtered bias
    biasValue = filterConstant * rawBias + (1.0 - filterConstant) * lastBiasValue
    log.tracef("...calculated the new biased value <%f> from <%f> and <%f> using a filter constant of <%f>", biasValue, newValue, lastBiasValue, filterConstant)

    system.tag.write(tagRoot + '/biasValue', biasValue)

    # Write this nicely calculated value to either the DCS or the PHD historian
    txt = writeBiasToExternalSystem(tagProvider, tagRoot, biasName, biasValue, sampleTime)
    
    msg = "%s %f that is the exponential filtered bias for %s" % (txt, biasValue, biasName)
    insertMessage(MESSAGE_QUEUE_KEY, QUEUE_INFO, msg)


def pidFilter(tagPath, previousValue, newValue, initialchange):
    print "In pidFilter..."
    
    newValue = newValue.value
    
    # Find tag provider and the root of the tag by stripping off LabData
    tagProvider=tagPath[tagPath.find("[") + 1:tagPath.find("]")]
    tagRoot=tagPath.rstrip('/labValue') 
    
    # Strip off the path and get just the name of the UDT
    biasName = tagRoot[:len(tagRoot)]
    biasName = biasName[biasName.rfind('/') + 1:]
    
    valueOk, rawBias = validateConditions(tagRoot, newValue, biasName)
    if not(valueOk):
        print "The conditions are not OK"
        return
    
    proportionalGain = system.tag.read(tagRoot + '/proportionalGain').value
    integralGain = system.tag.read(tagRoot + '/integralGain').value
    previousError = system.tag.read(tagRoot + '/previousError').value
    sampleTime = system.tag.read(tagRoot + '/sampleTime').value
    lastBiasValue = system.tag.read(tagRoot + '/biasValue').value
    print "  Last Bias: ", lastBiasValue
    
    if lastBiasValue == None:
        log.error("Unable to calculate a bias value for %s because the bias has not been initialized." % (tagPath))
        return
    
    biasValue = proportionalGain * (newValue - previousError) + integralGain * sampleTime * newValue + lastBiasValue
    print "Calculated the new biased value as: %f from %f and %f" % (biasValue, newValue, lastBiasValue)
    
    system.tag.write(tagRoot + '/biasValue', biasValue)
    system.tag.write(tagRoot + '/previousError', newValue)
    
    # Write this nicely calculated value to either the DCS or the PHD historian
    txt = writeBiasToExternalSystem(tagProvider, tagRoot, biasName, biasValue, sampleTime)
    msg = "%s %f that is the PID bias for %s" % (txt, biasValue, biasName)
    insertMessage(MESSAGE_QUEUE_KEY, QUEUE_INFO, msg)

'''
This was formerly the bias-update() methods for the root class bias-value.
It basically makes sure that the conditions are OK to calculate a new bias.
'''
def validateConditions(tagRoot, labValue, biasName):
    print "Tag Root: ", tagRoot
    historyProvider = getHistoryProvider()
    rateOfChangeLimit = system.tag.read(tagRoot + '/rateOfChangeLimit')
    if not (rateOfChangeLimit.quality.isGood()) or rateOfChangeLimit.value == None:
        msg = "The rate of change limit is either bad or does not have a value.  The validity of the lab sample <%s> cannot be verified, aborting new bias calculations." % (biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return False, 0.0

    '''
    Fetch the model value from history.  Get the value of the model at the time that the lab data sample was collected
    '''
    modelDeadTimeMinutes = system.tag.read(tagRoot + '/modelDeadTimeMinutes')
    if not (modelDeadTimeMinutes.quality.isGood()) or modelDeadTimeMinutes.value < 0.0:
        msg = "The Model dead time for <%s> is either bad or less than 0.0.  Overriding with 0.0 minutes." % (biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        modelDeadTimeMinutes = 0.0
    else:
        modelDeadTimeMinutes = modelDeadTimeMinutes.value
    deadTime = round(modelDeadTimeMinutes * 60.0)
    
    averageWindowMinutes = system.tag.read(tagRoot + '/averageWindowMinutes')
    if not (averageWindowMinutes.quality.isGood()) or averageWindowMinutes.value <= 0.0:
        msg = "The average window for <%s> is either bad or less than 0.0.  Overriding with 0.0 minutes." % (biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        averageWindowMinutes = 0.0
    else:
        averageWindowMinutes = averageWindowMinutes.value
        
    # Convert to seconds and divide by two so the history interval is the window size divided by 2.
    averageWindow = round( averageWindowMinutes * 60.0 / 2.0)
    
    sampleTime = system.tag.read(tagRoot + '/labSampleTime')
    if not (sampleTime.quality.isGood()):
        msg = "The sample time for <%s> is bad.  Aborting new bias calculations." % (biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return False, 0.0
    sampleTime = sampleTime.value
    
    # Now we have all of the parameters we need to query the model value.  We either get the model value at the time of the sample or get the 
    # average model value during a time window centered around the sample time.
    modelTagPath="%s/Model" % (tagRoot)
    if averageWindow == 0:      
        ds = system.tag.queryTagHistory(paths=[modelTagPath], startDate=sampleTime, rangeMinutes=1, aggregationMode="SimpleAverage", returnSize=1)
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
        ds = system.tag.queryTagHistory(paths=[modelTagPath], startDate=startDate, endDate=endDate, aggregationMode="SimpleAverage", returnSize=1)
        if ds.rowCount == 0:
            msg = "Unable to acquire an average value for the model <%s> from <%s> to <%s> for bias value %s." % (modelTagPath, str(startDate), str(endDate), biasName)
            log.warn(msg)
            insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
            return False, 0.0
        modelValue = ds.getValueAt(0,1)
        log.tracef("The average value of the model <%s> from <%s> to <%s> was <%f>", modelTagPath, str(startDate), str(endDate), modelValue)

    '''
    Check if this bias should be multiplicative
    '''
    multiplicative = system.tag.read(tagRoot + 'multiplicative').value
    if multiplicative:
        #TODO call DB-SPECIAL-VAL-CHK
        rawBias = labValue / modelValue
    else:
        rawBias = labValue - modelValue
    
    '''
    The final check is to check the rate of change
    '''
    oldRawBias = system.tag.read(tagRoot + '/rawBias')
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
    system.tag.write(tagRoot + '/rawBias', rawBias)
    return True, rawBias

def biasControlInUse():
    return True

def writeBiasToExternalSystem(tagProvider, tagRoot, biasName, biasValue, sampleTime):
    
    writeEnabled = system.tag.read("[" + tagProvider + "]/Configuration/LabData/labFeedbackWriteEnabled").value
    if not(writeEnabled):
        msg = "Unable to write bias value <%f> for <%s> because writes are inhibited for Lab Bias Feedback." % (biasValue, biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return "Unable to write lab bias because lab feedback writes are inhibited!"
    
    writeEnabled = system.tag.read("[" + tagProvider + "]/Configuration/Common/writeEnabled").value
    if not(writeEnabled):
        msg = "Unable to write bias value <%f> for <%s> because all writes are globally inhibited." % (biasValue, biasName)
        log.warn(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return "Unable to write lab bias because all writes are globally inhibited!"
    
    serverType = system.tag.read(tagRoot + 'biasTargetServerType')
    if not (serverType.quality.isGood()) or (serverType.value not in ["OPC", "HDA"]):
        msg = "Unable to write bias value <%f> for <%s> because the Target Server Type is bad or not one of OPC or HDA" % (biasValue, biasName)
        log.error(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, msg)
        return "Error writing bias because target server type was bad or not one of OPC or HDA"
    serverType = serverType.value
    
    serverName = system.tag.read(tagRoot + 'biasTargetServerName')
    if not (serverName.quality.isGood()) or serverName.value == None:
        msg = "Unable to write bias value <%f> for <%s> because the Target Server name is bad or not specified" % (biasValue, biasName)
        log.error(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, msg)
        return "Error writing bias because target server name was bad or missing"
    serverName = serverName.value
    
    itemId = system.tag.read(tagRoot + 'biasTargetItemId')
    if not (itemId.quality.isGood()) or itemId.value == None:
        msg = "Unable to write bias value <%f> for <%s> because the Target Item-Id is bad or not specified" % (biasValue, biasName)
        log.error(msg)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_ERROR, msg)
        return "Error writing bias because the target Item-Id was bad or missing"
    itemId = itemId.value
    
    if serverType == "HDA":
        returnQuality = system.opchda.insert(serverName, itemId, biasValue, sampleTime, 192)
        if returnQuality.isGood():
            txt = "Successfully wrote bias value <%f> at <%s> to <%s> via OPC-HDA for <%s>." % (biasValue, str(sampleTime), itemId, biasName)
        else:
            txt = "Error writing bias value <%f> at <%s> to <%s> via OPC-HDA for <%s>." % (biasValue, str(sampleTime), itemId, biasName)
    else:
        returnQuality = system.opc.writeValue(serverName, itemId, biasValue)
        if returnQuality.isGood():
            txt = "Successfully wrote bias value <%f> to <%s> for <%s>." % (biasValue, itemId, biasName)
        else:
            txt = "Error writing bias value <%f> to <%s> for <%s>." % (biasValue, itemId, biasName)
        
    return txt