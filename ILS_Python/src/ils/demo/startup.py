'''
Created on Jun 18, 2018

@author: phass
'''

import system
log = system.util.getLogger("com.ils.demo")

def client():
    print "***********************************************"
    print "*** Running the Demo client startup script. ***"
    print "***********************************************"


    from ils.common.config import getTagProvider, getIsolationTagProvider, getHistoryProvider, getDatabase
         
    tagProvider = getTagProvider()
    isolationTagProvider = getIsolationTagProvider()
    historyProvider = getHistoryProvider()
    database = getDatabase()
    
    print "Production Tag Provider: ", tagProvider
    print " Isolation Tag Provider: ", isolationTagProvider
    print "       History Provider: ", historyProvider
    print "               Database: ", database

    system.tag.write("[Client]Database", database)
    system.tag.write("[Client]Tag Provider", tagProvider)
    
    
    import ils.recipeToolkit.startup as recipeToolkitStartup
    recipeToolkitStartup.client()

    import ils.diagToolkit.startup as diagToolkitStartup
    diagToolkitStartup.client()
    

def gateway():
    
    #------------------------------------------------------------------------------------------------
    # Putting this in its own function allows the other startups to proceed while this sleeps.
    def doit(log=log):
        from ils.common.config import getTagProvider, getIsolationTagProvider, getHistoryProvider, getDatabase
        
        # Give the modules time to complete initialization.  Delays are always a bad / tricky thing.
        # I'm not sure if this is really required, but it sure makes it easier to follow the log messages during startup
        # where BLT, SFC, and lab data are all intermingled.
        import time
        time.sleep(5) 
        
        log = system.util.getLogger("com.ils.demo")
        log.info("Starting the deferred startup...")
        
        try:            
            tagProvider = getTagProvider()
            isolationTagProvider = getIsolationTagProvider()
            historyProvider = getHistoryProvider()
            database = getDatabase()
        except:
            print "Unable to obtain tag provider programatically, using hard coded values!"
            tagProvider = "Production"
            isolationTagProvider = "Isolation"
            historyProvider = "History"
            database = "Production"

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
        Now perform very specific startup for the demo
        '''
        createTags("[" + tagProvider + "]", log)
        createTags("[" + isolationTagProvider + "]", log)

        print "Done with Demo startup..."

    #---------------------------------------------------------------------------------------------------------

    from ils.common.util import isWarmboot
    if isWarmboot():
        log.info("Bypassing Vistalon startup for a warmboot")
        return 
    
    from ils.demo.version import version
    version, revisionDate = version()
    
    log.info("Starting Vistalon version %s - %s" % (version, revisionDate))
    system.util.invokeAsynchronous(doit)
    

def createTags(tagProvider, log):
    print "Creating global constant memory tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []

