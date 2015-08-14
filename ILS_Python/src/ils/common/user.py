'''
Created on Sep 10, 2014

@author: Pete
'''

import system

# TODO This should be site specific
def isOperator():    
    isRole = checkRole('Operator')   
    return isRole

# TODO These should be site specific
def isAE():
    isRole = checkRole('AE')   
    return isRole

def checkRole(ignitionRole):
    myRoles = system.security.getRoles()
    SQL = "Select WindowsRole from RoleTranslation where IgnitionRole = '%s'" % (ignitionRole)
    pds = system.db.runQuery(SQL)
    
    aeRoles = []
    for record in pds:
        role = record['WindowsRole']
        aeRoles.append(str(role))

#    print aeRoles
    for role in myRoles:
#        print "Checking: ", role
        if role in aeRoles:
#            print "Found it!!! %s is a %s" % (role, ignitionRole)
            return True
    
    return False
