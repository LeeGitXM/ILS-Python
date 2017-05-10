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