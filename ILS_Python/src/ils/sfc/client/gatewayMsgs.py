'''

Methods that involve sending a request to the Gateway
Created on Dec 2, 2015

@author: rforbes
'''

def sendMessageToGateway(handler, payload):
    '''Send a message to the gateway'''
    # TODO: check returned list of recipients
    # TODO: restrict to a particular client session
    from ils.sfc.common.constants import MESSAGE_ID, MESSAGE
    from ils.sfc.common.util import createUniqueId
    from system.util import sendMessage
    import system.util
    project = system.util.getProjectName()
    messageId = createUniqueId()
    payload[MESSAGE_ID] = messageId 
    payload[MESSAGE] = handler
    # print 'sending message to client', project, handler, payload
    sendMessage(project, 'sfcMessage', payload, "G")
    return messageId

# New session stuff:
def startSession(chartPath, isolationMode, startChart):
    from ils.sfc.common.constants import PROJECT, USER, ISOLATION_MODE, CHART_NAME, CLIENT_ID
    import system.util, system.security
    project = system.util.getProjectName() 
    user = system.security.getUsername()
    payload = dict()
    payload[ISOLATION_MODE] = isolationMode
    payload[PROJECT] = project
    payload[USER] = user
    payload[CHART_NAME] = chartPath
    payload[CLIENT_ID] = system.util.getClientId()
    sendMessageToGateway('sfcStartSession', payload)

def requestSessionData():
    '''Send a message to the gateway requesting chart names for sessions;
       the return message is sfcChartNamesResponse'''
    from ils.sfc.common.constants import PROJECT,CLIENT_ID
    import system.util
    payload = {PROJECT:system.util.getProjectName(), CLIENT_ID:system.util.getClientId()}
    sendMessageToGateway('sfcGetSessionData', payload)
    
def requestAddClient(sessionId):
    from ils.sfc.common.constants import PROJECT,CLIENT_ID, SESSION_ID
    import system.util
    payload = {
        PROJECT:system.util.getProjectName(), 
        CLIENT_ID:system.util.getClientId(),
        SESSION_ID: sessionId
        }
    sendMessageToGateway('sfcAddClient', payload)