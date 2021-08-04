'''
Copyright 2014 ILS Automation

**************************************************************************************
* WARNING: This Python is not reloaded dynamically!                                         *
* Any changes here requires a full gateway restart since this runs in the gateway *
**************************************************************************************
'''

import system
from ils.common.cast import toBit
from ils.common.database import toDateString
from ils.log.LogRecorder import LogRecorder
from ils.sfc.common.util import logExceptionCause

def getClassName():
    return "FinalDiagnosis"

# A FinalDiagnosis block receives a truth-value from an SQC
# or other block upstream and deduces the reason for the issue.
#
from ils.block import basicblock
#import ils.diagToolkit.finalDiagnosis as fd

callback = "fd.evaluate"

class FinalDiagnosis(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.initialize()
        self.state = "UNKNOWN"
        self.handler.setAlerterClass(self.getClassName())
        self.log = LogRecorder(__name__)
        self.log.infof("Instantiating a Final Diagnosis...")
    
    # Set attributes custom to this class
    def initialize(self):
        self.className = 'ils.block.finaldiagnosis.FinalDiagnosis'       
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
    def acceptValue(self, port, value, quality, ts):
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
            
    '''
    Set aux data in an external database. This base method does nothing
    
    **************************************************************************************
    * WARNING: This Python is not reloaded dynamically!                                         *
    * Any changes here requires a full gateway restart since this runs in the gateway *
    **************************************************************************************
    '''
    def setAuxData(self, data):
        self.log.infof("setAuxData() with %s", str(data))
        properties = data[0]
        outputs = data[1].get("OutputsInUse", [])
        
        db = self.handler.getDefaultDatabase(self.parentuuid)
        provider = self.handler.getDefaultTagProvider(self.parentuuid)
        self.log.infof("Using database: %s and tag provider: %s ", db, provider)
        
        applicationName = self.handler.getApplication(self.parentuuid).getName()
        familyName = self.handler.getFamily(self.parentuuid).getName()
        self.log.infof("Found Application: %s and Family: %s", applicationName, familyName)
        
        theFinalDiagnosis = self.handler.getBlock(self.parentuuid, self.uuid)
        fdName = theFinalDiagnosis.getName()
        self.log.infof("Final Diagnosis: %s", fdName)
        
        SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (applicationName)
        applicationId = system.db.runScalarQuery(SQL, db)
        self.log.infof("The application Id is: %s", str(applicationId))
        if applicationId == None:
            SQL = "insert into DtApplication (ApplicationName) values (?)"
            applicationId = system.db.runPrepUpdate(SQL, [applicationName], db, getKey=1)
    
        SQL = "SELECT familyId FROM DtFamily "\
              " WHERE ApplicationId = %s"\
              "  AND familyName = '%s'" % (applicationId, familyName)
        familyId = system.db.runScalarQuery(SQL,db)
        self.log.infof("The family Id is: %s", str(familyId))
        if familyId == None:
            SQL = "INSERT INTO DtFamily (applicationId,familyName,familyPriority) VALUES (?, ?, 0.0)"
            self.log.infof(SQL)
            familyId = system.db.runPrepUpdate(SQL, [applicationId, familyName], db, getKey=1)
        
        SQL = "SELECT finalDiagnosisId FROM DtFinalDiagnosis "\
              " WHERE FamilyId = %s"\
              "  AND finalDiagnosisName = '%s'" % (familyId, fdName)
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
                args =  [familyId, fdName, properties.get("FinalDiagnosisLabel",""), properties.get("Priority","0.0"), properties.get("CalculationMethod",""),\
                            properties.get("PostTextRecommendation","0"), properties.get("PostProcessingCallback",""),\
                            properties.get("RefreshRate","1"), properties.get("TextRecommendation",""), properties.get("Active","0"), properties.get("Explanation","0"),\
                            properties.get("TrapInsignificantRecommendations","1"), properties.get("Constant","0"),\
                            properties.get("ManualMoveAllowed","0"), properties.get("Comment",""), properties.get("ShowExplanationWithRecommendation","0"), recTime]
                self.log.infof("Arguments (%d): %s", len(args), str(args))
                fdId = system.db.runPrepUpdate(SQL, args, db, getKey=1)
                self.log.infof("Inserted a new final diagnosis with id: %d", fdId)
            except:
                logExceptionCause("Inserting a new Final Diagnosis", self.log)
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
        
        instr = None
        for output in outputs:
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
              % (fdId, applicationId, instr)
            self.log.infof(SQL)
            rows=system.db.runUpdateQuery(SQL,db)
    
        self.log.infof("Inserted %d recommendation definitions", rows)