'''
Created on Feb 4, 2015

@author: Pete
'''

import system, string
from __builtin__ import False
log = system.util.getLogger("com.ils.diagToolkit.download")
from ils.queue.message import insertPostMessage
from ils.io.api import confirmControllerMode
from ils.io.api import write

# This is called from the download button on the setpoint spreadsheet.
def downloadCallback(event, rootContainer):
    log.info("In downloadCallback()")
    
    from ils.common.config import getTagProviderClient, getDatabaseClient
    tagProvider=getTagProviderClient()
    db=getDatabaseClient()
    
    post=rootContainer.post
    
    repeater=rootContainer.getComponent("Template Repeater")
    ds = repeater.templateParams
    
    #TODO - Do I need to check if there is a download in progress
        
    workToDo=bookkeeping(ds)
    if not(workToDo):
        # Even though this is a warning, Warning boxes are not modal and these are!
        system.gui.messageBox("Canceling download because there is no work to be done!")
        return

    okToDownload=checkIfOkToDownload(repeater, ds, post, tagProvider, db)
    if not(okToDownload):
        insertPostMessage(post, "Warning", "SPs were NOT downloaded due to a controller configuration error", db)
        # Even though this is a warning, Warning boxes are not modal and these are!
        system.gui.messageBox("Cancelling download because one or more of the controllers is unreachable!")
        return

    ans = system.gui.confirm("There are setpoints to download and the controllers are in the correct mode, press 'Yes' to proceed with the downlaod.")
    
    if ans:
        serviceDownload(post, repeater, ds, tagProvider, db)
        
        # Now do the standard post processing work such as resetting diagrams
        from ils.diagToolkit.setpointSpreadsheet import postCallbackProcessing
        allApplicationsProcessed=postCallbackProcessing(rootContainer, ds, db, tagProvider, actionMessage="Download", recommendationStatus="Download")
    
        # If they disabled some applications then leave the spreadsheet open, otherwise dismiss it
        if allApplicationsProcessed:
            system.nav.closeParentWindow(event)
    else:
        print "The operator choose not to continue with the download."

# This looks at the data in the setpoint spreadsheet and basically looks for at least one row that is set to GO
def bookkeeping(ds):
    workToDo=False
    cnt=0
    # Check how many of the outputs the operator would like to download (GO/STOP)
    # The UI allows the user to make an application INACTIVE but then he can make an output GO. 
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")
        if rowType == "row":
            command=ds.getValueAt(row, "command")
            if string.upper(command) == 'GO':
                cnt=cnt+1
                workToDo=True
    log.info("There are %i outputs to write" % (cnt))
    return workToDo

# This verifies that the output exists and is in a state where it can accept a setpoint
def checkIfOkToDownload(repeater, ds, post, tagProvider, db):
    
    # iterate through each row of the dataset that is marked to go and make sure the controller is reachable
    # and that the setpoint is legal
    log.info("Checking if it is OK to download...")
    okToDownload=True
    unreachableCnt=0
    
    # If any one of the controllers is not reachable, then update all 
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")
        if rowType == "row":
            command=ds.getValueAt(row, "command")
            if string.upper(command) == 'GO':
                quantOutput=ds.getValueAt(row, "output")
                newSetpoint=ds.getValueAt(row, "finalSetpoint")
                tag=ds.getValueAt(row, "tag")
                tagPath="[%s]%s" % (tagProvider, tag)
                
                log.info("Checking Quant Output: %s - Tag: %s" % (quantOutput, tagPath))
                
                # The first check is to verify that the tag exists...
                exists = system.tag.exists(tagPath)
                if not(exists):
                    okToDownload = False
                    unreachableCnt=unreachableCnt+1
                    log.warn("The tag (%s) does not exist" % (tagPath))
                    insertPostMessage(post, "Error", "The tag does not exist for %s-%s" % (quantOutput, tagPath), db)
                else:
                    # The second check is to read the current SP - I guess if a controller doesn't have a SP then the
                    # odds of writing a new one successfully are low!
                    qv=system.tag.read(tagPath)
                    if not(qv.quality.isGood()):
                        okToDownload = False
                        unreachableCnt=unreachableCnt+1
                        print "The tag is bad"
                        insertPostMessage(post, "Error", "The quality of the tag %s-%s is bad (%s)" % (quantOutput, tagPath, qv.quality), db)
                    else:
                        # I'm calling a generic I/O API here which is shared with S88.  S88 can write to the OP of a controller, but I think that 
                        # the diag toolkit can only write to the SP of a controller.  (The G2 version just used stand-alone GSI variables, so it 
                        # was not obvious if we were writing to the SP or the OP, but I think we always wrote to the SP.
                        reachable,msg=confirmControllerMode(tagPath, newSetpoint, testForZero=False, checkPathToValve=True, valueType="SP")

                        if not(reachable):
                            okToDownload=False
                            unreachableCnt=unreachableCnt+1
                            ds=system.dataset.setValue(ds, row, "downloadStatus", "Config Error")
                            print "Row %i - Output %s - Tag %s is not reachable" % (row, quantOutput, tag)
                            insertPostMessage(post, "Error", "Controller %s is not reachable because %s" % (tagPath, msg), db)
    
    if okToDownload:
        log.info("It is OK to download")
    else:
        log.info("It is *NOT* OK to download - %i outputs are unreachable." % (unreachableCnt))
        repeater.templateParams=ds

    return okToDownload

def constructDownloadLogbookMessage(post, applicationName, db):
    from ils.diagToolkit.common import fetchActiveDiagnosis
    pds = fetchActiveDiagnosis(applicationName, db)
    txt = ""

    for finalDiagnosisRecord in pds:
        family=finalDiagnosisRecord['FamilyName']
        finalDiagnosis=finalDiagnosisRecord['FinalDiagnosisName']
        finalDiagnosisId=finalDiagnosisRecord['FinalDiagnosisId']
        multiplier=finalDiagnosisRecord['Multiplier']
        recommendationErrorText=finalDiagnosisRecord['RecommendationErrorText']
        print "Final Diagnosis: ", finalDiagnosis, finalDiagnosisId, recommendationErrorText
            
        if multiplier < 0.99 or multiplier > 1.01:
            txt += "       Diagnosis -- %s (multiplier = %f)\n" % (finalDiagnosis, multiplier)
        else:
            txt += "       Diagnosis -- %s\n" % (finalDiagnosis)

        if recommendationErrorText != None:
            txt += "       %s\n\n" % (recommendationErrorText) 

        from ils.diagToolkit.common import fetchSQCRootCauseForFinalDiagnosis
        rootCauseList=fetchSQCRootCauseForFinalDiagnosis(finalDiagnosis)
        for rootCause in rootCauseList:
            txt += "      %s\n" % (rootCause)

        from ils.diagToolkit.common import fetchOutputsForFinalDiagnosis
        pds, outputs=fetchOutputsForFinalDiagnosis(applicationName, family, finalDiagnosis)
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
            txt += "          the desired change in %s = %s" % (tagPath, str(feedbackOutput))
            if manualOverride:
                txt += "%s  (manually specified)" % (txt)
            txt += "\n"

            if outputLimited and feedbackOutput != 0.0:
                txt = "          change to %s adjusted to %s because %s" % (quantOutput, str(feedbackOutputConditioned), outputLimitedStatus)

    return txt


def serviceDownload(post, repeater, ds, tagProvider, db):
    # iterate through each row of the dataset that is marked to go and download it.
    log.info("Starting to download...")
    
    logbookMessage = "Download performed for the following:\n"
 
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")
        if rowType == "app":
            applicationName = ds.getValueAt(row, "application")
            logbookMessage += "  Application: %s\n" % applicationName
            firstOutputRow = True
            
        elif rowType == "row":
            command=ds.getValueAt(row, "command")
            if string.upper(command) == 'GO':
                if firstOutputRow:
                    # When we encounter the first output row, write out information about the Final diagnosis and violated SQC rules
                    firstOutputRow = False
                    logbookMessage += constructDownloadLogbookMessage(post, applicationName, db)
                    
                quantOutput=ds.getValueAt(row, "output")
                tag=ds.getValueAt(row, "tag")
                newSetpoint=ds.getValueAt(row, "finalSetpoint")
                tagPath="[%s]%s" % (tagProvider, tag)

                logbookMessage += "      download of %s to the value %f was " % (tagPath, newSetpoint)
                
                print "Row %i - Downloading %s to Output %s - Tag %s" % (row, str(newSetpoint), quantOutput, tagPath)
                success, errorMessage = write(tagPath, newSetpoint, writeConfirm=True, valueType='setpoint')
                
                if success:
                    ds = system.dataset.setValue(ds, row, "downloadStatus", "Success")
                    logbookMessage += "confirmed\n"
                    print "The write was successful"
                else:
                    print "The write FAILED because: ", errorMessage
                    ds = system.dataset.setValue(ds, row, "downloadStatus", "Error")
                    logbookMessage += "failed because of an error: %s\n" % (errorMessage)
    
    repeater.templateParams=ds
    
    from ils.common.operatorLogbook import insertForPost
    insertForPost(post, logbookMessage, db)