'''
Created on Sep 19, 2014

@author: Pete
'''

import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit.SQL")

# This gets called at the beginning of each recommendation management cycle.  It clears all of the dynamic attributes of a Quant Output
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

# Lookup the application Id given the name
def fetchApplicationId(application, database=""):
    SQL = "select ApplicationId from DtApplication where Application = '%s'" % (application)
    log.trace(SQL)
    applicationId = system.db.runScalarQuery(SQL, database)
    return applicationId

# Look up the final diagnosis id given the application, family, and final Diagnosis names
def fetchFinalDiagnosisId(application, family, finalDiagnosis, database=""):
    SQL = "select finalDiagnosisId "\
        " from DtFinalDiagnosis FD, DtFamily F, DtApplication A"\
        " where A.ApplicationId = F.ApplicationId "\
        " and FD.FamilyId = F.FamilyId "\
        " and A.Application = '%s'" \
        " and F.family = '%s'" \
        " and FD.FinalDiagnosis = '%s'" % (application, family, finalDiagnosis)
    log.trace(SQL)
    finalDiagnosisId = system.db.runScalarQuery(SQL, database)
    return finalDiagnosisId

# Fetch all of the active final diagnosis for an application
def fetchActiveDiagnosis(application, database=""):
    SQL = "select A.Application, F.Family, FD.FinalDiagnosis, FD.FinalDiagnosisPriority, FD.FinalDiagnosisId, DE.DiagnosisEntryId, F.FamilyPriority "\
        " from DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtDiagnosisEntry DE "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
        " and DE.Status = 'Active' " \
        " and not (FD.CalculationMethod != 'Constant' and (DE.RecommendationStatus in ('WAIT','NO-DOWNLOAD','DOWNLOAD'))) " \
        " and A.Application = '%s'"\
        " order by FamilyPriority, FinalDiagnosisPriority"  % (application) 
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds

# Fetch the outputs for a final diagnosis and return them as a list of dictionaries
# I'm not sure who the clients for this will be so I am returning all of the attributes of a quantOutput.  This includes the attributes 
# that are used when calculating/managing recommendations and the output of those recommendations.
def fetchOutputsForFinalDiagnosis(application, family, finalDiagnosis, database=""):
    SQL = "select QO.QuantOutput, QO.TagPath, QO.MostNegativeIncrement, QO.MostPositiveIncrement, QO.MinimumIncrement, QO.SetpointHighLimit, "\
        " QO.SetpointLowLimit, QO.FeedbackMethod, QO.OutputLimitedStatus, QO.OutputLimited, QO.OutputPercent, QO.IncrementalOutput, "\
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.QuantOutputId "\
        " from DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO "\
        " where A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and A.Application = '%s' "\
        " and F.Family = '%s' "\
        " and FD.FinalDiagnosis = '%s' "\
        " order by QuantOutput"  % (application, family, finalDiagnosis)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    outputList = []
    for record in pds:
        output = {}
        output['QuantOutputId'] = record['QuantOutputId']
        output['QuantOutput'] = str(record['QuantOutput'])
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

def fetchActiveOutputsForConsole(console, database=""):
    SQL = "select A.Application, QO.QuantOutput, QO.TagPath, QO.OutputLimitedStatus, QO.OutputLimited, "\
        " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride "\
        " from DtConsole C, DtConsoleSubscription CS, DtApplication A, DtFamily F, DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO "\
        " where C.ConsoleId = CS.ConsoleId "\
        " and CS.ApplicationId = A.ApplicationId "\
        " and A.ApplicationId = F.ApplicationId "\
        " and F.FamilyId = FD.FamilyId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and C.Console = '%s' "\
        " order by A.Application, QO.QuantOutput"  % (console)
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    return pds
