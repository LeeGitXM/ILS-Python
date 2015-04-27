'''
Created on Apr 24, 2015

@author: Pete
'''
import system

# Client startup is contingent on a relationship between the username and the post name.
# For an operator, the username is the same as the post name.
# For an engineer there will not be a matching post.  
def startup():
    print "In ils.common.console.startup()"
    
    username = system.security.getUsername()
    rows = system.db.runScalarQuery("select count(*) from TkPost where post = '%s'" % (username)) 
    if rows > 0:
        system.tag.write("[Client]Post", username)
    else:
        system.tag.write("[Client]Post", "Test")

    SQL = "select C.WindowName from TkConsole C, TkPost P where P.PostId = C.PostId and P.Post = '%s' order by C.priority" % (username)
    pds = system.db.runPrepQuery(SQL)
    for record in pds:
        windowName=record['WindowName']
        print "Opening the ", windowName
        window=system.nav.openWindow(windowName)
        system.nav.centerWindow(window)