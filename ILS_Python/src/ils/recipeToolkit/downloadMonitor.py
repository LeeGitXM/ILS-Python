'''
Created on Sep 10, 2014

@author: Pete
'''

import system, time
from ils.common.config import getTagProvider
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit.download.monitor")

# This is called for an automated download and runs in gateway scope.
def automatedRunner(dsProcessed, provider, recipeKey, grade, version, logId, downloadStartTime, downloadTimeout, database):
    from java.util import Date
    
    log.trace("Starting the automated download monitor...")
    
    localWriteAlias = system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/localWriteAlias").value
    recipeMinimumDifference = system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/recipeMinimumDifference").value
    recipeMinimumRelativeDifference = system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/recipeMinimumRelativeDifference").value
       
    from ils.recipeToolkit.downloadComplete import downloadCompleteRunner
    
    # Check the status of pending downloads
    pending = 1
    deltaTime = 0
    while pending > 0 and deltaTime < downloadTimeout * 1000:
        time.sleep(5)
#        pending = monitor(rootContainer)
        pending, dsProcessed = monitor(provider, recipeKey, localWriteAlias, recipeMinimumDifference, recipeMinimumRelativeDifference, logId, dsProcessed, database)

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
    timer = rootContainer.getComponent("Monitor Timer")
    timer.running = True

# This is called from the timer widget on the Recipe viewer screen in client scope.
def runner(rootContainer):
    from java.util import Date

    log.trace("Starting a download monitor cycle...")
    timer = rootContainer.getComponent("Monitor Timer")
    
    from ils.recipeToolkit.downloadComplete import downloadComplete
    
    # Check the status of pending downloads
    provider = rootContainer.getPropertyValue("provider")
    familyName = rootContainer.getPropertyValue("familyName")
    logId = rootContainer.logId
    
    localWriteAlias = system.tag.read("/Configuration/RecipeToolkit/localWriteAlias").value
    
    table = rootContainer.getComponent("Power Table")
    recipeMinimumDifference = table.getPropertyValue("recipeMinimumDifference")
    recipeMinimumRelativeDifference = table.getPropertyValue("recipeMinimumRelativeDifference")
    ds = table.processedData
    
    pending, ds = monitor(provider, familyName, localWriteAlias, recipeMinimumDifference, recipeMinimumRelativeDifference, logId, ds)

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
def monitor(provider, familyName, localWriteAlias, recipeMinimumDifference, recipeMinimumRelativeDifference, logId, ds, database = ""):
    import string
    from ils.recipeToolkit.log import logDetail

    log.trace("  Starting project.recipe.downloadMonitor.monitor()")
    
    
    productionProvider = getTagProvider()     # Get the production tag provider.
    
    recipeWriteEnabled = system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/recipeWriteEnabled").value
    globalWriteEnabled = system.tag.read("[" + provider + "]/Configuration/Common/writeEnabled").value
    writeEnabled = provider != productionProvider or (recipeWriteEnabled and globalWriteEnabled)

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
                storTagName = record["Store Tag"]
                compTagName = record["Comp Tag"]
                recommendVal = record["Recc"]
                log.trace("Checking step: %s - %s - %s" % (str(step), storTagName, str(recommendVal)))
                reason = ""

                # Even though these are 'IMMEDIATE' writes, it will take a cycle for OPC tags
                if downloadType == 'IMMEDIATE' or downloadType == 'DEFERRED VALUE' or downloadType == 'DEFERRED LOW LIMIT' or downloadType == 'DEFERRED HIGH LIMIT':
                    writeLocation = record["Write Location"]
                        
                    pendVal = record["Pend"]
                    reason = record["Reason"]

                    if writeEnabled:                    
                        if writeLocation == localWriteAlias:
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
                            tagName=formatTagName(provider, familyName, storTagName) + '/writeStatus'
                            qv = system.tag.read(tagName)
                            writeStatus=str(qv.value)
                            
                            if string.upper(writeStatus) == 'SUCCESS' or string.upper(writeStatus) == 'FAILURE':
                                if string.upper(writeStatus) == 'SUCCESS':
                                    successes = successes + 1
                                    status = 'Success'
                                    errorMessage = ''
                                else:
                                    failures = failures + 1 
                                    status = 'Failure'
                                    errorMessage = system.tag.read(formatTagName(provider, familyName, storTagName) + '/writeErrorMessage').value
    
                                ds = system.dataset.setValue(ds, i, "Download Status", status)
                                storVal = system.tag.read(formatTagName(provider, familyName, storTagName) + '/value').value
                                ds = system.dataset.setValue(ds, i, "Stor", storVal)
                                compVal = system.tag.read(formatTagName(provider, familyName, compTagName) + '/value').value
                                ds = system.dataset.setValue(ds, i, "Comp", compVal)
                                log.trace("  %s -> %s - %s" % (storTagName, storVal, writeStatus))
                                logDetail(logId, record["Store Tag"], pendVal, status, storVal, compVal, recommendVal, reason, errorMessage, database) 
                            else:
                                pending = pending + 1 
                    else:
                        # Writing is inhibited so this will never pass...
                        log.info("Skipping write to %s because writing is inhibited" % (storTagName))
                        failures = failures + 1
                        status = 'Failure - Write inhibited'
                        ds = system.dataset.setValue(ds, i, "Download Status", status)
                else:
                    log.info("Unexpected download type: %s on line %s" % (downloadType, str(i)))

            elif downloadStatus == 'SUCCESS':
                successes = successes + 1
                
            elif downloadStatus == 'FAILURE':
                failures = failures + 1            
            
            else:
                log.trace("Unexpected download status in step: %s - %s" % (str(step), downloadStatus))

        i = i + 1

    log.info("There are %i downloads (%i success, %i failed, %i pending)" % (downloads, successes, failures, pending))

    
    return pending, ds