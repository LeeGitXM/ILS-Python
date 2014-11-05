'''
Created on Sep 10, 2014

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
import ils.common.util as util
import ils.recipeToolkit.common as common
import ils.recipeToolkit.downloadMonitor as downloadMonitor
import ils.recipeToolkit.fetch as fetch
import ils.recipeToolkit.log as downloadLog
import ils.recipeToolkit.refresh as refresh
import ils.recipeToolkit.update as update

log = LogUtil.getLogger("com.ils.recipeToolkit.download")

def automatedDownloadHandler():
    print "In automatedDownloadHandler"

def downloadCallback(rootContainer):
    print "In downloadCallback() "

    recipeKey = rootContainer.getPropertyValue("recipeKey")
    print recipeKey
    
    recipeMap = fetch.recipeMap(recipeKey)
    if recipeMap == 'Not Found':
        system.gui.errorBox('Error fetching the recipe map from the database for: %s' % (recipeMap))
        return
        
    table = rootContainer.getComponent("Power Table")
    
    # TODO - Need to get all of the data - not just operator data!
    # This isn't right operator data is not the complete recipe!
    pdsRecipe = system.dataset.toPyDataSet(table.data)
    
    from ils.common.cast import toBool
    confirmDownload = toBool(recipeMap["ConfirmDownload"])
    if confirmDownload:
        confirmation = system.gui.confirm("Really download the values in the spreadsheet to the DCS?")
        if not(confirmation): 
            return

    download(rootContainer, recipeMap)

# Determine the download timeout interval, in seconds.  This is the time thatt he download 
# progress will be monitored after the user confirms the download.  Any writes that are still
# pending after this interval will be deemed a failure.
def setDownloadTimeout(rootContainer):
    rootContainer.downloadTimeout = 300


def download(rootContainer, recipeMap):
    
    #------------------------------------
    # Reset the command and message tags that are used during the download
    def resetTags(table, provider, recipeKey):
        import string
        
        print "  ...resetting tags..."    
        ds = table.processedData
        pds = system.dataset.toPyDataSet(ds)
    
        tags = []
        vals = []
    
        for record in pds:
            download = record["Download"]
            downloadType = record["Download Type"]
            if string.upper(downloadType) == 'IMMEDIATE' or string.upper(downloadType) == 'DEFERRED':
                tagName = record["Store Tag"]
                    
                # Convert to Ignition tagname
                from ils.recipeToolkit.common import formatTagName
                tagName = formatTagName(provider, recipeKey, tagName)
    
                tags.append(tagName + '/command')
                vals.append('')
                tags.append(tagName + '/writeMessage')
                vals.append('')
                tags.append(tagName + '/writeStatus')
                vals.append('')
                tags.append(tagName + '/writeConfirmed')
                vals.append(False)
    
        # Write them all at once
        status = system.tag.writeAll(tags, vals)
        return
    #------------------------------------

    provider = rootContainer.getPropertyValue("provider")
    recipeKey = rootContainer.getPropertyValue("recipeKey")
    table = rootContainer.getComponent("Power Table")
    writeEnabled = system.tag.read("/Recipe/Constants/recipeWriteEnabled")
    
    log.info("Downloading recipe <%s> (RecipeWriteEnabled: %s)..." % (recipeKey, str(writeEnabled)))

    # Set the download timeout
    setDownloadTimeout(rootContainer)
    
    update.recipeMapStatus(recipeKey, 'Processing Download')
    rootContainer.status = 'Processing Download'

    # Save the time that the download started so that we know when to stop monitoring it.
    
    now = util.getDate()
    rootContainer.timestamp = util.formatDateTime(now)
    rootContainer.downloadStartTime = now

    # Set the background color to indicate Downloading
    common.setBackgroundColor(rootContainer, "screenBackgroundColorDownloading")
    resetTags(table, provider, recipeKey)

    unit = rootContainer.recipeKey
    unitId = fetch.fetchUnitId(unit)
    grade = rootContainer.grade
    version = rootContainer.version
    
    logId = downloadLog.logMaster(unitId, grade, version)
    rootContainer.logId = logId
    
    # Based on the recipe and the current values in the table, determine the rows to write and update the 
    # processedData property of the table
    writeImmediate(table, provider, recipeKey, logId, writeEnabled)
    writeDeferred(table, provider, recipeKey, logId, writeEnabled)
    
    # Update the tables visible rows from the processed Data structure
    refresh.refreshVisibleData(table)

    # Start the download monitor
    downloadMonitor.start(rootContainer)


# There are two types of immediate writes: 1) writes to memory tags, and 2) writes to OPC tags that do not involve high low limits 
def writeImmediate(table, provider, recipeKey, logId, writeEnabled):
    import string
    from ils.recipeToolkit.common import formatLocalTagName
    from ils.recipeToolkit.common import formatTagName

    log.trace("  ...writing immediate tags...")
    localG2WriteAlias = system.tag.read("/Recipe/Constants/localG2WriteAlias").value    
    ds = table.processedData
    pds = system.dataset.toPyDataSet(ds)

    tags = []
    vals = []
    commandTags = []
    commandVals = []
    localTags = []
    localVals = []

    i = 0
    for record in pds:
        download = record["Download"]
        downloadType = record["Download Type"]
        if string.upper(downloadType) == 'IMMEDIATE' and download:
            pendVal = record["Pend"]
            tagName = record["Store Tag"]
            writeLocation = record["Write Location"]
            
            if writeLocation == localG2WriteAlias:            
                tagName = formatLocalTagName(provider, tagName)
                localTags.append(tagName)
                localVals.append(pendVal)
            else:
                # Convert to Ignition tagname            
                tagName = formatTagName(provider, recipeKey, tagName)
                tags.append(tagName + '/WriteVal')
                vals.append(pendVal)
                commandTags.append(tagName + '/Command')
                commandVals.append('WriteDatum')

            ds = system.dataset.setValue(ds, i, 'Download Status', 'Pending')

        i = i + 1
    
    # This needs to get to the visible data somehow...
    table.processedData = ds
    
    # Write the writevals all at once - first the local tags (non OPC)

    log.trace("====================================")
    if writeEnabled:
        log.info("Writing to immediate LOCAL tags...")
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

    print "Immediate downloads: %i local, %i OPC" % (len(localTags), len(tags))  

# Deferred writes generally involve a setpoint and one or more limits.  We need to be careful to write things in the correct order 
# so that the limits are not temporarily violated.
def writeDeferred(table, provider, recipeKey, logId, writeEnabled):
    import string
    from ils.recipeToolkit.common import formatTagName

    log.trace("******************************************")
    log.trace("Writing to deferred OPC tags...")
    
    # Collect all of the details that need to be downloaded
    
    ds = table.processedData
    pds = system.dataset.toPyDataSet(ds)

    tags = []
    vals = []

    i = 0
    print "  ...writing values to the memory tags..." 
    for record in pds:
        download = record["Download"]
        downloadType = string.upper(record["Download Type"])
        if download and (downloadType == 'DEFERRED VALUE' or downloadType == 'DEFERRED LOW LIMIT' or downloadType == 'DEFERRED HIGH LIMIT'):
            pendVal = record["Pend"]
            tagName = record["Store Tag"]

            # Convert to Ignition tagname        
            tagName = formatTagName(provider, recipeKey, tagName)
            
            # Write the value to be sent to the DCS
            tags.append(tagName + '/WriteVal')
            vals.append(pendVal)
            
            # Update status to indicate we are writing
            tags.append(tagName + '/WriteStatus')
            vals.append('Pending')

            ds = system.dataset.setValue(ds, i, 'Download Status', 'Pending')

        i = i + 1
    
    # This needs to get to the visible data somehow...
    table.processedData = ds
    
    # Write all of the PEND values to the memort tags - they will be downloaded from the gateway
    status = system.tag.writeAll(tags, vals)

    print "  ...setting write command for each recipe details..."
    tags = []
    vals = []
    path = '[' + provider + ']Recipe/' + recipeKey
    for udtType in ['Recipe Data/Recipe Details']:
        print udtType
        details = system.tag.browseTags(path, udtParentType=udtType)
        
        for detail in details:
            print detail.name
            tagName = formatTagName(provider, recipeKey, detail.name)
            tags.append(tagName + '/command')
            vals.append('write')

    # Write all of the COMMAND values at once which will kick off the writes in the gateway
    status = system.tag.writeAll(tags, vals)

    return