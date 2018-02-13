'''
Created on Feb 2, 2015

@author: Pete
'''

import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from time import sleep
log = LogUtil.getLogger("com.ils.diagToolkit")

def gateway(tagProvider, isolationTagProvider, database):
    
    from ils.common.util import isWarmboot
    if isWarmboot():
        log.info("Bypassing Diagnostic Toolkit startup for a warmboot")
        return 
    
    from ils.diagToolkit.version import version
    version, revisionDate = version()
    log.info("---------------------------------------------------------")
    log.info("Starting Diagnostic Toolkit gateway version %s - %s" % (version, revisionDate))
    log.info("---------------------------------------------------------")
    
    createTags("[" + tagProvider + "]")
    createTags("[" + isolationTagProvider + "]")


    # Make sure the database is ready, if this startup is following a reboot, Ignition can be ready before the database.
    sleepSeconds = 5
    for i in range(10):
        ds = system.db.getConnectionInfo(database)
        pds = system.dataset.toPyDataSet(ds)
        if len(pds) == 1:
            status = ds.getValueAt(0, "Status")        
            log.infof("The status of %s is: %s", database, status)
            if status == "Valid":
                break
            else:
                if i == 10:
                    log.warnf("Aborting the diagnostic toolkit startup because the database is still bad after 10 checks.")
                    return
                log.info("Sleeping...")
                sleep(sleepSeconds)
                log.info("...waking")
                sleepSeconds = sleepSeconds * 2
                if sleepSeconds > 30:
                    sleepSeconds = 30
            log.errorf("Error: Unable to determine the status of database <%s>", database)

    log.info("...Database is OK, resetting...")
    # Reset the database diagnosis and recommendations
    from ils.diagToolkit.finalDiagnosis import resetRecommendations, resetOutputs
    from ils.diagToolkit.common import resetFinalDiagnosis, resetDiagnosisEntries

    resetFinalDiagnosis(log, database)
    resetDiagnosisEntries(log, database)
    resetRecommendations("%", log, database)
    resetOutputs("%", log, database)

def client():
    from ils.diagToolkit.version import version
    version, releaseDate = version()
    log.info("Initializing the Diagnostic toolkit client version %s" % (version))

def createTags(tagProvider):
    print "Creating Diagnostic Toolkit configuration tags..."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/DiagnosticToolkit/"

    data.append([path, "vectorClampMode", "String", "Implement"])
    data.append([path, "itemIdPrefix", "String", ""])
    data.append([path, "diagnosticToolkitWriteEnabled", "Boolean", "True"])
    data.append([path, "downloadConfirmationEnabled", "Boolean", "False"])
    data.append([path, "diagnosticAgeInterval", "Int8", "5"])
    data.append([path, "freshnessToleranceSeconds", "Float8", "5.0"])
    data.append([path, "freshnessTimeoutSeconds", "Float8", "10.0"])
          
    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
    