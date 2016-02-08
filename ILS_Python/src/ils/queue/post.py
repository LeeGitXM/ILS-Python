'''
Created on Feb 4, 2015

@author: Pete
'''

def insertPostMessage(post, status, message):
    from ils.queue.commons import getQueueForPost
    queueKey=getQueueForPost(post)
    
    from ils.queue.message import insert
    insert(queueKey, status, message)    