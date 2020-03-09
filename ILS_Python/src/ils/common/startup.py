'''
Created on Nov 18, 2014

@author: Pete
'''

import system, string
from ils.common.user import isOperator
from ils.common.menuBar import getMenuBar, removeUnwantedConsoles, removeNonOperatorMenus,\
    removeUnwantedMenus
log = system.util.getLogger("com.ils.common.startup")

'''
These are the startup dispatchers.  They are called by the project startup scripts and then read the site specific startup scripts
name and calls them.
'''
def gateway():
    log.infof("In %s.gateway()", __name__)
    
    project = system.util.getProjectName()
    log.infof("The project is: %s (ils.common.startup.gateway)", project)
    
    pds = system.db.runQuery("select * from TkSite")
    if len(pds) <> 1:
        print "Found %d records in TkSite, exactly one is required!"
        return
    
    record = pds[0]
    siteName = record["SiteName"]
    gatewayStartupScript = record["GatewayStartupScript"]
    
    log.infof("Running gateway startup script named <%s> for %s", gatewayStartupScript, siteName)
    
    separator=string.rfind(gatewayStartupScript, ".")
    packagemodule=gatewayStartupScript[0:separator]
    separator=string.rfind(packagemodule, ".")
    package = packagemodule[0:separator]
    module  = packagemodule[separator+1:]

    exec("import %s" % (package))
    exec("from %s import %s" % (package,module))

    eval(gatewayStartupScript)()
    
    print "...completed %s.gateway()" % (__name__)


def client():
    print "In %s.client()" % (__name__)
    
    '''
    Every site needs to run this, which sets the menus, so save the user from having to call this.
    '''
    clientCommon()
    
    project = system.util.getProjectName()
    print "The project is: %s (ils.common.startup.client)" % (project)
    
    pds = system.db.runQuery("select * from TkSite")
    if len(pds) <> 1:
        print "Found %d records in TkSite, exactly one is required!" % (len(pds))
        return
    
    record = pds[0]
    siteName = record["SiteName"]
    clientStartupScript = record["ClientStartupScript"]
    
    print "Running client startup script named <%s> for %s" % (clientStartupScript, siteName)
    
    separator=string.rfind(clientStartupScript, ".")
    packagemodule=clientStartupScript[0:separator]
    separator=string.rfind(packagemodule, ".")
    package = packagemodule[0:separator]
    module  = packagemodule[separator+1:]

    exec("import %s" % (package))
    exec("from %s import %s" % (package,module))

    eval(clientStartupScript)()
    
    print "...completed %s.gateway()" % (__name__)



'''
Client startup is contingent on a relationship between the username and the post name.
For an operator, the username is the same as the post name.
For an engineer there will not be a matching post.  
'''
def clientCommon():    
    log.infof("In %s.clientCommon()", __name__)
    
    username = system.security.getUsername()
    rows = system.db.runScalarQuery("select count(*) from TkPost where post = '%s'" % (username)) 
    if rows > 0:
        system.tag.write("[Client]Post", username)
    else:
        system.tag.write("[Client]Post", "Test")

    SQL = "select C.WindowName from TkConsole C, TkPost P where P.PostId = C.PostId and P.Post = '%s' order by C.priority" % (username)
    pds = system.db.runPrepQuery(SQL)
    window=None
    for record in pds:
        windowName=record['WindowName']
        print "Opening the ", windowName
        window=system.nav.openWindow(windowName)
        system.nav.centerWindow(window)

    # I need some window open in order to remove the menu until Chuck can tell me how to get the menubar when there isn't a window
    if window == None:
        window=system.nav.openWindow("Admin/Versions")
        system.nav.centerWindow(window)
    
    '''
    Remove unwanted consoles.  Remember that there is a single project that contains all of the consoles for the Baton Rouge complex.
    This determines which consoles are appropriate for the site by querying the console definition table in the site specific database.
    '''
    if window != None:
        menubar = getMenuBar(window)
        removeUnwantedConsoles(menubar)
        removeUnwantedMenus(menubar, "XOM") #The second argument is NOT The project name, it is the project type

    '''
    If this is an operator, then remove the admin menu and the View->Consoles menu.
    '''
    if isOperator():
        if window != None:
            menubar = getMenuBar(window)
            removeNonOperatorMenus(menubar)


def gatewayCommon(tagPprovider, isolationTagProvider):
    # Create gateway loggers
    log = system.util.getLogger("com.ils.common")
    
    from ils.common.version import version
    version, revisionDate = version()
    log.info("Starting common modules version %s - %s" % (version, revisionDate))
    
    createTags("[" + tagPprovider + "]", log)
    createTags("[" + isolationTagProvider + "]", log)


def createTags(tagProvider, log):
    print "Creating common configuration tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    
    path = tagProvider + "Configuration/Common/"
    
    data.append([path, "dbPruneDays", "Int8", "365"])
    data.append([path, "historyTagProvider", "String", "XOMHistory"])
    data.append([path, "memoryTagLatencySeconds", "Float4", "2.5"])
    data.append([path, "ocAlertCallback", "String", ""])
    data.append([path, "opcTagLatencySeconds", "Float4", "5.0"])
    data.append([path, "opcPermissiveLatencySeconds", "Float4", "4.0"])
    data.append([path, "printingAllowed", "Boolean", "True"])
    data.append([path, "reportHome", "String", "e:"])
    data.append([path, "simulateHDA", "Boolean", "False"])
    data.append([path, "writeEnabled", "Boolean", "True"])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
    
    # Create E-Mail related tags which can be used any toolkit.  These tags are to configure the e-mail
    # server that sends the emails
    data = []
    path = tagProvider + "Configuration/Email/"

    data.append([path, "smtpProfile", "String", "mySmtpServer"])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
    