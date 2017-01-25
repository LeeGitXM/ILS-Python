'''
Created on Jan 10, 2017

@author: phass
'''

import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.sfc")

def gateway():
    from ils.sfc.version import version
    version, releaseDate = version()
    log.info("---------------------------------------------------------")
    log.info("Starting SFC Python version %s - %s" % (version, releaseDate))
    log.info("---------------------------------------------------------")
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    createTags("[" + provider + "]")

def client():
    from ils.sfc.version import version
    version, releaseDate = version()
    log.info("---------------------------------------------------------")
    log.info("Initializing the SFC client version %s" % (version, releaseDate))
    log.info("---------------------------------------------------------")

def createTags(tagProvider):
    print "Creating SFC configuration tags..."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/SFC/"

    data.append([path, "sfcWriteEnabled", "Boolean", "True"])
          
    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)