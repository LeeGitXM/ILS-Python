'''
Created on Sep 10, 2014

@author: Pete
'''

import system, time
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit.download")

def automatedRunner(dsProcessed, provider, recipeKey, grade, version, logId, downloadStartTime, downloadTimeout, database):
    from java.util import Date
    
    log.trace("Starting the automated download monitor...")
    
    localG2WriteAlias = system.tag.read("[" + provider + "]/Recipe/Constants/localG2WriteAlias").value
    recipeMinimumDifference = system.tag.read("[" + provider + "]/Recipe/Constants/recipeMinimumDifference").value
    recipeMinimumRelativeDifference = system.tag.read("[" + provider + "]/Recipe/Constants/recipeMinimumRelativeDifference").value
       
    from ils.recipeToolkit.downloadComplete import downloadCompleteRunner
    
    # Check the status of pending downloads
    pending = 1
    deltaTime = 0
    while pending > 0 and deltaTime < downloadTimeout * 1000:
        time.sleep(5)
#        pending = monitor(rootContainer)
        pending, dsProcessed = monitor(provider, recipeKey, localG2WriteAlias, recipeMinimumDifference, recipeMinimumRelativeDifference, logId, dsProcessed, database)

        # Check to see if we have timed out
        now = Date()
        deltaTime = now.getTime() - downloadStartTime.getTime()
        log.trace("The download has been running for: %s seconds" % (str(deltaTime / 1000.0)))
        
    if deltaTime > downloadTimeout * 1000:
        log.info("The download has exceeded the allowed time, aborting the download monitor!") 
        downloadCompleteRunner(dsProcessed, logId, recipeKey, grade, version, "Automated", "Grade Change", database)
    
    if pending == 0:
        log.info("All downloads have completed (there are no pending downloads), ending the download monitor!")
        downloadCompleteRunner(dsProcessed, logId, recipeKey, grade, version,  "Automated", "Grade Change", database)
        

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
    provider = rootContainer.getPropertyValue("provider")
    recipeKey = rootContainer.getPropertyValue("recipeKey")
    logId = rootContainer.logId
    
    localG2WriteAlias = system.tag.read("/Recipe/Constants/localG2WriteAlias").value
    
    table = rootContainer.getComponent("Power Table")
    recipeMinimumDifference = table.getPropertyValue("recipeMinimumDifference")
    recipeMinimumRelativeDifference = table.getPropertyValue("recipeMinimumRelativeDifference")
    ds = table.processedData
    
    pending, ds = monitor(provider, recipeKey, localG2WriteAlias, recipeMinimumDifference, recipeMinimumRelativeDifference, logId, ds)

    table.processedData = ds
    from ils.recipeToolkit.refresh import refreshVisibleData
    refreshVisibleData(table)
    
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
def monitor(provider, recipeKey, localG2WriteAlias, recipeMinimumDifference, recipeMinimumRelativeDifference, logId, ds, database = ""):
    import string
    from ils.recipeToolkit.log import logDetail

    log.trace("  Starting project.recipe.downloadMonitor.monitor()")
    
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
                compTagName = record["Comp Tag"]
                recommendVal = record["Recc"]
                reason = ""
                
                # Even though these are 'IMMEDIATE' writes, it will take a cycle for OPC tags
                if downloadType == 'IMMEDIATE' or downloadType == 'DEFERRED VALUE' or downloadType == 'DEFERRED LOW LIMIT' or downloadType == 'DEFERRED HIGH LIMIT':
                    writeLocation = record["Write Location"]    
                    pendVal = record["Pend"]
                    reason = record["Reason"]
                    
                    if writeLocation == localG2WriteAlias:
                        from ils.recipeToolkit.common import formatLocalTagName
                        tagName = formatLocalTagName(provider, storTagName)
                        storVal = system.tag.read(tagName).value
                        tagName = formatLocalTagName(provider, compTagName)
                        compVal = system.tag.read(tagName).value
                        log.trace("Comparing local value %s to %s" % (str(pendVal), str(storVal)))
                        ds = system.dataset.setValue(ds, i, "Stor", storVal)
                        ds = system.dataset.setValue(ds, i, "Comp", compVal)
                        from ils.io.util import equalityCheck
                        if equalityCheck(pendVal, storVal, recipeMinimumDifference, recipeMinimumRelativeDifference):
                            successes = successes + 1
                            status = "Success"
                            errorMessage = ""
                        else:
                            failures = failures + 1
                            status = "Failure"
                            errorMessage = "Local write error"
                            
                        logDetail(logId, storTagName, pendVal, status, storVal, compVal, recommendVal, reason, errorMessage, database)
                        ds = system.dataset.setValue(ds, i, "Download Status", status)
                        
                    else:
                        from ils.recipeToolkit.common import formatTagName
                        writeStatus = system.tag.read(formatTagName(provider, recipeKey, storTagName) + '/writeStatus').value
                        
                        if string.upper(writeStatus) == 'SUCCESS' or string.upper(writeStatus) == 'FAILURE':
                            if string.upper(writeStatus) == 'SUCCESS':
                                successes = successes + 1
                                status = 'Success'
                                errorMessage = ''
                            else:
                                failures = failures + 1 
                                status = 'Failure'
                                errorMessage = system.tag.read(formatTagName(provider, recipeKey, storTagName) + '/writeErrorMessage').value

                            ds = system.dataset.setValue(ds, i, "Download Status", status)
                            storVal = system.tag.read(formatTagName(provider, recipeKey, storTagName) + '/value').value
                            ds = system.dataset.setValue(ds, i, "Stor", storVal)
                            compVal = system.tag.read(formatTagName(provider, recipeKey, compTagName) + '/value').value
                            ds = system.dataset.setValue(ds, i, "Comp", compVal)
                            log.trace("  %s -> %s - %s" % (storTagName, storVal, writeStatus))
                            logDetail(logId, record["Store Tag"], pendVal, status, storVal, compVal, recommendVal, reason, errorMessage, database) 
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

    
    return pending, ds