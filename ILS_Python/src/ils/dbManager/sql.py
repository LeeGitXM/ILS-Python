'''
Created on Mar 21, 2017

@author: phass
'''

# Copyright 2014. ILS Automation. All rights reserved.
#
# This module contains a general-purpose scripts used
# for querying and updating the Recipe database

import system
log = system.util.getLogger("com.ils.recipe.sql")

# This method is SQL*Server-specific
def getColumnNames(database,table):        
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

# Given a component on a window, find the window's root container and
# fetch the current transaction id. If there is a current transaction
# then close it.
def closeTransactionForComponent(component):
    root = getRootContainer(component)
    if root!=None:
        txn = root.transaction
        log.info("sql.closeTransaction: TXN=%s" % txn)
        if txn!=None and txn!="0" and len(txn)>0:
            system.db.closeTransaction(txn)

# Given a component on a window, find the window's root container and
# fetch the current transaction id. If there is a current transaction
# in progress, commit and close it.
def commitTransactionForComponent(component):
    root = getRootContainer(component)
    if root!=None:
        txn = root.transaction
        log.info("sql.commitTransaction: TXN=%s" % txn)
        if txn!=None and txn!="0" and len(txn)>0:
            system.db.commitTransaction(txn)

# Open the transaction id lazily. Given a component on a window, 
# find the window's root container and attempt to fetch the
# current transaction id. If it doesn't exist, then begin
# a new one. Set the transaction for a one shift timeout (8 hours).
# TransactionIsolationLevel:
#   READ_UNCOMMITTED     = 1
#   READ_COMMITTED       = 2
#   READ_REPEATABLE_READ = 4
#   SERIALIZABLE         = 6
def getTransactionForComponent(component):
    txn = None
    try:
        root = getRootContainer(component)
        if root!= None:
            txn = root.transaction
            if txn==None or txn=="0" or len(txn)==0:
                txn = system.db.beginTransaction(timeout=8*60*60000)
                root.transaction=txn
                log.info("sql.createTransaction: TXN=%s" % txn)
            else:
                # There is a transaction Id - run a query that we know should succedd to see if it is good.
                try:
                    print "There is a transaction id - checking to see if it is good"
                    SQL = "select count(*) from RtGradeMaster"
                    cnt = system.db.runScalarQuery(SQL, tx=txn)
                    log.info("sql.getTransaction: TXN=%s" % txn)
                except:
                    print "The existing transaction is bad - fetching a new one"
                    txn = system.db.beginTransaction(timeout=8*60*60000)
                    root.transaction=txn
                    log.info("sql.createTransaction: TXN=%s" % txn)
                else:
                    print "The existing transaction id is valid"
    except:
        txn = None
    return txn

def fetchPostsForCombo():
    SQL = "select Post from TkPost order by Post" 
    pds = system.db.runQuery(SQL)
    posts=[]
    for record in pds:
        posts.append( (record["Post"], record["Post"]) )
    print "Posts: ", posts
    return posts

def fetchAnyPost():
    SQL = "select PostId, Post from TkPost order by Post" 
    pds = system.db.runQuery(SQL)
    posts=[]
    for record in pds:
        postId = record["PostId"]
        post = record["Post"]
    return postId, post

# Given the family name, return the Id
def idForFamily(name,txn):
    familyid=system.db.runScalarQuery("SELECT RecipeFamilyId FROM RtRecipeFamily "\
        "WHERE RecipeFamilyName like '"+name+"'",tx=txn)
    return familyid

# Given the post name, return the Id
def idForPost(post,txn):
    id=system.db.runScalarQuery("SELECT PostId FROM TkPost "\
        "WHERE Post like '"+post+"'",tx=txn)
    return id

# Given a component on a window, find the window's root container and
# fetch the current transaction id. If there is a current transaction
# in progress, commit it. Ignore attempts to close a stale transaction.
def rollbackTransactionForComponent(component):
    root = getRootContainer(component)
    if root!=None:
        txn = root.transaction
        if txn!=None and txn!="0" and len(txn)>0:
            try:
                log.info("sql.rollback and close transaction: TXN=%s" % txn)
                system.db.rollbackTransaction(txn)
                system.db.closeTransaction(txn)
            except:
                pass
            root.transaction=""    

def initializeRecipeDatabase():
    tables = ["RtDownloadDetail", "RtDownloadMaster", "RtValueDefinition", "RtGradeDetail", "RtGradeMaster",
        "RtGainGrade", "RtGain", "RtEvent", "RtEventParameter",  
        "RtSQCLimit", "RtSQCParameter", "RtAllowedFlyingSwitch", "RtWatchDog", "RtRecipeFamily"]
    print "Initializing the recipe database..."
    for table in tables:
        SQL = "delete from %s" % (table)
        rows=system.db.runUpdateQuery(SQL)
        print "   ...deleted %i rows from %s..." % (rows, table)
    print "Done!"

# Find the root container component that is, or is the parent
# of the specified component.
def getRootContainer(component):
    while component != None:
        if component.name == "Root Container":
            break
        component = component.parent
    return component