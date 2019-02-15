'''
Created on Dec 10, 2015

@author: Pete
'''

import system, string
from ils.common.config import getDatabaseClient
log = system.util.getLogger("com.ils.sqc.plotChooser")

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()", __name__)
    
    database=system.tag.read("[Client]Database").value
    log.tracef("The database is: %s", database)
    
    # Populate the list of all consoles - the selected console is passed from the console window and should be in the list
    SQL = "select post from TkPost order by post"
    pds = system.db.runQuery(SQL, database)
    rootContainer.posts=pds

# update the list of display tables that are appropriate for the selected console
def internalFrameActivated(rootContainer):
    log.tracef("In %s.internalFrameActivated()", __name__)
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
    
    SQL = "Select SQCDiagnosisName, Status, SQCDiagnosisUUID, SQCDiagnosisName as LabValueName,SQCDiagnosisName as LabValueDescription, SQCDiagnosisName as ButtonLabel "\
        "from DtSQCDiagnosis SQC, DtFamily F, DtApplication A, TkUnit U, TkPost P "\
        "where SQC.FamilyId = F.FamilyId "\
        " and F.ApplicationId = A.ApplicationId "\
        " and A.UnitId = U. UnitId "\
        " and U.PostId = P.PostId "\
        " and P.Post = '%s' "\
        "Order by SQCDiagnosisName" % (selectedPost)

    log.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    ds = system.dataset.toDataSet(pds)
    
    SQL = "Select ValueName, Description from LtValue"
    LabValuePds = system.db.runQuery(SQL, database)
    
    indexParameter = string.upper(system.tag.read("Configuration/LabData/sqcPlotMenuIndexParameter").value)
    
    from ils.sqc.plot import getLabValueNameFromDiagram
    row = 0
    for record in pds:
        sqcDiagnosisName = record["SQCDiagnosisName"]
        sqcDiagnosisUUID = record["SQCDiagnosisUUID"]
        status =  record["Status"]
        log.tracef("%s - %s", sqcDiagnosisName, status)
        
        ''' Now get the lab value name of the data that feeds the SQC Diagnosis '''
        unitName, labValueName = getLabValueNameFromDiagram(sqcDiagnosisName, sqcDiagnosisUUID)
        log.tracef("...%s - %s", unitName, labValueName)
        ds = system.dataset.setValue(ds, row, "LabValueName", labValueName)
        
        ''' Now update the lab Value Description '''
        for record in LabValuePds:
            if record["ValueName"] == labValueName:
                labValueDescription = record["Description"]
                ds = system.dataset.setValue(ds, row, "LabValueDescription", record["Description"])
        
        if indexParameter == "LABVALUEDESCRIPTION":
            ds = system.dataset.setValue(ds, row, "ButtonLabel", labValueDescription)
        elif indexParameter == "LABVALUENAME":
            ds = system.dataset.setValue(ds, row, "ButtonLabel", labValueName)
        else:
            ds = system.dataset.setValue(ds, row, "ButtonLabel", sqcDiagnosisName)
        
        row = row + 1

    rootContainer.templateParameters = ds


def openSQCPlot(event):
    log.infof("In %s.openSQCPlot()", __name__)
    sqcDiagnosisName = event.source.SQCDiagnosisName
    SQCDiagnosisUUID = event.source.SQCDiagnosisUUID
    openSQCPlotForSQCDiagnosis(sqcDiagnosisName, SQCDiagnosisUUID)


def openSQCPlotForSQCDiagnosis(sqcDiagnosisName, SQCDiagnosisUUID):
    sqcWindowPath='SQC/SQC Plot'
    n = 8
    intervalType = "Hours"
    
    log.infof("The user selected %s - %s ", sqcDiagnosisName, SQCDiagnosisUUID)
    
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
        
def openSQCPlots(sqcDiagnosisNames):
    db = getDatabaseClient()
    pds =system.db.runQuery("select SQCDiagnosisName, SQCDiagnosisUUID from DtSQCDiagnosis", db)
    
    for sqcDiagnosisName in sqcDiagnosisNames:
        SQCDiagnosisUUID = ""
        for record in pds:
            if string.upper(record["SQCDiagnosisName"]) == string.upper(sqcDiagnosisName):
                SQCDiagnosisUUID = record["SQCDiagnosisUUID"]
        openSQCPlotForSQCDiagnosis(sqcDiagnosisName, SQCDiagnosisUUID)
        

'''
Update the status of the SQC diagnosis.  This does not need to do all of the work of a populate.  The database is kept up to date with the 
Status of the SQC Diagnosis block, so all we have to do is query the DB and update the dataset that is driving the repeater.
This entires every SQC diagnosis with a single query,
This runs in client scope every 15 seconds or so from a timer script.
'''
def refresh(rootContainer):
    log.tracef("In %s.refresh()", __name__)
    selectedPost = rootContainer.selectedPost
    database=system.tag.read("[Client]Database").value
    
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
    
    ds=rootContainer.templateParameters
    
    for i in range(ds.rowCount):
        diagnosisName = ds.getValueAt(i, "SQCDiagnosisName")
        for record in pds:
            if diagnosisName == record["SQCDiagnosisName"]:
                log.tracef("Updating the status...")
                ds = system.dataset.setValue(ds, i, "STATUS", record["Status"])
    
    rootContainer.templateParameters=ds