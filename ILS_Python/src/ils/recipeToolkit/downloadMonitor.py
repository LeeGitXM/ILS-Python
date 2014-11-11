'''
Created on Sep 10, 2014

@author: Pete
'''

import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit.download")

def start(rootContainer):
    log.info("Starting the download monitor timer...")
    timer = rootContainer.getComponent("Timer")
    timer.running = True

def runner(rootContainer):
    from java.util import Date

    log.trace("Starting a download monitor cycle...")
    timer = rootContainer.getComponent("Timer")
    
    from ils.recipeToolkit.downloadComplete import downloadComplete
    
    # Check the status of pending downloads
    pending = monitor(rootContainer)
    if pending == 0:
        log.info("All downloads have completed (there are no pending downloads), disabling the download timer")
        timer.running = False
        downloadComplete(rootContainer)
    
    # Check to see if we have timed out
    now = Date()
    startTime = rootContainer.downloadStartTime
    deltaTime = now.getTime() - startTime.getTime()
    log.trace("The download has been running for: %s seconds" % (str(deltaTime / 1000.0)))
    if deltaTime > rootContainer.downloadTimeout * 1000:
        log.info("The download has exceeded the allowed time, disabling the download timer and aborting the download!") 
        timer.running = False
        downloadComplete(rootContainer)


# This is called from a timer on the window and monitors the download.  Part of monitoring is to 
# animate the table to indicate the success or failure of a tag.
# Monitor every row of the table that is marked to be downloaded
def monitor(rootContainer):
    import string
    from ils.recipeToolkit.log import logDetail

    log.trace("  Starting project.recipe.downloadMonitor.monitor()")
    provider = rootContainer.getPropertyValue("provider")
    recipeKey = rootContainer.getPropertyValue("recipeKey")
    table = rootContainer.getComponent("Power Table")
    localG2WriteAlias = system.tag.read("/Recipe/Constants/localG2WriteAlias").value
    recipeMinimumDifference = table.getPropertyValue("recipeMinimumDifference")
    recipeMinimumRelativeDifference = table.getPropertyValue("recipeMinimumRelativeDifference")

    logId = rootContainer.logId

    ds = table.processedData
    pds = system.dataset.toPyDataSet(ds)

    i = 0
    downloads = 0
    successes = 0
    failures = 0
    pending = 0
    log.trace("  ...processing %i rows" % len(pds))
    for record in pds:
        step = record["Step"]
        download = record["Download"]
        downloadType = string.upper(record["Download Type"])
        downloadStatus = string.upper(record["Download Status"])

        if download:
            downloads = downloads + 1

            if downloadStatus == 'PENDING':
                log.trace("Checking step: %s" % (str(step)))
                storTagName = record["Store Tag"]
                
                #TODO Get these 
                compareVal = record["Comp"]
                recommendVal = record["Recc"]
                reason = ""
                
                # Even though these are 'IMMEDIATE' writes, it will take a cycle for OPC tags
                if downloadType == 'IMMEDIATE' or downloadType == 'DEFERRED VALUE' or downloadType == 'DEFERRED LOW LIMIT' or downloadType == 'DEFERRED HIGH LIMIT':
                    writeLocation = record["Write Location"]    
                    pendVal = record["Pend"]
                    reason = record["Reason"]
                    
                    if writeLocation == localG2WriteAlias:
                        from ils.recipeToolkit.common import formatLocalTagName
                        storTagName = formatLocalTagName(provider, storTagName)
                        val = system.tag.read(storTagName).value
                        log.trace("Comparing local value %s to %s" % (str(pendVal), str(val)))
                        ds = system.dataset.setValue(ds, i, "Stor", val)
                        ds = system.dataset.setValue(ds, i, "Comp", val)
                        from ils.common.util import equalityCheck
                        if equalityCheck(pendVal, val, recipeMinimumDifference, recipeMinimumRelativeDifference):
                            successes = successes + 1
                            logDetail(logId, record["Store Tag"], pendVal, "Success", val, compareVal, recommendVal, reason, "")
                            ds = system.dataset.setValue(ds, i, "Download Status", "Success")
                        else:
                            failures = failures + 1
                            logDetail(logId, record["Store Tag"], pendVal, "Failure", val, compareVal, recommendVal, reason, "Local write error")
                            ds = system.dataset.setValue(ds, i, "Download Status", "Failure")
                        
                    else:
                        from ils.recipeToolkit.common import formatTagName
                        storTagName = formatTagName(provider, recipeKey, storTagName)
                        writeStatus = system.tag.read(storTagName + '/writeStatus').value
                        val = system.tag.read(storTagName + '/tag').value
                        ds = system.dataset.setValue(ds, i, "Stor", val)
                        ds = system.dataset.setValue(ds, i, "Comp", val)
                        log.trace("  %s -> %s - %s" % (storTagName, val, writeStatus))
                        if string.upper(writeStatus) == 'SUCCESS':
                            successes = successes + 1
                            ds = system.dataset.setValue(ds, i, "Download Status", "Success")
                            logDetail(logId, record["Store Tag"], pendVal, "Success", val, compareVal, recommendVal, reason, "")
                        elif string.upper(writeStatus) == 'FAILURE':
                            failures = failures + 1 
                            ds = system.dataset.setValue(ds, i, "Download Status", "Failure")
                            errorMessage = system.tag.read(storTagName + '/writeErrorMessage').value
                            logDetail(logId, record["Store Tag"], pendVal, "Failure", val, compareVal, recommendVal, reason, errorMessage)
                        else:
                            pending = pending + 1 
            
                else:
                    log.info("Unexpected download type: %s on line %s" % (downloadType, str(i)))

            elif downloadStatus == 'SUCCESS':
                successes = successes + 1
                
            elif downloadStatus == 'FAILURE':
                failures = failures + 1            
            
            else:
                print "Unexpected download status: ", downloadStatus

        i = i + 1

    log.info("There are %i downloads (%i success, %i failed, %i pending)" % (downloads, successes, failures, pending))
    table.processedData = ds
    from ils.recipeToolkit.refresh import refreshVisibleData
    refreshVisibleData(table)
    
    return pending