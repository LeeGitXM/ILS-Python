'''
Created on Sep 13, 2017

@author: phass
'''

import system

def sfcNotify(project, message, payload, post, controlPanelName, controlPanelId, db):
    print "In %s.sfcNotify(), Sending <%s> message to project: <%s>, post: <%s>, payload: <%s>" % (__name__, str(message), str(project), str(post), str(payload))
    payload["showOverride"] = False
    system.util.sendMessage(project, message, payload, scope="C")