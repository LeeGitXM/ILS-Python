'''
Created on Nov 13, 2016

@author: Pete
'''

from test.aed.pid.create import basic, basicHVar, basicLVar, basicHVarForSPSuppression, basicLVarForSPSuppression

def initializeTags():
    import system, time
    
    print "   ...initializing the tags used for inputs..."
    system.tag.write("[AED]AED/Tags/FC100_PV", -1.0)
    system.tag.write("[AED]AED/Tags/FC100_SP", -1.0)
    system.tag.write("[AED]AED/Tags/FC100_OP", -1.0)
    system.tag.write("[AED]AED/Tags/FC100_AWS", -1)
    system.tag.write("[AED]AED/Tags/FC100_DCSAlarm", "xxx")
    system.tag.write("[AED]AED/Tags/FC100_MODE", "xxx")

    time.sleep(5.0)

# Test #0: A very simple test of the test engine infrastructure
def test00(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,sp,deltaSP,dcSP,pv,filteredPV,controlError,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,spSuppression,"\
            "HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'

    # Create the dictionary
    modelDictionary = basicHVar(key, modelId)
    return params, sqlparams, tags, modelDictionary


# Test #1: Simple High Var Alert
def test01(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,sp,deltaSP,dcSP,pv,filteredPV,controlError,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,spSuppression,"\
            "HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'

    # Create the dictionary
    modelDictionary = basicHVar(key, modelId)
    return params, sqlparams, tags, modelDictionary

# Test #2: Simple High Var PID Alert with Acknowledgement"
def test02(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,sp,deltaSP,dcSP,pv,filteredPV,controlError,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,spSuppression,"\
                "HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicHVar(key, modelId)
    return params, sqlparams, tags, modelDictionary
        
# Test #3: Simple High Var PID Alert with Manual Suppression"
def test03(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,sp,deltaSP,dcSP,pv,filteredPV,controlError,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,spSuppression,"\
                "HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicHVar(key, modelId)
    return params, sqlparams, tags, modelDictionary
    
# Test #4: Deadband timer that expires with immediate ACK
def test04(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,sp,deltaSP,dcSP,pv,filteredPV,controlError,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,spSuppression,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicLVar(key, modelId, timeDeadband=3.5)
    return params, sqlparams, tags, modelDictionary

# Test #5: Deadband timer that expires with delayed ACK
def test05(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicLVar(key, modelId, timeDeadband=3.5)
    return params, sqlparams, tags, modelDictionary

# Test #6: Deadband timer that expires with very delayed ACK
def test06(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicLVar(key, modelId, timeDeadband=3.5)
    return params, sqlparams, tags, modelDictionary

# Test #7: Deadband timer without ACK
def test07(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicLVar(key, modelId, timeDeadband=5.5)
    return params, sqlparams, tags, modelDictionary

# Test #8: Deadband timer that suppresses with immediate ACK
def test08(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicLVar(key, modelId, timeDeadband=5.5)
    return params, sqlparams, tags, modelDictionary

# Test #9: Deadband timer that suppresses with delayed ACK
def test09(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicLVar(key, modelId, timeDeadband=5.5)
    return params, sqlparams, tags, modelDictionary
    
# Test #10: Deadband timer that suppresses with very delayed ACK
def test10(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicLVar(key, modelId, timeDeadband=5.5)
    return params, sqlparams, tags, modelDictionary

# Test #11: DCS Alarm where DCS Alarm precedes A E D alert
def test11(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicLVar(key, modelId)
    return params, sqlparams, tags, modelDictionary

# Test #12: DCS Alarm where A E D alert precedes DCS alert
def test12(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicLVar(key, modelId)
    return params, sqlparams, tags, modelDictionary

# Test #13: DCS Alarm precedes A E D alert and expires quickly
def test13(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicLVar(key, modelId)
    return params, sqlparams, tags, modelDictionary

# Test #14: DCS Alarm wher ethe DCS alert input is not defined
def test14(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicLVar(key, modelId)
    return params, sqlparams, tags, modelDictionary

# Test #15: SP Suppression - Suppressor precededand extends beyond H-VAR alert
def test15(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicHVarForSPSuppression(key, modelId)
    return params, sqlparams, tags, modelDictionary

# Test #16: SP Suppression - Suppressor precedes but expires before alert
def test16(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicHVarForSPSuppression(key, modelId)
    return params, sqlparams, tags, modelDictionary

# Test #17: SP Suppression - Alert precedes suppressor but clears before suppressor
def test17(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicHVarForSPSuppression(key, modelId)
    return params, sqlparams, tags, modelDictionary

# Test #18: SP suppression - Alert precedes suppressor and persists longer than suppressor
def test18(key, models):
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basicHVarForSPSuppression(key, modelId)
    return params, sqlparams, tags, modelDictionary
    
# Test #19: SP suppression - Suppressor precedes FROZEN VALUE alert
def test19(key, models):
    modelId = models[0]
        
    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)
    
    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
        
    # Create the dictionary
    modelDictionary = basicLVarForSPSuppression(key, modelId)
    return params, sqlparams, tags, modelDictionary

# Test #20: Short test using all submodels
def test20(key, models):
    modelId = models[0]
    
    # Define the output columns to extract from the results dictionary and write to the output file.
    params = 'status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,'\
        'LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter,'\
        'HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter,'\
        'controlError,COff.status,COff.state,COff.durationCounter,COff.certainty,COff.upperLimit,COff.lowerLimit,'\
        'ACE.accumulatedControlError,ACE.status,ACE.state,ACE.certainty,ACE.upperLimit,ACE.lowerLimit'

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    modelDictionary = basic(key, modelId)
    return params, sqlparams, tags, modelDictionary