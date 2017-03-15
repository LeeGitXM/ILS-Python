'''
Created on Mar 11, 2017

@author: phass
'''

import system
log = system.util.getLogger("com.ils.labData.labFeedback")
MESSAGE_QUEUE_KEY = "LABFEEDBACK"
from ils.queue.message import insert as insertMessage
from ils.constants.constants import QUEUE_INFO, QUEUE_ERROR, QUEUE_WARNING

def exponentialFilter(tagPath, previousValue, newValue, initialchange): 
    newValue = newValue.value
    
    # Find the root of the tag by stripping off LabData   
    tagRoot=tagPath.rstrip('labValue')
    
    # Strip off the path and get just the name of the UDT
    biasName = tagRoot[:len(tagRoot)-1]
    biasName = biasName[biasName.rfind('/') + 1:]
    
    log.infof("Calculating an exponentially filtered bias for %s (%s)", biasName, tagRoot)
    valueOk, rawBias = validateConditions(tagRoot, newValue, biasName)
    if not(valueOk):
        print "The conditions are not OK"
        return
    
    filterConstant = system.tag.read(tagRoot + 'filterConstant').value
    lastBiasValue = system.tag.read(tagRoot + 'biasValue').value
    print "  Last Bias: ", lastBiasValue
    
    if lastBiasValue == None:
        log.error("Unable to calculate a bias value for %s because the bias has not been initialized." % (tagPath))
        return
    
    # Calculate the exponentially filtered bias
    biasValue = filterConstant * rawBias + (1.0 - filterConstant) * lastBiasValue
    log.tracf("Calculated the new biased value as: %f from %f and %f using a filter constant of %f", biasValue, newValue, lastBiasValue, filterConstant)
    
    system.tag.write(tagRoot + '/biasValue', biasValue)
    
    #TODO - Write this nicely calculated value to either the DCS or phdLog
    
    #TODO - Incorporate the success / failure of the write into the message
    msg = "%f that is the exponential filtered bias for %s" % (biasValue, biasName)
    insertMessage(MESSAGE_QUEUE_KEY, QUEUE_INFO, msg)

def pidFilter(tagPath, previousValue, newValue, initialchange):
    print "In pidFilter..."
    
    newValue = newValue.value
    
    # Find the root of the tag by stripping off LabData   
    tagRoot=tagPath.rstrip('labData') 
    
    # Strip off the path and get just the name of the UDT
    biasName = tagRoot[:len(tagRoot)-1]
    biasName = biasName[biasName.rfind('/') + 1:]
    
    valueOk, rawBias = validateConditions(tagRoot, newValue, biasName)
    if not(valueOk):
        print "The conditions are not OK"
        return
    
    proportionalGain = system.tag.read(tagRoot + 'proportionalGain').value
    integralGain = system.tag.read(tagRoot + 'integralGain').value
    previousError = system.tag.read(tagRoot + 'previousError').value
    sampleTime = system.tag.read(tagRoot + 'sampleTime').value
    lastBiasValue = system.tag.read(tagRoot + 'biasValue').value
    print "  Last Bias: ", lastBiasValue
    
    if lastBiasValue == None:
        log.error("Unable to calculate a bias value for %s because the bias has not been initialized." % (tagPath))
        return
    
    biasValue = proportionalGain * (newValue - previousError) + integralGain * sampleTime * newValue + lastBiasValue
    print "Calculated the new biased value as: %f from %f and %f" % (biasValue, newValue, lastBiasValue)
    
    system.tag.write(tagRoot + '/biasValue', biasValue)
    system.tag.write(tagRoot + '/previousError', newValue)
    
    
    #TODO - Write this nicely calculated value to either the DCS or phdLog
    
    #TODO - Incorporate the success / failure of the write into the message
    msg = "%f that is the PID bias for %s" % (biasValue, biasName)
    insertMessage(MESSAGE_QUEUE_KEY, QUEUE_INFO, msg)

'''
This was formerly the bias-update() methods for the root class bias-value.
It basically makes sure that the conditions are OK to calculate a new bias.
'''
def validateConditions(tagRoot, labValue, biasName):
    rateOfChangeLimit = system.tag.read(tagRoot + 'rateOfChangeLimit').value
    valueOk = True
    
    '''
    Fetch the model value from history.  Get the value of the model at the time that the lab data sample was collected
    '''
     
    deadTime = round(system.tag.read(tagRoot + 'modelDeadTimeMinutes').value * 60.0)
    averageWindow = round(system.tag.read(tagRoot + 'averageWindowMinutes').value * 60.0)
    
    if averageWindow == 0:
        print "Get the value of the model at the lab sample time"
    else:
        print "Get the average value of the model over the average window centered around the sample time"
    
    modelValue = 1.2


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
    oldRawBias = system.tag.read(tagRoot + 'rawBias').value
    if abs(rawBias - oldRawBias) > rateOfChangeLimit:
        msg = "Last lab sample for %s is suspicious.  Raw bias is %f and the old raw bias is %f.  Aborting new bias calculations." % (biasName, rawBias, oldRawBias)
        insertMessage(MESSAGE_QUEUE_KEY, QUEUE_WARNING, msg)
        return False, rawBias
    
    return valueOk, rawBias

def biasControlInUse():
    return True