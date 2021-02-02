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
                       postTextRecommendation, textRecommendation, zeroChangeThreshold, database="", provider=""):
    log.tracef("********** In %s.makeRecommendation() *********", __name__)

    log.infof("Making a recommendation for final diagnosis with id: %s using calculation method: <%s>, Constant=<%s>, database: %s, provider: %s", str(finalDiagnosisId), calculationMethod, str(constantFD), database, provider)

    # If the FD is constant, then it shouldn't get this far because there really isn't a recommendation to make, so this code should never get exercised.
    if constantFD == True:
        log.tracef("Detected a CONSTANT Final Diagnosis")
        
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
            log.trace("   ...using External Python, the package is: <%s>.<%s>" % (package,module))
            exec("import %s" % (package))
            exec("from %s import %s" % (package,module))
        except:
            errorType,value,trace = sys.exc_info()
            errorTxt = str(traceback.format_exception(errorType, value, trace, 500))
            log.errorf("Caught an exception importing an external reference method named %s %s", str(calculationMethod), errorTxt)
            return [], errorTxt, "ERROR"
        else:
            log.tracef("...import of external reference was successful...")
            
    try:
        if calculationMethod in ["", None]:
            log.tracef("Implementing a static text recommendation because there is not a calculation method.")
            calculationSuccess = True
            explanation = ""
            rawRecommendationList = []
        else:
            calculationSuccess, explanation, rawRecommendationList = eval(calculationMethod)(application,finalDiagnosisName,finalDiagnosisId,provider,database)
            log.tracef("...back from the calculation method!")
    except:
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 500)
        errorTxt = "Caught an exception calling calculation method named %s %s" % (str(calculationMethod), str(errorTxt))
        log.errorf("%s", errorTxt)
        return [], errorTxt, "ERROR"
    
    else:
        log.tracef("The calculation method returned explanation: %s", explanation)
        
        ''' Make the quant output name case insensitive by casting to uppercase (need to the same for Quant Output names) '''
        i = 0
        for rec in rawRecommendationList:
            qo = string.upper(rec.get("QuantOutput"))
            rec["QuantOutput"] = qo
            rawRecommendationList[i] = rec
            i = i +1
        log.tracef("Received recommendations: %s", str(rawRecommendationList))
    
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
        log.tracef("Screening for no-change recommendations...") 
        screenedRecommendationList=[]
        for recommendation in rawRecommendationList:
            if abs(recommendation.get("Value",0.0)) < zeroChangeThreshold:
                log.tracef("...removing a no change recommendation (using threshold %.6f): %s", zeroChangeThreshold, str(recommendation))
            else:
                screenedRecommendationList.append(recommendation)

        # If the FD is a text recommendation then the FD will be cleared when the loud workspace is acknowledged!
        if not(postTextRecommendation) and len(screenedRecommendationList) == 0:
            log.infof("Performing an automatic NO-DOWNLOAD because there are no recommendations for final diagnosis %s - %s after screening for no change recommendations...", str(finalDiagnosisId), finalDiagnosisName)
            from ils.diagToolkit.common import fetchPostForApplication
            post=fetchPostForApplication(application, database)
                
            from ils.diagToolkit.setpointSpreadsheet import resetApplication
            resetApplication(post=post, application=application, families=[familyName], finalDiagnosisIds=[finalDiagnosisId], quantOutputIds=[], actionMessage=AUTO_NO_DOWNLOAD, recommendationStatus=AUTO_NO_DOWNLOAD, database=database, provider=provider)
            
            '''
            If we auto-nodownload on the highest priority problem, we should do another manage just to check if there is an active lower priority problem.
            '''
            from ils.diagToolkit.finalDiagnosis import requestToManage
            requestToManage(application, database, provider)
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
                    
                rampTime = recommendation.get('RampTime', None)
        
                if quantOutput != None and val != None:
                    log.infof("      Output: %s - Value: %s - Ramp Time: %s", quantOutput, str(val), str(rampTime))
                    recommendation['AutoRecommendation']=val
                    recommendation['AutoOrManual']='Auto'
                    recommendationId = insertAutoRecommendation(finalDiagnosisId, diagnosisEntryId, quantOutput, val, rampTime, database)
                    recommendation['RecommendationId']=recommendationId
                    del recommendation['Value']
                    recommendationList.append(recommendation)

    return recommendationList, str(explanation), "SUCCESS"

# Insert a recommendation into the database
def insertAutoRecommendation(finalDiagnosisId, diagnosisEntryId, quantOutputName, val, rampTime, database):
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
    
    if rampTime == None:
        rampTime = "NULL"
    
    SQL = "insert into DtRecommendation (RecommendationDefinitionId, DiagnosisEntryId, Recommendation, AutoRecommendation, AutoOrManual, RampTime) "\
        "values (%i, %i, %f, %f, 'Auto', %s)" % (recommendationDefinitionId, diagnosisEntryId, val, val, str(rampTime))
    logSQL.trace(SQL)
    recommendationId = system.db.runUpdateQuery(SQL,getKey=True, database=database)
    log.tracef("      ...inserted recommendation id: %s for recommendation definition id: %s", recommendationId, str(recommendationDefinitionId))
    return recommendationId

def determineRampTime(quantOutputs, groupRampMethod):
    '''
    If the recommendation is for a ramp controller then it MUST contain a rampTime property
    (If there are multiple recommendations for the same ramp output with different ramp times then the last one wins - that probably isn't right TODO
    '''
    log.tracef("Determining the group ramp time using strategy %s ", groupRampMethod)
    rampTimes = []
    
    for quantOutput in quantOutputs:
        recommendations = quantOutput.get("Recommendations", [])    

        for recommendation in recommendations:
            log.tracef("  The raw recommendation is: %s", str(recommendation))
            
            if recommendation.get("RampTime", None) != None:
                log.tracef("   ...found a ramp time in the recommendation, adding it to the quantOutput...")
                rampTime = recommendation.get("RampTime", None)
                if rampTime <> None:
                    rampTimes.append(rampTime)
        
    if len(rampTimes) > 0:
        if string.upper(groupRampMethod) == "LONGEST": 
            rampTime = max(rampTimes)
        elif string.upper(groupRampMethod) == "SHORTEST": 
            rampTime = min(rampTimes)
        elif string.upper(groupRampMethod) == "AVERAGE":
            total = 0
            for val in rampTimes:
                total = total + val
            rampTime = total / len(rampTimes)
        else:
            rampTime = None

        log.tracef("Calculated a ramp time of %f using %s strategy from %s", rampTime, groupRampMethod, str(rampTimes))
    else:
        log.tracef("There are no ramp recommendations!")
        rampTime = None

    return rampTime

# QuantOutput is a dictionary with all of the attributes of a QuantOut and a list of the recommendations that have been made
# for that QuantOutput - in the case where multiple FDs are active and of equal priority and tough the same quantOutput.
def calculateFinalRecommendation(quantOutput, groupRampTime):
    log.tracef("Calculating the final recommendation for: %s with group ramp time: %s", quantOutput, str(groupRampTime))
    
    feedbackMethod = string.upper(quantOutput.get('FeedbackMethod','Simple Sum'))
    log.tracef("   ...using feedback method %s to combine recommendations...", feedbackMethod)

    i = 0
    finalRecommendation = 0.0
    recommendations = quantOutput.get("Recommendations", [])
    
    '''
     It certainly isn't normal to get to this point and NOT have any recommendations but it is possible that a FD may have 5 outputs defined
    and for a certain situation may only decide to change 3 of them, for example.  This should not be treated as an error and should not cause
    the minimum change warning to kick in for the 2 quant outputs that were not changed.
    '''
    if len(recommendations) == 0:
        log.error("No recommendations were found for quant output: %s" % (quantOutput.get("QuantOutput", "Unknown")))
        return None

    isaRamp = False
    for recommendation in recommendations:
        log.tracef("  The raw recommendation is: %s", str(recommendation))
            
        autoOrManual = string.upper(quantOutput.get("AutoOrManual", "Auto"))
        if autoOrManual == 'AUTO':
            recommendationValue = recommendation.get('AutoRecommendation', 0.0)
            log.tracef("   ...using the auto value: %s", str(recommendationValue))
        else:
            recommendationValue = recommendation.get('ManualRecommendation', 0.0)
            log.tracef("   ...using the manual value: %s", str(recommendationValue))
        
        rampTime = recommendation.get("RampTime", None)
        if rampTime <> None:
            isaRamp = True

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
    
    if isaRamp:
        if groupRampTime in [None, "None"]:
            quantOutput["Ramp"] = rampTime
        else:
            quantOutput["Ramp"] = groupRampTime

    log.tracef("  The recommendation after combining multiple recommendations but before bounds checking) is: %s", str(finalRecommendation))
    return quantOutput


def test(applicationName, familyName, finalDiagnosisName, calculationMethod, database="", provider=""):
    log.infof("*** In recommendation.test() ***")
    # We could fetch the actual finalDiagnosis Id from the database, but for now I don't think anyone uses it...
    from ils.diagToolkit.common import fetchFinalDiagnosis
    fdDict=fetchFinalDiagnosis(applicationName, familyName, finalDiagnosisName, database)
    finalDiagnosisId = fdDict.get("FinalDiagnosisId")
    
    log.infof("Testing %s (%i) - %s", finalDiagnosisName, finalDiagnosisId, calculationMethod)

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

    return status, str(explanation), rawRecommendationList

def postApplicationMessage(applicationName, status, message, log, database):
    SQL = "select MessageQueueId from DtApplication where ApplicationName = '%s'" % (applicationName)
    queueId = system.db.runScalarQuery(SQL, database)
    
    SQL = "select QueueKey from QueueMaster where QueueId = %s" % (queueId)
    queueKey = system.db.runScalarQuery(SQL, database)
    
    from ils.queue.message import _insert
    _insert(queueKey, queueId, status, message, database)
    log.infof("%s - %s", str(status), str(message))