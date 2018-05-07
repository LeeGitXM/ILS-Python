'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def isOperator():    
    isRole = checkRole('Operator')   
    return isRole

def isAE():
    isRole = checkRole('AE')   
    return isRole

def isAdmin():
    isRole = checkRole('Admin')   
    return isRole

def checkRole(ignitionRole):
    myRoles = system.security.getRoles()
    SQL = "Select WindowsRole from RoleTranslation where IgnitionRole = '%s'" % (ignitionRole)
    pds = system.db.runQuery(SQL)
    
    theRoles = []
    for record in pds:
        role = record['WindowsRole']
        theRoles.append(str(role))

#    print aeRoles
    for role in myRoles:
#        print "Checking: ", role
        if role in theRoles:
#            print "Found it!!! %s is a %s" % (role, ignitionRole)
            return True
    
    return False
