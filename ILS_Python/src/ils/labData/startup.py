'''
Created on Apr 28, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.labData")

def gateway():
    from ils.labData.version import version
    version = version()
    log.info("Starting Lab Data Toolkit gateway version %s" % (version))
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    createTags("[" + provider + "]")

def client():
    from ils.labData.version import version
    version = version()
    log.info("Initializing the Lab Data Toolkit client version %s" % (version))

def createTags(tagProvider):
    print "Creating Lab Data configuration tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/LabData/"

    data.append([path, "pollingEnabled", "Boolean", "True"])
    data.append([path, "standardDeviationsToValidityLimits", "Float8", "4.5"])
    data.append([path, "manualEntryPermitted", "Boolean", "False"])
    data.append([path, "communicationHealthy", "Boolean", "True"])
    data.append([path, "labDataWriteEnabled", "Boolean", "True"])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)