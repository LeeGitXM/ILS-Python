'''
Created on Mar 10, 2015

@author: Pete
'''   
# Import the standard Python XML parsing library    
import xml.etree.ElementTree as ET
import sys, system, string, traceback
from ils.migration.common import lookupOPCServerAndScanClass
from ils.common.database import getUnitId
from ils.common.database import getPostId
from ils.common.database import lookup

def insertLabTableIntoDB(container):
    print "In migration.labData.insertLabTableIntoDB()"

    filename = container.getComponent('File Field').text
    
    if not(system.file.fileExists(filename)):
        system.gui.errorBox("The import file (" + filename + ") does not exist. Please specify a valid filename.")  
        return

    tree = ET.parse(filename)
    root = tree.getroot()

    for table in root.findall('console'):
        post = table.get("post")
        postId = getPostId(post)
        displayOrder = table.get("dataOrder")
        displayFlag = table.get("showInList")
        from ils.common.cast import toBit
        displayFlag = toBit(displayFlag)
        displayTableTitle = table.get("description")
        oldTableName = table.get("consoleName")
        displayPage = 1
        
        if postId > 0:
            SQL = "select DisplayTableId from LtDisplayTable where DisplayTableTitle = '%s'" % (displayTableTitle)
            displayTableId = system.db.runScalarQuery(SQL)
        
            if displayTableId == None:
                SQL = "insert into LtDisplayTable (DisplayTableTitle, postId, DisplayPage, DisplayOrder, DisplayFlag, OldTableName) values " \
                    "('%s', %i, %i, %s, %s, '%s')" % (displayTableTitle, postId, displayPage, displayOrder, displayFlag, oldTableName)
                print SQL
                displayTableId = system.db.runUpdateQuery(SQL, getKey=1)
        
            print "%s - %s - %s - %s" % (oldTableName, displayTableTitle, displayFlag, displayOrder)
            for labData in table.findall('labData'):
                # There is only room for one description, and it came from the other file, so ignore this one
                labDescription = labData.get("labDescription")
                valueName = labData.get("labDataName")
                print "     Setting display table for %s" % (valueName)
                SQL = "update LtValue set DisplayTableId = %s where ValueName = '%s'" % (str(displayTableId), valueName)
                system.db.runUpdateQuery(SQL)
        else:
            print "Skipping %s because a post <%s> was not found!" % (displayTableTitle, post)
            
    print "Done!"



def lookupLabConsoleId(consoleName):
    SQL = "select labConsoleId from LtConsoles where ConsoleName = '%s'" % (consoleName)
    consoleId = system.db.runScalarQuery(SQL)
    if consoleId == None:
        SQL = "insert into LtConsoles (ConsoleName) values ('%s')" % (consoleName)
        consoleId=system.db.runUpdateQuery(SQL, getKey=1)
    print "Fetched Console Id: ", consoleId 
    return consoleId

# Insert the necessary lab data objects into the database   
def insertIntoDB(container):
    print "In migration.labData.insertIntoDB()"
    
    #----------------------------------------------------
    def alreadyLoaded(valueName):    
        SQL = "select count(*) from LtValue where ValueName = '%s'" % (valueName)
        rows = system.db.runScalarQuery(SQL)
        if rows > 0:
            alreadyLoaded = True
        else:
            alreadyLoaded = False
        return alreadyLoaded
    #----------------------------------------------------
    
    filename = container.getComponent('File Field').text
    provider = container.getComponent("Tag Provider").text
    site = container.parent.getComponent("Site").text
    
    if not(system.file.fileExists(filename)):
        system.gui.errorBox("The import file (" + filename + ") does not exist. Please specify a valid filename.")  
        return
    
    tree = ET.parse(filename)
    root = tree.getroot()

    loaded = 0
    skipped = 0
    alreadyExists = 0
    for labData in root.findall('lab-data'):
        name=labData.get("name")
    
        if not(alreadyLoaded(name)):
            className = labData.get("class")
            unitName = labData.get("unit-name")
            print "Processing %s, a %s (unit: %s)" % (name, className, unitName)
        
            if className == "LAB-PHD-SQC":
                print "   Creating..."
                valueId=insertLabValue(labData, unitName)
                insertPHDLabValue(labData, valueId)
                insertSQCLimit(labData,valueId)
                loaded=loaded+1
                print "   ...done!"
            
            elif className == "LAB-DCS-SQC":
                print "   Creating..."
                valueId=insertLabValue(labData, unitName)
                insertDCSLabValue(labData, valueId, site)
                insertSQCLimit(labData,valueId)
                loaded=loaded+1
                print "   ...done!"
            
            elif className == "LAB-PHD-RELEASE":
                print "   Creating..."
                valueId=insertLabValue(labData, unitName)
                insertPHDLabValue(labData, valueId)
                insertReleaseLimit(labData,valueId)
                loaded=loaded+1
                print "   ...done!"
                
            elif className == "LAB-PHD-SQC-SELECTOR":
                print "   Creating..."
                valueId=insertLabValue(labData, unitName)
                loaded=loaded+1
                print "   ...done!"

            elif className == "LAB-PHD-RELEASE-SELECTOR":
                print "   Creating..."
                valueId=insertLabValue(labData, unitName)
                loaded=loaded+1
                print "   ...done!"
            
#        elif className == "LAB-PHD-DERIVED-SQC":
#            print "   ...skipping..."
            elif className == "LAB-PHD-SELECTOR":
                print "   Creating..."
                valueId=insertLabValue(labData, unitName)
                loaded=loaded+1
                print "   ...done!"
            
            elif className == "LAB-PHD":
                print "   Creating..."
                valueId=insertLabValue(labData, unitName)
                loaded=loaded+1
                print "   ...done!"
            
            elif className == "LAB-LOCAL-VALIDITY":
                print "   Creating..."
                valueId=insertLabValue(labData, unitName)
                localValueId=insertLocalLabValue(valueId)
                insertValidityLimit(labData,valueId)
                loaded=loaded+1
                print "   ...done!"
                
            else:
                skipped=skipped+1
                print "   <<< Unexpected class >>> "

#        success = load(model, userId, interfaceId, interfaceName, tx, log, statusField)
#        if success:
#            loaded = loaded + 1
#        else:
#            error = error + 1
        else:
            alreadyExists=alreadyExists+1
            
    print "Done - Successfully loaded %i lab data objects, %i were skipped, %i already exist." % (loaded, skipped, alreadyExists)

def lookupHDAInterface(interfaceName):
    SQL = "select InterfaceId from LtHDAInterface where InterfaceName = '%s'" % (interfaceName)
    interfaceId = system.db.runScalarQuery(SQL)
    if interfaceId == None:
        SQL = "insert into LtHDAInterface (InterfaceName) values ('%s')" % (interfaceName)
        interfaceId=system.db.runUpdateQuery(SQL, getKey=1)
    return interfaceId


# Insert a record into the main lad data catalog
def insertLabValue(labData, unitName):
    print "      Inserting into LtValue..."
    valueName = labData.get("name")
    description = labData.get("lab-desc")
    displayDecimals = labData.get("lab-display-decimals")
    unitId = getUnitId(unitName)

    SQL = "insert into LtValue (ValueName, Description, DisplayDecimals, UnitId) "\
        " values ('%s', '%s', %s, %s)" % (valueName, description, str(displayDecimals), str(unitId))
    valueId=system.db.runUpdateQuery(SQL, getKey=1)
    print "      ...inserted %s and assigned id %i" % (valueName, valueId)
    return valueId

#
# Insert a record into the main lad data catalog
def insertLocalLabValue(valueId):
    print "      Inserting into LtLocalValue..."
    itemId = labData.get("phd-result-flag-item-id")
    valueName = labData.get("name")
    
    SQL = "insert into LtLocalValue (ValueId) "\
        " values (%s)" % (str(valueId))
    localValueId=system.db.runUpdateQuery(SQL, getKey=1)
    print "      ...assigned id %i" % (localValueId)
    return localValueId


def insertPHDLabValue(labData, valueId):
    print "      Inserting into LtPHDValue..." 
    for rawValue in labData.findall('rawValue'):
        itemId = rawValue.get("item-id")
        interfaceName=rawValue.get("interface-name")
        interfaceId=lookupHDAInterface(interfaceName)

        SQL = "insert into LtPHDValue (ValueId, ItemId, InterfaceId) "\
            " values (%s, '%s', %s)" % (str(valueId), itemId, str(interfaceId))
        system.db.runUpdateQuery(SQL)
        print "      ...inserted a record into LtPHDValue..."
    return valueId

def insertDCSLabValue(labData, valueId, site):
    print "      Inserting into LtPHDValue..." 
    for rawValue in labData.findall('rawValue'):
        itemId = rawValue.get("item-id")
        interfaceName = rawValue.get("interface-name")
        serverName, scanClass, writeLocationId = lookupOPCServerAndScanClass(site, interfaceName)

        SQL = "insert into LtDCSValue (ValueId, ItemId, WriteLocationId) "\
            " values (%s, '%s', %s)" % (str(valueId), itemId, str(writeLocationId))
        system.db.runUpdateQuery(SQL)
        print "      ...inserted a record into LtPHDValue..."
    return valueId

def insertSQCLimit(labData, valueId):
    print "      Inserting a SQC limit..."

    # Each of these for loops should find exactly 1 match
    # The main thing we need to extract is the parameter name - the structure of the recipe database has changed so the upper and lower limit
    # use the same name, so I only need to extract one.  I need to extract the real name from the name in the export by stripping off the
    # _upper and _lower.
    # For the actual limits, these will be overwritten as soon as the first grade change occurs, so they are not terribly important.  
    # The upper and lower limit values are not in the export, so just use the validity limits as the SQC limits for starters.
    for limit in labData.findall('upperValidityLimit'):
        upperValidityLimit = limit.get("value")
    for limit in labData.findall('lowerValidityLimit'):
        lowerValidityLimit = limit.get("value")
    
    # The upper and lower SQC limits may either come from recipe (ODBC) or from the DCS (OPC).  If it comes from recipe, then the upper and 
    # lower limits are both in the same recipe record so only a single parameter name is need, therefore the lower limit isn't even 
    # processed.  If the limit comes from the DCS, the the upper and lower limit have unique item ids.  So look at the upper limit, 
    # determine if it is ODBC or OPC.  If it is OPC then process the lower limit.  
    for upperSQClimit in labData.findall('upperLimit'):
        limitClass = upperSQClimit.get("class")
        if limitClass == "ODBC-LIMIT-FOR-SQC":
            recipeParameterName = upperSQClimit.get("column-qualifier")   

            print "         The recipe parameter name is: ", recipeParameterName
            recipeParameterName=string.upper(recipeParameterName[:recipeParameterName.find('_hilim')])
            print "         ...has been shortened to: ", recipeParameterName
    
            # The SQC limits are not stored in the XML export, they will get loaded from recipe at run time, so for now just use
            # the validity limits in for the SQC
            upperLimit=upperValidityLimit
            lowerLimit=lowerValidityLimit
    
            typeId = lookup("RtLimitType", "SQC")
            sourceId = lookup("RtLimitSource", "Recipe")
            SQL = "insert into LtLimit (ValueId, LimitTypeId, LimitSourceId, UpperValidityLimit, LowerValidityLimit, UpperSQCLimit, LowerSQCLimit, RecipeParameterName) "\
                " values (%s, %s, %s, %s, %s, %s, %s, '%s')" \
                % (str(valueId), str(typeId), str(sourceId), str(upperValidityLimit), str(lowerValidityLimit), str(upperLimit), str(lowerLimit), recipeParameterName)
            system.db.runUpdateQuery(SQL)
            print "      ...inserted a record into LtLimit..."
        elif limitClass == "OPC-FLOAT-BAD-FLAG":
            upperItemId = upperSQClimit.get("item-id")   

            for lowerSQClimit in labData.findall('lowerLimit'):
                lowerItemId = lowerSQClimit.get("item-id")

            print "         The Item-Ids are: %s and %s" % (upperItemId, lowerItemId)
    
            # The SQC limits are not stored in the XML export, they will get loaded from recipe at run time, so for now just use
            # the validity limits in for the SQC
            upperLimit=upperValidityLimit
            lowerLimit=lowerValidityLimit
    
            typeId = lookup("RtLimitType", "SQC")
            sourceId = lookup("RtLimitSource", "DCS")
            SQL = "insert into LtLimit (ValueId, LimitTypeId, LimitSourceId, UpperValidityLimit, LowerValidityLimit, UpperSQCLimit, LowerSQCLimit, OPCUpperItemId, OPCLowerItemId) "\
                " values (%s, %s, %s, %s, %s, %s, %s, '%s', '%s')" \
                % (str(valueId), str(typeId), str(sourceId), str(upperValidityLimit), str(lowerValidityLimit), str(upperLimit), str(lowerLimit), upperItemId, lowerItemId)
            system.db.runUpdateQuery(SQL)
            print "      ...inserted a record into LtLimit..."
        else:
            print "**** Unexpected SQC limit class: <%s> ****" % (limitClass)

#
def insertReleaseLimit(labData, valueId):
    print "      Inserting a release limit..."

    # Each of these for loops should find exactly 1 match.
    # The main thing we need to extract is the parameter name - the structure of the recipe database has changed so the upper and lower limit
    # use the same name, so I only need to extract one.  I need to extract the real name from the name in the export by stripping off the
    # _upper and _lower.
    # For the actual limits, these will be overwritten as soon as the first grade change occurs, so they are not terribly important.  
    # The upper and lower limit values are not in the export, so just use the validity limits as the SQC limits for starters.
    for upperLimit in labData.findall('upperValidityLimit'):
        upperValidityLimit = upperLimit.get("value")
    for lowerLimit in labData.findall('lowerValidityLimit'):
        lowerValidityLimit = lowerLimit.get("value")
    
    # The upper and lower limits may either come from recipe (ODBC) or from the DCS (OPC).  If it comes from recipe, then the upper and 
    # lower limits are both in the same recipe record so only a single parameter name is need, therefore the lower limit isn't even 
    # processed.  If the limit comes from the DCS, the the upper and lower limit have unique item ids.  So look at the upper limit, 
    # determine if it is ODBC or OPC.  If it is OPC then process the lower limit.  

    typeId = lookup("RtLimitType", "Release")
    limitClass = lowerLimit.get("class")
    if limitClass == "ODBC-LIMIT-FOR-SQC":
        recipeParameterName = lowerLimit.get("column-qualifier")   

        print "         The recipe parameter name is: ", recipeParameterName
        recipeParameterName=string.upper(recipeParameterName[:recipeParameterName.find('_llimit')])
        print "         ...has been shortened to: ", recipeParameterName
    
        # The Release limits are not stored in the XML export, they will get loaded from recipe at run time, so just use some absurd constants
        upperLimit=1000.0
        lowerLimit=-1000.0

        sourceId = lookup("RtLimitSource", "Recipe")
        SQL = "insert into LtLimit (ValueId, LimitTypeId, LimitSourceId, UpperReleaseLimit, LowerReleaseLimit, RecipeParameterName) "\
             " values (%s, %s, %s, %s, %s, '%s')" \
             % (str(valueId), str(typeId), str(sourceId), str(upperLimit), str(lowerLimit), recipeParameterName)
        system.db.runUpdateQuery(SQL)
        print "      ...inserted a record into LtLimit..."
    elif limitClass == "OPC-FLOAT-BAD-FLAG":
        upperItemId = upperLimit.get("item-id")
        lowerItemId = lowerLimit.get("item-id")   

        print "         The Item-Ids are: %s and %s" % (upperItemId, lowerItemId)
            
        sourceId = lookup("RtLimitSource", "DCS")
        SQL = "insert into LtLimit (ValueId, LimitTypeId, LimitSourceId, OPCUpperItemId, OPCLowerItemId) "\
               " values (%s, %s, %s, '%s', '%s')" \
                % (str(valueId), str(typeId), str(sourceId), upperItemId, lowerItemId)
        system.db.runUpdateQuery(SQL)
        print "      ...inserted a record into LtLimit..."
    else:
        print "**** Unexpected SQC limit class: <%s> ****" % (limitClass)

#
def insertValidityLimit(labData, valueId):
    print "      Inserting a validity limit..."

    # Each of these for loops should find exactly 1 match.
    # The main thing we need to extract is the parameter name - the structure of the recipe database has changed so the upper and lower limit
    # use the same name, so I only need to extract one.  I need to extract the real name from the name in the export by stripping off the
    # _upper and _lower.
    # For the actual limits, these will be overwritten as soon as the first grade change occurs, so they are not terribly important.  
    # The upper and lower limit values are not in the export, so just use the validity limits as the SQC limits for starters.
    for upperLimit in labData.findall('upperValidityLimit'):
        upperValidityLimit = upperLimit.get("value")
    for lowerLimit in labData.findall('lowerValidityLimit'):
        lowerValidityLimit = lowerLimit.get("value")
    
    # The upper and lower limits may either come from recipe (ODBC), the DCS (OPC), or a constant.  If it comes from recipe, then the upper and 
    # lower limits are both in the same recipe record so only a single parameter name is need, therefore the lower limit isn't even 
    # processed.  If the limit comes from the DCS, the the upper and lower limit have unique item ids.  So look at the upper limit, 
    # determine if it is ODBC or OPC.  If it is OPC then process the lower limit.  

    typeId = lookup("RtLimitType", "Validity")
    limitClass = lowerLimit.get("class")
    if limitClass == "ODBC-LIMIT-FOR-SQC":
        recipeParameterName = lowerLimit.get("column-qualifier")   

        print "         The recipe parameter name is: ", recipeParameterName
        recipeParameterName=string.upper(recipeParameterName[:recipeParameterName.find('_llimit')])
        print "         ...has been shortened to: ", recipeParameterName
    
        # The limit values are not stored in the XML export, they will get loaded from recipe at run time, so just use some absurd constants
        upperLimit=1000.0
        lowerLimit=-1000.0
    
        sourceId = lookup("RtLimitSource", "Recipe")
        SQL = "insert into LtLimit (ValueId, LimitTypeId, LimitSourceId, UpperValidityLimit, LowerValidityLimit, RecipeParameterName) "\
            " values (%s, %s, %s, %s, %s, '%s')" \
            % (str(valueId), str(typeId), str(sourceId), str(upperLimit), str(lowerLimit), recipeParameterName)
        system.db.runUpdateQuery(SQL)
        print "      ...inserted a record into LtLimit..."
    elif limitClass == "OPC-FLOAT-BAD-FLAG":
        upperItemId = upperLimit.get("item-id")
        lowerItemId = lowerLimit.get("item-id")   

        print "         The Item-Ids are: %s and %s" % (upperItemId, lowerItemId)
    
        typeId = lookup("RtLimitType", "Release")
        sourceId = lookup("RtLimitSource", "DCS")
        SQL = "insert into LtLimit (ValueId, LimitTypeId, LimitSourceId, OPCUpperItemId, OPCLowerItemId) "\
            " values (%s, %s, %s, '%s', '%s')" \
            % (str(valueId), str(typeId), str(sourceId), upperItemId, lowerItemId)
        system.db.runUpdateQuery(SQL)
        print "      ...inserted a record into LtLimit..."
    elif limitClass == "FLOAT-PARAMETER":
        upperValue = upperLimit.get("value")
        lowerValue = lowerLimit.get("value")
        sourceId = lookup("RtLimitSource", "Constant")
        SQL = "insert into LtLimit (ValueId, LimitTypeId, LimitSourceId, UpperValidityLimit, LowerValidityLimit) "\
            " values (%s, %s, %s, %s, %s)" \
            % (str(valueId), str(typeId), str(sourceId), str(upperValue), str(lowerValue))
        system.db.runUpdateQuery(SQL)
        print "      ...inserted a record into LtLimit..."
        
    else:
        print "**** Unexpected SQC limit class: <%s> ****" % (limitClass)

def createTags(rootContainer):
    print "In labData.createTags()"

    filename = rootContainer.getComponent('File Field').text
    provider = rootContainer.getComponent("Tag Provider").text
    
    if not(system.file.fileExists(filename)):
        system.gui.errorBox("The import file (" + filename + ") does not exist. Please specify a valid filename.")  
        return

    tree = ET.parse(filename)
    root = tree.getroot()

    loaded = 0
    error = 0
    for labData in root.findall('lab-data'):
        className = labData.get("class")
        labDataName = labData.get("name")
        unitName = labData.get("unit-name")
        print "Processing a %s: %s " % (className, labDataName)
                   
        if className == "LAB-PHD":
            createLabValue(labData, provider, unitName)
            loaded=loaded+1
        elif className == "LAB-PHD-DERIVED":
            createLabValue(labData, provider, unitName)
            loaded=loaded+1
        elif className == "LAB-PHD-SQC":
            createLabValue(labData, provider, unitName)
            createLabLimitSQC(labData, provider, unitName)
            loaded=loaded+1
        elif className == "LAB-PHD-RELEASE":
            createLabValue(labData, provider, unitName)
            createLabLimitRelease(labData, provider, unitName)
            loaded=loaded+1
        elif className == "LAB-PHD-DERIVED-SQC":
            createLabValue(labData, provider, unitName)
            createLabLimitSQC(labData, provider, unitName)
            loaded=loaded+1
            
        elif className == "LAB-PHD-SELECTOR":
            createSelector(labData, 'Lab Data/Lab Selector Value', labDataName, provider, unitName)
            loaded=loaded+1
        elif className == "LAB-PHD-SQC-SELECTOR":
            createSelector(labData, 'Lab Data/Lab Selector Value', labDataName, provider, unitName)
            createSelector(labData, 'Lab Data/Lab Selector Limit SQC', labDataName + '-SQC', provider, unitName)
            loaded=loaded+1
        elif className == "LAB-PHD-VALIDITY-SELECTOR":
            createSelector(labData, 'Lab Data/Lab Selector Value', labDataName, provider, unitName)
            createSelector(labData, 'Lab Data/Lab Selector Limit Validity', labDataName + '-VALIDITY', provider, unitName)
            loaded=loaded+1
        elif className == "LAB-PHD-RELEASE-SELECTOR":
            createSelector(labData, 'Lab Data/Lab Selector Value', labDataName, provider, unitName)
            createSelector(labData, 'Lab Data/Lab Selector Limit Release', labDataName + '-RELEASE', provider, unitName)
            loaded=loaded+1
            
        elif className == "LAB-DCS-SQC":
            createLabValue(labData, provider, unitName)
            createLabLimitSQC(labData, provider, unitName)
            loaded=loaded+1
        elif className == "LAB-LOCAL-VALIDITY":
            createLabValue(labData, provider, unitName)
            createLabLimitValidity(labData, labDataName, provider, unitName)
            loaded=loaded+1
        else:
            print "Unexpected class: ", className
            error=error+1

    print "Done - Successfully created: %i, errors: %i" % (loaded, error)


def createSelector(labData, UDTType, labDataName, provider, unitName):
    path = "LabData/" + unitName + "/"
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", labDataName, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (UDTType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType})

def createLabValue(labData, provider, unitName):    
    UDTType='Lab Data/Lab Value'
    labDataName = labData.get("name")
    path = "LabData/" + unitName + "/"
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", labDataName, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (UDTType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType})

def createLabLimitSQC(labData, provider, unitName):    
    UDTType='Lab Data/Lab Limit SQC'
    labDataName = labData.get("name") + "-SQC"
    path = "LabData/" + unitName + '/'
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", labDataName, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (UDTType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType})

def createLabLimitRelease(labData, provider, unitName):    
    UDTType='Lab Data/Lab Limit Release'
    labDataName = labData.get("name") + "-RELEASE"
    path = "LabData/" + unitName + '/'
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", labDataName, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (UDTType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType})

def createLabLimitValidity(labData, labDataName, provider, unitName):    
    UDTType='Lab Data/Lab Limit Validity'
    labDataName = labDataName + "-VALIDITY"
    path = "LabData/" + unitName + '/'
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", labDataName, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (UDTType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType})

def loadUnitParameters(container):
    print "In labData.loadUnitParameters()"

    #-------------------------------------------------
    def create(unitParameter):    
        
        UDTType='Lab Data/Unit Parameter'
        parameterName = unitParameter.get("name")
        parent = unitParameter.get("parent")
        if parent == "None":
            path = "UnitParameter/"
        else:
            path = "UnitParameter/%s/" % (parent)
            
        print "Creating a Unit Parameter: %s" % (parameterName)
        
        numberOfPoints  = unitParameter.get("numberOfPoints")
        
        provider = "XOM"
        scanClass = "Default"
        
        parentPath = '[' + provider + ']' + path    
        tagPath = parentPath + parameterName
        tagExists = system.tag.exists(tagPath)

        connections=0        
        for connection in unitParameter.findall('connectedTo'):
            sourceTag=connection.get("name")
            connections = connections + 1

        if connections == 0:
            sourceType="Custom"
            sourceTag="Unknown"
        else:
            sourceType="Lab Data"
            
        if tagExists:
            print parameterName, " already exists!"
            pass
        else:
            print "Creating a %s\n  Name: %s\n  Path: %s\n  Scan Class: %s\n  Source Type: %s\n  Source Tag: %s\n" % \
                (UDTType, parameterName, tagPath, scanClass, sourceType, sourceTag)
            system.tag.addTag(parentPath=parentPath, name=parameterName, tagType="UDT_INST", 
                    attributes={"UDTParentType":UDTType}, 
                    parameters={"numberOfPoints":numberOfPoints, "sourceType":sourceType, "sourceTag":sourceTag})
    #-------------------------------------------------------------

    filename = container.getComponent('File Field').text
    
    if not(system.file.fileExists(filename)):
        system.gui.errorBox("The import file (" + filename + ") does not exist. Please specify a valid filename.")  
        return

    
    tree = ET.parse(filename)
    root = tree.getroot()

    loaded = 0
    error = 0
    for unitParam in root.findall('unitParameter'):
        loaded = loaded + 1
        create(unitParam)

    print "Done - Successfully loaded %i SLED models, %i were not loaded due to errors." % (loaded, error)
    