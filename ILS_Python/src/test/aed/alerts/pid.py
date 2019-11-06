'''
Created on Nov 13, 2016

@author: Pete
'''

import xom.emre.aed.engine.main as engineMain

#=====================================================================================================
# This module contains ad-hoc tests that are useful during development to test specific functionality.
# These tests are not part of the automated test framework.
#=====================================================================================================
def setAll():
    # Simulate the dictionary of results that the engine may return    
    results = []
    results.append(simulatePidHeader())
    results.append(simulatePidResults(2179, lVarState = True))    

    # Call the engine
    print "Simulating a return from JAVA..."

    engineMain(results)


def set(modelId):
    # Simulate the dictionary of results that the engine may return    
    results = []
    results.append(simulatePidHeader())
    results.append(simulatePidResults(modelId, lVarState = True))    

    # Call the engine
    print "Simulating a return from JAVA..."

    engineMain(results)
    

def setDeadbandTimer2179():    
    print "******************************************************************"
    print "* Simulate the deadband Timer becoming active.                   *"
    print "* The JAVA modele manages this, but the deadband timer becomes   *"
    print "* active when the model first becomes false.                     *"
    print "******************************************************************"

    results = []
    results.append(simulatePidHeader())
    results.append(simulatePidResults(2179, deadbandSuppression = True))

    # Call the engine
    print "Simulating a return from JAVA..."

    engineMain(results)
    

def setDeadbandTimerAndAlert2179():    
    print "******************************************************************"
    print "* Simulate the deadband Timer becoming active.                   *"
    print "* The JAVA modele manages this, but the deadband timer becomes   *"
    print "* active when the model first becomes false.                     *"
    print "******************************************************************"

    results = []
    results.append(simulatePidHeader())
    results.append(simulatePidResults(2179, deadbandSuppression = True, lVarState = True))

    # Call the engine
    print "Simulating a return from JAVA..."

    engineMain(results)


def clearDeadbandTimer2179():
    print "************************************************************************"
    print "* Simulate the deadbandTimer clearing (expiring).                      *"
    print "* The JAVA engine manages deadbandTimer expiration, but it should only *"
    print "* expire when the model has been false for a time greater than the     *"
    print "* deadband time interval.                                              *"
    print "************************************************************************"

    results = []
    results.append(simulatePidHeader())
    results.append(simulatePidResults(2179, deadbandSuppression = False))
    
    # Call the engine
    print "Simulating a return from JAVA..."
    
    engineMain(results)

#----------------------------------------------------------------------------------
def setSPSuppressor2179():
    print "*******************************************************************************"
    print "* Simulate the Setpoint Change Suppressor becoming active.                    *"
    print "* The JAVA modele detects this, but the setpoint change suppressor becomes    *"
    print "* active when the a large setpoint change is detected.  Setpoint Change       *"
    print "* suppression only applies toi the control submodels (HVar, COff, ACE)        *"
    print "*******************************************************************************"

    results = []
    results.append(simulatePidHeader())
    results.append(simulatePidResults(2179, spSuppression = True))

    # Call the engine
    print "Simulating a return from JAVA..."

    engineMain(results)


def setSPSuppressorAndLVarAlert2179():
    print "*******************************************************************************"
    print "* Simulate the Setpoint Change suppressor becoming active and an LVAR alert.  *"
    print "* The JAVA modele detects this, but the setpoint change suppressor becomes    *"
    print "* active when the a large setpoint change is detected.  Setpoint Change       *"
    print "* suppression only applies toi the control submodels (HVar, COff, ACE)        *"
    print "*******************************************************************************"

    results = []
    results.append(simulatePidHeader())
    results.append(simulatePidResults(2179, spSuppression = True, lVarState = True))
    
    # Call the engine
    print "Simulating a return from JAVA..."

    engineMain(results)


def setSPSuppressorAndHVarAlert2179():    
    print "*******************************************************************************"
    print "* Simulate the Setpoint Change suppressor becoming active and an HVAR alert.  *"
    print "* The JAVA modele detects this, but the setpoint change suppressor becomes    *"
    print "* active when the a large setpoint change is detected.  Setpoint Change       *"
    print "* suppression only applies toi the control submodels (HVar, COff, ACE)        *"
    print "*******************************************************************************"
    
    results = []
    results.append(simulatePidHeader())
    results.append(simulatePidResults(2179, spSuppression = True, hVarState = True))

    # Call the engine
    print "Simulating a return from JAVA..."

    engineMain(results)

#
def clearSPSuppressor2179():
    print "***************************************************************************"
    print "* Simulate the deadbandTimer clearing (expiring).                         *"
    print "* The JAVA modele detects this, but the setpoint change suppressor clears *"
    print "* a configurable time after the large change was detected.                *"
    print "***************************************************************************"

    results = []
    results.append(simulatePidHeader())
    results.append(simulatePidResults(2179, spSuppression = False))
    
    # Call the engine
    print "Simulating a return from JAVA..."
    
    engineMain(results)


#------------------------------------------------
def clearAll(): 
    # Simulate the dictionary of results that the engine may return    
    results = []
    results.append(simulatePidHeader())
    results.append(simulatePidResults(2179))    
    results.append(simulatePidResults(3155))
    results.append(simulatePidResults(3156))
    results.append(simulatePidResults(3157))
    results.append(simulatePidResults(3158))    

    # Call the engine
    print "Simulating a return from JAVA..."

    engineMain(results)

    
def clear(id):
    # Simulate the dictionary of results that the engine may return    
    results = []
    results.append(simulatePidHeader())
    results.append(simulatePidResults(id))    
    
    # Call the engine
    print "Simulating a return from JAVA..."
    
    engineMain(results)

def simulatePidHeader():
    import system
    
    print "****************************************************"
    print "***********  SETTING THE HEADER ********************"
    print "****************************************************"
    project = system.util.getProjectName()
    header = {'completionScript': 'xom.engine.core.wrapper.reportComplete()', 
        'dataCollectionTimeout': 60000, 'projectName': project}
    return header


def simulatePidResults(modelId, lVarState = False, hVarState = False, ACEState = False, coffState = False, 
    deadbandSuppression = False, dcsAlarmSuppression = False, spSuppression = False):

    from xom.emre.aed.startup.gateway import getPlainProviderName
    plainProvider = getPlainProviderName()
    modelType = "PID"
    
    hvarDict = {
        'state': hVarState,
        'status': 'INITIALIZING',
        'standardDeviation': 0.0, 
        'statusReason': '', 
        'certainty': 0.0, 
        'durationCounter': 0
        }
        
    aceDict = {
        'state': ACEState,
        'status': 'INITIALIZING',
        'standardDeviation': 0.0, 
        'statusReason': '', 
        'certainty': 0.0, 
        'durationCounter': 0
        }

    coffDict = {
        "state": coffState,
        'status': 'INITIALIZING',
        'standardDeviation': 0.0, 
        'statusReason': '', 
        'certainty': 0.0, 
        'durationCounter': 0
        }
        
    lvarDict = {
        "state": lVarState,
        'status': 'INITIALIZING',
        'standardDeviation': 0.0, 
        'statusReason': '', 
        'certainty': 0.0, 
        'durationCounter': 0
        }

    pidDict = {
        'id': modelId,
        'modelType': modelType,
        'provider': plainProvider,
        'parentTagPath': "Models/" + type + str(modelId), 
        'loggingEnabled': False,
        'debug': 'true',
        'deadbandSuppression': deadbandSuppression,
        'dcsAlarmSuppression': dcsAlarmSuppression,
        'spSuppression': spSuppression,
        'aws': 'NORMAL',
        'timestamp': '2013.04.14 17:46:25.463',
        'controlError': 0.0, 
        'filteredPV': 0.0, 
        'mode': 'UNKNOWN', 
        'status': 'INITIALIZING', 
        'statusReason': '',
        'dcSP': 0.0, 
        'dcsAlarm': False, 
        'certainty': 0.0,
        "ACE": aceDict,
        "COff": coffDict,
        "HVar": hvarDict,
        "LVar": lvarDict 
        }

    return pidDict