'''
Created on Jul 3, 2015

@author: Pete
'''

import system
    
# Fetch all of the labBalerService Data associated with the lab data item
def fetchSinks(source, associationType, db=''):

    SQL = "Select A.sink from TkAssociation A, TkAssociationType AT "\
        " where A.source = '%s' "\
        " and A.AssociationTypeId = AT.AssociationTypeId "\
        " and AT.AssocationType = '%s'" % (source, associationType)
    
    pds = system.db.runQuery(SQL, db)
    sinks=[]
    for record in pds:
        sinks.append(record["sink"])
    return sinks