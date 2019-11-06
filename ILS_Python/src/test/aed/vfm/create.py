'''
Created on Nov 13, 2016

@author: Pete
'''

def model(modelId, debug, inhibitEvaluation, loggingEnabled, logFile, timeDeadband, dcsAlarmTimeDeadband, deltaPressureExponent, deltaPressureReference, biasLimitTypeId, biasHighLimit, biasLowLimit, bias, filterParameter, durationLimit):
    import system

    SQL = "update RuleModel " \
        " set Debug = ?, InhibitEvaluation = ?, LoggingEnabled = ?, LogFile = ?"\
        " where RuleModelId = ?"
    system.db.runPrepUpdate(SQL, [debug, inhibitEvaluation, loggingEnabled, logFile, modelId])
    
    SQL = "update Model " \
        " set TimeDeadband = ?, DCSAlarmTimeDeadband = ? "\
        " where ModelId = ?"
    system.db.runPrepUpdate(SQL, [timeDeadband, dcsAlarmTimeDeadband, modelId])
    
    # The VFM model is intact - there is nothing in this table that needs to be changed

    SQL = "update ValveFlowMismatchSubmodel " \
        " set InhibitEvaluation = 0, DeltaPressureExponent = ?, DeltaPressureReference = ?, "\
        " BiasLimitTypeId = ?, BiasHighLimit = ?, BiasLowLimit = ?, Bias = ?, FilterParameter = ?, "\
        " DurationLimit = ? "\
        " where VFMModelId = ?"
    system.db.runPrepUpdate(SQL, [deltaPressureExponent, deltaPressureReference, biasLimitTypeId, biasHighLimit,
        biasLowLimit, bias, filterParameter, durationLimit, modelId])

# Create a basic VFM model
def basic(key, modelId):
    import app, system
    
    print "Configuring a basic VFM model..."

    debug =             True
    inhibitEvaluation =    False
    loggingEnabled =     True
    logFile =            'c:\temp\vfm.csv'
    timeDeadband =        4.5
    dcsAlarmTimeDeadband = 4.5
    deltaPressureExponent = 1
    deltaPressureReference = 2
    biasLimitTypeId    =    1
    biasHighLimit =     15.0
    biasLowLimit =        5.0
    bias =                0.0
    filterParameter =    0.001
    durationLimit =        2

    app.test.vfm.create.model(modelId, debug, inhibitEvaluation, loggingEnabled, logFile, timeDeadband, dcsAlarmTimeDeadband, deltaPressureExponent, deltaPressureReference, biasLimitTypeId, biasHighLimit, biasLowLimit, bias, filterParameter, durationLimit)

    dict = app.vfm.engine.dictionary.buildDictionary(key, modelId)
    
    return dict