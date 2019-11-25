'''
  Gateway scope extension functions dealing with Family instances.
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
#
# The production an isolation databases need to be kept structurally in-synch.
# Apply these changes against both instances.
def add(uuid):
    db = handler.getProductionDatabase()
    addToDatabase(uuid,db)
    db = handler.getIsolationDatabase()
    addToDatabase(uuid,db)
    
def addToDatabase(uuid,db):
    # These get() functions search up the hierarchy
    app = handler.getApplication(uuid)
    SQL = "SELECT ApplicationId FROM DtApplication WHERE Application = '%s' " % (app.getName())
    applicationId = system.db.runScalarQuery(SQL, db)
    
    if applicationId < 0:
        log.error("Unable to find the application id of an application named <%s> while inserting a new family" % (app.getName()))
        return
    
    fam = handler.getFamily(uuid)
    SQL = "INSERT INTO DtFamily(ApplicationId, Family, FamilyPriority) "\
        " values (%s, '%s', 0.0) " % (applicationId, fam.getName())
    
    print "Fam.insert: SQL =", SQL
    system.db.runUpdateQuery(SQL,db)
    
def clone(uuid1,uuid2):
    pass

def delete(uuid):
    db = handler.getProductionDatabase()
    deleteFromDatabase(uuid,db)
    db = handler.getIsolationDatabase()
    deleteFromDatabase(uuid,db)
    
def deleteFromDatabase(uuid,db):
    fam = handler.getFamily(uuid)
    SQL = "DELETE FROM DtFamily " \
          " WHERE Family = '%s'" \
          % (fam.getName())
    
    print "Fam.delete: SQL =", SQL
    system.db.runUpdateQuery(SQL,db)

# For an update we need both the old and new names
def update(name,uuid):
    db = handler.getProductionDatabase()
    updateInDatabase(name,uuid,db)
    db = handler.getIsolationDatabase()
    updateInDatabase(name,uuid,db)

def updateInDatabase(name,uuid,db):
    fam = handler.getFamily(uuid)
    SQL = "UPDATE DtFamily " \
          " SET Family = '%s'" \
          " WHERE Family = '%s'" \
          % (fam.getName(), name)
    
    log.trace("Family update: SQL = %s" % (SQL))
    rows = system.db.runUpdateQuery(SQL, db)
    if rows != 1:
        log.error("%d rows were updated, exactly 1 was expected (%s)" % (rows, SQL))