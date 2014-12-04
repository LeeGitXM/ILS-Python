'''
Created on Sep 10, 2014

@author: Pete
'''
import system
import ils.common.util as util
import ils.recipeToolkit.common as recipeToolkit_common
import ils.recipeToolkit.downloadMonitor as recipeToolkit_downloadMonitor
import ils.recipeToolkit.fetch as recipeToolkit_fetch
import ils.recipeToolkit.log as recipeToolkit_log
import ils.recipeToolkit.refresh as recipeToolkit_refresh
import ils.recipeToolkit.update as recipeToolkit_update
import ils.recipeToolkit.viewRecipe as recipeToolkit_viewRecipe
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit.download")

def automatedDownloadHandler(tagPath, grade):
    
    # Get the path to the UDT so I can get the other tags that configure the download
    tagPath = str(tagPath)
    if tagPath.endswith('/grade'):
        parentTagPath = tagPath[:len(tagPath) - 6]
    else:
        parentTagPath = tagPath

    if grade == "" or grade == None:
        log.trace('Exiting automatedDownloadHandler because a NULL grade was detected.')
        return
    
    automatedDownload = system.tag.read(parentTagPath + "/automatedDownload").value
    post = system.tag.read(parentTagPath + "/post").value
    project = system.tag.read(parentTagPath + "/project").value
    database = system.tag.read(parentTagPath + "/database").value
    recipeKey = system.tag.read(parentTagPath + "/recipeKey").value
    
    grade = str(grade)

    from ils.recipeToolkit.fetch import  fetchHighestVersion
    version = fetchHighestVersion(recipeKey, grade, database)
    if version < 0:
        log.error("Aborting the automated download because a recipe was not found for Unit: %s, Grade %s"% (str(recipeKey), str(grade)))
        return

    log.info("******************************")
    log.info("Starting an automated recipe download of %s - %s - %s (Post: %s, Automated: %s)" % (project, recipeKey, grade, post, str(automatedDownload)))
    log.info("******************************")

    if automatedDownload:
        fullyAutomatedDownload(post, project, database, recipeKey, grade, version)
    else:
        # Send a message to open the 
        log.trace("Sending a message to every client to post a download GUI")
        system.util.sendMessage(project, "automatedDownload", {"post": post, "recipeKey": recipeKey, "grade": grade, "version": version}, 'C')


# Start a fully automatic lights out automatic download
def fullyAutomatedDownload(post, project, database, recipeKey, grade, version):
    log.info("Setting up a fully automated download\n  Post: %s, Project: %s, Database: %s, Recipe Key: %s, Grade: %s, Version: %s" % (post, project, database, recipeKey, grade, str(version)))
    
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    
    # fetch the recipe map which will specify the database and table containing the recipe
    recipeMap = recipeToolkit_fetch.recipeMap(recipeKey, database)
    status = recipeMap['Status']
    timestamp = recipeMap['Timestamp']
    print "Status:", status, timestamp

    # Fetch the recipe
    pds = recipeToolkit_fetch.details(recipeKey, grade, version, database)

    # Create the processed data set by adding some columns to the raw recipe data. 
    dsProcessed = recipeToolkit_viewRecipe.update(pds)

    # Reset the recipe detail objects
    recipeToolkit_viewRecipe.resetRecipeDetails(provider, recipeKey)

    # Create any OPC tags that are required by the recipe
    dsProcessed, tags = recipeToolkit_viewRecipe.createOPCTags(dsProcessed, provider, recipeKey, database)
    
    # Refresh the table with data from the DCS and determine what needs to be downloaded
    dsProcessed = recipeToolkit_refresh.automatedRefresh(recipeKey, dsProcessed, database)

    writeEnabled = system.tag.read("[" + provider + "]/Recipe/Constants/recipeWriteEnabled")
    downloadTimeout = system.tag.read("[" + provider + "]/Recipe/Constants/downloadTimeout").value
    print "The download timeout is ", downloadTimeout, " seconds"
    
    log.info("Downloading recipe <%s> (RecipeWriteEnabled: %s)..." % (recipeKey, str(writeEnabled)))
    
    recipeToolkit_update.recipeMapStatus(recipeKey, 'Processing Download', database)

    # Save the time that the download started so that we know when to stop monitoring it.
    downloadStartTime = util.getDate(database)

    resetTags(dsProcessed, provider, recipeKey)

    unit = recipeKey
    unitId = recipeToolkit_fetch.fetchUnitId(unit, database)

    # Open a master download record for this download    
    logId = recipeToolkit_log.logMaster(unitId, grade, version, "Automatic", database)

    # Normally at this time we would log skipped tags, but since this automated, there can't be skipped tags
    
    # Based on the recipe and the current values in the table, determine the rows to write and update the 
    # processedData property of the table
    dsProcessed = writeImmediate(dsProcessed, provider, recipeKey, logId, writeEnabled)
    dsProcessed = writeDeferred(dsProcessed, provider, recipeKey, logId, writeEnabled)

    # Start the download monitor
    recipeToolkit_downloadMonitor.automatedRunner(dsProcessed, provider, recipeKey, grade, version, logId, downloadStartTime, downloadTimeout, database)
    
    log.info("Completed automated download!")


def downloadCallback(rootContainer):
    log.info("Starting a download...")

    recipeKey = rootContainer.getPropertyValue("recipeKey")
    print recipeKey
    
    recipeMap = recipeToolkit_fetch.recipeMap(recipeKey)
    if recipeMap == 'Not Found':
        system.gui.errorBox('Error fetching the recipe map from the database for: %s' % (recipeMap))
        return
     
    from ils.common.cast import toBool
    confirmDownload = toBool(recipeMap["ConfirmDownload"])
    if confirmDownload:
        confirmation = system.gui.confirm("Really download the values in the spreadsheet to the DCS?")
        if not(confirmation): 
            return

    # Insert a message into the log book queue that we are starting a manual download
    unit = rootContainer.recipeKey
    grade = rootContainer.grade
    version = rootContainer.version
    message = "Starting MANUAL download of %s - %s for %s" % (str(grade), str(version), str(unit))
    from ils.queue.log import insert
    insert(message)

    download(rootContainer, recipeMap)


def download(rootContainer, recipeMap):
    
    provider = rootContainer.getPropertyValue("provider")
    recipeKey = rootContainer.getPropertyValue("recipeKey")
    table = rootContainer.getComponent("Power Table")
    writeEnabled = system.tag.read("/Recipe/Constants/recipeWriteEnabled")
    
    downloadTimeout = system.tag.read("/Recipe/Constants/downloadTimeout").value
    rootContainer.downloadTimeout = downloadTimeout
    print "The download timeout is ", downloadTimeout, " seconds"
    
    log.info("Downloading recipe <%s> (RecipeWriteEnabled: %s)..." % (recipeKey, str(writeEnabled)))
    
    recipeToolkit_update.recipeMapStatus(recipeKey, 'Processing Download')
    rootContainer.status = 'Processing Download'

    # Save the time that the download started so that we know when to stop monitoring it.
    now = util.getDate()
    rootContainer.timestamp = util.formatDateTime(now)
    rootContainer.downloadStartTime = now

    # Set the background color to indicate Downloading
    recipeToolkit_common.setBackgroundColor(rootContainer, "screenBackgroundColorDownloading")
    resetTags(table.processedData, provider, recipeKey)

    # Reset the recipe detail objects
    resetRecipeDetails(provider, recipeKey)

    unit = rootContainer.recipeKey
    unitId = recipeToolkit_fetch.fetchUnitId(unit)
    grade = rootContainer.grade
    version = rootContainer.version
    
    logId = recipeToolkit_log.logMaster(unitId, grade, version)
    rootContainer.logId = logId
    
    logSkippedTags(table, logId)
    
    # Based on the recipe and the current values in the table, determine the rows to write and update the 
    # processedData property of the table
    ds = table.processedData 
    ds = writeImmediate(ds, provider, recipeKey, logId, writeEnabled)
    ds = writeDeferred(ds, provider, recipeKey, logId, writeEnabled)
    table.processedData = ds
    
    # Update the tables visible rows from the processed Data structure
    recipeToolkit_refresh.refreshVisibleData(table)

    # Start the download monitor
    recipeToolkit_downloadMonitor.start(rootContainer)


# Reset the command and message tags that are used during the download
def resetTags(ds, provider, recipeKey):
    import string
        
    log.trace("Resetting tags...")    
    pds = system.dataset.toPyDataSet(ds)
    
    tags = []
    vals = []
    
    for record in pds:
        download = record["Download"]
        downloadType = record["Download Type"]

        if download and (string.upper(downloadType) == 'IMMEDIATE' or string.upper(downloadType) == 'DEFERRED VALUE'):
            tagName = record["Store Tag"]
                    
            # Convert to Ignition tag name
            from ils.recipeToolkit.common import formatTagName
            tagName = formatTagName(provider, recipeKey, tagName)
            log.trace("Resetting %s" % (tagName))
    
            tags.append(tagName + '/command')
            vals.append('')
            tags.append(tagName + '/writeErrorMessage')
            vals.append('')
            tags.append(tagName + '/writeStatus')
            vals.append('')
            tags.append(tagName + '/writeConfirmed')
            vals.append(False)
            tags.append(tagName + '/badValue')
            vals.append(False)

    # Write them all at once
    print "Resetting: ", tags
    status = system.tag.writeAll(tags, vals)
    return

# Reset the command tag in all of the recipe detail objects.  This really isn't necessary for the detail objects that
# were newly created, but is necessary for ones that were existing.  
def resetRecipeDetails(provider, recipeKey):
    print "Resetting recipe details..."
            
    tags = []
    vals = []
    path = "[%s]Recipe/%s/" % (provider, recipeKey)

    for udtType in ['Recipe Data/Recipe Details']:
        details = system.tag.browseTags(path, udtParentType=udtType)
        for detail in details:           
            tags.append(path + detail.name + "/command")
            vals.append("")
            
    system.tag.writeAll(tags, vals)


# Log any tags that are skipped by the operator
def logSkippedTags(table, logId):
    import string
        
    log.trace("Logging skipped tags...")    
    ds = table.processedData
    pds = system.dataset.toPyDataSet(ds)

    for record in pds:
        planStatus = record["Plan Status"]

        if string.upper(planStatus) == "SKIPPED":
            print "Logging a skipped write"
                
            storTagName = record["Store Tag"]
            pendVal = record["Pend"]
            status = "Success"
            storVal = record["Stor"]
            compVal = record["Comp"]
            recommendVal = record["Recc"]
            reason = record["Reason"]
            errorMessage = ""
                
            from ils.recipeToolkit.log import logDetail
                
            logDetail(logId, storTagName, pendVal, status, storVal, compVal, recommendVal, reason, errorMessage)


# There are two types of immediate writes: 1) writes to memory tags, and 2) writes to OPC tags that do not involve high low limits 
def writeImmediate(ds, provider, recipeKey, logId, writeEnabled):
    import string
    from ils.recipeToolkit.common import formatLocalTagName
    from ils.recipeToolkit.common import formatTagName

    log.trace("  ...writing immediate tags...")
    localG2WriteAlias = system.tag.read("[" + provider + "]/Recipe/Constants/localG2WriteAlias").value    

    pds = system.dataset.toPyDataSet(ds)

    tags = []
    vals = []
    commandTags = []
    commandVals = []
    localTags = []
    localVals = []

    i = 0
    for record in pds:
        step = record["Step"]
        tagName = record["Store Tag"]
        download = record["Download"]
        downloadType = record["Download Type"]
        log.trace("%s - %s - %s - %s" % (str(step), tagName, str(download), downloadType))
        if string.upper(downloadType) == 'IMMEDIATE' and download:
            pendVal = record["Pend"]
            if string.upper(pendVal) == "NAN":
                pendVal = float("NaN")
            tagName = record["Store Tag"]
            writeLocation = record["Write Location"]
            
            if writeLocation == localG2WriteAlias:            
                tagName = formatLocalTagName(provider, tagName)
                localTags.append(tagName)
                localVals.append(pendVal)
            else:
                # Convert to Ignition tagname            
                tagName = formatTagName(provider, recipeKey, tagName)
                tags.append(tagName + '/writeValue')
                vals.append(pendVal)
                commandTags.append(tagName + '/Command')
                commandVals.append('WriteDatum')
                modeAttributeValue = record['Mode Attribute Value']
                if modeAttributeValue != '':
                    commandTags.append(tagName + '/PermissiveValue')
                    commandVals.append(modeAttributeValue)

            ds = system.dataset.setValue(ds, i, 'Download Status', 'Pending')

        i = i + 1

    # Write the writevals all at once - first the local tags (non OPC)

    log.trace("====================================")
    if writeEnabled:
        log.info("Writing to immediate LOCAL tags...")
        log.trace("Local Tags:   %s" % (str(localTags)))
        log.trace("Local Values: %s" % (str(localVals)))
        
        status = system.tag.writeAll(localTags, localVals)
        log.trace("   write results (0 = failed immediate, 1 = success, 2 = pending)")
        for i in range(0, len(status)):
            log.trace("    %s : %s  ->  %s" % (str(localTags[i]), str(localVals[i]), str(status[i])))
    else:
        log.info("*** Skipping write to immediate LOCAL tags ***")

    # Now write the immediate OPC tags

    log.trace("====================================")
    if writeEnabled:
        log.info("Writing to immediate OPC tags...") 
        log.trace("  Step 1: Writing values to the holding variables...")
        status = system.tag.writeAll(tags, vals)
        log.trace("    write results (0 = failed immediate, 1 = success, 2 = pending)")
        for i in range(0, len(status)):
            log.trace("      %s : %s -> %s" % (str(tags[i]), str(vals[i]), str(status[i])))

        # Now write the commands, which really make the download go
        log.trace("  Step 2: Writing to the command tag...")
        status = system.tag.writeAll(commandTags, commandVals)
        log.trace("    write results (0 = failed immediate, 1 = success, 2 = pending)")
        for i in range(0, len(status)):
            log.trace("      %s : %s  ->  %s" % (str(commandTags[i]), str(commandVals[i]), str(status[i])))

    else:
        log.info("*** Skipping write to immediate OPC tags ***")

    log.info("Immediate downloads: %i local, %i OPC" % (len(localTags), len(tags)))

    return ds


# Deferred writes generally involve a setpoint and one or more limits.  We need to be careful to write things in the correct order 
# so that the limits are not temporarily violated.
def writeDeferred(ds, provider, recipeKey, logId, writeEnabled):
    import string
    from ils.recipeToolkit.common import formatTagName

    log.trace("=====================================")
    log.trace("Writing to deferred OPC tags...")
    
    # Collect all of the details that need to be downloaded
    pds = system.dataset.toPyDataSet(ds)

    rootTags = []   # I'll use this later to determine which recipe detail onjects to use
    tags = []
    vals = []

    i = 0
    log.trace("  ...writing to the /writeVal and /writeStatus memory tags...") 
    for record in pds:
        download = record["Download"]
        downloadType = string.upper(record["Download Type"])
        if download and (downloadType == 'DEFERRED VALUE' or downloadType == 'DEFERRED LOW LIMIT' or downloadType == 'DEFERRED HIGH LIMIT'):
            pendVal = record["Pend"]
            tagName = record["Store Tag"]
            log.trace("     %s" % (tagName))

            # Convert to Ignition tagname        
            tagName = formatTagName(provider, recipeKey, tagName)
            rootTags.append(str(tagName))
            
            # Write the value to be sent to the DCS
            tags.append(tagName + '/writeValue')
            vals.append(pendVal)
            
            # Update status to indicate we are writing
            tags.append(tagName + '/writeStatus')
            vals.append('Pending')
            
            modeAttributeValue = record['Mode Attribute Value']
            if modeAttributeValue != '':
                tags.append(tagName + '/PermissiveValue')
                vals.append(modeAttributeValue)

            ds = system.dataset.setValue(ds, i, 'Download Status', 'Pending')

        i = i + 1

    status = system.tag.writeAll(tags, vals)
    
    # Write the "write" command to the recipe details which will initiate the download in the gateway
    log.trace("  ...writing the write command to the recipe details...")
    log.trace("     The root of the tags that will be written are: %s" % (str(rootTags)))
    
    tags = []
    vals = []
    path = '[' + provider + ']Recipe/' + recipeKey
    for udtType in ['Recipe Data/Recipe Details']:
        details = system.tag.browseTags(path, udtParentType=udtType)

        for detail in details:
#            print "Checking recipe detail named: ", detail.name
            tagName = formatTagName(provider, recipeKey, detail.name)

            highLimitTagName = system.tag.read(tagName+'/highLimitTagName').value
            highLimitTagName = formatTagName(provider, recipeKey, highLimitTagName)
            lowLimitTagName = system.tag.read(tagName+'/lowLimitTagName').value
            lowLimitTagName = formatTagName(provider, recipeKey, lowLimitTagName)
            valueTagName = system.tag.read(tagName+'/valueTagName').value
            valueTagName = formatTagName(provider, recipeKey, valueTagName)
            
#            print "   High: ", highLimitTagName
#            print "    Low: ", lowLimitTagName
#            print "  Value: ", valueTagName
            
            if highLimitTagName in rootTags or lowLimitTagName in rootTags or valueTagName in rootTags:
                log.trace("     adding %s to the deferred value write list..." % (tagName))
                tags.append(tagName + '/command')
                vals.append('write')

    # Write all of the COMMAND values at once which will kick off the writes in the gateway
    status = system.tag.writeAll(tags, vals)
    log.trace("=====================================")
    return ds