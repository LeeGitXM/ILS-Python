'''
Created on Sep 13, 2016

@author: ils
'''

import system, time
from ils.diagToolkit.test.common import insertApp1, insertApp2, insertQuantOutput, insertApp1Families, insertApp2Families, initLog
from ils.diagToolkit.finalDiagnosisClient import postDiagnosisEntry
logger=system.util.getLogger("ils.test")

project = "XOM"
T1TagName='Sandbox/Diagnostic/T1'
T2TagName='Sandbox/Diagnostic/T2'
T3TagName='Sandbox/Diagnostic/T3'
TC100TagName='Sandbox/Diagnostic/TC100/sp/value'
TC101TagName='Sandbox/Diagnostic/TC101/sp/value'

def foo():
    print "Hello foo"

def test00():
#    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
#    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')    
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')    
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID')    
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_4', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_4', 'FD_UUID', 'DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_4', 'FD_UUID', 'DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID', 'DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID', 'DIAGRAM_UUID')
    time.sleep(2.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName

def test16a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP2'
    appId=insertApp2()
    T1Id=insertQuantOutput(appId, 'TEST_Q0_TC100', TC100TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TEST_Q1_TC101', TC101TagName, 23.5)
    insertApp2Families(appId,T1Id,T2Id,FD211calculationMethod='xom.vistalon.diagToolkit.test.test.fd2_1_1')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily2_1', 'TESTFD2_1_1', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID')

    applicationName='TESTAPP2'
    appId=insertApp2()
    T1Id=insertQuantOutput(appId, 'TEST_Q0_TC100', TC100TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TEST_Q1_TC101', TC101TagName, 23.5)
    insertApp2Families(appId,T1Id,T2Id,FD211calculationMethod='xom.vistalon.diagToolkit.test.test.fd2_1_1')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily2_1', 'TESTFD2_1_1', 'FD_UUID', 'DIAGRAM_UUID')
    
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID')
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_5', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID')
    time.sleep(10.0)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID')
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID')
    return applicationName
