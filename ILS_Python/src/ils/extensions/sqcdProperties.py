'''
Created on Jun 14, 2019

@author: phass

Designer/client scope extension functions dealing with sqcDiagnosis instances.

These methods are usually called in Designer scope. However, we may be using either the
production or isolation databases. The Gateway makes this call when converting into
isolation mode.
'''
import system
import com.ils.blt.common.ApplicationRequestHandler as ApplicationRequestHandler

handler = ApplicationRequestHandler()
log = system.util.getLogger("com.ils.diagToolkit.extensions")

def delete(uuid):
    log.infof("In %s.delete()", __name__)
    pass

# The production an isolation databases need to be kept structurally in-synch.
# Apply these changes against both instances
def rename(uuid,oldName,newName):
    
    def renameInDatabase(uuid,oldName,newName,db):
        app = handler.getApplicationName(uuid)
        family = handler.getFamilyName(uuid)
        log.infof("Renaming Application / Family / SQC Diagnosis: %S / %s / %s to %s", app, family, oldName, newName)
    
        SQL = "UPDATE DtSqcDiagnosis SET SqcDiagnosisName= '%s' WHERE sqcDiagnosisName = '%s'" % (newName, uuid)
        system.db.runUpdateQuery(SQL,db)
    
    log.infof("In %s.rename()", __name__)
    db = handler.getProductionDatabase()
    renameInDatabase(uuid,oldName,newName,db)
    db = handler.getIsolationDatabase()
    renameInDatabase(uuid,oldName,newName,db)



def save(uuid,aux):
    '''
    This method IS called when they do a save from the Designer.  
    It should really insert a new record into the DB for a new application, but I don't have enough info here to
    do anything (and I don't know how to get it).  This isn't really a show stopper because the engineer needs to
    open the big configuration popup Swing dialog which will insert a record if it doesn't already exist.
    '''
    log.tracef("In %s.save()", __name__)

'''
NOTE: The UUID supplied is from the parent, a diagram. The database interactions
       are all based on a the block name which is  the data structure.

The aux data structure is a Python list of three dictionaries. These are:
properties, lists and maplists.
 
Fill the aux structure with values from the database.
'''
def getAux(uuid,aux,db):
    log.infof("In %s.getAux", __name__)
    app = handler.getApplicationName(uuid)
    family = handler.getFamilyName(uuid)
 
    properties = aux[0]
    name = properties.get("Name","")
    
    log.tracef("Application / Family / SQC Diagnosis: %S / %s / %s ", app, family, name)

    SQL = "SELECT SD.SQCDiagnosisId, SD.SQCDiagnosisLabel "\
          " FROM DtSqcDiagnosis SD,DtFamily FAM,DtApplication APP "\
          " WHERE APP.applicationId = FAM.applicationId"\
          " AND APP.applicationName = '%s' "\
          " AND FAM.familyId = SD.familyId "\
          " AND FAM.familyName = '%s'"\
          " AND SD.SQCDiagnosisName = '%s'"\
           % (app,family,name)
    ds = system.db.runQuery(SQL,db)
    
    if len(ds) == 0:
        log.warnf("Warning: No records found!")
        log.warnf(SQL)

    for rec in ds:
        properties["SQCDiagnosisLabel"]  = rec["SQCDiagnosisLabel"]

def setAux(uuid,aux,db):
    log.infof("In %s.setAux", __name__)
    app  = handler.getApplicationName(uuid)
    log.infof("yo")
    family = handler.getFamilyName(uuid)
    log.infof("...back in setAux...")
    properties = aux[0]

    name = properties.get("Name","")
    log.tracef("Application/family/diagnosis: %s / %s / %s", app, family, name)
    log.tracef("Properties: %s", str(properties))
    
    '''
    Get the Application ID or insert a new application
    '''
    SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (app)
    applicationId = system.db.runScalarQuery(SQL,db)
    log.tracef("The application Id is: %s", str(applicationId))
    if applicationId == None:
        SQL = "insert into DtApplication (ApplicationName) values (?)"
        applicationId = system.db.runPrepUpdate(SQL, [app], db, getKey=1)
    
    '''
    Get the Family ID or insert a new family
    '''
    SQL = "SELECT familyId FROM DtFamily "\
          " WHERE ApplicationId = %s"\
          "  AND familyName = '%s'" % (applicationId,family)
    familyId = system.db.runScalarQuery(SQL,db)
    log.tracef("The family Id is: %s", str(familyId))
    if familyId == None:
        SQL = "INSERT INTO DtFamily (applicationId,familyName,familyPriority) "\
               " VALUES (?, ?, 0.0)"
        log.tracef(SQL)
        familyId = system.db.runPrepUpdate(SQL, [applicationId, family], db, getKey=1)
    
    '''
    Get the SQC Diagnosis ID, then update it, or insert a new one
    '''
    SQL = "SELECT sqcDiagnosisId FROM DtSqcDiagnosis "\
          " WHERE FamilyId = %s"\
          "  AND sqcDiagnosisName = '%s'" % (familyId, name)
    log.tracef(SQL)
    sqcId = system.db.runScalarQuery(SQL,db)
    log.tracef("The sqc diagnosis Id is: %s", str(sqcId))
    if sqcId == None:
        log.infof("Inserting a new SQC diagnosis...")
        # When we insert a new final diagnosis it has to be false until it runs...
        SQL = "INSERT INTO DtSqcDiagnosis (familyId, sqcDiagnosisName, sqcDiagnosisLabel) "\
               " VALUES (?,?,?)"
        fdId = system.db.runPrepUpdate(SQL, [familyId, name, properties.get("FinalDiagnosisLabel","")], db, getKey=1)
        log.tracef("Inserted a new SQC diagnosis with id: %d", fdId)
    else:
        log.infof("Updating an existing SQC diagnosis...")
        SQL = "UPDATE DtSqcDiagnosis SET FamilyId = ?, sqcDiagnosisLabel=? WHERE sqcDiagnosisId = ?"
        args = [familyId, properties.get("SQCDiagnosisLabel",""), sqcId]
        
        log.tracef("SQL: %s", SQL)
        log.tracef("Args: %s", str(args))
        rows = system.db.runPrepUpdate(SQL, args, db)
        log.tracef("Updated %d rows", rows)
