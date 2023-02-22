'''
This module can be used as a template for a site specific startup.  
If any modifications are made to this module, then it should be moved out of the ILS-PYTHON folder so that it will not be overwritten
as new updates are installed.  It can be coipied to external Python in a new folder or into project or shared Python.  The tkSite table must be updated to point
to the 

Created on Jun 18, 2018

@author: phass
'''

import system
from ils.config.common import getHistoryProvider
from ils.config.common import getProductionDatabaseFromInternalDatabase, getIsolationDatabaseFromInternalDatabase
from ils.config.common import getProductionTagProviderFromInternalDatabase, getIsolationTagProviderFromInternalDatabase
from ils.log import getLogger
log = getLogger(__name__)

def client():
    print "***********************************************"
    print "*** Running the SITE client startup script. ***"
    print "***********************************************"
    
    projectName = system.util.getProjectName()
    payload = {"project": projectName, "isolationMode": False}
    tagProvider = system.util.sendRequest(projectName, "getTagProvider", payload)
    database = system.util.sendRequest(projectName, "getDatabase", payload)
        
    import ils.recipeToolkit.startup as recipeToolkitStartup
    recipeToolkitStartup.client(tagProvider, database)

    import ils.diagToolkit.startup as diagToolkitStartup
    diagToolkitStartup.client(tagProvider, database)
    

def gateway():
    projectName = system.util.getProjectName()
    
    log.infof("------------------------------")
    log.infof("In %s.gateway() for project <%s>", __name__, projectName)
    log.infof("------------------------------")
    
    tagProvider = getProductionTagProviderFromInternalDatabase(projectName)
    isolationTagProvider = getIsolationTagProviderFromInternalDatabase(projectName)
    database = getProductionDatabaseFromInternalDatabase(projectName)
    isolationDatabase = getIsolationDatabaseFromInternalDatabase(projectName)
    
    log.infof("Checking for a warmboot...")
    from ils.common.util import isWarmboot
    if isWarmboot(tagProvider):
        log.info("Bypassing Symbolic AI startup for a warmboot")
        return 
    
    log.infof("...getting version...")
    from ils.demo.version import version
    version, revisionDate = version()
    
    log.infof("In %s.gateway(): Starting Symbolic AI version %s - %s for project <%s>", __name__, version, revisionDate, projectName)

    historyProvider = getHistoryProvider()

    #------------------------------------------------------------------------------------------------
    # Putting this in its own function allows the other startups to proceed while this sleeps.
    def doit(tagProvider=tagProvider, isolationTagProvider=isolationTagProvider, historyProvider=historyProvider, database=database, 
             isolationDatabase=isolationDatabase, projectName=projectName, log=log):
        log.infof("Starting the deferred startup for project <%s>...", projectName)

        # Start all of the packages used at the site
        
        import ils.recipeToolkit.startup as recipeToolkitStartup
        recipeToolkitStartup.gateway(tagProvider, isolationTagProvider)
    
        log.warnf("Skipping startup of SymbolicAi until it has been ported to 8.x!")
        #import ils.diagToolkit.startup as diagToolkitStartup
        #diagToolkitStartup.gateway(tagProvider, isolationTagProvider, database)
        
        import ils.uir.startup as uirStartup
        uirStartup.gateway(tagProvider, isolationTagProvider)
        
        import ils.labData.startup as labDataStartup
        labDataStartup.gateway(tagProvider, isolationTagProvider)
        
        import ils.labFeedback.startup as labFeedbackStartup
        labFeedbackStartup.gateway(tagProvider, isolationTagProvider)
        
        import ils.common.startup as commonStartup
        commonStartup.gatewayCommon(tagProvider, isolationTagProvider) 
        
        import ils.sfc.startup as sfcStartup
        sfcStartup.gateway(tagProvider, isolationTagProvider)
        
        import ils.diagToolkit.startup as diagToolkitStartup
        diagToolkitStartup.gateway(tagProvider, isolationTagProvider, database)
        
        import ils.dataPump.startup as dataPumpStartup
        dataPumpStartup.gateway(tagProvider, isolationTagProvider)

        log.infof("...done with deferred startup for project <%s>!", projectName)

    #---------------------------------------------------------------------------------------------------------


    '''
    I used to finish the startup asynchronously... but that makes things much harder to debug a multi project gateway
    '''
    #system.util.invokeAsynchronous(doit)
    doit()
    
