'''
Created on Apr 8, 2016

@author: ils
'''
import system

def showLogbookCallback(event):
    print "In showLogbookCallback()"
    rootContainer = event.source.parent.parent.parent
    post=rootContainer.post
    
    logbook=getLogbookForPost(post)
    from java.util import Calendar
    cal = Calendar.getInstance()
    cal.set(Calendar.HOUR_OF_DAY, 0)
    cal.set(Calendar.MINUTE, 0)
    cal.set(Calendar.SECOND, 0)
    cal.set(Calendar.MILLISECOND, 0)
    startDate = cal.getTime()
    
    logbooks = system.db.runQuery("SELECT LogbookId, LogbookName FROM TkLogbook ORDER BY LogbookName")
    
    print "The post is: <%s> and it uses logbook: <%s>" % (post, logbook)
    
    win = system.nav.openWindowInstance('Logbook/Logbook Viewer', {"logbook": logbook, "startDate": startDate, "logbooks": logbooks})
    system.nav.centerWindow(win)
    
def getLogbookForPost(post):
    SQL = "select LogbookName from TkPost P, TkLogbook L "\
        " where P.logbookId = L.logbookId "\
        " and P.Post = '%s'" % (post)
    logbook = system.db.runScalarQuery(SQL)
    return logbook

def initializeView(rootContainer):
    print "Initializing..."

    print "Done initializing"