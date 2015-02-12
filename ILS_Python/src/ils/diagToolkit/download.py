'''
Created on Feb 4, 2015

@author: Pete
'''

import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.diagToolkit.downlload")

#
def downloadCallback(rootContainer):
    from ils.queue.post import postConsoleMessage
    log.info("In downloadCallback()")
    console=rootContainer.console
    
    repeater=rootContainer.getComponent("Template Repeater")
    ds = repeater.templateParams
    
    #TODO - Do I need to check if there is a download in progress
        
    workToDo=bookkeeping(ds)
    if not(workToDo):
        # Even though this is a warning, Warning boxes are not modal and these are!
        system.gui.messageBox("Cancelling download because there is no work to be done!")
        return;

    okToDownload=checkIfOkToDownload(repeater, ds)
    if not(okToDownload):
        postConsoleMessage(console, "Warning", "SPs were NOT downloaded due to a controller configuration error")
        # Even though this is a warning, Warning boxes are not modal and these are!
        system.gui.messageBox("Cancelling download because one or more of the controllers is unreachable!")
        return

    system.gui.messageBox("The Download will begin as soon as you press OK and may take a while, please be patient.")
    
    serviceDownload(repeater, ds)

    postConsoleMessage(console, "Info", "This is a test")

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

def checkIfOkToDownload(repeater, ds):
    
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
                quantOutput=ds.getValueAt(row, "tag")
                tag=ds.getValueAt(row, "tag")
                
                reachable=True
                if not(reachable):
                    okToDownload=False
                    unreachableCnt=unreachableCnt+1
                    ds=system.dataset.setValue(ds, row, "downloadStatus", "Config Error")
                    print "Row %i - Output %s - Tag %s is not reachable" % (row, quantOutput, tag)
    
    if okToDownload:
        log.info("It is OK to download")
    else:
        log.info("It is *NOT* OK to download - %i outputs are unreachable." % (unreachableCnt))
        repeater.templateParams=ds

    return okToDownload

def serviceDownload(repeater, ds):
    
    # iterate through each row of the dataset that is marked to go and make sure the controller is reachable
    # and that the setpoint is legal
    log.info("Starting to download...")
 
    for row in range(ds.rowCount):
        rowType=ds.getValueAt(row, "type")
        if rowType == "row":
            command=ds.getValueAt(row, "command")
            if string.upper(command) == 'GO':
                quantOutput=ds.getValueAt(row, "tag")
                tag=ds.getValueAt(row, "tag")
                
                print "Downloading: Row %i - Output %s - Tag %s" % (row, quantOutput, tag)
    
    return