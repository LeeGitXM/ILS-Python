'''
Created on Jul 14, 2017

@author: phass
'''

import system
log = system.util.getLogger("com.ils.dataPump")

def gateway(tagProvider, isolationTagProvider):
    from ils.labFeedback.version import version
    version, revisionDate = version()
    log.info("---------------------------------------------------------")
    log.info("Starting Data Pump Toolkit ")
    log.info("---------------------------------------------------------")

    createTags("[" + tagProvider + "]")
    createTags("[" + isolationTagProvider + "]")

def createTags(tagProvider):
    print "Creating Data pump configuration tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/Data Pump/"

    data.append([path, "Command", "String", ""])
    data.append([path, "data", "DataSet", ""])
    data.append([path, "lineNumber", "Int8", "0"])
    data.append([path, "simulationState", "String", ""])
    data.append([path, "timeDelay", "Int8", "60"])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
