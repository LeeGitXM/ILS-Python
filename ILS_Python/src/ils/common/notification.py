'''
Created on Nov 5, 2016

@author: Pete
'''

import system
from ils.log import getLogger
log = getLogger(__name__)

def notifyError(project, message, payload, post, db, isolationMode):
    log.infof("In %s.notifyError(), Sending <%s> message to project: <%s>, post: <%s>, isolation: %s, payload: <%s>", __name__, str(message), str(project), str(post), str(isolationMode), str(payload))
    
    notifier(project, message, payload, post, db, isolationMode)


def notifyText(project, notificationText, post, db, isolationMode):
    log.infof("In %s.notifyText(), Sending <%s> message to project: <%s>, post: <%s>", __name__, str(notificationText), str(project), str(post), str(isolationMode))
    
    message = "consoleManager"
    payload = {'type': "textNotification", 'notificationText': notificationText}
    notifier(project, message, payload, post, db, isolationMode)
        

def notifier(project, message, payload, post, db, isolationMode):
    '''
    If a post is specified, then:
    1) Notify every client where the username = the post and the isolation mode matched
    2) Notify every client that was not in #1 that is showing the console window and the isolation mode matched.
    3) If no windows matched 1 or 2, then blast it everywhere.
    '''
    notifiedClients = []
    
    if post <> "":
        log.tracef("Targeting post: <%s>", post)
        
        ''' Implement rule #1 '''
        foundClient, notifiedClients = notifyByPost(project, message, payload, post, db, isolationMode)

        ''' Implement Rule #2 '''
        foundClient, notifiedClients = notifyByConsoleWindow(project, message, payload, post, db, isolationMode, foundClient, notifiedClients)
        
        if not(foundClient):
            log.trace("Notifying every client because I could not find the post logged in")
            payload["showOverride"] = False
            system.util.sendMessage(project, message, payload, scope="C")
    else:
        log.trace("Sending notification to every client because this is not a targeted alert")
        payload["showOverride"] = False
        system.util.sendMessage(project, message, payload, scope="C")
        
def notifyByPost(project, message, payload, post, db, isolationMode):
    log.tracef("Rule #1 - looking for clients logged in as %s that are in isolation mode: %s!", post, str(isolationMode))
    notifiedClients = []
    foundClient = False
    from ils.common.message.interface import getPostClientIds
    clientSessionIds = getPostClientIds(post, project, db, isolationMode)
    if len(clientSessionIds) > 0:
        foundClient = True
        log.tracef("Found %d clients logged in as %s that are in isolation mode: %s!", len(clientSessionIds), post, str(isolationMode))
        
        for clientSessionId in clientSessionIds:
            if clientSessionId not in notifiedClients:
                notifiedClients.append(clientSessionId)
                system.util.sendMessage(project, message, payload, scope="C", clientSessionId=clientSessionId)
    return foundClient, notifiedClients

def notifyByConsoleWindow(project, message, payload, post, db, isolationMode, foundClient, notifiedClients):
    log.tracef("Rule #2 - looking for clients with consoles displayed...")
    from ils.common.message.interface import getConsoleClientIdsForPost
    clientSessionIds = getConsoleClientIdsForPost(post, project, db, isolationMode)
    if len(clientSessionIds) > 0:
        payload["showOverride"] = True
        foundClient = True
        for clientSessionId in clientSessionIds:
            if clientSessionId not in notifiedClients:
                log.tracef("Found a client with the console displayed %s with client Id %s", post, str(clientSessionId))
                notifiedClients.append(clientSessionId)
                system.util.sendMessage(project, message, payload, scope="C", clientSessionId=clientSessionId)
    return foundClient, notifiedClients