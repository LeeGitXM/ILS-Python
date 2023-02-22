'''
Created on Feb 2, 2015

@author: Pete
'''

import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from time import sleep

from ils.log import getLogger
log = getLogger(__name__)

def gateway(tagProvider, isolationTagProvider, database):
    
    from ils.common.util import isWarmboot
    if isWarmboot(tagProvider):
        log.info("Bypassing Symbolic AI startup for a warmboot")
        return 
    
    from ils.diagToolkit.version import version
    version, revisionDate = version()
    projectName = system.project.getProjectName()
    log.info("---------------------------------------------------------")
    log.info("Starting Symbolic AI version %s - %s for project <%s>" % (version, revisionDate, projectName))
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
                    log.warnf("Aborting the Symbolic AI startup because the database is still bad after 10 checks.")
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

def client(tagProvider, database):
    from ils.diagToolkit.version import version
    version, releaseDate = version()
    log.info("Initializing the Symbolic AI client version %s" % (version))

def createTags(tagProvider):
    print "Creating Symbolic AI configuration tags..."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/DiagnosticToolkit/"

    data.append([path, "diagnosticToolkitWriteEnabled", "Boolean", "True"])
    data.append([path, "downloadConfirmationEnabled", "Boolean", "False"])
    data.append([path, "diagnosticAgeInterval", "Int8", "5"])
    data.append([path, "freshnessToleranceSeconds", "Float8", "5.0"])
    data.append([path, "freshnessTimeoutSeconds", "Float8", "10.0"])
    data.append([path, "itemIdPrefix", "String", ""])
    data.append([path, "manualChangeUsernames", "DataSet", None])
    data.append([path, "vectorClampMode", "String", "Implement"])
    data.append([path, "writeTextRecommendationsToLogbook", "Boolean", "False"])
    data.append([path, "zeroChangeThreshold", "Float8", "0.00005"])
    
    path = tagProvider + "Configuration/DiagnosticToolkit/ApplicationExtensions/"
    data.append([path, "Delete", "String", "ils.extensions.appProperties.delete"])
    data.append([path, "GetAux", "String", "ils.extensions.appProperties.getAux"])
    data.append([path, "Rename", "String", "ils.extensions.appProperties.rename"])
    data.append([path, "Save", "String", "ils.extensions.appProperties.save"])
    data.append([path, "SetAux", "String", "ils.extensions.appProperties.setAux"])
    data.append([path, "GetList", "String", "ils.extensions.appProperties.getList"])
    
    path = tagProvider + "Configuration/DiagnosticToolkit/FamilyExtensions/"
    data.append([path, "Delete", "String", "ils.extensions.famProperties.delete"])
    data.append([path, "GetAux", "String", "ils.extensions.famProperties.getAux"])
    data.append([path, "Rename", "String", "ils.extensions.famProperties.rename"])
    data.append([path, "Save", "String", "ils.extensions.famProperties.save"])
    data.append([path, "SetAux", "String", "ils.extensions.famProperties.setAux"])
    
    path = tagProvider + "Configuration/DiagnosticToolkit/DiagramExtensions/"
    data.append([path, "Delete", "String", "ils.extensions.diaProperties.delete"])
    data.append([path, "GetAux", "String", "ils.extensions.diaProperties.getAux"])
    data.append([path, "Rename", "String", "ils.extensions.diaProperties.rename"])
    data.append([path, "Save", "String", "ils.extensions.diaProperties.save"])
    data.append([path, "SetAux", "String", "ils.extensions.diaProperties.setAux"])
          
    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
    