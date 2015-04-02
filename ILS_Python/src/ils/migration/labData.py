'''
Created on Mar 10, 2015

@author: Pete
'''   
# Import the standard Python XML parsing library    
import xml.etree.ElementTree as ET
import sys, system, string, traceback
from ils.migration.common import lookupOPCServerAndScanClass
from ils.diagToolkit.common import fetchConsoleId

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
        consoleId = fetchConsoleId(post)
        displayOrder = table.get("dataOrder")
        displayFlag = table.get("showInList")
        from ils.common.cast import toBit
        displayFlag = toBit(displayFlag)
        displayTableTitle = table.get("description")
        oldTableName = table.get("consoleName")
        displayPage = 1
        
        if consoleId > 0:
            SQL = "select DisplayTableId from LtDisplayTable where DisplayTableTitle = '%s'" % (displayTableTitle)
            displayTableId = system.db.runScalarQuery(SQL)
        
            if displayTableId == None:
                SQL = "insert into LtDisplayTable (DisplayTableTitle, consoleId, DisplayPage, DisplayOrder, DisplayFlag, OldTableName) values " \
                    "('%s', %i, %i, %s, %s, '%s')" % (displayTableTitle, consoleId, displayPage, displayOrder, displayFlag, oldTableName)
                print SQL
                displayTableId = system.db.runUpdateQuery(SQL, getKey=1)
        
            print "%s - %s - %s - %s" % (oldTableName, displayTableTitle, displayFlag, displayOrder)
            for labData in table.findall('labData'):
                labDescription = labData.get("labDescription")
                labDataName = labData.get("labDataName")
                print "     %s - %s" % (labDescription, labDataName)
        else:
            print "Skipping %s because a console was not found for post %s" % (displayTableTitle, post)
            
    print "Done!"
    
def insertIntoDB(rootContainer):
    print "In migration.labData.insertIntoDB()"

    filename = rootContainer.getComponent('File Field').text
    site = rootContainer.getComponent("Site").text
    provider = rootContainer.getComponent("Tag Provider").text
    
    if not(system.file.fileExists(filename)):
        system.gui.errorBox("The import file (" + filename + ") does not exist. Please specify a valid filename.")  
        return
    
    tree = ET.parse(filename)
    root = tree.getroot()

    loaded = 0
    error = 0
    for labData in root.findall('lab-data'):
        print "Processing: ", labData
        className = labData.get("class")
        if className == "LAB-PHD-SQC":
            insertLabValue(labData)
            print "Inserting a LAB-PHD-SQC"
        elif className == "LAB-PHD-DERIVED-SQC":
            print "Inserting a LAB-PHD-DERIVED-SQC"
        elif className == "LAB-PHD":
            print "Inserting a LAB-PHD"
            createLabPhd(labData, site, provider)
        else:
            print "Unexpected class: ", className

#        success = load(model, userId, interfaceId, interfaceName, tx, log, statusField)
#        if success:
#            loaded = loaded + 1
#        else:
#            error = error + 1

    print "Done - Successfully loaded %i SLED models, %i were not loaded due to errors." % (loaded, error)

# This inserts the list of tags and their classes into a special table just for migration that can be edited 
# to indicate instances that are not needed in the new platform.
def insertListIntoMigrationDB(rootContainer):
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
        SQL = "insert into LabData (site, name, class, instantiate) values ('%s', '%s', '%s', 1)" % (site, objectName, className)
        system.db.runUpdateQuery(SQL, database="XOMMigration")
        loaded = loaded + 1

    print "Done - Successfully loaded %i lab data objects." % (loaded)


def deleteListFromMigrationDB(rootContainer):
    print "In migration.labData.insertIntoDB()"

    site = rootContainer.getComponent("Site").text
    
    SQL = "delete from LabData where site = '%s'" % (site)
    rows = system.db.runUpdateQuery(SQL, database="XOMMigration")

    print "Done - Successfully deleted %i lab data objects." % (rows)


def lookupLabConsoleId(consoleName):
    SQL = "select labConsoleId from LtConsoles where ConsoleName = '%s'" % (consoleName)
    consoleId = system.db.runScalarQuery(SQL)
    if consoleId == None:
        SQL = "insert into LtConsoles (ConsoleName) values ('%s')" % (consoleName)
        consoleId=system.db.runUpdateQuery(SQL, getKey=1)
    print "Fetched Console Id: ", consoleId 
    return consoleId


def insertLabValue(labData):
    labValueName = labData.get("name")
    description = labData.get("lab-desc")
    displayDecimals = labData.get("lab-display-decimals")
    labConsole = labData.get("lab-console", "default")
    labConsoleId = lookupLabConsoleId(labConsole)
    post = labData.get("post", "")
#    itemId = ds.getValueAt(row, "item-id")
#    itemId = itemIdPrefix + itemId
#    gsiInterface = labData.get("value-update-flag-interface")
#    serverName, scanClass = lookupOPCServerAndScanClass(site, gsiInterface)

    SQL = "insert into LtLabValue (LabValueName, Description, DisplayDecimals, LabConsoleId, Post) "\
        " values ('%s', '%s', %s, %s, '%s')" % (labValueName, description, str(displayDecimals), str(labConsoleId), post)
    labId=system.db.runUpdateQuery(SQL, getKey=1)
    print "Inserted %s and assigned id %i" % (labValueName, labId)

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
    skipped = 0
    for labData in root.findall('lab-data'):
        className = labData.get("class")
        labDataName = labData.get("name")
        print "Processing a %s: %s " % (className, labDataName)
        
        SQL = "select instantiate from LabData where site = '%s' and name = '%s'" % (site, labDataName)
        instantiate = system.db.runScalarQuery(SQL, database="XOMMigration")

        if instantiate:
            
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
                createLabPhd(labData, site, provider)
                loaded=loaded+1
            elif className == "LAB-PHD-SQC-SELECTOR":
                createLabPhd(labData, site, provider)
                createLabLimitSQC(labData, site, provider)
                loaded=loaded+1
            elif className == "LAB-PHD-VALIDITY-SELECTOR":
                createLabPhd(labData, site, provider)
                createLabLimitValidity(labData, site, provider)
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
        else:
            skipped=skipped+1
            print "  Skipping because this has been marked as do not instantiate"

    print "Done - Successfully loaded: %i, skipped: %i, errors: %i" % (loaded, skipped, error)


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
