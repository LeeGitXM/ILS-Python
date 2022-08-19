'''
Created on Feb 4, 2015

@author: Pete
'''

import system, string, time
from __builtin__ import False
from ils.diagToolkit.setpointSpreadsheet import hideDetailMap
from ils.io.api import confirmControllerMode, write
from ils.io.util import getOuterUDT, readTag
from ils.queue.message import insertPostMessage

from ils.log import getLogger
log = getLogger(__name__)

def downloadLogbookTestCallback(event, rootContainer):
    from ils.config.client import getTagProvider, getDatabase
    tagProvider=getTagProvider()
    db=getDatabase()
    post=rootContainer.post
    
    repeater=rootContainer.getComponent("Template Repeater")
    ds = repeater.templateParams
    
    from ils.diagToolkit.downloader import Downloader
    downloader = Downloader(post, ds, tagProvider, db)
    downloader.downloadMessage()

# This is called from the download button on the setpoint spreadsheet.
def downloadCallback(event, rootContainer):
    log.infof("In %s.downloadCallback()", __name__)
    
    from ils.config.client import getTagProvider, getDatabase
    tagProvider=getTagProvider()
    db=getDatabase()
    project = system.util.getProjectName()
    
    post=rootContainer.post
    
    repeater=rootContainer.getComponent("Template Repeater")
    
    from ils.diagToolkit.setpointSpreadsheet import logAction
    logAction("DOWNLOAD", repeater)
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

    confirmationEnabled = readTag("[" + tagProvider + "]/Configuration/DiagnosticToolkit/downloadConfirmationEnabled").value
    if confirmationEnabled:
        ans = system.gui.confirm("There are setpoints to download and the controllers are in the correct mode, press 'Yes' to proceed with the downlaod.")
    else:
        ans = True

    if ans:
        # If there is an open recommendation map then close it
        hideDetailMap()
        
        # Send a serviceDownload message to the gateway
        payload = {"post": post, "tagProvider": tagProvider, "database": db, "ds": ds}
        log.infof("Sending serviceDownload message to the gateway...")
        log.infof("Payload: %s", str(payload))
        system.util.sendMessage(project, "serviceDownload", payload, "G")
        
        # Set the download active flag on the UI that triggers the status message and database updates...
        rootContainer.downloadActive = True
        
        # Set a flag that will be used when the notification arrives.  This is only relevent when two applications are present but one of them was INACTIVE
        rootContainer.lastAction = "download"
        
        from ils.diagToolkit.setpointSpreadsheet import updateDownloadActiveFlag
        updateDownloadActiveFlag(post, True, db)

    else:
        print "The operator choose not to continue with the download."

# This looks at the data in the setpoint spreadsheet and basically looks for at least one row that is set to GO
def bookkeeping(ds):
    log.infof("In %s.bookkeeping()", __name__)
    workToDo=False
    cnt=0
    # Check how many of the outputs the operator would like to download (GO/STOP)
    # The UI allows the user to make an application INACTIVE but then he can make an output GO. 
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")
        if rowType == "row":
            command=ds.getValueAt(row, "command")
            downloadStatus=ds.getValueAt(row, "downloadStatus")
            if string.upper(command) == 'GO' and string.upper(downloadStatus) in ['', 'ERROR']:
                cnt=cnt+1
                workToDo=True
    log.infof("...there are %i outputs to write", cnt)
    return workToDo


def checkIfOkToDownload(repeater, ds, post, tagProvider, db):
    '''
    This verifies that the output exists and is in a state where it can accept a setpoint.
    Iterate through each row of the dataset that is marked to go and make sure the controller is reachable
    and that the setpoint is legal
    '''
    log.infof("In %s.checkIfOkToDownload() - Checking if it is OK to download...", __name__)
    okToDownload=True
    unreachableCnt=0
    
    # If any one of the controllers is not reachable, then update all 
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")
        if rowType == "row":
            command=ds.getValueAt(row, "command")
            downloadStatus=ds.getValueAt(row, "downloadStatus")
            if string.upper(command) == 'GO' and string.upper(downloadStatus) in ['', 'ERROR']:
                quantOutput=ds.getValueAt(row, "output")
                newSetpoint=ds.getValueAt(row, "finalSetpoint")
                tag=ds.getValueAt(row, "tag")
                tagPath="[%s]%s" % (tagProvider, tag)
                
                from ils.io.util import getOutputForTagPath
                outputTagPath=getOutputForTagPath(tagProvider, tagPath, "sp")
                
                log.infof("Checking Quant Output: %s - Tag: %s", quantOutput, outputTagPath)
                
                # The first check is to verify that the tag exists...
                exists = system.tag.exists(outputTagPath)
                if not(exists):
                    okToDownload = False
                    unreachableCnt=unreachableCnt+1
                    log.warnf("The tag (%s) does not exist", tagPath)
                    insertPostMessage(post, "Error", "The tag does not exist for %s-%s" % (quantOutput, tagPath), db)
                else:
                    # The second check is to read the current SP - I guess if a controller doesn't have a SP then the
                    # odds of writing a new one successfully are low!
                    qv=readTag(outputTagPath)
                    if not(qv.quality.isGood()):
                        okToDownload = False
                        unreachableCnt=unreachableCnt+1
                        log.warnf("The tag is bad!")
                        insertPostMessage(post, "Error", "The quality of the tag %s-%s is bad (%s)" % (quantOutput, outputTagPath, qv.quality), db)
                    else:
                        # I'm calling a generic I/O API here which is shared with S88.  S88 can write to the OP of a controller, but I think that 
                        # the diag toolkit can only write to the SP of a controller.  (The G2 version just used stand-alone GSI variables, so it 
                        # was not obvious if we were writing to the SP or the OP, but I think we always wrote to the SP.
                        reachable,msg,itemId=confirmControllerMode(tagPath, newSetpoint, testForZero=False, checkPathToValve=True, valueType="SP")

                        if not(reachable):
                            okToDownload=False
                            unreachableCnt=unreachableCnt+1
                            ds=system.dataset.setValue(ds, row, "downloadStatus", "Config Error")
                            log.arnf("Row %i - Output %s - Tag %s is not reachable", row, quantOutput, tag)
                            insertPostMessage(post, "Error", "Controller %s is not reachable because %s (tag: %s)" % (itemId, msg, tagPath), db)
    
    if okToDownload:
        log.infof("It is OK to download")
    else:
        log.infof("It is *NOT* OK to download - %i outputs are unreachable.", unreachableCnt)
        repeater.templateParams=ds

    return okToDownload

'''
This should run in the gateway to free up the client.  Status is communicated via the database
'''
def serviceDownloadMessageHandler(payload):
    from ils.diagToolkit.downloader import Downloader
    log.infof("In %s.serviceDownloadMessageHandler() - Received a service download message", __name__)
    log.tracef("The payload is: %s", str(payload))
    
    post = payload.get("post", None)
    ds = payload.get("ds", None)
    tagProvider = payload.get("tagProvider", None)
    db = payload.get("database", None)
    
    log.tracef("Post:         %s", post)
    log.tracef("Tag Provider: %s", tagProvider)
    log.tracef("Database:     %s", db)
    log.tracef("Dataset:      %s", ds)  
    
    downloader = Downloader(post, ds, tagProvider, db)
    downloader.download()
