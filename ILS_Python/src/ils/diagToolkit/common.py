'''
Created on Sep 19, 2014

@author: Pete
'''

import system, time
#import system.ils.blt.diagram as scriptingInterface
from ils.io.util import readTag

from ils.log import getLogger
log = getLogger(__name__)

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

'''
Check if the timestamps of two tags are consistent.  
This uses theLastChange property of a tag, so what would happen if we received two consecutive identical values?
'''
def checkConsistency(tagPath1, tagPath2, tolerance=5, recheckInterval=1.0, timeout=10):
    log.tracef("In %s.checkConsistency()...", __name__)
    startTime = system.date.now()
    isConsistent = False
    log.trace("Checking if %s and %s are consistent..." % (tagPath1, tagPath2))
    while isConsistent == False and (system.date.secondsBetween(startTime, system.date.now())) < timeout:
        log.trace("Checking consistency...")
        vals = system.tag.readBlocking([tagPath1, tagPath2])
        timestamp1 = vals[0].timestamp
        timestamp2 = vals[1].timestamp
        secondsBetween = abs(system.date.secondsBetween(timestamp1, timestamp2))

        if secondsBetween < tolerance:
            log.trace("%s and %s are consistent!" % (tagPath1, tagPath2))
            isConsistent = True
            return isConsistent
        
        log.tracef("The seconds between the two values is %s and the tolerance is %s", str(secondsBetween), str(tolerance))
        time.sleep(recheckInterval)

    log.trace("** %s and %s are NOT consistent **" % (tagPath1, tagPath2))
    return isConsistent
    
# Check if the timestamp of the tag is less than a certain tolerance older then theTime, or the current time if theTime 
# is omitted.  This uses theLastChange property of a tag, so what would happen if we received two consecutive identical values?
def checkFreshness(tagPath, theTime="now", provider="XOM", tolerance=-1, recheckInterval=1.0, timeout=-1.0):
    log.tracef("In %s.checkFreshness()...", __name__)
    if tolerance < 0.0:
        tolerance = readTag("[%s]Configuration/DiagnosticToolkit/freshnessToleranceSeconds" % (provider)).value
        print "Using the default freshness tolerance: ", tolerance

    if timeout < 0.0:
        timeout = readTag("[%s]Configuration/DiagnosticToolkit/freshnessTimeoutSeconds" % (provider)).value
        print "Using the default timeout: ", timeout
        
    if theTime == "now" or theTime == None:
        theTime = system.date.now()
        print "Using the current time: ", theTime
    
    # Subtract the tolerance
    theTime = system.date.addSeconds(theTime, int(-1 * tolerance))
    print "Check the tag time against the time - the tolerance: ", theTime

    startTime = system.date.now()
    now = system.date.now()
    isFresh = False
    log.trace("Checking if %s is fresh..." % (tagPath))
    while isFresh == False and system.date.secondsBetween(startTime, now) < timeout:
        log.trace("Checking freshness...")
        qv = readTag(tagPath)
        timestamp = qv.timestamp

        log.tracef("Comparing tag time (%s) to (%s)", str(timestamp), str(theTime))
        if system.date.isAfter(timestamp, theTime):
            log.trace("%s is now fresh!" % (tagPath))
            isFresh = True
            return isFresh

        time.sleep(recheckInterval)
        now = system.date.now()

    log.trace("** %s is NOT fresh **" % (tagPath))
    return isFresh

'''
Check that tag1 is fresher than tag2.  
The timeout here is in seconds, the default time to wait is 1 minute.
'''
def checkFresher(tagPath1, tagPath2, recheckInterval=1.0, timeout=60):
    log.tracef("In %s.checkFresher()...", __name__)
    startTime = system.date.now()
    isFresher = False
    log.trace("Checking if %s is fresher than %s..." % (tagPath1, tagPath2))
    while isFresher == False and (system.date.secondsBetween(startTime, system.date.now())) < timeout:
        log.trace("Checking freshness...")
        vals = system.tag.readBlocking([tagPath1, tagPath2])
        timestamp1 = vals[0].timestamp
        timestamp2 = vals[1].timestamp
        
        if system.date.secondsBetween(timestamp2, timestamp1) > 0:
            log.trace("%s is now fresher than %s!" % (tagPath1, tagPath2))
            isFresher = True
            return isFresher
        
        time.sleep(recheckInterval)

    log.trace("** %s is NOT fresher than %s **" % (tagPath1, tagPath2))
    return isFresher

# This gets called at the beginning of each recommendation management cycle.  It clears all of the dynamic attributes of 
# a Quant Output.  
def clearQuantOutputRecommendations(application, database=""):
    log.tracef("In %s.clearQuantOutputRecommendations()...", __name__)
    SQL = "update DtQuantOutput set FeedbackOutput = 0.0, OutputLimitedStatus = '', OutputLimited = 0, "\
        " OutputPercent = 0.0, FeedbackOutputManual = 0.0, FeedbackOutputConditioned = 0.0, "\
        " ManualOverride = 0, Active = 0 "\
        " from DtApplication A, DtFamily F, DtDiagnosis D, DtFinalDiagnosis FD, DtRecommendationDefinition RD "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = D.FamilyId "\
        " and D.DiagramId = FD.DiagramId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = DtQuantOutput.QuantOutputId "\
        " and A.Application = '%s' " % (application)
    log.tracef("%s.clearQuantOutputRecommendations(): %s", __name__, SQL)
    system.db.runUpdateQuery(SQL, database)
    return

def convertOutputRecordToDictionary(record):
    log.tracef("In %s.convertOutputRecordToDictionary()...", __name__)
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
    output['TrapInsignificantRecommendations'] = record['TrapInsignificantRecommendations']
    return output

# Fetch all of the active final diagnosis for an application.
# Order the diagnosis from most import to least important - remember that the numeric priority is such that
# low numbers are higher priority than high numbers. 
def fetchActiveDiagnosis(applicationName, database=""):
    log.tracef("In %s.fetchActiveDiagnosis()...", __name__)
    SQL = "select A.ApplicationName, F.FamilyName, F.FamilyId, D.DiagramName, D.DiagramId, FD.FinalDiagnosisName, FD.FinalDiagnosisPriority, FD.FinalDiagnosisId, "\
        " FD.Constant, DE.DiagnosisEntryId, F.FamilyPriority, DE.Multiplier, FD.Explanation, FD.ShowExplanationWithRecommendation, "\
        " DE.RecommendationErrorText, FD.PostTextRecommendation, FD.PostProcessingCallback, FD.TextRecommendation, FD.CalculationMethod,  "\
        " L.LookupName as GroupRampMethod"\
        " from DtApplication A, DtFamily F, DtDiagram D, DtFinalDiagnosis FD, DtDiagnosisEntry DE,  Lookup L"\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = D.FamilyId "\
        " and D.DiagramId = FD.DiagramId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and DE.Status = 'Active' " \
        " and (FD.Constant = 0 or not(DE.RecommendationStatus in ('WAIT','NO-DOWNLOAD','DOWNLOAD'))) " \
        " and A.ApplicationName = '%s'"\
        " and A.GroupRampMethodId = L.LookupId"\
        " and L.LookupTypeCode='GroupRampMethod' "\
        " order by FamilyPriority ASC, FinalDiagnosisPriority ASC"  % (applicationName) 
    log.tracef("%s.fetchActiveDiagnosis(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    log.tracef("Fetched %d active diagnosis", len(pds))
    return pds

# Fetch the outputs for a final diagnosis and return them as a list of dictionaries
# I'm not sure who the clients for this will be so I am returning all of the attributes of a quantOutput.  This includes the attributes 
# that are used when calculating/managing recommendations and the output of those recommendations.
def fetchActiveOutputsForFinalDiagnosis(applicationName, familyName, finalDiagnosisName, database=""):
    log.tracef("In %s.fetchActiveOutputsForFinalDiagnosis()...", __name__)
    SQL = "select QO.QuantOutputName, QO.TagPath, QO.MostNegativeIncrement, QO.MostPositiveIncrement, QO.MinimumIncrement, QO.SetpointHighLimit, "\
        " QO.SetpointLowLimit, L.LookupName FeedbackMethod, QO.OutputLimitedStatus, QO.OutputLimited, QO.OutputPercent, QO.IncrementalOutput, "\
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.QuantOutputId, QO.IgnoreMinimumIncrement, "\
        " FD.TrapInsignificantRecommendations "\
        " from DtApplication A, DtFamily F, DtDiagram D, DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO, Lookup L "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = D.FamilyId "\
        " and D.DiagramId = FD.DiagramId "\
        " and L.LookupTypeCode = 'FeedbackMethod'"\
        " and L.LookupId = QO.FeedbackMethodId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and A.ApplicationName = '%s' "\
        " and F.FamilyName = '%s' "\
        " and FD.FinalDiagnosisName = '%s' "\
        " and QO.Active = 1"\
        " order by QuantOutputName"  % (applicationName, familyName, finalDiagnosisName)
    log.tracef("%s.fetchActiveOutputsForFinalDiagnosis(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    outputList = []
    for record in pds:
        output=convertOutputRecordToDictionary(record)       
        outputList.append(output)
    return pds, outputList

# Fetch all of the active final diagnosis for an application.
# Order the diagnosis from most import to least important - remember that the numeric priority is such that
# low numbers are higher priority than high numbers. 
def fetchActiveFamilies(applicationName, database=""):
    log.tracef("In %s.fetchActiveFamilies()...", __name__)
    SQL = "select distinct A.ApplicationName, F.FamilyName, F.FamilyId "\
        " from DtApplication A, DtFamily F, DtDiagram D, DtFinalDiagnosis FD, DtDiagnosisEntry DE "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = D.FamilyId "\
        " and D.DiagramId = FD.DiagramId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and DE.Status = 'Active' " \
        " and not (FD.CalculationMethod != 'Constant' and (DE.RecommendationStatus in ('WAIT','NO-DOWNLOAD','DOWNLOAD'))) " \
        " and A.ApplicationName = '%s'"\
        " order by FamilyName ASC"  % (applicationName) 
    log.tracef("%s.fetchActiveFamilies(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

# Look up the final diagnosis and family given an application and a quantoutput.
# I'm not sure that I need the application here because there is a unique index on the quant output
# name - which I'm not sure is correct - so if we ever remove that unique index then this will still work.
def fetchActiveFinalDiagnosisForAnOutput(application, quantOutputId, database=""):
    log.tracef("In %s.fetchActiveFinalDiagnosisForAnOutput()...", __name__)
    SQL = "select FD.FinalDiagnosisName, FD.FinalDiagnosisId, F.FamilyName "\
        " from DtFinalDiagnosis FD, DtFamily F, DtDiagram D, DtApplication A, DtQuantOutput QO, DtRecommendationDefinition RD "\
        " where A.ApplicationId = F.ApplicationId "\
        " and A.ApplicationName = '%s' "\
        " and F.FamilyId = D.FamilyId "\
        " and D.DiagramId = FD.DiagramId "\
        " and QO.ApplicationId = A.ApplicationId "\
        " and RD.quantOutputId = QO.QuantOutputId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and FD.Active = 1 "\
        " and QO.QuantOutputId = %s " % (application, str(quantOutputId))
    log.tracef("%s.fetchActiveFinalDiagnosisForAnOutput(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

def fetchActiveOutputsForPost(post, database=""):
    ''' Updated to use a view that incorporates new DtDiagram table - PH 6/8/2022 '''
    log.tracef("In %s.fetchActiveOutputsForPost()...", __name__)
    SQL = "SELECT distinct ApplicationName, QuantOutputName, TagPath, OutputLimitedStatus, OutputLimited, FeedbackOutput, FeedbackOutputManual, "\
        "FeedbackOutputConditioned, ManualOverride, IncrementalOutput, CurrentSetpoint, FinalSetpoint, DisplayedRecommendation, QuantOutputId, "\
        "DownloadAction, DownloadStatus, Ramp "\
        "FROM DtActiveOutputsForPostView "\
        "WHERE Active = 1 "\
        "and Post = '%s' "\
        "ORDER BY ApplicationName, QuantOutputName" % (post)
    
    log.tracef("%s.fetchActiveOutputsForPost(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    log.tracef("   ...returned %d records", len(pds))
    return pds

def fetchActiveTextRecommendationsForPost(post, database=""):      
    ''' Modified to use new View which incorporates the DtDiagram table - PH 6/8/2022 '''
    log.tracef("In %s.fetchActiveTextRecommendationsForPost()...", __name__)
    SQL = "select distinct TextRecommendation, PostProcessingCallback, ApplicationName, DiagnosisEntryId "\
        " from DtActiveTextRecommendationsForPostView "\
        " where Post = '%s' "  % (post)

    log.tracef("%s.fetchActiveTextRecommendationsForPost(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    for record in pds:
        log.tracef("%s - %s - %s", record["ApplicationName"], record["DiagnosisEntryId"], record["TextRecommendation"])
    return pds

def fetchAnyFinalDiagnosisForAnOutput(application, quantOutputId, database=""):
    log.tracef("In %s.fetchAnyFinalDiagnosisForAnOutput()...", __name__)
    SQL = "select FD.FinalDiagnosisName, FD.FinalDiagnosisId, F.FamilyName "\
        " from DtFinalDiagnosis FD, DtDiagram D, DtFamily F, DtApplication A, DtQuantOutput QO, DtRecommendationDefinition RD "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = D.FamilyId "\
        " and D.DiagramId = FD.DiagramId "\
        " and A.ApplicationName = '%s' "\
        " and QO.ApplicationId = A.ApplicationId "\
        " and RD.quantOutputId = QO.QuantOutputId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and QO.QuantOutputId = %s " % (application, str(quantOutputId))
    log.tracef("%s.fetchAnyFinalDiagnosisForAnOutput(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

def fetchApplications(db):
    log.tracef("In %s.fetchApplications()...", __name__)
    pds = system.db.runQuery("Select ApplicationName from DtApplication order by ApplicationName", database=db)
    log.infof("Fetched %d applications." % (len(pds)))
    return pds

# Fetch applications for a console
def fetchApplicationsForPost(post, database=""):
    log.tracef("In %s.fetchApplicationsForPost()...", __name__)
    SQL = "select distinct A.ApplicationName "\
        " from TkPost P, TkUnit U, DtApplication A "\
        " where P.PostId = U.PostId "\
        " and U.UnitId = A.UnitId "\
        " and P.Post = '%s' "\
        " order by A.ApplicationName"  % (post)
    log.tracef("%s.fetchApplicationsForPost(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

# Lookup the application Id given the name
def fetchApplicationManaged(applicationName, database=""):
    log.tracef("In %s.fetchApplicationManaged()...", __name__)
    SQL = "select Managed from DtApplication where ApplicationName = '%s'" % (applicationName)
    log.tracef("%s.fetchApplicationManaged(): %s", __name__, SQL)
    managed = system.db.runScalarQuery(SQL, database)
    return managed

def fetchApplicationNameForDiagram(diagramName, database=""):
    ''' Lookup the application name for the diagram '''
    log.tracef("In %s.fetchApplicationNameForDiagram()...", __name__)
    SQL = "select ApplicationName from DtApplicationHierarchyView where DiagramName = '%s'" % (diagramName)
    log.tracef("%s.fetchApplicationforDiagram(): %s", __name__, SQL)
    applicationName = system.db.runScalarQuery(SQL, database)
    return applicationName

def fetchApplicationAndFamilyForDiagram(diagramName, database=""):
    ''' Lookup the application name for the diagram '''
    log.tracef("In %s.fetchApplicationAndFamilyForDiagram()...", __name__)
    SQL = "select ApplicationName, FamilyName from DtApplicationHierarchyView where DiagramName = '%s'" % (diagramName)
    log.tracef("%s.fetchApplicationAndFamilyForDiagram(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    if len(pds) == 1:
        record = pds[0]
        applicationName = record["ApplicationName"]
        familyName = record["FamilyName"]
    else:
        log.errorf("Error fetching application and family information for diagram %s", diagramName)
        applicationName = None
        familyName = None
        
    return applicationName, familyName

# Lookup the application Id given the name
def fetchApplicationId(applicationName, database=""):
    log.tracef("In %s.fetchApplicationId()...", __name__)
    SQL = "select ApplicationId from DtApplication where ApplicationName = '%s'" % (applicationName)
    log.tracef("%s.fetchApplicationId(): %s", __name__, SQL)
    applicationId = system.db.runScalarQuery(SQL, database)
    return applicationId

def fetchDiagrams(db):
    log.tracef("In %s.fetchDiagrams()...", __name__)
    SQL = "Select ApplicationName, FamilyName, FamilyPriority, DiagramName "\
        "from DtApplicationHierarchyView "\
        "order by ApplicationName, FamilyName, DiagramName"
    pds = system.db.runQuery(SQL, database=db)
    log.infof("Fetched %d applications." % (len(pds)))
    return pds


# Look up the final diagnosis id given the application, family, and final Diagnosis names
def fetchDiagramForFinalDiagnosis(application, family, finalDiagnosis, database=""):
    log.tracef("In %s.fetchFinalDiagnosis()...", __name__)
    SQL = "select D.DiagramName "\
        " from TkUnit U, DtFinalDiagnosis FD, DtDiagram D, DtFamily F, DtApplication A"\
        " where U.UnitId = A.UnitId "\
        " and A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = D.FamilyId "\
        " and FD.DiagramId = D.DiagramId "\
        " and A.ApplicationName = '%s'" \
        " and F.FamilyName = '%s'" \
        " and FD.FinalDiagnosisName = '%s'" % (application, family, finalDiagnosis)
    log.tracef("%s.fetchFinalDiagnosis(): %s", __name__, SQL)
    try:
        diagramName = system.db.runScalarQuery(SQL, database)
    except:
        log.errorf("fetchDiagramForFinalDiagnosis: SQL error in %s for (%s)",database,SQL)
        diagramName = None
    
    return diagramName


def fetchDiagramId(diagramName, db):
    log.tracef("In %s.fetchDiagramId()...", __name__)
    diagramId = system.db.runScalarQuery("select DiagramId from DtDiagram where DiagramName = '%s'" % (diagramName), database=db)
    return diagramId

# Fetch the time of the last recommendation, which should be the same as when the final diagnosis last became True
def fetchDiagnosisActiveTime(finalDiagnosisId, database = ""):
    log.tracef("In %s.fetchDiagnosisActiveTime()...", __name__)
    SQL = "select LastRecommendationTime from DtFinalDiagnosis where FinalDiagnosisId = %s" % (str(finalDiagnosisId))
    log.trace(SQL)
    lastRecommendtaionTime = system.db.runScalarQuery(SQL, database)
    log.trace("The last recommendation time is: %s" % (str(lastRecommendtaionTime)))
    return lastRecommendtaionTime

def fetchFamilies(db):
    log.tracef("In %s.fetchFamilies()...", __name__)
    SQL = "Select A.ApplicationName, F.FamilyName, F.FamilyPriority "\
        "from DtApplication A, DtFamily F "\
        "where A.ApplicationId = F.ApplicationId "\
        "order by ApplicationName, FamilyName"
    pds = system.db.runQuery(SQL, database=db)
    log.infof("Fetched %d applications." % (len(pds)))
    return pds

def fetchFamilyNameForFinalDiagnosisId(finalDiagnosisId, db=""):
    log.tracef("In %s.fetchFamilyNameForFinalDiagnosisId()...", __name__)
    SQL = "select FamilyName from DtFinalDiagnosisView where FinalDiagnosisId = %s" % (str(finalDiagnosisId))
    log.tracef("%s.fetchFamilyId(): %s", __name__, SQL)
    familyName = system.db.runScalarQuery(SQL, db)
    return familyName

# Lookup the family Id given the name
def fetchFamilyId(applicationName, familyName, database=""):
    log.tracef("In %s.fetchFamilyId()...", __name__)
    SQL = "select F.FamilyId from DtApplication A, DtFamily F "\
        "where A.ApplicationId = F.ApplicationId and A.ApplicationName = '%s' and F.FamilyName = '%s'" % (applicationName, familyName)
    log.tracef("%s.fetchFamilyId(): %s", __name__, SQL)
    familyId = system.db.runScalarQuery(SQL, database)
    return familyId

def fetchFinalDiagnosisList(db):
    log.tracef("In %s.fetchFinalDiagnosisList()...", __name__)
    SQL = "Select ApplicationName, FamilyName, FamilyPriority, DiagramId, DiagramName, FinalDiagnosisName, FinalDiagnosisPriority "\
        "from DtFinalDiagnosisView "\
        "order by ApplicationName, FamilyName, DiagramName, FinalDiagnosisName"
    pds = system.db.runQuery(SQL, database=db)
    log.infof("Fetched %d final diagnosis." % (len(pds)))
    return pds

# Look up the final diagnosis id given the application, family, and final Diagnosis names
def fetchFinalDiagnosisDiagramUUID(finalDiagnosisId, database=""):
    log.tracef("In %s.fetchFinalDiagnosisDiagramUUID()...", __name__)
    SQL = "select DiagramUUID "\
        " from DtFinalDiagnosis "\
        " where FinalDiagnosisId = %d" % (finalDiagnosisId)
    log.tracef("%s.fetchFinalDiagnosisDiagramUUID(): %s", __name__, SQL)
    diagramUUID = system.db.runScalarQuery(SQL, database)
    return diagramUUID

def fetchFinalDiagnosisId(diagramName, fdName, db):
    log.tracef("In %s.fetchFinalDiagnosisId()...", __name__)
    SQL = "select FD.FinalDiagnosisId from DtDiagram D, DtFinalDiagnosis FD "\
        "where D.DiagramId = FD.DiagramId and D.DiagramName = '%s' and FD.FinalDiagnosisName = '%s'" % (diagramName, fdName)
    log.tracef("%s.fetchFinalDiagnosisId(): %s", __name__, SQL)
    finalDiagnosisId = system.db.runScalarQuery(SQL, database=db)
    return finalDiagnosisId

# Look up the final diagnosis id given the application, family, and final Diagnosis names
def fetchFinalDiagnosis(application, family, diagram, finalDiagnosis, database=""):
    log.tracef("In %s.fetchFinalDiagnosis()...", __name__)
    SQL = "select U.UnitName, FD.FinalDiagnosisId, FD.FinalDiagnosisName, F.FamilyId, FD.FinalDiagnosisPriority, "\
        " FD.CalculationMethod, FD.FinalDiagnosisUUID, FD.DiagramUUID, FD.Explanation, "\
        " FD.PostTextRecommendation, FD.PostProcessingCallback, FD.RefreshRate, FD.TextRecommendation "\
        " from TkUnit U, DtFinalDiagnosis FD, DtDiagram D, DtFamily F, DtApplication A"\
        " where U.UnitId = A.UnitId "\
        " and A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = D.FamilyId "\
        " and FD.DiagramId = D.DiagramId "\
        " and A.ApplicationName = '%s'" \
        " and F.FamilyName = '%s'" \
        " and D.DiagramName = '%s'"\
        " and FD.FinalDiagnosisName = '%s'" % (application, family, diagram, finalDiagnosis)
    log.tracef("%s.fetchFinalDiagnosis(): %s", __name__, SQL)
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

# Look up the final diagnosis id given the application, family, and final Diagnosis names
def fetchFinalDiagnosisNameFromId(finalDiagnosisId, database=""):
    log.tracef("In %s.fetchFinalDiagnosisNameFromId()...", __name__)
    SQL = "select FinalDiagnosisName "\
        " from DtFinalDiagnosis "\
        " where FinalDiagnosisId = %s "  % (finalDiagnosisId)
    log.tracef("%s.fetchFinalDiagnosis(): %s", __name__, SQL)
    finalDiagnosisName = system.db.runScalarQuery(SQL, database)
    return finalDiagnosisName


# Fetch all of the active final diagnosis for an application.
# Order the diagnosis from most import to least important - remember that the numeric priority is such that
# low numbers are higher priority than high numbers. 
def fetchHighestActiveDiagnosis(applicationName, database=""):
    log.tracef("In %s.fetchHighestActiveDiagnosis()...", __name__)
    SQL = "select A.ApplicationName, F.FamilyName, F.FamilyId, D.DiagramName, FD.FinalDiagnosisName, FD.FinalDiagnosisPriority, FD.FinalDiagnosisId, "\
        " FD.Constant, DE.DiagnosisEntryId, F.FamilyPriority, DE.Multiplier, "\
        " DE.RecommendationErrorText, FD.PostTextRecommendation, FD.PostProcessingCallback, FD.TextRecommendation, FD.CalculationMethod  "\
        " from DtApplication A, DtFamily F, DtDiagram D, DtFinalDiagnosis FD, DtDiagnosisEntry DE "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = D.FamilyId "\
        " and D.DiagramId = FD.DiagramId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and DE.Status = 'Active' "\
        " and FD.Active = 1 "\
        " and (FD.Constant = 0 or not(DE.RecommendationStatus in ('WAIT','NO-DOWNLOAD','DOWNLOAD'))) "\
        " and A.ApplicationName = '%s'"\
        " order by FamilyPriority ASC, FinalDiagnosisPriority ASC"  % (applicationName) 
    log.tracef("%s.fetchHighestActiveDiagnosis(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

# Fetch the post for an application
def fetchNotificationStrategy(application, database=""):
    log.tracef("In %s.fetchNotificationStrategy()...", __name__)
    SQL = "select NotificationStrategy, ClientId from DtApplication where ApplicationName = '%s' " % (application)
    log.tracef("%s.fetchNotificationStrategy(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    record = pds[0]
    return record["NotificationStrategy"], record["ClientId"]

def fetchOutputNamesForApplication(applicationName, db):
    log.tracef("In %s.fetchOutputNamesForApplication()...", __name__)
    SQL = "select QuantOutputName, QuantOutputId "\
            "from DtQuantOutputDefinitionView "\
            "where ApplicationName = '%s' "\
            "order by QuantOutputName" % (applicationName)
    pds = system.db.runQuery(SQL, database=db)
    return pds

def fetchOutputsForApplication(applicationName, db):
    log.tracef("In %s.fetchOutputsForApplication()...", __name__)
    SQL = "select QuantOutputId, QuantOutputName, TagPath, MostNegativeIncrement, MostPositiveIncrement, IgnoreMinimumIncrement, "\
            "MinimumIncrement, SetpointHighLimit, SetpointLowLimit, IncrementalOutput, FeedbackMethod "\
            "from DtQuantOutputDefinitionView "\
            "where ApplicationName = '%s' "\
            "order by QuantOutputName" % (applicationName)
    pds = system.db.runQuery(SQL, database=db)
    return pds

# Fetch the outputs for a final diagnosis and return them as a list of dictionaries
# I'm not sure who the clients for this will be so I am returning all of the attributes of a quantOutput.  This includes the attributes 
# that are used when calculating/managing recommendations and the output of those recommendations.
def fetchOutputsForFinalDiagnosis(applicationName, familyName, finalDiagnosisName, database=""):
    log.tracef("In %s.fetchOutputsForFinalDiagnosis()...", __name__)
    SQL = "select upper(QO.QuantOutputName) QuantOutputName, QO.TagPath, QO.MostNegativeIncrement, QO.MostPositiveIncrement, QO.MinimumIncrement, QO.SetpointHighLimit, "\
        " QO.SetpointLowLimit, L.LookupName FeedbackMethod, QO.OutputLimitedStatus, QO.OutputLimited, QO.OutputPercent, QO.IncrementalOutput, "\
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.QuantOutputId, QO.IgnoreMinimumIncrement, "\
        " FD.TrapInsignificantRecommendations "\
        " from DtApplication A, DtFamily F, DtDiagram D, DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO, Lookup L "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = D.FamilyId "\
        " and D.DiagramId = FD.DiagramId "\
        " and L.LookupTypeCode = 'FeedbackMethod'"\
        " and L.LookupId = QO.FeedbackMethodId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and A.ApplicationName = '%s' "\
        " and F.FamilyName = '%s' "\
        " and FD.FinalDiagnosisName = '%s' "\
        " order by QuantOutputName"  % (applicationName, familyName, finalDiagnosisName)
    log.tracef("%s.fetchOutputsForFinalDiagnosis(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    outputList = []
    for record in pds:
        output=convertOutputRecordToDictionary(record)       
        outputList.append(output)
    return pds, outputList

def fetchOutputNamesForFinalDiagnosisId(finalDiagnosisId, db=""):
    ''' Fetch the outputs for a final diagnosis '''
    log.tracef("In %s.fetchOutputNamesForFinalDiagnosisId()...", __name__)
    SQL = "select QO.QuantOutputName, QO.QuantOutputId "\
        " from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO, Lookup L "\
        " where L.LookupTypeCode = 'FeedbackMethod'"\
        " and L.LookupId = QO.FeedbackMethodId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and FD.FinalDiagnosisId = %s "\
        " order by QuantOutputName"  % (str(finalDiagnosisId))
    log.tracef("%s.fetchOutputNamesForFinalDiagnosisId(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database=db)
    return pds

def fetchOutputsForFinalDiagnosisId(finalDiagnosisId, db=""):
    ''' Fetch the outputs for a final diagnosis '''
    log.tracef("In %s.fetchOutputsForFinalDiagnosisId()...", __name__)
    SQL = "select upper(QO.QuantOutputName) QuantOutputName, QO.TagPath, QO.MostNegativeIncrement, QO.MostPositiveIncrement, QO.MinimumIncrement, QO.SetpointHighLimit, "\
        " QO.SetpointLowLimit, L.LookupName FeedbackMethod, QO.OutputLimitedStatus, QO.OutputLimited, QO.OutputPercent, QO.IncrementalOutput, "\
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.QuantOutputId, QO.IgnoreMinimumIncrement, "\
        " FD.TrapInsignificantRecommendations "\
        " from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO, Lookup L "\
        " where L.LookupTypeCode = 'FeedbackMethod'"\
        " and L.LookupId = QO.FeedbackMethodId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and FD.FinalDiagnosisId = %s "\
        " order by QuantOutputName"  % (str(finalDiagnosisId))
    log.tracef("%s.fetchOutputsForFinalDiagnosisId(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database=db)
    return pds

# Fetch the post for an application
def fetchPostForApplication(application, database=""):
    log.tracef("In %s.fetchPostForApplication()...", __name__)
    SQL = "select post "\
        " from TkPost P, TkUnit U, DtApplication A "\
        " where P.PostId = U.PostId "\
        " and U.UnitId = A.UnitId "\
        " and A.ApplicationName = '%s' " % (application)
    log.tracef("%s.fetchPostForApplication(): %s", __name__, SQL)
    post = system.db.runScalarQuery(SQL, database)
    return post

# Fetch the post for an application
def fetchPostForUnit(unit, database=""):
    log.tracef("In %s.fetchPostForUnit()...", __name__)
    SQL = "select post "\
        " from TkPost P, TkUnit U "\
        " where P.PostId = U.PostId "\
        " and U.UnitName = '%s' " % (unit)
    log.tracef("%s.fetchPostForUnit(): %s", __name__, SQL)
    post = system.db.runScalarQuery(SQL, database)
    return post

def fetchQuantOutputsForFinalDiagnosisIds(finalDiagnosisIds, database=""):
    log.tracef("In %s.fetchQuantOutputsForFinalDiagnosisIds()...", __name__)
    quantOutputIds=[]
    if len(finalDiagnosisIds) > 0:
        from ils.common.database import idListToString
        idString=idListToString(finalDiagnosisIds)
    
        SQL = "select distinct QuantOutputId "\
            " from DtRecommendationDefinition "\
            " where FinalDiagnosisId in ( %s ) " % (idString)
        log.tracef("%s.fetchQuantOutputsForFinalDiagnosisIds(): %s", __name__, SQL)
        pds = system.db.runQuery(SQL, database)
        
        quantOutputIds=[]
        for record in pds:
            quantOutputIds.append(record["QuantOutputId"])
        
    return quantOutputIds

def fetchQuantOutput(quantOutputId, database=""):
    log.tracef("In %s.fetchQuantOutput()...", __name__)
    SQL = "select QO.QuantOutputName, QO.TagPath, QO.OutputLimitedStatus, QO.OutputLimited, QO.OutputPercent, "\
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.IncrementalOutput, "\
        " QO.CurrentSetpoint, QO.FinalSetpoint, QO.DisplayedRecommendation, QO.QuantOutputId, QO.MostNegativeIncrement, "\
        " QO.MostPositiveIncrement, QO.MinimumIncrement, QO.SetpointHighLimit, QO.SetpointLowLimit, L.LookupName FeedbackMethod, "\
        " QO.IgnoreMinimumIncrement "\
        " from DtQuantOutput QO, Lookup L "\
        " where QO.QuantOutputId = %d "\
        " and QO.FeedbackMethodId = L.LookupId"  % (quantOutputId)
        
    SQL = "SELECT DtQuantOutput.QuantOutputId, DtQuantOutput.QuantOutputName, DtQuantOutput.TagPath, DtQuantOutput.OutputLimitedStatus, DtQuantOutput.OutputLimited, "\
        "DtQuantOutput.OutputPercent, DtQuantOutput.FeedbackOutput, DtQuantOutput.FeedbackOutputManual, DtQuantOutput.FeedbackOutputConditioned, "\
        "DtQuantOutput.ManualOverride, DtQuantOutput.IncrementalOutput, DtQuantOutput.CurrentSetpoint, DtQuantOutput.FinalSetpoint, DtQuantOutput.DisplayedRecommendation, "\
        "DtQuantOutput.MostNegativeIncrement, DtQuantOutput.MostPositiveIncrement, DtQuantOutput.MinimumIncrement, DtQuantOutput.SetpointHighLimit, "\
        "DtQuantOutput.SetpointLowLimit, Lookup.LookupName AS FeedbackMethod, DtQuantOutput.IgnoreMinimumIncrement, 0 as TrapInsignificantRecommendations "\
        "FROM DtQuantOutput INNER JOIN "\
        "Lookup ON DtQuantOutput.FeedbackMethodId = Lookup.LookupId LEFT OUTER JOIN "\
        "DtQuantOutputRamp ON DtQuantOutput.QuantOutputId = DtQuantOutputRamp.QuantOutputId "\
        "WHERE (DtQuantOutput.QuantOutputId = %d) " % (quantOutputId)
    
    log.tracef("%s.fetchQuantOutput(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    return pds


# Fetch all of the recommendations that touch a quant output.
def fetchRecommendationsForOutput(QuantOutputId, database=""):
    log.tracef("In %s.fetchRecommendationsForOutput()...", __name__)
    SQL = "select R.RecommendationId, R.Recommendation, R.AutoRecommendation, R.AutoRecommendation, R.ManualRecommendation, "\
        " R.AutoOrManual, R.RampTime, QO.QuantOutputName, QO.TagPath "\
        " from DtRecommendationDefinition RD, DtQuantOutput QO, DtRecommendation R "\
        " where RD.QuantOutputId = QO.QuantOutputId "\
        " and QO.QuantOutputId = %d "\
        " and RD.RecommendationDefinitionId = R.RecommendationDefinitionId "\
        " order by QO.QuantOutputName"  % (QuantOutputId)
    log.tracef("%s.fetchRecommendationsForOutput(): %s", __name__, SQL)
    pds = system.db.runQuery(SQL, database)
    return pds


def fetchSQCRootCauseForFinalDiagnosis(diagramName, finalDiagnosisName):
    '''
    Fetch the SQC blocks that led to a Final Diagnosis becoming true.
    Implement this be looking for SQC blocks upstream of the final diagnosis whose state is TRUE.
    '''
    log.infof("In %s.fetchSQCRootCauseForFinalDiagnosis() - Searching for SQC blocks for %s on %s", __name__, finalDiagnosisName, diagramName)
    sqcBlockNames=[]

    # Get the upstream blocks, make sure to jump connections
    from ils.blt.api import listBlocksGloballyUpstreamOf
    blocks = listBlocksGloballyUpstreamOf(diagramName, finalDiagnosisName)
        
    log.infof("...found %d upstream blocks...", len(blocks))

    for block in blocks:
        if block.getClassName() == "com.ils.block.SQC":
            blockName=block.getName()            
            blockAttributes = block.getAttributes()
            blockState = blockAttributes.get("State", None)

            log.infof("Found: %s - %s", str(blockName), str(blockState))
            if str(blockState) == "TRUE":
                sqcBlockNames.append(blockName)

    return sqcBlockNames

def fetchTagPathForQuantOutputName(quantOutputName, database=""):
    log.tracef("In %s.fetchTagPathForQuantOutputName()...", __name__)
    SQL = "select QuantOutputName from DtQuantOutput where QuantOutputName = '%s'"  % (quantOutputName)
    log.tracef("%s.fetchTagPathForQuantOutputName(): %s", __name__, SQL)
    tagPath = system.db.runScalarQuery(SQL, database)
    return tagPath

def updateBoundRecommendationPercent(quantOutputId, outputPercent, database):
    log.tracef("In %s.updateBoundRecommendationPercent() - Updating the Bound Recommendation percent...", __name__)
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
        SQL = "update DtRecommendation set Recommendation = %s where RecommendationId = %d" % (str(recommendation), recommendationId)
        log.trace(SQL)
        system.db.runUpdateQuery(SQL, database)

# Update the application priority
def updateFamilyPriority(familyName, familyPriority, database=""):
    log.tracef("In %s.updateFamilyPriority()...", __name__)
    SQL = "update DtFamily set FamilyPriority = %d where FamilyName = '%s'" % (familyPriority, familyName)
    log.tracef("%s.updateFamilyPriority(): %s", __name__, SQL)
    rows = system.db.runUpdateQuery(SQL, database)
    log.trace("Updated %i rows" % (rows))
    
# Delete all Final Diagnosis.
def resetFinalDiagnosis(log, database):
    log.tracef("In %s.resetFinalDiagnosis() - Resetting Final Diagnosis...", __name__)
    SQL = "update DtFinalDiagnosis set Active = 0 where Active = 1"
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.infof("...reset %d finalDiagnosis", rows)

# Delete the quant outputs for an applicatuon.
def resetDiagnosisEntries(log, database):
    log.infof("In %s.resetDiagnosisEntries() - Resetting Diagnosis Entries...", __name__)
    SQL = "update DtDiagnosisEntry set Status = 'InActive', RecommendationStatus = 'Restart' where Status = 'Active' "
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.infof("...reset %d Diagnosis Entries!", rows)
    
def stripClassPrefix(className):
    className = className[className.rfind(".")+1:]
    return className