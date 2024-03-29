'''
Created on Jan 10, 2017

@author: phass
'''

import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.sfc")

def gateway(tagProvider, isolationTagProvider):
    from ils.common.util import isWarmboot
    if isWarmboot():
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
    log.info("---------------------------------------------------------")
    log.info("Initializing the SFC client")
    log.info("---------------------------------------------------------")
    system.tag.write("[Client]SFC Browser/Chart View State", 0)
    system.tag.write("[Client]SFC Browser/Selected Chart Path", "")
    system.tag.write("[Client]SFC Browser/Selected Chart Row", -1)
    system.tag.write("[Client]SFC Browser/Selected Step", -1)

def createTags(tagProvider):
    log.infof("Creating SFC configuration tags...")
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/SFC"

    data.append([path, "sfcMaxDownloadGuiAdjustment", "Float4", "1.7"])
    data.append([path, "sfcRecipeDataMigrationEnabled", "Boolean", "False"])
    data.append([path, "sfcRecipeDataShowProductionOnly", "Boolean", "True"])
    data.append([path, "sfcWriteEnabled", "Boolean", "True"])
    
          
    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)