'''
Created on Nov 13, 2016

@author: Pete
'''

global fileRoot, params, sqlparams, dict, pyResults

def initializeTags():
    import system, time
    
    print "   ...initializing the tags used for inputs..."
    system.tag.write("[AED]AED/Tags/T1", 0.0)
    system.tag.write("[AED]AED/Tags/T2", 0.0)
    system.tag.write("[AED]AED/Tags/T3", 0.0)
    system.tag.write("[AED]AED/Tags/T4", 0.0)
    system.tag.write("[AED]AED/Tags/T5", 0.0)

    time.sleep(5.0)

# Test #1: Simple High Var Alert
def test01(key, models):
    import app, system, time
    import app.test.common as common
    import app.test.rule as rule
    global params, sqlparams, tags, dict
    
    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,sp,deltaSP,dcSP,pv,filteredPV,controlError,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,spSuppression,"\
            "HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/T1,Tags/T2,Tags/T3,Tags/T4,Tags/T5'

    # Create the dictionary
#    dict = pid.create.basicHVar(key, modelId)

# Test #2: Simple High Var PID Alert with Acknowledgement"
def test02(key, models):
    import app, system, time
    import app.test.common as common
    import app.test.pid as pid
    global params, sqlparams, tags, dict

    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,sp,deltaSP,dcSP,pv,filteredPV,controlError,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,spSuppression,"\
                "HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    dict = pid.create.basicHVar(key, modelId)
        
# Test #3: Simple High Var PID Alert with Manual Suppression"
def test03(key, models):
    import app, system, time
    import app.test.common as common
    import app.test.pid as pid
    global params, sqlparams, tags, dict

    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,sp,deltaSP,dcSP,pv,filteredPV,controlError,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,spSuppression,"\
                "HVar.status,HVar.certainty,HVar.standardDeviation,HVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    dict = pid.create.basicHVar(key, modelId)
    
# Test #4: Deadband timer that expires with immediate ACK
def test04(key, models):
    import app.test.pid as pid
    global params, sqlparams, tags, dict

    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,sp,deltaSP,dcSP,pv,filteredPV,controlError,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,spSuppression,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    dict = pid.create.basicLVar(key, modelId)

# Test #5: Deadband timer that expires with immediate ACK
def test05(key, models):
    import app.test.pid as pid
    global params, sqlparams, tags, dict

    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    dict = pid.create.basicLVar(key, modelId)

# Test #6: Deadband timer that expires with immediate ACK
def test06(key, models):
    import app.test.pid as pid
    global params, sqlparams, tags, dict

    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    dict = pid.create.basicLVar(key, modelId)

# Test #7: Deadband timer without ACK
def test07(key, models):
    import app.test.pid as pid
    global params, sqlparams, tags, dict

    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    dict = pid.create.basicLVar(key, modelId)

# Test #8: Deadband timer that suppresses with immediate ACK
def test08(key, models):
    import app.test.pid as pid
    global params, sqlparams, tags, dict

    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    dict = pid.create.basicLVar(key, modelId)

# Test #9: Deadband timer that suppresses with delayed ACK
def test09(key, models):
    import app.test.pid as pid
    global params, sqlparams, tags, dict

    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    dict = pid.create.basicLVar(key, modelId)
    
# Test #10: Deadband timer that suppresses with very delayed ACK
def test10(key, models):
    import app.test.pid as pid
    global params, sqlparams, tags, dict

    modelId = models[0]

    # Define the output columns to extract from the results dictionary and write to the output file.
    params = "status,certainty,deadbandSuppression,dcsAlarm,dcsAlarmSuppression,deltaSP,dcSP,spSuppression,filteredPV,"\
            "LVar.status,LVar.certainty,LVar.standardDeviation,LVar.durationCounter:" + str(modelId)

    # Define the SQL queries that will be logged each cycle to the data file
    sqlparams = 'status:' + str(modelId) + ',activeAlertCount:' + str(modelId) + ',clearedAlertCount:' + str(modelId) + ',ackdAlertCount:' + str(modelId) + ',suppressedAlertCount:' + str(modelId)

    # Define tags whose values should be written to the logfile
    tags = 'Tags/FC100_OP'
    
    # Create the dictionary
    dict = pid.create.basicLVar(key, modelId)

