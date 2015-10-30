'''
Created on Sep 19, 2014

@author: Pete
'''

import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.SQL.diagToolkit")


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

# Delete all of the recommendations for an Application.  This is in response to a change in the status of a final diagnosis
# and is the first step in evaluating the active FDs and calculating new recommendations.
def deleteRecommendations(applicationName, log, database):
    log.trace("Deleting recommendations for %s" % (applicationName))
    SQL = "delete from DtRecommendation " \
        " where DiagnosisEntryId in (select DE.DiagnosisEntryId "\
        " from DtDiagnosisEntry DE, DtFinalDiagnosis FD, DtFamily F, DtApplication A"\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and A.ApplicationName = '%s')" % (applicationName)
    rows=system.db.runUpdateQuery(SQL, database)
    log.trace("Deleted %i recommendations..." % (rows))
    return

# Delete all of the recommendations for an Application.  This is in response to a change in the status of a final diagnosis
# and is the first step in evaluating the active FDs and calculating new recommendations.
def resetOutputs(applicationName, log, database):
    log.trace("Resetting QuantOutputs for %s" % (applicationName))
    SQL = "update DtQuantOutput " \
        " set Active = 0 where ApplicationId in (select ApplicationId "\
        " from DtApplication where ApplicationName = '%s') and Active = 1" % (applicationName)
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.trace("Reset %i QuantOutputs..." % (rows))
    return

# Lookup the application Id given the name
def fetchApplicationId(application, database=""):
    SQL = "select ApplicationId from DtApplication where Application = '%s'" % (application)
    log.trace(SQL)
    applicationId = system.db.runScalarQuery(SQL, database)
    return applicationId

# Update the application priority
def updateFamilyPriority(familyName, familyPriority, database=""):
    SQL = "update DtFamily set FamilyPriority = %i where FamilyName = '%s'" % (familyPriority, familyName)
    log.trace(SQL)
    rows = system.db.runUpdateQuery(SQL, database)
    print "Updated %i rows" % (rows)

# Look up the final diagnosis id given the application, family, and final Diagnosis names
def fetchFinalDiagnosis(application, family, finalDiagnosis, database=""):
    SQL = "select U.UnitName, FD.FinalDiagnosisId, FD.FinalDiagnosisName, FD.FamilyId, FD.FinalDiagnosisPriority, FD.CalculationMethod, "\
        " FD.PostTextRecommendation, FD.TextRecommendationCallback, FD.RefreshRate, FD.TextRecommendation "\
        " from TkUnit U, DtFinalDiagnosis FD, DtFamily F, DtApplication A"\
        " where U.UnitId = A.UnitId and A.ApplicationId = F.ApplicationId "\
        " and FD.FamilyId = F.FamilyId "\
        " and A.ApplicationName = '%s'" \
        " and F.FamilyName = '%s'" \
        " and FD.FinalDiagnosisName = '%s'" % (application, family, finalDiagnosis)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    from ils.common.database import toDict
    records=toDict(pds)
    if len(records) == 0:
        record={}
    else:
        record = records[0]
    return record

# Fetch all of the active final diagnosis for an application.
# Order the diagnosis from most import to least important - remember that the numeric priority is such that
# low numbers are higher priority than high numbers. 
def fetchActiveDiagnosis(applicationName, database=""):
    SQL = "select A.ApplicationName, F.FamilyName, F.FamilyId, FD.FinalDiagnosisName, FD.FinalDiagnosisPriority, FD.FinalDiagnosisId, "\
        " DE.DiagnosisEntryId, F.FamilyPriority, DE.ManualMove, DE.ManualMoveValue, DE.RecommendationMultiplier, "\
        " DE.RecommendationErrorText "\
        " from DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtDiagnosisEntry DE "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and DE.Status = 'Active' " \
        " and not (FD.CalculationMethod != 'Constant' and (DE.RecommendationStatus in ('WAIT','NO-DOWNLOAD','DOWNLOAD'))) " \
        " and A.ApplicationName = '%s'"\
        " order by FamilyPriority ASC, FinalDiagnosisPriority ASC"  % (applicationName) 
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

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
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.QuantOutputId "\
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
        
        outputList.append(output)
    return pds, outputList


# Fetch the SQC blocks that led to a Final Diagnosis becoming true.
# We could implement this in one of two ways: 1) we could insert something into the database when the FD becomes true
# or 2) At the time we want to know the SQC blocks, we could query the diagram.
def fetchSQCRootCauseForFinalDiagnosis(finalDiagnosis, database=""):
    #TODO Need to implement this
    print "**** NEED TO IMPLEMENT fetchSQCRootCauseForFinalDiagnosis() ****"
    sqcRootCause=[]
    return sqcRootCause


def fetchActiveOutputsForPost(post, database=""):
    SQL = "select distinct A.ApplicationName, QO.QuantOutputName, QO.TagPath, QO.OutputLimitedStatus, QO.OutputLimited, "\
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.IncrementalOutput, "\
        " QO.CurrentSetpoint, QO.FinalSetpoint, QO.DisplayedRecommendation, QO.QuantOutputId "\
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
    print "Using database: ", database
    pds = system.db.runQuery(SQL, database)
    return pds

#
def fetchQuantOutput(quantOutputId, database=""):
    SQL = "select QO.QuantOutputName, QO.TagPath, QO.OutputLimitedStatus, QO.OutputLimited, QO.OutputPercent, "\
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.IncrementalOutput, "\
        " QO.CurrentSetpoint, QO.FinalSetpoint, QO.DisplayedRecommendation, QO.QuantOutputId, QO.MostNegativeIncrement, "\
        " QO.MostPositiveIncrement, QO.MinimumIncrement, QO.SetpointHighLimit, QO.SetpointLowLimit "\
        " from DtQuantOutput QO "\
        " where QO.QuantOutputId = %i "  % (quantOutputId)
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
