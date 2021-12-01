'''
Created on Mar 21, 2017

@author: phass
'''

# Copyright 2014. ILS Automation. All rights reserved.
#
# This module contains a general-purpose scripts used
# for querying and updating the Recipe database

import system
from ils.log.LogRecorder import LogRecorder
from ils.common.config import getDatabaseClient
log = LogRecorder(__name__)

# This method is SQL*Server-specific
def getColumnNames(database, table): 
    # SQL Server 2005 or 2008:
    SQL = "SELECT COLUMN_NAME FROM information_schema.columns WHERE TABLE_NAME like '"+table+"'"
    pds = system.db.runQuery(SQL,database)
    names = []
    for row in pds:
        names.append(row['COLUMN_NAME'])
    return names
    
# This method is SQL*Server-specific
def getTableNames(database):
    # SQL Server 2005 or 2008:
    SQL = "SELECT TABLE_NAME FROM information_schema.tables"
    pds = system.db.runQuery(SQL,database)
    names = []
    for row in pds:
        names.append(row['TABLE_NAME'])
        
    return names


def fetchPostsForCombo():
    db = getDatabaseClient()     
    SQL = "select Post from TkPost order by Post" 
    pds = system.db.runQuery(SQL, database=db)
    posts=[]
    for record in pds:
        posts.append( (record["Post"], record["Post"]) )
    return posts

def fetchAnyPost():
    db = getDatabaseClient()     
    SQL = "select PostId, Post from TkPost order by Post" 
    pds = system.db.runQuery(SQL, database=db)
    for record in pds:
        postId = record["PostId"]
        post = record["Post"]
    return postId, post

# Given the family name, return the Id
def idForFamily(name):
    db = getDatabaseClient()     
    familyid=system.db.runScalarQuery("SELECT RecipeFamilyId FROM RtRecipeFamily "\
        "WHERE RecipeFamilyName like '"+name+"'", database=db)
    return familyid

# Given the family and SQC parameter name, return the Id of the SQC parameter
def idForParameter(familyId, parameterName):
    db = getDatabaseClient()     
    SQL = "SELECT ParameterId FROM RtSQCParameter "\
        "WHERE RecipeFamilyId = %d and Parameter = '%s'"   % (familyId, parameterName)
    parameterId=system.db.runScalarQuery(SQL, database=db)
    return parameterId

# Given the family and Gain parameter name, return the Id of the Gain parameter
def idForGain(familyId, parameterName):
    db = getDatabaseClient()     
    SQL = "SELECT ParameterId FROM RtGain "\
        "WHERE RecipeFamilyId = %d and Parameter = '%s'"   % (familyId, parameterName)
    parameterId=system.db.runScalarQuery(SQL, database=db)
    return parameterId

# Given the post name, return the Id
def idForPost(post):
    db = getDatabaseClient()     
    postId = system.db.runScalarQuery("SELECT PostId FROM TkPost WHERE Post like '"+post+"'", database=db)
    return postId

def initializeRecipeDatabase():
    db = getDatabaseClient()     
    tables = ["RtDownloadDetail", "RtDownloadMaster", "RtValueDefinition", "RtGradeDetail", "RtGradeMaster",
        "RtGainGrade", "RtGain", "RtEvent", "RtEventParameter",  
        "RtSQCLimit", "RtSQCParameter", "RtAllowedFlyingSwitch", "RtWatchDog", "RtRecipeFamily"]
    print "Initializing the recipe database..."
    for table in tables:
        SQL = "delete from %s" % (table)
        rows=system.db.runUpdateQuery(SQL, database=db)
        print "   ...deleted %i rows from %s..." % (rows, table)
    print "Done!"