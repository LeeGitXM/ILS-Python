'''
Created on Jun 28, 2015

@author: Pete
'''
def viscosity_sqc(application,finaldiagnosis):
    print "In viscosity_sqc"
    textRecommendation = "Close the valve because the flow is too great and needs to be minimized to reduce flooding in the control room."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 12.3})
    return textRecommendation, recommendations

def viscosity_feed(application,finaldiagnosis):
    print "In viscosity_feed"
    textRecommendation = "Close the valve because the flow is too great and needs to be minimized to reduce flooding in the control room."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 12.3})
    return textRecommendation, recommendations