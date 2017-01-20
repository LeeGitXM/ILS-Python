'''
Created on Dec 10, 2015

@author: Pete
'''

import system
log = system.util.getLogger("com.ils.sqc.plotChooser")

def internalFrameOpened(rootContainer):
    log.info("In internalFrameOpened()")
    
    database=system.tag.read("[Client]Database").value
    log.tracef("The database is: %s", database)
    
    # Populate the list of all consoles - the selected console is passed from the console window and should be in the list
    SQL = "select post from TkPost order by post"
    pds = system.db.runQuery(SQL, database)
    rootContainer.posts=pds

# update the list of display tables that are appropriate for the selected console
def internalFrameActivated(rootContainer):
    log.trace("In internalFrameActivated()")
    populateRepeater(rootContainer)

# update the list of display tables that are appropriate for the selected console
def refresh(rootContainer):
    log.trace("In refresh()")
    populateRepeater(rootContainer)

def newPostSelected(rootContainer):
    log.info("In newPostSelected()")
    populateRepeater(rootContainer)

# Populate the template repeater with the table names for the selected post and page
def populateRepeater(rootContainer):
    log.trace("In populateTablesForConsole")
    selectedPost = rootContainer.selectedPost
    database=system.tag.read("[Client]Database").value
    log.tracef("The database is: %s", database)
    
    SQL = "Select SQCDiagnosisName, Status, SQCDiagnosisUUID "\
        "from DtSQCDiagnosis SQC, DtFamily F, DtApplication A, TkUnit U, TkPost P "\
        "where SQC.FamilyId = F.FamilyId "\
        " and F.ApplicationId = A.ApplicationId "\
        " and A.UnitId = U. UnitId "\
        " and U.PostId = P.PostId "\
        " and P.Post = '%s' "\
        "Order by SQCDiagnosisName" % (selectedPost)
    
    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    
    for record in pds:
        log.tracef("%s - %s", record["SQCDiagnosisName"], record["Status"])

    ds = system.dataset.toDataSet(pds)
    repeater=rootContainer.getComponent("Template Repeater")
    repeater.templateParams=ds

def openSQCPlot(event):
    sqcDiagnosisName = event.source.text
    SQCDiagnosisUUID = event.source.SQCDiagnosisUUID
    openSQCPlotForSQCDiagnosis(sqcDiagnosisName, SQCDiagnosisUUID)


def openSQCPlotForSQCDiagnosis(sqcDiagnosisName, SQCDiagnosisUUID):
    sqcWindowPath='SQC/SQC Plot'
    n = 8
    intervalType = "Hours"
    
    log.tracef("The user selected %s - %s ", sqcDiagnosisName, SQCDiagnosisUUID)
    
    # If this is the first SQC plot open it at full size and centered, if it is the nth plot
    # then open it tiled at 75%
    
    instanceCount = 0
    windows = system.gui.getOpenedWindows()
    for w in windows:
        windowPath = w.getPath()
        if windowPath == sqcWindowPath:
            instanceCount = instanceCount + 1 

    from ils.common.windowUtil import openWindowInstance
    if instanceCount == 0:
        openWindowInstance(sqcWindowPath, {'sqcDiagnosisName': sqcDiagnosisName, 'sqcDiagnosisUUID': SQCDiagnosisUUID, 'n': n, 'intervalType': intervalType}, mode="CENTER", scale=1.0)
    else:
        openWindowInstance(sqcWindowPath, {'sqcDiagnosisName': sqcDiagnosisName, 'sqcDiagnosisUUID': SQCDiagnosisUUID, 'n': n, 'intervalType': intervalType}, mode="Tile", scale = 0.75)
        