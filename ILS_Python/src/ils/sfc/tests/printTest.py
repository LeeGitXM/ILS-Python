'''
Created on Jun 27, 2018

@author: phass
'''

import system
from ils.sfc.gateway.api import getDatabaseName, getProviderName

def test1(chart,block):
    print "Running %s.test1()..." % (__name__)
    project = "XOM"
    provider = getProviderName(chart)
    database = getDatabaseName(chart)
    reportName = "Vistalon/Catout Rate Change Data"

    # Read the reactor configuration
    paths = []
    paths.append("[%s]Configuration/SFC/CATOUT-PRINT-PATH" % (provider))
    paths.append("[%s]Configuration/SFC/CATOUT-PRINT-FILE-NAME" % (provider))
    paths.append("[%s]Configuration/SFC/CATOUT-PRINTER" % (provider))
    values = system.tag.readAll(paths)
    print values

    path = values[0].value
    fileName = values[1].value
    printer = values[2].value

    chartPath = "VistalonUnitProcedure/PolymerizeEpdm/RateChange/SingleRxRateChange/SingleRxRateChange"    
    stepName = "CurrentData"
    rxConfig = "foobar"
    
    # Save the report to the event directory
    parameters = {"Configuration":rxConfig, "ChartPath": chartPath, "StepName": stepName}
    actionDictionary = {"path":path, "fileName": fileName, "format": "pdf"}
    
    system.report.executeAndDistribute(path=reportName, project=project, parameters=parameters, action="save", actionSettings=actionDictionary)
 
    # Print the report
    actionDictionary = {"primaryPrinterName": printer}
    
    # This should work but it doesn't
    #system.report.executeAndDistribute(path=reportName, project=project, parameters=parameters, action="print", actionSettings=actionDictionary)
    
    # This doesn't match the documentation, but it works!
    # system.report.executeAndDistribute(path=reportName, project=project, parameters=parameters, action="print", actionDictionary=actionDictionary)
    system.report.executeAndDistribute(path=reportName, project=project, parameters=parameters, action="print", blahblahblah="foobar")