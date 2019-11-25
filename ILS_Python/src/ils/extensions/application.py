  '''
  Gateway scope extension functions dealing with Application instances.
  I believe this to be obsolete 05/10/2016 - clc
'''
import system
import com.ils.blt.gateway.PythonRequestHandler as PythonRequestHandler
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit.SQL")

handler = PythonRequestHandler()

# These methods are called in Gateway scope. In this scope 
# SQL calls should use the handler to acquire the database 
# connections. The handler is a com.ils.blt.gateway.proxy.ProxyHandler 

# This called immediately after the mouse gesture to create a new application, which
# is before the user gets to configure the real name and the console and any other 
# required attributes.  So need a scheme for selecting a default console.
#
# The production an isolation databases need to be kept structurally in-synch.
# Apply these changes against both instances.
def add(uuid):
    db = handler.getProductionDatabase()
    addToDatabase(uuid,db)
    db = handler.getIsolationDatabase()
    addToDatabase(uuid,db)
    
def addToDatabase(uuid,db):
    app = handler.getApplication(uuid)
    consoleId=fetchDefaultConsole(db)
    SQL = "INSERT INTO DtApplication(Application, ConsoleId) " \
          " VALUES('%s', %s)" \
          % (app.getName(), str(consoleId))
    
    log.trace("Inserting application: SQL = <%s>" % (SQL))
    system.db.runUpdateQuery(SQL,db)
    
def clone(uuid1,uuid2):
    pass

def delete(uuid):
    db = handler.getProductionDatabase()
    deleteFromDatabase(uuid,db)
    db = handler.getIsolationDatabase()
    deleteFromDatabase(uuid,db)
    
def deleteFromDatabase(uuid,db):
    app = handler.getApplication(uuid)
    if app != None:
        SQL = "DELETE FROM DtApplication " \
            " WHERE Application = '%s'" \
            % (app.getName())
    
        log.trace("Deleting application: %s" % SQL)
        system.db.runUpdateQuery(SQL,db)
    else:
        log.error("Error deleting application: %s did not exist" % (uuid))

# For an update we need both the old and new names
def update(uuid):
    db = handler.getProductionDatabase()
    updateInDatabase(uuid,db)
    db = handler.getIsolationDatabase()
    updateInDatabase(uuid,db)
    
def updateInDatabase(name,uuid,db):
    app = handler.getApplication(uuid)
    SQL = "UPDATE DtApplication " \
          " SET Application = '%s'" \
          " WHERE Application = '%s'" \
          % (app.getName(), name)
    
    log.trace("Updating Application: SQL = <%s>" % (SQL))
    rows = system.db.runUpdateQuery(SQL, db)
    if rows != 1:
        log.error("%d rows were updated, exactly 1 was expected (%s)" % (rows, SQL))

# There really isn't a way to specify a default console, so just fetch the first one
def fetchDefaultConsole(db):
    SQL = "select min(consoleId) from DtConsole"
    consoleId = system.db.runScalarQuery(SQL, db)
    return consoleId 