#  Copyright 2014 ILS Automation
#
import system
from ils.common.cast import toBit
from ils.common.database import toDateString

def getClassName():
    return "FinalDiagnosis"

# A FinalDiagnosis block receives a truth-value from an SQC
# or other block upstream and deduces the reason for the issue.
#
from ils.block import basicblock
from ils.log.LogRecorder import LogRecorder
#import ils.diagToolkit.finalDiagnosis as fd

callback = "fd.evaluate"

class FinalDiagnosis(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.initialize()
        self.state = "UNKNOWN"
        self.handler.setAlerterClass(self.getClassName())
        self.log = LogRecorder(__name__)
    
    # Set attributes custom to this class
    def initialize(self):
        self.className = 'ils.block.finaldiagnosis.FinalDiagnosis'
#        self.properties['Label'] = {'value':'FinalDiagnosis','editable':True}
        
        self.inports = [{'name':'in','type':'TRUTHVALUE','allowMultiple':False}]
        self.outports= [{'name':'out','type':'TRUTHVALUE'}]
    
        
    # Return a dictionary describing how to draw an icon
    # in the palette and how to create a view from it.
    def getPrototype(self):
        proto = {}
        proto['auxData'] = True
        proto['iconPath']= "Block/icons/palette/final_diagnosis.png"
        proto['label']   = "FinDiagnosis"
        proto['tooltip']        = "Conclude a diagnosis based on input"
        proto['tabName']        = 'Conclusion'
        proto['viewBackgroundColor'] = '0xFCFEFE'
        proto['viewLabel']      = "Final\nDiagnosis"
        proto['blockClass']     = self.getClassName()
        proto['blockStyle']     = 'square'
        proto['viewFontSize']       = 14
        proto['viewHeight']     = 80
        proto['inports']        = self.getInputPorts()
        proto['outports']       = self.getOutputPorts()
        proto['viewWidth']      = 100
        proto['transmitEnabled']= True
        return proto
            
    # Called when a value has arrived on one of our input ports
    # It is our diagnosis. Set the property then evaluate.
    def acceptValue(self,port,value,quality,ts):
        newState = str(value).upper()
        if newState == self.state:
            return
        
        self.state = newState
        
        # I'm not really using this, but I'm printing it up front just to make sure this works
        projectName = system.util.getProjectName()
        self.log.tracef("FinalDiagnosis.acceptValue: %s (project: %s)", self.state, projectName)

        if self.state != "UNKNOWN":
            print "Clearing the watermark"
            system.ils.blt.diagram.clearWatermark(self.parentuuid)
        
        # On startup, it is possible for a block to get a value before
        # all resources (like the parent application) have been loaded. 
        if self.handler.getApplication(self.parentuuid)==None or self.handler.getFamily(self.parentuuid)==None:
            print "FinalDiagnosis.acceptValue: Parent application or family not loaded yet, ignoring state change"
            self.state = "UNKNOWN"
            return

        database = self.handler.getDefaultDatabase(self.parentuuid)
        provider = self.handler.getDefaultTagProvider(self.parentuuid)
        
        print "Using database: %s and tag provider: %s " % (database, provider)
        
        applicationName = self.handler.getApplication(self.parentuuid).getName()
        familyName = self.handler.getFamily(self.parentuuid).getName()
        print "Application: %s\nFamily: %s" % (applicationName, familyName)
        
        theFinalDiagnosis = self.handler.getBlock(self.parentuuid, self.uuid)
        finalDiagnosisName = theFinalDiagnosis.getName()
        print "Final Diagnosis: %s" % (finalDiagnosisName)        

        if self.state == "TRUE":
            print "The diagnosis just became TRUE"
            def work(fd=self,applicationName=applicationName,familyName=familyName,finalDiagnosisName=finalDiagnosisName,database=database,provider=provider):
                # Notify inhibit blocks to temporarily halt updates to SQC
                # handler.sendTimestampedSignal(self.parentuuid, "inhibit", "", "",time)
                from ils.diagToolkit.finalDiagnosis import postDiagnosisEntry
                postDiagnosisEntry(applicationName, familyName, finalDiagnosisName, fd.uuid, fd.parentuuid, database, provider)
            system.util.invokeAsynchronous(work)
        else:
            print "The diagnosis just became FALSE"
            from ils.diagToolkit.finalDiagnosis import clearDiagnosisEntry
            clearDiagnosisEntry(applicationName, familyName, finalDiagnosisName, database, provider)

        # Pass the input through to the output
        self.value = value
        self.quality=quality
        self.time = ts
        self.postValue('out',value,quality,ts)
        
        print "FinalDiagnosis.acceptValue: COMPLETE"
    
        # The base method leaves the aux data unchanged.
    
    # Trigger property and connection notifications on the block
    def notifyOfStatus(self):
        self.handler.sendConnectionNotification(self.uuid, 'out', self.state,'good',0)
        
    # Propagate the most recent state of the block. 
    def propagate(self):
        if self.state <> "UNSET":
            self.postValue('out',str(self.state),self.quality,self.time)
    
    def getAuxData(self, aux):
        '''
        NOTE: The UUID supplied is from the parent, a diagram. The database interactions
               are all based on a the block name which is  the data structure.
        
        The aux data structure is a Python list of three dictionaries. These are:
        properties, lists and maplists.
         
        Fill the aux structure with values from the database.
        '''
        self.log.infof("In finalDiagnosis.getAuxData() with %s", str(aux))
        
        db = self.handler.getDefaultDatabase(self.parentuuid)
        provider = self.handler.getDefaultTagProvider(self.parentuuid)
        
        self.log.tracef("Using database: %s and tag provider: %s ", db, provider)
        
        applicationName = self.handler.getApplication(self.parentuuid).getName()
        familyName = self.handler.getFamily(self.parentuuid).getName()
        theFinalDiagnosis = self.handler.getBlock(self.parentuuid, self.uuid)
        finalDiagnosisName = theFinalDiagnosis.getName()
        self.log.infof("The final diagnosis: %s", str(theFinalDiagnosis))
        
#        finalDiagnosisName = self.name
#        self.log.infof("The final diagnosis (self.name): %s", str(theFinalDiagnosis))
        
#        finalDiagnosisName = theFinalDiagnosis.name
#        self.log.infof("The final diagnosis (self.name #2): %s", str(theFinalDiagnosis))
        
        self.log.tracef("Application: %s", applicationName)
        self.log.tracef("Family: %s", familyName)
        self.log.tracef("Final Diagnosis: %s", finalDiagnosisName)
        
        finalDiagnosisName = "TESTFD1_2_2"
        self.log.infof("***********************************************")
        self.log.infof("Hard-CODED Final Diagnosis: %s", finalDiagnosisName)
        self.log.infof("***********************************************")

        properties = aux[0]
        lists = aux[1]

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
               % (applicationName, familyName, finalDiagnosisName)
        ds = system.db.runQuery(SQL,db)
        
        if len(ds) == 0:
            self.log.warnf("Warning: No records found!")
            self.log.warnf(SQL)
    
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
    
        SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (applicationName)
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
        
        self.log.tracef("properties: %s", str(properties))
        self.log.tracef("lists: %s", str(lists))
    
    
    def setAuxData(self, data):
        '''
        Set aux data in an external database. This base method does nothing
        '''
        self.log.infof("In finalDiagnosis.setAuxData() with %s", str(data))
        
        db = self.handler.getDefaultDatabase(self.parentuuid)
        provider = self.handler.getDefaultTagProvider(self.parentuuid)
        
        self.log.tracef("Using database: %s and tag provider: %s ", db, provider)
        
        applicationName = self.handler.getApplication(self.parentuuid).getName()
        familyName = self.handler.getFamily(self.parentuuid).getName()
        theFinalDiagnosis = self.handler.getBlock(self.parentuuid, self.uuid)
        self.log.infof("The final diagnosis: %s", str(theFinalDiagnosis))
        finalDiagnosisName = theFinalDiagnosis.getName()

        self.log.tracef("Application: %s", applicationName)
        self.log.tracef("Family: %s", familyName)
        self.log.tracef("Final Diagnosis: %s", finalDiagnosisName)
        
        finalDiagnosisName = "TESTFD1_2_2"
        self.log.infof("***********************************************")
        self.log.infof("Hard-CODED Final Diagnosis: %s", finalDiagnosisName)
        self.log.infof("***********************************************")
                
        properties = data[0]
        lists = data[1]
        
        self.log.tracef("Properties: %s", str(properties))
        self.log.tracef("Lists: %s", str(lists))
        
        self.log.infof("Show Explanation with Recommendation: %s", str(properties.get("ShowExplanationWithRecommendation","0")))
        
        SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (applicationName)
        applicationId = system.db.runScalarQuery(SQL,db)
        self.log.infof("The application Id is: %s", str(applicationId))
        if applicationId == None:
            SQL = "insert into DtApplication (ApplicationName) values (?)"
            applicationId = system.db.runPrepUpdate(SQL, [applicationName], db, getKey=1)
        
        SQL = "SELECT familyId FROM DtFamily "\
              " WHERE ApplicationId = %s"\
              "  AND familyName = '%s'" % (applicationId,familyName)
        familyId = system.db.runScalarQuery(SQL,db)
        self.log.infof("The family Id is: %s", str(familyId))
        if familyId == None:
            SQL = "INSERT INTO DtFamily (applicationId,familyName,familyPriority) "\
                   " VALUES (?, ?, 0.0)"
            self.log.infof(SQL)
            familyId = system.db.runPrepUpdate(SQL, [applicationId, familyName], db, getKey=1)
            
        SQL = "SELECT finalDiagnosisId FROM DtFinalDiagnosis "\
              " WHERE FamilyId = %s"\
              "  AND finalDiagnosisName = '%s'" % (familyId, finalDiagnosisName)
        self.log.infof(SQL)
        fdId = system.db.runScalarQuery(SQL,db)
        self.log.infof("The final diagnosis Id is: %s", str(fdId))
        if fdId == None:
            self.log.infof("Inserting a new final diagnosis...")
            recTime = system.date.now()
            recTime = system.date.addMonths(recTime, -12)
            recTime = toDateString(recTime)
            # When we insert a new final diagnosis it has to be false until it runs...
            SQL = "INSERT INTO DtFinalDiagnosis (familyId, finalDiagnosisName, finalDiagnosisLabel, finalDiagnosisPriority, calculationMethod, "\
                   "postTextRecommendation, PostProcessingCallback, refreshRate, textRecommendation, active, explanation, "\
                   "trapInsignificantRecommendations, constant, manualMoveAllowed, comment, showExplanationWithRecommendation, timeOfMostRecentRecommendationImplementation)"\
                   " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            self.log.infof("SQL: %s", SQL)
            try:
                args =  [familyId, finalDiagnosisName, properties.get("FinalDiagnosisLabel",""), properties.get("Priority","0.0"), properties.get("CalculationMethod",""),\
                            properties.get("PostTextRecommendation","0"), properties.get("PostProcessingCallback",""),\
                            properties.get("RefreshRate","1"), properties.get("TextRecommendation",""), properties.get("Active","0"), properties.get("Explanation","0"),\
                            properties.get("TrapInsignificantRecommendations","1"), properties.get("Constant","0"),\
                            properties.get("ManualMoveAllowed","0"), properties.get("Comment",""), properties.get("ShowExplanationWithRecommendation","0"), recTime]
                self.log.infof("Arguments (%d): %s", len(args), str(args))
                fdId = system.db.runPrepUpdate(SQL, args, db, getKey=1)
                self.log.infof("Inserted a new final diagnosis with id: %d", fdId)
            except:
                self.logExceptionCause("Inserting a new Final Diagnosis", self.log)
                return
        else:
            self.log.infof("Updating an existing final diagnosis...")
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
            
            self.log.infof("SQL: %s", SQL)
            self.log.infof("Args: %s", str(args))
            rows = system.db.runPrepUpdate(SQL, args, db)
            self.log.infof("Updated %d rows", rows)
            
        ''' 
        Delete any recommendations that may exist for this final diagnosis to avoid foreign key constraints when we delete and recreate the DtRecommendationDefinitions.
        (I'm not sure this is the correct thing to do - this will affect a live system.  Not sure we want to do this just because they press OK to update the comment, explanation, etc.
        '''
        self.log.infof("Deleting existing recommendations...")
        SQL = "select RecommendationDefinitionId from DtRecommendationDefinition where FinalDiagnosisId = %s" % (fdId)
        self.log.infof(SQL)
        pds = system.db.runQuery(SQL, db)
        totalRows = 0
        for record in pds:
            SQL = "delete from DtRecommendation where RecommendationDefinitionId = %s" % (record["RecommendationDefinitionId"])
            self.log.infof(SQL)
            rows = system.db.runUpdateQuery(SQL, db)
            totalRows = totalRows + rows
        self.log.infof("Deleted %d recommendations prior to updating the Recommendation Definitions...", totalRows)
        
        # Update the list of outputs used
        self.log.infof("Deleting Recommendation Definitions...")
        SQL = "DELETE FROM DtRecommendationDefinition WHERE finalDiagnosisId = %s" % (str(fdId))
        self.log.infof(SQL)
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
            self.log.infof("Inserting a recommendation definition for %s...", instr)
            SQL = "INSERT INTO DtRecommendationDefinition(finalDiagnosisId,quantOutputId) "\
              "SELECT %s,quantOutputId FROM DtQuantOutput QO"\
              " WHERE QO.applicationID = %s "\
              "  AND QO.quantOutputName IN (%s)" \
              % (fdId,applicationId,instr)
            self.log.infof(SQL)
            rows=system.db.runUpdateQuery(SQL,db)
    
        self.log.infof("Inserted %d recommendation definitions", rows)