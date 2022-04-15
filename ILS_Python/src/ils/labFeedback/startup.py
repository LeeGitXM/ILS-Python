'''
Created on Mar 21, 2017

@author: phass

The only thing we do to start LabFeedback is to make sure the write enabled tag exists.  If making it make sure it is False.
'''

import system
from ils.log import getLogger
log = getLogger(__name__)
EXPONENTIAL_FILTER_BIAS_UDT = "Lab Bias/Lab Bias Exponential Filter"
PID_BIAS_UDT = "Lab Bias/Lab Bias PID"

def gateway(tagProvider, isolationTagProvider):
    
    from ils.common.util import isWarmboot
    if isWarmboot(tagProvider):
        log.info("Bypassing Lab Feedback Toolkit startup for a warmboot")
        return 
    
    from ils.labFeedback.version import version
    version, revisionDate = version()
    log.info("---------------------------------------------------------")
    log.info("Starting Lab Data Feedback Toolkit gateway version %s - %s" % (version, revisionDate))
    log.info("---------------------------------------------------------")

    createTags("[" + tagProvider + "]")
    createTags("[" + isolationTagProvider + "]")

    initializeTags(tagProvider)

def createTags(tagProvider):
    log.tracef("Creating Lab Feedback configuration tags....")
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/LabFeedback/"

    data.append([path, "labFeedbackWriteEnabled", "Boolean", "False"])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)

def initializeTags(provider):
    log.tracef("Initializing Bias feedback UDTs...")
    
    parentPath = "[%s]LabData" % (provider)
    for udtParentType in [EXPONENTIAL_FILTER_BIAS_UDT, PID_BIAS_UDT]:
        filters = {"tagType": "UDT_INST", "typeId": udtParentType, "recursive": True}
        udts = system.tag.browse(parentPath, filters)
        
        log.infof("   Discovered %d %s UDTs...", len(udts), udtParentType)
        
        for udt in udts:
            udtPath = str(udt['fullPath'])
            log.infof("Initializing: %s", udtPath)
            biasName = udtPath[udtPath.rfind("/") + 1:]
            
            # Read the memory tags
            vals = system.tag.readBlocking([udtPath + "/biasTargetItemId", udtPath + "/biasTargetServerName",  udtPath + "/biasValue"])
            itemId=vals[0].value
            opcServer=vals[1].value
            localBias=vals[2]
            log.infof("   Reading DCS bias from %s %s", opcServer, itemId)

            dcsBias = system.opc.readValue(opcServer, itemId) 
            log.infof("   Local bias: %s", str(localBias))
            log.infof("   DCS Bias:   %s", str(dcsBias))
            
            if localBias.quality.isGood() and dcsBias.quality.isGood() and localBias.value != None and dcsBias.value != None:
                localBias = localBias.value
                dcsBias = dcsBias.value
                
                if abs(localBias - dcsBias) > 0.01:
                    if udtParentType == PID_BIAS_UDT:
                        print "   ...initializing a PID bias..."
                    
                    log.tracef("   writing %f to the rawBias and biasValue...", dcsBias)
                    system.tag.writeBlocking([udtPath + "/rawBias", udtPath + "/biasValue"], [dcsBias, dcsBias])
            else:
                log.warnf("Unable to initialize %s because the quality of the local bias or the DCS bias was bad or the value was None", biasName)
                system.tag.writeBlocking([udtPath + "/rawBias", udtPath + "/biasValue"], [0.0, 0.0])
                
    log.info("...done initializing Bias Feedback UDTs!")
