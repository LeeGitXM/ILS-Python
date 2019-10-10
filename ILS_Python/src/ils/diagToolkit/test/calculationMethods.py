'''
Created on May 5, 2017

@author: phass

The pupose of this test module is to test the configuration of the the test mthods for a final 
diagnosis and to perform a basic sanity check on the calculation method.  Essentially does it run,
it does not do any validation that the number is correct.  Numbers in & numbers out.

'''

import system, sys, string, traceback

def populateTable(table, applicationName):
    SQL = "select ApplicationName, FamilyName, FinalDiagnosisName, Constant, CalculationMethod, 0 as Run, '' as Status "\
        " from DtFinalDiagnosisView "\
        " where ApplicationName = '%s'" % (applicationName)
    pds = system.db.runQuery(SQL)

    header=["Application", "Family", "Final Diagnosis", "Constant", "Calculation Method", "Run", "Status"]

    data=[]
    for record in pds:
        data.append([record["ApplicationName"],record["FamilyName"], record["FinalDiagnosisName"], record["Constant"], record["CalculationMethod"], False, ""])

    ds=system.dataset.toDataSet(header, data)
    table.data=ds
    
def clearSelected(table):
    ds=table.data

    for row in range(ds.rowCount):
        run = ds.getValueAt(row,"Run")
        if run:
            ds=system.dataset.setValue(ds, row, "Status", "")

    table.data=ds

def runTest(database, provider, table):
    from ils.diagToolkit.recommendation import test as recommendationTest

    ds=table.data

    for row in range(ds.rowCount):
        applicationName = ds.getValueAt(row,"Application")
        familyName = ds.getValueAt(row,"Family")
        finalDiagnosisName = ds.getValueAt(row,"Final Diagnosis")
        calculationMethod = ds.getValueAt(row,"Calculation Method")
        run = ds.getValueAt(row,"Run")
    
        if run:
            print " "
            print "----------------------------"
    
            try:
                calculationStatus, explanation, recommendations=recommendationTest(applicationName, familyName, finalDiagnosisName, calculationMethod, database, provider)
                print "Calculation method returned: %s - %s - %s" % (calculationStatus, explanation, str(recommendations))
                status = 'Pass'
            except:
                errorType,value,trace = sys.exc_info()
                errorTxt = traceback.format_exception(errorType, value, trace, 500)
                print "Caught an exception:%s" % (errorTxt)
                status = 'Error'
        
            ds=system.dataset.setValue(ds, row, "Status", status)
    
    table.data=ds
    
    
import system
from ils.diagToolkit.common import checkFreshness, fetchDiagnosisActiveTime
from ils.diagToolkit.manualMoveEntry import fetchManualMoveInfoById

def fd1_1_1(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_1_1"
    explanation = "Close the valve because the flow is too great and needs to be minimized to reduce flooding in the control room."
    
    manualMove, manualMoveAllowed = fetchManualMoveInfoById(finalDiagnosisId, database)
    
    move = 12.3
    if manualMove in [0.0, None]:
        move = 12.3
    else:
        print "Implementing a manual move!"
        move = manualMove * move
        
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": move})
    recommendations.append({"QuantOutput": "TEST_TC102", "Value": 45.9})
    return True, explanation, recommendations

def fd1_1_1d(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_1_1d"
    explanation = "Here is some <b>dynamic</b> text from the calculation method."
    recommendations = []
    return True, explanation, recommendations

def fd1_2_1(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_1"
    explanation = "The TESTFD1_2_1 will use data of gain = 1.2, 1.5, and 0.9, SP = 23.4."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 31.4})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 53.4})
    return True, explanation, recommendations

def fd1_2_1b(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_1b"
    explanation = "The TESTFD1_2_1 will use data of gain = 1.2, 1.5, and 0.9, SP = 23.4."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 31.4})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 0.017})
    return True, explanation, recommendations

def fd1_2_1c(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_1c"
    explanation = "The TESTFD1_2_1 will return all 0.0 recommendations!"
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 0.0})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 0.0})
    return True, explanation, recommendations

def fd1_2_1d(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_1d"
    explanation = "The TESTFD1_2_1 will return insignificant recommendations."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 0.0001})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 0.0050})
    return True, explanation, recommendations

def fd1_2_1e(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_1e"
    
    print "Bypassing the output limits for Final Diagnosis Id: ", finalDiagnosisId
    from ils.diagToolkit.finalDiagnosis import bypassOutputLimits
    bypassOutputLimits(finalDiagnosisId, database)
    
    explanation = "The TESTFD1_2_1 will use data of gain = 1.2, 1.5, and 0.9, SP = 23.4."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 31.4})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 53.4})
    return True, explanation, recommendations

def fd1_2_1f(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_1f"
    explanation = "The TESTFD1_2_1 will return one of two outputs."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 13.33})
    return True, explanation, recommendations

def fd1_2_2(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_2"
    explanation = "Turn down the flame and open the window."
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 5.4})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": -20.4})
    return True, explanation, recommendations

def fd1_2_3(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3 "
    explanation = "Turn down the flame and open the window."
    recommendations = []
    
    val = system.tag.read("[XOM]DiagnosticToolkit/Inputs/T3").value
    if val < 15:
        recommendations.append({"QuantOutput": "TESTQ2", "Value": 42.9})
    else:
        recommendations.append({"QuantOutput": "TESTQ1", "Value": 6.8})
        recommendations.append({"QuantOutput": "TESTQ2", "Value": -12.3})
        recommendations.append({"QuantOutput": "TESTQ3", "Value": 15.8})
    return True, explanation, recommendations

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
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 0.00009})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 0.00009})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": 0.00009})
    return True, explanation, recommendations

def fd1_2_3e(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3e - returning 3 recommendations with lots of decimals"
    explanation = "Returning 3 recommendations which lots of precision"
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 7.123456789})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 5.123456789})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": 3.123456789})
    return True, explanation, recommendations

'''
This calculation method has a divide by 0 error.
'''
def fd1_2_3f(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3f - testing a computation error (divide by 0)"
    explanation = "Returning 3 recommendations which are all 0.0"
    myVal = 25.4 / 0.0
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": myVal})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 5.12348})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": 3.123456789})
    return True, explanation, recommendations

def fd1_2_3h(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3h - returning 3 recommendations, 1 real, 1 insignificant, and 1 = 0"
    explanation = "Returning 3 recommendations, 1 real, 1 insignificant, and 1 = 0"
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 7.123456789})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 0.000082345})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": 0.0})
    return True, explanation, recommendations

def fd1_2_3i(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd1_2_3i - returning 3 integer recommendations"
    explanation = "Returning 3 integer recommendations"
    recommendations = []
    recommendations.append({"QuantOutput": "TESTQ1", "Value": 7})
    recommendations.append({"QuantOutput": "TESTQ2", "Value": 5})
    recommendations.append({"QuantOutput": "TESTQ3", "Value": 3})
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

def fd2_1_1a(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd2_1_1a - returning recommendations for outputs and controllers"
    explanation = "Returning recommendations for outputs and controllers"
    recommendations = []
    recommendations.append({"QuantOutput": "TEST_Q21", "Value": 7.35})
    recommendations.append({"QuantOutput": "TEST_Q22", "Value": 30.54})
    recommendations.append({"QuantOutput": "TEST_Q23", "Value": -5.23})
    recommendations.append({"QuantOutput": "TEST_Q24", "Value": 12.45})

    return True, explanation, recommendations

def fd2_1_1b(applicationName, finalDiagnosisName, finalDiagnosisId, provider, database):
    print "In fd2_1_1b"
    explanation = "Get the steak out."
    recommendations = []
    
    pv = system.tag.read("[%s]DiagnosticToolkit/Inputs/Lab_Data/value" % (provider)).value
    sp = system.tag.read("[%s]DiagnosticToolkit/Inputs/T1_Target" % (provider)).value
    
    manualMove, manualMoveAllowed = fetchManualMoveInfoById(finalDiagnosisId, database)
    
    if manualMove in [0.0, None]:
        error = sp - pv
        print "Using a calculated value (%f) as the error." % (error)
    else:
        error = manualMove
        print "Using the manual move (%f) as the error." % (error)
    
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

#    recommendations.append({"QuantOutput": "TEST_Q21", "Value": 19.88})
#   recommendations.append({"QuantOutput": "TEST_Q22", "Value": 123.15})
#  recommendations.append({"QuantOutput": "TEST_Q23", "Value": 2.31})
#    recommendations.append({"QuantOutput": "TEST_Q24", "Value": 36.23})

    val = error * 5.234
    t15 = system.tag.read("[%s]DiagnosticToolkit/Inputs/T15" % (provider)).value
    if t15 < 20:
        recommendations.append({"QuantOutput": "TEST_Q25", "Value": val, "RampTime": 10.0})
    else:
        recommendations.append({"QuantOutput": "TEST_Q25", "Value": val})
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

def version():
    return "1.2"