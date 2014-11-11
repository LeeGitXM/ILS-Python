'''
Created on Sep 10, 2014

@author: Pete
'''

import system

# Update the processedData to include the tag values and then make the subset of processed data that will
# be shown and put it in table.data.  (If the user is an engineer then processed data is all data, but 
# operators only see a subset of the data.
def refresh(rootContainer):
    import string
    print "---------------\nRefreshing Recipe Table..."
    
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    status = rootContainer.getPropertyValue("status")
    if status == 'Processing Download':
        system.gui.warningBox("Ignoring the refresh request because a download is in process!")
        return

    # The downloadType is either GradeChange or MidRun
    downloadType = rootContainer.getPropertyValue("downloadType")
    print "The Download Type is: ", downloadType 
    key = rootContainer.getPropertyValue("recipeKey")
    table = rootContainer.getComponent("Power Table")
    
    from ils.recipeToolkit.update import recipeMapStatus
    recipeMapStatus(key, "Refreshing")
    rootContainer.status = "Refreshing"
    
    localG2WriteAlias = system.tag.read("/Recipe/Constants/localG2WriteAlias").value
    recipeMinimumDifference = table.getPropertyValue("recipeMinimumDifference")
    recipeMinimumRelativeDifference = table.getPropertyValue("recipeMinimumRelativeDifference")

    ds = table.processedData
    pds = system.dataset.toPyDataSet(ds)
        
    # I'm not sure that we can force a device read in Ignition so put together a list of tags and we'll
    # read them all in one read. 
    # (I'm not sure that we were actually doing a device read anyway)

    tagNames = []
    localTagNames = []
    print "  ...extracting tagnames from the table..."
    for record in pds:
        step = record['Step']
        changeLevel = record['Change Level']
        writeLocation = record['Write Location']
#        print "Step: %s <%s>" % ( str(step), writeLocation)

        storTag = record['Store Tag']
        if writeLocation != "" and writeLocation != None and storTag != "":
            if writeLocation == localG2WriteAlias:
                if storTag not in localTagNames:
                    localTagNames.append(storTag)
            else:
                if storTag not in tagNames:
                    tagNames.append(storTag)

        compTag = record['Comp Tag']
        if writeLocation != "" and writeLocation != None and compTag != "":
            if writeLocation == localG2WriteAlias:
                if storTag not in localTagNames:
                    localTagNames.append(compTag)
            else:
                if storTag not in tagNames:
                    tagNames.append(compTag)
    
    # Now convert from MS Access tagnames to Ignition tagnames - First OPC Tags
    print "  ...converting tag names from SQL*Server format to Ignition format..."
    tags = []
    for tagName in tagNames:
        from ils.recipeToolkit.common import formatTagName
        tagName = formatTagName(provider, key, tagName)
        tags.append(tagName + '/Tag')

    print "  ...reading tag values..."
#    print tags
    values = system.tag.readAll(tags)
#    print values
    
    # Now the local tags
    print "  ...converting *local* tagnames from SQL*Server format to Ignition format..."
    tags = []
    for tagName in localTagNames:
        from ils.recipeToolkit.common import formatLocalTagName
        tagName = formatLocalTagName(provider, tagName)
        tags.append(tagName)

    print "  ...reading *local* tag values..."
    localValues = system.tag.readAll(tags)
    
    # We have now read all of the tags, merge the values back into the Python dataset
    print "  ...updating table dataset...."
    i = 0    
    for record in pds:
        step = record['Step']
        changeLevel = record['Change Level']
        writeLocation = record['Write Location']
        pendVal = record['Pend']
        download = False
    
        storTag = record['Store Tag']
        if writeLocation != "" and writeLocation != None and storTag != "":
            if writeLocation == localG2WriteAlias:
                idx = localTagNames.index(storTag)
                storVal = localValues[idx].value
                quality = localValues[idx].quality
            else:
                idx = tagNames.index(storTag)
                storVal = values[idx].value
                quality = values[idx].quality
                
            ds = system.dataset.setValue(ds, i, 'Stor', storVal)

    
        compTag = record['Comp Tag']
        if writeLocation != "" and writeLocation != None and compTag != "":
            if writeLocation == localG2WriteAlias:
                idx = localTagNames.index(compTag)
                compVal = localValues[idx].value
                quality = localValues[idx].quality
            else:
                idx = tagNames.index(compTag)
                compVal = values[idx].value
                quality = values[idx].quality

            ds = system.dataset.setValue(ds, i, "Comp", compVal)
            if downloadType == 'MidRun':
                ds = system.dataset.setValue(ds, i, "Pend", compVal)
                
#            print "line %i - step %i :: stor: %s - comp: %s" % (i, step, str(storVal), str(compVal))
        
        # This will override any reason that may have already been entered, which diesn't seem right
        if writeLocation == "" or writeLocation == None:
            reason = ""
        else:
            from ils.common.util import isText
            pendValIsText = isText(pendVal)
            storValIsText = isText(storVal)
#            print "StorVal: %s (Text: %s) PendVal: %s (Text: %s)" % (str(storVal), str(storValIsText), str(pendVal), str(pendValIsText))

            # Check if they are both text
            if storValIsText and pendValIsText:
                if storVal == pendVal:
                    reason = ""
                else:
                    reason = "Set to recipe value"
                    download = True
            else:
                # They aren't both text, so if only one is text, then they don't match 
                if storValIsText or pendValIsText:
                    reason = "Set to recipe value"
                    download = True
                else:
                    storVal = float(storVal)
                    pendVal = float(pendVal)

                    minThreshold = abs(recipeMinimumRelativeDifference * storVal)
                    if minThreshold < recipeMinimumDifference:
                        minThreshold = recipeMinimumDifference

                    if abs(storVal - float(pendVal)) < minThreshold:
                        reason = ""
                    else:
                        reason = "Set to recipe value"
                        download = True

        ds = system.dataset.setValue(ds, i, "Reason", reason)
        ds = system.dataset.setValue(ds, i, "Download", download)
#        print "Reason: ", reason
#        print ""

        i = i + 1
    table.processedData = ds
    
    refreshVisibleData(table)
    recipeMapStatus(key, "Refreshed")
    rootContainer.status = "Refreshed"
    from ils.common.util import getDate
    timestamp = getDate()
    rootContainer.timestamp = system.db.dateFormat(timestamp, "MM/dd/YY HH:mm")

#--------------------------------------------------------------------------------
# This script takes the processed data, considers the role of the users, and filters out OE data
# if the user is an operator
def refreshVisibleData(table):
    import string

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