'''
Created on Sep 10, 2014

@author: Pete
'''

import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit.ui")

def refresh(rootContainer):
    log.info("In ils.recipeToolkit.refresh.refresh()")

    status = rootContainer.getPropertyValue("status")
    if status == 'Processing Download':
        system.gui.warningBox("Ignoring the refresh request because a download is in process!")
        return

    # The downloadType is either GradeChange or MidRun
    downloadType = rootContainer.getPropertyValue("downloadType")
    familyName = rootContainer.getPropertyValue("familyName")
    rootContainer.status = "Refreshing"

    from ils.recipeToolkit.common import setBackgroundColor
    setBackgroundColor(rootContainer, "screenBackgroundColorInitializing")
    
    table = rootContainer.getComponent("Power Table")
    processedData = table.processedData
    processedData = refresher(familyName, processedData, downloadType)

    table.processedData = processedData

    refreshVisibleData(table)

    rootContainer.status = "Refreshed"
    from ils.common.util import getDate
    timestamp = getDate()
    rootContainer.timestamp = system.db.dateFormat(timestamp, "MM/dd/yy HH:mm")


def automatedRefresh(familyName, processedData, database):
    log.info("In ils.recipeToolkit.refresh.automatedRefresh()")
    # The downloadType is either GradeChange or MidRun
    downloadType = "GradeChange"

    processedData = refresher(familyName, processedData, downloadType, database)
    return processedData


# Update the processedData to include the tag values and then make the subset of processed data that will
# be shown and put it in table.data.  (If the user is an engineer then processed data is all data, but 
# operators only see a subset of the data.
def refresher(familyName, ds, downloadType, database = ""):
    log.info("In ils.recipeToolkit.refresh.refresher()")
    log.info("Refreshing Recipe Table for a %s download..." % (downloadType))

    #===============================================
    # This checks if the reason is one of the standard reasons or a custom one entered by the operator.
    # We'd like to NOT overwrite a operator entered reason when pressing refresh.
    def enteredReason(reason):
        if reason in ["", "Enter reason for changing the recommended value", "Enter a reason to skip"]:
            return False
        return True
    #===============================================

    from ils.common.config import getTagProvider
    provider = getTagProvider()

    from ils.recipeToolkit.update import recipeFamilyStatus
    recipeFamilyStatus(familyName, "Refreshing", database)

    localWriteAlias = string.upper(system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/localWriteAlias").value)
    recipeMinimumDifference = system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/recipeMinimumDifference").value
    recipeMinimumRelativeDifference = system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/recipeMinimumRelativeDifference").value

    log.trace("recipeMinimumDifference: %s" %  (str(recipeMinimumDifference)))
    log.trace("recipeMinimumRelativeDifference: %s" % (str(recipeMinimumRelativeDifference)))
    log.trace("localWriteAlias: %s" % (str(localWriteAlias)))

    pds = system.dataset.toPyDataSet(ds)

    # I'm not sure that we can force a device read in Ignition so put together a list of tags and we'll
    # read them all in one read. 
    # (I'm not sure that we were actually doing a device read anyway)

    tagNames = []
    localTagNames = []
    log.trace("-------------------------------------------")
    log.trace("  ...extracting tag names from the table...")
    for record in pds:
        step = record['Step']
        writeLocation = record['Write Location']
        log.trace("Step: %s <%s> <%s>" % ( str(step), writeLocation, record['Store Tag']))

        storTag = record['Store Tag']
        if writeLocation != "" and writeLocation != None and storTag not in ["", None, "NULL", "null"]:
            if string.upper(writeLocation) == localWriteAlias:
                if storTag not in localTagNames:
                    localTagNames.append(storTag)
            else:
                if storTag not in tagNames:
                    tagNames.append(storTag)

        compTag = record['Comp Tag']
        if writeLocation != "" and writeLocation != None and compTag not in ["", None, "NULL", "null"]:
            if string.upper(writeLocation) == localWriteAlias:
                if storTag not in localTagNames:
                    localTagNames.append(compTag)
            else:
                if storTag not in tagNames:
                    tagNames.append(compTag)
    
    # Now  convert the OPC tag names from MS Access to Ignition names
    tags = []
    for tagName in tagNames:
        from ils.recipeToolkit.common import formatTagName
        tagName = formatTagName(provider, familyName, tagName)
        tags.append(tagName + '/value')
    log.trace("OPC tag names: %s" % (str(tags)))

    values = system.tag.readAll(tags)
#    print values

    # Now the local tags - convert *local* tagnames from SQL*Server format to Ignition format...
    tags = []
    for tagName in localTagNames:
        from ils.recipeToolkit.common import formatLocalTagName
        tagName = formatLocalTagName(provider, tagName)
        tags.append(tagName)

    log.trace("Local tag names: %s" % (str(tags)))
    localValues = system.tag.readAll(tags)

    # We have now read all of the tags, merge the values back into the Python dataset
    log.trace("  ...updating table dataset....")
    i = 0    
    for record in pds:
        step = record['Step']
        writeLocation = record['Write Location']
        pendVal = record['Pend']
        storVal = ""
        storQuality = ""
        compVal = ""
        compQuality = ""
        reccVal = record['Recc']
        reason = record['Reason']
        download = False
        planStatus = "readOnly"

        storTag = record['Store Tag']
        if writeLocation != "" and writeLocation != None and storTag not in ["", None, "NULL", "null"]:
            if string.upper(writeLocation) == localWriteAlias:
                idx = localTagNames.index(storTag)
                storVal = localValues[idx].value
                storQuality = str(localValues[idx].quality) 
            else:
                idx = tagNames.index(storTag)
                storVal = values[idx].value
                storQuality = str(values[idx].quality)

            ds = system.dataset.setValue(ds, i, 'Stor', storVal)
    
        compTag = record['Comp Tag']
        if writeLocation != "" and writeLocation != None and compTag not in ["", None, "NULL", "null"]:
            if string.upper(writeLocation) == localWriteAlias:
                idx = localTagNames.index(compTag)
                compVal = localValues[idx].value
                compQuality = str(localValues[idx].quality)
            else:
                idx = tagNames.index(compTag)
                compVal = values[idx].value
                compQuality = str(values[idx].quality)

            ds = system.dataset.setValue(ds, i, "Comp", compVal)
            if downloadType == 'MidRun':
                ds = system.dataset.setValue(ds, i, "Pend", compVal)
                pendVal = compVal
                
        log.trace("line %i - step %i :: pend: %s - stor: %s (%s)- comp: %s (%s)" % (i, step, str(pendVal), str(storVal), str(storQuality), str(compVal), str(compQuality)))
        
        # Based on everything that we have collected about this tag, determine if we should download it
        # This will override any reason that may have already been entered, which doesn't seem right
        if downloadType == 'MidRun':
            reason = ""
        else:
            if writeLocation == "" or writeLocation == None:
                reason = ""
                planStatus = "noChange"
                download = False
            elif (pendVal == None or pendVal == "") and (reccVal == None or reccVal == ""):
                reason = ""
                planStatus = "noChange"
                download = False
            elif (pendVal == None or pendVal == "") and (reccVal != "" and reccVal != None):
                if reason == "":
                    reason = "Enter a reason to skip"
                planStatus = "skipped"
            else:
                if string.upper(storQuality) == 'NOT FOUND':
                    reason = "Error: Tag does not exist!"
                    planStatus = "Error"
                else:
                    from ils.io.util import equalityCheck
                    if equalityCheck(pendVal, storVal, recipeMinimumDifference, recipeMinimumRelativeDifference):
                        download = False
                        planStatus = "noChange"
                        if equalityCheck(pendVal, reccVal, recipeMinimumDifference, recipeMinimumRelativeDifference):
                            reason = ""    
                        else:
                            # If they have entered a reason then don't overwrite it
                            if not(enteredReason(reason)):
                                reason = "Enter reason for changing the recommended value"
                    else:
                        download = True
                        planStatus = "mismatch"
                        if equalityCheck(pendVal, reccVal, recipeMinimumDifference, recipeMinimumRelativeDifference):
                            reason = "Set to recipe value"
                        else:
                            # If they have entered a reason then don't overwrite it
                            if not(enteredReason(reason)):
                                reason = "Enter reason for changing the recommended value"

        ds = system.dataset.setValue(ds, i, "Reason", reason)
        ds = system.dataset.setValue(ds, i, "Download", download)
        ds = system.dataset.setValue(ds, i, "Plan Status", planStatus)
        ds = system.dataset.setValue(ds, i, "Download Status", "")
#        print "Reason: ", reason
#        print ""

        i = i + 1
    
    recipeFamilyStatus(familyName, "Refreshed", database)
    log.info("-- refresh complete --")
    return ds


# This is redundant with what is in ils.common.util.equalityCheck but it is done in a slightly different way so 
# keep it around for a bit (11/13/14)
def equivalentValues(pendVal, storVal, recipeMinimumDifference, recipeMinimumRelativeDifference):
    from ils.common.util import isText
    pendValIsText = isText(pendVal)
    storValIsText = isText(storVal)
#   print "StorVal: %s (Text: %s) PendVal: %s (Text: %s)" % (str(storVal), str(storValIsText), str(pendVal), str(pendValIsText))

    if string.upper(str(pendVal))  == "NAN" or string.upper(str(storVal)) == "NAN":
        pendVal = string.upper(str(pendVal))
        storVal = string.upper(str(storVal))
                
#        print "One of the tags is a NAN... <%s> <%s>" % (pendVal, storVal)
        if (pendVal == "NAN") and (storVal == "NAN" or storVal == "" or storVal == None or storVal == "NONE"):
            equivalent = True
        else:
            equivalent = False

    # Check if they are both text
    elif storValIsText and pendValIsText:
        if storVal == pendVal:
            equivalent = True
        else:
            equivalent = False
    else:
        # They aren't both text, so if only one is text, then they don't match 
        if storValIsText or pendValIsText:
            equivalent = False
        else:
            storVal = float(storVal)
            pendVal = float(pendVal)

            minThreshold = abs(recipeMinimumRelativeDifference * storVal)
            if minThreshold < recipeMinimumDifference:
                minThreshold = recipeMinimumDifference

#            print "Min Threshold: ", minThreshold
            if abs(storVal - float(pendVal)) < minThreshold:
                equivalent = True
            else:
                equivalent = False

    return equivalent

# This takes the processed data, considers the role of the user, and filters out OE data
# if the user is an operator
def refreshVisibleData(table):
    log.info("In ils.recipeToolkit.refresh.refreshVisibleData()")
    ds = table.processedData    
    # Now create the data that will be shown
    from ils.common.user import isAE
    isAE = isAE()
    if isAE:
        table.data = ds
    else:
        pds = system.dataset.toPyDataSet(ds)
        deleteRows = []
        row = 0
        for record in pds:
            changeLevel = record["Change Level"]
            if string.upper(changeLevel) == 'EO':
                deleteRows.append(row)
            row = row + 1

        table.data = system.dataset.deleteRows(ds, deleteRows)

