'''
Created on Nov 13, 2016

@author: Pete
'''
import system, string
from xom.emre.aed.pid.engine.dictionary import buildDictionary

def hvar(modelId, inhibitEvaluation, timeWindow, spcLimit, durationLimit):
    SQL = "update VariabilitySubmodel " \
        " set InhibitEvaluation = ?, TimeWindow = ?, SPCLimit = ?, DurationLimit = ? "\
        " where ModelId = ? and ModelType = 'High'"
    system.db.runPrepUpdate(SQL, [inhibitEvaluation, timeWindow, spcLimit, durationLimit, modelId])

def lvar(modelId, inhibitEvaluation, timeWindow, spcLimit, durationLimit):
    SQL = "update VariabilitySubmodel " \
        " set InhibitEvaluation = ?, TimeWindow = ?, SPCLimit = ?, DurationLimit = ? "\
        " where ModelId = ? and ModelType = 'Low'"
    system.db.runPrepUpdate(SQL, [inhibitEvaluation, timeWindow, spcLimit, durationLimit, modelId])

def ace(modelId, inhibitEvaluation, deadbandType, lowerDeadband, upperDeadband, accumulatedControlErrorLimit):
    if string.upper(deadbandType) == 'PCT':
        deadbandTypeId = 1
    else:
        deadbandTypeId = 2

    SQL = "update ACESubmodel " \
            " set InhibitEvaluation = ?, UpperDeadband = ?, LowerDeadband = ?, DeadbandTypeID = ?, SPCLimit = ? "\
            " where PIDModelId = ?"
    system.db.runPrepUpdate(SQL, [inhibitEvaluation, upperDeadband, lowerDeadband, deadbandTypeId, accumulatedControlErrorLimit, modelId])

def coff(modelId, inhibitEvaluation, deadbandType, durationLimit, lowerDeadband, upperDeadband):
    if string.upper(deadbandType) == 'PCT':
        deadbandTypeId = 1
    else:
        deadbandTypeId = 2

    SQL = "update ControlOffsetSubmodel " \
        " set InhibitEvaluation = ?, UpperDeadband = ?, LowerDeadband = ?, DeadbandTypeID = ?, DurationLimit = ? "\
        " where PIDModelId = ?"
    system.db.runPrepUpdate(SQL, [inhibitEvaluation, upperDeadband, lowerDeadband, deadbandTypeId, durationLimit, modelId])

def model(modelId, debug, inhibitEvaluation, loggingEnabled, logFile, timeDeadband, dcsAlarmTimeDeadband, dcTimeConstant, dcDelayTime, spChangeLimit, DCSAlarmTagIsNull):
    SQL = "update RuleModel " \
        " set Debug = ?, InhibitEvaluation = ?, LoggingEnabled = ?, LogFile = ?"\
        " where RuleModelId = ?"
    system.db.runPrepUpdate(SQL, [debug, inhibitEvaluation, loggingEnabled, logFile, modelId])
    
    SQL = "update Model " \
        " set TimeDeadband = ?, DCSAlarmTimeDeadband = ? "\
        " where ModelId = ?"
    system.db.runPrepUpdate(SQL, [timeDeadband, dcsAlarmTimeDeadband, modelId])
    
    SQL = "update PIDModel " \
        " set DCTimeConstant = ?, DCDelayTime = ?, SPChangeLimit = ? "\
        " where PIDModelId = ?"
    system.db.runPrepUpdate(SQL, [dcTimeConstant, dcDelayTime, spChangeLimit, modelId])

    if DCSAlarmTagIsNull:
        SQL = "update PIDModel " \
            " set DCSAlarmTagId is NULL "\
            " where PIDModelId = ?"
        system.db.runPrepUpdate(SQL, [modelId])    
    else:
        SQL = "update PIDModel " \
            " set DCSAlarmTagId = (select TagID from Tag where Name = 'FC100_DCSAlarm') "\
            " where PIDModelId = ?"
        system.db.runPrepUpdate(SQL, [modelId])    

# Create a basic PID model with just the High Variability submodel enabled
def basicHVar(key, modelId):
    log = system.util.getLogger("com.ils.aed.python.test")
    
#    print "Configuring a basic High Variability PID model..."
    
    # HVar 
    inhibitEvaluation = False
    timeWindow = 1.5
    spcLimit = 3.0
    durationLimit = 1.

    hvar(modelId, inhibitEvaluation, timeWindow, spcLimit, durationLimit)

    # LVar
    inhibitEvaluation = True
    timeWindow = 5.5
    spcLimit = 0.1
    durationLimit = 3.

    lvar(modelId, inhibitEvaluation, timeWindow, spcLimit, durationLimit)

    # ACE
    inhibitEvaluation = True
    deadbandType = 'ABS'
    lowerDeadband = 5.
    upperDeadband = 5.
    accumulatedControlErrorLimit = 50.0

    ace(modelId, inhibitEvaluation, deadbandType, lowerDeadband, upperDeadband, accumulatedControlErrorLimit)

    # Control Offset
    inhibitEvaluation = True
    deadbandType = 'ABS'
    durationLimit = 5.
    lowerDeadband = 7.5
    upperDeadband = 7.5

    coff(modelId, inhibitEvaluation, deadbandType, durationLimit, lowerDeadband, upperDeadband)

    # PID Model
    debug =             True
    inhibitEvaluation =    False
    loggingEnabled =     False
    logFile =            'c:\temp\pid.csv'
    timeDeadband =        4.5
    dcsAlarmTimeDeadband = 4.5
    dcTimeConstant =    0.0
    dcDelayTime =         0.0
    spChangeLimit =        20.0
    DCSAlarmTagIsNull =    False

    model(modelId, debug, inhibitEvaluation, loggingEnabled, logFile, timeDeadband, dcsAlarmTimeDeadband, dcTimeConstant, dcDelayTime, spChangeLimit, DCSAlarmTagIsNull)

    modelDict = buildDictionary(key, modelId, "Test", log)
    
    return modelDict

# Create a basic PID model with just the High Variability submodel enabled
def basicHVarForSPSuppression(key, modelId):
    log = system.util.getLogger("com.ils.aed.python.test")
        
#    print "Configuring a High Variability PID model for Setpoint Suppression..."

    # Everything is the same except for the SP Change Limit
    basicHVar(key, modelId)
    
    spChangeLimit = 3.0
    
    SQL = "update PIDModel " \
        " set SPChangeLimit = ? "\
        " where PIDModelId = ?"
    system.db.runPrepUpdate(SQL, [spChangeLimit, modelId])

    modelDict = buildDictionary(key, modelId, "Test", log)
        
    return modelDict

#
def basicLVar(key, modelId, timeDeadband):
    log = system.util.getLogger("com.ils.aed.python.test")
#    print "Configuring a basic Low Variability PID model..."

    # HVar 
    inhibitEvaluation = True
    timeWindow = 0.5
    spcLimit = 4.0
    durationLimit = 1.

    hvar(modelId, inhibitEvaluation, timeWindow, spcLimit, durationLimit)

    # LVar
    inhibitEvaluation = False
    timeWindow = 0.5
    spcLimit = 0.1
    durationLimit = 1.

    lvar(modelId, inhibitEvaluation, timeWindow, spcLimit, durationLimit)

    # ACE
    inhibitEvaluation = True
    deadbandType = 'ABS'
    lowerDeadband = 10.
    upperDeadband = 10.
    accumulatedControlErrorLimit = 100.0

    ace(modelId, inhibitEvaluation, deadbandType, lowerDeadband, upperDeadband, accumulatedControlErrorLimit)

    # Control Offset
    inhibitEvaluation = True
    deadbandType = 'ABS'
    durationLimit = 50.
    lowerDeadband = 51.5
    upperDeadband = 51.5

    coff(modelId, inhibitEvaluation, deadbandType, durationLimit, lowerDeadband, upperDeadband)

    # PID Model
    debug =             True
    inhibitEvaluation =    False
    loggingEnabled =     False
    logFile =            'c:\temp\pid.csv'
    dcsAlarmTimeDeadband = 4.5
    dcTimeConstant =    0.0
    dcDelayTime =         0.0
    spChangeLimit =        20.0
    DCSAlarmTagIsNull =    False

    model(modelId, debug, inhibitEvaluation, loggingEnabled, logFile, timeDeadband, dcsAlarmTimeDeadband, dcTimeConstant, dcDelayTime, spChangeLimit, DCSAlarmTagIsNull)

    modelDict = buildDictionary(key, modelId, "Test", log)
    
    return modelDict

# 
def basicLVarWithoutDCSAlarm(key, modelId):
    log = system.util.getLogger("com.ils.aed.python.test")

    # Everything is the same except for the DCSAlarmTag
    basicLVar(key, modelId)

    # PID Model
    debug =             True
    inhibitEvaluation =    False
    loggingEnabled =     False
    logFile =            'c:\temp\pid.csv'
    timeDeadband =        4.5
    dcsAlarmTimeDeadband = 4.5
    dcTimeConstant =    0.0
    dcDelayTime =         0.0
    spChangeLimit =        20.0
    DCSAlarmTagIsNull =    True

    model(modelId, debug, inhibitEvaluation, loggingEnabled, logFile, timeDeadband, dcsAlarmTimeDeadband, dcTimeConstant, dcDelayTime, spChangeLimit, DCSAlarmTagIsNull)

    modelDict = buildDictionary(key, modelId, "Test", log)
    
    return modelDict

# Create a basic PID model with just the Low Variability submodel enabled
def basicLVarForSPSuppression(key, modelId):
    log = system.util.getLogger("com.ils.aed.python.test")
        
#    print "Configuring a Low Variability PID model for Setpoint Suppression..."
    
    # Everything is the same except for the SP Change Limit
    basicLVar(key, modelId)
        
    spChangeLimit = 3.0
        
    SQL = "update PIDModel " \
        " set SPChangeLimit = ? "\
        " where PIDModelId = ?"
    system.db.runPrepUpdate(SQL, [spChangeLimit, modelId])
    modelDict = buildDictionary(key, modelId, "Test", log)
            
    return modelDict

# Create a basic PID model with all 4 submodels
def basic(key, modelId):
    log = system.util.getLogger("com.ils.aed.python.test")
    
#    print "Configuring a basic PID model (%s) with all four submodels enabled..." % (modelId)

    # HVar 
    inhibitEvaluation = False
    timeWindow = 5.5
    spcLimit = 2.0
    durationLimit = 4.

    hvar(modelId, inhibitEvaluation, timeWindow, spcLimit, durationLimit)

    # LVar
    inhibitEvaluation = False
    timeWindow = 5.5
    spcLimit = 0.1
    durationLimit = 5.

    lvar(modelId, inhibitEvaluation, timeWindow, spcLimit, durationLimit)

    # ACE
    inhibitEvaluation = False
    deadbandType = 'ABS'
    lowerDeadband = 2.6
    upperDeadband = 2.6
    accumulatedControlErrorLimit = 20.0

    ace(modelId, inhibitEvaluation, deadbandType, lowerDeadband, upperDeadband, accumulatedControlErrorLimit)

    # Control Offset
    inhibitEvaluation = False
    deadbandType = 'ABS'
    durationLimit = 5.
    lowerDeadband = 2.6
    upperDeadband = 2.6

    coff(modelId, inhibitEvaluation, deadbandType, durationLimit, lowerDeadband, upperDeadband)

    # PID Model
    debug =             True
    inhibitEvaluation =    False
    loggingEnabled =     False
    logFile =            'c:\temp\pid.csv'
    timeDeadband =        4.5
    dcsAlarmTimeDeadband = 4.5
    dcTimeConstant =    0.0
    dcDelayTime =         0.0
    spChangeLimit =        20.0
    DCSAlarmTagIsNull =    False
    
    model(modelId, debug, inhibitEvaluation, loggingEnabled, logFile, timeDeadband, dcsAlarmTimeDeadband, dcTimeConstant, dcDelayTime, spChangeLimit, DCSAlarmTagIsNull)

    modelDict = buildDictionary(key, modelId, "Test", log)
    
    return modelDict