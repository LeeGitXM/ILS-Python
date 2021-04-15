'''
  Gateway scope extension functions dealing with Family instances.
'''
import system
from ils.diagToolkit.common import fetchApplicationId
import com.ils.blt.gateway.ControllerRequestHandler as ControllerRequestHandler
handler = ControllerRequestHandler.getInstance()

'''
These run in Gateway scope
'''
def delete(familyUUID):
    '''
    This is called when the user deletes an family from the designer.  I hope that it already called the delete method for the diagrams in the family
    from the bottom up so that we don't hit a FK constraint here.
    
    I'd like to use the application name, which is guarenteed to be unique by the database, but I think that the gateway has already deleted the application so the getApplicationName()
    call fails - at least that is the only explanation I can come up with!  So instead use the UUID to delete the application.
    '''
    from ils.log.LogRecorder import LogRecorder
    log = LogRecorder(__name__ + ".delete")

    log.infof("In %s.delete() with family uuid: %s", __name__, familyUUID)
    db = handler.getProductionDatabase()
        
    SQL = "delete from DtFamily where FamilyUUID = '%s'" % (familyUUID)
    rows = system.db.runUpdateQuery(SQL, db)
    if rows == 1:
        log.infof("Successfully deleted family with UUID <%s> from the database!", familyUUID)
    elif rows == 0:
        log.errorf("Unable to delete family with UUID <%s> from the database", familyUUID)
    else:
        log.warnf("Multiple rows <%d> were deleted from the database for family with UUID <%s>", rows, familyUUID)

    
# The production an isolation databases need to be kept structurally in-synch.
# Apply these changes against both instances.
def rename(uuid,oldName,newName):
    
    def renameInDatabase(uuid,oldName,newName,db):
        SQL = "UPDATE DtFamily SET FamilyName= '%s' WHERE FamilyName = '%s'" % (newName,oldName)
        system.db.runUpdateQuery(SQL,db)
    
    from ils.log.LogRecorder import LogRecorder
    log = LogRecorder(__name__ + ".rename")
    
    log.infof("In %s.rename()", __name__)
    db = handler.getProductionDatabase()
    
    renameInDatabase(uuid,oldName,newName,db)
    
    db = handler.getIsolationDatabase()
    renameInDatabase(uuid,oldName,newName,db)

   
def save(familyUUID):
    '''
    This method IS called when they do a save from the Designer. 
    Although this is initiated from Designer - this runs in Gateway scope!
     
    It should really insert a new record into the DB for a new application, but I don't have enough info here to
    do anything (and I don't know how to get it).  This isn't really a show stopper because the engineer needs to
    open the big configuration popup Swing dialog which will insert a record if it doesn't already exist.
    '''
    from ils.log.LogRecorder import LogRecorder
    log = LogRecorder(__name__ + ".save")
    log.infof("In %s.save()", __name__)
    
    db = handler.getProductionDatabase()
    
    from system.ils.blt.diagram import getFamilyName, getApplicationName
    familyName = getFamilyName(familyUUID)
    log.tracef("...familyName: %s", familyName)
    
    applicationName = getApplicationName(familyUUID)
    log.tracef("...applicationName: %s", applicationName)
    
    applicationId = fetchApplicationId(applicationName, db)
    log.tracef("...the id for <%s> is %s", applicationName, str(applicationId))
    
    SQL = "select FamilyId from DtFamily where familyUUID = '%s'" % (familyUUID)
    familyId = system.db.runScalarQuery(SQL, db)

    if familyId == None:
        '''
        Take some extra steps here to see if this is an old legacy family that was saved before we added familyUUID to the database.
        If we find a family where the application and family name match then update the Family UUID.
        '''
        SQL = "select familyId from DtFamily where applicationId = %d and FamilyName = '%s'" % (applicationId, familyName)
        familyId = system.db.runScalarQuery(SQL, db)
        if familyId == None:
            SQL = "insert into DtFamily (ApplicationId, FamilyName, FamilyUUID, FamilyPriority) "\
                "values (%s, '%s', '%s', 0)" % (applicationId, familyName, familyUUID)
            log.tracef("...SQL: %s,", SQL)
            familyId = system.db.runUpdateQuery(SQL, db, getKey=1)
            log.tracef("Inserted a new family with id: %d", familyId)
        else:
            SQL = "update DtFamily set FamilyUUID = '%s' where ApplicationId = %d and FamilyName = '%s'  "\
                 % (familyUUID, applicationId, familyName)
            log.tracef("...SQL: %s,", SQL)
            system.db.runUpdateQuery(SQL, db)
            log.tracef("...updated the familyUUID for a legacy family!")
            
    else:
        SQL = "update DtFamily set FamilyName = '%s', applicationId = %s where familyId = %s" % (familyName, applicationId, familyId)
        log.tracef("...SQL: %s,", SQL)
        rows = system.db.runUpdateQuery(SQL, db)
        log.tracef("...updated %d rows in DtFamily for %s", rows, familyName)

'''
These methods are  called in Designer scope. However, we may be using either the
production or isolation databases. The Gateway makes this call when converting into
 isolation mode. 
'''

# The aux data structure is a Python list of three dictionaries. These are:
# properties, lists and maplists. Of these, the family only uses properties.
# 
# Fill the aux structure with values from the database
def getAux(uuid, aux, db):
    from ils.log.LogRecorder import LogRecorder
    log = LogRecorder(__name__ + ".getAux")
    log.infof("In %s.getAux()", __name__)
    
    applicationName  = handler.getApplicationName(uuid)
    familyName = handler.getFamilyName(uuid)
    
    properties = aux[0]
    
    log.tracef("     Application name: %s", applicationName)
    log.tracef("     Family name: %s", familyName)
    
    SQL = "SELECT FAM.Description,FAM.FamilyPriority "\
          " FROM DtFamily FAM,DtApplication APP "\
          " WHERE FAM.applicationId = APP.applicationId "\
          "   AND FAM.familyName = '%s'"\
          "   AND APP.ApplicationName = '%s' " % (familyName, applicationName)
    ds = system.db.runQuery(SQL,db)
    for rec in ds:
        properties["Description"] = rec["Description"]
        properties["Priority"]    = rec["FamilyPriority"]
    
    log.tracef("...leaving %s.getAux()", __name__)


def setAux(uuid,aux,db):
    from ils.log.LogRecorder import LogRecorder
    log = LogRecorder(__name__ + ".setAux")
    log.infof("In %s.setAux()", __name__)
    
    appName  = handler.getApplicationName(uuid)
    familyName = handler.getFamilyName(uuid)

    properties = aux[0]
    log.tracef("   Application: %s", appName)
    log.tracef("   Family: %s", familyName)
    log.tracef("   Properties: %s", str(properties))
    
    SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (appName)
    applicationId = system.db.runScalarQuery(SQL,db)

    if applicationId == None:
        SQL = "insert into DtApplication (ApplicationName) values (?)"
        applicationId = system.db.runPrepUpdate(SQL, [appName], db, getKey=1)
    
    SQL = "SELECT familyId FROM DtFamily "\
          " WHERE ApplicationId = %s"\
          "  AND familyName = '%s'" % (applicationId,familyName)
    familyId = system.db.runScalarQuery(SQL,db)
    
    if familyId == None:
        SQL = "INSERT INTO DtFamily(applicationId,familyName,description,familyPriority) VALUES (?,?,?,?)"
        args = [applicationId, familyName, properties.get("Description",""), properties.get("Priority","0.0")]
        log.tracef("     SQL: %s", SQL)
        log.tracef("     ARGS: %s", args)
        familyId = system.db.runPrepUpdate(SQL, args, db, getKey=1)
        log.tracef("     Inserted a new family with id: %d", familyId)
    else:
        SQL = "UPDATE DtFamily SET familyName = ?, description = ?, familyPriority = ? where familyId = ? "
        args = [familyName, properties.get("Description",""), properties.get("Priority","0.0"),familyId]
        log.tracef("     SQL: %s", SQL)
        log.tracef("     ARGS: %s", args)
        system.db.runPrepUpdate(SQL, args, db)
        log.tracef("     Updated an existing family with id: %d", familyId)
    
    log.tracef("...leaving %s.setAux()", __name__)