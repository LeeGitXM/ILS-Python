'''
Created on Sep 9, 2014

@author: ILS
'''

import system, string
from ils.sfc.common.constants import SQL
log = system.util.getLogger("com.ils.diagToolkit")
WAIT_FOR_MORE_DATA="Wait For Data"

def initialize(rootContainer):
    print "In %s.initialize()..." % (__name__)

    rootContainer.initializationComplete = False
    database=system.tag.read("[Client]Database").value
    print "The database is: ", database
    
    post = rootContainer.post
    repeater = rootContainer.getComponent("Template Repeater")
    
    from ils.diagToolkit.common import fetchActiveOutputsForPost
    pds = fetchActiveOutputsForPost(post, database)
    
    # Create the data structures that will be used to make the dataset the drives the template repeater
    header=['type','row','selected','qoId','command','commandValue','application','output','tag','setpoint','manualOverride','recommendation','finalSetpoint','status','downloadStatus','numberFormat']
    rows=[]
    # The data types for the column is set from the first row, so I need to put floats where I want floats, even though they don't show up for the header
    row = ['header',0,0,0,'Action',0,'','Outputs','',1.2,False,1.2,1.2,'','','']
    rows.append(row)
    
    application = ""
    i = 1
    for record in pds:
        
        # If the record that we are processing is for a different application, or if this is the first row, then insert an application divider row
        if record['ApplicationName'] != application:
            # Remember the row number of the application because we will need to update the status if we encounter
            # any minimum change bound outputs
            applicationRowNumber = i
            minChangeBoundCount = 0
             
            application = record['ApplicationName']
            applicationRow = ['app',i,0,0,'Active',0,application,'','',0,False,0,0,'','','']
            print "App row: ", applicationRow
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
            
            row = ['row',i,0,record['QuantOutputId'],'GO',0,application,record['QuantOutputName'],record['TagPath'],record['CurrentSetpoint'],
                   record['ManualOverride'],record['DisplayedRecommendation'],record['FinalSetpoint'],statusMessage,'',numberPattern]
            print "Output Row: ", row
            rows.append(row)
            i = i + 1

    print rows
    ds = system.dataset.toDataSet(header, rows)
    repeater.templateParams=ds
    repeater.selectedRow = -1

    #----------------------------------------------------------
    def initializationComplete(rootContainer=rootContainer):
        print "Setting initializationComplete to TRUE"
        rootContainer.initializationComplete = True
    #----------------------------------------------------------

    print "Invoking later..."
    system.util.invokeLater(initializationComplete, 1000)
    

def writeFileCallback(rootContainer):
    print "In writeFileCallback()..."
    logFileName=system.file.openFile('*.log')
    writeFile(rootContainer, logFileName)

# The state of the diagnosis / recommendations are written to a file for various reasons, including from the toolbar button 
# and as part of a download request.  The contents of the file are not simply the lines of the spreadsheet, in order to keep
# the same format as the old platform, we need to query the database and get the data that was used to build the spreadsheet.
def writeFile(rootContainer, filepath):
    print "In writeFile() to ", filepath
    post = rootContainer.post

    exists=system.file.fileExists(filepath)
    if not(exists):
        print "Write some sort of new file header"

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
            recommendationMultiplier=finalDiagnosisRecord['RecommendationMultiplier']
            recommendationErrorText=finalDiagnosisRecord['RecommendationErrorText']
            print "Final Diagnosis: ", finalDiagnosis, finalDiagnosisId, recommendationErrorText
            
            if recommendationMultiplier < 0.99 or recommendationMultiplier > 1.01:
                system.file.writeFile(filepath, "       Diagnosis -- %s (multiplier = %f)\n" % (finalDiagnosis, recommendationMultiplier), True)
            else:
                system.file.writeFile(filepath, "       Diagnosis -- %s\n" % (finalDiagnosis), True)

            if recommendationErrorText != None:
                system.file.writeFile(filepath, "       %s\n\n" % (recommendationErrorText), True) 

            from ils.diagToolkit.common import fetchSQCRootCauseForFinalDiagnosis
            rootCauseList=fetchSQCRootCauseForFinalDiagnosis(finalDiagnosis)
            for rootCause in rootCauseList:
                print "Root cause: ????", rootCause

            from ils.diagToolkit.common import fetchOutputsForFinalDiagnosis
            pds, outputs=fetchOutputsForFinalDiagnosis(application, family, finalDiagnosis)
            for record in outputs:
                print record
                quantOutput = record.get('QuantOutput','')
                tagPath = record.get('TagPath','')
                feedbackOutput=record.get('FeedbackOutput',0.0)
                feedbackOutputConditioned = record.get('FeedbackOutputConditioned',0.0)
                manualOverride=record.get('ManualOverride', False)
                outputLimited=record.get('OutputLimited', False)
                outputLimitedStatus=record.get('OutputLimitedStatus', '')
                print "Manual Override: ", manualOverride
                txt = "          the desired change in %s = %f" % (tagPath, feedbackOutput)
                if manualOverride:
                    txt = "%s  (manually specified)" % (txt)
                system.file.writeFile(filepath, txt + "\n", True)

                if outputLimited and feedbackOutput != 0.0:
                    txt = "          change to %s returnadjusted to %f because %s" % (quantOutput, feedbackOutputConditioned, outputLimitedStatus)

    print "Done!"

def detailsCallback(rootContainer):
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
    
    system.nav.openWindowInstance('DiagToolkit/Recommendation Map', {'quantOutputName' : quantOutputName})
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
            txt = "The output (%s) is %s limited!\n\nIt was reduced from %.2f to %.2f because the most bound output "\
                "could only use %.0f%% of its value" % (quantOutputName, outputLimitedStatus, record['FeedbackOutput'], \
                                                    record['FeedbackOutputConditioned'], record['OutputPercent'])
        else:
            txt = "The output (%s) is %s limited!\n\n%s" % (quantOutputName, outputLimitedStatus, limitDetails)
    else:
        txt = "The output (%s) is not limited!\n\n%s" % (quantOutputName, limitDetails)
    
    title = "Output Details"

    system.gui.messageBox(txt, title)

# This is called from the recalc button on the setpoint spreadsheet
def recalcCallback(event):
    rootContainer=event.source.parent
    post=rootContainer.post
    database=system.tag.read("[Client]Database").value
    tagProvider=system.tag.read("[Client]Tag Provider").value
    
    print "Sending a message to manage applications for post: %s (database: %s)" % (post, database)
    projectName=system.util.getProjectName()
    payload={"post": post, "database": database, "provider": tagProvider}
    system.util.sendMessage(projectName, "recalc", payload, "G")

    print "Need to do something to update the spreadsheet..."
    # A recalculation happens in the gateway, so I', not sure how I can know when it is done...
    
#    from ils.diagToolkit.common import fetchApplicationsForPost
#    pds=fetchApplicationsForPost(post, database)

#    from ils.diagToolkit.finalDiagnosis import manage
#    for record in pds:
#        applicationName=record["ApplicationName"]
#        manage(applicationName)

    # Now update the UI
#    initialize(rootContainer)

#
# FYI - the download callback is in its own module.
#

# This is called from the WAIT button on the set-point spreadsheet
def waitCallback(event):
    print "Processing a WAIT-FOR-MORE-DATA..."
    rootContainer=event.source.parent

    from ils.common.config import getDatabaseClient, getTagProviderClient
    db=getDatabaseClient()
    tagProvider=getTagProviderClient()
    repeater=rootContainer.getComponent("Template Repeater")
    ds = repeater.templateParams
    postCallbackProcessing(rootContainer, ds, db, tagProvider, actionMessage=WAIT_FOR_MORE_DATA, recommendationStatus=WAIT_FOR_MORE_DATA)


# This is called from the NO DOWNLOAD button on the set-point spreadsheet
def noDownloadCallback(event):
    print "Processing a NO-DOWNLOAD..."
    rootContainer=event.source.parent

    from ils.common.config import getDatabaseClient, getTagProviderClient
    db=getDatabaseClient()
    tagProvider=getTagProviderClient()
    repeater=rootContainer.getComponent("Template Repeater")
    ds = repeater.templateParams
    allApplicationsProcessed=postCallbackProcessing(rootContainer, ds, db, tagProvider, actionMessage="No Download", recommendationStatus="No Download")
    
    # If they disabled some applications then leave the spreadsheet open, otherwise dismiss it
    if allApplicationsProcessed:
        system.nav.closeParentWindow(event)

# This is called when we do a "No Download" or "Wait For More Data".
# Use the action message to determine which button was pressed and exactly how much processing to do.
# Reset the database tables and the BLT diagrams for every application that is active.
# We do not consider individual outputs that the operator may have chosen to not download.   
def postCallbackProcessing(rootContainer, ds, db, tagProvider, actionMessage, recommendationStatus):
    
    #--------------
    def resetter(application, families, finalDiagnosisIds, quantOutputIds, actionMessage, recommendationStatus, db):
        if len(finalDiagnosisIds) == 0:
            print "...did not find any finalDiagnosis in the spreadsheet, fetching for all active ones..."
            from ils.diagToolkit.common import fetchActiveDiagnosis
            pds = fetchActiveDiagnosis(application, db)
            finalDiagnosisIds=[]
            for record in pds:
                finalDiagnosisIds.append(record["FinalDiagnosisId"])

        print "Resetting: "
        print "  Application: ", application
        print "  Families:    ", families
        print "  FDs:         ", finalDiagnosisIds
        
        quantOutputIds=fetchQuantOutputsForFinalDiagnosisIds(finalDiagnosisIds)

        resetApplication(post, application, families, finalDiagnosisIds, quantOutputIds, actionMessage, recommendationStatus, db)
    #-------------
    from ils.diagToolkit.common import fetchQuantOutputsForFinalDiagnosisIds
    print "...performing generic post callback cleanup..." 
    allApplicationsProcessed=True
    post=rootContainer.post
    applicationActive=False
    application=""
    families=[]
    finalDiagnosisIds=[]
    quantOutputIds=[]
    
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")

        if string.upper(rowType) == "APP":
            command=ds.getValueAt(row, "command")

            if string.upper(command) == 'ACTIVE':
                if application != "":
                    resetter(application, families, finalDiagnosisIds, quantOutputIds, actionMessage, recommendationStatus, db)

                families=[]
                finalDiagnosisIds=[]
                quantOutputIds=[]
                
                applicationActive=True
                application=ds.getValueAt(row, "application")
            else:
                applicationActive=False
                allApplicationsProcessed=False

        elif string.upper(rowType) == "ROW":
            if applicationActive:
                quantOutputId=ds.getValueAt(row, "qoId")
                if quantOutputId not in quantOutputIds:
                    quantOutputIds.append(quantOutputId)
                    
                    from ils.diagToolkit.common import fetchActiveFinalDiagnosisForAnOutput
                    pds=fetchActiveFinalDiagnosisForAnOutput(application, quantOutputId, db)
                    for rec in pds:
                        if rec["FinalDiagnosisId"] not in finalDiagnosisIds:
                            finalDiagnosisIds.append(rec["FinalDiagnosisId"])
                        if rec["FamilyName"] not in families:
                            families.append(rec["FamilyName"])

    resetter(application, families, finalDiagnosisIds, quantOutputIds, actionMessage, recommendationStatus, db)
    print "...done post action processing!"
    
    # Refresh the spreadsheet - This needs to be done in a general way that will update the spreadsheet 
    # that may be displayed on multiple clients.  This callback is running in a client, if I just call 
    # initialize it will just update this client.  Because the database and blocks have been reset,
    # I should be able to call recalc in the gateway which will notify client to update the spreadsheet
    print "Sending a message to manage applications for post: %s (database: %s)" % (post, db)
    projectName=system.util.getProjectName()
    payload={"post": post, "database": db, "provider": tagProvider}
    system.util.sendMessage(projectName, "recalc", payload, "G")
    return allApplicationsProcessed

def resetApplication(post, application, families, finalDiagnosisIds, quantOutputIds, actionMessage, recommendationStatus, database):
    log.info("In %s resetting application %s because %s - %s" % (__name__, application, actionMessage, recommendationStatus))
    log.trace("  Families: %s" % (str(families)))
    log.trace("  Final Diagnosis Ids: %s" % (str(finalDiagnosisIds)))
    log.trace("  Quant Output Ids: %s" % (str(quantOutputIds)))

    # Post a message to the applications queue documenting what we are doing to the active families    
    postSetpointSpreadsheetActionMessage(post, families, finalDiagnosisIds, actionMessage, database)

    # Perform all of the database updates necessary to update the affected FDs, 
    # Quant Outputs, recommendations, and diagnosis entries.

    resetOutputs(quantOutputIds, actionMessage, log, database)
    resetRecommendations(quantOutputIds, actionMessage, log, database)
    resetFinalDiagnosis(application, actionMessage, finalDiagnosisIds, log, database)
    resetDiagnosisEntry(application, actionMessage, finalDiagnosisIds, recommendationStatus, log, database)
                
    # Reset the BLT blocks - this varies slightly depending on the action
    if actionMessage == WAIT_FOR_MORE_DATA:
        partialResetDiagram(finalDiagnosisIds, database)
    else:
        resetDiagram(finalDiagnosisIds, database)


def postSetpointSpreadsheetActionMessage(post, families, finalDiagnosisIds, actionMessage, database):
    from ils.queue.commons import getQueueForPost
    queueKey=getQueueForPost(post, database)

    delimiter=""
    msg="%s was selected for: " % (actionMessage)
    for familyName in families:
        msg+=delimiter + familyName
        delimiter=" ,"
    print "Posting <%s>" % (msg)
    from ils.queue.message import insert
    insert(queueKey, "Info", msg, database)

    
# Delete all of the recommendations for an Application.  This is in response to a change in the status of a final diagnosis
# and is the first step in evaluating the active FDs and calculating new recommendations.
def resetOutputs(quantOutputIds, actionMessage, log, database):
    log.info("Resetting QuantOutputIds: %s" % (str(quantOutputIds)))
    rows=0
    for quantOutputId in quantOutputIds:
        SQL = "update DtQuantOutput " \
            " set Active = 0 where QuantOutputId = %s" % (str(quantOutputId))
        log.trace(SQL)
        cnt=system.db.runUpdateQuery(SQL, database)
        rows+=cnt
    log.trace("Reset %i QuantOutputs..." % (rows))


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
        log.trace(SQL)
        cnt=system.db.runUpdateQuery(SQL, database)
        rows+=cnt
    log.trace("Deleted %i recommendations..." % (rows))

def resetFinalDiagnosis(applicationName, actionMessage, finalDiagnosisIds, log, database):
    log.info("Resetting Final Diagnosis for application %s" % (applicationName))

    totalRows = 0    
    for finalDiagnosisId in finalDiagnosisIds:
        # if we are processing a wait-for-more-data then do not update the timeOfMostRecentRecommendationImplementation
        if actionMessage == WAIT_FOR_MORE_DATA:
            SQL = "update DtFinalDiagnosis set Active = 0 "
        else:
            SQL = "update DtFinalDiagnosis set Active = 0, TimeOfMostRecentRecommendationImplementation = getdate() "
    
    #    SQL = "%s where active = 1 and FamilyId in "\
    #        " (select F.familyId "\
    #        " from DtFamily F, DtApplication A "\
    #        " where F.ApplicationId = A.ApplicationId "\
    #        " and A.ApplicationName = '%s')" % (SQL, applicationName)
    
        SQL = "%s where FinalDiagnosisId = %s" % (SQL, str(finalDiagnosisId))
        
        log.trace(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        totalRows = totalRows + rows
        
    log.trace("Updated %i records for %i final diagnosis..." % (totalRows, len(finalDiagnosisIds)))

def resetDiagnosisEntry(applicationName, actionMessage, finalDiagnosisIds, recommendationStatus, log, database):
    log.info("Resetting Diagnosis Entries for application %s with final diagnosis %s" % (applicationName, str(finalDiagnosisIds)))
    
    totalRows=0
    for finalDiagnosisId in finalDiagnosisIds:
#        SQL = "update DtDiagnosisEntry set Status = 'Inactive', RecommendationStatus='%s' "\
#            " where status = 'Active' and FinalDiagnosisId in "\
#            " (select FD.FinalDiagnosisId "\
#            " from DtFinalDiagnosis FD, DtFamily F, DtApplication A "\
#            " where FD.FamilyId = F.FamilyId "\
#            " and F.ApplicationId = A.ApplicationId "\
#            " and A.ApplicationName = '%s')" % (recommendationStatus, applicationName)
         
        SQL = "update DtDiagnosisEntry set Status = 'Inactive', RecommendationStatus='%s' "\
            " where status = 'Active' and FinalDiagnosisId = %s " % (recommendationStatus, str(finalDiagnosisId))   
            
        log.trace(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        totalRows=totalRows + rows
        
    log.trace("Updated %i diagnosis entries for %i final diagnosis..." % (totalRows, len(finalDiagnosisIds)))

# Reset the BLT diagram in response to a No-Download or Download
def resetDiagram(finalDiagnosisIds, database):
#    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
    import system.ils.blt.diagram as diagram
    print "Resetting BLT diagrams..."
    
    for finalDiagnosisId in finalDiagnosisIds:
        print "Resetting final diagnosis Id: %s" % (str(finalDiagnosisId))
        
        SQL = "select FinalDiagnosisName, DiagramUUID, UUID from DtFinalDiagnosis "\
            "where FinalDiagnosisId = %s " % (str(finalDiagnosisId))
        pds = system.db.runQuery(SQL, database)
        
        for record in pds:
            finalDiagnosisName=record["FinalDiagnosisName"]
            diagramUUID=record["DiagramUUID"]
            fdUUID=record["UUID"]
            
            print "Diagram: <%s>, FD: <%s>" % (str(diagramUUID), str(fdUUID))
            
            print "   ... Resetting the final diagnosis: %s  %s..." % (finalDiagnosisName, diagramUUID)
            system.ils.blt.diagram.resetBlock(diagramUUID, finalDiagnosisName)
                        
            print "Fetching upstream blocks for diagram <%s> - final diagnosis <%s>..." % (str(diagramUUID), finalDiagnosisName)

            if diagramUUID != None and fdUUID != None:
                blocks=diagram.listBlocksGloballyUpstreamOf(diagramUUID, finalDiagnosisName)

#TODO These blocks may have crossed over boundaries onto other diagrams, so I can't keep feeding the same diagramUUID
# along with the block UUIDs.  Need a way to call a getParentUUID() method for a block.

                for block in blocks:
                    blockId=block.getIdString()
                    blockName=block.getName()
                    blockClass=block.getClassName()
                    parentUUID=block.getAttributes().get("parent")
                    
                    print "Found a <%s> block named %s..." % (blockClass, blockName)

                    if blockClass in ["com.ils.block.SQC", "xom.block.sqcdiagnosis.SQCDiagnosis",
                                "com.ils.block.TrendDetector", "com.ils.block.LogicFilter"]:
                        print "   ... resetting a %s named: %s with id: %s on diagram: %s..." % (blockClass, blockName, blockId, parentUUID)
                        system.ils.blt.diagram.resetBlock(parentUUID, blockName)
                        
                    if blockClass == "xom.block.sqcdiagnosis.SQCDiagnosis":
                        print "Setting the lastResetTime for SQC diagnosis named: %s" % (blockName)
                        SQL = "update DtSQCDiagnosis set LastResetTime = getdate() where BlockId = '%s'" % (blockId)
                        print SQL
                        rows = system.db.runUpdateQuery(SQL, database)
                        print "Updated %i rows" % (rows)

                    if blockClass == "com.ils.block.Inhibitor":
                            print "   ... setting a %s named: %s  to inhibit! (%s  %s)..." % (blockClass,blockName,diagramUUID, blockId)
                            system.ils.blt.diagram.sendSignal(parentUUID, blockName,"INHIBIT","")
                        
            else:
                log.error("Skipping diagram reset because the diagram or FD UUID is Null!")


# Reset the BLT diagram in response to a Wait-For-More-Data
def partialResetDiagram(finalDiagnosisIds, database):
    print "Performing a *partial* reset of the BLT diagrams..."
    
    for finalDiagnosisId in finalDiagnosisIds:
        print "Resetting final diagnosis Id: %s" % (str(finalDiagnosisId))
        
        SQL = "select FinalDiagnosisName, DiagramUUID, UUID from DtFinalDiagnosis "\
            "where FinalDiagnosisId = %s " % (str(finalDiagnosisId))
        pds = system.db.runQuery(SQL, database)
        
        for record in pds:
            finalDiagnosisName=record["FinalDiagnosisName"]
            diagramUUID=record["DiagramUUID"]
            fdUUID=record["UUID"]
            
            print "Diagram: <%s>, FD: <%s>" % (str(diagramUUID), str(fdUUID))
            
            print "Setting the watermark"
            system.ils.blt.diagram.setWatermark(diagramUUID,"Wait For New Data")
            
            print "   ... Resetting the final diagnosis: %s  %s..." % (finalDiagnosisName, diagramUUID)
            system.ils.blt.diagram.resetBlock(diagramUUID, finalDiagnosisName)
                        
            print "Fetching upstream blocks for diagram <%s> - final diagnosis <%s>..." % (str(diagramUUID), finalDiagnosisName)

            downstreamBlocks=[]
            if diagramUUID != None and fdUUID != None:
                blocks=system.ils.blt.diagram.listBlocksGloballyUpstreamOf(diagramUUID, finalDiagnosisName)

                for block in blocks:
                    blockId=block.getIdString()
                    blockName=block.getName()
                    blockClass=block.getClassName()
                    
                    print "Found a <%s> block..." % (blockClass)

                    # I'm not exactly sure why we choose to do a full reset on the logic filter block, but the 
                    # reason from G2 was to allow high-frequency data to flow through the diagrams, and possibly
                    # trigger other diagnosis, but the diagnosis connected to this logic-filter will effectively
                    # be inhibited from firing based on the configuration of the logic filter. 
                    if blockClass == "com.ils.block.LogicFilter":
                        print "   ... found a logic filter named: %s  %s  %s..." % (blockName,diagramUUID, blockId)
                        system.ils.blt.diagram.resetBlock(diagramUUID, blockName)
                    elif blockClass in ["com.ils.block.SQC", "xom.block.sqcdiagnosis.SQCDiagnosis",
                            "com.ils.block.TrendDetector"]:
                        print "   ... doing a partial reset of a %s named: %s  %s  %s..." % (blockClass, blockName,diagramUUID, blockId)
                        system.ils.blt.diagram.setBlockState(diagramUUID, blockName, "UNKNOWN")
                        # We do NOT want tosend a signal to the block to evaluate in order to get the signal 
                        # to propagate because the EVALUATE signal will cause the block to reevaluate the history
                        # buffer and reach the same conclusion that we just cleared.
                        
                        tList=system.ils.blt.diagram.listBlocksDownstreamOf(diagramUUID, blockName)
                        for tBlock in tList:
                            tBlockName=tBlock.getName()
                            if tBlockName not in downstreamBlocks and tBlockName != finalDiagnosisName:
                                downstreamBlocks.append(tBlockName)
                
                print "The blocks between the observations and the final diagnosis that need to be reset are: ", downstreamBlocks
                for blockName in downstreamBlocks:
                    system.ils.blt.diagram.resetBlock(diagramUUID, blockName)
            else:
                log.error("Skipping diagram reset because the diagram or FD UUID is Null!")

def manualEdit(rootContainer, post, applicationName, quantOutputId, tagName, newValue):
    # I'm not sure if this will work out, but it would be nice to validate the manual entry and provide some 
    # feedback back to the operator
    valid=True
    txt=""
    
    from ils.common.config import getDatabaseClient
    database=getDatabaseClient()
    
    from ils.common.config import getTagProviderClient
    tagProvider=getTagProviderClient() 
    
    SQL = "update DtQuantOutput set ManualOverride = 1, FeedbackOutputManual = %f "\
        "where QuantOutputId = %i" % (newValue, quantOutputId)
    print SQL
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
    print "Before: ", quantOutput
    
    from ils.diagToolkit.finalDiagnosis import checkBounds
    quantOutput = checkBounds(quantOutput, database, tagProvider)
    
    print "After: ", quantOutput
    
    from ils.diagToolkit.finalDiagnosis import updateQuantOutput
    updateQuantOutput(quantOutput, database, tagProvider)
    
    # Now refresh the screen
    initialize(rootContainer)
    
    return valid, txt
