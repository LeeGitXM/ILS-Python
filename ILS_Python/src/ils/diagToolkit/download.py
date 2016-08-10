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

def downloadCallback(rootContainer):
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
        return;

    okToDownload=checkIfOkToDownload(repeater, ds, post, tagProvider, db)
    if not(okToDownload):
        insertPostMessage(post, "Warning", "SPs were NOT downloaded due to a controller configuration error", db)
        # Even though this is a warning, Warning boxes are not modal and these are!
        system.gui.messageBox("Cancelling download because one or more of the controllers is unreachable!")
        return

    system.gui.messageBox("The Download will begin as soon as you press OK and may take a while, please be patient.")
    
    serviceDownload(repeater, ds, tagProvider)


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
                
                log.trace("Checking Quant Output: %s - Tag: %s" % (quantOutput, tagPath))
                
                # The first check is to verify that the tag exists...
                exists = system.tag.exists(tagPath)
                if not(exists):
                    okToDownload = False
                    unreachableCnt=unreachableCnt+1
                    print "The tag does not exist"
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
                        reachable,msg=confirmControllerMode(tagPath, newSetpoint, testForZero=False, checkPathToValve=True, valueType="SP", logger=log)

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

def serviceDownload(repeater, ds, tagProvider):
    # iterate through each row of the dataset that is marked to go and download it.
    log.info("Starting to download...")
 
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")
        if rowType == "row":
            command=ds.getValueAt(row, "command")
            if string.upper(command) == 'GO':
                quantOutput=ds.getValueAt(row, "output")
                tag=ds.getValueAt(row, "tag")
                newSetpoint=ds.getValueAt(row, "finalSetpoint")
                tagPath="[%s]%s" % (tagProvider, tag)
                
                print "Row %i - Downloading %s to Output %s - Tag %s" % (row, str(newSetpoint), quantOutput, tagPath)
                success, errorMessage = write(tagPath, newSetpoint, writeConfirm=True, valueType='setpoint')
                
                if success:
                    ds = system.dataset.setValue(ds, row, "downloadStatus", "Success")
                    print "The write was successful"
                else:
                    print "The write FAILED because: ", errorMessage
                    ds = system.dataset.setValue(ds, row, "downloadStatus", "Error")
    
    repeater.templateParams=ds
    return