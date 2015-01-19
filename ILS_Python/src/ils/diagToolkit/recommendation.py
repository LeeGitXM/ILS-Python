'''
Created on Sep 9, 2014

@author: ILS
'''

import system, string
import ils
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit.recommendation")

# NOTE: We need these two imports in order to get the classes generically.
# We require the "wild" import so that we can iterate over classes
# NOTE: __init__.py defines the modules
import xom.vistalon.diagToolkit
from xom.vistalon.diagToolkit import *

def hello():
    print "Hello There!"

def notifyConsole():
    print "Waking up the console"

# This is a replacement to em-quant-recommend-gda
def makeRecommendation(application, family, finalDiagnosis, finalDiagnosisId, diagnosisEntryId, database=""):
    print "Making a recommendation"
   
    SQL = "select CalculationMethod "\
        "from DtFinalDiagnosis "\
        "where FinalDiagnosisId = %s " % (finalDiagnosisId)
    calculationMethod = system.db.runScalarQuery(SQL, database)
    print "The calculation method is ", calculationMethod
    
    func = eval(calculationMethod)
    textRecommendation, rawRecommendationList = func()
    print "The list of recommendations is: ", rawRecommendationList
    
    recommendationList=[]
    for recommendation in rawRecommendationList:
        # Validate that there is a 'QuantOutput' key and a 'Value' Key
        quantOutput = recommendation.get('QuantOutput', None)
        if quantOutput == None:
            log.error("ERROR: A recommendation returned from %s did not contain a 'QuantOutput' key" % (calculationMethod))
        val = recommendation.get('Value', None)
        if val == None:
            log.error("ERROR: A recommendation returned from %s did not contain a 'Value' key" % (calculationMethod))

        if quantOutput != None and val != None:
            val = recommendation.get('Value', 0.0)
            recommendation['AutoRecommendation']=val
            recommendation['AutoOrManual']='Auto'
            recommendationId = insertAutoRecommendation(finalDiagnosisId, diagnosisEntryId, quantOutput, val, database)
            recommendation['RecommendationId']=recommendationId
            del recommendation['Value']
            recommendationList.append(recommendation)

    return textRecommendation, recommendationList

# Insert a recommendation into the database
def insertAutoRecommendation(finalDiagnosisId, diagnosisEntryId, quantOutput, val, database):
    
    SQL = "select RecommendationDefinitionId "\
        "from DtRecommendationDefinition RD, DtQuantOutput QO "\
        "where RD.QuantOutputID = QO.QuantOutputId "\
        " and RD.FinalDiagnosisId = %i "\
        " and QO.QuantOutput = '%s'" % (finalDiagnosisId, quantOutput)
    recommendationDefinitionId = system.db.runScalarQuery(SQL, database)
    
    SQL = "insert into DtRecommendation (RecommendationDefinitionId,DiagnosisEntryId,Recommendation,AutoRecommendation,AutoOrManual) "\
        "values (%i,%i,%f,%f,'Auto')" % (recommendationDefinitionId, diagnosisEntryId, val, val)
    print SQL
    recommendationId = system.db.runUpdateQuery(SQL,getKey=True, database=database)
    return recommendationId

# QuantOutput is a dictionary with all of the attributes of a QuantOut and a list of the recommendations that have been made.
def calculateFinalRecommendation(quantOutput):
    print "\nCalculating the final recommendation for ", quantOutput

    i = 0
    finalRecommendation = 0.0
    recommendations = quantOutput.get("Recommendations", [])
    for recommendation in recommendations:
        print "  Recommendation: ", recommendation
            
        autoOrManual = string.upper(quantOutput.get("AutoOrManual", "Auto"))
        if autoOrManual == 'AUTO':
            recommendationValue = recommendation.get('AutoRecommendation', 0.0)
        else:
            recommendationValue = recommendation.get('ManualRecommendation', 0.0)
    
        feedbackMethod = string.upper(quantOutput.get('FeedbackMethod','Simple Sum'))
        print "  Feedback Method: ", feedbackMethod
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
    quantOutput['FeedbackOutputConditioned'] = 0.0
    quantOutput['OutputLimited'] = False
    quantOutput['OutputLimitedStatus'] = 'Not Bound'
    quantOutput['FeedbackOutput'] = finalRecommendation
    quantOutput['FeedbackOutputConditioned'] = finalRecommendation

    print "Returning:", quantOutput, "\n"
    return quantOutput