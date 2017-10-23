'''
Created on Sep 9, 2014

@author: ILS
'''

import sys, system, string, traceback
#import project, shared
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from ils.queue.constants import QUEUE_INFO, QUEUE_ERROR
from ils.diagToolkit.constants import RECOMMENDATION_REC_MADE, RECOMMENDATION_NONE_MADE, RECOMMENDATION_POSTED, AUTO_NO_DOWNLOAD
log = LogUtil.getLogger("com.ils.diagToolkit.recommendation")
logSQL = LogUtil.getLogger("com.ils.diagToolkit.SQL")


def notifyConsole():
    print "Waking up the console"

# This is a replacement to em-quant-recommend-gda
def makeRecommendation(application, familyName, finalDiagnosisName, finalDiagnosisId, diagnosisEntryId, constantFD, calculationMethod, 
                       postTextRecommendation, textRecommendation, database="", provider=""):
    log.infof("********** In %s *********", __name__)

    log.infof("Making a recommendation for final diagnosis with id: %s using calculation method: <%s>, Constant=<%s>, \
        database: %s, provider: %s", str(finalDiagnosisId), calculationMethod, str(constantFD), database, provider)

    # If the FD is constant, then it shouldn't get this far because there really isn't a recommendation to make, so this code should never get exercised.
    if constantFD == True:
        print "The FD IS a CONSTANT"
        log.infof("Detected a CONSTANT Final Diagnosis")
        
        SQL = "Update DtDiagnosisEntry set RecommendationStatus = '%s' where DiagnosisEntryId = %i " % (RECOMMENDATION_POSTED, diagnosisEntryId)
        logSQL.trace(SQL)
        system.db.runUpdateQuery(SQL, database)

        recommendationList=[]
        return recommendationList, "", "SUCCESS"

    # If they specify shared or project scope, then we don't need to do this
    if calculationMethod not in ["", None] and (not(string.find(calculationMethod, "project") == 0 or string.find(calculationMethod, "shared") == 0)):
        # The method contains a full python path, including the method name
        try:
            separator=string.rfind(calculationMethod, ".")
            packagemodule=calculationMethod[0:separator]
            separator=string.rfind(packagemodule, ".")
            package = packagemodule[0:separator]
            module  = packagemodule[separator+1:]
            log.info("   ...using External Python, the package is: <%s>.<%s>" % (package,module))
            exec("import %s" % (package))
            exec("from %s import %s" % (package,module))
        except:
            errorType,value,trace = sys.exc_info()
            errorTxt = traceback.format_exception(errorType, value, trace, 500)
            log.errorf("Caught an exception importing an external reference method named %s %s", calculationMethod, errorTxt)
            return [], "", "ERROR"
        else:
            log.tracef("...import of external reference was successful...")
            
    try:
        if calculationMethod in ["", None]:
            log.infof("Implementing a static text recommendation because there is not a calculation method.")
            calculationSuccess = True
            explanation = ""
            rawRecommendationList = []
        else:
            calculationSuccess, explanation, rawRecommendationList = eval(calculationMethod)(application,finalDiagnosisName,finalDiagnosisId,provider,database)
            log.infof("...back from the calculation method!")
    except:
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 500)
        log.errorf("Caught an exception calling calculation method named %s %s", calculationMethod, errorTxt)
        return [], "", "ERROR"
    
    else:
        log.infof("The calculation method returned explanation: %s", explanation)
        log.infof("Received recommendations: %s", str(rawRecommendationList))
    
        # Insert text returned by the calculation method into the application Queue
        if calculationSuccess:
            messageLevel = QUEUE_INFO
        else:
            messageLevel = QUEUE_ERROR
    
        if textRecommendation != "":
            explanation = "%s  %s" % (textRecommendation, explanation)
    
        postApplicationMessage(application, messageLevel, explanation, log, database)

        # We want to weed out a recommendation with a value of 0.0 - We don't want to treat these as a less than minimum change.
        # I'm not exactly sure why we don't let the generic check for insignificant recommendation handle this... seems redundant...
        log.infof("Screening for no-change recommendations...") 
        screenedRecommendationList=[]
        for recommendation in rawRecommendationList:
            if recommendation.get("Value",0.0) == 0.0:
                log.infof("...removing a no change recommendation: %s", str(recommendation))
            else:
                screenedRecommendationList.append(recommendation)

        # If the FD is a text recommendation then the FD will be cleared when the loud workspace is acknowledged!
        if not(postTextRecommendation) and len(screenedRecommendationList) == 0:
            log.infof("Performing an automatic NO-DOWNLOAD because there are no recommendations for final diagnosis %s - %s...", str(finalDiagnosisId), finalDiagnosisName)
            from ils.diagToolkit.common import fetchPostForApplication
            post=fetchPostForApplication(application, database)
                
            from ils.diagToolkit.setpointSpreadsheet import resetApplication
            resetApplication(post=post, application=application, families=[familyName], finalDiagnosisIds=[finalDiagnosisId], quantOutputIds=[], actionMessage=AUTO_NO_DOWNLOAD, recommendationStatus=AUTO_NO_DOWNLOAD, database=database, provider=provider)
            return [], "", RECOMMENDATION_NONE_MADE
        else:
            SQL = "Update DtDiagnosisEntry set RecommendationStatus = '%s' where DiagnosisEntryId = %i " % (RECOMMENDATION_REC_MADE, diagnosisEntryId)
            logSQL.trace(SQL)
            system.db.runUpdateQuery(SQL, database)
    
            recommendationList=[]
            log.infof("  The recommendations returned from the calculation method are: ")
            for recommendation in screenedRecommendationList:
                # Validate that there is a 'QuantOutput' key and a 'Value' Key
                quantOutput = recommendation.get('QuantOutput', None)
                if quantOutput == None:
                    log.errorf("ERROR: A recommendation returned from %s did not contain a 'QuantOutput' key", calculationMethod)
                val = recommendation.get('Value', None)
                if val == None:
                    log.errorf("ERROR: A recommendation returned from %s did not contain a 'Value' key", calculationMethod)
        
                if quantOutput != None and val != None:
                    log.infof("      Output: %s - Value: %s", quantOutput, str(val))
                    recommendation['AutoRecommendation']=val
                    recommendation['AutoOrManual']='Auto'
                    recommendationId = insertAutoRecommendation(finalDiagnosisId, diagnosisEntryId, quantOutput, val, database)
                    recommendation['RecommendationId']=recommendationId
                    del recommendation['Value']
                    recommendationList.append(recommendation)

    return recommendationList, explanation, "SUCCESS"

# Insert a recommendation into the database
def insertAutoRecommendation(finalDiagnosisId, diagnosisEntryId, quantOutputName, val, database):
    SQL = "select RecommendationDefinitionId "\
        "from DtRecommendationDefinition RD, DtQuantOutput QO "\
        "where RD.QuantOutputID = QO.QuantOutputId "\
        " and RD.FinalDiagnosisId = %i "\
        " and QO.QuantOutputName = '%s'" % (finalDiagnosisId, quantOutputName)
    logSQL.trace(SQL)
    recommendationDefinitionId = system.db.runScalarQuery(SQL, database)
    
    if recommendationDefinitionId == None:
        log.error("Unable to fetch a recommendation definition for output <%s> for finalDiagnosis with id: %i" % (quantOutputName, finalDiagnosisId))
        return -1
    
    SQL = "insert into DtRecommendation (RecommendationDefinitionId,DiagnosisEntryId,Recommendation,AutoRecommendation,AutoOrManual) "\
        "values (%i,%i,%f,%f,'Auto')" % (recommendationDefinitionId, diagnosisEntryId, val, val)
    logSQL.trace(SQL)
    recommendationId = system.db.runUpdateQuery(SQL,getKey=True, database=database)
    log.infof("      ...inserted recommendation id: %s for recommendation definition id: %s", recommendationId, str(recommendationDefinitionId))
    return recommendationId

# QuantOutput is a dictionary with all of the attributes of a QuantOut and a list of the recommendations that have been made
# for that QuantOutput - in the case where multiple FDs are active and of equal priority and tough the same quantOutput.
def calculateFinalRecommendation(quantOutput):
    log.infof("Calculating the final recommendation for: %s ", quantOutput)

    i = 0
    finalRecommendation = 0.0
    recommendations = quantOutput.get("Recommendations", [])
    
    # It certainly isn't normal to get to this point and NOT have any recommendations but it is possible that a FD may have 5 outputs defined
    # and for a certain situation may only decide to change 3 of them, for example.  This should not be treated as an error and should not cause
    # the minimum change warning to kick in for the 2 quant outputs that were not changed.
    if len(recommendations) == 0:
        log.error("No recommendations were found for quant output: %s" % (quantOutput.get("QuantOutput", "Unknown")))
        return None
        
    for recommendation in recommendations:
        log.infof("  The raw recommendation is: %s", str(recommendation))
            
        autoOrManual = string.upper(quantOutput.get("AutoOrManual", "Auto"))
        if autoOrManual == 'AUTO':
            recommendationValue = recommendation.get('AutoRecommendation', 0.0)
            log.infof("   ...using the auto value: %f", recommendationValue)
        else:
            recommendationValue = recommendation.get('ManualRecommendation', 0.0)
            log.infof("   ...using the manual value: %f", recommendationValue)
    
        feedbackMethod = string.upper(quantOutput.get('FeedbackMethod','Simple Sum'))
        log.infof("   ...using feedback method %s to combine recommendations...", feedbackMethod)

        if feedbackMethod == 'MOST POSITIVE':
            if i == 0: 
                finalRecommendation = recommendationValue 
            else: 
                finalRecommendation = max(recommendationValue, finalRecommendation)
        elif feedbackMethod == 'MOST NEGATIVE':
            if i == 0: 
                finalRecommendation = recommendationValue 
            else: 
                finalRecommendation = min(recommendationValue, finalRecommendation)
        elif feedbackMethod == 'AVERAGE':
            if i == 0: 
                total = recommendationValue
                finalRecommendation =  recommendationValue
            else: 
                total = recommendationValue + total
                finalRecommendation = total / (i + 1)
        elif feedbackMethod == 'SIMPLE SUM':
            if i == 0: 
                finalRecommendation = recommendationValue 
            else: 
                finalRecommendation = recommendationValue + finalRecommendation
            
        i = i + 1

    quantOutput['ManualOverride'] = False
    quantOutput['FeedbackOutputManual'] = 0.0
    quantOutput['OutputLimited'] = False
    quantOutput['OutputLimitedStatus'] = 'Not Bound'
    quantOutput['OutputPercent'] = 100.0
    quantOutput['FeedbackOutput'] = finalRecommendation
    quantOutput['FeedbackOutputConditioned'] = finalRecommendation

    log.infof("  The recommendation after combining multiple recommendations but before bounds checking) is: %f", finalRecommendation)
    return quantOutput

def test(applicationName, familyName, finalDiagnosisName, calculationMethod, database="", provider=""):
    log.infof("*** In recommendation.test() ***")
    # We could fetch the actual finalDiagnosis Id from the database, but for now I don't think anyone uses it...
    from ils.diagToolkit.common import fetchFinalDiagnosis
    fdDict=fetchFinalDiagnosis(applicationName, familyName, finalDiagnosisName, database)
    finalDiagnosisId = fdDict.get("FinalDiagnosisId")
    
    print "Testing %s (%i) - %s" % (finalDiagnosisName, finalDiagnosisId, calculationMethod)

#    if string.upper(calculationMethod) == "CONSTANT":
#        print "Bypassing calculations for a CONSTANT calculation method!"
#        return "", []

    # If they specify shared or project scope, then we don't need to do this
    if not(string.find(calculationMethod, "project") == 0 or string.find(calculationMethod, "shared") == 0):
        # The method contains a full python path, including the method name
        separator=string.rfind(calculationMethod, ".")
        packagemodule=calculationMethod[0:separator]
        separator=string.rfind(packagemodule, ".")
        package = packagemodule[0:separator]
        module  = packagemodule[separator+1:]
        log.infof("   ...using External Python, the package is: <%s>.<%s>", package, module)
        exec("import %s" % (package))
        exec("from %s import %s" % (package,module))

    status, explanation, rawRecommendationList = eval(calculationMethod)(applicationName,finalDiagnosisName, finalDiagnosisId, provider,database)

    if len(rawRecommendationList) == 0:
        log.infof("No recommendations were returned!")
    else:
        log.infof("Recommendations: %s", str(rawRecommendationList))

    return status, explanation, rawRecommendationList

def postApplicationMessage(applicationName, status, message, log, database):
    SQL = "select MessageQueueId from DtApplication where ApplicationName = '%s'" % (applicationName)
    queueId = system.db.runScalarQuery(SQL, database)
    from ils.queue.message import _insert
    _insert(queueId, status, message, database)
    log.infof("%s - %s", str(status), str(message))