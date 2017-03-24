'''
Created on Mar 21, 2017

@author: phass

The only thing we do to start LabFeedback is to make sure the write enabled tag exists.  If making it make sure it is False.
'''

import system
log = system.util.getLogger("com.ils.labFeedback")

def gateway():
    from ils.labFeedback.version import version
    version, revisionDate = version()
    log.info("---------------------------------------------------------")
    log.info("Starting Lab Data Feedback Toolkit gateway version %s - %s" % (version, revisionDate))
    log.info("---------------------------------------------------------")
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    createTags("[" + provider + "]")

def createTags(tagProvider):
    print "Creating Lab Feedback configuration tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/LabFeedback/"

    data.append([path, "labFeedbackWriteEnabled", "Boolean", "False"])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)