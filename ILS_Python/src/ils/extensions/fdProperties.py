'''
  Designer/client scope extension functions dealing with FinalDiagnosis instances.
'''
import system
import com.ils.blt.common.ApplicationRequestHandler as ApplicationRequestHandler
from ils.common.cast import toBit
from ils.common.database import toDateString
from ils.sfc.common.util import logExceptionCause

handler = ApplicationRequestHandler()
log = system.util.getLogger("com.ils.diagToolkit.extensions")

'''

Gateway Scope Functions

'''

def delete(finalDiagnosisUUID):
    '''
    Even though a delete is initiated from Designer scope, this runs in gateway scope!
    '''
    log.tracef("In %s.delete()", __name__)
    
    import com.ils.blt.gateway.PythonRequestHandler as PythonRequestHandler
    handler = PythonRequestHandler()
    db = handler.getProductionDatabase()
    
    SQL = "delete from DtFinalDiagnosis where FinalDiagnosisUUID = '%s'" % (finalDiagnosisUUID)
    rows = system.db.runUpdateQuery(SQL, db)
    if rows == 1:
        log.tracef("Successfully deleted %d final diagnosis!", rows)
    else:
        log.tracef("Error deleting Final diagnosis with UUID <%s> - %d rows were deleted!", finalDiagnosisUUID, rows)
    
    
#    app = handler.getApplicationName(uuid)
#   print "     Application: ", app
#  family = handler.getFamilyName(uuid)
#    print "    Family: ", family
#    db = handler.getProductionDatabase()
#    print "    db: ", db
   
 



    

def save(uuid, aux):
    '''
    This method IS called when they do a save from the Designer.  
    It should really insert a new record into the DB for a new application, but I don't have enough info here to
    do anything (and I don't know how to get it).  This isn't really a show stopper because the engineer needs to
    open the big configuration popup Swing dialog which will insert a record if it doesn't already exist.
    '''
    log.tracef("In %s.save()", __name__)


'''

Designer Scope Functions

'''

def rename(uuid,oldName,newName):
    '''
    This is called in Designer Scope!
    The production and isolation databases need to be kept structurally in-synch.
    Apply these changes against both instances
    '''

    def renameInDatabase(uuid,oldName,newName,db):
        '''
        These methods are usually called in Designer scope. However, we may be using either the
        production or isolation databases. The Gateway makes this call when converting into
        isolation mode.
        '''
        SQL = "UPDATE DtFinalDiagnosis SET FinalDiagnosisName= '%s' WHERE FinalDiagnosisName = '%s'" % (newName,oldName)
        system.db.runUpdateQuery(SQL,db)
    
    log.tracef("In %s.rename(), renaming from %s to %s", __name__, oldName, newName)
    db = handler.getProductionDatabase()
    renameInDatabase(uuid,oldName,newName,db)
    db = handler.getIsolationDatabase()
    renameInDatabase(uuid,oldName,newName,db)

def getAux(uuid, aux, db):
    '''
    NOTE: The UUID supplied is from the parent, a diagram. The database interactions
           are all based on a the block name which is  the data structure.
    
    The aux data structure is a Python list of three dictionaries. These are:
    properties, lists and maplists.
     
    Fill the aux structure with values from the database.
    '''
    log.tracef("In %s.getAux", __name__)
    app = handler.getApplicationName(uuid)
    family = handler.getFamilyName(uuid)
 
    properties = aux[0]
    lists = aux[1]
    name = properties.get("Name","")
    
    log.tracef("Application / Family / Diagnosis: %S / %s / %s ", app, family, name)

    SQL = "SELECT FD.FinalDiagnosisPriority,FD.CalculationMethod,FD.PostTextRecommendation,"\
          " FD.PostProcessingCallback,FD.RefreshRate,FD.TextRecommendation,FD.Comment, "\
          " FD.Active,FD.Explanation,FD.TrapInsignificantRecommendations, FD.FinalDiagnosisLabel, "\
          " FD.FinalDiagnosisId, FD.Constant, FD.ManualMoveAllowed, FD.ShowExplanationWithRecommendation "\
          " FROM DtFinalDiagnosis FD,DtFamily FAM,DtApplication APP "\
          " WHERE APP.applicationId = FAM.applicationId"\
          " AND APP.applicationName = '%s' "\
          " AND FAM.familyId = FD.familyId "\
          " AND FAM.familyName = '%s'"\
          " AND FAM.familyId = FD.familyId " \
          " AND FD.finalDiagnosisName = '%s'"\
           % (app,family,name)
    ds = system.db.runQuery(SQL,db)
    
    if len(ds) == 0:
        log.warnf("Warning: No records found!")
        log.warnf(SQL)

    finalDiagnosisId = "NONE"
    for rec in ds:
        postTextRecommendation = toBit(rec["PostTextRecommendation"])
        active = toBit(rec["Active"])
        trapInsignificatRecommendations = toBit(rec["TrapInsignificantRecommendations"])
        constant = toBit(rec["Constant"])
        manualMoveAllowed = toBit(rec["ManualMoveAllowed"])
        showExplanationWithRecommendation = toBit(rec["ShowExplanationWithRecommendation"])
        
        finalDiagnosisId = rec["FinalDiagnosisId"]
        
        properties["FinalDiagnosisLabel"]  = rec["FinalDiagnosisLabel"]
        properties["Priority"]  = rec["FinalDiagnosisPriority"]
        properties["CalculationMethod"] = rec["CalculationMethod"]
        properties["Comment"] = rec["Comment"]
        properties["TextRecommendation"] = rec["TextRecommendation"]
        properties["PostTextRecommendation"] = postTextRecommendation
        properties["PostProcessingCallback"] = rec["PostProcessingCallback"]
        properties["RefreshRate"] = rec["RefreshRate"]
        properties["Active"] = active
        properties["Explanation"] = rec["Explanation"]
        properties["TrapInsignificantRecommendations"] = trapInsignificatRecommendations
        properties["Constant"] = constant
        properties["ManualMoveAllowed"] = manualMoveAllowed
        properties["ShowExplanationWithRecommendation"] = showExplanationWithRecommendation

    SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (app)
    applicationId = system.db.runScalarQuery(SQL,db)
    
    # Create lists of QuantOutputs
    # First is the list of all names for the Application
    SQL = "SELECT QuantOutputName "\
          " FROM DtQuantOutput "\
          " WHERE applicationId=%s" % (str(applicationId))
    ds = system.db.runQuery(SQL,db)
    outputs = []
    for record in ds:
        outputs.append(str(record["QuantOutputName"]))
    lists["QuantOutputs"] = outputs
    
    # Next get the list that is used by the diagnosis, if it exists
    outputs = []
    if finalDiagnosisId != "NONE":
        SQL = "SELECT QO.QuantOutputName "\
            " FROM DtQuantOutput QO,DtRecommendationDefinition REC "\
            " WHERE QO.quantOutputId = REC.quantOutputId "\
            "  AND REC.finalDiagnosisId = %s" %(finalDiagnosisId)
        ds = system.db.runQuery(SQL,db)
    
        for record in ds:
            outputs.append(str(record["QuantOutputName"]))
            
    lists["OutputsInUse"] = outputs
    
    log.tracef("properties: %s", str(properties))
    log.tracef("lists: %s", str(lists))
    

def setAux(uuid,aux,db):
    log.tracef("In %s.setAux", __name__)
    app  = handler.getApplicationName(uuid)
    family = handler.getFamilyName(uuid)
    log.tracef("...back in setAux...")
    properties = aux[0]
    lists = aux[1]
    name = properties.get("Name","")
    log.tracef("Application/family/diagnosis: %s / %s / %s", app, family, name)
    log.tracef("Properties: %s", str(properties))
    log.tracef("Lists: %s", str(lists))
    
    log.tracef("Show Explanation with Recommendation: %s", str(properties.get("ShowExplanationWithRecommendation","0")))
    
    SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (app)
    applicationId = system.db.runScalarQuery(SQL,db)
    log.tracef("The application Id is: %s", str(applicationId))
    if applicationId == None:
        SQL = "insert into DtApplication (ApplicationName) values (?)"
        applicationId = system.db.runPrepUpdate(SQL, [app], db, getKey=1)
    
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
        
    SQL = "SELECT finalDiagnosisId FROM DtFinalDiagnosis "\
          " WHERE FamilyId = %s"\
          "  AND finalDiagnosisName = '%s'" % (familyId,name)
    log.tracef(SQL)
    fdId = system.db.runScalarQuery(SQL,db)
    log.tracef("The final diagnosis Id is: %s", str(fdId))
    if fdId == None:
        log.tracef("Inserting a new final diagnosis...")
        recTime = system.date.now()
        recTime = system.date.addMonths(recTime, -12)
        recTime = toDateString(recTime)
        # When we insert a new final diagnosis it has to be false until it runs...
        SQL = "INSERT INTO DtFinalDiagnosis (familyId, finalDiagnosisName, finalDiagnosisLabel, finalDiagnosisPriority, calculationMethod, "\
               "postTextRecommendation, PostProcessingCallback, refreshRate, textRecommendation, active, explanation, "\
               "trapInsignificantRecommendations, constant, manualMoveAllowed, comment, showExplanationWithRecommendation, timeOfMostRecentRecommendationImplementation)"\
               " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        log.tracef("SQL: %s", SQL)
        try:
            args =  [familyId, name, properties.get("FinalDiagnosisLabel",""), properties.get("Priority","0.0"), properties.get("CalculationMethod",""),\
                        properties.get("PostTextRecommendation","0"), properties.get("PostProcessingCallback",""),\
                        properties.get("RefreshRate","1.0"), properties.get("TextRecommendation",""), properties.get("Active","0"), properties.get("Explanation","0"),\
                        properties.get("TrapInsignificantRecommendations","1"), properties.get("Constant","0"),\
                        properties.get("ManualMoveAllowed","0"), properties.get("Comment",""), properties.get("ShowExplanationWithRecommendation","0"), recTime]
            log.tracef("Arguments (%d): %s", len(args), str(args))
            fdId = system.db.runPrepUpdate(SQL, args, db, getKey=1)
            log.tracef("Inserted a new final diagnosis with id: %d", fdId)
        except:
            logExceptionCause("Inserting a new Final Diagnosis", log)
            return
    else:
        log.tracef("Updating an existing final diagnosis...")
        SQL = "UPDATE DtFinalDiagnosis SET familyId=?, finalDiagnosisPriority=?, calculationMethod=?, finalDiagnosisLabel=?, " \
            "postTextRecommendation=?, postProcessingCallback=?, refreshRate=?, textRecommendation=?, explanation=?, "\
            "trapInsignificantRecommendations=?, constant=?, manualMoveAllowed=?, comment=?, showExplanationWithRecommendation=? "\
            " WHERE finalDiagnosisId = ?"
        args = [familyId, properties.get("Priority","0.0"), properties.get("CalculationMethod",""), properties.get("FinalDiagnosisLabel",""),\
                    properties.get("PostTextRecommendation","0"), properties.get("PostProcessingCallback",""),\
                    properties.get("RefreshRate","1.0"), properties.get("TextRecommendation",""),\
                    properties.get("Explanation","0"), properties.get("TrapInsignificantRecommendations","1"),\
                    properties.get("Constant","0"), properties.get("ManualMoveAllowed","0"), properties.get("Comment",""), \
                    properties.get("ShowExplanationWithRecommendation","0"), fdId]
        
        log.tracef("SQL: %s", SQL)
        log.tracef("Args: %s", str(args))
        rows = system.db.runPrepUpdate(SQL, args, db)
        log.tracef("Updated %d rows", rows)
        
    ''' 
    Delete any recommendations that may exist for this final diagnosis to avoid foreign key constraints when we delete and recreate the DtRecommendationDefinitions.
    (I'm not sure this is the correct thing to do - this will affect a live system.  Not sure we want to do this just because they press OK to update the comment, explanation, etc.
    '''
    log.tracef("Deleting existing recommendations...")
    SQL = "select RecommendationDefinitionId from DtRecommendationDefinition where FinalDiagnosisId = %s" % (fdId)
    log.tracef(SQL)
    pds = system.db.runQuery(SQL, db)
    totalRows = 0
    for record in pds:
        SQL = "delete from DtRecommendation where RecommendationDefinitionId = %s" % (record["RecommendationDefinitionId"])
        log.tracef(SQL)
        rows = system.db.runUpdateQuery(SQL, db)
        totalRows = totalRows + rows
    log.tracef("Deleted %d recommendations prior to updating the Recommendation Definitions...", totalRows)
    
    # Update the list of outputs used
    log.tracef("Deleting Recommendation Definitions...")
    SQL = "DELETE FROM DtRecommendationDefinition WHERE finalDiagnosisId = %s" % (str(fdId))
    log.tracef(SQL)
    system.db.runUpdateQuery(SQL,db)
    
    olist = lists.get("OutputsInUse")
    instr = None
    for output in olist:
        if instr == None:
            instr = ""
        else:
            instr = instr+","
        instr = instr+"'"+output+"'"
    
    rows = 0
    if instr != None:
        log.tracef("Inserting a recommendation definition for %s...", instr)
        SQL = "INSERT INTO DtRecommendationDefinition(finalDiagnosisId,quantOutputId) "\
          "SELECT %s,quantOutputId FROM DtQuantOutput QO"\
          " WHERE QO.applicationID = %s "\
          "  AND QO.quantOutputName IN (%s)" \
          % (fdId,applicationId,instr)
        log.tracef(SQL)
        rows=system.db.runUpdateQuery(SQL,db)

    print "Inserted %d recommendation definitions" % (rows)