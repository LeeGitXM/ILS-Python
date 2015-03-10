'''
Created on Jan 15, 2015

@author: rforbes
'''
def inputStepTest():
    import ils.sfc.client.util
    ils.sfc.client.util.runChart('StepTests/InputStepTest/InputStepProcedure')

def reviewDataStepTest():
    import ils.sfc.client.util
    ils.sfc.client.util.runChart('StepTests/ReviewDataStepTest/ReviewData')

def testStep(stepClassName, stepProperties):
    '''Activate a single step on the gateway as if it was in a chart'''
    from ils.sfc.client.controlPanel import createControlPanel
    from ils.sfc.client.util import registerClient
    from ils.sfc.common.constants import PROJECT, USER, INSTANCE_ID
    from ils.sfc.common.constants import CHART_PROPERTIES, STEP_PROPERTIES, CLASS_NAME
    from ils.sfc.common.util import createUniqueId
    import system.util.sendMessage
    project = system.util.getProjectName()
    user = system.security.getUsername()
    chartProperties = dict()
    chartProperties[PROJECT] = project
    chartProperties[USER] = user
    chartProperties[INSTANCE_ID] = createUniqueId()
    createControlPanel(chartProperties)
    registerClient()
    payload = dict()
    payload[CHART_PROPERTIES] = chartProperties
    payload[STEP_PROPERTIES] = stepProperties
    payload[CLASS_NAME] = stepClassName
    system.util.sendMessage(project, 'sfcActivateStep', payload, "G")

def clickButton(payload):
    '''Programmatically click the named button in the named window'''
    from ils.sfc.common.constants import WINDOW, BUTTON, MESSAGE_ID
    from system.gui import findWindow
    from ils.sfc.client.util import sendResponse
    response = "OK"
    window = findWindow(WINDOW)
    if window != None:
        button = window.getRootContainer().getComponent(payload[BUTTON])
        if button != None:
            button.doClick()
        else:
            response = 'Button not found: ' + payload[BUTTON]
    else :
        response = 'Window not found: ' + payload[WINDOW]
    sendResponse(payload[MESSAGE_ID], response)
