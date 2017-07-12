'''
Created on Sep 19, 2014

@author: Pete
'''

import system, time
from java.util import Date, Calendar
import system.ils.blt.diagram as scriptingInterface
from ils.queue.commons import getQueueForDiagnosticApplication

log = system.util.getLogger("com.ils.diagToolkit")

# -------------------------- Helper methods ----------------------
# Return the ProcessDiagram at the specified path
def getDiagram(project, diagramPath):
    print "Getting the process diagram named: %s" % (diagramPath)
    
    # The descriptor paths are :-separated, the input uses /
    # the descriptor path starts with ":root:", 
    # the input starts with the application
    
    descriptors = scriptingInterface.getDiagramDescriptors()
    handler = scriptingInterface.getHandler()

    for desc in descriptors:
        path = desc.path[6:]
        
        if diagramPath == path:
            log.trace("*** Found it ***")
            return handler.getDiagram(desc.id)
    
    log.errorf("Unable to find diagram: %s", diagramPath)
    return None  


# Check if the timestamps of two tags are consistent.  
# This uses theLastChange property of a tag, so what would happen if we received two consecutive identical values?
def checkConsistency(tagPath1, tagPath2, tolerance=5, recheckInterval=1.0, timeout=10):
    log = system.util.getLogger("com.ils.diagToolkit")
    startTime = Date().getTime()
    isConsistent = False
    log.trace("Checking if %s and %s are consistent..." % (tagPath1, tagPath2))
    while isConsistent == False and ((Date().getTime() - startTime) / 1000) < timeout:
        log.trace("Checking consistency...")
        vals = system.tag.readAll([tagPath1, tagPath2])
        timestamp1 = vals[0].timestamp
        cal1 = Calendar.getInstance()
        cal1.setTime(timestamp1)
        
        timestamp2 = vals[1].timestamp
        cal2 = Calendar.getInstance()
        cal2.setTime(timestamp2)

        if abs(cal1.getTimeInMillis() - cal2.getTimeInMillis()) < tolerance * 1000:
            log.trace("%s and %s are consistent!" % (tagPath1, tagPath2))
            isConsistent = True
            return isConsistent
        
        time.sleep(recheckInterval)

    log.trace("** %s and %s are NOT consistent **" % (tagPath1, tagPath2))
    return isConsistent

def insertApplicationQueueMessage(applicationName, message, status="info", db=""):
    key = getQueueForDiagnosticApplication(applicationName, db)
    from ils.queue.message import insert
    insert(key, status, message)
    
# Check if the timestamp of the tag is less than a certain tolerance older then theTime, or the current time if theTime 
# is omitted.  This uses theLastChange property of a tag, so what would happen if we received two consecutive identical values?
def checkFreshness(tagPath, theTime="now", provider="XOM", tolerance=-1, recheckInterval=1.0, timeout=-1.0):
    log = system.util.getLogger("com.ils.diagToolkit")
    
    if tolerance < 0.0:
        print "Using the default freshness tolerance"
        tolerance = system.tag.read("[%s]Configuration/DiagnosticToolkit/freshnessToleranceSeconds" % (provider)).value
    if timeout < 0.0:
        print "Using the default freshness timeout"
        timeout = system.tag.read("[%s]Configuration/DiagnosticToolkit/freshnessTimeoutSeconds" % (provider)).value

    startTime = Date().getTime()
    isFresh = False
    log.trace("Checking if %s is fresh..." % (tagPath))
    while isFresh == False and ((Date().getTime() - startTime) / 1000) < timeout:
        log.trace("Checking freshness...")
        qv = system.tag.read(tagPath)
        timestamp = qv.timestamp
        cal1 = Calendar.getInstance()
        cal1.setTime(timestamp)

        cal2 = Calendar.getInstance()
        if theTime == "now" or theTime == None:
            cal2.setTime(Date())
        else:
            cal2.setTime(theTime)

        if abs(cal1.getTimeInMillis()) > cal2.getTimeInMillis() - tolerance * 1000:
            log.trace("%s is now fresh!" % (tagPath))
            isFresh = True
            return isFresh

        time.sleep(recheckInterval)

    log.trace("** %s is NOT fresh **" % (tagPath))
    return isFresh


# Check that tag1 is fresher than tag2.  
# The timeout here is in seconds, the default time to wait is 1 minute.
def checkFresher(tagPath1, tagPath2, recheckInterval=1.0, timeout=60):
    log = system.util.getLogger("com.ils.diagToolkit")
    startTime = Date().getTime()
    isFresher = False
    log.trace("Checking if %s is fresher than %s..." % (tagPath1, tagPath2))
    while isFresher == False and ((Date().getTime() - startTime) / 1000) < timeout:
        log.trace("Checking freshness...")
        vals = system.tag.readAll([tagPath1, tagPath2])
        timestamp1 = vals[0].timestamp
        cal1 = Calendar.getInstance()
        cal1.setTime(timestamp1)
        
        timestamp2 = vals[1].timestamp
        cal2 = Calendar.getInstance()
        cal2.setTime(timestamp2)
        
        if cal1.getTimeInMillis() > cal2.getTimeInMillis():
            log.trace("%s is now fresher than %s!" % (tagPath1, tagPath2))
            isFresher = True
            return isFresher
        
        time.sleep(recheckInterval)

    log.trace("** %s is NOT fresher than %s **" % (tagPath1, tagPath2))
    return isFresher 

# Fetch the time of the last recommendation, which should be the same as when the final diagnosis last became True
def fetchDiagnosisActiveTime(finalDiagnosisId, database = ""):
    SQL = "select LastRecommendationTime from DtFinalDiagnosis where FinalDiagnosisId = %s" % (str(finalDiagnosisId))
    log.trace(SQL)
    lastRecommendtaionTime = system.db.runScalarQuery(SQL, database)
    log.trace("The last recommendation time is: %s" % (str(lastRecommendtaionTime)))
    return lastRecommendtaionTime 


# This gets called at the beginning of each recommendation management cycle.  It clears all of the dynamic attributes of 
# a Quant Output.  
def clearQuantOutputRecommendations(application, database=""):
    SQL = "update DtQuantOutput set FeedbackOutput = 0.0, OutputLimitedStatus = '', OutputLimited = 0, "\
        " OutputPercent = 0.0, FeedbackOutputManual = 0.0, FeedbackOutputConditioned = 0.0, "\
        " ManualOverride = 0, Active = 0 "\
        " from DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtRecommendationDefinition RD "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = DtQuantOutput.QuantOutputId "\
        " and A.Application = '%s' " % (application)
    log.trace(SQL)
    system.db.runUpdateQuery(SQL, database)
    return


# Fetch all of the active final diagnosis for an application.
# Order the diagnosis from most import to least important - remember that the numeric priority is such that
# low numbers are higher priority than high numbers. 
def fetchActiveDiagnosis(applicationName, database=""):
    SQL = "select A.ApplicationName, F.FamilyName, F.FamilyId, FD.FinalDiagnosisName, FD.FinalDiagnosisPriority, FD.FinalDiagnosisId, "\
        " FD.Constant, DE.DiagnosisEntryId, F.FamilyPriority, DE.Multiplier, "\
        " DE.RecommendationErrorText, FD.PostTextRecommendation, FD.PostProcessingCallback, FD.TextRecommendation, FD.CalculationMethod  "\
        " from DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtDiagnosisEntry DE "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and DE.Status = 'Active' " \
        " and (FD.Constant = 0 or not(DE.RecommendationStatus in ('WAIT','NO-DOWNLOAD','DOWNLOAD'))) " \
        " and A.ApplicationName = '%s'"\
        " order by FamilyPriority ASC, FinalDiagnosisPriority ASC"  % (applicationName) 
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

# Fetch all of the active final diagnosis for an application.
# Order the diagnosis from most import to least important - remember that the numeric priority is such that
# low numbers are higher priority than high numbers. 
def fetchHighestActiveDiagnosis(applicationName, database=""):
    SQL = "select A.ApplicationName, F.FamilyName, F.FamilyId, FD.FinalDiagnosisName, FD.FinalDiagnosisPriority, FD.FinalDiagnosisId, "\
        " FD.Constant, DE.DiagnosisEntryId, F.FamilyPriority, DE.Multiplier, "\
        " DE.RecommendationErrorText, FD.PostTextRecommendation, FD.PostProcessingCallback, FD.TextRecommendation, FD.CalculationMethod  "\
        " from DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtDiagnosisEntry DE "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and DE.Status = 'Active' "\
        " and FD.Active = 1 "\
        " and (FD.Constant = 0 or not(DE.RecommendationStatus in ('WAIT','NO-DOWNLOAD','DOWNLOAD'))) "\
        " and A.ApplicationName = '%s'"\
        " order by FamilyPriority ASC, FinalDiagnosisPriority ASC"  % (applicationName) 
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds


# Fetch all of the active final diagnosis for an application.
# Order the diagnosis from most import to least important - remember that the numeric priority is such that
# low numbers are higher priority than high numbers. 
def fetchActiveFamilies(applicationName, database=""):
    SQL = "select distinct A.ApplicationName, F.FamilyName, F.FamilyId "\
        " from DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtDiagnosisEntry DE "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and DE.Status = 'Active' " \
        " and not (FD.CalculationMethod != 'Constant' and (DE.RecommendationStatus in ('WAIT','NO-DOWNLOAD','DOWNLOAD'))) " \
        " and A.ApplicationName = '%s'"\
        " order by FamilyName ASC"  % (applicationName) 
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

# Look up the final diagnosis and family given an application and a quantoutput.
# I'm not sure that I need the application here because there is a unique index on the quant output
# name - which I'm not sure is correct - so if we ever remove that unique index then this will still work.
def fetchActiveFinalDiagnosisForAnOutput(application, quantOutputId, database=""):
    SQL = "select FD.FinalDiagnosisName, FD.FinalDiagnosisId, F.FamilyName "\
        " from DtFinalDiagnosis FD, DtFamily F, DtApplication A, DtQuantOutput QO, DtRecommendationDefinition RD "\
        " where A.ApplicationId = F.ApplicationId "\
        " and FD.FamilyId = F.FamilyId "\
        " and A.ApplicationName = '%s' "\
        " and F.FamilyId = FD.FamilyId "\
        " and QO.ApplicationId = A.ApplicationId "\
        " and RD.quantOutputId = QO.QuantOutputId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and FD.Active = 1 "\
        " and QO.QuantOutputId = %s " % (application, str(quantOutputId))
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

def fetchActiveOutputsForPost(post, database=""):
    SQL = "select distinct A.ApplicationName, "\
        " QO.QuantOutputName, QO.TagPath, QO.OutputLimitedStatus, QO.OutputLimited, "\
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.IncrementalOutput, "\
        " QO.CurrentSetpoint, QO.FinalSetpoint, QO.DisplayedRecommendation, QO.QuantOutputId, QO.DownloadAction, QO.DownloadStatus "\
        " from TkPost P, TkUnit U, DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO "\
        " where P.PostId = U.PostId "\
        " and U.UnitId = A.UnitId "\
        " and A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and P.Post = '%s' "\
        " and QO.Active = 1"\
        " order by A.ApplicationName, QO.QuantOutputName"  % (post)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

def fetchActiveTextRecommendationsForPost(post, database=""):
    SQL = "select distinct TR.TextRecommendation, FD.PostProcessingCallback, A.ApplicationName, DE.DiagnosisEntryId "\
        " from TkPost P, TkUnit U, DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtDiagnosisEntry DE, DtTextRecommendation TR "\
        " where P.PostId = U.PostId "\
        " and U.UnitId = A.UnitId "\
        " and A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and DE.DiagnosisEntryId = TR.DiagnosisEntryId "\
        " and P.Post = '%s' "  % (post)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

# Fetch applications for a console
def fetchApplicationsForPost(post, database=""):
    SQL = "select distinct A.ApplicationName "\
        " from TkPost P, TkUnit U, DtApplication A "\
        " where P.PostId = U.PostId "\
        " and U.UnitId = A.UnitId "\
        " and P.Post = '%s' "\
        " order by A.ApplicationName"  % (post)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

# Lookup the application Id given the name
def fetchApplicationId(application, database=""):
    SQL = "select ApplicationId from DtApplication where Application = '%s'" % (application)
    log.trace(SQL)
    applicationId = system.db.runScalarQuery(SQL, database)
    return applicationId

# Lookup the family Id given the name
def fetchFamilyId(familyName, database=""):
    SQL = "select FamilyId from DtFamily where FamilyName = '%s'" % (familyName)
    log.trace(SQL)
    familyId = system.db.runScalarQuery(SQL, database)
    return familyId

# Look up the final diagnosis id given the application, family, and final Diagnosis names
def fetchFinalDiagnosisDiagramUUID(finalDiagnosisId, database=""):
    SQL = "select DiagramUUID "\
        " from DtFinalDiagnosis "\
        " where FinalDiagnosisId = %i" % (finalDiagnosisId)
    diagramUUID = system.db.runScalarQuery(SQL, database)
    return diagramUUID

# Look up the final diagnosis id given the application, family, and final Diagnosis names
def fetchFinalDiagnosis(application, family, finalDiagnosis, database=""):
    SQL = "select U.UnitName, FD.FinalDiagnosisId, FD.FinalDiagnosisName, FD.FamilyId, FD.FinalDiagnosisPriority, "\
        " FD.CalculationMethod, FD.FinalDiagnosisUUID, FD.DiagramUUID, "\
        " FD.PostTextRecommendation, FD.PostProcessingCallback, FD.RefreshRate, FD.TextRecommendation "\
        " from TkUnit U, DtFinalDiagnosis FD, DtFamily F, DtApplication A"\
        " where U.UnitId = A.UnitId and A.ApplicationId = F.ApplicationId "\
        " and FD.FamilyId = F.FamilyId "\
        " and A.ApplicationName = '%s'" \
        " and F.FamilyName = '%s'" \
        " and FD.FinalDiagnosisName = '%s'" % (application, family, finalDiagnosis)
    log.trace(SQL)
    try:
        pds = system.db.runQuery(SQL, database)
        from ils.common.database import toDict
        records=toDict(pds)      
        if len(records) == 0:
            record={}
        else:
            record = records[0]
    except:
        log.errorf("fetchFinalDiagnosis: SQL error in %s for (%s)",database,SQL)
        record={}
    return record

# Fetch all of the recommendations that touch a quant output.
def fetchRecommendationsForOutput(QuantOutputId, database=""):
    SQL = "select R.RecommendationId, R.Recommendation, R.AutoRecommendation, R.AutoRecommendation, R.ManualRecommendation, "\
        " R.AutoOrManual, QO.QuantOutputName, QO.TagPath "\
        " from DtRecommendationDefinition RD, DtQuantOutput QO, DtRecommendation R "\
        " where RD.QuantOutputId = QO.QuantOutputId "\
        " and QO.QuantOutputId = %i "\
        " and RD.RecommendationDefinitionId = R.RecommendationDefinitionId "\
        " order by QO.QuantOutputName"  % (QuantOutputId)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

# Fetch the outputs for a final diagnosis and return them as a list of dictionaries
# I'm not sure who the clients for this will be so I am returning all of the attributes of a quantOutput.  This includes the attributes 
# that are used when calculating/managing recommendations and the output of those recommendations.
def fetchOutputsForFinalDiagnosis(applicationName, familyName, finalDiagnosisName, database=""):
    SQL = "select QO.QuantOutputName, QO.TagPath, QO.MostNegativeIncrement, QO.MostPositiveIncrement, QO.MinimumIncrement, QO.SetpointHighLimit, "\
        " QO.SetpointLowLimit, L.LookupName FeedbackMethod, QO.OutputLimitedStatus, QO.OutputLimited, QO.OutputPercent, QO.IncrementalOutput, "\
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.QuantOutputId, QO.IgnoreMinimumIncrement "\
        " from DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO, Lookup L "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and L.LookupTypeCode = 'FeedbackMethod'"\
        " and L.LookupId = QO.FeedbackMethodId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and A.ApplicationName = '%s' "\
        " and F.FamilyName = '%s' "\
        " and FD.FinalDiagnosisName = '%s' "\
        " order by QuantOutputName"  % (applicationName, familyName, finalDiagnosisName)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    outputList = []
    for record in pds:
        output=convertOutputRecordToDictionary(record)       
        outputList.append(output)
    return pds, outputList

def convertOutputRecordToDictionary(record):
    output = {}
    output['QuantOutputId'] = record['QuantOutputId']
    output['QuantOutput'] = str(record['QuantOutputName'])
    output['TagPath'] = str(record['TagPath'])
    output['MostNegativeIncrement'] = record['MostNegativeIncrement']
    output['MostPositiveIncrement'] = record['MostPositiveIncrement']
    output['MinimumIncrement'] = record['MinimumIncrement']
    output['SetpointHighLimit'] = record['SetpointHighLimit']
    output['SetpointLowLimit'] = record['SetpointLowLimit']
    output['FeedbackMethod'] = record['FeedbackMethod']
    output['OutputLimitedStatus'] = record['OutputLimitedStatus']
    output['OutputLimited'] = record['OutputLimited']
    output['OutputPercent'] = record['OutputPercent']
    output['IncrementalOutput'] = record['IncrementalOutput']
    output['FeedbackOutput'] = record['FeedbackOutput']
    output['FeedbackOutputManual'] = record['FeedbackOutputManual']
    output['FeedbackOutputConditioned'] = record['FeedbackOutputConditioned']
    output['ManualOverride'] = record['ManualOverride']
    output['IgnoreMinimumIncrement'] = record['IgnoreMinimumIncrement']    
    return output

# Fetch the SQC blocks that led to a Final Diagnosis becoming true.
# We could implement this in one of two ways: 1) we could insert something into the database when the FD becomes true
# or 2) At the time we want to know the SQC blocks, we could query the diagram.
def fetchSQCRootCauseForFinalDiagnosis(finalDiagnosisName, database=""):
    sqcRootCauses=[]

    import system.ils.blt.diagram as diagram
    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor

    print "Searching for SQC blocks for %s:" % (finalDiagnosisName)
    
    SQL = "select DiagramUUID from DtFinalDiagnosis where FinalDiagnosisName = '%s'" % (finalDiagnosisName)
    diagramUUID = system.db.runScalarQuery(SQL, database)
    print "  Diagram UUID: %s" % (str(diagramUUID))
        
    if diagramUUID != None: 
        # Get the upstream blocks, make sure to jump connections
        blocks=diagram.listBlocksGloballyUpstreamOf(diagramUUID, finalDiagnosisName)
            
        print "...found %i upstream blocks..." % (len(blocks))
    
        for block in blocks:
            if block.getClassName() == "com.ils.block.SQC":
                print "   ... found a SQC block..."
                blockId=block.getIdString()
                blockName=block.getName()
                print "Found: %s - %s" % (str(blockId), str(blockName))

    return sqcRootCauses


def fetchQuantOutputsForFinalDiagnosisIds(finalDiagnosisIds, database=""):
    quantOutputIds=[]
    if len(finalDiagnosisIds) > 0:
        from ils.common.database import idListToString
        idString=idListToString(finalDiagnosisIds)
    
        SQL = "select distinct QuantOutputId "\
            " from DtRecommendationDefinition "\
            " where FinalDiagnosisId in ( %s ) " % (idString)
        log.trace(SQL)
        pds = system.db.runQuery(SQL, database)
        
        quantOutputIds=[]
        for record in pds:
            quantOutputIds.append(record["QuantOutputId"])
        
    return quantOutputIds

#
def fetchQuantOutput(quantOutputId, database=""):
    SQL = "select QO.QuantOutputName, QO.TagPath, QO.OutputLimitedStatus, QO.OutputLimited, QO.OutputPercent, "\
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.IncrementalOutput, "\
        " QO.CurrentSetpoint, QO.FinalSetpoint, QO.DisplayedRecommendation, QO.QuantOutputId, QO.MostNegativeIncrement, "\
        " QO.MostPositiveIncrement, QO.MinimumIncrement, QO.SetpointHighLimit, QO.SetpointLowLimit, L.LookupName FeedbackMethod, "\
        " QO.IgnoreMinimumIncrement "\
        " from DtQuantOutput QO, Lookup L "\
        " where QO.QuantOutputId = %i "\
        " and QO.FeedbackMethodId = L.LookupId"  % (quantOutputId)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

#
def fetchTagPathForQuantOutputName(quantOutputName, database=""):
    SQL = "select QuantOutputName from DtQuantOutput where QuantOutputName = '%s'"  % (quantOutputName)
    log.trace(SQL)
    tagPath = system.db.runScalarQuery(SQL, database)
    return tagPath


# Fetch the post for an application
def fetchPostForApplication(application, database=""):
    SQL = "select post "\
        " from TkPost P, TkUnit U, DtApplication A "\
        " where P.PostId = U.PostId "\
        " and U.UnitId = A.UnitId "\
        " and A.ApplicationName = '%s' " % (application)
    log.trace(SQL)
    post = system.db.runScalarQuery(SQL, database)
    return post


def updateBoundRecommendationPercent(quantOutputId, outputPercent, database):
    log.trace("Updating the Bound Recommendation percent")
    pds=fetchRecommendationsForOutput(quantOutputId, database)
    for record in pds:
        autoOrManual=record["AutoOrManual"]
        recommendationId=record["RecommendationId"]
        if autoOrManual == "Manual":
            log.trace("Scaling manual recommendation: %s" % (str(record["ManualRecommendation"])))
            recommendation = record["ManualRecommendation"]
        else:
            log.trace("Scaling auto recommendation: %s" % (str(record["AutoRecommendation"])))
            recommendation = record["AutoRecommendation"]
        recommendation = recommendation * outputPercent / 100.0
        SQL = "update DtRecommendation set Recommendation = %s where RecommendationId = %i" % (str(recommendation), recommendationId)
        log.trace(SQL)
        system.db.runUpdateQuery(SQL, database)

# Update the application priority
def updateFamilyPriority(familyName, familyPriority, database=""):
    SQL = "update DtFamily set FamilyPriority = %i where FamilyName = '%s'" % (familyPriority, familyName)
    log.trace(SQL)
    rows = system.db.runUpdateQuery(SQL, database)
    log.trace("Updated %i rows" % (rows))
    
# Delete all Final Diagnosis.
def resetFinalDiagnosis(log, database):
    log.info("Resetting Final Diagnosis...")
    SQL = "update DtFinalDiagnosis set Active = 0 where Active = 1"
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.info("...reset %i finalDiagnosis" % (rows))

# Delete the quant outputs for an applicatuon.
def resetDiagnosisEntries(log, database):
    log.info("Resetting Diagnosis Entries...")
    SQL = "update DtDiagnosisEntry set Status = 'InActive', RecommendationStatus = 'Restart' where Status = 'Active' "
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.info("...reset %i Diagnosis Entries!" % (rows))