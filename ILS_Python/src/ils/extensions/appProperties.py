'''
  Designer/client scope extension functions dealing with Application instances.
'''
import system
import com.ils.blt.common.ApplicationRequestHandler as ApplicationRequestHandler
import com.ils.blt.gateway.PythonRequestHandler as PythonRequestHandler
from ils.common.cast import toBit

log = system.util.getLogger("com.ils.diagToolkit.extensions")
handler = ApplicationRequestHandler()

def delete(applicationUUID):
    '''
    This is called when the user deletes an application from the designer.  I hope that it already called the delete method for the diagrams and families in the application
    from the bottom up so that we don't hit a FK constraint here.
    
    I'd like to use the application name, which is guarenteed to be unique by the database, but I think that the gateway has already deleted the application so the getApplicationName()
    call fails - at least that is the only explanation I can come up with!  So instead use the UUID to delete the application.
    '''
    log.infof("In %s.delete()", __name__)
    

    handler = PythonRequestHandler()
    db = handler.getProductionDatabase()
    
    SQL = "delete from DtApplication where ApplicationUUID = '%s'" % (applicationUUID)
    rows = system.db.runUpdateQuery(SQL, db)
    if rows == 1:
        log.infof("Successfully deleted application with UUID <%s> from the database!", applicationUUID)
    elif rows == 0:
        log.errorf("Unable to delete application with UUID <%s> from the database", applicationUUID)
    else:
        log.warnf("Multiple rows <%d> were deleted from the database for application with UUID <%s>", rows, applicationUUID)


def rename(uuid,oldName,newName):
    '''
    TODO: It appears that this is NOT called when I rename an application.  
    I think I can handle this case in the save method, especially if I can figure out how to get the name.
    '''
    log.infof("In %s.rename()", __name__)
    def renameInDatabase(uuid, oldName, newName, db):
        SQL = "UPDATE DtApplication SET ApplicationName= '%s' WHERE ApplicationName = '%s'" % (newName,oldName)
        system.db.runUpdateQuery(SQL, db)
    
    log.tracef("In %s.rename(), renaming from %s to %s", __name__, oldName, newName)
    db = handler.getProductionDatabase()
    renameInDatabase(uuid,oldName,newName,db)


    
def save(applicationUUID, aux):
    '''
    This method IS called when they do a save from the Designer.  
    It should really insert a new record into the DB for a new application, but I don't have enough info here to
    do anything (and I don't know how to get it).  This isn't really a show stopper because the engineer needs to
    open the big configuration popup Swing dialog which will insert a record if it doesn't already exist.
    '''
    log.infof("In %s.save()", __name__)
    handler = PythonRequestHandler()
    db = handler.getProductionDatabase()
    
    from system.ils.blt.diagram import getApplicationName
    applicationName = getApplicationName(applicationUUID)
    log.tracef("...applicationName from system.ils.blt.diagram.getApplicationName: %s", applicationName)
    
    SQL = "select ApplicationId from DtApplication where ApplicationUUID = '%s'" % (applicationUUID)
    applicationId = system.db.runScalarQuery(SQL, db)

    if applicationId == None:
        '''
        Take some extra steps here to see if this is an old legacy application that was saved before we added applicationUUID to the database.
        If we find an application name match then update the application's UUID.
        '''
        SQL = "select applicationId from DtApplication where applicationName = '%s'" % (applicationName)
        applicationId = system.db.runScalarQuery(SQL, db)
        if applicationId == None:
            SQL = "insert into DtApplication (ApplicationUUID, ApplicationName, NotificationStrategy, Managed) "\
                "values ('%s', '%s', 'ocAlert', 0)" % (applicationUUID, applicationName)
            log.tracef("...SQL: %s,", SQL)
            applicationId = system.db.runUpdateQuery(SQL, db, getKey=1)
            log.tracef("Inserted a new application with id: %d", applicationId)
        else:
            SQL = "update DtApplication set ApplicationUUID = '%s' where applicationId = %s" % (applicationUUID, applicationId)
            log.tracef("...SQL: %s,", SQL)
            rows = system.db.runUpdateQuery(SQL, db)
            log.tracef("...updated the applicationUUID (rows=%d) for a legacy family named %s!", rows, applicationName)
    else:
        SQL = "update DtApplication set ApplicationName = '%s' where applicationId = %s" % (applicationName, applicationId)
        log.tracef("...SQL: %s,", SQL)
        rows = system.db.runUpdateQuery(SQL, db)
        log.tracef("...updated %d rows in DtApplication for %s", rows, applicationName)


'''
These methods are usually called in Designer scope. However, we may be using either the
production or isolation databases. The Gateway makes this call when converting into
isolation mode. 

The aux data structure is a Python list of three dictionaries. These are:
properties, lists and maplists.
 
Fill the aux structure with values from the database
The caller must supply either the production or isolation database name
'''
def getAux(uuid,aux,db):
    log.infof("In %s.getAux()", __name__)
    applicationId = -1
    appName = handler.getApplicationName(uuid)
    
    properties = aux[0]
    lists      = aux[1]
    maplists   = aux[2]
    
    log.tracef("...the application name is: %s, database is: %s", appName, db)
    
    SQL = "SELECT A.ApplicationId, A.Description, A.Managed, P.Post, U.UnitName, Q.QueueKey MessageQueue, A.IncludeInMainMenu, L.LookupName GroupRampMethod "\
          " FROM DtApplication A, TkPost P, TkUnit U, QueueMaster Q, Lookup L "\
          " WHERE A.ApplicationName = '%s' " \
          " and A.UnitId = U.UnitId "\
          " and U.PostId = P.PostId "\
          " and A.GroupRampMethodId = L.LookupId "\
          " and A.MessageQueueId = Q.QueueId" % (appName)

    pds = system.db.runQuery(SQL,db)
    
    if len(pds) == 0:
        log.errorf("Warning: %s was not found in the application table", appName)
    
    if len(pds) > 1:
        log.errorf("Error: more than one application record was found for %s - the last one will be used!", appName)

    for record in pds:
        applicationId = record["ApplicationId"]
        properties["Description"]=str(record["Description"])
        properties["Post"]=str(record["Post"])
        properties["Unit"]=str(record["UnitName"])
        properties["MessageQueue"]=str(record["MessageQueue"])
        properties["IncludeInMainMenu"]=str(record["IncludeInMainMenu"])
        properties["GroupRampMethod"]=record["GroupRampMethod"]
        properties["Managed"]=str(record["Managed"])

    log.tracef("Properties: %s", str(properties))
    
    # Fetch the list of posts
    SQL = "SELECT Post "\
          " FROM TkPost "\
          " ORDER BY Post"
    ds = system.db.runQuery(SQL,db)
    
    posts = []
    for record in ds:
        posts.append(str(record["Post"]))
    lists["Posts"] = posts
    
    # Fetch the list of units
    SQL = "SELECT UnitName "\
          " FROM TkUnit "\
          " ORDER BY UnitName"
    ds = system.db.runQuery(SQL,db)
    units = []
    for record in ds:
        units.append(str(record["UnitName"]))
    lists["Units"] = units
    
    # Fetch the list of Ramp Methods
    SQL = "SELECT LookupName "\
          " FROM Lookup "\
          " where LookupTypeCode = 'GroupRampMethod' "\
          " ORDER BY LookupName"
    ds = system.db.runQuery(SQL,db)
    methods = []
    for record in ds:
        methods.append(str(record["LookupName"]))
    lists["GroupRampMethods"] = methods
    
    # Fetch the list of Feedback Methods
    SQL = "SELECT LookupName "\
          " FROM Lookup "\
          " where LookupTypeCode = 'FeedbackMethod' "\
          " ORDER BY LookupName"
    ds = system.db.runQuery(SQL,db)
    methods = []
    for record in ds:
        methods.append(str(record["LookupName"]))
    lists["FeedbackMethods"] = methods
    
    # Fetch the list of queues
    SQL = "SELECT QueueKey "\
          " FROM QueueMaster "\
          " ORDER BY QueueKey"
    ds = system.db.runQuery(SQL,db)
    queues = []
    for record in ds:
        queues.append(str(record["QueueKey"]))
    lists["MessageQueues"] = queues
    
    # Fetch the list of Quant outputs
    SQL = "SELECT QuantOutputId, QuantOutputName QuantOutput, TagPath, MostNegativeIncrement, MostPositiveIncrement, MinimumIncrement, SetpointHighLimit,"\
          "SetpointLowLimit, L.LookupName FeedbackMethod, IncrementalOutput "\
          " FROM DtQuantOutput QO, Lookup L  "\
          " WHERE ApplicationId = %s "\
          " and QO.FeedbackMethodId = L.LookupId "\
          " ORDER BY QuantOutput" % (str(applicationId))
    ds = system.db.runQuery(SQL,db)

    maplist = []
    for record in ds:
        rec = {}
        rec["QuantOutputId"]=str(record["QuantOutputId"])
        rec["QuantOutput"]=str(record["QuantOutput"]) 
        rec["TagPath"]=str(record["TagPath"])
        rec["MostNegativeIncrement"]=str(record["MostNegativeIncrement"])
        rec["MostPositiveIncrement"]=str(record["MostPositiveIncrement"])
        rec["MinimumIncrement"]=str( record["MinimumIncrement"])
        rec["SetpointHighLimit"]=str( record["SetpointHighLimit"])
        rec["SetpointLowLimit"]=str(record["SetpointLowLimit"])
        rec["FeedbackMethod"]=str(record["FeedbackMethod"])
        rec["IncrementalOutput"]=str(record["IncrementalOutput"])
        maplist.append(rec)
        
    maplists["QuantOutputs"]=maplist
    
    log.tracef("appProperties.getAux: properties: %s", str(properties))
    log.tracef("appProperties.getAux: lists: %s: ", str(lists))
    log.tracef("appProperties.getAux: maplists: %s", str(maplists))
    log.tracef("  ...leaving getAux()!")


# Set values in the database from contents of the aux container
# The caller must supply either the production or isolation database name
def setAux(uuid, aux, db):
    log.infof("In %s.setAux()", __name__)
    applicationName = handler.getApplicationName(uuid)
    log.tracef("  ...the application name is: %s,  database: %s",applicationName, db)
    
    from locale import setlocale, LC_NUMERIC, atof
    setlocale(LC_NUMERIC, '')
    
    properties = aux[0]
    lists      = aux[1]
    maplists   = aux[2]
    
    log.tracef("Saving properties: %s", str(properties))
    log.tracef("Saving lists: %s", str(lists))
    log.tracef("Saving maplists: %s", str(maplists))
    
    description = properties.get("Description","")
    managed = properties.get("Managed", 1)
     
    SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (applicationName)
    applicationId = system.db.runScalarQuery(SQL,db)
    
    log.tracef("The application Id is: %d", applicationId)
    
    SQL = "select PostId from TkPost where Post = '%s'" % (properties.get("Post",""))
    postId = system.db.runScalarQuery(SQL,db)
    
    SQL = "select UnitId from TkUnit where UnitName = '%s'" % (properties.get("Unit",""))
    unitId = system.db.runScalarQuery(SQL,db)
    
    SQL = "select QueueId from QueueMaster where QueueKey = '%s'" % (properties.get("MessageQueue",""))
    messageQueueId = system.db.runScalarQuery(SQL,db)
    
    SQL = "select LookupId from Lookup where LookupTypeCode = 'GroupRampMethod' and LookupName = '%s'" % (properties.get("GroupRampMethod",""))
    groupRampMethodId = system.db.runScalarQuery(SQL,db)
    
    if applicationId == None:
        SQL = "insert into DtApplication (ApplicationName, Description, MessageQueueId, GroupRampMethodId, UnitId, Managed) "\
            "values (?, ?, ?, ?, ?, ?)"
        applicationId = system.db.runPrepUpdate(SQL, [applicationName, description,  
                messageQueueId, groupRampMethodId, unitId, managed], db, getKey=1)
        log.tracef("Inserted a new application with id: %d", applicationId)
    else:
        SQL = "Update DtApplication set ApplicationName = ?, Description = ?, UnitId = ?, MessageQueueId = ?, GroupRampMethodId = ?, managed = ?" \
            " where ApplicationId = ? "
        system.db.runPrepUpdate(SQL, [applicationName, description, unitId, 
                messageQueueId, groupRampMethodId, managed, applicationId],db)
        log.tracef("Updated an existing application with id: %d", applicationId)
    
    # Before we add any new quant outputs, fetch the ones that are already there so we can see if the user deleted any
    SQL = "select QuantOutputId from DtQuantOutput where ApplicationId = %s" % (str(applicationId))
    pds = system.db.runQuery(SQL,db)
    quantOutputIds = []
    for record in pds:
        quantOutputId = record["QuantOutputId"]
        quantOutputIds.append(quantOutputId)
    log.tracef("The list of existing Quant Output Ids is: %s", str(quantOutputIds))
    
    # Now process the quant outputs that are in the list.
    # The list is a list of dictionaries
    outputList = maplists.get("QuantOutputs",[])
    for record in outputList:
        quantOutputId=record.get("QuantOutputId", -1)
        quantOutputId = int(quantOutputId)
        
        # Update the list of ids so I know which ones to delete at the end
        if quantOutputId in quantOutputIds:
            quantOutputIds.remove(quantOutputId)

        quantOutput=record.get("QuantOutput", "")
        log.tracef("...saving Quant Output: %s", str(quantOutput))
        tagPath = record.get("TagPath", "")
        feedbackMethod = record.get("FeedbackMethod", 'Simple Sum')
        
        '''
        I am having a tough time dealing with the commas that Swing is putting into the string which represent floats.  SQLServer
        chokes on it.  I tried using the locale utilities and atof, but if they don't include a decimal that that chokes.  The database
        field is a float but they can enter an integer.
        '''
        setpointLowLimit = str(record.get("SetpointLowLimit", 0.0)).replace(',','')
        setpointHighLimit = str(record.get("SetpointHighLimit", 100.0)).replace(',','')
        minimumIncrement = str(record.get("MinimumIncrement", 0.01)).replace(',','')
        mostPositiveIncrement = str(record.get("MostPositiveIncrement", 10.0)).replace(',','')
        mostNegativeIncrement = str(record.get("MostNegativeIncrement", -10.0)).replace(',','')
        
        incrementalOutput = record.get("IncrementalOutput", 1)

        if incrementalOutput in ['True', '1']:
            incrementalOutput = 1
        else:
            incrementalOutput = 0

        SQL = "select LookupId from Lookup where LookupTypeCode = 'FeedbackMethod' and LookupName = '%s'" % (feedbackMethod)
        feedbackMethodId = system.db.runScalarQuery(SQL,db)
        
        log.tracef("Id: %d", quantOutputId)
        log.tracef("Tagpath: %s", tagPath)
        log.tracef("Minimum Increment: %s", str(minimumIncrement))
        log.tracef("Most Negative Increment: %s", str(mostNegativeIncrement))
        log.tracef("Most Positive Increment: %s", str(mostPositiveIncrement))
        
        if quantOutputId < 0:
            log.tracef("...inserting...")
            SQL = "insert into DtQuantOutput (QuantOutputName, ApplicationId, TagPath, MostNegativeIncrement, MostPositiveIncrement,"\
                " MinimumIncrement, SetpointHighLimit, SetpointLowLimit, FeedbackMethodId, IncrementalOutput) values (?,?,?,?,?,?,?,?,?,?)"
            system.db.runPrepUpdate(SQL,[quantOutput, applicationId, tagPath, mostNegativeIncrement, mostPositiveIncrement, \
                minimumIncrement, setpointHighLimit, setpointLowLimit, feedbackMethodId, incrementalOutput],db)
        else:
            log.tracef("...updating...")
            SQL = "update DtQuantOutput set QuantOutputName = '%s', TagPath = '%s', MostNegativeIncrement = %s, MostPositiveIncrement = %s,"\
                " MinimumIncrement = %s, SetpointHighLimit = %s, SetpointLowLimit = %s, FeedbackMethodId = %s, IncrementalOutput = %s "\
                " where QuantOutputId = %s" % (quantOutput, tagPath, str(mostNegativeIncrement), str(mostPositiveIncrement), \
                str(minimumIncrement), str(setpointHighLimit), str(setpointLowLimit), str(feedbackMethodId), str(incrementalOutput), str(quantOutputId))
            system.db.runUpdateQuery(SQL, db)
    
    # Now see if there are some Quant Outputs in the database that were not in the list
    log.tracef("--- Quant Outputs to delete: %s", str(quantOutputIds))
    for quantOutputId in quantOutputIds:
        log.tracef("...delete: %d", quantOutputId)
        system.db.runUpdateQuery("delete from DtQuantOutput where QuantOutputId = %s" % (str(quantOutputId)),db)