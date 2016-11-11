'''
Created on Nov 5, 2016

@author: Pete
'''

import system
logger=system.util.getLogger("com.ils.common.notification")

def notify(project, message, payload, post, db):
    
    if post <> "":
        logger.trace("Targeting a <%s> message to post: <%s>" % (message, post))
        
        from ils.common.message.interface import getPostClientIds
        clientSessionIds = getPostClientIds(post, project)
        if len(clientSessionIds) > 0:
            logger.trace("Found %i clients logged in as %s!" % (len(clientSessionIds), post))
            for clientSessionId in clientSessionIds:
                system.util.sendMessage(project, message, payload, scope="C", clientSessionId=clientSessionId)
        else:
            logger.trace("Did not find any console login sessions, now looking for clients with consoles displayed...")
            from ils.common.message.interface import getConsoleClientIdsForPost
            clientSessionIds = getConsoleClientIdsForPost(post, project, db)
            if len(clientSessionIds) > 0:
                for clientSessionId in clientSessionIds:
                    logger.trace("Found a client with the console displayed %s with client Id %s" % (post, str(clientSessionId)))
                    system.util.sendMessage(project, message, payload, scope="C", clientSessionId=clientSessionId)
            else:
                logger.trace("Notifying every client because I could not find the post logged in")
                system.util.sendMessage(project, message, payload, scope="C")
    else:
        logger.trace("Sending notification to every client because this is not a targeted alert")
        system.util.sendMessage(project, message, payload, scope="C")