'''
Unit test support

@author: rforbes
'''

actions = []

def clientTestWatcher():
    '''if there are any pending actions, execute them'''
    from ils.sfc.common.util import callMethod
    completedActions = []
    for action in actions:
        if callMethod(action):
            completedActions.append(action)
    for action in completedActions:
        actions.remove(action) 
        

def addAction(methodName, testName, chartRunId):
    actions.append({'testName' : testName, 'methodName' : methodName, 'chartRunId' : chartRunId})
    
def doActions():
    from ils.sfc.common.util import callMethod
    completedActions = []
    for action in actions:
        args = "'" + action['testName'] + "', '" + action['chartRunId'] + "'"
        if callMethod(action['methodName'], args):
            completedActions.append(action)
    for completedAction in completedActions:
        actions.remove(completedAction)
        
def failTest(testName, msg):
    from ils.sfc.common.constants import CHART_NAME, MESSAGE
    import system.util
    payload = dict()
    payload[CHART_NAME] = testName
    payload[MESSAGE] = msg
    system.util.sendMessage(system.util.getProjectName(), 'sfcTestFail', payload, "G")
