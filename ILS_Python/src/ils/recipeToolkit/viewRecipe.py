'''
Created on Sep 10, 2014

@author: Pete
'''
import system

def showCurrentRecipeCallback(recipeKey):
    print "In project.recipe.viewRecipe.showCurrentRecipeCallback()"
    # Fetch the grade and type from the recipe map table. The grade looks like an int, 
    # but it is probably a stringgggg
    SQL = "select CurrentRecipeGrade from RtRecipeMap where RecipeKey = '%s'" % (recipeKey)
    print "SQL: ", SQL
    pds = system.db.runQuery(SQL)

    if len(pds) == 0:
        system.gui.errorBox("Unable to retrieve the current recipe for recipe key: %s" % (recipeKey), "Error")
        return 

    if len(pds) > 1:
        system.gui.errorBox("Multiple rows retrieve for the current recipe for recipe key: %s" % (recipeKey), "Error")
        return 

    record = pds[0];
    grade = record["CurrentRecipeGrade"]
    grade = str(grade)
    
    print "Fetched %s" % (str(grade))
    
    system.nav.openWindow('Recipe/Recipe Viewer', {'recipeKey': recipeKey, 'grade': grade,'downloadType':'GradeChange'})
    system.nav.centerWindow('Recipe/Recipe Viewer')

    return

def showMidRunRecipeCallback(recipeKey):
    print "In project.recipe.viewRecipe.showCurrentRecipeCallback()"
    # Fetch the grade and type from the recipe map table. The grade looks like an int, but it is probably a string
    SQL = "select CurrentRecipeGrade from RtRecipeMap where RecipeKey = '%s'" % (recipeKey)
    print "SQL: ", SQL
    pds = system.db.runQuery(SQL)

    if len(pds) == 0:
        system.gui.errorBox("Unable to retrieve the current recipe for recipe key: %s" % (recipeKey), "Error")
        return 

    if len(pds) > 1:
        system.gui.errorBox("Multiple rows retrieve for the current recipe for recipe key: %s" % (recipeKey), "Error")
        return 

    record = pds[0];
    grade = record["CurrentRecipeGrade"]
    grade = str(grade)
    
    print "Fetched %s" % (str(grade))
    
    system.nav.openWindow('Recipe/Recipe Viewer', {'recipeKey': recipeKey, 'grade': grade,'downloadType':'MidRun'})
    system.nav.centerWindow('Recipe/Recipe Viewer')

    return


def initialize(rootContainer):
    import string

    print "In project.recipe.viewRecipe.initialize()..."

    from ils.common.config import getTagProvider
    provider = getTagProvider()
    rootContainer.provider = provider
    recipeKey = rootContainer.recipeKey
    grade = rootContainer.grade
    version = rootContainer.version

    # fetch the recipe map which will specify the database and table containing the recipe
    from ils.recipeToolkit.fetch import recipeMap
    recipeMap = recipeMap(recipeKey)

    status = recipeMap['Status']
    rootContainer.status = status
    timestamp = recipeMap['Timestamp']
    rootContainer.timestamp = system.db.dateFormat(timestamp, "MM/dd/YY HH:mm")

    # Set the background color based on the status
    from ils.recipeToolkit.common import setBackgroundColor
    if string.upper(status) == 'INITIALIZING':
        setBackgroundColor(rootContainer, "screenBackgroundColorInitializing")
    else:
        setBackgroundColor(rootContainer, "screenBackgroundColorDownloading")

    # Fetch the recipe
    from ils.recipeToolkit.fetch import details
    pds = details(recipeKey, grade, version)

    # Put the raw recipe into a dataset attribute of the table
    table = rootContainer.getComponent('Power Table')
    table.rawData = pds

    # Update the table
    dsProcessed = update(rootContainer)

    # Reset the recipe detail objects
    resetRecipeDetails(provider, recipeKey)

    # Create any OPC tags that are required by the recipe
    tags = createOPCTags(table, provider, recipeKey)
    
    # Sweep the folder of recipe tags and delete any that are not needed
    sweepTags(provider, recipeKey, tags)

    # Refresh the table with data from the DCS
    from ils.recipeToolkit.refresh import refresh
    refresh(rootContainer)


# Reset all of the recipe detail objects.  This really isn't necessary for the detail objects that
# were newly created, but is necessary for ones that were existing
def resetRecipeDetails(provider, recipeKey):
    print "Resetting recipe details..."
            
    tags = []
    vals = []
    path = "[%s]Recipe/%s/" % (provider, recipeKey)

    for udtType in ['Recipe Data/Recipe Details']:
        details = system.tag.browseTags(path, udtParentType=udtType)
        for detail in details:
            tags.append(path + detail.name + "/value")
            vals.append(-1)
            tags.append(path + detail.name + "/valueTagName")
            vals.append("")
                    
            tags.append(path + detail.name + "/highLimit")
            vals.append(-1)
            tags.append(path + detail.name + "/highLimitTagName")
            vals.append("")
                
            tags.append(path + detail.name + "/lowLimit")
            vals.append(-1)
            tags.append(path + detail.name + "/lowLimitTagName")
            vals.append("")
            
            tags.append(path + detail.name + "/command")
            vals.append("")
            
    system.tag.writeAll(tags, vals)

# Update the table with the recipe data - this is called when we change the grade.  This does not
# incorporate the DCS data, that is done in refresh()
def update(rootContainer):
    print "In project.recipe.viewRecipe.update()"
    print "Updating the table with data from the recipe database and the DCS"

    from ils.common.user import isAE
    isAE = isAE()
    table = rootContainer.getComponent('Power Table')
    rawData = table.rawData
    
    headers = ['Descriptor', 'Pend', 'Stor', 'Comp', 'Recc', 'High Limit', 'Low Limit', 'Reason',\
        'Store Tag', 'Comp Tag', 'Change Level', 'Write Location', 'Step', 'Mode Attribute', \
        'Mode Attribute Value', 'Download Type', 'Download', 'Data Type', 'Download Status', 'ValueId']
        
    data = []
    for record in system.dataset.toPyDataSet(rawData):
        step = record['PresentationOrder']
        descriptor = record['Description']
        valueId = record['ValueId']
        downloadType = 'skip'
        download = False
        dataType = ''
        downloadStatus = ''
        
        if descriptor != None:
            pend = record['RecommendedValue']
            stor = ''
            comp = ''
            recommendedValue = record['RecommendedValue']
            highLimit = record['HighLimit']
            lowLimit = record['LowLimit']
            storeTag = record['StoreTag']
            compareTag = record['CompareTag']
            changeLevel = record['ChangeLevel']
            writeLocation = record['WriteLocation']
            modeAttribute = record['ModeAttribute']
            modeValue = record['ModeValue']
            if changeLevel == 'CC':
                reason = ''
            else:
                reason = "Set to recipe value"
        else:
            pend = ''
            stor = ''
            comp = ''
            recommendedValue = ''
            highLimit = ''
            lowLimit = ''
            storeTag = ''
            compareTag = ''
            changeLevel = ''
            writeLocation = ''
            modeAttribute = ''
            modeValue = ''
            reason = ''

        vals = [descriptor, pend, stor, comp, recommendedValue, highLimit, lowLimit, reason, storeTag, compareTag, changeLevel, \
            writeLocation, step, modeAttribute, modeValue, downloadType, download, dataType, downloadStatus, valueId]
        data.append(vals)

    ds = system.dataset.toDataSet(headers, data)
    table.processedData = ds
    return ds


def createOPCTags(table, provider, recipeKey):
    import string
    from ils.recipeToolkit.tagFactory import createRecipeDetailUDT
    
    #------------------------------------------------------------
    # Fetch the alias to OPC server map from the EMC database
    def fetchOPCServers():
        SQL = "select * from RtWriteLocation"
        pds = system.db.runQuery(SQL)
        print "Fetched ", len(pds), " OPC servers..."
        return pds
    #------------------------------------------------------------
    # Given an alias for a write location from the recipe database and the alias/OPC Server map,
    # find the OPC server that corresponds to the 
    def determineOPCServer(writeLocation, opcServers):
        serverName = 'Unknown'
        scanClass = 'unknown'
        for server in opcServers:
            if writeLocation == server['Alias']:
                serverName = server['ServerName']
                scanClass = server['ScanClass']
        return serverName,scanClass
    #------------------------------------------------------------
    # Parse the tagname from the recipe database to determine the root and the suffix (PV, SP, etc.)
    def parseRecipeTagName(recipeTagName):
    
        if len(recipeTagName) == 0:
            tagRoot = ""
            tagSuffix = ""
            tagName = ""
        else:
            period = recipeTagName.rfind('.')
            if period < 0:
                tagRoot = recipeTagName
                tagSuffix = ""
                tagName = recipeTagName
            else:
                tagRoot = recipeTagName[:period]
                tagSuffix = recipeTagName[period+1:]
                tagName = tagRoot + "." + tagSuffix
                
            from ils.recipeToolkit.common import updateTagName
            tagRoot = updateTagName(tagRoot)
            tagName = updateTagName(tagName)

#        print "Input tagname: <%s> split into <%s> <%s>" % (recipeTagName, tagRoot, tagSuffix)
        return tagRoot, tagSuffix, tagName
    #------------------------------------------------------------
    def determineOPCTypeModeAndVal(modeAttribute, modeAttributeValue):
        # Determine the full mode attribute tag path
        if modeAttribute == None:
            modeAttribute = ""
        else:
            modeAttribute = string.upper(modeAttribute)
    
        # Convert the modeAttributeValue from a text string that looks like a number to a number
        if modeAttributeValue == None:
            modeAttributeValue = ""
        else:
            try:
                val = float(modeAttributeValue)
                modeAttributeValue = round(float(modeAttributeValue))
            except:
                pass

        return modeAttribute, modeAttributeValue
    #------------------------------------------------------------
    # Determine if recc is a float or a text - everything is stored in the table as text.
    def determineTagClass(recc, modeAttribute, modeAttributeValue, specialValueNAN):
    
        try:
            val = float(recc)
            isText = False
            dataType = 'Float'
        except:
            isText = True
            dataType = 'String'

        if isText:
            if modeAttribute != "":
                className = "OPC Conditional Output"
                if modeAttributeValue != specialValueNAN:
                    conditionalDataType = "String"
                else:
                    conditionalDataType = "Int8"
            else:
                className = "OPC Output"
                conditionalDataType = None
    
        else:
            if modeAttribute != "":
                className = "OPC Conditional Output"
                if modeAttributeValue != specialValueNAN:
                    conditionalDataType = "String"
                else:
                    conditionalDataType = "Int8"
            else:
                className = "OPC Output"
                conditionalDataType = None

#        print "The tag class is: %s (%s - %s - %s)" % (className, recc, modeAttribute, modeAttributeValue)
        
        return className, dataType, conditionalDataType
    #------------------------------------------------------------

    print "Creating recipe tags..."
    
    ds = table.processedData
    pds = system.dataset.toPyDataSet(ds)
    tags = []
    recipeDetailTagNames = []
    recipeDetailTagValues = []
    specialValueNAN = system.tag.read("Recipe/Constants/Special Values/NAN").value
    localG2WriteAlias = system.tag.read("Recipe/Constants/localG2WriteAlias").value
    print "*** The local G2 write alias is: <%s> ***" % (localG2WriteAlias)
    opcServers = fetchOPCServers()
    # I'm not sure that we can force a device read in Ignition so put together a list of tags and we'll
    # read them all in one read. (I'm not sure that we were actually doing a device read anyway)

    i = 0
    for record in pds:
        step = record['Step']
        changeLevel = record['Change Level']
        writeLocation = record['Write Location']
    
#        print "\nStep: ", step, writeLocation
        downloadType = "Skip"
        dataType = ''
        if writeLocation == localG2WriteAlias:
            downloadType = "Immediate"
            
        elif writeLocation != "" and writeLocation != None:
            modeAttribute = record['Mode Attribute']
            modeAttributeValue = record['Mode Attribute Value']
            recc = record['Recc']
            
            # I'm not sure we we use the store tag here and not the compare tag??
            storeTag = record['Store Tag']
            if storeTag != "":
                opcServer, scanClass = determineOPCServer(writeLocation, opcServers)

                # There is a store tag, so assume it will be an immediate download, may change to deferred later
                downloadType = "Immediate"
                
                # Use the modeAttribute, modeAttributeValue and recc to determine the class of tag
                tagRoot, tagSuffix, tagName = parseRecipeTagName(storeTag)
                modeAttribute, modeAttributeValue = determineOPCTypeModeAndVal(modeAttribute, modeAttributeValue)
                UDTType, dataType, conditionalDataType = determineTagClass(recc, modeAttribute, modeAttributeValue, specialValueNAN)
#                print "The OPC server is: ", opcServer, " and class name (UDT) is: ", UDTType
                itemId = storeTag

                path = "/Recipe/" + recipeKey
                from ils.recipeToolkit.tagFactory import createUDT
                createUDT(UDTType, provider, path, dataType, tagName, opcServer, scanClass, itemId, conditionalDataType)

                # The tags list list all of the tags that are required for this recipe.  It will be used
                # later to determine which tags are no longer required. 
#                fullTagName = str("[" + provider + "]Recipe/" + recipeKey + '/' + tagName)
                if tagName not in tags:
                    tags.append(tagName)

                # If I encounter a tag with a any of these suffixes then create a recipe detail so
                # that the write can be coordinated.  Just because there is a SP doesn't necessarily 
                # mean that there will be limits / clamps, but that is OK, better to have the object
                # and not need it than to need it and not have it! 
                
                #
                # 7/18/14 - Changed the name of the UDT to create to use the same UDT for all 3 types of recipe detail
                #
                if string.upper(tagSuffix) in ['SP', 'SPCH', 'SPCL', 'SPHILM', 'SPLOLM']:
                    detailTagName = tagRoot + '-SPDETAILS'
                    createRecipeDetailUDT('Recipe Details', provider, path, detailTagName)

                    if string.upper(tagSuffix) in string.upper(tagSuffix) in ['SPCH', 'SPHILM']:
                        downloadType = "Deferred High Limit"
                        detailAttribute = 'highLimit'
                    elif string.upper(tagSuffix) in ['SPCL', 'SPLOLM']:
                        downloadType = "Deferred Low Limit"
                        detailAttribute = 'lowLimit'
                    else:
                        downloadType = "Deferred Value"
                        detailAttribute = 'value'
                    
                    # Update the recipe detail objects appropriately
                    recipeDetailTagNames.append('[' + provider + ']' + path + '/' + detailTagName + '/' + detailAttribute)
                    recipeDetailTagValues.append(1)
                    recipeDetailTagNames.append('[' + provider + ']' + path + '/' + detailTagName + '/' + detailAttribute + 'TagName')
                    recipeDetailTagValues.append(tagName)
                    
                    if detailTagName not in tags: tags.append(detailTagName)
                    
                elif string.upper(tagSuffix) in ['PV', 'PVHILM', 'PVLOLM']:
                    detailTagName = tagRoot + '-PVDETAILS'
                    createRecipeDetailUDT('Recipe Details', provider, path, detailTagName)

                    if string.upper(tagSuffix) in ['PVHILM']:
                        downloadType = "Deferred High Limit"
                        detailAttribute = 'highLimit'
                    elif string.upper(tagSuffix) in ['PVLOLM']:
                        downloadType = "Deferred Low Limit"
                        detailAttribute = 'lowLimit'
                    else:
                        downloadType = "Deferred Value"
                        detailAttribute = 'value'
            
                    # Update the recipe detail objects appropriately
                    recipeDetailTagNames.append('[' + provider + ']' + path + '/' + detailTagName + '/' + detailAttribute)
                    recipeDetailTagValues.append(1)
                    recipeDetailTagNames.append('[' + provider + ']' + path + '/' + detailTagName + '/' + detailAttribute + 'TagName')
                    recipeDetailTagValues.append(tagName)
                                            
                    if detailTagName not in tags: tags.append(detailTagName)
                    
                elif string.upper(tagSuffix) in ['OP', 'OPCH', 'OPCL', 'OPHILM', 'OPLOLM']:
                    detailTagName = tagRoot + '-OPDETAILS'
                    createRecipeDetailUDT('Recipe Details', provider, path, detailTagName)

                    if string.upper(tagSuffix) in ['OPCH', 'OPHILM']:
                        downloadType = "Deferred High Limit"
                        detailAttribute = 'highLimit'
                    elif string.upper(tagSuffix) in ['OPCL', 'OPLOLM']:
                        downloadType = "Deferred Low Limit"
                        detailAttribute = 'lowLimit'
                    else:
                        downloadType = "Deferred Value"
                        detailAttribute = 'value'

                    # Update the recipe detail objects appropriately
                    recipeDetailTagNames.append('[' + provider + ']' + path + '/' + detailTagName + '/' + detailAttribute)
                    recipeDetailTagValues.append(1)
                    recipeDetailTagNames.append('[' + provider + ']' + path + '/' + detailTagName + '/' + detailAttribute + 'TagName')
                    recipeDetailTagValues.append(tagName)

                    if detailTagName not in tags: tags.append(detailTagName)

        ds = system.dataset.setValue(ds, i, "Download Type", downloadType) 
        ds = system.dataset.setValue(ds, i, "Data Type", dataType) 
        i = i + 1

    # Update the recipe detail objects, they were previously reset, now update
    results = system.tag.writeAll(recipeDetailTagNames, recipeDetailTagValues)

    table.processedData = ds
    return tags

# This is called whenever we fetch a new recipe from the database.  It deletes any recipe tags that are 
# not needed by the current recipe.
def sweepTags(provider, recipeKey, tags):
    print "Sweeping unused recipe tags..."

    unneededTags = []
    path = "[" + provider + "]Recipe/" + recipeKey
    existingTags = system.tag.browseTagsSimple(path, "ASC")
    for tag in existingTags:
        
        if tag.isUDT():
            if tag.name not in tags:
                unneededTags.append(path + '/' + tag.name)
                print "   Deleting unneeded tag: ", tag.name

    system.tag.removeTags(unneededTags)
    print "   Done (%i tags were deleted)!" % ( len(unneededTags) )