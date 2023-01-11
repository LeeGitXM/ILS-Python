'''
Created on Sep 13, 2016

@author: ils

This is used exclusively by the SQA Final Test and should NOT be used (or at least
modified for any other purpose).
'''

import system, time
from ils.diagToolkit.test.common import insertApp1, insertApp2, insertQuantOutput, insertApp1Families, insertApp2Families, \
    initLog, updateFinalDiagnosisTextRecommendation, writeTag, disableVectorClampMode, implementVectorClampMode, adviseVectorClampMode
from ils.diagToolkit.finalDiagnosisClient import postDiagnosisEntry
from ils.log import getLogger
log = getLogger(__name__)

project = "XOM_Dev"
providerName = "Dev"
provider = "[" + providerName + "]"

T1TagName = 'DiagnosticToolkit/Outputs/T1'
T2TagName = 'DiagnosticToolkit/Outputs/T2'
T3TagName = 'DiagnosticToolkit/Outputs/T3'

TC100_TagName='DiagnosticToolkit/Outputs/TC100'
TC101_TagName='DiagnosticToolkit/Outputs/TC101'
TC102_TagName='DiagnosticToolkit/Outputs/TC102'
TC103_TagName='DiagnosticToolkit/Outputs/TC103'
TC104_TagName='DiagnosticToolkit/Outputs/TC104'
TC105_TagName='DiagnosticToolkit/Outputs/TC105'

T100_TagName='DiagnosticToolkit/Outputs/T100'
T101_TagName='DiagnosticToolkit/Outputs/T101'
DELAY_BETWEEN_PROBLEMS=16

def stub1(arg1):
    print "In stub1 with ", arg1

def stub2(arg1):
    print "In stub2 with ", arg1

def test00(db):
    log.tracef("Starting %s.test00()", __name__)
    disableVectorClampMode(provider)
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 09.6789123456, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5432198765, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3456789123, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,postProcessingCallback='ils.diagToolkit.test.calculationMethods.postDownloadSpecialActions', db=db)
    
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  19.88, db=db)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 123.15, db=db)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName,    2.31, db=db)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName,   36.23, db=db)
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName,   15.2, db=db)
    Q26_id=insertQuantOutput(appId, 'TEST_Q26', TC105_TagName,   10.0, db=db)
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, Q26_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1a', db=db)
    return applicationName

def test01(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_1'
    diagramName = 'FT_Diagram1_1'
    fDName = 'FT_FD1_1_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 09.6789123456, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5432198765, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3456789123, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,postProcessingCallback='ils.diagToolkit.test.calculationMethods.postDownloadSpecialActions', db=db)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test02(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'

    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 09.6789123456, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5432198765, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3456789123, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test03a(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    initLog(db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test03b(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'

    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    initLog(db)
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test03c(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    initLog(db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    familyName = 'FT_Family1_1'
    diagramName = 'FT_Diagram1_1'
    fDName = 'FT_FD1_1_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test03d(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'

    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    initLog(db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    
    familyName = 'FT_Family1_1'
    diagramName = 'FT_Diagram1_1'
    fDName = 'FT_FD1_1_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test03e(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_3'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3e', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test04(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    
    fDName = 'FT_FD1_2_2'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
        
def test05(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, feedbackMethod='Most Negative', db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, feedbackMethod='Most Negative', db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, feedbackMethod='Most Negative', db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    
    fDName = 'FT_FD1_2_2'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test06(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, feedbackMethod='Average', db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, feedbackMethod='Average', db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, feedbackMethod='Average', db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    
    fDName = 'FT_FD1_2_2'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
            
def test07(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, feedbackMethod='Simple Sum', db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, feedbackMethod='Simple Sum', db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, feedbackMethod='Simple Sum', db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_2'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test08a(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=True, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=True, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=True, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test08b(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=False, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test08c(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=False, mostPositiveIncrement=10.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test08d(db):
    implementVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=False, mostPositiveIncrement=10.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test08e(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=False, setpointHighLimit=15.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test08f(db):
    implementVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=False, setpointHighLimit=15.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test11a(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_1'
    diagramName = 'FT_Diagram1_1'
    fDName = 'FT_FD1_1_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, minimumIncrement=20.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db, trapInsignificantRecommendations=1)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test11a2(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_1'
    diagramName = 'FT_Diagram1_1'
    fDName = 'FT_FD1_1_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, minimumIncrement=20.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db, trapInsignificantRecommendations=0)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test11b(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, minimumIncrement=40.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test11c(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, minimumIncrement=40.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1e', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test12aa(db):
    '''
    This uses the same calculation method as the rest of the 
    '''
    implementVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=1000.0, mostNegativeIncrement=-1000, setpointHighLimit=1000, setpointLowLimit=-1000, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test12a(db):
    implementVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, mostPositiveIncrement=25.0, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test12b(db):
    adviseVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, mostPositiveIncrement=25.0, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test12c(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, mostPositiveIncrement=25.0, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test12d(db):
    implementVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_3'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=5.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3a', insertExtraRecDef=True, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test12e(db):
    implementVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test12f(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, mostPositiveIncrement=2.0, mostNegativeIncrement=-2.0, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1a', insertExtraRecDef=True, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test13a(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_1'
    diagramName = 'FT_Diagram1_1'
    fDName = 'FT_FD1_1_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=False, setpointHighLimit=100.0, setpointLowLimit=50.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test13b(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_1'
    diagramName = 'FT_Diagram1_1'
    fDName = 'FT_FD1_1_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)    
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Test incremental recommendations when the setpoint is way outside the limits.
def test13c(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_1'
    diagramName = 'FT_Diagram1_1'
    fDName = 'FT_FD1_1_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)    
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Test a bad output wherte the FD only writes to 1
def test14a1(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_1'
    diagramName = 'FT_Diagram1_1'
    fDName = 'FT_FD1_1_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', 'Sandbox/T99', 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Test a bad output where the FD writes to 2 - I think if we can't write to all of them we don't want to write to any.
def test14a2(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', 'Sandbox/T99', 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test14b1(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_1'
    diagramName = 'FT_Diagram1_1'
    fDName = 'FT_FD1_1_1'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD111calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_1_1X', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# This tests error handling for a non existent calculation method.  Specifically it tests that the Final diagnosis
# does not remain active and therefore block subsequent lower priority diagnosis from becoming active. 
def test14b2(db):
    disableVectorClampMode(provider)
    writeTag(provider + "DiagnosticToolkit/Inputs/T3", 20.3)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1X', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Test divide by zero in the calculation method
def test14b3(db):
    disableVectorClampMode(provider)
    writeTag(provider + "DiagnosticToolkit/Inputs/T3", 20.3)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 60.6, incrementalOutput=True, setpointHighLimit=100.0, setpointLowLimit=50.0, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=False, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=False, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3f', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Test case insesitive recommendations
def test14b4(db):
    disableVectorClampMode(provider)
    writeTag(provider + "DiagnosticToolkit/Inputs/T3", 20.3)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'testq1', T1TagName, 60.6, incrementalOutput=True, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, incrementalOutput=True, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, incrementalOutput=True, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3j', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test14c(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_3'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3b', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test14d(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,
                       FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_1b',
                       FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3b',
                       FD121Priority=5.0, FD123Priority=5.0, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

'''
The purpose of this test is to test residual recommendations that are not cleaned up when a FD is cleared or a higher priority
FD comes in.
'''
def test14e(db):
    disableVectorClampMode(provider)
    writeTag(provider + "DiagnosticToolkit/Inputs/T3", 20.3)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test15a(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_4'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3b', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test15b(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3b', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_4'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test15c(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3b', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_4'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test15d(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_3'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3c', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test15e(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_3'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3d', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test15f(db):
    disableVectorClampMode(provider)
    writeTag(provider + "DiagnosticToolkit/Inputs/T3", 20.3)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3c', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName
    
def test15g(db):
    disableVectorClampMode(provider)
    writeTag(provider + "DiagnosticToolkit/Inputs/T3", 20.3)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'

    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD121calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3d', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_1'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test15h(db):
    '''
    See ticket #597 which raises questions about this issue.
    '''
    disableVectorClampMode(provider)
    writeTag(provider + "Configuration/DiagnosticToolkit/zeroChangeThreshold", 0.01)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_3'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, minimumIncrement=0.5, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, minimumIncrement=0.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, minimumIncrement=0.5, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3h', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test15i(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_3'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3i', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test16a(db):
    print "-----------------------------------"
    print "Start test16a()"
    disableVectorClampMode(provider)
    
    ''' Write the PV and SP which will be used to calculate the error '''
    writeTag(provider + "DiagnosticToolkit/Inputs/Lab_Data/value", 17.345)
    writeTag(provider + "DiagnosticToolkit/Inputs/T1_Target", 25.0)
    
    applicationName='FINAL_TEST_2'
    familyName = 'FT_Family2_1'
    diagramName = 'FT_Diagram2_1'
    fDName = 'FT_FD2_1_1'
    appId=insertApp2(db)  
    
    writeTag(provider + TC100_TagName + "/sp/value", 35.63)
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63, db=db)
    
    writeTag(provider + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89, db=db)
    
    writeTag(provider + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91, db=db)
    
    writeTag(provider + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81, db=db)
    
    writeTag(provider + TC102_TagName + "/value", 20.5)
    writeTag(provider + TC102_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC102_TagName + "/sp/value", 20.5)
    writeTag(provider + TC102_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC102_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 10.5, db=db)
    
    writeTag(provider + TC105_TagName + "/value", 20.0)
    writeTag(provider + TC105_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC105_TagName + "/sp/value", 20.0)
    writeTag(provider + TC105_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC105_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC105_TagName + "/sp/rampState", "")
    Q26_id=insertQuantOutput(appId, 'TEST_Q26', TC105_TagName, 10.0, db=db)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, Q26_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1a', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test16b(db):
    disableVectorClampMode(provider)
    writeTag(provider + "DiagnosticToolkit/Inputs/Lab_Data/value", 17.345)
    writeTag(provider + "DiagnosticToolkit/Inputs/T1_Target", 25.0)

    applicationName='FINAL_TEST_2'
    familyName = 'FT_Family2_1'
    diagramName = 'FT_Diagram2_1'
    fDName = 'FT_FD2_1_1'
    appId=insertApp2(db)  
    
    writeTag(provider + TC100_TagName + "/sp/value", 35.63)
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63, db=db)
    
    writeTag(provider + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89, db=db)
    
    writeTag(provider + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91, db=db)
    
    writeTag(provider + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81, db=db)
    
    writeTag(provider + TC102_TagName + "/value", 20.5)
    writeTag(provider + TC102_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC102_TagName + "/sp/value", 20.5)
    writeTag(provider + TC102_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC102_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5, db=db)
    
    writeTag(provider + TC105_TagName + "/value", 20.0)
    writeTag(provider + TC105_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC105_TagName + "/sp/value", 20.0)
    writeTag(provider + TC105_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC105_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC105_TagName + "/sp/rampState", "")
    Q26_id=insertQuantOutput(appId, 'TEST_Q26', TC105_TagName, 10.0, db=db)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, Q26_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1b', db=db)
    
    print "Setting the manual move for the final diagnosis in the database..."
    manualMove = 2.0
    finalDiagnosisId = system.db.runScalarQuery("select finalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName = 'FT_FD2_1_1'  ", database=db)
    SQL = "update DtFinalDiagnosis set ManualMove = %s, ManualMoveAllowed = 1 where FinalDiagnosisId = %s" % (str(manualMove), str(finalDiagnosisId))
    print SQL
    system.db.runUpdateQuery(SQL, database=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test16c(db):
    disableVectorClampMode(provider)
    writeTag(provider + "DiagnosticToolkit/Inputs/Lab_Data/value", 20.0)
    writeTag(provider + "DiagnosticToolkit/Inputs/T1_Target", 25.0)

    applicationName='FINAL_TEST_2'
    familyName = 'FT_Family2_1'
    diagramName = 'FT_Diagram2_1'
    fDName = 'FT_FD2_1_1'
    appId=insertApp2(db)  
    
    writeTag(provider + TC100_TagName + "/sp/value", 35.63)
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63, db=db)
    
    writeTag(provider + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89, db=db)
    
    writeTag(provider + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91, db=db)
    
    writeTag(provider + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81, db=db)
    
    writeTag(provider + TC102_TagName + "/value", 20.5)
    writeTag(provider + TC102_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC102_TagName + "/sp/value", 20.5)
    writeTag(provider + TC102_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC102_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5, db=db)
    
    writeTag(provider + TC105_TagName + "/value", 20.0)
    writeTag(provider + TC105_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC105_TagName + "/sp/value", 20.0)
    writeTag(provider + TC105_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC105_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC105_TagName + "/sp/rampState", "")
    Q26_id=insertQuantOutput(appId, 'TEST_Q26', TC105_TagName, 10.0, db=db)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, Q26_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1b', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    print "...posting a diagnosis entry..."
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    print "...done setting up the test..."
    return applicationName

def test16d(db):
    disableVectorClampMode(provider)
    writeTag(provider + "DiagnosticToolkit/Inputs/Lab_Data/value", 20.0)
    writeTag(provider + "DiagnosticToolkit/Inputs/T1_Target", 25.0)

    applicationName='FINAL_TEST_2'
    familyName = 'FT_Family2_1'
    diagramName = 'FT_Diagram2_1'
    fDName = 'FT_FD2_1_1'
    appId=insertApp2(db)  
    
    writeTag(provider + TC100_TagName + "/sp/value", 35.63)
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63, db=db)
    
    writeTag(provider + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89, db=db)
    
    writeTag(provider + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91, db=db)
    
    writeTag(provider + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81, db=db)
    
    writeTag(provider + TC102_TagName + "/value", 20.5)
    writeTag(provider + TC102_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC102_TagName + "/sp/value", 20.5)
    writeTag(provider + TC102_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC102_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5, db=db)
    
    writeTag(provider + TC105_TagName + "/value", 20.0)
    writeTag(provider + TC105_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC105_TagName + "/sp/value", 20.0)
    writeTag(provider + TC105_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC105_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC105_TagName + "/sp/rampState", "")
    Q26_id=insertQuantOutput(appId, 'TEST_Q26', TC105_TagName, 10.0, db=db)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, Q26_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1c', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    print "...posting a diagnosis entry..."
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName)
    print "...done setting up the test..."
    return applicationName

def test16e(db):
    disableVectorClampMode(provider)
    writeTag(provider + "DiagnosticToolkit/Inputs/Lab_Data/value", 20.0)
    writeTag(provider + "DiagnosticToolkit/Inputs/T1_Target", 25.0)

    applicationName='FINAL_TEST_2'
    familyName = 'FT_Family2_1'
    diagramName = 'FT_Diagram2_1'
    fDName = 'FT_FD2_1_1'
    appId=insertApp2(db)  
    
    writeTag(provider + TC100_TagName + "/sp/value", 35.63)
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63, db=db)
    
    writeTag(provider + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89, db=db)
    
    writeTag(provider + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91, db=db)
    
    writeTag(provider + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81, db=db)
    
    writeTag(provider + TC102_TagName + "/value", 20.5)
    writeTag(provider + TC102_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC102_TagName + "/sp/value", 20.5)
    writeTag(provider + TC102_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC102_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5, db=db)
    
    writeTag(provider + TC105_TagName + "/value", 20.0)
    writeTag(provider + TC105_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC105_TagName + "/sp/value", 20.0)
    writeTag(provider + TC105_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC105_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC105_TagName + "/sp/rampState", "")
    Q26_id=insertQuantOutput(appId, 'TEST_Q26', TC105_TagName, 10.0, db=db)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, Q26_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1d', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    print "...posting a diagnosis entry..."
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    print "...done setting up the test..."
    return applicationName

def test16f(db):
    disableVectorClampMode(provider)
    writeTag(provider + "DiagnosticToolkit/Inputs/Lab_Data/value", 20.0)
    writeTag(provider + "DiagnosticToolkit/Inputs/T1_Target", 25.0)

    applicationName='FINAL_TEST_2'
    familyName = 'FT_Family2_1'
    diagramName = 'FT_Diagram2_1'
    fDName = 'FT_FD2_1_1'
    appId=insertApp2(db)  
    
    writeTag(provider + TC100_TagName + "/sp/value", 35.63)
    writeTag(provider + TC100_TagName + "/mode/value", "AUTO")
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  35.63, db=db)
    
    writeTag(provider + TC101_TagName + "/sp/value", 526.89)
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 526.89, db=db)
    
    writeTag(provider + T100_TagName + "/value", 27.91)
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName, 27.91, db=db)
    
    writeTag(provider + T101_TagName + "/value", 113.81)
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName, 113.81, db=db)
    
    writeTag(provider + TC102_TagName + "/value", 20.5)
    writeTag(provider + TC102_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC102_TagName + "/sp/value", 20.5)
    writeTag(provider + TC102_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC102_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5, db=db)
    
    writeTag(provider + TC105_TagName + "/value", 20.0)
    writeTag(provider + TC105_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC105_TagName + "/sp/value", 20.0)
    writeTag(provider + TC105_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC105_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC105_TagName + "/sp/rampState", "")
    Q26_id=insertQuantOutput(appId, 'TEST_Q26', TC105_TagName, 10.0, db=db)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, Q26_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1e', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    print "...posting a diagnosis entry..."
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    print "...done setting up the test..."
    return applicationName

def test16g(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db, groupRampMethod='Longest')
    
    writeTag(provider + TC101_TagName + "/sp/value", 9.6)
    writeTag(provider + TC101_TagName + "/mode/value", "AUTO")
    T1Id=insertQuantOutput(appId, 'TESTQ1', TC101_TagName, 9.6, feedbackMethod='Simple Sum', db=db)
    
    writeTag(provider + TC103_TagName + "/sp/value", 23.5)
    writeTag(provider + TC103_TagName + "/mode/value", "AUTO")
    T2Id=insertQuantOutput(appId, 'TESTQ2', TC103_TagName, 23.5, feedbackMethod='Simple Sum', db=db)
    
    writeTag(provider + TC104_TagName + "/sp/value", 46.3)
    writeTag(provider + TC104_TagName + "/mode/value", "AUTO")
    T3Id=insertQuantOutput(appId, 'TESTQ3', TC104_TagName, 46.3, feedbackMethod='Simple Sum', db=db)
    
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD122Priority=3.4, FD123Priority=3.4, FD122calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_2a', FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3g', db=db)
   
    fDName = 'FT_FD1_2_2'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test16h(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db, groupRampMethod='Shortest')
    
    writeTag(provider + TC101_TagName + "/sp/value", 9.6)
    writeTag(provider + TC101_TagName + "/mode/value", "AUTO")
    T1Id=insertQuantOutput(appId, 'TESTQ1', TC101_TagName, 9.6, feedbackMethod='Simple Sum', db=db)
    
    writeTag(provider + TC103_TagName + "/sp/value", 23.5)
    writeTag(provider + TC103_TagName + "/mode/value", "AUTO")
    T2Id=insertQuantOutput(appId, 'TESTQ2', TC103_TagName, 23.5, feedbackMethod='Simple Sum', db=db)
    
    writeTag(provider + TC104_TagName + "/sp/value", 46.3)
    writeTag(provider + TC104_TagName + "/mode/value", "AUTO")
    T3Id=insertQuantOutput(appId, 'TESTQ3', TC104_TagName, 46.3, feedbackMethod='Simple Sum', db=db)
    
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD122Priority=3.4, FD123Priority=3.4, FD122calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_2a', FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3g', db=db)
   
    fDName = 'FT_FD1_2_2'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

def test16i(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db, groupRampMethod='Average')
    
    writeTag(provider + TC101_TagName + "/sp/value", 9.6)
    writeTag(provider + TC101_TagName + "/mode/value", "AUTO")
    T1Id=insertQuantOutput(appId, 'TESTQ1', TC101_TagName, 9.6, feedbackMethod='Simple Sum', db=db)
    
    writeTag(provider + TC103_TagName + "/sp/value", 23.5)
    writeTag(provider + TC103_TagName + "/mode/value", "AUTO")
    T2Id=insertQuantOutput(appId, 'TESTQ2', TC103_TagName, 23.5, feedbackMethod='Simple Sum', db=db)
    
    writeTag(provider + TC104_TagName + "/sp/value", 46.3)
    writeTag(provider + TC104_TagName + "/mode/value", "AUTO")
    T3Id=insertQuantOutput(appId, 'TESTQ3', TC104_TagName, 46.3, feedbackMethod='Simple Sum', db=db)
    
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD122Priority=3.4, FD123Priority=3.4, FD122calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_2a', FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3g', db=db)

    fDName = 'FT_FD1_2_2'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName


def test16j(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db, groupRampMethod='None')
    
    writeTag(provider + TC101_TagName + "/sp/value", 9.6)
    writeTag(provider + TC101_TagName + "/mode/value", "AUTO")
    T1Id=insertQuantOutput(appId, 'TESTQ1', TC101_TagName, 9.6, feedbackMethod='Simple Sum', db=db)
    
    writeTag(provider + TC103_TagName + "/sp/value", 23.5)
    writeTag(provider + TC103_TagName + "/mode/value", "AUTO")
    T2Id=insertQuantOutput(appId, 'TESTQ2', TC103_TagName, 23.5, feedbackMethod='Simple Sum', db=db)
    
    writeTag(provider + TC104_TagName + "/sp/value", 46.3)
    writeTag(provider + TC104_TagName + "/mode/value", "AUTO")
    T3Id=insertQuantOutput(appId, 'TESTQ3', TC104_TagName, 46.3, feedbackMethod='Simple Sum', db=db)
    
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD122Priority=3.4, FD123Priority=3.4, FD122calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_2a', FD123calculationMethod='ils.diagToolkit.test.calculationMethods.fd1_2_3g', db=db)
   
    #postDiagnosisEntry(project, applicationName, 'FT_Family1_2', 'FT_FD1_2_2', 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    fDName = 'FT_FD1_2_3'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName


def test17a(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_1'
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID','DIAGRAM_UUID', provider=providerName, database=db)

    #
    # Set up the 2nd application
    #
    
    applicationName='FINAL_TEST_2'
    familyName = 'FT_Family2_1'
    diagramName = 'FT_Diagram2_1'
    fDName = 'FT_FD2_1_1'
    appId=insertApp2(db)
    Q21_id=insertQuantOutput(appId, 'TEST_Q21', TC100_TagName,  19.88, db=db)
    writeTag(provider + TC100_TagName + "/sp/value", 19.88)
    
    Q22_id=insertQuantOutput(appId, 'TEST_Q22', TC101_TagName, 123.15, db=db)
    writeTag(provider + TC101_TagName + "/sp/value", 123.15)
    
    Q23_id=insertQuantOutput(appId, 'TEST_Q23', T100_TagName,    2.31, db=db)
    writeTag(provider + T100_TagName + "/value", 2.31)
    
    Q24_id=insertQuantOutput(appId, 'TEST_Q24', T101_TagName,   36.23, db=db)
    writeTag(provider + T101_TagName + "/value", 36.23)
    
    writeTag(provider + TC102_TagName + "/value", 20.5)
    writeTag(provider + TC102_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC102_TagName + "/sp/value", 20.5)
    writeTag(provider + TC102_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC102_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC102_TagName + "/sp/rampState", "")
    Q25_id=insertQuantOutput(appId, 'TEST_Q25', TC102_TagName, 20.5, db=db)
    
    writeTag(provider + TC105_TagName + "/value", 20.0)
    writeTag(provider + TC105_TagName + "/mode/value", "AUTO")
    writeTag(provider + TC105_TagName + "/sp/value", 20.0)
    writeTag(provider + TC105_TagName + "/sp/targetValue", 0.0)
    writeTag(provider + TC105_TagName + "/sp/rampTime", 10.0)
    writeTag(provider + TC105_TagName + "/sp/rampState", "")
    Q26_id=insertQuantOutput(appId, 'TEST_Q26', TC105_TagName, 10.0, db=db)
    
    insertApp2Families(appId, Q21_id, Q22_id, Q23_id, Q24_id, Q25_id, Q26_id, FD211calculationMethod='ils.diagToolkit.test.calculationMethods.fd2_1_1a', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    
    applicationName = "FINAL_TEST_%"
    return applicationName

# Test a single text recommendation
def test18a(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_5'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id,postProcessingCallback='ils.diagToolkit.test.calculationMethods.postDownloadSpecialActions', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Simultaneously post two text recommendations with different priorities
def test18b1(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_6'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_5'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Simultaneously post two text recommendations with the same priorities
def test18b2(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId, T1Id, T2Id, T3Id, FD125Priority=5.0, FD126Priority=5.0, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_6'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_5'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Simultaneously post two text recommendations with the same priorities
def test18b3(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId, T1Id, T2Id, T3Id, FD125Priority=5.0, FD126Priority=5.0, postProcessingCallback='ils.diagToolkit.test.calculationMethods.postDownloadSpecialActions', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_6'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    
    fDName = 'FT_FD1_2_5'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Test a high priority text final diagnosis becoming true followed by a low priority numeric diagnosis 
def test18c(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_6'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    
    fDName = 'FT_FD1_2_2'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Test a low priority text FD followed by a high priority numeric FD
def test18d(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    fDName = 'FT_FD1_2_5'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    time.sleep(DELAY_BETWEEN_PROBLEMS)
    
    fDName = 'FT_FD1_2_2'
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Test a static (One without a calculation method) text recommendation.
def test18e(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName = 'FT_FD1_2_6'
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD126calculationMethod='', db=db)
    
    # Insert a diagnosis Entry - This simulates the FD becoming True
    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName

# Test a text recommendation loaded with special punctuation.
def test18f(db):
    disableVectorClampMode(provider)
    applicationName='FINAL_TEST_1'
    familyName = 'FT_Family1_2'
    diagramName = 'FT_Diagram1_2'
    fDName="FT_FD1_2_6"
    
    appId=insertApp1(db)
    T1Id=insertQuantOutput(appId, 'TESTQ1', T1TagName, 9.6, db=db)
    T2Id=insertQuantOutput(appId, 'TESTQ2', T2TagName, 23.5, db=db)
    T3Id=insertQuantOutput(appId, 'TESTQ3', T3TagName, 46.3, db=db)
    insertApp1Families(appId,T1Id,T2Id,T3Id, FD126calculationMethod='', db=db)
    
    textRecommendation="Hello, It's a sunny day! The boss said: \"Turn up the heat!\".  Here are some more \@#/$@%^&*()?>< THE END"
    updateFinalDiagnosisTextRecommendation(fDName, textRecommendation, db)

    postDiagnosisEntry(project, applicationName, familyName, diagramName, fDName, 'FD_UUID', 'DIAGRAM_UUID', provider=providerName, database=db)
    return applicationName