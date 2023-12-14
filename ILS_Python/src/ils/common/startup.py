'''
Created on Nov 18, 2014

@author: Pete
'''

import system, string, time
from ils.config.common import getTagProviderFromInternalDatabase, getDatabaseFromInternalDatabase, getIsolationDatabaseFromInternalDatabase, getUserLibDir
from ils.common.user import isOperator
from ils.common.menuBar import getMenuBar, clearConsoles, removeNonOperatorMenus, removeUnwantedMenus, ConsoleMenus
from ils.common.error import catchError
from ils.io.util import readTag, writeTag

from ils.log import getLogger
log = getLogger(__name__)

IMPLEMENT = "IMPLEMENT"
PLAN = "PLAN"

'''
These are the startup dispatchers.  They are called by the project startup scripts and then read the site specific startup scripts
name and calls them.
'''
def gateway():
    log.infof("In %s.gateway()", __name__)
    
    projectName = system.util.getProjectName()
    log.infof("Starting project %s...", projectName)
    
    setLogLevels()
    
    ''' Call a special function that will wait until BLT is ready and running - this goes into a wait loop until it succeeds. '''
    log.infof("Getting database and tag providers...")
    tagProvider = getTagProviderFromInternalDatabase(projectName)
    productionDatabase = getDatabaseFromInternalDatabase(projectName)
    isolationDatabase = getIsolationDatabaseFromInternalDatabase(projectName)
    log.infof("   Production Tag Provider: %s", tagProvider)
    
    updateDatabaseSchema(tagProvider, productionDatabase)
    updateDatabaseSchema(tagProvider, isolationDatabase)
    
    pds = system.db.runQuery("select * from TkSite")
    if len(pds) <> 1:
        log.errorf("Found %d records in TkSite, exactly one is required - aborting startup!", len(pds))
        return
    
    record = pds[0]
    siteName = record["SiteName"]
    gatewayStartupScript = record["GatewayStartupScript"]
    
    log.infof("Running gateway startup script named <%s> for TkSite.SiteName: <%s>", gatewayStartupScript, siteName)
    
    separator=string.rfind(gatewayStartupScript, ".")
    packagemodule=gatewayStartupScript[0:separator]
    separator=string.rfind(packagemodule, ".")
    package = packagemodule[0:separator]
    module  = packagemodule[separator+1:]

    exec("import %s" % (package))
    exec("from %s import %s" % (package,module))

    eval(gatewayStartupScript)()
    
    log.infof("...completed %s.gateway()", __name__)


def setLogLevels():
    print "Setting log levels..."

    ''' This throws an error, maybe it is running too early??  PH 5/19/21 '''
    #system.util.setLoggingLevel("ils.common.watchdog", "off")


def client():
    log.infof("In %s.client()", __name__)
    
    '''
    Every site needs to run this, which sets the menus, so save the user from having to call this.
    '''
    clientCommon()
    
    '''
    Set the default values of the client tags that drive the log viewer
    '''
    from ils.logging.viewer import clientStartup
    clientStartup()
    
    from ils.sfc.startup import client as sfcClientStartup
    sfcClientStartup()
    
    project = system.util.getProjectName()
    log.infof("The project is: %s (ils.common.startup.client)", project)
    
    pds = system.db.runQuery("select * from TkSite")
    if len(pds) <> 1:
        log.errorf("Found %d records in TkSite, exactly one is required - aborting client startup!", len(pds))
        return
    
    record = pds[0]
    siteName = record["SiteName"]
    clientStartupScript = record["ClientStartupScript"]
    
    log.infof("Running client startup script named <%s> for %s", clientStartupScript, siteName)
    
    separator=string.rfind(clientStartupScript, ".")
    packagemodule=clientStartupScript[0:separator]
    separator=string.rfind(packagemodule, ".")
    package = packagemodule[0:separator]
    module  = packagemodule[separator+1:]

    exec("import %s" % (package))
    exec("from %s import %s" % (package,module))

    eval(clientStartupScript)()
    
    log.infof("...completed %s.client()", __name__)



'''
Client startup is contingent on a relationship between the username and the post name.
For an operator, the username is the same as the post name.
For an engineer there will not be a matching post.  
'''
def clientCommon():    
    log.infof("In %s.clientCommon()", __name__)
    
    from javax.swing import ToolTipManager
    ToolTipManager.sharedInstance().setDismissDelay(30000)
    ToolTipManager.sharedInstance().setInitialDelay(300)
    
    isolationMode = system.tag.readBlocking(["[Client]Isolation Mode"])[0].value
    log.infof("The currentIsolationMode is: %s", str(isolationMode))
    
    if isolationMode:
        ''' This should trigger the tag change handler which will read the values from the Internal database '''
        log.infof("   ...tickling the Isolation Mode client tag...")
        system.tag.writeBlocking(["[Client]Isolation Mode"], [False])
    else:
        ''' 
        Isolation Mode is set correctly, but that doesn't mean that the tag provider and database 
        tags are set correctly.  So set them without touching the isolation mode. 
        '''
        from ils.config.client import _isolationModeChangeHandler as setIsolationModeTags
        setIsolationModeTags(False)  
    
    username = system.security.getUsername()
    rows = system.db.runScalarQuery("select count(*) from TkPost where post = '%s'" % (username)) 
    if rows > 0:
        writeTag("[Client]Post", username)
    else:
        writeTag ("[Client]Post", "Test")

    window=None
    SQL = "select C.WindowName from TkConsole C, TkPost P where P.PostId = C.PostId and P.Post = '%s' order by C.priority" % (username)
    pds = system.db.runPrepQuery(SQL)

    if len(pds) == 0:
        ''' log the fact that we didn't find a console window '''
        log.infof("Unable to find a console window for user <%s>", username)

    for record in pds:
        windowName=record['WindowName']
        print "Opening the ", windowName
        window=system.nav.openWindow(windowName)
        system.nav.centerWindow(window)

    # I need some window open in order to remove the menu until Chuck can tell me how to get the menubar when there isn't a window
    if window == None:
        window=system.nav.openWindow("Admin/Versions", {"StartupMode": True})
        system.nav.centerWindow(window)
    
    '''
    With Ignition 8 where each site has it's own site specific project we do not have all of the consoles in the project 
    or in the menu so there is nothing that needs to be removed.
    '''
    
    '''
    if window != None:
        menubar = getMenuBar(window)
        clearConsoles(menubar)
        ConsoleMenus(menubar)
        removeUnwantedMenus(menubar, "XOM") #The second argument is NOT The project name, it is the project type
    '''
    
    '''
    If this is an operator, then remove the admin menu and the View->Consoles menu.
    '''
    if isOperator():
        if window != None:
            menubar = getMenuBar(window)
            removeNonOperatorMenus(menubar)


def gatewayCommon(tagPprovider, isolationTagProvider):  
    from ils.common.version import version
    version, revisionDate = version()
    log.infof("Starting common modules version %s - %s", version, revisionDate)
    
    createTags("[" + tagPprovider + "]", log)
    createTags("[" + isolationTagProvider + "]", log)


def createTags(tagProvider, log):
    log.tracef("Creating common configuration tags....")
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    
    path = tagProvider + "Configuration/Common/"
    
    data.append([path, "dbPruneDays", "Int8", "365"])
    data.append([path, "dbUpdateStrategy", "String", "implement"])
    data.append([path, "historyTagProvider", "String", "XOMHistory"])
    data.append([path, "ioMinimumDifference", "Float8", "0.00001"])
    data.append([path, "ioMinimumRelativeDifference", "Float8", "0.00001"])
    data.append([path, "memoryTagLatencySeconds", "Float4", "2.5"])
    data.append([path, "ocAlertCallback", "String", ""])
    data.append([path, "opcTagLatencySeconds", "Float4", "5.0"])
    data.append([path, "opcPermissiveLatencySeconds", "Float4", "4.0"])
    data.append([path, "printingAllowed", "Boolean", "True"])
    data.append([path, "reportHome", "String", "e:"])
    data.append([path, "simulateHDA", "Boolean", "False"])
    data.append([path, "sqcPlotScaleFactor", "Float4", "0.75"])
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
    createConfigurationTags(ds, log)
    
    
def updateDatabaseSchema(tagProvider, db):
    log.infof("In %s.updateDatabaseSchema()", __name__)
    try:
        dbVersions = []
        dbVersions.append({"versionId": 1, "version": "1.1r0", "filename": "update_1.1r0.sql", "releaseDate": "2020-04-01"})
        dbVersions.append({"versionId": 2, "version": "1.2r0", "filename": "update_1.2r0.sql", "releaseDate": "2020-06-22"})
        dbVersions.append({"versionId": 3, "version": "1.3r0", "filename": "update_1.3r0.sql", "releaseDate": "2020-09-14"})
        dbVersions.append({"versionId": 4, "version": "1.4r0", "filename": "update_1.4r0.sql", "releaseDate": "2020-10-25"})
        dbVersions.append({"versionId": 5, "version": "1.5r0", "filename": "update_1.5r0.sql", "releaseDate": "2021-04-15"})
        dbVersions.append({"versionId": 6, "version": "1.6r0", "filename": "update_1.6r0.sql", "releaseDate": "2021-07-04"})
        dbVersions.append({"versionId": 7, "version": "1.7r0", "filename": "update_1.7r0.sql", "releaseDate": "2021-08-31"})
        dbVersions.append({"versionId": 8, "version": "1.8r0", "filename": "update_1.8r0.sql", "releaseDate": "2021-10-08"})
        dbVersions.append({"versionId": 9, "version": "1.9r0", "filename": "update_1.9r0.sql", "releaseDate": "2022-01-24"})
        dbVersions.append({"versionId": 12, "version": "2.2r0", "filename": "update_2.1r0.sql", "releaseDate": "2022-09-01"})
        dbVersions.append({"versionId": 13, "version": "2.3r0", "filename": "update_2.3r0.sql", "releaseDate": "2022-09-01"})
        
        projectName = system.util.getProjectName()
        log.infof("In %s.updateDatabaseSchema()for project: %s - DB: %s", __name__, projectName, db)
        
        tagPath = "[%s]Configuration/Common/dbUpdateStrategy" % (tagProvider)
        exists = system.tag.exists(tagPath)
        if exists:
            strategy = string.upper(readTag(tagPath).value)
        else:
            log.warnf("Exiting updateDatabaseSchema because %s does not exist, (hopefully this is the first startup after an install and the tag will be created later)", tagPath)
            return
        
        ''' Use the magic function in the SFC module that tells us where Ignition is installered and therefore where the SQL scripts are. '''
        homeDir = getUserLibDir(projectName)
        homeDir = homeDir + "/database/"
        
        currentId = readCurrentDbVersionId(projectName, strategy, db)
        log.infof("The current database version is %d (%s)", currentId, strategy)
        
        for dbVersion in dbVersions:
            versionId = dbVersion.get("versionId", None)
            version = dbVersion.get("version", None)
            filename = dbVersion.get("filename", None)
            filename = homeDir + filename
            releaseDate = dbVersion.get("releaseDate", None)
            
            if currentId < versionId:
                installDbUpdate(versionId, version, filename, releaseDate, strategy, db)
                
        log.infof("...done updating database schema!")
    except:
        txt = "Caught an error while updating the database schema for %s" % (db)
        txt = catchError(__name__, txt)
        log.errorf("%s", str(txt))
   

def readCurrentDbVersionId(projectName, strategy, db):
    ''' Check if the table exists'''
    log.tracef("Checking if the version table exists....")
    SQL = "select count(*) FROM sys.Tables WHERE  Name = 'Version' AND Type = 'U' "
    count = system.db.runScalarQuery(SQL, db)
    
    if count == 0:
        log.infof("*** The VERSION table doesn't exist! ***")
        createVersionTable(projectName, strategy, db)
        currentId = -1
    else:
        ''' 
        Check if this was an early version of the table that didn't have all of the columns. 
        The final version of the Version table didn't get implemented until version 1.2.
        If the VersionId column exists then we are at least version 1 (1.2r0).
        If it doesn't exist then I need to figure out if we ar version 0 or version 1.
        If we are version 0, then just drop the table and initialize the data.
        I can check for DtApplication.ApplicationUUID to see if we are at 1.1.
        If we are at 1.1r0, then alter the version Table.
        '''
        log.tracef("...the version table exists, check if the versionId column exists....")
        SQL = "SELECT COUNT(*)   FROM INFORMATION_SCHEMA.COLUMNS  WHERE TABLE_NAME = 'Version' and COLUMN_NAME = 'VersionId' "
        count = system.db.runScalarQuery(SQL, db)
    
        if count == 0:
            log.infof("...the versionId column does not exist, we are either version 0 or 1, check if the applicationUUID column exists...")
            ''' If the VersionId column doesn't exist, then we have an early version of the table, either 0 or 1. '''
            SQL = "SELECT COUNT(*)   FROM INFORMATION_SCHEMA.COLUMNS  WHERE TABLE_NAME = 'DtApplication' and COLUMN_NAME = 'ApplicationUUID' "
            count = system.db.runScalarQuery(SQL, db)
            if count == 0:
                currentId = 0
                log.infof("...it DOES NOT exist, so we are version 0!")
                if strategy == IMPLEMENT:
                    system.db.runUpdateQuery("drop table Version", db)
                    createVersionTable(projectName, strategy, db)
                    system.db.runUpdateQuery("Insert into Version (VersionId, Version, ReleaseDate, InstallDate) values (0, '1.0r0', '2019-10-01', '2019-10-01')", db)
            else:
                currentId = 1
                log.infof("...it exists, so we are version 1!")
                if strategy == IMPLEMENT:
                    system.db.runUpdateQuery("drop table Version", db)
                    createVersionTable(projectName, strategy, db)
                    system.db.runUpdateQuery("Insert into Version (VersionId, Version, ReleaseDate, InstallDate) values (0, '1.0r0', '2019-10-01', '2019-10-01') ", db)
                    system.db.runUpdateQuery("Insert into Version (VersionId, Version, ReleaseDate, InstallDate) values (1, '1.1r0', '2020-04-01', '2020-04-01') ", db)
        else:
            log.tracef("...it is the latest version table, select the max version...")
            SQL = "select max(versionId) from Version"
            currentId = system.db.runScalarQuery(SQL, db)
            log.infof("The current database version is: %d", currentId)
    
    return currentId


def createVersionTable(projectName, strategy, db):
    homeDir = getUserLibDir(projectName)
    filename = homeDir + "/database/createVersion.sql"

    log.infof("Creating Version table")
    
    ''' Read the sql commands from the SQL file '''
    sql = system.file.readFileAsString(filename)
    cmds = sql.split(";")
    for cmd in cmds:
        cmd = cmd.strip()
        if cmd <> "":
            log.infof("Command: <%s>", cmd)
            if strategy == IMPLEMENT:
                system.db.runUpdateQuery(cmd, db)


def installDbUpdate(versionId, version, filename, releaseDate, strategy, db):
    log.infof("**************************************************************")
    log.infof("** Updating database %s to version %d - %s - %s (%s)", db, versionId, version, releaseDate, strategy)
    log.infof("**************************************************************")
    
    def runCommand(SQL, db):
        ''' Run the SQL update inside a try - except so that we keep going even if we hit an error ''' 
        try:
            system.db.runUpdateQuery(cmd, db)
        except:
            txt = "Error running database update on %s - %s" % (db, cmd)
            txt = catchError(__name__, txt)
            log.errorf(txt)
        else:
            log.infof("The command was successfully processed!")


    ''' Read the sql commands from the SQL file '''
    sql = system.file.readFileAsString(filename)
    cmds = sql.split(";")
    for cmd in cmds:
        commentStart = cmd.find("/*")
        commentEnd = cmd.find("*/")
        
        if commentStart >= 0 and commentEnd > commentStart:
            cmd = cmd[commentEnd+2:]
            
        cmd = cmd.strip()
        cmd = cmd.lstrip()
            
        if cmd <> "":
            log.infof("SQL Command: <%s>", cmd)
            if strategy == IMPLEMENT:
                runCommand(cmd, db)
    
    ''' Add a record to the version table'''
    if strategy == IMPLEMENT:
        SQL = "Insert into Version (VersionId, Version, ReleaseDate, InstallDate) values (%d, '%s', '%s', GETDATE())" % (versionId, version, releaseDate)
        log.infof("Final SQL Command: <%s>", SQL)
        system.db.runUpdateQuery(SQL, db)
