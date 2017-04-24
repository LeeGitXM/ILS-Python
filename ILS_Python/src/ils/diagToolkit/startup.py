'''
Created on Feb 2, 2015

@author: Pete
'''

import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit")

def gateway():
    from ils.diagToolkit.version import version
    version, revisionDate = version()
    log.info("---------------------------------------------------------")
    log.info("Starting Diagnostic Toolkit gateway version %s - %s" % (version, revisionDate))
    log.info("---------------------------------------------------------")
    from ils.common.config import getTagProvider, getDatabase
    provider = getTagProvider()
    database = getDatabase()
    
    createTags("[" + provider + "]")
    
    #
    # Reset the database diagnosis and recommendations
    #
    
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
          
    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
    