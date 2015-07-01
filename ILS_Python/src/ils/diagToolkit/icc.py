'''
Created on Jun 28, 2015

@author: Pete
'''
def viscosity_sqc(application,finaldiagnosis):
    print "In viscosity_sqc()"
    textRecommendation = "Close the valve because the flow is too great and needs to be minimized to reduce flooding in the control room."
    recommendations = []
    recommendations.append({"QuantOutput": "Q100", "Value": 12.3})
    recommendations.append({"QuantOutput": "Q101", "Value": 3.7})
    recommendations.append({"QuantOutput": "Q102", "Value": 3.6})
    return textRecommendation, recommendations

def viscosity_feed(application,finaldiagnosis):
    print "In viscosity_feed"
    textRecommendation = "Close the valve because the flow is too great and needs to be minimized to reduce flooding in the control room."
    recommendations = []
    recommendations.append({"QuantOutput": "Q100", "Value": 11.3})
    recommendations.append({"QuantOutput": "Q101", "Value": 1.4})
    print "Returning: ", recommendations
    
    return textRecommendation, recommendations