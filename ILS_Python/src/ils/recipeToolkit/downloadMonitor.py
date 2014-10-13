'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def start(rootContainer):
    print "Starting the download monitor timer..."
    timer = rootContainer.getComponent("Timer")
    timer.running = True

def runner(rootContainer):
    from java.util import Date

    print "\n\nStarting a download monitor cycle..."
    timer = rootContainer.getComponent("Timer")
    
    from ils.recipeToolkit.downloadComplete import downloadComplete
    
    # Check the status of pending downloads
    pending = monitor(rootContainer)
    if pending == 0:
        print "All downloads have completed (there are no pending downloads), disabling the download timer" 
        timer.running = False
        downloadComplete(rootContainer)
    
    # Check to see if we have timed out
    now = Date()
    startTime = rootContainer.downloadStartTime
    deltaTime = now.getTime() - startTime.getTime()
    print "The download has been running for: ", deltaTime
    if deltaTime > rootContainer.downloadTimeout * 1000:
        print "The download has exceeded the allowed time, disabling the download timer and aborting the download!" 
        timer.running = False
        downloadComplete(rootContainer)


# This is called from a timer on the window and monitors the download.  Part of monitoring is to 
# animate the table to indicate the success or failure of a tag.
# Monitor every row of the table that is marked to be downloaded
def monitor(rootContainer):
    import string

    print "Starting project.recipe.downloadMonitor.monitor()"
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
    print "...processing %i rows" % len(pds)
    for record in pds:
        step = record["Step"]
        download = record["Download"]
        downloadType = string.upper(record["Download Type"])
        downloadStatus = string.upper(record["Download Status"])

        if download:
            downloads = downloads + 1

            if downloadStatus == 'PENDING':
                print "Checking step", step
                storTagName = record["Store Tag"]
                
                # Even though these are 'IMMEDIATE' writes, it will take a cycle for OPC tags
                if downloadType == 'IMMEDIATE' or downloadType == 'DEFERRED VALUE' or downloadType == 'DEFERRED LOW LIMIT' or downloadType == 'DEFERRED HIGH LIMIT':
                    writeLocation = record["Write Location"]    
                    pendVal = record["Pend"]
                    
                    if writeLocation == localG2WriteAlias:
                        from ils.recipeToolkit.common import formatLocalTagName
                        storTagName = formatLocalTagName(provider, storTagName)
                        val = system.tag.read(storTagName).value
                        print "Comparing local value %s to %s" % (str(pendVal), str(val))
                        ds = system.dataset.setValue(ds, i, "Stor", val)
                        ds = system.dataset.setValue(ds, i, "Comp", val)
                        from ils.common.util import equalityCheck
                        if equalityCheck(pendVal, val, recipeMinimumDifference, recipeMinimumRelativeDifference):
                            successes = successes + 1
                            status = "Success"
                            ds = system.dataset.setValue(ds, i, "Download Status", "Success")
                        else:
                            failures = failures + 1
                            status = "Failure"
                            ds = system.dataset.setValue(ds, i, "Download Status", "Failure")
                        from ils.recipeToolkit.log import logDetail
                        #TODO Get these 
                        compare = None
                        recommend = None
                        reason = ""
                        logDetail(logId, storTagName, pendVal, status, val, compare, recommend, reason)
                    else:
                        from ils.recipeToolkit.common import formatTagName
                        storTagName = formatTagName(provider, recipeKey, storTagName)
                        writeStatus = system.tag.read(storTagName + '/WriteStatus').value
                        val = system.tag.read(storTagName + '/tag').value
                        ds = system.dataset.setValue(ds, i, "Stor", val)
                        ds = system.dataset.setValue(ds, i, "Comp", val)
                        print "  ", storTagName, " -> ", val, writeStatus
                        if string.upper(writeStatus) == 'SUCCESS':
                            successes = successes + 1
                            ds = system.dataset.setValue(ds, i, "Download Status", "Success")
                        elif string.upper(writeStatus) == 'FAILURE':
                            failures = failures + 1 
                            ds = system.dataset.setValue(ds, i, "Download Status", "Failure")
                        else:
                            pending = pending + 1 
            
                else:
                    print "Unexpected download type: ", downloadType, " on line ", i

            elif downloadStatus == 'SUCCESS':
                successes = successes + 1
                
            elif downloadStatus == 'FAILURE':
                failures = failures + 1            
            
            else:
                print "Unexpected download status: ", downloadStatus

        i = i + 1

    print "There are %i downloads (%i success, %i failed, %i pending)" % (downloads, successes, failures, pending)
    table.processedData = ds
    from ils.recipeToolkit.refresh import refreshVisibleData
    refreshVisibleData(table)
    
    return pending