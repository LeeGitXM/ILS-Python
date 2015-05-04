'''
Created on Feb 2, 2015

@author: Pete
'''

import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit")

def gateway():
    from ils.diagToolkit.version import version
    version = version()
    log.info("Starting Diagnostic Toolkit gateway version %s" % (version))
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    createTags("[" + provider + "]")

def client():
    from ils.diagToolkit.version import version
    version = version()
    log.info("Initializing the Diagnostic toolkit client version %s" % (version))

def createTags(tagProvider):
    print "Creating Diagnostic Toolkit configuration tags..."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/DiagnosticToolkit/"

    data.append([path, "vectorClampMode", "String", "Implement"])
    data.append([path, "itemIdPrefix", "String", ""])
          
    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
    