'''
Created on Sep 10, 2014

@author: Pete
'''
import system

def automatedDownloadHandler():
    print "In automatedDownloadHandler"

def downloadCallback(rootContainer):
    print "In downloadCallback() "

    recipeKey = rootContainer.getPropertyValue("recipeKey")
    print recipeKey
    from ils.recipeToolkit.fetch import map
    recipeMap = map(recipeKey)
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
    
    print "Downloading " + recipeKey + "..."

    # Set the download timeout
    setDownloadTimeout(rootContainer)
    
    from ils.recipeToolkit.update import recipeMapStatus
    recipeMapStatus(recipeKey, 'Processing Download')
    rootContainer.status = 'Processing Download'

    # Save the time that the download started so that we know when to stop monitoring it.
    from ils.common.util import getDate
    now = getDate()
    
    from ils.common.util import formatDateTime
    rootContainer.timestamp = formatDateTime(now)
    rootContainer.downloadStartTime = now

    # Set the background color to indicate Downloading
    from ils.recipeToolkit.common import setBackgroundColor
    setBackgroundColor(rootContainer, "screenBackgroundColorDownloading")
    resetTags(table, provider, recipeKey)

    from ils.recipeToolkit.log import logMaster
    unit = rootContainer.recipeKey
    grade = rootContainer.grade
    version = rootContainer.version
    logId = logMaster(unit, grade, version)
    rootContainer.logId = logId
    
    # Based on the recipe and the current values in the table, determine the rows to write and update the 
    # processedData property of the table
    writeImmediate(table, provider, recipeKey, logId, writeEnabled)
    writeDeferred(table, provider, recipeKey, logId, writeEnabled)
    
    # Update the tables visible rows from the processed Data structure
    from ils.recipeToolkit.refresh import refreshVisibleData
    refreshVisibleData(table)

    # Start the download monitor
    from ils.recipeToolkit.downloadMonitor import start
    start(rootContainer)


#------------------------------------
def writeImmediate(table, provider, recipeKey, logId, writeEnabled):
    import string
    from ils.recipeToolkit.common import formatLocalTagName
    from ils.recipeToolkit.common import formatTagName

    print "  ...writing immediate tags..."
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

    print "\nWriting values directly to *LOCAL* tags..."
    status = system.tag.writeAll(localTags, localVals)
    print "   write results (0 = failed immediate, 1 = success, 2 = pending)"
    for i in range(0, len(status)):
        print "    ", localTags[i], localVals[i], ' -> ', status[i]

#        print "Tags: ", len(tags), tags
#        print "Vals: ", len(vals), vals
    print "\nWriting to immediate OPC tags..." 
    print "  Step 1: Writing values to the holding variables..."
    status = system.tag.writeAll(tags, vals)
    print "    write results (0 = failed immediate, 1 = success, 2 = pending)"
    for i in range(0, len(status)):
        print "      ", tags[i], vals[i], ' -> ', status[i]
        
    # Now write the commands, which really make the download go
    print "  Step 2: Writing to the command tag..."
    status = system.tag.writeAll(commandTags, commandVals)
    print "    write results (0 = failed immediate, 1 = success, 2 = pending)"
    for i in range(0, len(status)):
        print "      ", commandTags[i], commandVals[i], ' -> ', status[i]
        
    print "Immediate downloads: %i local, %i OPC" % (len(localTags), len(tags))


#-----------------------------------------
# The deferred writes are organized by recipe details
def writeDeferred(table, provider, recipeKey, logId, writeEnabled):
    import string
    from ils.recipeToolkit.common import formatTagName

    print "\n\n\n******************************************"
    print "  ...writing deferred tags..."

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

#
#-----------------------------------------
# The deferred writes are organized by recipe details
#TODO Delete this - I don't think this version did anything useful anyway
def writeDeferredOld(table, provider, recipeKey):
    import string

    print "\n\n\n******************************************"
    print "  ...writing deferred tags..."

    # Write the PEND value to the WriteVal tag of the UDT.  It won't be written until the Command is set 
    ds = table.processedData
    pds = system.dataset.toPyDataSet(ds)

    tags = []
    vals = []

    i = 0
    print "  ...writing values to the memory tags..." 
    for record in pds:
        download = record["Download"]
        downloadType = record["Download Type"]
        if string.upper(downloadType) == 'DEFERRED'and download:
            pendVal = record["Pend"]
            tagName = record["Store Tag"]

            # Convert to Ignition tagname
            from ils.recipeToolkit.common import formatTagName
            tagName = formatTagName(provider, recipeKey, tagName)
            tags.append(tagName + '/WriteVal')
            vals.append(pendVal)

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
    for udtType in ['Recipe SP Details', 'Recipe PV Details', ' Recipe OP Details']:
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