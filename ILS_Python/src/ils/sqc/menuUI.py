'''
Created on Dec 10, 2015

@author: Pete
'''

import system

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()"
    
    database=system.tag.read("[Client]Database").value
    print "The database is: ", database
    
    # Populate the list of all consoles - the selected console is passed from the console window and should be in the list
    SQL = "select post from TkPost order by post"
    pds = system.db.runQuery(SQL, database)
    rootContainer.posts=pds

# update the list of display tables that are appropriate for the selected console
def internalFrameActivated(rootContainer):
    print "In internalFrameActivated()"
    populateRepeater(rootContainer)

def newPostSelected(rootContainer):
    print "In newPostSelected()"
    populateRepeater(rootContainer)

# Populate the template repeater with the table names for the selected post and page
def populateRepeater(rootContainer):
    print "In populateTablesForConsole"
    selectedPost = rootContainer.selectedPost
    database=system.tag.read("[Client]Database").value
    print "The database is: ", database
    
    SQL = "Select SQCDiagnosisName, Status, BlockId "\
        "from DtSQCDiagnosis SQC, DtFamily F, DtApplication A, TkUnit U, TkPost P "\
        "where SQC.FamilyId = F.FamilyId "\
        " and F.ApplicationId = A.ApplicationId "\
        " and A.UnitId = U. UnitId "\
        " and U.PostId = P.PostId "\
        " and P.Post = '%s' "\
        "Order by SQCDiagnosisName" % (selectedPost)
    
    print SQL
    pds = system.db.runQuery(SQL, database)
    ds = system.dataset.toDataSet(pds)
    repeater=rootContainer.getComponent("Template Repeater")
    repeater.templateParams=ds
