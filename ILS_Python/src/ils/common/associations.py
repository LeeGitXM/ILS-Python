'''
Created on Jul 3, 2015

@author: Pete
'''

import system

# Fetch all of the sources associated with this sink
def fetchSources(sink, associationType='%', db=''):
    SQL = "Select A.source from TkAssociation A, TkAssociationType AT "\
        " where A.sink = '%s' "\
        " and A.AssociationTypeId = AT.AssociationTypeId "\
        " and AT.AssociationType = '%s'" % (sink, associationType)
    
    pds = system.db.runQuery(SQL, db)
    sources=[]
    for record in pds:
        sources.append(record["source"])
    return sources

# Fetch all of the sinks associated with this source
def fetchSinks(source, associationType='%', db=''):
 
    SQL = "Select A.sink from TkAssociation A, TkAssociationType AT "\
        " where A.source = '%s' "\
        " and A.AssociationTypeId = AT.AssociationTypeId "\
        " and AT.AssociationType = '%s'" % (source, associationType)
    
    pds = system.db.runQuery(SQL, db)
    sinks=[]
    for record in pds:
        sinks.append(record["sink"])
    return sinks

def lookupAssociationType(associationType):
    associationTypeId = system.db.runScalarQuery("select associationTypeId from TkAssociationType where AssociationType ='%s' " % (associationType)) 
    return associationTypeId