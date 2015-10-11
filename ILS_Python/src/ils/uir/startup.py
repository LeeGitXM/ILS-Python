'''
Created on Oct 9, 2015

@author: Pete
'''

import system

def gateway():
    # Create gateway loggers
    log = system.util.getLogger("com.ils.uir")
    
    from ils.uir.version import version
    version, revisionDate = version()
    log.info("Starting UIR modules version %s - %s" % (version, revisionDate))
    
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    createTags("[" + provider + "]", log)

def createTags(tagProvider, log):
    print "Creating UIR configuration tags...."

    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/UIR/"

    # This should create an empty dataset tag, but IA has not added it to their API yet.
#    data.append([path, "EmailList", "Dataset", ""])
    data.append([path, "EmailList", "String", ""])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
