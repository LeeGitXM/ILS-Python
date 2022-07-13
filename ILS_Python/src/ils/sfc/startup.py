'''
Created on Jan 10, 2017

@author: phass
'''

import system
from ils.log import getLogger
log = getLogger(__name__)

def gateway(tagProvider, isolationTagProvider):
    from ils.common.util import isWarmboot
    if isWarmboot(tagProvider):
        log.info("Bypassing SFC Toolkit startup for a warmboot")
        return 
    
    from ils.sfc.version import version
    version, releaseDate = version()
    log.info("---------------------------------------------------------")
    log.info("Starting SFC Toolkit version %s - %s" % (version, releaseDate))
    log.info("---------------------------------------------------------")

    createTags("[" + tagProvider + "]")
    createTags("[" + isolationTagProvider + "]")

def client():
    from ils.sfc.version import version
    version, releaseDate = version()
    log.infof("---------------------------------------------------------")
    log.infof("Initializing the SFC client version %s - %s" % (version, str(releaseDate)))
    log.infof("---------------------------------------------------------")
    tagPaths = ["[Client]SFC Browser/Chart View State", 
                "[Client]SFC Browser/Selected Chart Path",
                "[Client]SFC Browser/Selected Chart Row",
                "[Client]SFC Browser/Selected Step"]
    vals = [0, "", -1, -1]
    system.tag.writeBlocking(tagPaths, vals)

def createTags(tagProvider):
    log.tracef("Creating SFC configuration tags...")
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/SFC/"

    data.append([path, "sfcMaxDownloadGuiAdjustment", "Float4", "1.7"])
    data.append([path, "sfcRecipeDataMigrationEnabled", "Boolean", "False"])
    data.append([path, "sfcRecipeDataShowProductionOnly", "Boolean", "True"])
    data.append([path, "sfcWriteEnabled", "Boolean", "True"])
    
    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)