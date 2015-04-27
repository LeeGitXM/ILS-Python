'''
Created on Mar 10, 2015

@author: Pete
'''   
# Import the standard Python XML parsing library    
import xml.etree.ElementTree as ET
import sys, system, string, traceback
from ils.migration.common import lookupOPCServerAndScanClass
from ils.common.database import getPostId

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
def insertIntoDB(rootContainer):
    print "In migration.labData.insertIntoDB()"

    filename = rootContainer.getComponent('File Field').text
    provider = rootContainer.getComponent("Tag Provider").text
    
    if not(system.file.fileExists(filename)):
        system.gui.errorBox("The import file (" + filename + ") does not exist. Please specify a valid filename.")  
        return
    
    tree = ET.parse(filename)
    root = tree.getroot()

    loaded = 0
    skipped = 0
    error = 0
    for labData in root.findall('lab-data'):
        name=labData.get("name")
        className = labData.get("class")
        print "Processing %s, a %s" % (name, className)
        
        if className == "LAB-PHD-SQC":
            print "   ** Created **"
            valueId=insertLabValue(labData)
            insertPHDLabValue(labData, valueId)
            loaded=loaded+1
            
        elif className == "LAB-PHD-SQC-SELECTOR":
            print "   ** Created **"
            valueId=insertLabValue(labData)
            loaded=loaded+1
            
#        elif className == "LAB-PHD-DERIVED-SQC":
#            print "   ...skipping..."
#        elif className == "LAB-PHD":
#            print "   ...skipping..."
#            createLabPhd(labData, site, provider)
        else:
            skipped=skipped+1
            print "   <<< Unexpected class >>> "

#        success = load(model, userId, interfaceId, interfaceName, tx, log, statusField)
#        if success:
#            loaded = loaded + 1
#        else:
#            error = error + 1

    print "Done - Successfully loaded %i lab data objects, %i were skipped." % (loaded, skipped)

def lookupHDAInterface(interfaceName):
    SQL = "select InterfaceId from LtHDAInterface where InterfaceName = '%s'" % (interfaceName)
    interfaceId = system.db.runScalarQuery(SQL)
    if interfaceId == None:
        SQL = "insert into LtHDAInterface (InterfaceName) values ('%s')" % (interfaceName)
        interfaceId=system.db.runUpdateQuery(SQL, getKey=1)
    return interfaceId


# The display table Has been so to allow NULL so that we can insert the lab data from this export file.  The display table
# info is contained in the display table export and will be updated later
def insertLabValue(labData):
    valueName = labData.get("name")
    description = labData.get("lab-desc")
    displayDecimals = labData.get("lab-display-decimals")
    post = labData.get("post", "")
    postId = getPostId(post)
    print "Post: %s has idL %i" % (post, postId)

    SQL = "insert into LtValue (ValueName, Description, DisplayDecimals, PostId) "\
        " values ('%s', '%s', %s, %s)" % (valueName, description, str(displayDecimals), str(postId))
    print SQL
    valueId=system.db.runUpdateQuery(SQL, getKey=1)
    print "Inserted %s and assigned id %i" % (valueName, valueId)
    return valueId


def insertPHDLabValue(labData, valueId):    
    for rawValue in labData.findall('rawValue'):
        itemId = rawValue.get("item-id")
        interfaceName=rawValue.get("interface-name")
        interfaceId=lookupHDAInterface(interfaceName)

        SQL = "insert into LtPHDValue (ValueId, ItemId, InterfaceId) "\
            " values (%s, '%s', %s)" % (str(valueId), itemId, str(interfaceId))
        print SQL
        system.db.runUpdateQuery(SQL)
        print "  inserted a record into LtPHDValue..."
    return valueId



def createTags(rootContainer):
    print "In labData.createTags()"

    filename = rootContainer.getComponent('File Field').text
    site = rootContainer.getComponent("Site").text
    provider = rootContainer.getComponent("Tag Provider").text
    
    if not(system.file.fileExists(filename)):
        system.gui.errorBox("The import file (" + filename + ") does not exist. Please specify a valid filename.")  
        return

    # Import the standard Python XML parsing library    
    import xml.etree.ElementTree as ET
    tree = ET.parse(filename)
    root = tree.getroot()

    loaded = 0
    error = 0
    for labData in root.findall('lab-data'):
        className = labData.get("class")
        labDataName = labData.get("name")
        print "Processing a %s: %s " % (className, labDataName)
                   
        if className == "LAB-PHD":
            createLabPhd(labData, site, provider)
            loaded=loaded+1
        elif className == "LAB-PHD-DERIVED":
            createLabPhd(labData, site, provider)
            loaded=loaded+1
        elif className == "LAB-PHD-SQC":
            createLabPhd(labData, site, provider)
            createLabLimitSQC(labData, site, provider)
            loaded=loaded+1
        elif className == "LAB-PHD-RELEASE":
            createLabPhd(labData, site, provider)
            createLabLimitRelease(labData, site, provider)
            loaded=loaded+1
        elif className == "LAB-PHD-DERIVED-SQC":
            createLabPhd(labData, site, provider)
            createLabLimitSQC(labData, site, provider)
            loaded=loaded+1
            
        elif className == "LAB-PHD-SELECTOR":
            createSelector(labData, 'Lab Data/Lab Selector Value', labDataName, site, provider)
            loaded=loaded+1
        elif className == "LAB-PHD-SQC-SELECTOR":
            createSelector(labData, 'Lab Data/Lab Selector Value', labDataName, site, provider)
            createSelector(labData, 'Lab Data/Lab Selector SQC', labDataName + '-SQC', site, provider)
            loaded=loaded+1
        elif className == "LAB-PHD-VALIDITY-SELECTOR":
            createSelector(labData, 'Lab Data/Lab Selector Value', labDataName, site, provider)
            createSelector(labData, 'Lab Data/Lab Selector Validity', labDataName + '-VALIDITY', site, provider)
            loaded=loaded+1
            
        elif className == "LAB-DCS-SQC":
            createLabDCS(labData, site, provider)
            createLabLimitSQC(labData, site, provider)
            loaded=loaded+1
        elif className == "LAB-LOCAL-VALIDITY":
            createLabLocal(labData, site, provider)
            createLabLimitValidity(labData, site, provider)
            loaded=loaded+1
        else:
            print "Unexpected class: ", className
            error=error+1

    print "Done - Successfully created: %i, errors: %i" % (loaded, error)


def createSelector(labData, UDTType, labDataName, site, provider):    
    path = "LabData/"    
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", labDataName, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (UDTType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType})

def createLabPhd(labData, site, provider):    
    UDTType='Lab Data/Lab Value PHD'
    labDataName = labData.get("name")
    path = "LabData/"    
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", labDataName, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (UDTType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType})

def createLabLocal(labData, site, provider):    
    UDTType='Lab Data/Lab Value Local'
    labDataName = labData.get("name")
    path = "LabData/"    
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", labDataName, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (UDTType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType})

def createLabDCS(labData, site, provider):
    UDTType='Lab Data/Lab Value DCS'
    labDataName = labData.get("name")
    path = "LabData/"    
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", labDataName, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (UDTType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType})

def createLabLimitSQC(labData, site, provider):    
    UDTType='Lab Data/Lab Limit SQC'
    labDataName = labData.get("name") + "-SQC"
    path = "LabData/"    
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", labDataName, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (UDTType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType})

def createLabLimitRelease(labData, site, provider):    
    UDTType='Lab Data/Lab Limit Release'
    labDataName = labData.get("name") + "-RELEASE"
    path = "LabData/"    
    parentPath = '[' + provider + ']' + path    
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", labDataName, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (UDTType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
            attributes={"UDTParentType":UDTType})

def createLabLimitValidity(labData, site, provider):    
    UDTType='Lab Data/Lab Limit Validity'
    labDataName = labData.get("name") + "-VALIDITY"
    path = "LabData/"    
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
        
        print "Creating a Unit Parameter: %s" % (parameterName)
        
        numberOfPoints  = unitParameter.get("numberOfPoints")
        path = "UnitParameter/"
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

    # Import the standard Python XML parsing library    
    import xml.etree.ElementTree as ET
    tree = ET.parse(filename)
    root = tree.getroot()

    loaded = 0
    error = 0
    for unitParam in root.findall('unitParameter'):
        loaded = loaded + 1
        create(unitParam)

    print "Done - Successfully loaded %i SLED models, %i were not loaded due to errors." % (loaded, error)
    
#
 
# This inserts the list of tags and their classes into a special table just for migration that can be edited 
# to indicate instances that are not needed in the new platform.
def CRAPinsertListIntoMigrationDB(rootContainer):
    print "In migration.labData.insertIntoDB()"

    filename = rootContainer.getComponent('File Field').text
    site = rootContainer.getComponent("Site").text
    
    if not(system.file.fileExists(filename)):
        system.gui.errorBox("The import file (" + filename + ") does not exist. Please specify a valid filename.")  
        return
    
    tree = ET.parse(filename)
    root = tree.getroot()

    loaded = 0
    for labData in root.findall('lab-data'):
        className = labData.get("class")
        objectName = labData.get("name")
        try:
            SQL = "insert into LabData (site, name, class, instantiate) values ('%s', '%s', '%s', 1)" % (site, objectName, className)
            system.db.runUpdateQuery(SQL, database="XOMMigration")
        except:
            print "%s already exists..." % (objectName)
        else:
            print "created %s" % (objectName)
            loaded = loaded + 1

    print "Done - Successfully loaded %i lab data objects." % (loaded)


def CRAPdeleteListFromMigrationDB(rootContainer):
    print "In migration.labData.insertIntoDB()"

    site = rootContainer.getComponent("Site").text
    
    SQL = "delete from LabData where site = '%s'" % (site)
    rows = system.db.runUpdateQuery(SQL, database="XOMMigration")

    print "Done - Successfully deleted %i lab data objects." % (rows)
