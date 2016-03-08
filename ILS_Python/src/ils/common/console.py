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
    window=None
    for record in pds:
        windowName=record['WindowName']
        print "Opening the ", windowName
        window=system.nav.openWindow(windowName)
        system.nav.centerWindow(window)

    # The way this is designed right now, it will only remove unwanted consoles if the user is an operator
    # (If it isn't an operator then there isn't a window, so I'd need to figure out how to get the menubar 
    # without a window.)
    from ils.common.menuBar import getMenuBar, removeUnwantedConsoles
    if window != None:
        menubar = getMenuBar(window)
        removeUnwantedConsoles(menubar)


# This is called by an event handler on each console window.  The main reason for determining the role of the user is to 
# allow the console to be closed by AE's.  (Perhaps I could allow the close button if the username != the post).
def internalFrameOpened(event):
    rootContainer = event.source.rootContainer
    
    username = system.security.getUsername()
    rootContainer.username = username
    
    userRoles = system.security.getRoles()
    if "Admin" in userRoles or "Administrator" in userRoles:
        role = "AE"
    elif "ae" in userRoles or "AE" in userRoles:
        role = "AE"
    else:
        role = "OPERATOR"
    
    rootContainer.role = role