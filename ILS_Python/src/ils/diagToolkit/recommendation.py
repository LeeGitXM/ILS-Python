'''
Created on Sep 9, 2014

@author: ILS
'''

import sys, system, string, traceback
#import project, shared
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit.recommendation")
logSQL = LogUtil.getLogger("com.ils.diagToolkit.SQL")

def notifyConsole():
    print "Waking up the console"

# This is a replacement to em-quant-recommend-gda
def makeRecommendation(application, family, finalDiagnosis, finalDiagnosisId, diagnosisEntryId, database="", provider=""):
    SQL = "select CalculationMethod "\
        "from DtFinalDiagnosis "\
        "where FinalDiagnosisId = %s " % (finalDiagnosisId)
    logSQL.trace(SQL)
    calculationMethod = system.db.runScalarQuery(SQL, database)
    log.trace("Making a recommendation for final diagnosis with id: %i using calculation method: %s, database: %s, provider: %s" % (finalDiagnosisId, calculationMethod, database, provider))
    
    if string.upper(calculationMethod) == "CONSTANT":
        log.trace("Detected a CONSTANT calculation method")
        
        SQL = "Update DtDiagnosisEntry set RecommendationStatus = 'Posted' where DiagnosisEntryId = %i " % (diagnosisEntryId)
        logSQL.trace(SQL)
        system.db.runUpdateQuery(SQL, database)
            
        textRecommendation="A constant"
        recommendationList=[]
        return textRecommendation, recommendationList, "SUCCESS"

    # If they specify shared or project scope, then we don't need to do this
    if not(string.find(calculationMethod, "project") == 0 or string.find(calculationMethod, "shared") == 0):
        # The method contains a full python path, including the method name
        separator=string.rfind(calculationMethod, ".")
        packagemodule=calculationMethod[0:separator]
        separator=string.rfind(packagemodule, ".")
        package = packagemodule[0:separator]
        module  = packagemodule[separator+1:]
        log.trace("   ...using External Python, the package is: <%s>.<%s>" % (package,module))
        exec("import %s" % (package))
        exec("from %s import %s" % (package,module))

    try:
        textRecommendation, rawRecommendationList = eval(calculationMethod)(application,finalDiagnosisId,provider,database)
    except:
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 500)
        log.error("Caught an exception calling calculation method named %s... \n%s" % (calculationMethod, errorTxt) )
        return "", [], "ERROR"
   
    else:
        if len(rawRecommendationList) == 0:
            return textRecommendation, [], "NO-RECOMMENDATIONS"
        else:
            SQL = "Update DtDiagnosisEntry set RecommendationStatus = 'REC-Made' where DiagnosisEntryId = %i " % (diagnosisEntryId)
            logSQL.trace(SQL)
            system.db.runUpdateQuery(SQL, database)
        
            recommendationList=[]
            log.trace("  The recommendations returned from the calculation method are: ")
            for recommendation in rawRecommendationList:
                # Validate that there is a 'QuantOutput' key and a 'Value' Key
                quantOutput = recommendation.get('QuantOutput', None)
                if quantOutput == None:
                    log.error("ERROR: A recommendation returned from %s did not contain a 'QuantOutput' key" % (calculationMethod))
                val = recommendation.get('Value', None)
                if val == None:
                    log.error("ERROR: A recommendation returned from %s did not contain a 'Value' key" % (calculationMethod))
    
                if quantOutput != None and val != None:
                    log.trace("      Output: %s - Value: %s" % (quantOutput, str(val)))
                    recommendation['AutoRecommendation']=val
                    recommendation['AutoOrManual']='Auto'
                    recommendationId = insertAutoRecommendation(finalDiagnosisId, diagnosisEntryId, quantOutput, val, database)
                    recommendation['RecommendationId']=recommendationId
                    del recommendation['Value']
                    recommendationList.append(recommendation)

    return textRecommendation, recommendationList, "SUCCESS"

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
    log.trace("      ...inserted recommendation id: %s for recommendation definition id: %i" % (recommendationId, recommendationDefinitionId))
    return recommendationId

# QuantOutput is a dictionary with all of the attributes of a QuantOut and a list of the recommendations that have been made
# for that QuantOutput - in the case where multiple FDs are active and of equal priority and tough the same quantOutput.
def calculateFinalRecommendation(quantOutput):
    log.trace("Calculating the final recommendation for: %s " % (quantOutput))

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
        log.trace("  The raw recommendation is: %s" % (str(recommendation)))
            
        autoOrManual = string.upper(quantOutput.get("AutoOrManual", "Auto"))
        if autoOrManual == 'AUTO':
            recommendationValue = recommendation.get('AutoRecommendation', 0.0)
            log.trace("   ...using the auto value: %f" % (recommendationValue))
        else:
            recommendationValue = recommendation.get('ManualRecommendation', 0.0)
            log.trace("   ...using the manual value: %f" % (recommendationValue))
    
        feedbackMethod = string.upper(quantOutput.get('FeedbackMethod','Simple Sum'))
        log.trace("   ...using feedback method %s to combine recommendations..." % (feedbackMethod))

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

    log.trace("  The recommendation after combining multiple recommendations but before bounds checking) is: %f" % (finalRecommendation))
    return quantOutput

def test(applicationName, familyName, finalDiagnosisName, database="", provider=""):
    SQL = "select CalculationMethod "\
        "from DtFinalDiagnosisView "\
        "where ApplicationName = '%s' "\
        "  and FamilyName = '%s' "\
        "  and FinalDiagnosisName = '%s'" % (applicationName, familyName, finalDiagnosisName)
    print SQL
    calculationMethod = system.db.runScalarQuery(SQL, database)
    print "Using calculation method: <%s>" % (calculationMethod)
    
    if string.upper(calculationMethod) == "CONSTANT":
        print "Bypassing calculations for a CONSTANT calculation method!"
        return

    # If they specify shared or project scope, then we don't need to do this
    if not(string.find(calculationMethod, "project") == 0 or string.find(calculationMethod, "shared") == 0):
        # The method contains a full python path, including the method name
        separator=string.rfind(calculationMethod, ".")
        packagemodule=calculationMethod[0:separator]
        separator=string.rfind(packagemodule, ".")
        package = packagemodule[0:separator]
        module  = packagemodule[separator+1:]
        print "   ...using External Python, the package is: <%s>.<%s>" % (package, module)
        exec("import %s" % (package))
        exec("from %s import %s" % (package,module))

    textRecommendation, rawRecommendationList = eval(calculationMethod)(applicationName,finalDiagnosisName,provider,database)

    if len(rawRecommendationList) == 0:
        print "NO-RECOMMENDATIONS were returned!"
    else:
        print "Recommendations: ", rawRecommendationList

    return