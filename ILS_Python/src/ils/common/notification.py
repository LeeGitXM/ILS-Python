'''
Created on Nov 5, 2016

@author: Pete
'''

import system
logger=system.util.getLogger("com.ils.common.notification")

def notify(project, message, payload, post, db):
    logger.infof("In %s.notify(), Sending <%s> message to project: <%s>, post: <%s>, payload: <%s>" % (__name__, message, project, post, str(payload)))
    if post <> "":
        logger.trace("Targeting post: <%s>" % (post))
        
        from ils.common.message.interface import getPostClientIds
        clientSessionIds = getPostClientIds(post, project)
        if len(clientSessionIds) > 0:
            logger.trace("Found %i clients logged in as %s!" % (len(clientSessionIds), post))
            payload["showOverride"] = True
            for clientSessionId in clientSessionIds:
                system.util.sendMessage(project, message, payload, scope="C", clientSessionId=clientSessionId)

        logger.trace("...now looking for clients with consoles displayed...")
        from ils.common.message.interface import getConsoleClientIdsForPost
        clientSessionIds = getConsoleClientIdsForPost(post, project, db)
        if len(clientSessionIds) > 0:
            payload["showOverride"] = True
            for clientSessionId in clientSessionIds:
                logger.trace("Found a client with the console displayed %s with client Id %s" % (post, str(clientSessionId)))
                system.util.sendMessage(project, message, payload, scope="C", clientSessionId=clientSessionId)
        else:
            logger.trace("Notifying every client because I could not find the post logged in")
            payload["showOverride"] = False
            system.util.sendMessage(project, message, payload, scope="C")
    else:
        logger.trace("Sending notification to every client because this is not a targeted alert")
        payload["showOverride"] = False
        system.util.sendMessage(project, message, payload, scope="C")