'''
This module can be used as a template for a site specific startup.  
If any modifications are made to this module, then it should be moved out of the ILS-PYTHON folder so that it will not be overwritten
as new updates are installed.  It can be coipied to external Python in a new folder or into project or shared Python.  The tkSite table must be updated to point
to the 

Created on Jun 18, 2018

@author: phass
'''

import system, time
from ils.common.config import getTagProvider, getIsolationTagProvider, getHistoryProvider, getDatabase, getIsolationDatabase
from ils.log import getLogger
log =getLogger(__name__)

def client():
    print "***********************************************"
    print "*** Running the SITE client startup script. ***"
    print "***********************************************"

    tagProvider = getTagProvider()
    isolationTagProvider = getIsolationTagProvider()
    historyProvider = getHistoryProvider()
    database = getDatabase()

    system.tag.write("[Client]Database", database)
    system.tag.write("[Client]Tag Provider", tagProvider)
        
    import ils.recipeToolkit.startup as recipeToolkitStartup
    recipeToolkitStartup.client()

    import ils.diagToolkit.startup as diagToolkitStartup
    diagToolkitStartup.client()
    

def gateway():
    from ils.common.util import isWarmboot
    if isWarmboot():
        log.info("Bypassing Symbolic AI startup for a warmboot")
        return 
    
    from ils.demo.version import version
    version, revisionDate = version()
    
    log.info("Starting Symbolic AI version %s - %s" % (version, revisionDate))
    
    tagProvider, isolationTagProvider, historyProvider, database, isolationDatabase = getDbAndTagProviderFromBltModule()

    '''
    This used to be done in an aynchronous thread, the only thing that can be really time consuming is restoring Lab Data, maybe something in 
    Diag Toolkit IDK.  But all of a sudden I am having trouble creating the configuration tags.  So grab the CPU and get er done PH 7/30/2021
    '''
    #------------------------------------------------------------------------------------------------
    # Putting this in its own function allows the other startups to proceed while this sleeps.
    '''
    def doit(tagProvider=tagProvider, isolationTagProvider=isolationTagProvider, historyProvider=historyProvider, database=database, isolationDatabase=isolationDatabase, log=log):
        log.info("Starting the deferred startup...")
    '''

    # Start all of the packages used at the site
    
    import ils.recipeToolkit.startup as recipeToolkitStartup
    recipeToolkitStartup.gateway(tagProvider, isolationTagProvider)

    import ils.diagToolkit.startup as diagToolkitStartup
    diagToolkitStartup.gateway(tagProvider, isolationTagProvider, database)
    
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
    
    import ils.dataPump.startup as dataPumpStartup
    dataPumpStartup.gateway(tagProvider, isolationTagProvider)
    
    '''
    Now perform very specific startup for the client
    '''

    log.tracef("Done with core startup...")

    #---------------------------------------------------------------------------------------------------------

'''
    system.util.invokeAsynchronous(doit)
'''  

def getDbAndTagProviderFromBltModule():
    
    def getter():
        log.infof("...getting db and tagProviders from BLT...")
        try:
            tagProvider = getTagProvider()
            isolationTagProvider = getIsolationTagProvider()
            historyProvider = getHistoryProvider()
            database = getDatabase()
            isolationDatabase = getIsolationDatabase()
        except:
            log.tracef("...BLT module isn't quite ready, sleeping...")
            time.sleep(5)
            tagProvider = None
            isolationTagProvider = None
            historyProvider = None
            database = None
            isolationDatabase = None
            
        return tagProvider, isolationTagProvider, historyProvider, database, isolationDatabase
    
    tagProvider, isolationTagProvider, historyProvider, database, isolationDatabase = getter()
    while tagProvider == None or isolationTagProvider == None or historyProvider == None or database == None or isolationDatabase == None:
        tagProvider, isolationTagProvider, historyProvider, database, isolationDatabase = getter()
        
    return tagProvider, isolationTagProvider, historyProvider, database, isolationDatabase