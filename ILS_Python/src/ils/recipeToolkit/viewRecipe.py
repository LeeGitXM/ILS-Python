'''
Created on Sep 10, 2014

@author: Pete
'''
import system, string
from ils.recipeToolkit.tagFactory import createUDT
from sys import path
log = system.util.getLogger("com.ils.recipeToolkit.ui")

'''
This runs in the client when the operator presses the "View Recipe" button on the OC Alert.
The OC alert is sent in response to the Automated download tag
receiving a new Grade (a download is being initiated from the DCS) AND the automatedDownload tag of the download trigger UDT is set to FALSE, meaning that the 
download is initiated automatically, but the operator is in charge, so this is really a semi-automatic mode.  So all we have to do is launch the Recipe Viewer
screen with the new grade selected.  It is up to the operator to press the Download button and actually start the download.
'''
def semiAutomatedDownloadCallback(event, payload):
    print "In %s.automatedDownloadMessageHandler(), the payload is %s" % (__name__, payload)
    system.nav.closeParentWindow(event)
    
    targetPost = payload.get("post", "None")
    myPost = system.tag.read("[Client]Post").value

    # If the message was intended for another post then bail    
    if string.upper(targetPost) != string.upper(myPost):
        print "Bailing from a semi-automated download request because my post (%s) does not match the target post (%s)" % (string.upper(myPost), string.upper(targetPost))
        return
    
    '''
    There is a requirement that only one download can happen at a time, so if the recipe screen is open and a new request comes in then the old 
    one should be dismissed.  There can only ever be one review data screen at a time.
    '''
    wins = system.gui.getOpenedWindows()
    for win in wins:
        print win.getPath()
        if win.getPath() == "Recipe/Recipe Viewer":
            print "Found a recipe viewer that was already open - closing it"
            system.nav.closeWindow(win.getPath())
        
    
    grade = payload.get("grade", "")
    version = payload.get("version", 0)
    recipeKey = payload.get("recipeKey", "")
    downloadType = 'GradeChange'
    
    # Save the grade and type to the recipe map table.
    SQL = "update RtRecipeFamily set CurrentGrade = '%s', CurrentVersion = %s, Status = 'Initializing', "\
        "Timestamp = getdate() where RecipeFamilyName = '%s'" \
        % (str(grade), version, recipeKey)
    
    print "SQL: ", SQL
    rows = system.db.runUpdateQuery(SQL)
    print "Successfully updated %i rows" % (rows)

    system.nav.openWindow('Recipe/Recipe Viewer', {'familyName': recipeKey, 'grade': grade, 'version': version, 'downloadType':downloadType})
    system.nav.centerWindow('Recipe/Recipe Viewer')
    
def showCurrentRecipeCallback(familyName):
    print "In project.recipe.viewRecipe.showCurrentRecipeCallback()"
    # Fetch the grade and type from the recipe map table. The grade looks like an int, 
    # but it is probably a string
    SQL = "select CurrentGrade from RtRecipeFamily where RecipeFamilyName = '%s'" % (familyName)
    print "SQL: ", SQL
    pds = system.db.runQuery(SQL)

    if len(pds) == 0:
        system.gui.errorBox("Unable to retrieve the current recipe for recipe key: %s" % (familyName), "Error")
        return 

    if len(pds) > 1:
        system.gui.errorBox("Multiple rows retrieve for the current recipe for recipe key: %s" % (familyName), "Error")
        return 

    record = pds[0];
    grade = record["CurrentGrade"]
    grade = str(grade)
    
    print "Fetched %s" % (str(grade))
    
    system.nav.openWindow('Recipe/Recipe Viewer', {'familyName': familyName, 'grade': grade,'downloadType':'GradeChange'})
    system.nav.centerWindow('Recipe/Recipe Viewer')

    return

def showMidRunRecipeCallback(recipeFamilyName):
    print "In project.recipe.viewRecipe.showCurrentRecipeCallback()"
    #   Fetch the grade and type from the recipe map table. The grade looks like an int, but it is probably a string
    SQL = "select CurrentGrade from RtRecipeFamily where RecipeFamilyName = '%s'" % (recipeFamilyName)
    print "SQL: ", SQL
    pds = system.db.runQuery(SQL)

    if len(pds) == 0:
        system.gui.errorBox("Unable to retrieve the current recipe for recipe family: %s" % (recipeFamilyName), "Error")
        return 

    if len(pds) > 1:
        system.gui.errorBox("Multiple rows retrieve for the current recipe for recipe family: %s" % (recipeFamilyName), "Error")
        return 

    record = pds[0];
    grade = record["CurrentGrade"]
    grade = str(grade)
    
    print "Fetched %s" % (str(grade))
    
    system.nav.openWindow('Recipe/Recipe Viewer', {'familyName': recipeFamilyName, 'grade': grade,'downloadType':'MidRun'})
    system.nav.centerWindow('Recipe/Recipe Viewer')

    return


def initialize(rootContainer):
    log.infof("In project.recipe.viewRecipe.initialize()...")

    #=============================================================================================
    # This function is definitely a workaround.  When I try to bind my custom color properties directly to a tag, they 
    # don't work the very first time I open a window.  So here I will explicitly read the tags and set the properties, 
    # which is exactly what a binding is supposed to do automatically
    def initializeTableColors(table):
        color = system.tag.read("/Configuration/RecipeToolkit/backgroundColorError").value
        table.setPropertyValue("backgroundColorError", color)
        
        color = system.tag.read("/Configuration/RecipeToolkit/backgroundColorMismatch").value
        table.setPropertyValue("backgroundColorMismatch", color)
        
        color = system.tag.read("/Configuration/RecipeToolkit/backgroundColorNoChange").value
        table.setPropertyValue("backgroundColorNoChange", color)
        
        color = system.tag.read("/Configuration/RecipeToolkit/backgroundColorReadOnly").value
        table.setPropertyValue("backgroundColorReadOnly", color)

        color = system.tag.read("/Configuration/RecipeToolkit/backgroundColorReadWrite").value
        table.setPropertyValue("backgroundColorReadWrite", color)

        color = system.tag.read("/Configuration/RecipeToolkit/backgroundColorWriteError").value
        table.setPropertyValue("backgroundColorWriteError", color)

        color = system.tag.read("/Configuration/RecipeToolkit/backgroundColorWritePending").value
        table.setPropertyValue("backgroundColorWritePending", color)

        color = system.tag.read("/Configuration/RecipeToolkit/backgroundColorWriteSuccess").value
        table.setPropertyValue("backgroundColorWriteSuccess", color)
        
        val = system.tag.read("/Configuration/RecipeToolkit/recipeMinimumDifference").value
        table.setPropertyValue("recipeMinimumDifference", val)
        
        val = system.tag.read("/Configuration/RecipeToolkit/recipeMinimumRelativeDifference").value
        table.setPropertyValue("recipeMinimumRelativeDifference", val)
    #=======================================================================================
        
    from ils.common.config import getTagProviderClient
    provider = getTagProviderClient()
    rootContainer.provider = provider
    familyName = rootContainer.familyName
    grade = rootContainer.grade
    version = rootContainer.version

    # fetch the recipe family
    from ils.recipeToolkit.fetch import recipeFamily as fetchRecipeFamily
    recipeFamily = fetchRecipeFamily(familyName)

    status = str(recipeFamily['Status'])
    rootContainer.status = status
    timestamp = recipeFamily['Timestamp']
    log.tracef( "Status: %s - %s", status, str(timestamp))
    rootContainer.timestamp = system.db.dateFormat(timestamp, "MM/dd/yy HH:mm")

    # Set the background color based on the status 
    from ils.recipeToolkit.common import setBackgroundColor
    if string.upper(status) == 'INITIALIZING':
        setBackgroundColor(rootContainer, "screenBackgroundColorInitializing")
    else:
        setBackgroundColor(rootContainer, "screenBackgroundColorDownloading")

    # Fetch the recipe
    from ils.recipeToolkit.fetch import details
    pds = details(familyName, grade, version)

    # Initialize table colors and put the raw recipe into a dataset attribute of the table
    table = rootContainer.getComponent('Power Table')
    initializeTableColors(table)
    table.rawData = pds

    # Create the processed data set by adding some columns to the raw recipe data. 
    dsProcessed = update(pds)
    table.processedData = dsProcessed
    
    # Reset the recipe detail objects
    resetRecipeDetails(provider, familyName)

    # Create any OPC tags that are required by the recipe
    dsProcessed, tags = createOPCTags(table.processedData, provider, familyName)
    table.processedData = dsProcessed
    
    # Sweep the folder of recipe tags and delete any that are not needed
    sweepTags(provider, familyName, tags)

    # Refresh the table with data from the DCS
    from ils.recipeToolkit.refresh import refresh
    refresh(rootContainer)


# Reset all of the recipe detail objects.  This really isn't necessary for the detail objects that
# were newly created, but is necessary for ones that were existing
def resetRecipeDetails(provider, familyName):
    log.infof("Resetting recipe details...")
            
    tags = []
    vals = []
    path = "[%s]Recipe/%s/" % (provider, familyName)

    for udtType in ['Recipe Data/Recipe Details']:
        details = system.tag.browseTags(path, udtParentType=udtType)
        for detail in details:
            tags.append(path + detail.name + "/valueTagName")
            vals.append("")
                    
            tags.append(path + detail.name + "/highLimitTagName")
            vals.append("")
                
            tags.append(path + detail.name + "/lowLimitTagName")
            vals.append("")
            
            tags.append(path + detail.name + "/command")
            vals.append("")
            
    system.tag.writeAll(tags, vals)

# Update the table with the recipe data - this is called when we change the grade.  This does not
# incorporate the DCS data, that is done in refresh()
def update(rawData):
    log.trace("In project.recipe.viewRecipe.update()")
    log.trace("Updating the table with data from the recipe database")

    headers = ['Descriptor', 'Pend', 'Stor', 'Comp', 'Recc', 'High Limit', 'Low Limit', 'Reason',\
        'Store Tag', 'Comp Tag', 'Change Level', 'Write Location', 'Step', 'Mode Attribute', \
        'Mode Attribute Value', 'Download Type', 'Download', 'Data Type', 'Plan Status', 'Download Status', 'ValueId', 'ValueType']
        
    data = []
    for record in rawData:
        step = record['PresentationOrder']
        descriptor = record['Description']
        valueId = record['ValueId']
        downloadType = 'skip'
        download = False
        dataType = ''
        downloadStatus = ''
        planStatus = ''
        valueType = record['ValueType']
        
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
            writeLocation, step, modeAttribute, modeValue, downloadType, download, dataType, planStatus, downloadStatus, valueId, valueType]

        data.append(vals)
#        print vals

    dsProcessed = system.dataset.toDataSet(headers, data)
    
    return dsProcessed


# ds is the processed data of the table
def createOPCTags(ds, provider, recipeKey, database = ""):
    from ils.recipeToolkit.tagFactory import createRecipeDetailUDT
    from ils.recipeToolkit.common import formatLocalTagPathAndName
    
    #------------------------------------------------------------
    # Fetch the alias to OPC server map from the EMC database
    def fetchOPCServers(database):
        SQL = "select * from TkWriteLocation"
        pds = system.db.runQuery(SQL, database)
        log.tracef("Fetched %d OPC servers...", len(pds))
        return pds
    #------------------------------------------------------------
    # Given an alias for a write location from the recipe database and the alias/OPC Server map,
    # find the OPC server that corresponds to the 
    def determineOPCServer(writeLocation, opcServers):
        serverName = 'Unknown'
        scanClass = 'Unknown'
        for server in opcServers:
            if writeLocation == server['Alias']:
                serverName = server['ServerName']
                scanClass = server['ScanClass']
        return serverName,scanClass
    #------------------------------------------------------------
    # Parse the tagname from the recipe database to determine the root and the suffix (PV, SP, etc.)
    def parseRecipeTagName(recipeTagName):
    
        log.tracef("Parsing %s...", recipeTagName)
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

        log.tracef("...returning %s %s %s", tagRoot, tagSuffix, tagName)
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
    # Determine if the recommended is a float or a text - everything is stored in the table as text.
    def determineTagClass(recc, valueType, modeAttribute, modeAttributeValue, specialValueNAN):

        if valueType == 'String':
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
        
        return className, conditionalDataType
    #------------------------------------------------------------

    log.tracef("Creating OPC recipe tags...")
    
    tags = []
    recipeDetailTagNames = []
    recipeDetailTagValues = []
    specialValueNAN = system.tag.read("[" + provider + "]Configuration/RecipeToolkit/Special Values/NAN").value
    localWriteAlias = system.tag.read("[" + provider + "]Configuration/RecipeToolkit/localWriteAlias").value
    itemIdPrefix = system.tag.read("[" + provider + "]Configuration/RecipeToolkit/itemIdPrefix").value
    
    log.tracef("Special NAN Value: %s", str(specialValueNAN))
    log.tracef("Local G2 Alias: %s", str(localWriteAlias))
    
    # There needs to be at least one OPC write alias or nothing will work!
    opcServers = fetchOPCServers(database)
    if len(opcServers) == 0:
        system.gui.errorBox("The RtWriteLocation table in the SQL*Server database is not configured properly.  The OPC server aliases must be configured before tags can be created.")
        return tags
    
    # I'm not sure that we can force a device read in Ignition so put together a list of tags and we'll
    # read them all in one read. (I'm not sure that we were actually doing a device read anyway)

    i = 0
    pds = system.dataset.toPyDataSet(ds)
    for record in pds:
        step = record['Step']
        changeLevel = record['Change Level']
        writeLocation = record['Write Location']
        valueType = record['ValueType']
    
        log.tracef("--- Step: %s - %s ---", str(step), writeLocation)
        downloadType = "Skip"
        dataType = ''
        if string.upper(str(writeLocation)) == string.upper(str(localWriteAlias)):
            log.tracef("Handling a local tag")
            downloadType = "Immediate"

            tagName = record['Store Tag']       
            tagPath, tagName = formatLocalTagPathAndName(provider, tagName)
            
            # Determine the data type by browsing the tag
            browseTags = system.tag.browseTags(parentPath=tagPath, tagPath="*"+tagName)
            
            if len(browseTags) == 0:
                log.tracef("The tag %s does not exist", tagName)
                dataType = "Float"
            else:
                browseTag = browseTags[0]
                dataType = browseTag.dataType
                dataType = str(dataType)
            
                if dataType == "Float8":
                    dataType = "Float"
                
        elif writeLocation != "" and writeLocation != None:
            log.tracef("Handling an OPC tag")
            modeAttribute = record['Mode Attribute']
            modeAttributeValue = record['Mode Attribute Value']
            recc = record['Recc']
            
            # I'm not sure we we use the store tag here and not the compare tag??
            storeTag = record['Store Tag']
            if storeTag not in ["", None, "NULL", "null"]:
                opcServer, scanClass = determineOPCServer(writeLocation, opcServers)
                
                if string.upper(opcServer) == 'UNKNOWN':
                    system.gui.warningBox("%s will be created with an unknown OPC Server, update the alias %s" % (storeTag, writeLocation)) 

                # There is a store tag, so assume it will be an immediate download, may change to deferred later
                downloadType = "Immediate"
                
                # Use the modeAttribute, modeAttributeValue and recc to determine the class of tag
                tagRoot, tagSuffix, tagName = parseRecipeTagName(storeTag)
                modeAttribute, modeAttributeValue = determineOPCTypeModeAndVal(modeAttribute, modeAttributeValue)
                UDTType, conditionalDataType = determineTagClass(recc, valueType, modeAttribute, modeAttributeValue, specialValueNAN)
                log.tracef("The OPC server is: %s and class name (UDT) is: %s", opcServer,UDTType)
                itemId = itemIdPrefix + storeTag

                path = "/Recipe/" + recipeKey

                # The tag factory will check if the tag already exists
                createUDT(UDTType, provider, path, valueType, tagName, opcServer, scanClass, itemId, conditionalDataType)

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
    
    return ds, tags

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