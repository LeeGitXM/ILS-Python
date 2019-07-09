'''
Created on Apr 8, 2016

@author: ils
'''

import system, string
from ils.common.util import stripHTML
LOGBOOK_DETAIL_MESSAGE_LENGTH = 2000

def writeToLogbook(logbook, message, database=""):
    insert(logbook, message, database)

def insert(logbook, message, database=""):
    logbookId = getLogbookId(logbook, database)
    _insert(logbookId, message, database)
    
def writeToLogbookForPost(post, message, database=""):
    insertForPost(post, message, database)
    
def insertForPost(post, message, database=""):
    logbookId = getLogbookIdForPost(post, database)
    _insert(logbookId, message, database)

def _insert(logbookId, message, database=""):
    # The length of the message is limited to 2000 characters
    
    '''
    7/8/19 I'm not sure why I was stripping the HTML formatting from a logbook message.  The download message is carefully formatted using HTML.  
    If I really need to stripthe HTML, then the message needs to be reformatted with returns spaces and tabs.  And this utiility function would not be needed.
    '''
    #message=stripHTML(message)
    message=message[:LOGBOOK_DETAIL_MESSAGE_LENGTH - 2]
    SQL = "insert into TkLogbookDetail (LogbookId, Timestamp, Message) values (?, getdate(), ?)"
    system.db.runPrepUpdate(SQL, [logbookId, message], database)
    
# Fetch the logbook id given the logbook name 
def getLogbookId(logbook, database = ''):
    logbook=string.upper(logbook)    
    SQL = "select LogbookId from TkLogbook where upper(LogbookName) = '%s'" % (logbook)
    logbookId = system.db.runScalarQuery(SQL, database)
    return logbookId

# Fetch the logbook id for a post 
def getLogbookIdForPost(post, database = ''):
    post=string.upper(post)    
    SQL = "select LogbookId from TkPost where upper(Post) = '%s'" % (post)
    logbookId = system.db.runScalarQuery(SQL, database)
    return logbookId