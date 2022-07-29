'''
Created on Jul 11, 2022

@author: ils
'''

import system
from ils.diagToolkit.common import checkFreshness, fetchDiagnosisActiveTime
from ils.io.util import readTag

def fd1_1_1(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In %s.fd1_1_1" % (__name__)
    explanation = "Close the valve because the flow is too great and needs to be minimized to reduce flooding in the control room."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 12.3})
    return True, explanation, recommendations

def fd1_2_1(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In %s.fd1_2_1" % (__name__)
    explanation = "Get a hose and spray down the tank."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 31.4})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 53.4})
    return True, explanation, recommendations

def fd1_2_2(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In %s.fd1_2_2" % (__name__)
    explanation = "Turn down the flame and open the window."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 5.4})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": -2.4})
    return True, explanation, recommendations

def fd1_2_3(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In %s.fd1_2_3" % (__name__)
    explanation = "Turn down the flame and open the window."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 6.8})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": -12.3})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": 15.8})
    return True, explanation, recommendations

# A text recommendations
def fd1_2_5(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In %s.fd1_2_5" % (__name__)
    recommendations = []
    import random
    
    rand = random.random()
    if rand < 0.1:
        txt = "Open the door at least 20% open"
    elif rand < 0.2:
        txt = "Turn on the fanto 50% speed."
    elif rand < 0.3:
        txt = "Turn down the AC, it is 200% high"
    elif rand < 0.4:
        txt = "Turn on the auxiliary AC, need to cool by 50% at least."
    elif rand < 0.5:
        txt = "Turn on the heaters to 10% power"
    elif rand < 0.6:
        txt = "Turn on the boilers all the way up, at least 95% minimum"
    elif rand < 0.7:
        txt = "Put more coal on the fire, the boilers are running at 10% of max."
    else:
        txt = "Close the window, no more than 25% open please."
    
    return True, txt, recommendations

# A text recommendations
def fd1_2_6(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In %s.fd1_2_6" % (__name__)
    recommendations = []
    return True, "Turn up the heat", recommendations

'''
*****************************************************************************
'''





def fd1_2_3a(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3a - returning a 0.0 recommendation "
    explanation = "Turn down the flame and open the window."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 6.8})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": -12.3})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": 0.0})
    return True, explanation, recommendations

def fd1_2_3b(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3b - returning just 1 of the expected 3 recommendations "
    explanation = "Turn down the flame and open the window."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 6.8})
    return True, explanation, recommendations

def fd1_2_3c(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3c - returning 3 recommendations which are all 0.0"
    explanation = "Returning 3 recommendations which are all 0.0"
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 0.0})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 0.0})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": 0.0})
    return True, explanation, recommendations

def fd1_2_3d(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3d - returning 3 recommendations which are all 0.00001"
    explanation = "Returning 3 recommendations which are all 0.0"
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 0.00001})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 0.00001})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": 0.00001})
    return True, explanation, recommendations

def fd1_2_3e(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3e - returning 3 recommendations with lots of decimals"
    explanation = "Returning 3 recommendations which are all 0.0"
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 7.0})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 5.12348})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": 3.123456789})
    return True, explanation, recommendations

def fd1_2_3f(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3f - testing a computation error (divide by 0)"
    explanation = "Returning 3 recommendations which are all 0.0"
    myVal = 25.4 / 0.0
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": myVal})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 5.12348})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": 3.123456789})
    return True, explanation, recommendations



def fd2_1_1(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd2_1_1"
    explanation = "Get the steak out."
    recommendations = []
    
    # Check that the filtered value is fresh by making sure is was updated after the unfiltered lab data value.
    filteredTagName = "[%s]LabData/RLA3/ETHYLENE-FILTERED-VALUE/filteredValue" % (provider)
    pvTagName = "[%s]LabData/RLA3/C2-LAB-DATA/value" % (provider)
    qv = readTag(pvTagName)
    activeTime = qv.timestamp
    
    isFresh=checkFreshness(filteredTagName, activeTime, provider, timeout=30)
    if not(isFresh):
        print "%s: The filtered value (%s) is not fresh, proceeding with calculation anyway." % (__name__, filteredTagName)    
    
    # The data should be fresh so now read the value.
    fv = readTag(filteredTagName)
    if not (fv.quality.isGood()):
        explanation = "%s - Filtered value is bad (%s) %s" % (__name__, filteredTagName, str(fv.quality))
        return False, explanation, recommendations
    fv=fv.value
    
    # Now read the source of the recipe data
    tagName="[%s]LabData/RLA3/FD-C2-LAB-DATA/value" % (provider)
    pv = readTag(tagName)
    if not (pv.quality.isGood()):
        explanation = "%s - present value is bad (%s) %s" % (__name__, tagName, str(pv.quality))
        return False, explanation, recommendations
    pv=pv.value
    
    print "The PV is %s and the filtered value is %s" % (pv, fv)

    recommendations.append({"QuantOutput": "TEST_Q21", "Value":  19.88})
    recommendations.append({"QuantOutput": "TEST_Q22", "Value": 123.15})
    recommendations.append({"QuantOutput": "TEST_Q23", "Value":   2.31})
    recommendations.append({"QuantOutput": "TEST_Q24", "Value":  36.23})
    return True, explanation, recommendations

def fd1_3_3a(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_3_3a"
    explanation = ""
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 12.3})
    return True, explanation, recommendations

def fd1_3_3b(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_3_3b"
    explanation = "Close the valve because the flow is too great and needs to be minimized to reduce flooding in the control room."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 10.3})
    return True, explanation, recommendations

def fd1_3_3c(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_3_3c"
    explanation = "Open the valve because the the cows need more water!"
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": -5.4})
    return True, explanation, recommendations

def fd1_3_3d(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_3_3d"
    explanation = "Here is a dynamic text recommendation!"
    recommendations = []
    return True, explanation, recommendations