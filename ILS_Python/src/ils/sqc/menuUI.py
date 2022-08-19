'''
Created on Dec 10, 2015

@author: Pete
'''

import system, string
from ils.config.client import getDatabase, getTagProvider
from ils.io.util import readTag
from ils.log import getLogger
log = getLogger(__name__)

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()", __name__)
    
    database=readTag("[Client]Database").value
    log.tracef("The database is: %s", database)
    
    # Populate the list of all consoles - the selected console is passed from the console window and should be in the list
    SQL = "select post from TkPost order by post"
    pds = system.db.runQuery(SQL, database)
    log.tracef("...fetched %d posts", len(pds))
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
    log.tracef("In %s.populateRepeater", __name__)
    selectedPost = rootContainer.selectedPost
    database=readTag("[Client]Database").value
    log.tracef("The database is: %s and the selected post is: %s", database, str(selectedPost))
    
    SQL = "Select SQCDiagnosisName, SQCDiagnosisLabel, Status, SQCDiagnosisUUID, SQCDiagnosisName as LabValueName,SQCDiagnosisName as LabValueDescription, SQCDiagnosisName as ButtonLabel "\
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
    
    indexParameter = string.upper(readTag("Configuration/LabData/sqcPlotMenuIndexParameter").value)
    
    from ils.sqc.plot import getLabValueNameFromDiagram
    row = 0
    for record in pds:
        sqcDiagnosisName = record["SQCDiagnosisName"]
        sqcDiagnosisLabel = record["SQCDiagnosisLabel"]
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
            if sqcDiagnosisLabel in ["", None]:
                ds = system.dataset.setValue(ds, row, "ButtonLabel", sqcDiagnosisName)
            else:
                ds = system.dataset.setValue(ds, row, "ButtonLabel", sqcDiagnosisLabel)
        
        row = row + 1

    rootContainer.templateParameters = ds


def openSQCPlot(event):
    log.infof("In %s.openSQCPlot()", __name__)
    sqcDiagnosisName = event.source.SQCDiagnosisName
    SQCDiagnosisUUID = event.source.SQCDiagnosisUUID
    sqcDiagnosisLabel = event.source.ButtonLabel
    openSQCPlotForSQCDiagnosis(sqcDiagnosisName, SQCDiagnosisUUID, sqcDiagnosisLabel)


def openSQCPlotForSQCDiagnosis(sqcDiagnosisName, SQCDiagnosisUUID, sqcDiagnosisLabel):
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
        openWindowInstance(sqcWindowPath, {'sqcDiagnosisName': sqcDiagnosisName,'sqcDiagnosisLabel': sqcDiagnosisLabel, 'sqcDiagnosisUUID': SQCDiagnosisUUID, 'n': n, 'intervalType': intervalType}, mode="CENTER", scale=1.0)
    else:
        provider = getTagProvider()
        scaleFactor = readTag("[%s]Configuration/Common/sqcPlotScaleFactor" % (provider)).value
        openWindowInstance(sqcWindowPath, {'sqcDiagnosisName': sqcDiagnosisName,'sqcDiagnosisLabel': sqcDiagnosisLabel, 'sqcDiagnosisUUID': SQCDiagnosisUUID, 'n': n, 'intervalType': intervalType}, mode="Tile", scale = scaleFactor)


def openSQCPlots(sqcDiagnosisNames):
    '''
    This is called by the predefined SQC plots button which is a shortcut for preconfiguring buttons to show a whole group of SQC plots. 
    '''
    db = getDatabase()
    pds =system.db.runQuery("select SQCDiagnosisName, SQCDiagnosisLabel, SQCDiagnosisUUID from DtSQCDiagnosis", db)
    
    for sqcDiagnosisName in sqcDiagnosisNames:
        sqcDiagnosisUUID = ""
        sqcDiagnosisLabel = sqcDiagnosisName
        
        for record in pds:
            if string.upper(record["SQCDiagnosisName"]) == string.upper(sqcDiagnosisName):
                sqcDiagnosisUUID = record["SQCDiagnosisUUID"]
                sqcDiagnosisLabel = record["SQCDiagnosisLabel"]
                if sqcDiagnosisLabel in ["", None]:
                    sqcDiagnosisLabel = sqcDiagnosisName
        
        openSQCPlotForSQCDiagnosis(sqcDiagnosisName, sqcDiagnosisUUID, sqcDiagnosisLabel)
        

def refresh(rootContainer):
    '''
    Update the status of the SQC diagnosis.  This does not need to do all of the work of a populate.  The database is kept up to date with the 
    Status of the SQC Diagnosis block, so all we have to do is query the DB and update the dataset that is driving the repeater.
    This entires every SQC diagnosis with a single query,
    This runs in client scope every 15 seconds or so from a timer script.
    '''    
    log.tracef("In %s.refresh()", __name__)
    selectedPost = rootContainer.selectedPost
    database=readTag("[Client]Database").value
    
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