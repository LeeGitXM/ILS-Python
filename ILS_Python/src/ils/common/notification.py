'''
Created on Nov 5, 2016

@author: Pete
'''

import system
from ils.common.config import getDatabase, getIsolationDatabase
from ils.log import getLogger
logger = getLogger(__name__)

def notifyError(project, message, payload, post, db, isolationMode):
    logger.infof("In %s.notifyError(), Sending <%s> message to project: <%s>, post: <%s>, isolation: %s, payload: <%s>", __name__, str(message), str(project), str(post), str(isolationMode), str(payload))
    
    notifier(project, message, payload, post, db, isolationMode)


def notifyText(project, notificationText, post, isolationMode):
    logger.infof("In %s.notifyText(), Sending <%s> message to project: <%s>, post: <%s>", __name__, str(notificationText), str(project), str(post), str(isolationMode))
    
    message = "consoleManager"

    payload = {'type': "textNotification", 'notificationText': notificationText}

    if isolationMode:
        db = getIsolationDatabase()
    else:
        db = getDatabase()
    
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
        logger.tracef("Targeting post: <%s>", post)
        
        foundClient = False
        
        ''' Implement rule #1 '''
        logger.tracef("Rule #1 - looking for clients logged in as %s that are in isolation mode: %s!", post, str(isolationMode))
        from ils.common.message.interface import getPostClientIds
        clientSessionIds = getPostClientIds(post, project, db, isolationMode)
        if len(clientSessionIds) > 0:
            foundClient = True
            logger.tracef("Found %d clients logged in as %s that are in isolation mode: %s!", len(clientSessionIds), post, str(isolationMode))
            
            for clientSessionId in clientSessionIds:
                if clientSessionId not in notifiedClients:
                    notifiedClients.append(clientSessionId)
                    system.util.sendMessage(project, message, payload, scope="C", clientSessionId=clientSessionId)

        ''' Implement Rule #2 '''
        logger.tracef("Rule #2 - looking for clients with consoles displayed...")
        from ils.common.message.interface import getConsoleClientIdsForPost
        clientSessionIds = getConsoleClientIdsForPost(post, project, db, isolationMode)
        if len(clientSessionIds) > 0:
            payload["showOverride"] = True
            foundClient = True
            for clientSessionId in clientSessionIds:
                if clientSessionId not in notifiedClients:
                    logger.tracef("Found a client with the console displayed %s with client Id %s", post, str(clientSessionId))
                    notifiedClients.append(clientSessionId)
                    system.util.sendMessage(project, message, payload, scope="C", clientSessionId=clientSessionId)
        
        if not(foundClient):
            logger.trace("Notifying every client because I could not find the post logged in")
            payload["showOverride"] = False
            system.util.sendMessage(project, message, payload, scope="C")
    else:
        logger.trace("Sending notification to every client because this is not a targeted alert")
        payload["showOverride"] = False
        system.util.sendMessage(project, message, payload, scope="C")