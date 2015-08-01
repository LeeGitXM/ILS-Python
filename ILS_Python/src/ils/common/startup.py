'''
Created on Nov 18, 2014

@author: Pete
'''

import system

def client():    
    print "In ils.common.startup.client()"
    
    # Create client loggers
    log = system.util.getLogger("com.ils.recipeToolkit.ui")
    log.info("Initializing...")


def gateway():
    # Create gateway loggers
    log = system.util.getLogger("com.ils.common")
    
    from ils.common.version import version
    version, revisionDate = version()
    log.info("Starting common modules version %s - %s" % (version, revisionDate))
    
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    createTags("[" + provider + "]", log)

def createTags(tagProvider, log):
    print "Creating common configuration tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/Common/"

    data.append([path, "writeEnabled", "Boolean", "True"])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
    