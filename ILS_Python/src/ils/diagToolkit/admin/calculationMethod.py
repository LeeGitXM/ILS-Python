'''
Created on Dec 12, 2022

@author: phass
'''

import sys, system, string, traceback
from ils.config.client import getTagProvider, getDatabase
from ils.common.constants import CR

log = system.util.getLogger(__name__)

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()"
    db = getDatabase()
    
    SQL = "select ApplicationName, FamilyName, FinalDiagnosisName, FinalDiagnosisId, CalculationMethod, Status = '' "\
        " from DtFinalDiagnosisView "\
        " order by ApplicationName, FamilyName, FinalDiagnosisName"
    pds = system.db.runQuery(SQL, db)
    
    table = rootContainer.getComponent("Power Table")
    table.data = pds
    
def export(rootContainer):       
    print "In export()..."
    table = rootContainer.getComponent("Power Table")
    filename = system.dataset.exportCSV("calculationMethodTestResults.csv", 1, table.data)
    print "Saved table to: ", filename


def runTest(rootContainer):       
    print "In runTest()..."
    resultsTextArea = rootContainer.getComponent("Results Text Area")
    resultsTextArea.text = ""
    table = rootContainer.getComponent("Power Table")
    selectedRow = table.selectedRow
    
    test(selectedRow, table, resultsTextArea)

def runAllTests(rootContainer):
    print "In runAllTests()..."
    resultsTextArea = rootContainer.getComponent("Results Text Area")
    resultsTextArea.text = ""
    table = rootContainer.getComponent("Power Table")
    
    for row in range(table.data.getRowCount()):
        print "Row: ", row
        test(row, table, resultsTextArea)
    
def test(selectedRow, table, resultsTextArea):
    ds = table.data

    applicationName = ds.getValueAt(selectedRow, 0)
    finalDiagnosisName = ds.getValueAt(selectedRow, 2)
    finalDiagnosisId = ds.getValueAt(selectedRow, 3)
    provider = getTagProvider()
    db = getDatabase()    
    
    calculationMethod = ds.getValueAt(selectedRow, 4)
    if calculationMethod == "":
        txt = "The selected Final Diagnosis <%s> does not have a calculation method!" % (finalDiagnosisName)
        resultsTextArea.text = txt
    
        ds = system.dataset.setValue(ds, selectedRow, 5, "N/A")
        table.data = ds
        return
    
    print "Testing ", calculationMethod

    # The method contains a full python path, including the method name
    try:
        separator=string.rfind(calculationMethod, ".")
        packagemodule=calculationMethod[0:separator]
        separator=string.rfind(packagemodule, ".")
        package = packagemodule[0:separator]
        module  = packagemodule[separator+1:]
        log.trace("   ...using External Python, the package is: <%s>.<%s>" % (package, module))
        exec("import %s" % (package))
        exec("from %s import %s" % (package, module))
    except:
        errorType,value,trace = sys.exc_info()
        errorTxt = str(traceback.format_exception(errorType, value, trace, 500))
        log.errorf("Caught an exception importing an external reference method named %s %s", str(calculationMethod), errorTxt)
        ds = system.dataset.setValue(ds, selectedRow, 5, "Error")
        table.data = ds
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
            calculationSuccess, explanation, rawRecommendationList = eval(calculationMethod)(applicationName, finalDiagnosisName, finalDiagnosisId, provider, db)
            log.tracef("...back from the calculation method!")
    except:
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 500)
        errorTxt = "Caught an exception calling calculation method named %s %s" % (str(calculationMethod), str(errorTxt))
        log.errorf("%s", errorTxt)
        ds = system.dataset.setValue(ds, selectedRow, 5, "Error")
        table.data = ds
        return [], errorTxt, "ERROR"
    
    print "Calculation Success: ", calculationSuccess
    print "Explanation: ", explanation
    print "Recommendations: ", rawRecommendationList
    
    txt = "Calculation Success: %s%sExplanation: %s%s%s" % (calculationMethod, CR, explanation, CR, str(rawRecommendationList))
    resultsTextArea.text = txt
    
    ds = system.dataset.setValue(ds, selectedRow, 5, "Pass")
    table.data = ds