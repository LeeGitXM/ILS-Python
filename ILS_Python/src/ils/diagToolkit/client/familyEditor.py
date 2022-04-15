'''
Created on Apr 15, 2022

@author: ils
'''

import system
from ils.common.config import getDatabaseClient

from ils.log import getLogger
log = getLogger(__name__)

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()", __name__)
    db = getDatabaseClient()
    rootContainer = event.source.rootContainer
    SQL = "select FamilyName, Description, FamilyPriority from DtFamily where FamilyId = %d" % (rootContainer.familyId)
    pds = system.db.runQuery(SQL, database=db)
    if len(pds) == 0:
        familyName = ""
        description = ""
        familyPriority = 0.0
    else:
        record = pds[0]
        familyName = record["FamilyName"]
        description = record["Description"]
        familyPriority = record["FamilyPriority"]
    
    rootContainer.familyName = familyName
    rootContainer.description = description
    rootContainer.familyPriority = familyPriority 
        

def saveCallback(event):
    log.infof("In %s.internalFrameOpened()", __name__)
    db = getDatabaseClient()
    rootContainer = event.source.parent
    
    familyId = rootContainer.familyId
    familyName = rootContainer.familyName
    description = rootContainer.description
    familyPriority = rootContainer.familyPriority
    
    if familyId == -1:
        print "Insert a new family"
        SQL = "insert  DtFamily (FamilyName, Description, FamilyPriority) values(?, ?, ?)"
        familyId = system.db.runPrepUpdate(SQL, [familyName, description, familyPriority], database=db)
        rootContainer.familyId = familyId
    else:
        print "Updating..."
        SQL = "update DtFamily set FamilyName = ?, Description = ?, FamilyPriority = ? where FamilyId = ?"
        rows = system.db.runPrepUpdate(SQL, [familyName, description, familyPriority, familyId], database=db)
        print "Updated %d rows" % (rows)
        