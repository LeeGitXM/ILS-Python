#  Copyright 2014 ILS Automation

import system
from ils.block import basicblock
from ils.log.LogRecorder import LogRecorder

def getClassName():
    return "SQCDiagnosis"

# A SQCDiagnosis block receives a truth-value from an SQC
# or other block upstream and deduces the reason for the issue.

class SQCDiagnosis(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.log = LogRecorder(__name__)
        self.log.infof("Instantiating a SQC Diagnosis...")
        self.initialize()
    
    # Set attributes custom to this class
    def initialize(self):
        self.className = 'ils.block.sqcdiagnosis.SQCDiagnosis'
#        self.properties['Label'] = {'value':'SQCDiagnosis','editable':'True'}
        self.properties['TagPath'] = { 'value':'','binding':'','bindingType':'TAG_WRITE','editable':'True'}
    
        self.inports = [{'name':'in','type':'TRUTHVALUE','allowMultiple':False}]
        self.outports= [{'name':'out','type':'TRUTHVALUE'}]

        
    # Return a dictionary describing how to draw an icon
    # in the palette and how to create a view from it.
    def getPrototype(self):
        proto = {}
        proto['auxData'] = True
        proto['iconPath']= "Block/icons/palette/SQC_diagnosis.png"
        proto['label']   = "SQCDiagnosis"
        proto['tooltip']        = "Conclude a diagnosis from an upstream SQC block based on input"
        proto['tabName']        = 'Conclusion'
        proto['viewBackgroundColor'] = '0xFCFEFE'
        proto['viewLabel']      = "SQC\nDiagnosis"
        proto['blockClass']     = self.getClassName()
        proto['blockStyle']     = 'square'
        proto['viewFontSize']       = 14
        proto['viewHeight']     = 80
        proto['inports']        = self.getInputPorts()
        proto['editorClass']   = "com.ils.blt.designer.config.SQCDiagnosisConfiguration"
        proto['outports']       = self.getOutputPorts()
        proto['viewWidth']      = 100
        return proto
            
    # Called when a value has arrived on one of our input ports
    # For now we record it to a tag and pass it through to the output
    def acceptValue(self,port,value,quality,time):
        if not self.state==str(value):
            self.log.trace("Accepting a new value <%s> for an SQC diagnosis block..." % (str(value)))
            self.state = str(value)
        
            # Write to the tag, if it exists
            prop = self.properties['TagPath']
            path = prop['binding']
            if len(path)>0:
                self.handler.updateTag(self.parentuuid,path,str(value),quality,time)
            
        # Pass the input through to the output
        self.value = value
        self.quality=quality
        self.time = time
        self.postValue('out',value,quality,time)
                
        handler = self.handler
        database = handler.getDefaultDatabase(self.parentuuid)
        
        sqcDiagnosis = handler.getBlock(self.parentuuid, self.uuid)
        sqcDiagnosisName = sqcDiagnosis.getName()
        
        # If the block got through migration and still has a '-GDA' as part of its name strip it off
        tokens=sqcDiagnosisName.split('-GDA')
        sqcDiagnosisName=tokens[0]
        
        # If we can find the block by UUID then the name and the parent have got to be correct
        self.log.trace("Updating a SQC diagnosis by uuid...")
        SQL = "update DtSQCDiagnosis set SQCDiagnosisName = '%s', Status = '%s', DiagramUUID = '%s' where SQCDiagnosisUUID = '%s'"\
             % (sqcDiagnosisName, str(value), str(self.parentuuid), str(self.uuid))
        try:
            rows=system.db.runUpdateQuery(SQL, database)
            if rows > 0:
                self.log.trace("...success")
                return
        
            # The block Id could not be found - see if the block name exists.
            self.log.trace("...that didn't work, try updating by name...")
            SQL = "update DtSQCDiagnosis set SQCDiagnosisUUID = '%s', DiagramUUID = '%s', Status = '%s' where SQCDiagnosisName = '%s'" \
                % (str(self.uuid), str(self.parentuuid), str(value), sqcDiagnosisName)
            print SQL
            rows=system.db.runUpdateQuery(SQL, database)
            if rows > 0:
                self.log.trace("...success")
                return
        
            # The name couldn't be found either so this must be a totally new SQC diagnosis which we have never seen before
            self.log.trace("...that didn't work either, try inserting a new record, this must be a new block...")

            applicationName = handler.getApplication(self.parentuuid).getName()
            familyName = handler.getFamily(self.parentuuid).getName()
            self.log.trace("From the BLT handler, the family name is: %s" % (familyName))
            from ils.diagToolkit.common import fetchFamilyId
            familyId = fetchFamilyId(familyName, database)
            if familyId == None:
                self.log.error("Unable to insert the SQC diagnosis into the database because the family <%s> is undefined" % (familyName))
                return
        
            print "Application: %s\nFamily: %s (%d)" % (applicationName, familyName, familyId)
        
            SQL = "insert into DtSQCDiagnosis (SQCDiagnosisUUID, DiagramUUID, Status, SQCDiagnosisName, FamilyId) "\
                "values ('%s', '%s', '%s', %s)" % (str(self.uuid), str(self.parentuuid), str(value), sqcDiagnosisName, str(familyId))
            rows=system.db.runUpdateQuery(SQL, database)
            if rows > 0:
                print "...success"
                return
        
            self.log.error("Unable to update a change in value for an SQC Diagnosis")
        except:
            from ils.common.error import catchError
            txt=catchError(__name__, "Error handling a new value for an SQC Diagnosis")
            self.log.error(txt)

    # Trigger property and connection notifications on the block
    def notifyOfStatus(self):
        self.handler.sendConnectionNotification(self.uuid, 'out', self.state,'good',0)
        
    # Propagate the most recent state of the block. 
    def propagate(self):
        if self.state <> "UNSET":
            self.postValue('out',str(self.state),self.quality,self.time)
            
    # Reset the block. This default implementation
    # sends notifications on all output connections.
    def reset(self):
        try:
            basicblock.BasicBlock.reset(self)
            handler = self.handler
            database = handler.getDefaultDatabase(self.parentuuid)
            sqcDiagnosis = handler.getBlock(self.parentuuid, self.uuid)
            sqcDiagnosisName = sqcDiagnosis.getName()
            
            self.log.info("   ... setting the lastResetTime for SQC diagnosis named: %s" % (sqcDiagnosisName))
            SQL = "update DtSQCDiagnosis set LastResetTime = getdate(), Status = 'UNKNOWN' where SQCDiagnosisUUID = '%s'" % (str(self.uuid))
            rows = system.db.runUpdateQuery(SQL, database)
            self.log.info("      ...updated %i rows" % (rows))
        except:
            from ils.common.error import catchError
            txt=catchError(__name__, "Error resetting a SQC Diagnosis")
            self.log.error(txt)