'''
Created on Nov 18, 2014

@author: Pete
'''

import system
from ils.common.user import isOperator
from ils.common.menuBar import getMenuBar, removeUnwantedConsoles, removeNonOperatorMenus,\
    removeUnwantedMenus

'''
Client startup is contingent on a relationship between the username and the post name.
For an operator, the username is the same as the post name.
For an engineer there will not be a matching post.  
'''
def client():    
    print "In ils.common.startup.client()"
    
    # Create client loggers
    log = system.util.getLogger("com.ils.recipeToolkit.ui")
    log.info("Initializing...")
    
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
    data.append([path, "historyTagProvider", "String", "XOMHistory"])
    data.append([path, "memoryTagLatencySeconds", "Float4", "2.5"])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
    
    # Create E-Mail related tags which can be used any toolkit.  These tags are to configure the e-mail
    # server that sends the emails
    data = []
    path = tagProvider + "Configuration/Email/"

    data.append([path, "password", "String", ""])
    data.append([path, "smtp", "String", ""])
    data.append([path, "username", "String", ""])

    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
    