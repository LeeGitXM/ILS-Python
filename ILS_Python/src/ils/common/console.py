'''
Created on Apr 24, 2015

@author: Pete
'''
import system


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