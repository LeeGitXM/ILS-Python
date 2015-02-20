'''
Created on Feb 4, 2015

@author: Pete
'''

def postConsoleMessage(console, status, message):
    from ils.queue.commons import getQueueForConsole
    queueKey=getQueueForConsole(console)
    
    from ils.queue.message import insert
    insert(queueKey, status, message)    