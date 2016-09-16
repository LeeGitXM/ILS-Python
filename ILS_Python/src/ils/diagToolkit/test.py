'''
Created on Jun 14, 2016

@author: ils
'''
'''
Created on Apr 1, 2016

@author: ils
'''

import system

global params, sqlparams, dict, pyResults

import time
from ils.diagToolkit.finalDiagnosisClient import postDiagnosisEntry
logger=system.util.getLogger("ils.test")

T1TagName='Sandbox/Diagnostic/T1'
T2TagName='Sandbox/Diagnostic/T2'
T3TagName='Sandbox/Diagnostic/T3'
TC100TagName='Sandbox/Diagnostic/TC100/sp/value'
TC101TagName='Sandbox/Diagnostic/TC101/sp/value'

def test00():
#    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    logger=system.util.getLogger(ils.test)
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
#    postDiagnosisEntry(applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName

def test01():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 09.6789123456)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5432198765)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3456789123)
    insertApp1Families(appId,T1Id,T2Id,T3Id,postProcessingCallback='xom.vistalon.diagToolkit.test.test.postDownloadSpecialActions')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test02():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 09.6789123456)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5432198765)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3456789123)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test03a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    initLog()
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test03b():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    initLog()
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test03c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    initLog()
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test03d():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    initLog()
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName

def test04():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
        
def test05():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, feedbackMethod='Most Negative')
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, feedbackMethod='Most Negative')
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, feedbackMethod='Most Negative')
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test06():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, feedbackMethod='Average')
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, feedbackMethod='Average')
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, feedbackMethod='Average')
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
            
def test07():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, feedbackMethod='Simple Sum')
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, feedbackMethod='Simple Sum')
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, feedbackMethod='Simple Sum')
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test08a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=False)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
# Same test as above but use incremental outputs
def test08b():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=True)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=True)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=True)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
        
def test09():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=False, mostPositiveIncrement=10.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test10():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=False, setpointHighLimit=15.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test11a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, minimumIncrement=20.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test11b():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, minimumIncrement=40.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName

def test11c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, minimumIncrement=40.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_1e')
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test12a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Implement")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=10.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test12b():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Advise")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=10.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test12c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=10.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test12d():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Implement")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=5.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_3a')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
    return applicationName

def test13a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=False, setpointHighLimit=100.0, setpointLowLimit=50.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test13b():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id)    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName

# Test incremental recommendations when the setpoint is way outside the limits.
def test13c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id)    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
    return applicationName

# Test a bad output wherte the FD only writes to 1
def test14a1():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', 'Sandbox/T99', 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')    
    return applicationName

# Test a bad output where the FD writes to 2 - I think if we can't write to all of them we don't want to write to any.
def test14a2():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', 'Sandbox/T99', 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')    
    return applicationName

def test14b1():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD111calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_1_1X')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')    
    return applicationName

# This tests error handling for a non existent calculation method.  Specifically it tests that the Final diagnosis
# does not remain active and therefore block subsequent lower priority diagnosis from becoming active. 
def test14b2():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_1X')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName

def test14c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_3b')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
    return applicationName
    
def test15a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_3b')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_4', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName
    
def test15b():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_3b')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_4', 'FD_UUID', 'DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName
    
def test15c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_3b')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_4', 'FD_UUID', 'DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName
    
def test15d():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_3c')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName
    
def test15e():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_3d')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName
    
def test15f():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD121calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_3c')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID', 'DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName
    
def test15g():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD121calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_3d')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID', 'DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName

def test16a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP2'
    appId=insertApp2()
    T1Id=insertQuantOutput(appId, 'TEST_Q0_TC100', TC100TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TEST_Q1_TC101', TC101TagName, 23.5)
    insertApp2Families(appId,T1Id,T2Id,FD211calculationMethod='xom.vistalon.diagToolkit.test.test.fd2_1_1')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily2_1', 'TESTFD2_1_1', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName

def test17a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')

    applicationName='TESTAPP2'
    appId=insertApp2()
    T1Id=insertQuantOutput(appId, 'TEST_Q0_TC100', TC100TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TEST_Q1_TC101', TC101TagName, 23.5)
    insertApp2Families(appId,T1Id,T2Id,FD211calculationMethod='xom.vistalon.diagToolkit.test.test.fd2_1_1')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily2_1', 'TESTFD2_1_1', 'FD_UUID', 'DIAGRAM_UUID')
    
    return applicationName

# Test a single text recommendation
def test18a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,postProcessingCallback='xom.vistalon.diagToolkit.test.test.postDownloadSpecialActions')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName

# Simultaneously post two text recommendations
def test18b():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID')
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_5', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName

# Test a high priority text final diagnosis becoming true followed by a low priority numeric diagnosis 
def test18c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID')
    time.sleep(10.0)
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName

def test18d():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName

# Test a static (One without a calculation method) text recommendation.
def test18e():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD126calculationMethod='')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName

# This is called from a button
def clear(rootContainer):
    import system, os

    table = rootContainer.getComponent("Table")
    ds = table.data
    # Clear the results column for every selected row
    for row in range(ds.rowCount):
        selected = ds.getValueAt(row, 'selected')
        if selected:
            ds = system.dataset.setValue(ds, row, 'result', '')
    table.data = ds

# This is called from a button
def clearAll(rootContainer):
    import system, os

    table = rootContainer.getComponent("Table")
    ds = table.data
    # Clear the results column for every selected row
    for row in range(ds.rowCount):
        ds = system.dataset.setValue(ds, row, 'result', '')
    table.data = ds
    
# This is called from a button
def checkAll(rootContainer):
    import system, os

    table = rootContainer.getComponent("Table")
    ds = table.data
    # Clear the results column for every selected row
    for row in range(ds.rowCount):
        ds = system.dataset.setValue(ds, row, 'selected', True)
    table.data = ds

# This is called from a button
def uncheckAll(rootContainer):
    import system, os
    
    table = rootContainer.getComponent("Table")
    ds = table.data
    # Clear the results column for every selected row
    for row in range(ds.rowCount):
        ds = system.dataset.setValue(ds, row, 'selected', False)
    table.data = ds
    
# This is called from a button
def initLog():
    import system, time
    time.sleep(1.0)
    SQL = "delete from DtFinalDiagnosisLog"
    system.db.runUpdateQuery(SQL)        
    time.sleep(1.0)

# This is called from a button
def run(rootContainer):
    import system, os, time
    
    #-------------------------------------------
    def initializeDatabase():
        #TODO Do something smarter about DtRecommendationDefinition
        import system
        logger.info("Initializing the database...")
        for SQL in [
            "delete from DtFinalDiagnosisLog",\
            "delete from DtRecommendation", \
            "delete from QueueDetail", \
            "delete from DtDiagnosisEntry", \
            "delete from DtRecommendationDefinition where FinalDiagnosisId in (select FinalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName like 'TEST%')", \
            "delete from DtQuantOutput where QuantOutputName like 'TEST%'",\
            "delete from DtFinalDiagnosis where FinalDiagnosisName like 'TEST%'", \
            "delete from DtFamily where FamilyName like 'TEST%'", \
            "delete from DtApplication where ApplicationName like 'TEST%'" ]:
            system.db.runUpdateQuery(SQL)
        
        logger.info("...done initializing the database")
#        print "---------------------"
    #-------------------------------------------
    
    delay = 5
    path = rootContainer.getComponent("Path").text
    table = rootContainer.getComponent("Table")
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    post = "XO1TEST"

    # Clear the results column for selected rows
    cnt = 0
    for row in range(ds.rowCount):
        selected = ds.getValueAt(row, 'selected')
        if selected:
            time.sleep(delay + 2)

            rootContainer.ExecutionState = "Waiting"
            
            cnt = cnt + 1
            table.setValue(row, 'result', 'Running')
                
            functionName = ds.getValueAt(row, 'function')
            description = ds.getValueAt(row, 'description')

            # Start with a clean slate            
            initializeDatabase()
            time.sleep(2)
            
            # Run a specific test
            func = getattr(project.test.diagToolkit, functionName)
            logger.info("Starting %s..." % (functionName))
            applicationName=func()
            logger.info("   .. finished %s, application %s" % (functionName, applicationName))
            
            # Define the path to the results file in an O/S neutral way
            outputFilename = os.path.join(path,functionName + "-out.csv")
            goldFilename = os.path.join(path,functionName + "-gold.csv")

            #-------------------------------------------------------------------
            def fetchAndCompare(rootContainer=rootContainer, post=post, applicationName=applicationName, outputFilename=outputFilename, 
                goldFilename=goldFilename, table=table, row=row):
                # Fetch the results from the database
                fetchResults(post, applicationName, outputFilename)
            
                # Compare the results of this run to the Master results
                compareResults(outputFilename, goldFilename, table, row)
                
                rootContainer.ExecutionState = "Ready"
            #-------------------------------------------------------------------

            system.util.invokeLater(fetchAndCompare, delay * 1000)

    # If we get all of the way through, and there is nothing left to run, then stop the timer.
    print "Done"

# This is called from a button
def fetcher(rootContainer):
    import system, os, time
    
    applicationName = "TESTAPP1"
    path = rootContainer.getComponent("Path").text
    table = rootContainer.getComponent("Table")
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    post = "XO1TEST"
    
    # Clear the results column for selected rows
    cnt = 0
    for row in range(ds.rowCount):
        selected = ds.getValueAt(row, 'selected')
        if selected:
            cnt = cnt + 1
            functionName = ds.getValueAt(row, 'function')
            description = ds.getValueAt(row, 'description')

            # Define the path to the results file in an O/S neutral way
            outputFilename = os.path.join(path,functionName + "-out.csv")
            goldFilename = os.path.join(path,functionName + "-gold.csv")

            # Fetch the results from the database
            fetchResults(post, applicationName, outputFilename)

            # Compare the results of this run to the Master results
            compareResults(outputFilename, goldFilename, table, row)

    # If we get all of the way through, and there is nothing left to run, then stop the timer.
    print "Done"

# There are several sets of Data here, When I compare them I load them into a single datset.
# So make sure that the recommendation records have the same number of columns as the 
# QuantOutput dataset.
def fetchResults(post, application, filename):

    #----------------
    # Fetch Recommendations
    def logRecommendations(post):
        SQL = "select count(*) from DtRecommendation"
        rows = system.db.runScalarQuery(SQL)
        print "***************  There are %i rows" % (rows)
        
        import string
        SQL = "select F.FamilyName, F.FamilyPriority, FD.FinalDiagnosisName, FD.FinalDiagnosisPriority, DE.Status, "\
            " DE.RecommendationStatus, DE.TextRecommendation, QO.QuantOutputName, QO.TagPath, R.Recommendation, "\
            " R.AutoRecommendation, R.ManualRecommendation "\
            " from DtFamily F, DtFinalDiagnosis FD, DtDiagnosisEntry DE, DtRecommendationDefinition RD, "\
            "      DtQuantOutput QO, DtRecommendation R"\
            " where F.FamilyId = FD.FamilyId "\
            "   and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
            "   and DE.DiagnosisEntryId = R.DiagnosisEntryId "\
            "   and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
            "   and RD.QuantOutputId = QO.QuantOutputId "\
            "   and RD.RecommendationDefinitionId = R.RecommendationDefinitionId "\
            " order by FamilyName, FinalDiagnosisName"
        print SQL
        pds = system.db.runQuery(SQL)
        print "   fetched ", len(pds), " recommendation..."

        header = 'Family,FamilyPriority,FinalDiagnosis,FinalDiagnosisPriority,Status,'\
            'RecommendationStatus,TextRecommendation,QuantOutput, TagPath,Recommendation,'\
            'AutoRecommendation,ManualRecommendation,A,B,C,D,E,F,G,H,I'
#        print header
        system.file.writeFile(filename, header, False)

        for record in pds:
            textRecommendation=record['TextRecommendation']
            textRecommendation=string.replace(textRecommendation, '\n',' ')
            txt = "\n%s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s,0,0,0,0,0,0,0,0,0" % \
                (record['FamilyName'], str(record['FamilyPriority']), record['FinalDiagnosisName'], \
                str(record['FinalDiagnosisPriority']), record['Status'], record['RecommendationStatus'], \ 
                textRecommendation, record['QuantOutputName'], record['TagPath'],\
                str(record['Recommendation']), str(record['AutoRecommendation']), str(record['ManualRecommendation']))
#            print txt
            system.file.writeFile(filename, txt, True)
            
    #----------------------------------------------------
    # Fetch Quant Outputs
    def logQuantOutputs(application):
    
        SQL = "select QuantOutputName, TagPath, MostNegativeIncrement, MostPositiveIncrement, "\
            " MinimumIncrement, SetpointHighLimit, SetpointLowLimit, L.LookupName FeedbackMethod, "\
            " OutputLimitedStatus, OutputLimited, OutputPercent, IncrementalOutput, "\
            " FeedbackOutput, FeedbackOutputManual, FeedbackOutputConditioned, "\
            " DisplayedRecommendation, ManualOverride, QO.Active, CurrentSetpoint,  "\
            " FinalSetpoint, DisplayedRecommendation"\
            " from DtQuantOutput QO, lookup L, DtApplication A "\
            " where QO.FeedbackMethodId = L.LookupId "\
            " and L.LookupTypeCode = 'FeedbackMethod' "\
            " and A.ApplicationId = QO.ApplicationId "\
            " and A.ApplicationName = '%s' "\
            " order by QuantOutputName" % (application)

#        print SQL
        pds = system.db.runQuery(SQL)
        print "   fetched ", len(pds), " QuantOutputs..."

        header = "\nQuantOutput,TagPath,MostNegativeIncrement,MostPositiveIncrement,"\
            "MinimumIncrement,SetpointHighLimit,SetpointLowLimit,FeedbackMethod,"\
            "OutputLimitedStatus,OutputLimited,OutputPercent,IncrementalOutput,"\
            "FeedbackOutput,FeedbackOutputManual,FeedbackOutputConditioned,"\
            "DisplayedRecommendation,ManualOverride,Active,CurrentSetpoint,"\
            "FinalSetpoint,DisplayedRecommendation"
#        print header
        system.file.writeFile(filename, header, True)

        for record in pds:
            txt = "\n%s,%s,%f, %f,%f,%f, %f,%s,%s, %s,%s,%s, %s,%s, %s,%s, %s,%s,%s,%s,%s" % \
                (record['QuantOutputName'], record['TagPath'], record['MostNegativeIncrement'], \
                record['MostPositiveIncrement'], record['MinimumIncrement'], record['SetpointHighLimit'], \
                record['SetpointLowLimit'], record['FeedbackMethod'], record['OutputLimitedStatus'], \
                str(record['OutputLimited']), str(record['OutputPercent']), str(record['IncrementalOutput']), \
                str(record['FeedbackOutput']), str(record['FeedbackOutputManual']), \
                str(record['FeedbackOutputConditioned']), str(record['DisplayedRecommendation']), \
                str(record['ManualOverride']), str(record['Active']), str(record['CurrentSetpoint']), \
                str(record['FinalSetpoint']),str(record['DisplayedRecommendation']) )

#            print txt
            system.file.writeFile(filename, txt, True)

    #----------------------------------------------------
    # Fetch Diagnosis
    def logDiagnosis(post):
        import string
        SQL = "select FD.FinalDiagnosisName, DE.Status, DE.TextRecommendation, DE.RecommendationStatus, "\
            " DE.Multiplier, FD.Constant "\
            " from DtFinalDiagnosis FD, DtDiagnosisEntry DE "\
            " where FD.FinalDiagnosisId = DE.FinalDiagnosisId"\
            " order by FD.FinalDiagnosisName"

        pds = system.db.runQuery(SQL)
        print "   fetched ", len(pds), " Diagnosis..."

        header = "\nFinalDiagnosis,Status,TextRecommendation,RecommendationStatus, "\
            "Multiplier,Constant,A,B,C,D,E,F,G,H,I,J,K,L,M,N,O"
#        print header
        system.file.writeFile(filename, header, True)

        for record in pds:
            textRecommendation=record['TextRecommendation']
            textRecommendation=string.replace(textRecommendation, '\n',' ')
            txt = "\n%s,%s,%s,%s,%s,%s,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0" % \
                (record['FinalDiagnosisName'], record['Status'], textRecommendation, \
                record['RecommendationStatus'], \
                str(record['Multiplier']),str(record['Constant']))

#            print txt
            system.file.writeFile(filename, txt, True)
    #---------------

    
    print "...fetching results..."
    logRecommendations(post)
    logQuantOutputs(application)
    logDiagnosis(post)


def compareResults(outputFilename, goldFilename, table, row):
    print "...analyzing the results..."

    # Check if the Gold file exists
    if not(system.file.fileExists(goldFilename)):
        print "  The gold file <%s> does not exist!" % (goldFilename)
        print "Complete ........................... FAILED"
        table.setValue(row, 'result', 'Failed')
        return
    
    # Check if the output file exists
    if not(system.file.fileExists(outputFilename)):
        print "  The output file <%s> does not exist!" % (outputFilename)
        print "Complete ........................... FAILED"
        table.setValue(row, 'result', 'Failed')
        return

    # Check if the two files are identical
    result, explanation = project.test.diff.diff(outputFilename, goldFilename)
        
    if result:
        txt = 'Passed'
        print "Complete ........................... Passed"
    else:
        txt = 'Failed'
        print "Complete ........................... FAILED"
            
    # Try to update the status row of the table
    table.setValue(row, 'result', txt)

def scrubDatabase(applicationName):
    SQL = "select applicationId from DtApplication where ApplicationName = '%s'" % (applicationName)
    applicationId = system.db.runScalarQuery(SQL)
    
    if applicationId > 0:
        print "Deleting application with id: ", applicationId
        
        # Delete the diagnosis log
        SQL = "delete from DtFinalDiagnosisLog"
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtFinalDiagnosisLog..." % (rows)
        
        # Delete the text recommendations
        SQL = "delete from DtTextRecommendation"
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtTextRecommendation..." % (rows)
        
        # Delete recommendations
        SQL = "delete from DtRecommendation"
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtRecommendations..." % (rows)
        
        # Delete recommendationDefinitionss
        SQL = "select FinalDiagnosisId from DtFinalDiagnosis FD, DtFamily F "\
            " where F.ApplicationID = %i and FD.FamilyId = F.FamilyId " % applicationId
        pds = system.db.runQuery(SQL)
        cnt = 0
        for record in pds:
            finalDiagnosisId = record["FinalDiagnosisId"]
            SQL = "delete from DtRecommendationDefinition where FinalDiagnosisId = %i" % (finalDiagnosisId)
            rows=system.db.runUpdateQuery(SQL)
            cnt=cnt+rows
        print "   ...deleted %i rows from DtRecommendationDefinitions..." % (cnt)
    
        # Delete diagnosisEntries
        SQL = "delete from DtDiagnosisEntry"
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtDiagnosisEntry..." % (rows)
    
        # Delete QuantRecDefs
        SQL = "select QuantOutputId from DtQuantOutput where ApplicationID = %i" % applicationId
        pds = system.db.runQuery(SQL)
        cnt = 0
        for record in pds:
            quantOutputId = record["QuantOutputId"]
            SQL = "delete from DtRecommendationDefinition where QuantOutputId = %i" % (quantOutputId)
            rows = system.db.runUpdateQuery(SQL)
            cnt = cnt + rows
        print "   ...deleted %i rows from DtRecommendationDefinition" % (rows)
        
        # Delete QuantOutputs
        SQL = "delete from DtQuantOutput where ApplicationId = %i" % (applicationId)
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtQuantOutputs..." % (rows)
        
        # Delete FinalDiagnosis
        SQL = "select FamilyId from DtFamily where ApplicationID = %i" % applicationId
        pds = system.db.runQuery(SQL)
        cnt = 0
        for record in pds:
            familyId = record["FamilyId"]
            SQL = "delete from DtFinalDiagnosis where FamilyId = %i" % (familyId)
            rows = system.db.runUpdateQuery(SQL)
            cnt = cnt + rows
        print "   ...deleted %i rows from DtFinalDiagnosis" % (rows)
        
        # Delete Families
        SQL = "delete from DtFamily where ApplicationId = %i" % (applicationId)
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtFamily..." % (rows)
        
        # Delete the Application
        SQL = "delete from DtApplication where ApplicationId = %i" % (applicationId)
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from DtApplication..." % (rows)
        
        # Delete everything from the message Queues
        SQL = "delete from QueueDetail" 
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from QueueDetail..." % (rows)
    print "Done!" 
    
# Create everything required for the APP1 test
def insertApp1():
    application='TESTAPP1'
    logbook='Test Logbook'
    post = 'XO1TEST'
    unit = 'TESTUnit'
    logbookId = insertLogbook(logbook)
    postId = insertPost(post, logbookId)
    groupRampMethod='Simple'
    queueKey='TEST'
    app1Id=insertApplication(application, postId, unit, groupRampMethod, queueKey)
    return app1Id

def insertApp1Families(appId,T1Id,T2Id,T3Id,
    FD111calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_1_1',
    FD121calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_1',
    FD122calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_2',
    FD123calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_3',
    FD124calculationMethod='',
    FD125calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_5',
    FD126calculationMethod='xom.vistalon.diagToolkit.test.test.fd1_2_6',
    postProcessingCallback=None
    ):
    
    family = 'TESTFamily1_1'
    familyPriority=5.4
    familyId=insertFamily(family, appId, familyPriority)

    finalDiagnosis = 'TESTFD1_1_1'
    finalDiagnosisPriority=2.3
    textRecommendation = "Final Diagnosis 1.1.1"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD111calculationMethod, 
        textRecommendation, postProcessingCallback=postProcessingCallback)
    insertRecommendationDefinition(finalDiagnosisId, T1Id)

    family = 'TESTFamily1_2'
    familyPriority=7.6
    familyId=insertFamily(family, appId, familyPriority)
    
    finalDiagnosis = 'TESTFD1_2_1'
    finalDiagnosisPriority=4.5
    textRecommendation = "Final Diagnosis 1.2.1"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD121calculationMethod, 
        textRecommendation, postProcessingCallback=postProcessingCallback)
    insertRecommendationDefinition(finalDiagnosisId, T1Id)
    insertRecommendationDefinition(finalDiagnosisId, T2Id)

    finalDiagnosis = 'TESTFD1_2_2'
    finalDiagnosisPriority=4.5
    textRecommendation = "Final Diagnosis 1.2.2"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD122calculationMethod, 
        textRecommendation, postProcessingCallback=postProcessingCallback)
    insertRecommendationDefinition(finalDiagnosisId, T2Id)
    insertRecommendationDefinition(finalDiagnosisId, T3Id)
    
    finalDiagnosis = 'TESTFD1_2_3'
    finalDiagnosisPriority=9.8
    textRecommendation = "Final Diagnosis 1.2.3"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD123calculationMethod, 
        textRecommendation, postProcessingCallback=postProcessingCallback)
    insertRecommendationDefinition(finalDiagnosisId, T1Id)
    insertRecommendationDefinition(finalDiagnosisId, T2Id)
    insertRecommendationDefinition(finalDiagnosisId, T3Id)
    
    finalDiagnosis = 'TESTFD1_2_4'
    finalDiagnosisPriority=4.5
    textRecommendation = "Final Diagnosis 1.2.4 is CONstant"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD124calculationMethod, 
        textRecommendation, constant=1, postProcessingCallback=postProcessingCallback)
    
    finalDiagnosis = 'TESTFD1_2_5'
    finalDiagnosisPriority=10.2
    textRecommendation = "Final Diagnosis 1.2.5 is a low priority text recommendation.  "
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD125calculationMethod, 
        textRecommendation, postTextRecommendation=1, postProcessingCallback=postProcessingCallback)

    finalDiagnosis = 'TESTFD1_2_6'
    finalDiagnosisPriority=1.2
    textRecommendation = "Final Diagnosis 1.2.6 is a high priority text recommendation.  "
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD126calculationMethod, 
        textRecommendation, postTextRecommendation=1, postProcessingCallback=postProcessingCallback)

# Create everything required for the APP2 test
def insertApp2():
    application='TESTAPP2'
    logbook='Test Logbook'
    post = 'XO1TEST'
    unit = 'TESTUnit'
    logbookId = insertLogbook(logbook)
    postId = insertPost(post, logbookId)
    groupRampMethod='Simple'
    queueKey='TEST'
    app2Id=insertApplication(application, postId, unit, groupRampMethod, queueKey)
    return app2Id

def insertApp2Families(appId,T1Id,T2Id,
    FD211calculationMethod='xom.vistalon.diagToolkit.test.test.fd2_1_1'
    ):

    family = 'TESTFamily2_1'
    familyPriority=5.2
    familyId=insertFamily(family, appId, familyPriority)

    finalDiagnosis = 'TESTFD2_1_1'
    finalDiagnosisPriority=7.8
    textRecommendation = "Final Diagnosis 2.1.1"
    finalDiagnosisId=insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, FD211calculationMethod, textRecommendation)
    insertRecommendationDefinition(finalDiagnosisId, T1Id)

# Insert a Quant Output
def insertQuantOutput(appId, quantOutput, tagPath, tagValue, mostNegativeIncrement=-500.0, mostPositiveIncrement=500.0, minimumIncrement=0.0001,
        setpointHighLimit=1000.0, setpointLowLimit=-1000.0, feedbackMethod='Most Positive', incrementalOutput=True):
    feedbackMethodId=fetchFeedbackMethodId(feedbackMethod)
    SQL = "insert into DtQuantOutput (QuantOutputName, ApplicationId, TagPath, MostNegativeIncrement, MostPositiveIncrement, MinimumIncrement, "\
        "SetpointHighLimit, SetpointLowLimit, FeedbackMethodId, IncrementalOutput) values "\
        "('%s', %i, '%s', %f, %f, %f, %f, %f, %i, '%s')" % \
        (quantOutput, appId, tagPath, mostNegativeIncrement, mostPositiveIncrement, minimumIncrement,
        setpointHighLimit, setpointLowLimit, feedbackMethodId, incrementalOutput)
    id = system.db.runUpdateQuery(SQL, getKey=True)
    print "Writing ", tagValue, " to ", tagPath
    system.tag.write(tagPath, tagValue, 60)
    return id

# Define a Logbook
def insertLogbook(logbookName):
    SQL = "select logbookId from tkLogbook where LogbookName = '%s'" % (logbookName)
    logbookId = system.db.runScalarQuery(SQL)
    
    if logbookId < 0:
        SQL = "insert into TkLogbook (LogbookName) values ('%s')" % (logbookName)
        logbookId = system.db.runUpdateQuery(SQL, getKey=True)
    return logbookId

# Define a post
def insertPost(post, logbookId):
    SQL = "select postId from tkPost where Post = '%s'" % (post)
    postId = system.db.runScalarQuery(SQL)
    
    if postId < 0:
        SQL = "insert into TkPost (Post, LogbookId) values ('%s', %i)" % (post, logbookId)
        postId = system.db.runUpdateQuery(SQL, getKey=True)
    return postId

# Define a unit
def insertUnit(unitName, postId):
    SQL = "select unitId from TkUnit where UnitName = '%s'" % (unitName)
    unitId = system.db.runScalarQuery(SQL)
    
    if unitId < 0:
        SQL = "insert into TkUnit (UnitName, PostId) values ('%s', %s)" % (unitName, str(postId))
        unitId = system.db.runUpdateQuery(SQL, getKey=True)
    return unitId

# Fetch the Group Ramp Method for the unit
def fetchGroupRampMethodId(groupRampMethod):
    SQL = "select LookupId from Lookup where LookupTypeCode = 'GroupRampMethod' and LookupName = '%s'" % (groupRampMethod)
    groupRampMethodId = system.db.runScalarQuery(SQL)
    return groupRampMethodId

def fetchFeedbackMethodId(feedbackMethod):
    SQL = "select LookupId from Lookup where LookupTypeCode = 'FeedbackMethod' and LookupName = '%s'" % (feedbackMethod)
    feedbackMethodId = system.db.runScalarQuery(SQL)
    return feedbackMethodId

def fetchFinalDiagnosisId(finalDiagnosisName):
    SQL = "select FinalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName = '%s'" % (finalDiagnosisName)
    finalDiagnosisId = system.db.runScalarQuery(SQL)
    return finalDiagnosisId
        
# Fetch the Queue id for the key
def fetchQueueId(queueKey):
    SQL = "select QueueId from QueueMaster where QueueKey = '%s'" % (queueKey)
    queueId = system.db.runScalarQuery(SQL)
    return queueId
    
# Fetch the Post id for the post
def fetchPostId(post):
    SQL = "select PostId from TkPost where Post = '%s'" % (post)
    postId = system.db.runScalarQuery(SQL)
    return postId
    
# Define an application
def insertApplication(application, postId, unit, groupRampMethod, queueKey):
    print "The group ramp method is: ", groupRampMethod
    unitId=insertUnit(unit, postId)
    groupRampMethodId=fetchGroupRampMethodId(groupRampMethod)
    queueId=fetchQueueId(queueKey)
    SQL = "insert into DtApplication (applicationName, UnitId, GroupRampMethodId, IncludeInMainMenu, MessageQueueId)"\
        " values ('%s', %s, %s, 1, %s)" % (application, str(unitId), str(groupRampMethodId), str(queueId))
    applicationId = system.db.runUpdateQuery(SQL, getKey=True)
    return applicationId

# Create all of the families in this Application
def insertFamily(familyName, applicationId, familyPriority):
    SQL = "insert into DtFamily (FamilyName, ApplicationId, FamilyPriority) values ('%s', %i, %f)" % (familyName, applicationId, familyPriority)
    familyId = system.db.runUpdateQuery(SQL, getKey=True)
    return familyId

# Create a final diagnosis
def insertFinalDiagnosis(finalDiagnosis, familyId, finalDiagnosisPriority, calculationMethod='', 
    textRecommendation='', constant=0, postTextRecommendation=0, postProcessingCallback=None, 
    refreshRate=300):

#    SQL = "insert into DtFinalDiagnosis (FinalDiagnosisName, FamilyId, FinalDiagnosisPriority, CalculationMethod, "\
#        " TextRecommendation, Constant, PostTextRecommendation, " \
#        " PostProcessingCallback, RefreshRate, Active, State) "\
#        " values ('%s', %i, %f, '%s', '%s', %i, %i, '%s', %i, 0, 0)"\
#        % (finalDiagnosis, familyId, finalDiagnosisPriority, calculationMethod, textRecommendation, constant, 
#        postTextRecommendation, postProcessingCallback, refreshRate)
#    finalDiagnosisId = system.db.runUpdateQuery(SQL, getKey=True)
    
    SQL = "insert into DtFinalDiagnosis (FinalDiagnosisName, FamilyId, FinalDiagnosisPriority, CalculationMethod, "\
            " TextRecommendation, Constant, PostTextRecommendation, " \
            " PostProcessingCallback, RefreshRate, Active, State) "\
            " values (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)"
            
    finalDiagnosisId = system.db.runPrepUpdate(SQL, [finalDiagnosis, familyId, finalDiagnosisPriority, calculationMethod, 
        textRecommendation, constant, postTextRecommendation, postProcessingCallback, refreshRate], getKey=True)
        
    return finalDiagnosisId
    
# Create the recommendationDefinitions
def insertRecommendationDefinition(finalDiagnosisId, quantOutputId):
    SQL = "insert into DtRecommendationDefinition (FinalDiagnosisId, QuantOutputId) "\
        " values (%i, %i)" % (finalDiagnosisId, quantOutputId)
    system.db.runUpdateQuery(SQL)