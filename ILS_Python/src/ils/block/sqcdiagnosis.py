#  Copyright 2014 ILS Automation

import system
from ils.common.database import toDateString
from ils.block import basicblock
from ils.log import getLogger
from ils.sfc.common.util import logExceptionCause
log =getLogger(__name__)

def getClassName():
    return "SQCDiagnosis"

# A SQCDiagnosis block receives a truth-value from an SQC
# or other block upstream and deduces the reason for the issue.

class SQCDiagnosis(basicblock.BasicBlock):
    def __init__(self):
        basicblock.BasicBlock.__init__(self)
        self.log =getLogger(__name__)
        self.log.infof("Instantiating a new SQC Diagnosis...")
        self.initialize()
    
    # Set attributes custom to this class
    def initialize(self):
        self.className = 'ils.block.sqcdiagnosis.SQCDiagnosis'
#        self.properties['Label'] = {'value':'SQCDiagnosis','editable':'True'}

        '''
        Removed because if they want the state of the block to go to a tag then they should connect an output block.
        The real purpose of this block is to provide a collection point for the SQC Plotting system.  PAH - 8/12/2021
        '''
#        self.properties['TagPath'] = { 'value':'','binding':'','bindingType':'TAG_WRITE','editable':'True'}
    
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
        
            '''
            Commented out when the tagPath property was removed - PH 8/12/2021
            # Write to the tag, if it exists
            prop = self.properties['TagPath']
            path = prop['binding']
            if len(path)>0:
                self.handler.updateTag(self.parentuuid,path,str(value),quality,time)
            '''
            
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
            

'''
Synchronize the aux data in the block with the SQL*Server database.
'''
def setAuxData(block, applicationName, familyName, diagramUUID, blockName, auxData, db):
    from ils.blt.util import getProperty
    blockUUID = str(block.getBlockId())
    log.infof("In %s.setAuxData() with %s - %s - %s - %s - %s", __name__, applicationName, familyName, blockName, blockUUID, str(auxData))
    
    log.tracef("************************************************")
    log.tracef("* Saving SQC Diagnosis %s Data to <%s>*", blockName, db)
    log.tracef("************************************************")
    
    # All of these things in the auxData general purpose container are Linked HashMaps which is some Jave class that is more like a This is a LinkedHashMap
    lists = auxData.getLists()
    log.tracef("Lists: (a %s), %s", type(lists).__name__, str(lists)) 

    mapLists = auxData.getMapLists()
    log.tracef("Map Lists: (a %s), %s", type(mapLists).__name__, str(mapLists)) 
    
    properties = auxData.getProperties()
    log.tracef("Properties: (a %s), %s", type(properties).__name__, str(properties)) 
    
    ''' 
    The properties should have a SQC diagnosis label but there is a bigger problem here, mainly that the label isn't showing
    up on property editor.  I think the label is important for the SQC plotting facility, but for now there needs to be another way to get it there.
    '''
    sqcDiagnosisLabel = ""
  
    SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (applicationName)
    applicationId = system.db.runScalarQuery(SQL, db)
    log.tracef("The application Id is: %s", str(applicationId))
    if applicationId == None:
        SQL = "insert into DtApplication (ApplicationName) values (?)"
        applicationId = system.db.runPrepUpdate(SQL, [applicationName], db, getKey=1)

    SQL = "SELECT familyId FROM DtFamily "\
          " WHERE ApplicationId = %s"\
          "  AND familyName = '%s'" % (applicationId, familyName)
    familyId = system.db.runScalarQuery(SQL,db)
    log.tracef("The family Id is: %s", str(familyId))
    if familyId == None:
        SQL = "INSERT INTO DtFamily (applicationId,familyName,familyPriority) VALUES (?, ?, 0.0)"
        log.tracef(SQL)
        familyId = system.db.runPrepUpdate(SQL, [applicationId, familyName], db, getKey=1)

    ''' 
    The UUID assigned to a SQC Diagnosis does appear to be Universally Unique.  
    Copy and pasting a SQC Diagnosis results in a new UUID for the new diagnosis.  
    (I shouldn't really include the family ID here, the UUID should be enough)
    '''
    SQL = "SELECT sqcDiagnosisId FROM DtSqcDiagnosis "\
          " WHERE FamilyId = %s"\
          "  AND SQCDiagnosisUUID = '%s'" % (familyId, blockUUID)
    log.tracef(SQL)
    blockId = system.db.runScalarQuery(SQL, db)
    log.tracef("The SQC diagnosis Id is: %s", str(blockId))
    if blockId == None:
        log.tracef("*** Inserting a new SQC diagnosis ***")
        lastResetTime = system.date.now()
        lastResetTime = system.date.addMonths(lastResetTime, -12)
        lastResetTime = toDateString(lastResetTime)
        status = "New"
        
        SQL = "INSERT INTO DtSqcDiagnosis (SqcDiagnosisName, SqcDiagnosisLabel, Status, FamilyId, "\
               "SqcDiagnosisUUID, DiagramUUID, lastResetTime)"\
               " VALUES (?,?,?,?,?,?,?)"
        log.tracef("SQL: %s", SQL)
        try:
            args =  [blockName, sqcDiagnosisLabel, status, familyId, blockUUID, diagramUUID, lastResetTime]
            log.tracef("Arguments (%d): %s", len(args), str(args))
            blockId = system.db.runPrepUpdate(SQL, args, db, getKey=1)
            log.tracef("Inserted a new SQC diagnosis with id: %d", blockId)
        except:
            logExceptionCause("Inserting a new SQC Diagnosis", log)
            return
    else:
        log.tracef("*** Updating an existing SQC diagnosis ***")

        ''' I shouldn't really need to update the UUID here, it should never change, but there may be old systems where it wasn't stored. '''
        SQL = "UPDATE DtSqcDiagnosis SET SqcDiagnosisName=?, SqcDiagnosisLabel=?, familyId=?, SqcDiagnosisUUID=?, DiagramUUID=? "\
            " WHERE SqcDiagnosisId = ?"

        args = [blockName, sqcDiagnosisLabel, familyId, blockUUID, diagramUUID, blockId]
        
        log.tracef("SQL: %s", SQL)
        log.tracef("Args: %s", str(args))
        rows = system.db.runPrepUpdate(SQL, args, db)
        log.tracef("Updated %d rows", rows)

    return blockId

def removeDeletedBlocksFromDatabase(ids, db):
    log.infof("Removing SQC diagnosis ids: %s", str(ids))
    totalRows = 0
    for ID in ids:
        SQL = "Delete from DtSqcDiagnosis where SQCDiagnosisId = %s" % (str(ID))
        rows = system.db.runUpdateQuery(SQL, db)
        totalRows = totalRows + rows
    log.tracef("Deleted %d SQC Diagnosis", totalRows)