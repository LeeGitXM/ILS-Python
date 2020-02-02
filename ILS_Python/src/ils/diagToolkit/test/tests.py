'''
Created on Sep 13, 2016

@author: ils
'''

import system, time
from ils.diagToolkit.test.common import insertApp1, insertApp2, insertQuantOutput, insertApp1Families, insertApp2Families, initLog
from ils.diagToolkit.finalDiagnosisClient import postDiagnosisEntry
logger=system.util.getLogger("ils.test")

project = "XOM"
T1TagName='DiagnosticToolkit/Outputs/T1'
T2TagName='DiagnosticToolkit/Outputs/T2'
T3TagName='DiagnosticToolkit/Outputs/T3'
TC100_TagName='DiagnosticToolkit/Outputs/TC100'
TC101_TagName='DiagnosticToolkit/Outputs/TC101'
TC102_TagName='DiagnosticToolkit/Outputs/TC102'
T100_TagName='DiagnosticToolkit/Outputs/T100'
T101_TagName='DiagnosticToolkit/Outputs/T101'
DELAY_BETWEEN_PROBLEMS=16

def stub1(arg1):
    print "In stub1 with ", arg1

def stub2(arg1):
    print "In stub2 with ", arg1

def test00():
    logger.tracef("Starting %s.test00()", __name__)
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 09.6789123456)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5432198765)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3456789123)
    insertApp1Families(appId,T1Id,T2Id,T3Id,postProcessingCallback='ils.diagToolkit.test.calculationMethods.postDownloadSpecialActions')
    
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  19.88)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 123.15)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName,    2.31)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName,   36.23)
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName,   15.2)
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1a')
    return applicationName


def test01():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 09.6789123456)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5432198765)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3456789123)
    insertApp1Families(appId,T1Id,T2Id,T3Id,postProcessingCallback='ils.diagToolkit.test.calculationMethods.postDownloadSpecialActions')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName

def test03e():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3e')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName

def test11c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, minimumIncrement=40.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1e')
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName

def test12aa():
    '''
    This uses the same calculation method as the rest of the 
    '''
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Implement")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=1000.0, mostNegativeIncrement=-1000, setpointHighLimit=1000, setpointLowLimit=-1000)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName
    
def test12a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Implement")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, mostPositiveIncrement=25.0)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName
    
def test12b():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Advise")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, mostPositiveIncrement=25.0)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName
    
def test12c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, mostPositiveIncrement=25.0)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName
    
def test12d():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Implement")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=5.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3a', insertExtraRecDef=True)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName

def test12e():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Implement")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName

def test12f():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")    
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")    
    return applicationName

def test14b1():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD111calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_1_1X')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_1', 'TESTFD1_1_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")    
    return applicationName

# This tests error handling for a non existent calculation method.  Specifically it tests that the Final diagnosis
# does not remain active and therefore block subsequent lower priority diagnosis from becoming active. 
def test14b2():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/T3", 20.3)
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1X')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName

# Test divide by zero in the calculation method
def test14b3():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/T3", 20.3)
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3f')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName


def test14c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3b')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName

def test14d():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,
                       FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1b',
                       FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3b',
                       FD121Priority=5.0, FD123Priority=5.0)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName

'''
The purpose of this test s to test residual recommendations that are not cleaned up when a FD is cleared or a higher priority
FD comes in.
'''
def test14e():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/T3", 20.3)
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    return applicationName
    
def test15a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3b')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_4', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName
    
def test15b():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3b')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_4', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName
    
def test15c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3b')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_4', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName
    
def test15d():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3c')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName
    
def test15e():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3d')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName
    
def test15f():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/T3", 20.3)
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3c')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName
    
def test15g():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/T3", 20.3)
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3d')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName

def test15h():
    '''
    See ticket #597 which raises questions about this issue.
    '''
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/zeroChangeThreshold", 0.01)
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, minimumIncrement=0.5)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, minimumIncrement=0.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, minimumIncrement=0.5)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3h')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName

def test15i():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3i')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName

def test16a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    
    ''' Write the PV and SP which will be used to calculate the error '''
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/Lab_Data/value", 17.345)
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/T1_Target", 25.0)
    
    applicationName='TESTAPP2'
    appId=insertApp2()  
    
    system.tag.write("[XOM]" + TC100_TagName + "/sp/value", 35.63)
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63)
    
    system.tag.write("[XOM]" + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89)
    
    system.tag.write("[XOM]" + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91)
    
    system.tag.write("[XOM]" + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81)
    
    system.tag.write("[XOM]" + TC102_TagName + "/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/mode/value", "AUTO")
    system.tag.write("[XOM]" + TC102_TagName + "/sp/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/targetValue", 0.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampTime", 10.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 10.5)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1a')
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily2_1', 'TESTFD2_1_1', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName

def test16b():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/Lab_Data/value", 17.345)
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/T1_Target", 25.0)

    applicationName='TESTAPP2'
    appId=insertApp2()  
    
    system.tag.write("[XOM]" + TC100_TagName + "/sp/value", 35.63)
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63)
    
    system.tag.write("[XOM]" + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89)
    
    system.tag.write("[XOM]" + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91)
    
    system.tag.write("[XOM]" + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81)
    
    system.tag.write("[XOM]" + TC102_TagName + "/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/mode/value", "AUTO")
    system.tag.write("[XOM]" + TC102_TagName + "/sp/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/targetValue", 0.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampTime", 10.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1b')
    
    print "Setting the manual move for the final diagnosis in the database..."
    manualMove = 2.0
    finalDiagnosisId = system.db.runScalarQuery("select finalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName = 'TESTFD2_1_1'  ")
    SQL = "update DtFinalDiagnosis set ManualMove = %s, ManualMoveAllowed = 1 where FinalDiagnosisId = %s" % (str(manualMove), str(finalDiagnosisId))
    print SQL
    system.db.runUpdateQuery(SQL)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily2_1', 'TESTFD2_1_1', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName

def test16c():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/Lab_Data/value", 20.0)
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/T1_Target", 25.0)

    applicationName='TESTAPP2'
    appId=insertApp2()  
    
    system.tag.write("[XOM]" + TC100_TagName + "/sp/value", 35.63)
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63)
    
    system.tag.write("[XOM]" + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89)
    
    system.tag.write("[XOM]" + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91)
    
    system.tag.write("[XOM]" + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81)
    
    system.tag.write("[XOM]" + TC102_TagName + "/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/mode/value", "AUTO")
    system.tag.write("[XOM]" + TC102_TagName + "/sp/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/targetValue", 0.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampTime", 10.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1c')
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily2_1', 'TESTFD2_1_1', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName

def test16d():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/Lab_Data/value", 20.0)
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/T1_Target", 25.0)

    applicationName='TESTAPP2'
    appId=insertApp2()  
    
    system.tag.write("[XOM]" + TC100_TagName + "/sp/value", 35.63)
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63)
    
    system.tag.write("[XOM]" + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89)
    
    system.tag.write("[XOM]" + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91)
    
    system.tag.write("[XOM]" + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81)
    
    system.tag.write("[XOM]" + TC102_TagName + "/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/mode/value", "AUTO")
    system.tag.write("[XOM]" + TC102_TagName + "/sp/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/targetValue", 0.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampTime", 10.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1c')
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily2_1', 'TESTFD2_1_1', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName

def test16e():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/Lab_Data/value", 20.0)
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/T1_Target", 25.0)

    applicationName='TESTAPP2'
    appId=insertApp2()  
    
    system.tag.write("[XOM]" + TC100_TagName + "/sp/value", 35.63)
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63)
    
    system.tag.write("[XOM]" + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89)
    
    system.tag.write("[XOM]" + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91)
    
    system.tag.write("[XOM]" + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81)
    
    system.tag.write("[XOM]" + TC102_TagName + "/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/mode/value", "AUTO")
    system.tag.write("[XOM]" + TC102_TagName + "/sp/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/targetValue", 0.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampTime", 10.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1d')
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily2_1', 'TESTFD2_1_1', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName

def test16f():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/Lab_Data/value", 20.0)
    system.tag.write("[XOM]DiagnosticToolkit/Inputs/T1_Target", 25.0)

    applicationName='TESTAPP2'
    appId=insertApp2()  
    
    system.tag.write("[XOM]" + TC100_TagName + "/sp/value", 35.63)
    system.tag.write("[XOM]" + TC100_TagName + "/mode/value", "AUTO")
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63)
    
    system.tag.write("[XOM]" + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89)
    
    system.tag.write("[XOM]" + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91)
    
    system.tag.write("[XOM]" + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81)
    
    system.tag.write("[XOM]" + TC102_TagName + "/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/mode/value", "AUTO")
    system.tag.write("[XOM]" + TC102_TagName + "/sp/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/targetValue", 0.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampTime", 10.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1e')
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily2_1', 'TESTFD2_1_1', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName

def test16g():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, feedbackMethod='Simple Sum')
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, feedbackMethod='Simple Sum')
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, feedbackMethod='Simple Sum')
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD122Priority=3.4, FD123Priority=3.4, FD122calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_2a', FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3g')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_3', 'FD_UUID','DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_1', 'FD_UUID','DIAGRAM_UUID', provider="XOM")

    applicationName='TESTAPP2'
    appId=insertApp2()
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  19.88)
    system.tag.write("[XOM]" + TC100_TagName + "/sp/value", 19.88)
    
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 123.15)
    system.tag.write("[XOM]" + TC101_TagName + "/sp/value", 123.15)
    
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName,    2.31)
    system.tag.write("[XOM]" + T100_TagName + "/value", 2.31)
    
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName,   36.23)
    system.tag.write("[XOM]" + T101_TagName + "/value", 36.23)
    
    system.tag.write("[XOM]" + TC102_TagName + "/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/mode/value", "AUTO")
    system.tag.write("[XOM]" + TC102_TagName + "/sp/value", 20.5)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/targetValue", 0.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampTime", 10.0)
    system.tag.write("[XOM]" + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1a')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily2_1', 'TESTFD2_1_1', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    
    return applicationName

# Test a single text recommendation
def test18a():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id,postProcessingCallback='ils.diagToolkit.test.calculationMethods.postDownloadSpecialActions')
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_5', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_5', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName

# Test a low priority text FD followed by a high priority numeric FD
def test18d():
    system.tag.write("[XOM]Configuration/DiagnosticToolkit/vectorClampMode", "Disabled")
    applicationName='TESTAPP1'
    appId=insertApp1()
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3)
    insertApp1Families(appId,T1Id,T2Id,T3Id)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_5', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_2', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
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
    postDiagnosisEntry(project, applicationName, 'TESTFamily1_2', 'TESTFD1_2_6', 'FD_UUID', 'DIAGRAM_UUID', provider="XOM")
    return applicationName
