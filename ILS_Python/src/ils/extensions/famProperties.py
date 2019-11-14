'''
  Designer/client scope extension functions dealing with Family instances.
'''
import system
import com.ils.blt.common.ApplicationRequestHandler as ApplicationRequestHandler

handler = ApplicationRequestHandler()
def delete(uuid):
    pass
# The production an isolation databases need to be kept structurally in-synch.
# Apply these changes against both instances.
def rename(uuid,oldName,newName):
    db = handler.getProductionDatabase()
    renameInDatabase(uuid,oldName,newName,db)
    db = handler.getIsolationDatabase()
    renameInDatabase(uuid,oldName,newName,db)
    
def renameInDatabase(uuid,oldName,newName,db):
    SQL = "UPDATE DtFamily SET FamilyName= '%s' WHERE FamilyName = '%s'" % (newName,oldName)
    system.db.runUpdateQuery(SQL,db)
   
def save(uuid,aux):
    print "Saving Family: %s - %s" % (uuid, str(aux))
    pass 
# These methods are usually called in Designer scope. However, we may be using either the
# production or isolation databases. The Gateway makes this call when converting into
# isolation mode. 
#
# The aux data structure is a Python list of three dictionaries. These are:
# properties, lists and maplists. Of these, the family only uses properties.
# 
# Fill the aux structure with values from the database
def getAux(uuid,aux,db):
    app  = handler.getApplicationName(uuid)
    name = handler.getFamilyName(uuid)
    
    properties = aux[0]
    
    print "famProperties,getAux():  ...the family name is ", name
    
    SQL = "SELECT FAM.Description,FAM.FamilyPriority "\
          " FROM DtFamily FAM,DtApplication APP "\
          " WHERE FAM.applicationId = APP.applicationId "\
          "   AND FAM.familyName = '%s'"\
          "   AND APP.ApplicationName = '%s' " % (name,app)
    ds = system.db.runQuery(SQL,db)
    for rec in ds:
        properties["Description"] = rec["Description"]
        properties["Priority"]    = rec["FamilyPriority"]


def setAux(uuid,aux,db):
    app  = handler.getApplicationName(uuid)
    name = handler.getFamilyName(uuid)
    properties = aux[0]
    print "famProperties.setAux()  ...the application/family name is: ",app,"/",name,", properties:", properties
    
    SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (app)
    applicationId = system.db.runScalarQuery(SQL,db)
    if applicationId == None:
        SQL = "insert into DtApplication (ApplicationName) values (?)"
        applicationId = system.db.runPrepUpdate(SQL, [app], db, getKey=1)
    
    SQL = "SELECT familyId FROM DtFamily "\
          " WHERE ApplicationId = %s"\
          "  AND familyName = '%s'" % (applicationId,name)
    familyId = system.db.runScalarQuery(SQL,db)
    if familyId == None:
        SQL = "INSERT INTO DtFamily(applicationId,familyName,description,familyPriority)"\
               " VALUES(?,?,?,?)"
        familyId = system.db.runPrepUpdate(SQL, [applicationId, name, properties.get("Description",""),  
                                                 properties.get("Priority","0.0")], db, getKey=1)
        print "famProperties.setAux(): Inserted a new family with id: ", familyId
    else:
        SQL = "UPDATE DtFamily SET familyName = ?, description = ?, familyPriority = ?" \
            " where familyId = ? "
        system.db.runPrepUpdate(SQL, [name, properties.get("Description",""), properties.get("Priority","0.0"),familyId],db)
        print "famProperties.setAux(): Updated an existing family with id: ", familyId
