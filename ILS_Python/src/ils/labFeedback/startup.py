'''
Created on Mar 21, 2017

@author: phass

The only thing we do to start LabFeedback is to make sure the write enabled tag exists.  If making it make sure it is False.
'''

import system
log = system.util.getLogger("com.ils.labFeedback")
EXPONENTIAL_FILTER_BIAS_UDT = "Lab Bias/Lab Bias Exponential Filter"
PID_BIAS_UDT = "Lab Bias/Lab Bias PID"

def gateway(provider):
    from ils.labFeedback.version import version
    version, revisionDate = version()
    log.info("---------------------------------------------------------")
    log.info("Starting Lab Data Feedback Toolkit gateway version %s - %s" % (version, revisionDate))
    log.info("---------------------------------------------------------")
    from ils.common.config import getTagProvider

    initializeTags(provider)

def createTags(tagProvider):
    print "Creating Lab Feedback configuration tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/LabFeedback/"

    data.append([path, "labFeedbackWriteEnabled", "Boolean", "False"])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)

def initializeTags(provider):
    log.info("Initializing Bias feedback UDTs...")
    
    parentPath = "[%s]LabData" % (provider)
    for udtParentType in [EXPONENTIAL_FILTER_BIAS_UDT, PID_BIAS_UDT]:

        udts = system.tag.browseTags(
            parentPath=parentPath, 
            tagType="UDT_INST", 
            udtParentType=udtParentType,
            recursive=True)
        
        log.tracef("   Discovered %d %s UDTs...", len(udts), udtParentType)
        
        for udt in udts:
            log.infof("Initializing: %s", udt.path)
            udtPath = udt.path
            biasName = udtPath[udtPath.rfind("/") + 1:]
            
            # Read the memory tags
            vals = system.tag.readAll([udtPath + "/biasTargetItemId", udtPath + "/biasTargetServerName",  udtPath + "/biasValue"])
            itemId=vals[0].value
            opcServer=vals[1].value
            localBias=vals[2]
            log.tracef("   Reading DCS bias from %s %s", opcServer, itemId)

            dcsBias = system.opc.readValue(opcServer, itemId) 
            log.tracef("   Local bias: %s", str(localBias))
            log.tracef("   DCS Bias:   %s", str(dcsBias))
            
            if localBias.quality.isGood() and dcsBias.quality.isGood():
                localBias = localBias.value
                dcsBias = dcsBias.value
                
                if abs(localBias - dcsBias) > 0.01:
                    if udtParentType == PID_BIAS_UDT:
                        print "   ...initializing a PID bias..."
                    
                    log.tracef("   writing %f to the rawBias and biasValue...", dcsBias)
                    system.tag.writeAll([udtPath + "/rawBias", udtPath + "/biasValue"], [dcsBias, dcsBias])
            else:
                log.warnf("Unable to initialize %s because the quality of the local bias or the DCS bias was bad", biasName)
    log.info("...done initializing Bias Feedback UDTs!")
