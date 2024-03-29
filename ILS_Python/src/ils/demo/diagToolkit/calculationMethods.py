'''
Created on Jun 18, 2018

@author: phass
'''

import system
from ils.diagToolkit.common import checkFreshness, fetchDiagnosisActiveTime

def fd1_1_1(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_1_1"
    explanation = "Close the valve because the flow is too great and needs to be minimized to reduce flooding in the control room."
    recommendations = []
    recommendations.append({"QuantOutput": "Q1", "Value": 12.3})
    return True, explanation, recommendations

def fd1_2_1(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In %s.fd1_2_1" % (__name__)
    explanation = "Use data of gain = 1.2, 1.5, and 0.9, SP = 23.4."
    recommendations = []
    recommendations.append({"QuantOutput": "Q1", "Value": 31.4})
    recommendations.append({"QuantOutput": "Q2", "Value": 53.4})
    return True, explanation, recommendations


def fd1_2_2(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_2"
    explanation = "Turn down the flame and open the window."
    recommendations = []
    recommendations.append({"QuantOutput": "Q2", "Value": 40.0, "RampTime": 2.0})
    recommendations.append({"QuantOutput": "Q3", "Value": 60.0, "RampTime": 3.0})
    return True, explanation, recommendations

def fd1_2_3(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3 "
    explanation = "Turn down the flame and open the window."
    recommendations = []
    recommendations.append({"QuantOutput": "Q1", "Value": 6.8})
    recommendations.append({"QuantOutput": "Q2", "Value": -12.3})
    recommendations.append({"QuantOutput": "Q3", "Value": 15.8})
    return True, explanation, recommendations

# A text recommendations
def fd1_2_5(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_5"
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
    print "In fd1_2_6"
    recommendations = []
    return True, "Turn up the heat", recommendations

def fd2_1_1(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd2_1_1"
    explanation = "Turn it up!."
    recommendations = []
    recommendations.append({"QuantOutput": "Q2_1", "Value": 12.3})
    return True, explanation, recommendations

def fd2_1_3(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd2_1_3"
    explanation = "Made a recommendation!."
    recommendations = []
    recommendations.append({"QuantOutput": "Q2_1", "Value": 25.0})
    return True, explanation, recommendations

def fd2_1_1_original(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd2_1_1"
    explanation = "Get the steak out."
    recommendations = []
    
    # Check that the filtered value is fresh by making sure is was updated after the unfiltered lab data value.
    filteredTagName = "[%s]LabData/RLA3/ETHYLENE-FILTERED-VALUE/filteredValue" % (provider)
    pvTagName = "[%s]LabData/RLA3/C2-LAB-DATA/value" % (provider)
    qv = system.tag.read(pvTagName)
    activeTime = qv.timestamp
    
    isFresh=checkFreshness(filteredTagName, activeTime, provider, timeout=30)
    if not(isFresh):
        print "%s: The filtered value (%s) is not fresh, proceeding with calculation anyway." % (__name__, filteredTagName)    
    
    # The data should be fresh so now read the value.
    fv = system.tag.read(filteredTagName)
    if not (fv.quality.isGood()):
        explanation = "%s - Filtered value is bad (%s) %s" % (__name__, filteredTagName, str(fv.quality))
        return False, explanation, recommendations
    fv=fv.value
    
    # Now read the source of the recipe data
    tagName="[%s]LabData/RLA3/FD-C2-LAB-DATA/value" % (provider)
    pv = system.tag.read(tagName)
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



def postDownloadSpecialActions(applicationName, actionMessage, finalDiagnosisId, provider, database):
    print "********************************"
    print "* In ", __name__
    print "*     DOING SPECIAL ACTIONS    *"
    print "********************************"

def lowViscosityHighFeed(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "Calculating the correction for Low Viscosity & High Feed"
    
    explanation=""
    recommendations=[]
        
    recommendations.append({"QuantOutput": "QO1", "Value": 16.37})
    recommendations.append({"QuantOutput": "QO2", "Value": 5.61})
    recommendations.append({"QuantOutput": "QO3", "Value": 7.8})

    return True, explanation,recommendations

def action1_1_2(blockName, blockUUID, parentUUID, provider, db):
    print "In %s.action1_1_2()" % (__name__)
    
    from ils.sfc.common.util import startChartAndOpenControlPanel

    chartPath = "Samples/Adhoc/NotifyOperator"
    controlPanelName = "Adhoc"
    project = system.util.getProjectName()
    post = "XO1TEST"
    isolationMode = False
    showControlPanel = True

    chartParams = {"reactor": "R2", "setpoint": 212.0}
    
    startChartAndOpenControlPanel(chartPath, controlPanelName, project, post, isolationMode, showControlPanel, db, chartParams=chartParams)
