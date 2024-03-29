'''
Created on Sep 10, 2014

@author: Pete
'''
import system, string, time
from ils.recipeToolkit.common import checkForUncommentedChanges
import ils.common.util as util
import ils.recipeToolkit.common as recipeToolkit_common
import ils.recipeToolkit.downloadMonitor as recipeToolkit_downloadMonitor
import ils.recipeToolkit.fetch as recipeToolkit_fetch
import ils.recipeToolkit.log as recipeToolkit_log
import ils.recipeToolkit.refresh as recipeToolkit_refresh
import ils.recipeToolkit.update as recipeToolkit_update
import ils.recipeToolkit.viewRecipe as recipeToolkit_viewRecipe
from ils.io.client import writeWithNoChecks, writeRecipeDetails, writeDatums
from ils.io.util import getTagSuffix
from ils.common.config import getTagProvider, getTagProviderClient, getDatabaseClient, getIsolationModeClient
from ils.common.ocAlert import sendAlert
from ils.io.util import getProviderFromTagPath
from ils.log import getLogger
log =getLogger(__name__)

def automatedDownloadHandler(tagPath, grade):
    
    # Get the path to the UDT so I can get the other tags that configure the download
    tagPath = str(tagPath)
    if tagPath.endswith('/grade'):
        parentTagPath = tagPath[:len(tagPath) - 6]
    elif tagPath.endswith('/gradeManual'):
        parentTagPath = tagPath[:len(tagPath) - 12]
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
    log.infof("In %s.automatedDownloadHandler(), the recipeKey is: %s, automated download is %s", __name__, recipeKey, str(automatedDownload))

    from ils.recipeToolkit.fetch import  fetchHighestVersion
    version = fetchHighestVersion(recipeKey, grade, database)
    if version == None:
        log.error("Aborting the automated download because a recipe was not found for Unit: %s, Grade: %s, Version: %s"% (str(recipeKey), str(grade), str(version)))
        familyId = recipeToolkit_fetch.fetchFamilyId(recipeKey, database)
        logId = recipeToolkit_log.logMaster(familyId, grade, version=-1, downloadType="Automatic", database=database)
        recipeToolkit_log.updateLogMaster(logId, status="Failed", totalDownloads=0, passedDownloads=0, failedDownloads=0, database=database)
        return

    log.info("******************************")
    log.info("Starting an automated recipe download of %s - recipe family: %s - %s (Post: %s, Automated: %s, initiated by: %s)" % (project, recipeKey, grade, post, str(automatedDownload), tagPath))
    log.info("******************************")

    if automatedDownload:
        fullyAutomatedDownload(parentTagPath, post, project, database, recipeKey, grade, version)
        log.info("...back from a fully automated download...")
    else:
        # Send a message to open the 
        log.trace("Sending a message to every client to post a download GUI")
        # system.util.sendMessage(project, "automatedDownload", {"post": post, "recipeKey": recipeKey, "grade": grade, "version": version}, 'C')
        
        callbackPayloadDictionary = {"post": post, "recipeKey": recipeKey, "grade": grade, "version": version, "triggerTagPath": parentTagPath}
        # This is generally called from the gateway, but should work from th
        mainMessage = "Semi-automated recipe download for grade %s - %s" % (str(grade), str(version))
        topBottomMessage = "Semi-automated recipe download!"
        sendAlert(project, post, topMessage=topBottomMessage, bottomMessage=topBottomMessage, mainMessage=mainMessage, 
                  buttonLabel="View Recipe", callback="ils.recipeToolkit.viewRecipe.semiAutomatedDownloadCallback", 
                  callbackPayloadDictionary=callbackPayloadDictionary, db=database)    
        
        ''' Initialize the UDT tags  '''
        tags = [parentTagPath + "/downloadStartTime",
                parentTagPath + "/downloadEndTime",
                parentTagPath + "/failedDownloads",
                parentTagPath + "/passedDownloads",
                parentTagPath + "/totalDownloads",
                parentTagPath + "/status"
            ]
    
        vals = ["",
                "",
                0,
                0,
                0,
                "Sending OC Alert"
            ]
        
        system.tag.writeAll(tags, vals)


'''
Start a fully automatic lights out automatic download.
It looks like this only supports production.
'''
def fullyAutomatedDownload(parentTagPath, post, project, database, familyName, grade, version):
    log.info("Setting up a fully automated download\n  Post: %s, Project: %s, Database: %s, Recipe Family: %s, Grade: %s, Version: %s" % (post, project, database, familyName, grade, str(version)))
    
    tagProvider = getProviderFromTagPath(parentTagPath) # Get the production tag provider.
    
    # fetch the recipe map which will specify the database and table containing the recipe
    recipeFamily = recipeToolkit_fetch.recipeFamily(familyName, database)
    status = recipeFamily['Status']
    timestamp = recipeFamily['Timestamp']
    print "Status:", status, timestamp

    # Fetch the recipe
    pds = recipeToolkit_fetch.details(familyName, grade, version, database)

    # Create the processed data set by adding some columns to the raw recipe data. 
    dsProcessed = recipeToolkit_viewRecipe.update(pds)

    # Reset the recipe detail objects
    recipeToolkit_viewRecipe.resetRecipeDetails(tagProvider, familyName)

    # Create any OPC tags that are required by the recipe
    dsProcessed, tags = recipeToolkit_viewRecipe.createOPCTags(dsProcessed, tagProvider, familyName, database)
    
    # Refresh the table with data from the DCS and determine what needs to be downloaded
    dsProcessed = recipeToolkit_refresh.automatedRefresh(familyName, dsProcessed, tagProvider, database)

    recipeWriteEnabled = system.tag.read("[" + tagProvider + "]/Configuration/RecipeToolkit/recipeWriteEnabled").value
    globalWriteEnabled = system.tag.read("[" + tagProvider + "]/Configuration/Common/writeEnabled").value
    writeEnabled = recipeWriteEnabled and globalWriteEnabled
    localWriteAlias = string.upper(system.tag.read("[" + tagProvider + "]/Configuration/RecipeToolkit/localWriteAlias").value)
    downloadTimeout = system.tag.read("[" + tagProvider + "]/Configuration/RecipeToolkit/downloadTimeout").value
    
    log.info("Downloading recipe <%s> (RecipeWriteEnabled: %s, timeout: %s seconds)..." % (familyName, str(writeEnabled), str(downloadTimeout)))
    
    recipeToolkit_update.recipeFamilyStatus(familyName, 'Processing Download', database)

    # Save the time that the download started so that we know when to stop monitoring it.
    downloadStartTime = util.getDate(database)

    resetTags(dsProcessed, tagProvider, familyName, localWriteAlias)

    # Open a master download record for this download
    familyId = recipeToolkit_fetch.fetchFamilyId(familyName, database)
    logId = recipeToolkit_log.logMaster(familyId, grade, version, "Automatic", database)
    
    ''' Initialize the UDT tags  '''
    tags = [parentTagPath + "/masterId",
            parentTagPath + "/downloadStartTime",
            parentTagPath + "/downloadEndTime",
            parentTagPath + "/failedDownloads",
            parentTagPath + "/passedDownloads",
            parentTagPath + "/totalDownloads",
            parentTagPath + "/status"
        ]

    vals = [logId,
            str(system.date.now()),
            "",
            0,
            0,
            0,
            "Downloading"
        ]
    
    system.tag.writeAll(tags, vals)

    # Normally at this time we would log skipped tags, but since this automated, there can't be skipped tags
    
    # Based on the recipe and the current values in the table, determine the rows to write and update the 
    # processedData property of the table
    dsProcessed = writeImmediate(dsProcessed, tagProvider, familyName, logId, localWriteAlias, writeEnabled, project)
    dsProcessed = writeDeferred(dsProcessed, tagProvider, familyName, logId, writeEnabled, project)

    # Start the download monitor
    recipeToolkit_downloadMonitor.automatedRunner(parentTagPath, dsProcessed, tagProvider, familyName, grade, version, logId, downloadStartTime, downloadTimeout, database)
    
    log.info("Completed automated download!")


def downloadCallback(rootContainer):
    log.info("Starting a download...")
    
    provider = rootContainer.getPropertyValue("provider")
    requireComments = system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/requireCommentsForChangedValues").value
    if requireComments:
        uncommentedChanges = checkForUncommentedChanges(rootContainer)
        if uncommentedChanges:
            system.gui.messageBox("Please enter comments for any changed values before downloading recipe!")
            return

    familyName = rootContainer.getPropertyValue("familyName")
    
    recipeFamily = recipeToolkit_fetch.recipeFamily(familyName)
    if recipeFamily == 'Not Found':
        system.gui.errorBox('Error fetching the recipe map from the database for: %s' % (familyName))
        return
     
    from ils.common.cast import toBool
    confirmDownload = toBool(recipeFamily["ConfirmDownload"])
    if confirmDownload:
        confirmation = system.gui.confirm("Really download the values in the spreadsheet to the DCS?")
        if not(confirmation): 
            return

    # Insert a message into the log book queue that we are starting a manual download
    familyName = rootContainer.familyName
    grade = rootContainer.grade
    version = rootContainer.version
    message = "Starting MANUAL download of %s - %s for %s" % (str(grade), str(version), str(familyName))
    from ils.common.operatorLogbook import insert
    insert(familyName, message)
    
    # Save the grade and type to the recipe family table.
    # grade looks like an int, but it is probably a string
    db = getDatabaseClient()
    SQL = "update RtRecipeFamily set CurrentGrade = '%s', CurrentVersion = %s, Status = 'Initializing', "\
        "Timestamp = getdate() where RecipeFamilyName = '%s'" % (str(grade), version, familyName)
    rows = system.db.runUpdateQuery(SQL, database=db)
    print "Successfully updated %i rows" % (rows)

    download(rootContainer)


def download(rootContainer):
    project = system.util.getProjectName()
    provider = rootContainer.getPropertyValue("provider")
    database = getDatabaseClient()
    isolationMode = getIsolationModeClient()
    familyName = rootContainer.getPropertyValue("familyName")
    mode = rootContainer.getPropertyValue("mode")
    table = rootContainer.getComponent("Power Table")
    
    productionProvider = getTagProvider()     # Get the production tag provider.
    
    localWriteAlias = string.upper(system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/localWriteAlias").value)
    recipeWriteEnabled = system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/recipeWriteEnabled").value
    globalWriteEnabled = system.tag.read("[" + provider + "]/Configuration/Common/writeEnabled").value
    writeEnabled = (provider != productionProvider) or (recipeWriteEnabled and globalWriteEnabled)
    print "The combined write enabled status, considering the tag provider, is: ", writeEnabled
    
    downloadTimeout = system.tag.read("[%s]/Configuration/RecipeToolkit/downloadTimeout" % (provider)).value
    rootContainer.downloadTimeout = downloadTimeout
    print "The download timeout is ", downloadTimeout, " seconds"
    
    log.info("Downloading recipe <%s> (Write Enabled: %s)..." % (familyName, str(writeEnabled)))
    
    recipeToolkit_update.recipeFamilyStatus(familyName, 'Processing Download')
    rootContainer.status = 'Processing Download'

    # Save the time that the download started so that we know when to stop monitoring it.
    now = util.getDate()
    rootContainer.timestamp = util.formatDateTime(now)
    rootContainer.downloadStartTime = system.date.now()
    
    ''' If we are in semi-automatic mode, then this download was triggerred from a trigger tag UDT which needs to be updated ''' 
    if mode == "semi-automatic":
        tagPath = rootContainer.getPropertyValue("triggerTagPath")
        tags = [tagPath + "/status", tagPath + "/failedDownloads", tagPath + "/passedDownloads", tagPath + "/totalDownloads", tagPath + "/downloadStartTime"]
        vals = ["Downloading", 0, 0, 0, now]
        system.tag.writeAll(tags, vals)

    # Set the background color to indicate Downloading
    recipeToolkit_common.setBackgroundColor(rootContainer, "screenBackgroundColorDownloading")
    resetTags(table.processedData, provider, familyName, localWriteAlias)

    # Reset the recipe detail objects
    resetRecipeDetails(provider, familyName)

    familyId = recipeToolkit_fetch.fetchFamilyId(familyName)
    grade = rootContainer.grade
    version = rootContainer.version
    
    logId = recipeToolkit_log.logMaster(familyId, grade, version, database=database)
    rootContainer.logId = logId
    
    logSkippedTags(table, logId, database)
    
    # Based on the recipe and the current values in the table, determine the rows to write and update the 
    # processedData property of the table
    ds = table.processedData 
    ds = writeImmediate(ds, provider, familyName, logId, localWriteAlias, writeEnabled, project)

    ds = writeDeferred(ds, provider, familyName, logId, writeEnabled, project, isolationMode)
    table.processedData = ds
    
    # Update the tables visible rows from the processed Data structure
    recipeToolkit_refresh.refreshVisibleData(table)

    # Start the download monitor
    recipeToolkit_downloadMonitor.start(rootContainer)


# Reset the command and message tags that are used during the download
def resetTags(ds, provider, familyName, localWriteAlias):
    log.info("Resetting tags...")    
    pds = system.dataset.toPyDataSet(ds)
    
    tags = []
    vals = []
    
    for record in pds:
        download = record["Download"]
        downloadType = record["Download Type"]
        writeLocation = record["Write Location"]

        if download and (string.upper(downloadType) == 'IMMEDIATE' or string.upper(downloadType) == 'DEFERRED VALUE') and (string.upper(writeLocation) != localWriteAlias):
            tagName = record["Store Tag"]
                    
            # Convert to Ignition tag name
            from ils.recipeToolkit.common import formatTagName
            tagName = formatTagName(provider, familyName, tagName)
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
    status = system.tag.writeAll(tags, vals)
    
    # TODO - I should check that the reset was successful
    log.trace("Tag write status: %s" % (str(status)))
    
    return

# Reset the command tag in all of the recipe detail objects.  This really isn't necessary for the detail objects that
# were newly created, but is necessary for ones that were existing.  
def resetRecipeDetails(provider, familyName):
    log.info("Resetting recipe details...")
            
    tags = []
    vals = []
    path = "[%s]Recipe/%s/" % (provider, familyName)

    for udtType in ['Recipe Data/Recipe Details']:
        details = system.tag.browseTags(path, udtParentType=udtType)
        for detail in details:           
            tags.append(path + detail.name + "/command")
            vals.append("")

    log.infof("...reset %d recipe detail UDTs", len(details))            
    system.tag.writeAll(tags, vals)

# Log any tags that are skipped by the operator
def logSkippedTags(table, logId, database):
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
                
            logDetail(logId, storTagName, pendVal, status, storVal, compVal, recommendVal, reason, errorMessage, database)


# There are two types of immediate writes: 1) writes to memory tags, and 2) writes to OPC tags that do not involve high low limits 
def writeImmediate(ds, provider, familyName, logId, localWriteAlias, writeEnabled, project):
    from ils.recipeToolkit.common import formatLocalTagName
    from ils.recipeToolkit.common import formatTagName

    log.trace("  ...writing immediate tags...")  

    pds = system.dataset.toPyDataSet(ds)

    localTagValues = []
    opcTagValues = []
    opcModeTagValues = []
    opcTagCntr = 0
    opcModeTagCntr = 0
    permissiveTags = []
    permissiveValues = []

    i = 0
    for record in pds:
        step = record["Step"]
        tagName = record["Store Tag"]
        download = record["Download"]
        downloadType = record["Download Type"]
        if string.upper(downloadType) == 'IMMEDIATE' and download:
            pendVal = record["Pend"]
            if string.upper(pendVal) == "NAN":
                pendVal = float("NaN")
            tagName = record["Store Tag"]
            writeLocation = record["Write Location"]
            
            if string.upper(writeLocation) == localWriteAlias:
                tagName = formatLocalTagName(provider, tagName)
                log.trace("Immediate Local: Step: %s, tag: %s, value: %s" % (str(step), tagName, str(pendVal)))
                localTagValues.append({"tagPath": tagName, "tagValue": pendVal})
            else:
                tagSuffix = getTagSuffix(tagName)
                # Convert to Ignition tagname
                tagName = formatTagName(provider, familyName, tagName)
                
                modeAttributeValue = record['Mode Attribute Value']
                
                if modeAttributeValue != '' and modeAttributeValue != None:
                    permissiveTags.append(tagName + "/PermissiveValue")
                    permissiveValues.append(modeAttributeValue)
                
                if tagSuffix in ["MODE", "MODE/ENUM", "MODE /ENUM"]:
                    opcModeTagCntr += 1
                    log.trace("Immediate OPC ** MODE TAG**: Step: %s, tag: %s, value: %s" % (str(step), tagName, str(pendVal)))
                    opcModeTagValues.append({"tagPath": tagName, "tagValue": pendVal})
                    
                    #modeAttributeValue = record['Mode Attribute Value']
                    #if modeAttributeValue != '' and modeAttributeValue != None:
                    #    opcModeTagValues.append({"tagPath": tagName + '/PermissiveValue', "val": modeAttributeValue})
                else:
                    opcTagCntr += 1
                    log.trace("Immediate OPC: Step: %s, tag: %s, value: %s" % (str(step), tagName, str(pendVal)))
                    opcTagValues.append({"tagPath": tagName, "tagValue": pendVal})
                    #modeAttributeValue = record['Mode Attribute Value']
                    #if modeAttributeValue != '' and modeAttributeValue != None:
                    #   opcTagValues.append({"tagPath": tagName + '/PermissiveValue', "val": modeAttributeValue})

            ds = system.dataset.setValue(ds, i, 'Download Status', 'Pending')

        i = i + 1

    # The actual writes are done in the gateway, but setting up the permissive values, which is memory tags, can be written here and now
    log.infof("Setting up permissive values...")
    log.tracef("Permissive Tags: %s", str(permissiveTags))
    log.tracef("Permissive Values: %s", str(permissiveValues))
    
    system.tag.writeAll(permissiveTags, permissiveValues)

    # Write the writevals all at once - first the local tags (non OPC)

    log.trace("====================================")
    if writeEnabled:
        log.info("Writing to %i immediate LOCAL tags..." % (len(localTagValues)))
        log.trace("  %s" % (str(localTagValues)))
        #writeWithNoChecks(localTagValues, project)
        writeDatums(localTagValues, project)
    else:
        log.info("*** Skipping write to immediate LOCAL tags ***")

    # Now write the immediate OPC tags

    log.trace("====================================")
    if writeEnabled:
        if opcModeTagCntr > 0:
            log.infof("Writing to %d immediate OPC MODE tags...", opcModeTagCntr) 
            writeDatums(opcModeTagValues, project)
            
            ''' 
            The point of all of this is to set the mode before a corresponding SP or OP write, but this is running in the client and the 
            writes are actually running in the gateway (via message passing) so I can't easily confirm the writes.  The cheap and easy thing to do
            is to just wait for the site configurable latency time.
            If this wait is typically more than a couple of seconds then this should all be put into an asynchronous thread so as not to lock the UI
            '''
            latencyTime = system.tag.read("[%s]Configuration/Common/opcTagLatencySeconds" % (provider)).value
            time.sleep(latencyTime)
            
        log.infof("Writing to %d immediate OPC tags...", opcTagCntr) 
        writeDatums(opcTagValues, project)
    else:
        log.info("*** Skipping write to immediate OPC tags ***")

    log.info("Immediate downloads: %i local, %i OPC" % (len(localTagValues), len(opcTagValues)))

    return ds


def writeDeferred(ds, provider, familyName, logId, writeEnabled, project, isolationMode=False):
    '''
    Deferred writes generally involve a setpoint and one or more limits.  We need to be careful to write things in the correct order 
    so that the limits are not temporarily violated.  The idea behind the deferred write is that multiple lines in the recipe viewer are
    related and the write to them needs to be coordinated.  If we want to write to a target that has high and low limits set then we can 
    also change the high and low limits.  When the limits are changed then we need to consider the order of change that will prevent a
    momentary violation of limits.
    The first step is to gather all of the deferred writes and put them in the list.  Then we need to determine if any of then are 
    related.  We do this by finding all of the recipe detail UDTs.  Every deferred write in the recipe viewer should be referenced in a
    recipe detail.  The recipe detail UDT contains the association between target and the high and low limits.  
    Once we have paired things up, then we make a dictionary and send it to the gateway for processing.
    '''
    from ils.recipeToolkit.common import formatTagName

    log.trace("=====================================")
    log.trace("Writing to deferred (recipe detail) tags...")
    
    # Collect all of the details that need to be downloaded
    pds = system.dataset.toPyDataSet(ds)

    rootTags = []   # I'll use this later to determine which recipe detail onjects to use
    pendVals = []
    downloadTypes = []
    
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

            # Convert to Ignition tag name        
            tagName = formatTagName(provider, familyName, tagName)
            rootTags.append(str(tagName))
            
            # Save the value that we are going to write
            pendVals.append(pendVal)
            downloadTypes.append(downloadType)
            
            # Update status to indicate we are writing
            tags.append(tagName + '/writeStatus')
            vals.append('Pending')
            
            modeAttributeValue = record['Mode Attribute Value']
            if modeAttributeValue != '':
                tags.append(tagName + '/PermissiveValue')
                vals.append(modeAttributeValue)

            ds = system.dataset.setValue(ds, i, 'Download Status', 'Pending')

        i = i + 1

    log.trace("    The root tags are:     %s" %  (str(rootTags)))
    log.trace("    The pendVals are:      %s" % (str(pendVals)))
    log.trace("    The downloadTypes are: %s" % (str(downloadTypes)))
    log.trace("    The actual tags are:   %s" % (str(tags)))
    log.trace("    The actual vals are:   %s" % (str(vals)))
    
    status = system.tag.writeAll(tags, vals)
    log.trace("Tag write status: %s" % (str(status)))
    
    if isolationMode:
        ''' If we are in isolation mode then the recie detail UDTs have been turned into folders so none of the production logic will work in isolation,
            furthermore, the need to be careful about writing the limits before the SP does not exist in isolation, since there are no alarms.  Therefore, 
            if we are in isolation, we really are not testing the order of download logic, so just do immediate writes from the client. '''
        
        for record in pds:
            download = record["Download"]
            downloadType = string.upper(record["Download Type"])
            if download and (downloadType == 'DEFERRED VALUE' or downloadType == 'DEFERRED LOW LIMIT' or downloadType == 'DEFERRED HIGH LIMIT'):
                pendVal = record["Pend"]
                tagName = record["Store Tag"]
                log.trace("     %s" % (tagName))
    
                # Convert to Ignition tag name        
                tagName = formatTagName(provider, familyName, tagName)
                rootTags.append(str(tagName) + "/value")
                rootTags.append(str(tagName) + "/writeStatus")
                
                # Save the value that we are going to write
                pendVals.append(pendVal)
                pendVals.append("Success")

        
        log.trace("*** Writing the deferred tags immediately because we are in Isolation mode ***")
        log.trace("    Tags:     %s" % (str(rootTags)))
        log.trace("    Values:   %s" % (str(pendVals)))
        status = system.tag.writeAll(rootTags, pendVals)
        log.trace("Tag write status: %s" % (str(status)))
        
    else:
        log.trace("    --- matching recipe detail UDTS with deferred tags ---")
        
        tagDicts = []
        path = '[' + provider + ']Recipe/' + familyName
        for udtType in ['Recipe Data/Recipe Details']:
            details = system.tag.browseTags(path, udtParentType=udtType)
    
            for detail in details:
                log.tracef("Checking recipe detail named: %s", detail.name)
                tagName = formatTagName(provider, familyName, detail.name)
                log.tracef("  Tag: %s", tagName)
    
                highLimitTagName = system.tag.read(tagName+'/highLimitTagName').value
                highLimitTagName = formatTagName(provider, familyName, highLimitTagName)
                lowLimitTagName = system.tag.read(tagName+'/lowLimitTagName').value
                lowLimitTagName = formatTagName(provider, familyName, lowLimitTagName)
                valueTagName = system.tag.read(tagName+'/valueTagName').value
                valueTagName = formatTagName(provider, familyName, valueTagName)
                
                if highLimitTagName in rootTags or lowLimitTagName in rootTags or valueTagName in rootTags:
                    tagDict = {"tagPath": tagName}
                    
                    if highLimitTagName in rootTags:
                        idx = rootTags.index(highLimitTagName)
                        val = pendVals[idx]
                        log.tracef("    Changing the high limit to %s", str(val))
                        tagDict['newHighLimit'] = val
                        
                    if lowLimitTagName in rootTags:
                        idx = rootTags.index(lowLimitTagName)
                        val = pendVals[idx]
                        log.tracef("    Changing the low limit to %s", str(val))
                        tagDict['newLowLimit'] = val
                    
                    if valueTagName in rootTags:
                        idx = rootTags.index(valueTagName)
                        val = pendVals[idx]
                        log.tracef("    Changing the SP to %s", str(val))
                        tagDict['newValue'] = val
                        
                    tagDicts.append(tagDict)
                    log.trace("     adding %s to the deferred value write list..." % (tagName))
    
        # send the recipe detail write dictionaries to the gateway
        if len(tagDicts) > 0:
            if writeEnabled:
                log.info("Sending %i recipeDetail dictionaries to the gateway..." % (len(tagDicts)))
                writeRecipeDetails(tagDicts,project)
            else:
                log.info("*** Skipping write to deferred tags ***")

    log.trace("=====================================")
    return ds