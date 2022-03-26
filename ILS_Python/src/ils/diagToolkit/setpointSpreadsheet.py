'''
Created on Sep 9, 2014

@author: ILS
'''

import system, string
from ils.sfc.common.constants import SQL
from ils.common.constants import CR
from ils.diagToolkit.constants import OBSERVATION_BLOCK_LIST
from ils.common.operatorLogbook import insertForPost
from ils.queue.message import insertPostMessage
from ils.queue.constants import QUEUE_INFO
from ils.common.config import getDatabaseClient, getTagProviderClient
from ils.common.util import dsToText
from ils.diagToolkit.common import fetchFamilyNameForFinalDiagnosisId, stripClassPrefix,\
    fetchRecommendationsForOutput
from ils.diagToolkit.constants import WAIT_FOR_MORE_DATA, AUTO_NO_DOWNLOAD, DOWNLOAD, NO_DOWNLOAD
from ils.diagToolkit.api import resetManualMove

from ils.log import getLogger
log=getLogger(__name__)

def initialize(rootContainer):
    log.infof("In %s.initialize()...", __name__)
    rootContainer.initializationComplete = False
    rootContainer.recalculateFlag = False
    rootContainer.lastAction = "opened"
    rootContainer.initializationTime = system.date.now()
    refresh(rootContainer)


def refresh(rootContainer):
    log.infof("In %s.refresh()...", __name__)
    db=system.tag.read("[Client]Database").value
    
    post = rootContainer.post
    fetchAndSetDownloadActiveFlag(rootContainer, post, db)
    repeater = rootContainer.getComponent("Template Repeater")
    
    ds = getSetpointSpreadsheetDataset(post, db)
    repeater.templateParams=ds
    repeater.selectedRow = -1

    #----------------------------------------------------------
    def initializationComplete(rootContainer=rootContainer):
        log.tracef("Setting initializationComplete to TRUE")
        rootContainer.initializationComplete = True
    #----------------------------------------------------------

    system.util.invokeLater(initializationComplete, 1000)


def getSetpointSpreadsheetDataset(post, db):
    log.infof("In %s.getSetpointSpreadsheetDataset() using %s...", __name__, db)
    from ils.diagToolkit.common import fetchActiveOutputsForPost
    pds = fetchActiveOutputsForPost(post, db)
    log.infof("...fetched %d active outputs", len(pds))
    
    # Create the data structures that will be used to make the dataset the drives the template repeater
    header=['type','row','selected','qoId','command','commandValue','application','output','tag','setpoint','manualOverride','recommendation','finalSetpoint','status','downloadStatus','numberFormat','ramp']
    rows=[]
    # The data types for the column is set from the first row, so I need to put floats where I want floats, even though they don't show up for the header
    row = ['header',0,0,0,'Action',0,'','Outputs','',1.2,False,1.2,1.2,'','','',""]
    rows.append(row)
    
    application = ""
    i = 1
    for record in pds:
        log.infof("%s - %s - %s - %s - %s - %s - %s - %s - %s - %s - %s - %s - %s - %s - %s - %s - %s", \
                  record['ApplicationName'], record["QuantOutputName"], record["TagPath"], record["OutputLimitedStatus"], record["OutputLimited"], \
                  str(record["FeedbackOutput"]), str(record["FeedbackOutputManual"]), str(record["FeedbackOutputConditioned"]), str(record["ManualOverride"]), \
                  str(record["IncrementalOutput"]), str(record["CurrentSetpoint"]), str(record["FinalSetpoint"]), str(record["DisplayedRecommendation"]), str(record["QuantOutputId"]), \
                  str(record["DownloadAction"]), str(record["DownloadStatus"]), str(record["Ramp"]))
        
        # If the record that we are processing is for a different application, or if this is the first row, then insert an application divider row
        if record['ApplicationName'] != application:
            # Remember the row number of the application because we will need to update the status if we encounter
            # any minimum change bound outputs
            applicationRowNumber = i
            minChangeBoundCount = 0
             
            application = record['ApplicationName']
            downloadAction = fetchApplicationDownloadAction(application, db)
            if string.upper(downloadAction) == 'ACTIVE':
                actionValue = 0
            else:
                actionValue = 1
            applicationRow = ['app',i,0,0,downloadAction,actionValue,application,'','',0,False,0,0,'','','',""]
            log.tracef("Appending application row: %s", str(applicationRow))
            rows.append(applicationRow)
            i = i + 1

        outputLimited = record['OutputLimited']
        outputLimitedStatus = record['OutputLimitedStatus']
        if outputLimitedStatus == 'Positive Incremental Bound':
            statusMessage='<HTML>CLAMPED<br>(+ Incr)'
        elif outputLimitedStatus == 'Negative Incremental Bound':
            statusMessage='<HTML>CLAMPED<br>(- Incr)'
        elif outputLimitedStatus == 'Positive Absolute Bound':
            statusMessage='<HTML>CLAMPED<br>(High)'
        elif outputLimitedStatus == 'Negative Absolute Bound':
            statusMessage='<HTML>CLAMPED<br>(Low)'
        elif outputLimitedStatus == 'Vector':
            statusMessage='<HTML>CLAMPED<br>(Vector)'
        elif outputLimitedStatus == 'Minimum Change Bound':
            statusMessage='<HTML>CLAMPED<br>(Min Change)'
            minChangeBoundCount = minChangeBoundCount + 1
            if minChangeBoundCount == 1:
                applicationRow[13]="%i output < minimum change" % (minChangeBoundCount)
            else:
                applicationRow[13]="%i outputs < minimum change" % (minChangeBoundCount)
            rows[applicationRowNumber]=applicationRow
        else:
            statusMessage=''
        
        # Regardless of whether the quant output is incremental or absolute, the recommendation displayed on 
        # the setpoint spreadsheet is ALWAYS incremental.  In fact, the feedbackOutput that is stored in the 
        # QuantOutput table is always incremental.
        # If the recommended change is insignificant (< the minimum change) then don't display it, but we do 
        # want to update the status field of the Application line
        if outputLimitedStatus != 'Minimum Change Bound':
            # Determine the number format dynamically by reading the number format of the tag
            tagPath = record["TagPath"]
            numberPattern= system.tag.read(tagPath + ".FormatString").value
            
            action = record['DownloadAction']
    
            if action == 'GO':
                actionValue = 0
            else:
                actionValue = 1

            row = ['row',i,0,record['QuantOutputId'],action,actionValue,application,record['QuantOutputName'],record['TagPath'],record['CurrentSetpoint'],
                   record['ManualOverride'],record['DisplayedRecommendation'],record['FinalSetpoint'],statusMessage,record['DownloadStatus'],numberPattern, str(record['Ramp'])]
            log.tracef("Appending row: %s", str(row))
            rows.append(row)
            i = i + 1

    ds = system.dataset.toDataSet(header, rows)
    return ds

# This is called by a timer script that runs when a download is active.  It determines if the download is complete by checking for a terminal
# download status (Error or Success) in each of the outputs that are marked as GO 
def checkIfDownloadComplete(event):
    rootContainer = event.source.parent
    log.infof("Checking if the download is complete...")
    downloadComplete = True
    
    repeater=rootContainer.getComponent("Template Repeater")
    ds = repeater.templateParams
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")
        if rowType == "row":
            command=ds.getValueAt(row, "command")
            if string.upper(command) == 'GO':
                downloadStatus=ds.getValueAt(row, "downloadStatus")
                if downloadStatus not in ['Error', 'Success']:
                    log.tracef("   ...found an output still working on row: %d ", row)
                    downloadComplete = False

    # Only update the database if downloadComplete is True, we assume it is True since this is running
    if downloadComplete:
        log.infof("...the download is complete...")
        
        ''' Make a logbook message for the download BEFORE we reset the FDs in the DB '''
        post = rootContainer.post
        db = getDatabaseClient()
        tagProvider = getTagProviderClient()
        
        from ils.diagToolkit.downloader import Downloader
        downloader = Downloader(post, ds, tagProvider, db)
        downloader.downloadMessage(messageType="download")
        insertForPost(post, downloader.logbookMessage, db)
        
        ''' Now get to work '''
        rootContainer.downloadActive = False
        db=system.tag.read("[Client]Database").value
        db=getDatabaseClient()
        tagProvider=getTagProviderClient()
        updateDownloadActiveFlag(rootContainer.post, False, db)
        
        # If all of the downloads were successful, then dismiss the setpoint spreadsheet
        writesWereSuccessful = True
        ds = repeater.templateParams
        for row in range(ds.rowCount):
            rowType=ds.getValueAt(row, "type")
            if rowType == "row":
                command=ds.getValueAt(row, "command")
                if string.upper(command) == 'GO':
                    downloadStatus=ds.getValueAt(row, "downloadStatus")
                    if downloadStatus not in ['Success', '']:
                        writesWereSuccessful = False

        if writesWereSuccessful:
            log.infof("...all of the writes were successful, resetting diagrams and checking if all applications were processed...")
            allApplicationsProcessed=postCallbackProcessing(rootContainer, ds, db, tagProvider, actionMessage=DOWNLOAD, recommendationStatus=DOWNLOAD)
        
            # If they disabled some applications then leave the spreadsheet open, otherwise dismiss it
            if allApplicationsProcessed:
                log.infof("...all applications were processed, closing the setpoint spreadsheet...")
                system.nav.closeParentWindow(event)
            else:
                log.infof("...not all applications were processed, hide the spreadsheet but leave the window open...")
                rootContainer.recalculateFlag = True
    
# This is called from the cliant when they press the STOP / GO action button an a row of the spreadsheet.  This updates the database so that we can synchronize another client
def updateQuantOutputAction(rootContainer, ds, row, action):
    log.info("Updating the database with the QuantOutput action...")
    database=system.tag.read("[Client]Database").value
    quantOutputId = ds.getValueAt(row, 'qoId')
    SQL = "update DtQuantOutput set DownloadAction = '%s' where QuantOutputId = %i " % (action, quantOutputId)
    system.db.runUpdateQuery(SQL, database)

# This fetches the flag from the TkPost table and sets the flag on the rootContainer
def fetchAndSetDownloadActiveFlag(rootContainer, post, db):
    SQL = "select DownloadActive from TkPost where Post = '%s'" % (post)
    downloadActive = system.db.runScalarQuery(SQL, db)
    rootContainer.downloadActive = downloadActive
    
# This is called from the download.py (client scope) when the download starts and from here when the download is done.
def updateDownloadActiveFlag(post, state, db):
    from ils.common.cast import toBit
    state = toBit(state)
    SQL = "update TkPost set DownloadActive = %d where Post = '%s'" % (state, post)
    system.db.runUpdateQuery(SQL, db)

def resetAllApplicationAndOutputActions(rootContainer):
    log.infof("Resetting the action of all applications")
    repeater = rootContainer.getComponent("Template Repeater")
    ds = repeater.templateParams
    pds = system.dataset.toPyDataSet(ds)
    row = 0
    for record in pds:
        if record[0] == 'app':
            updateApplicationAction(rootContainer, ds, row, "ACTIVE")
        elif record[0] == 'row':
            updateQuantOutputAction(rootContainer, ds, row, "GO")
        else:
            log.tracef("skipped a %s", str(record[0]))
            
        row = row + 1

    
# This is called from the cliant when they press the STOP / GO action button an a row of the spreadsheet.  This updates the database so that we can synchronize another client
def updateApplicationAction(rootContainer, ds, row, action):
    log.info("Updating the database with the application action...")
    database=system.tag.read("[Client]Database").value
    applicationName = ds.getValueAt(row, 'application')
    SQL = "update DtApplication set DownloadAction = '%s' where ApplicationName = '%s'" % (string.upper(action), applicationName)
    system.db.runUpdateQuery(SQL, database)

def fetchApplicationDownloadAction(applicationName, db):
    log.tracef("In %s.fetchApplicationDownloadAction() using %s", __name__, db)
    SQL = "select DownloadAction from DtApplication where applicationName = '%s'" % (applicationName)
    log.tracef(SQL)
    downloadAction = system.db.runScalarQuery(SQL, db)
    log.tracef("Fetched %s for %s", downloadAction, applicationName)
    return downloadAction

def writeFileCallback(rootContainer):
    log.tracef("In %s.writeFileCallback()...", __name__)
    logFileName=system.file.openFile('*.log')
    if logFileName <> None:
        writeFile(rootContainer, logFileName)

# The state of the diagnosis / recommendations are written to a file for various reasons, including from the toolbar button 
# and as part of a download request.  The contents of the file are not simply the lines of the spreadsheet, in order to keep
# the same format as the old platform, we need to query the database and get the data that was used to build the spreadsheet.
def writeFile(rootContainer, filepath):
    log.tracef("In %s.writeFile() to %s", __name__, filepath)
    post = rootContainer.post

    exists=system.file.fileExists(filepath)
    if not(exists):
        log.warnf("Write some sort of new file header")

    from ils.diagToolkit.common import fetchApplicationsForPost
    applicationPDS = fetchApplicationsForPost(post)
    for applicationRecord in applicationPDS:
        application=applicationRecord['ApplicationName']
        system.file.writeFile(filepath, "    Application: %s\n" % (application), True)
        
        from ils.diagToolkit.common import fetchActiveDiagnosis
        finalDiagnosisPDS=fetchActiveDiagnosis(application)
        for finalDiagnosisRecord in finalDiagnosisPDS:
            family=finalDiagnosisRecord['FamilyName']
            finalDiagnosis=finalDiagnosisRecord['FinalDiagnosisName']
            finalDiagnosisId=finalDiagnosisRecord['FinalDiagnosisId']
            multiplier=finalDiagnosisRecord['Multiplier']
            recommendationErrorText=finalDiagnosisRecord['RecommendationErrorText']
            log.tracef("Final Diagnosis: %s - %d - %s", finalDiagnosis, finalDiagnosisId, recommendationErrorText)
            
            if multiplier < 0.99 or multiplier > 1.01:
                system.file.writeFile(filepath, "       Diagnosis -- %s (multiplier = %f)\n" % (finalDiagnosis, multiplier), True)
            else:
                system.file.writeFile(filepath, "       Diagnosis -- %s\n" % (finalDiagnosis), True)

            if recommendationErrorText != None:
                system.file.writeFile(filepath, "       %s\n\n" % (recommendationErrorText), True) 

            from ils.diagToolkit.common import fetchSQCRootCauseForFinalDiagnosis
            rootCauseList=fetchSQCRootCauseForFinalDiagnosis(finalDiagnosis)
            for rootCause in rootCauseList:
                log.tracef("Root cause: %s", str(rootCause))

            from ils.diagToolkit.common import fetchOutputsForFinalDiagnosis
            pds, outputs=fetchOutputsForFinalDiagnosis(application, family, finalDiagnosis)
            for record in outputs:
                quantOutput = record.get('QuantOutput','')
                tagPath = record.get('TagPath','')
                feedbackOutput=record.get('FeedbackOutput',0.0)
                feedbackOutputConditioned = record.get('FeedbackOutputConditioned',0.0)
                manualOverride=record.get('ManualOverride', False)
                outputLimited=record.get('OutputLimited', False)
                outputLimitedStatus=record.get('OutputLimitedStatus', '')
    
                txt = "          the desired change in %s = %f" % (tagPath, feedbackOutput)
                if manualOverride:
                    txt = "%s  (manually specified)" % (txt)
                system.file.writeFile(filepath, txt + "\n", True)

                if outputLimited and feedbackOutput != 0.0:
                    txt = "          change to %s returnadjusted to %f because %s" % (quantOutput, feedbackOutputConditioned, outputLimitedStatus)


def detailsCallback(rootContainer):
    post = rootContainer.post
    repeater=rootContainer.getComponent("Template Repeater")
    
    # Check if there is a selected row (could be an app or a quant output
    selectedRow=repeater.selectedRow
    if selectedRow < 0:
        system.gui.warningBox("Please select a row first")
        return
    
    # Get the quant output for the row
    ds = repeater.templateParams
    quantOutputId=ds.getValueAt(selectedRow, 'qoid')
    quantOutputName=ds.getValueAt(selectedRow, 'output')
    applicationName= ds.getValueAt(selectedRow, 'application')
    
    system.nav.openWindowInstance('DiagToolkit/Recommendation Map', {'applicationName': applicationName, 'quantOutputName': quantOutputName, 'post': post})
    system.nav.centerWindow('DiagToolkit/Recommendation Map')

# This is called when the operator selects a cell in the "Status" column
def statusCallback(event):
    label=event.source
    container=label.parent
    template=container.parent
    row=template.row

    window=system.gui.getParentWindow(event)
    rootContainer=window.rootContainer
    
    repeater=rootContainer.getComponent("Template Repeater")
    
    # Get the quant output for the row
    ds = repeater.templateParams
    quantOutputId=ds.getValueAt(row, 'qoid')

    # Fetch everything about the quant output from the database
    from ils.diagToolkit.common import fetchQuantOutput
    pds = fetchQuantOutput(quantOutputId)
    if len(pds) == 0:
        system.gui.warningBox("The Quant Output was not found")
        return
    
    if len(pds) > 1:
        system.gui.warningBox("Multiple quant outputs were found where only one was expected!")
        return

    # Format the information
    record=pds[0]
    quantOutputName = record['QuantOutputName']   
    outputLimited=record['OutputLimited']
    outputLimitedStatus=record['OutputLimitedStatus']
    mostNegativeIncrement=record['MostNegativeIncrement']
    mostPositiveIncrement=record['MostPositiveIncrement']
    minimumIncrement=record['MinimumIncrement']
    setpointHighLimit=record['SetpointHighLimit']
    setpointLowLimit=record['SetpointLowLimit']
    
    limitDetails = "The Output limit details are:\n  Max Positive Change: %f\n"\
            "  Max Negative Change: %f\n  Min Change: %f\n  Max Setpoint: %f\n  Min Setpoint: %f" \
            % (mostPositiveIncrement, mostNegativeIncrement, minimumIncrement, setpointHighLimit, setpointLowLimit)
    
    if outputLimited:
        if outputLimitedStatus == 'Vector':
            txt = "The output (%s) is %s limited!\n\nthe final setpoint was reduced from %.2f to %.2f because the most bound output "\
                "could only use %.0f%% of its value" % (quantOutputName, outputLimitedStatus, record['FeedbackOutput'], \
                                                    record['FeedbackOutputConditioned'], record['OutputPercent'])
        else:
            txt = "The output (%s) is %s limited,\nthe final setpoint was reduced from %.2f to %.2f\n\n%s" % \
                (quantOutputName, outputLimitedStatus, record['FeedbackOutput'], record['FeedbackOutputConditioned'], limitDetails)
    else:
        txt = "The output (%s) is not limited!\n\n%s" % (quantOutputName, limitDetails)
    
    title = "Output Details"

    system.gui.messageBox(txt, title)

# This is called from the recalc button on the setpoint spreadsheet
def recalcCallback(event):
    log.infof("In %s.recalcCallback()", __name__)
    rootContainer=event.source.parent
    rootContainer.recalculateFlag=True
    post=rootContainer.post
    database=system.tag.read("[Client]Database").value
    tagProvider=system.tag.read("[Client]Tag Provider").value
    
    # Don't do a recalc if there is a download in progress
    if rootContainer.downloadActive:
        log.infof("...exiting because a download is active!")
        return
    
    repeater=rootContainer.getComponent("Template Repeater")
    logAction("RECALC", repeater)
    
    activeApplication = isThereAnActiveApplication(repeater)
    if not(activeApplication):
        log.infof("...exiting because the application is not active!")
        return
    
    ds=repeater.templateParams

    applications = []
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")

        if string.upper(rowType) == "APP":
            command=ds.getValueAt(row, "command")

            if string.upper(command) == 'ACTIVE':
                application=ds.getValueAt(row, "application")
                if application not in applications:
                    applications.append(application)

    log.infof("Sending a RECALC message to the gateway for post: %s, applications: %s (database: %s)", post, str(applications), database)
    projectName=system.util.getProjectName()
    payload={"post": post, "database": database, "provider": tagProvider, "applications": applications}
    log.infof("   the payload is: %s", str(payload))
    system.util.sendMessage(projectName, "recalc", payload, "G")  


# This is called from the Recalc Refresh Timer on the setpoint spreadsheet.  It runs every 10 seconds or so.
# If it finds any Final Diagnosis on the spreadsheet it will recalculate all active FDs.  It is possible that multiple FDs
# are active, I don't think I can do any harm by recalculating too often.  In reality, most problems all have the same 
# refresh time anyway.
def recalcTimer(event):
    rootContainer = event.source.parent
    log.tracef("Checking the recalculation timer...") 
    
    #--------------------------------------------------------
    def checkRecalcTime(projectName, applicationName, finalDiagnosisIds):
        
        log.tracef("Checking recalculate application: %s, FDs: %s", applicationName, str(finalDiagnosisIds))

        recalculateFlag = False
        for finalDiagnosisId in finalDiagnosisIds:
            SQL = "select LastRecommendationTime, RefreshRate from DtFinalDiagnosis where FinalDiagnosisId = %s" % (str(finalDiagnosisId))
            pds = system.db.runQuery(SQL, db)
            if len(pds) == 1:
                record = pds[0]
            else:
                raise ValueError, "Fetched %d records when exactly one was expected" % (len(pds))
    
            lastRecommendationTime = record["LastRecommendationTime"]
            refreshRate = record["RefreshRate"]
            log.tracef("    Final Diagnosis Id: %s, last Recomendation time: %s, refresh rate: %s", str(finalDiagnosisId), str(lastRecommendationTime), str(refreshRate))

            # The refresh rate is in minutes
            minutesSinceLastCalc = system.date.minutesBetween(lastRecommendationTime, system.date.now())
            if minutesSinceLastCalc > refreshRate:
                log.infof("*** It is time to recalc ***")
                recalculateFlag = True
    
        return recalculateFlag
        
    #--------------------------------------------------------
    
    # Don't do a recalc if there is a download in progress
    if rootContainer.downloadActive:
        return

    db=getDatabaseClient()
    projectName=system.util.getProjectName()
    repeater=rootContainer.getComponent("Template Repeater")
    
    activeApplication = isThereAnActiveApplication(repeater)
    if not(activeApplication):
        return
    
    ds=repeater.templateParams

    finalDiagnosisIds=[]
    quantOutputIds=[]
    applicationName = ""
    applications = []
    applicationActive = False
    
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")

        if string.upper(rowType) == "APP":
            if len(finalDiagnosisIds) > 0:
                recalc = checkRecalcTime(projectName, applicationName, finalDiagnosisIds)
                if recalc:
                    applications.append(applicationName)
            
            command=ds.getValueAt(row, "command")

            if string.upper(command) == 'ACTIVE':
                applicationActive=True
                applicationName=ds.getValueAt(row, "application")
            else:
                applicationActive=False

        elif string.upper(rowType) == "ROW":
            if applicationActive:
                quantOutputId=ds.getValueAt(row, "qoId")
                if quantOutputId not in quantOutputIds:
                    quantOutputIds.append(quantOutputId)
                    
                    from ils.diagToolkit.common import fetchActiveFinalDiagnosisForAnOutput
                    pds=fetchActiveFinalDiagnosisForAnOutput(applicationName, quantOutputId, db)
                    for rec in pds:
                        if rec["FinalDiagnosisId"] not in finalDiagnosisIds:
                            finalDiagnosisIds.append(rec["FinalDiagnosisId"])

    if len(finalDiagnosisIds) > 0:
        recalc = checkRecalcTime(projectName, applicationName, finalDiagnosisIds)
        if recalc:
            applications.append(applicationName)

    # If any application needs recalculating send a message to the gateway and post the recalculating banner on the setpoint spreadsheet            
    if len(applications):
        rootContainer.recalculateFlag=True
        post=rootContainer.post
        tagProvider=system.tag.read("[Client]Tag Provider").value
        payload={"post": post, "database": db, "provider": tagProvider, "applications": [applicationName]}
        log.infof("Sending a RECALC message to the gateway to manage applications: %s (database: %s)", str(payload), db)
        system.util.sendMessage(projectName, "recalc", payload, "G")  
    
    
# This is called from the WAIT button on the set-point spreadsheet
def waitCallback(event):
    log.infof("In %s.waitCallback() processing a WAIT-FOR-MORE-DATA...", __name__)
    rootContainer=event.source.parent
    post = rootContainer.post

    db=getDatabaseClient()
    tagProvider=getTagProviderClient()
    repeater=rootContainer.getComponent("Template Repeater")
    logAction("WAIT", repeater)
    
    activeApplication = isThereAnActiveApplication(repeater)
    if activeApplication:
        ds = repeater.templateParams
        
        # Write something useful to the logbook to document this No Download
        from ils.diagToolkit.downloader import Downloader
        downloader = Downloader(post, ds, tagProvider, db)
        downloader.downloadMessage(messageType="wait")
        insertForPost(post, downloader.logbookMessage, db)
    
        allApplicationsProcessed = postCallbackProcessing(rootContainer, ds, db, tagProvider, actionMessage=WAIT_FOR_MORE_DATA, recommendationStatus=WAIT_FOR_MORE_DATA)

        # If they disabled some applications then leave the spreadsheet open, otherwise dismiss it
        if allApplicationsProcessed:
            system.nav.closeParentWindow(event)


# This is called from the NO DOWNLOAD button on the set-point spreadsheet
def noDownloadCallback(event):
    log.infof("In %s.noDownloadCallback() processing a NO-DOWNLOAD...", __name__)
    rootContainer=event.source.parent
    post = rootContainer.post
    
    hideDetailMap()

    db=getDatabaseClient()
    tagProvider=getTagProviderClient()
    repeater=rootContainer.getComponent("Template Repeater")
    logAction("NO DOWNLOAD", repeater)
    
    activeApplication = isThereAnActiveApplication(repeater)
    if activeApplication:
        log.tracef("There IS an active application...")
        ds = repeater.templateParams
        
        # Write something useful to the logbook to document this No Download        
        from ils.diagToolkit.downloader import Downloader
        downloader = Downloader(post, ds, tagProvider, db)
        downloader.downloadMessage(messageType="no_download")
        insertForPost(post, downloader.logbookMessage, db)
    
        # Set a flag that will be used when the notification arrives.  This is only relevent when two applications are present but one of them was INACTIVE
        rootContainer.lastAction = "noDownload"
        
        # Now do the work of the NO Download
        allApplicationsProcessed=postCallbackProcessing(rootContainer, ds, db, tagProvider, actionMessage=NO_DOWNLOAD, recommendationStatus=NO_DOWNLOAD)
    
        # If they disabled some applications then leave the spreadsheet open, otherwise dismiss it
        if allApplicationsProcessed:
            system.nav.closeParentWindow(event)

'''
This is called when the operator does a download or a No Download.  It closes any open recommendation maps that are open on the client.
It does not check other clients.  It doesn't worry about if the operator only selected one output or application.
'''
def hideDetailMap():
    windows = system.gui.getOpenedWindows()
    for window in windows:
        if window.getPath() == "DiagToolkit/Recommendation Map":
            system.nav.closeWindow(window)


def isThereAnActiveApplication(repeater):
    ds = repeater.templateParams
    
    active = False
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")

        if string.upper(rowType) == "APP":
            command=ds.getValueAt(row, "command")
            if string.upper(command) == 'ACTIVE':
                active = True

    return active

# This is called when we do a "No Download" or "Wait For More Data".
# Use the action message to determine which button was pressed and exactly how much processing to do.
# Reset the database tables and the BLT diagrams for every application that is active.
# We do not consider individual outputs that the operator may have chosen to not download.   
def postCallbackProcessing(rootContainer, ds, db, tagProvider, actionMessage, recommendationStatus):
    log.infof("In %s.postCallbackProcessing(), performing generic post callback cleanup for a <%s>...", __name__, actionMessage)
    allApplicationsProcessed=True
    post=rootContainer.post
    applicationActive=False
    application=""
    families=[]
    finalDiagnosisIds=[]
    quantOutputIds=[]
    applications=[]
    
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")

        if string.upper(rowType) == "APP":
            command=ds.getValueAt(row, "command")

            if string.upper(command) == 'ACTIVE':
                if application != "":
                    ''' We fall into here if we have multiple applications in the spreadsheet and we just finished one and are now starting to look at the next one.  So this processes the previous one.'''
                    resetter(post, application, families, finalDiagnosisIds, quantOutputIds, actionMessage, recommendationStatus, db, tagProvider)
                    applications.append(application)

                families=[]
                finalDiagnosisIds=[]
                quantOutputIds=[]
                
                applicationActive=True
                application=ds.getValueAt(row, "application")
            else:
                applicationActive=False
                allApplicationsProcessed=False
                log.infof("Updating the DownloadAction for application <%s> to <ACTIVE>", ds.getValueAt(row, "application"))
                SQL = "update DtApplication set downloadAction = 'ACTIVE' where ApplicationName = '%s'" % (ds.getValueAt(row, "application"))
                system.db.runUpdateQuery(SQL, db)

        elif string.upper(rowType) == "ROW":
            if applicationActive:
                quantOutputId=ds.getValueAt(row, "qoId")
                if quantOutputId not in quantOutputIds:
                    quantOutputIds.append(quantOutputId)
                    
                    from ils.diagToolkit.common import fetchActiveFinalDiagnosisForAnOutput
                    pds=fetchActiveFinalDiagnosisForAnOutput(application, quantOutputId, db)
                    
                    if len(pds) ==0:
                        log.tracef("...no ACTIVE final diagnosis were found for quantOutputId %s, looking for ANY final diagnosis...", str(quantOutputId))
                        from ils.diagToolkit.common import fetchAnyFinalDiagnosisForAnOutput
                        pds=fetchAnyFinalDiagnosisForAnOutput(application, quantOutputId, db)
                        
                    for rec in pds:
                        if rec["FinalDiagnosisId"] not in finalDiagnosisIds:
                            finalDiagnosisIds.append(rec["FinalDiagnosisId"])
                        if rec["FamilyName"] not in families:
                            families.append(rec["FamilyName"])
            else:
                log.infof("Checking quant output for an application that is not active...")
                quantOutputId=ds.getValueAt(row, "qoId")
                log.infof("Updating the DownloadAction for quant output <%s> to <GO>", str(quantOutputId))
                SQL = "update DtQuantOutput set downloadAction = 'GO' where QuantOutputId = %s" % ( str(quantOutputId) )
                system.db.runUpdateQuery(SQL, db)

    resetter(post, application, families, finalDiagnosisIds, quantOutputIds, actionMessage, recommendationStatus, db, tagProvider)
    
    # Refresh the spreadsheet - This needs to be done in a general way that will update the spreadsheet 
    # that may be displayed on multiple clients.  This callback is running in a client, if I just call 
    # initialize it will just update this client.  Because the database and blocks have been reset,
    # I should be able to call recalc in the gateway which will notify client to update the spreadsheet
    log.infof("Sending a message to manage applications for post: %s (database: %s)", post, db)
    projectName=system.util.getProjectName()
    payload={"post": post, "database": db, "provider": tagProvider, "applications": applications}
    system.util.sendMessage(projectName, "recalc", payload, "G")
    
    from ils.diagToolkit.finalDiagnosis import requestToManage
    requestToManage(application, db, tagProvider)
    
    log.infof("...done post action processing!")
    return allApplicationsProcessed


def resetter(post, application, families, finalDiagnosisIds, quantOutputIds, actionMessage, recommendationStatus, db, tagProvider):
    from ils.diagToolkit.common import fetchQuantOutputsForFinalDiagnosisIds
    log.infof("In %s.resetter(), the action is %s", __name__, actionMessage)
    log.tracef("...the original quantOutputIds are: %s", str(quantOutputIds))
        
    if len(finalDiagnosisIds) == 0:
        log.infof("...did not find any finalDiagnosis in the spreadsheet, fetching for all active ones...")
        from ils.diagToolkit.common import fetchActiveDiagnosis
        pds = fetchActiveDiagnosis(application, db)
        finalDiagnosisIds=[]
        for record in pds:
            finalDiagnosisIds.append(record["FinalDiagnosisId"])

    log.infof("Resetting: ")
    log.infof("   Application: %s", application)
    log.infof("   Families: %s", str(families))
    log.infof("   FDs:%s", str(finalDiagnosisIds))
    
    ''' The list of quant outputs that are passed in are only the ones with significant recommendations, we want ALL of the quant outputs, even if they made insignificant recommendations '''
    quantOutputIds=fetchQuantOutputsForFinalDiagnosisIds(finalDiagnosisIds)

    resetApplication(post, application, families, finalDiagnosisIds, quantOutputIds, actionMessage, recommendationStatus, db, tagProvider)

'''
July 25, 2018 - I ran into a infinite loop problem when I try and reset everything after a rate change download.  The reset is triggered from each of the 4 
rate change final diagnosis.  So when any one of them is active and the operator presses download and the download completes, we call its postProcessing callback
which collects all FDs in RLA3 and resets them all.  Part of resetting a FD is to call its postProcessingFinalDiagnosis... and so on and so on!
So I'm not sure if it is really appropriate to do this here or not, seems like there might be a better place to call this from, but I don't want to break a 
bunch of stuff, so I am going to add an optional argument: enablePostProcessingCallback with a default value of True
'''
def resetApplication(post, application, families, finalDiagnosisIds, quantOutputIds, actionMessage, recommendationStatus, database, provider, enablePostProcessingCallback=True):
    log.infof("In %s.resetApplication() resetting application %s because %s - %s", __name__, application, actionMessage, recommendationStatus)
    log.trace("  Families: %s" % (str(families)))
    log.trace("  Final Diagnosis Ids: %s" % (str(finalDiagnosisIds)))
    log.trace("  Quant Output Ids: %s" % (str(quantOutputIds)))

    # Post a message to the applications queue documenting what we are doing to the active families    
    postSetpointSpreadsheetActionMessage(post, families, finalDiagnosisIds, actionMessage, recommendationStatus, database)

    # Perform all of the database updates necessary to update the affected FDs, 
    # Quant Outputs, recommendations, and diagnosis entries.

    resetOutputs(quantOutputIds, actionMessage, log, database)
    resetRecommendations(quantOutputIds, actionMessage, log, database)
    resetFinalDiagnosis(application, actionMessage, finalDiagnosisIds, log, database, provider, enablePostProcessingCallback)
    resetDiagnosisEntry(application, actionMessage, finalDiagnosisIds, recommendationStatus, log, database)
                
    # Reset the BLT blocks - this varies slightly depending on the action
    if actionMessage == WAIT_FOR_MORE_DATA:
        partialResetDiagram(finalDiagnosisIds, database)
    else:
        resetDiagram(finalDiagnosisIds, database)

    print "Updating the DownloadAction for <%s> to <%s>" % (application, actionMessage)
    SQL = "update DtApplication set downloadAction = '%s' where ApplicationName = '%s'" % (actionMessage, application)
    system.db.runUpdateQuery(SQL, database)


def postSetpointSpreadsheetActionMessage(post, families, finalDiagnosisIds, actionMessage, recommendationStatus, database):
    log.infof("In %s.postSetpointSpreadsheetActionMessage() - action: %s - rec Status: %s - Families: %s", __name__, actionMessage, recommendationStatus, str(families))
    
    isTextRec = True
    for finalDiagnosisId in finalDiagnosisIds:
        SQL = "select textRecommendationId "\
            " from DtDiagnosisEntry DE, DtTextRecommendation TR "\
            " where DE.DiagnosisEntryId = TR.DiagnosisEntryId "\
            " and DE.FinalDiagnosisId = %s" % (str(finalDiagnosisId))
        pds = system.db.runQuery(SQL, database)
        if len(pds) == 0:
            isTextRec = False
            
    from ils.queue.commons import getQueueForPost
    queueKey=getQueueForPost(post, database)

    delimiter=""
    if isTextRec:
        msg = "Text recommendation for "
        for familyName in families:
            msg+=delimiter + familyName
            delimiter=" ,"    
        msg += " was acknowledged."
    else:
        msg="%s was selected for: " % (actionMessage)
        
        for familyName in families:
            msg+=delimiter + familyName
            delimiter=" ,"
    log.infof("Posting <%s>", msg)
    from ils.queue.message import insert
    insert(queueKey, "Info", msg, database)

    
# Delete all of the recommendations for an Application.  This is in response to a change in the status of a final diagnosis
# and is the first step in evaluating the active FDs and calculating new recommendations.
def resetOutputs(quantOutputIds, actionMessage, log, database):
    log.info("Resetting QuantOutputIds: %s" % (str(quantOutputIds)))
    rows=0
    for quantOutputId in quantOutputIds:
        SQL = "update DtQuantOutput set Active = 0 where QuantOutputId = %s" % (str(quantOutputId))
        log.info(SQL)
        cnt=system.db.runUpdateQuery(SQL, database)
        rows+=cnt
    log.info("Reset %i QuantOutputs..." % (rows))


# Delete all of the recommendations for an Application.  This is in response to a change in the status of a final diagnosis
# and is the first step in evaluating the active FDs and calculating new recommendations.
def resetRecommendations(quantOutputIds, actionMessage, log, database):
    log.info("Deleting recommendations for %s" % (str(quantOutputIds)))
    rows=0
    for quantOutputId in quantOutputIds:
        SQL = "delete from DtRecommendation " \
            " where RecommendationDefinitionId in (select RD.RecommendationDefinitionId "\
            " from DtRecommendationDefinition RD, DtQuantOutput QO"\
            " where RD.QuantOutputId = QO.QuantOutputId "\
            " and QO.QuantOutputId = %s)" % (str(quantOutputId))
        log.info(SQL)
        cnt=system.db.runUpdateQuery(SQL, database)
        rows+=cnt
    log.info("Deleted %i recommendations..." % (rows))


def resetFinalDiagnosis(applicationName, actionMessage, finalDiagnosisIds, log, database, provider, enablePostProcessingCallback=True):
    log.info("Resetting Final Diagnosis for application %s" % (applicationName))

    totalRows = 0    
    for finalDiagnosisId in finalDiagnosisIds:
        # if we are processing a wait-for-more-data then do not update the timeOfMostRecentRecommendationImplementation
        if actionMessage == WAIT_FOR_MORE_DATA:
            SQL = "update DtFinalDiagnosis set Active = 0 "
        else:
            SQL = "update DtFinalDiagnosis set Active = 0, TimeOfMostRecentRecommendationImplementation = getdate() "
    
        SQL = "%s where FinalDiagnosisId = %s" % (SQL, str(finalDiagnosisId))
        
        if enablePostProcessingCallback:
            performSpecialActions(applicationName, actionMessage, finalDiagnosisId, log, database, provider)

        log.info(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        totalRows = totalRows + rows
        
        '''
        If there was a manual move, a download, no download or wait for data should clear it!
        In the old application, this was done in the callback method.  This will make it available longer and should make the callback easier.
        '''
        resetManualMove(finalDiagnosisId, database)
        
    log.info("Updated %i records for %i final diagnosis..." % (totalRows, len(finalDiagnosisIds)))


def performSpecialActions(applicationName, actionMessage, finalDiagnosisId, log, database, provider):
    import sys, traceback
    log.info("Checking for special actions for final Diagnosis: %s (%s)" % (str(finalDiagnosisId), actionMessage))
    SQL = "select PostProcessingCallback from DtFinalDiagnosis where FinalDiagnosisId = %s" % (str(finalDiagnosisId))
    callback = system.db.runScalarQuery(SQL, database)
    log.info("The callback is <%s>" % (callback))

    if callback <> None and callback <> "":
        log.info("   ...there IS a callback...")
        
        if actionMessage == AUTO_NO_DOWNLOAD:
            log.info("   Skipping the special actions because the action is *AUTO* No Download!")
            return

        # If they specify shared or project scope, then we don't need to do this
        if not(string.find(callback, "project") == 0 or string.find(callback, "shared") == 0):
            # The method contains a full python path, including the method name
            separator=string.rfind(callback, ".")
            packagemodule=callback[0:separator]
            log.infof("Packagemodule: %s", packagemodule)
            separator=string.rfind(packagemodule, ".")
            package = packagemodule[0:separator]
            module  = packagemodule[separator+1:]
            log.infof("   ...using External Python, the package is: <%s>.<%s>...", package,module)
            
            exec("import %s" % (package))
            exec("from %s import %s" % (package,module))
            log.infof("   ...done with import...")
    
        try:
            log.infof("Calling Python...")
            eval(callback)(applicationName, actionMessage, finalDiagnosisId, provider, database)
            log.infof("...back from the special post processing callback!")
        except:
            log.error("Caught an error...")
            errorType,value,trace = sys.exc_info()
            errorTxt = traceback.format_exception(errorType, value, trace, 500)
            log.error("Caught an exception calling the special post processing callback named %s... \n%s" % (callback, errorTxt) )
    
        else:
            log.info("The special post processing callback completed successfully!")
    

def resetDiagnosisEntry(applicationName, actionMessage, finalDiagnosisIds, recommendationStatus, log, database):
    log.infof("In %s.resetDiagnosisEntry() - Resetting Diagnosis Entries for application %s with final diagnosis %s, status = %s", __name__, applicationName, str(finalDiagnosisIds), recommendationStatus)
    
    totalRows=0
    for finalDiagnosisId in finalDiagnosisIds:
        SQL = "update DtDiagnosisEntry set Status = 'InActive', RecommendationStatus='%s' "\
            " where status = 'Active' and FinalDiagnosisId = %s " % (recommendationStatus, str(finalDiagnosisId))   
            
        log.info(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        totalRows=totalRows + rows
        
    log.info("Updated %i diagnosis entries for %i final diagnosis..." % (totalRows, len(finalDiagnosisIds)))

# Reset the BLT diagram in response to a No-Download or Download.  This runs in the client in response to an operator action.
def resetDiagram(finalDiagnosisIds, database):
#    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
    import system.ils.blt.diagram as diagram
    log.infof("In %s.resetDiagram() - Resetting BLT diagrams...", __name__)
    
    for finalDiagnosisId in finalDiagnosisIds:
        log.info("...resetting final diagnosis Id: %s" % (str(finalDiagnosisId)))
        
        SQL = "select FinalDiagnosisName, DiagramUUID, FinalDiagnosisUUID from DtFinalDiagnosis "\
            "where FinalDiagnosisId = %s and DiagramUUID != 'DIAGRAM_UUID'" % (str(finalDiagnosisId))
        pds = system.db.runQuery(SQL, database)
        
        for record in pds:
            finalDiagnosisName=record["FinalDiagnosisName"]
            diagramUUID=record["DiagramUUID"]
            finalDiagnosisUUID=record["FinalDiagnosisUUID"]
            
            log.info("... resetting the final diagnosis: %s <%s>, FD: <%s>" % (finalDiagnosisName, str(diagramUUID), str(finalDiagnosisUUID)))

            # Resetting a block sets its state to UNSET, which does not propagate. 
            system.ils.blt.diagram.resetBlock(diagramUUID, finalDiagnosisName)
            
            # Now set the state to UNKNOWN and propagate it
            system.ils.blt.diagram.setBlockState(diagramUUID, finalDiagnosisName, "UNKNOWN")
            system.ils.blt.diagram.propagateBlockState(diagramUUID, finalDiagnosisUUID)
                        
            log.info("... fetching upstream blocks ...")

            if diagramUUID != None and finalDiagnosisUUID != None:
                blocks=diagram.listBlocksGloballyUpstreamOf(diagramUUID, finalDiagnosisName)

                upstreamBlocks = []
                blockUUIDUpstreamOfLatch = []
                for block in blocks:
                    blockName=block.getName()
                    blockClass=stripClassPrefix(block.getClassName())
                    
                    parentUUID=block.getAttributes().get("parent")

                    if blockClass in OBSERVATION_BLOCK_LIST:
                        log.info("   ... adding a %s named: %s to the reset list..." % (blockClass, blockName))
                        upstreamBlocks.append(block)

                    elif blockClass == "Inhibitor":
                        log.info("   ... setting a %s named: %s  to inhibit!..." % (blockClass, blockName))
                        upstreamBlocks.append(block)
                    
                    elif blockClass == "LogicLatch":
                        log.info("Found a logic latch")
                        blocksUpstreamofLatch=diagram.listBlocksGloballyUpstreamOf(parentUUID, blockName)
                        for upstreamBlock in blocksUpstreamofLatch:
                            if upstreamBlock.getIdString() not in blockUUIDUpstreamOfLatch and stripClassPrefix(upstreamBlock.getClassName()) in OBSERVATION_BLOCK_LIST:
                                log.tracef("Adding a %s named %s to the list of blocks upstream of a latch...", upstreamBlock.getClassName(), upstreamBlock.getName())
                                blockUUIDUpstreamOfLatch.append(upstreamBlock.getIdString())

                    else:
                        log.tracef("   ...skipping a %s...", blockClass)
                
                ''' Remove the upstream blocks from the main list '''
                log.infof("Removing %d blocks upstream of a latch from the list of %d blocks to reset...", len(blockUUIDUpstreamOfLatch), len(upstreamBlocks))
                blocksToReset = []
                for block in upstreamBlocks:
                    UUID=block.getIdString()
                    if UUID not in blockUUIDUpstreamOfLatch:
                        blocksToReset.append(block)
                    else:
                        log.tracef("Removing a %s - %s that is in the latch list from the reset list...", block.getClassName(), block.getName())

                ''' Now reset what is left '''        
                for block in blocksToReset:
                    UUID=block.getIdString()
                    blockName=block.getName()
                    blockClass=stripClassPrefix(block.getClassName())
                    blockId=block.getIdString()
                    parentUUID=block.getAttributes().get("parent")

                    if blockClass in OBSERVATION_BLOCK_LIST:
                        log.info("   ... resetting a %s named: %s..." % (blockClass, blockName))
                        
                        # Resetting a block sets its state to UNSET, which does not propagate. 
                        system.ils.blt.diagram.resetBlock(parentUUID, blockName)
                        
                        # Now set the state to UNKNOWN, then propagate
                        system.ils.blt.diagram.setBlockState(parentUUID, blockName, "UNKNOWN")
                        system.ils.blt.diagram.propagateBlockState(parentUUID, blockId)

                    elif blockClass == "Inhibitor":
                        log.info("   ... setting a %s named: %s  to inhibit! (%s  %s)..." % (blockClass,blockName,diagramUUID, UUID))
                        system.ils.blt.diagram.sendSignal(parentUUID, blockName,"INHIBIT","")
                        
                    else:
                        log.tracef("   ...skipping a %s...", blockClass)
                        
            else:
                log.error("Skipping diagram reset because the diagram or FD UUID is Null!")


# Reset the BLT diagram in response to a Wait-For-More-Data
def partialResetDiagram(finalDiagnosisIds, database):
    log.info("   ... performing a *partial* reset of the BLT diagrams ...")
    
    diagramUUIDs = []
    for finalDiagnosisId in finalDiagnosisIds:
        log.info("      ...resetting final diagnosis Id: %s" % (str(finalDiagnosisId)))
        
        SQL = "select FinalDiagnosisName, DiagramUUID, FinalDiagnosisUUID from DtFinalDiagnosis "\
            "where FinalDiagnosisId = %s " % (str(finalDiagnosisId))
        pds = system.db.runQuery(SQL, database)
        
        for record in pds:
            finalDiagnosisName=record["FinalDiagnosisName"]
            diagramUUID=record["DiagramUUID"]
            
            if diagramUUID not in diagramUUIDs:
                diagramUUIDs.append(diagramUUID)
                
            finalDiagnosisUUID=record["FinalDiagnosisUUID"]
            
            log.infof("   Diagram: <%s>, FD: <%s>", str(diagramUUID), str(finalDiagnosisUUID))           
            log.infof("   ... Resetting the final diagnosis: %s  %s...", finalDiagnosisName, diagramUUID)
            
            system.ils.blt.diagram.resetBlock(diagramUUID, finalDiagnosisName)
            system.ils.blt.diagram.setBlockState(diagramUUID, finalDiagnosisName, "UNKNOWN")
            system.ils.blt.diagram.propagateBlockState(diagramUUID, diagramUUID)
                        
            log.infof("Fetching upstream blocks for diagram <%s> - final diagnosis <%s>...", str(diagramUUID), finalDiagnosisName)

            downstreamBlocks=[]
            if diagramUUID != None and finalDiagnosisUUID != None:
                blocks=system.ils.blt.diagram.listBlocksGloballyUpstreamOf(diagramUUID, finalDiagnosisName)

                for block in blocks:
                    UUID=block.getIdString()
                    blockName=block.getName()
                    blockClass=stripClassPrefix(block.getClassName())
                    blockId=block.getIdString()
                    parentUUID=block.getAttributes().get("parent")

                    # I'm not exactly sure why we choose to do a full reset on the logic filter block, but the 
                    # reason from G2 was to allow high-frequency data to flow through the diagrams, and possibly
                    # trigger other diagnosis, but the diagnosis connected to this logic-filter will effectively
                    # be inhibited from firing based on the configuration of the logic filter. 
                    if blockClass == "LogicFilter":
                        log.infof("   ... found a logic filter named: %s  %s  %s...", blockName,diagramUUID, UUID)
                        system.ils.blt.diagram.resetBlock(diagramUUID, blockName)
                    
                    elif blockClass in ["SQC", "SQCDiagnosis", "TrendDetector"]:
                        # Set the state to UNKNOWN, then propagate
                        log.infof("   ... setting a %s named: %s to UNKNOWN (%s  %s)...", blockClass, blockName, parentUUID, UUID)
                        system.ils.blt.diagram.setBlockState(parentUUID, blockName, "UNKNOWN")
                        system.ils.blt.diagram.propagateBlockState(parentUUID, UUID)
 
                        if parentUUID not in diagramUUIDs:
                            diagramUUIDs.append(parentUUID)

                        '''
                        We do NOT want to send a signal to the block to evaluate in order to get the signal 
                        to propagate because the EVALUATE signal will cause the block to reevaluate the history
                        buffer and reach the same conclusion that we just cleared.
                        '''
                        
#                        tList=system.ils.blt.diagram.listBlocksDownstreamOf(diagramUUID, blockName)
#                        for tBlock in tList:
#                            tBlockName=tBlock.getName()
#                            if tBlockName not in downstreamBlocks and tBlockName != finalDiagnosisName:
#                                downstreamBlocks.append(tBlockName)
                
#                print "The blocks between the observations and the final diagnosis that need to be reset are: ", downstreamBlocks
#                for blockName in downstreamBlocks:
#                    system.ils.blt.diagram.resetBlock(diagramUUID, blockName)
            else:
                log.error("Skipping diagram reset because the diagram or FD UUID is Null!")
    
    '''
    I'm not 100% sure how this worked in G2, do I put the watermark just on the diagram that has the final diagnosis or on all diagrams that have a block that 
    we set to unknown.  The key is making sure that the watermark disappears when the next datapoint arrives.
    '''
    for diagramUUID in diagramUUIDs:
        log.infof("Setting the watermark on %s", diagramUUID)
        system.ils.blt.diagram.setWatermark(diagramUUID,"Wait For New Data")


def manualEdit(rootContainer, post, applicationName, quantOutputId, tagName, newValue):
    '''
    This runs in the client when they edit the Recommendation field of the setpoint spreadsheet.
    I'm not sure if this will work out, but it would be nice to validate the manual entry and provide some feedback back to the operator.
    '''
    log.infof("In %s.manualEdit()", __name__)
    valid=True
    
    database=getDatabaseClient()
    tagProvider=getTagProviderClient()
    projectName = system.util.getProjectName()
    
    SQL = "update DtQuantOutput set ManualOverride = 1, FeedbackOutputManual = %f "\
        "where QuantOutputId = %i" % (newValue, quantOutputId)
    log.tracef("SQL: %s", SQL)
    system.db.runUpdateQuery(SQL, database)
    
    # Now check the bounds - fetch everything about the quant output first
    from ils.diagToolkit.common import fetchQuantOutput
    quantOutputs = fetchQuantOutput(quantOutputId, database)
    if len(quantOutputs) != 1:
        system.gui.errorBox("Unable to fetch quant output with id: %s" % (str(quantOutputId)))
        return
    
    record=quantOutputs[0]
    from ils.diagToolkit.common import convertOutputRecordToDictionary
    quantOutput=convertOutputRecordToDictionary(record)
    quantOutputName=quantOutput.get("QuantOutput","")
    log.tracef("Before: %s", str(quantOutput))
    
    ''' Insert a message into the queue so that we can help debug the setpoint spreadsheet '''
    txt = "A manual recommendation of %s was entered for %s (id: %d)" % (str(newValue), quantOutputName, quantOutputId)
    insertPostMessage(post, QUEUE_INFO, txt, database, projectName)
    
    from ils.diagToolkit.finalDiagnosis import checkBounds
    quantOutput, madeSignificantRecommendation = checkBounds(applicationName, quantOutput, quantOutputName, database, tagProvider)
    
    log.tracef("After: %s", str(quantOutput))
    
    '''
    We need to make sure we have enough information here to determine that the recommendation is for a ramp 
    '''
    quantOutputId = quantOutput["QuantOutputId"]
    pds = fetchRecommendationsForOutput(quantOutputId, database)
    recommendations = []
    rampTime = None
    for record in pds:
        recommendations.append({"RampTime": record["RampTime"]})
        rampTime = record["RampTime"]
    
    quantOutput["Recommendations"] = recommendations
    quantOutput["Ramp"] = rampTime
    
    from ils.diagToolkit.finalDiagnosis import updateQuantOutput
    updateQuantOutput(quantOutput, database, tagProvider)
    
    # Now refresh the screen
    initialize(rootContainer)
    
    return valid, ""


# This is called when the operator acknowledges a text alert.  It should effectively do a NO Download on the
# application.  This is called from the ACK button on the loud workspace.
def acknowledgeTextRecommendationProcessing(post, application, diagnosisEntryId, db, provider, recalc=True):
    from ils.diagToolkit.common import fetchQuantOutputsForFinalDiagnosisIds
    log.infof("... in %s.acknowledgeTextRecommendationProcessing() performing Text Recommendation acknowledgement for diagnosis entry %s (recalc=%s)...", __name__, str(diagnosisEntryId), str(recalc))
    
    actionMessage=NO_DOWNLOAD
    recommendationStatus="Acknowledged"
    
    SQL = "select FinalDiagnosisId from DtDiagnosisEntry where DiagnosisEntryId = %i" % (diagnosisEntryId)
    finalDiagnosisId = system.db.runScalarQuery(SQL, database=db) 
    if finalDiagnosisId == None:
        log.warnf("Unable to acknowledge a text recommendation because the Final Diagnosis could not be found for diagnosis entry <%s>", str(diagnosisEntryId))
        return
    
    finalDiagnosisIds=[finalDiagnosisId]
    
    familyName = fetchFamilyNameForFinalDiagnosisId(finalDiagnosisId)
    families = [familyName]

    log.infof("Resetting: ")
    log.infof("  Application: %s", application)
    log.infof("  Families:    %s", str(families))
    log.infof("  FDs:         %s", str(finalDiagnosisIds))
        
    quantOutputIds=fetchQuantOutputsForFinalDiagnosisIds(finalDiagnosisIds)

    resetApplication(post, application, families, finalDiagnosisIds, quantOutputIds, actionMessage, recommendationStatus, db, provider)

    SQL = "delete from DtTextRecommendation where DiagnosisEntryId = %i" % (diagnosisEntryId)
    rows = system.db.runUpdateQuery(SQL, database=db)
    log.infof("...deleted %d text recommendations...", rows)
    log.infof("...done acknowledging text recommendation!")
    
    # Refresh the spreadsheet - This needs to be done in a general way that will update the spreadsheet 
    # that may be displayed on multiple clients.  This callback is running in a client, if I just call 
    # initialize it will just update this client.  Because the database and blocks have been reset,
    # I should be able to call recalc in the gateway which will notify client to update the spreadsheet
    if recalc:
        log.infof("Sending a message to manage applications for post: %s (database: %s)", post, db)
        projectName=system.util.getProjectName()
        payload={"post": post, "database": db, "provider": provider, "applications": [application]}
        system.util.sendMessage(projectName, "recalc", payload, "G")

def logAction(action, repeater):
    '''
    Send a message to the gateway so that the requested action and the complete state of the setpoint spreadsheet will be logged to a file
    '''
    project = system.util.getProjectName()
    payload = {"action": action, "ds": repeater.templateParams}
    system.util.sendMessage(project=project, messageHandler="setpointSpreadsheetLogger", payload=payload, scope="G")
    
def logActionMessageHandler(payload):
    log.infof("In %s.logActionMessageHandler with %s ", __name__, str(payload))
    
    action = payload.get("action", "")
    ds = payload.get("ds", None)
    timestamp = system.date.format(system.date.now(), "yyyy_MM_dd_HH_mm_ss")
    reportHome = system.tag.read("Configuration/Common/reportHome").value
    filename = "%s/Event_Logs/Diagnostic_Actions/%s_%s.csv" % (reportHome, timestamp, action)
    log.infof("...logging to %s", filename)
    
    txt = "action,%s%s" % (action, CR)
    txt = "%stimestamp,%s%s" % (txt, system.date.format(system.date.now(), "yyyy_MM_dd_HH_mm_ss"), CR)
    txt = "%s%s" % (txt, dsToText(ds, ","))
    
    system.file.writeFile(filename, txt, False)