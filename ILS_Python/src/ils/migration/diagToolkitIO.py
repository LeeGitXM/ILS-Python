'''
Created on Feb 5, 2015

@author: Pete
'''
import sys, system, string, traceback
from ils.migration.common import lookupOPCServerAndScanClass

def load(rootContainer):
    filename=rootContainer.getComponent("File Field").text
    if not(system.file.fileExists(filename)):
        system.gui.messageBox("Yes, the file exists")
        return
    
    contents = system.file.readFileAsString(filename, "US-ASCII")
    records = contents.split('\n')
    
    ds=parseRecords(records,"INTERFACE")
    table=rootContainer.getComponent("Interface Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"APPLICATION")
    table=rootContainer.getComponent("Application Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"FAMILY")
    table=rootContainer.getComponent("Family Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"FINAL-DIAGNOSIS")
    table=rootContainer.getComponent("Final Diagnosis Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"QUANT-OUTPUT")
    table=rootContainer.getComponent("Quant Output Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"QUANT-RECOMMENDATION-DEF")
    table=rootContainer.getComponent("Quant Recommendation Def Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"OPC-FLOAT-OUTPUT")
    table=rootContainer.getComponent("Float Output Container").getComponent("Power Table")
    table.data=ds

    ds=parseRecords(records,"OPC-TEXT-COND-CNTRL-ACE-OUTPUT")
    table=rootContainer.getComponent("Text Cond Cntrl ACE Output Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"OPC-TEXT-COND-CNTRL-PKS-OUTPUT")
    table=rootContainer.getComponent("Text Cond Cntrl PKS Output Container").getComponent("Power Table")
    table.data=ds
        
    print "Done Loading!"

def parseRecords(records,recordType):        
    print "Parsing %s records... " % (recordType)
    i = 0
    numTokens=100
    data = []    
    for line in records:
        line=line[:len(line)-1] #Strip off the last character which is some sort of CRLF
        tokens = line.split(',')
        if string.upper(tokens[0]) == recordType:
            if (i == 0):
                line=line.rstrip(',')
                line="id,%s" % (line)
                header = line.split(',')
                numTokens=len(header)
            else:
                line="-1,%s" % (line)
                tokens = line.split(',')
                data.append(tokens[:numTokens])
            i = i + 1

    print "Header: ", header
    print "Data: ", data
        
    ds = system.dataset.toDataSet(header, data)
    print "   ...parsed %i %s records!" % (len(data), recordType)
    return ds

def initializeApplication(container):
    SQL="delete from DtApplication"
    rows=system.db.runUpdateQuery(SQL)
    print "Delete %i rows from DtApplication" % (rows)

def initializeFamily(container):
    SQL="delete from DtFamily"
    rows=system.db.runUpdateQuery(SQL)
    print "Delete %i rows from DtFamily" % (rows)
    
def initializeFinalDiagnosis(container):
    SQL="delete from DtDiagnosisEntry"
    rows=system.db.runUpdateQuery(SQL)
    print "Delete %i rows from DtDiagnosisEntry" % (rows)
    
    SQL="delete from DtFinalDiagnosis"
    rows=system.db.runUpdateQuery(SQL)
    print "Delete %i rows from DtFinalDiagnosis" % (rows)    
    
def initializeQuantOutput(container):
    SQL="delete from DtQuantOutput"
    rows=system.db.runUpdateQuery(SQL)
    print "Delete %i rows from DtQuantOutput" % (rows)

def initializeRecommendationDefinition(container):
    SQL="delete from DtRecommendation"
    rows=system.db.runUpdateQuery(SQL)
    print "Delete %i rows from DtRecommendation" % (rows)

    SQL="delete from DtRecommendationDefinition"
    rows=system.db.runUpdateQuery(SQL)
    print "Delete %i rows from DtRecommendationDefinition" % (rows)
    
    
    
def insertApplication(container):
    table=container.getComponent("Power Table")
    ds=table.data
    try:
        tx=system.db.beginTransaction()
        for row in range(ds.rowCount):
            application = ds.getValueAt(row, 4) #There are two columns named application so use idx here
            unit = ds.getValueAt(row, "unit")
            post = ds.getValueAt(row, "post")
            messageQueue = ds.getValueAt(row, "msg-queue-name")
            includeInMainMenu = ds.getValueAt(row, "include-in-main-menu")
            if includeInMainMenu == "TRUE":
                includeInMainMenu=1
            else:
                includeInMainMenu=0
            groupRampMethod = ds.getValueAt(row, "group-ramp-method")
            
            from ils.diagToolkit.common import fetchConsoleId
            consoleId = fetchConsoleId(post)
    
            if consoleId >= 0:
                SQL = "insert into DtApplication (Application, ConsoleId, MessageQueue, IncludeInMainMenu, "\
                    "GroupRampMethod) values ('%s', %i, '%s', %i, '%s')" % \
                    (application, consoleId, messageQueue, includeInMainMenu, groupRampMethod)
                applicationId=system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
                ds=system.dataset.setValue(ds, row, "id", applicationId) 
                print "Insert %s and got id: %i" % (application, applicationId)                                                         
            else:
                print "Could not find console: <%s>" % (unit)

    except:
        print "Caught an error - rolling back transactions!"
        system.db.rollbackTransaction(tx)
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 500)
        print errorTxt

    else:
        print "Committing!"
        system.db.commitTransaction(tx)
        table.data=ds

    system.db.closeTransaction(tx)

# We can't use the database to do this because the export contains the G2 name, but we inserted the 
# "application" attribute as the name of the application in the new platform
def getApplicationId(rootContainer, application):
    applicationId = -1
    ds=rootContainer.getComponent("Application Container").getComponent("Power Table").data
    for row in range(ds.rowCount):
        if ds.getValueAt(row, "name") == application:
            return ds.getValueAt(row, "id")
    return applicationId

# We could use the database to do this, but since we have everything here in the table, I can just look it up. 
def getApplicationName(rootContainer, oldApplicationName):
    applicationName = ""
    ds=rootContainer.getComponent("Application Container").getComponent("Power Table").data
    for row in range(ds.rowCount):
        if ds.getValueAt(row, "name") == oldApplicationName:
            return ds.getValueAt(row, 4)
    return applicationName

#
def insertFamily(container):
    rootContainer=container.parent
    table=container.getComponent("Power Table")
    ds=table.data
    try:
        tx=system.db.beginTransaction()
        for row in range(ds.rowCount):
            application = ds.getValueAt(row, "Application")
            family = ds.getValueAt(row, "label")  # Use the label as the name
            description = ds.getValueAt(row, "description")
            priority = ds.getValueAt(row, "priority")

            applicationId=getApplicationId(rootContainer, application)
            if applicationId >= 0:
                SQL = "insert into DtFamily (Family, ApplicationId, FamilyPriority, Description) "\
                    "values ('%s', %s, %s, '%s')" % \
                    (family, str(applicationId), str(priority), description)
                print SQL
                familyId=system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
                ds=system.dataset.setValue(ds, row, "id", familyId) 
                print "Insert %s and got id: %i" % (family, familyId)                                                         
            else:
                print "Could not find application: <%s>" % (application)

    except:
        print "Caught an error - rolling back transactions!"
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 500)
        print errorTxt
        system.db.rollbackTransaction(tx)

    else:
        print "Committing!"
        system.db.commitTransaction(tx)
        table.data=ds

    system.db.closeTransaction(tx)


# We can't use the database to do this because the export contains the G2 name, but we inserted the 
# "label" attribute as the name of the family in the new platform
def getFamilyId(rootContainer, family):
    familyId = -1
    ds=rootContainer.getComponent("Family Container").getComponent("Power Table").data
    for row in range(ds.rowCount):
        if ds.getValueAt(row, "name") == family:
            return ds.getValueAt(row, "id")
    return familyId


def insertFinalDiagnosis(container):
    rootContainer=container.parent
    table=container.getComponent("Power Table")
    ds=table.data

    for row in range(ds.rowCount):
        family=ds.getValueAt(row, "family")
        finalDiagnosis=ds.getValueAt(row, "label")    # Use the label as the new name
        explanation=ds.getValueAt(row, "explanation")
        priority=ds.getValueAt(row, "priority")
        calculationMethod=ds.getValueAt(row, "recommendation-calculation-method")
        trapInsignificantRecommendations=ds.getValueAt(row, "trap-insignificant-recommendation-conditions")
        if trapInsignificantRecommendations == "TRUE":
            trapInsignificantRecommendations=1
        else:
            trapInsignificantRecommendations=0
        postTextRecommendation=ds.getValueAt(row, "post-text-recommendation")
        if postTextRecommendation == "TRUE":
            postTextRecommendation=1
        else:
            postTextRecommendation=0
        textRecommendation=ds.getValueAt(row, "text-recommendation")
        textRecommendationCallback=ds.getValueAt(row, "text-recommendation-callback")
        refreshRate=ds.getValueAt(row, "recommendation-refresh-rate-in-minutes")
            
        familyId=getFamilyId(rootContainer, family)
            
        if familyId >= 0:
            SQL = "insert into DtFinalDiagnosis (FinalDiagnosis, FamilyId, Explanation, "\
                "FinalDiagnosisPriority, CalculationMethod, TrapInsignificantRecommendations, "\
                "PostTextRecommendation, TextRecommendation, TextRecommendationCallback, RefreshRate) "\
                "values ('%s', %s, '%s', %s, '%s', %s, %s, '%s', '%s', %s)" % \
                 (finalDiagnosis, str(familyId), explanation, str(priority), calculationMethod, 
                 trapInsignificantRecommendations, postTextRecommendation, textRecommendation,
                 textRecommendationCallback, refreshRate)
            print SQL
            familyId=system.db.runUpdateQuery(SQL, getKey=True)
            ds=system.dataset.setValue(ds, row, "id", familyId) 
            print "Insert %s and got id: %i" % (family, familyId)                                                         
        else:
            print "Could not find family: <%s>" % (family)

    table.data=ds


def insertQuantOutput(container):
    rootContainer=container.parent
    table=container.getComponent("Power Table")
    ds=table.data

    for row in range(ds.rowCount):
        application = ds.getValueAt(row, "application")
        quantOutput = ds.getValueAt(row, 3)
        mostNegativeIncrement = ds.getValueAt(row, "most-negative-increment")
        mostPositiveIncrement = ds.getValueAt(row, "most-positive-increment")
        minimumIncrement = ds.getValueAt(row, "minimum-increment")
        setpointHighLimit = ds.getValueAt(row, "setpoint-high-limit")
        setpointLowLimit = ds.getValueAt(row, "setpoint-low-limit")
        incrementalOutput = ds.getValueAt(row, "incremental-output")
        if incrementalOutput == "TRUE":
            incrementalOutput=1
        else:
            incrementalOutput=0
        feedbackMethod = ds.getValueAt(row, "feedback-method")
        tagPath = ds.getValueAt(row, "connected-output-name")
    
        applicationId=getApplicationId(rootContainer, application)
        if applicationId >= 0:
            SQL = "insert into DtQuantOutput (QuantOutput, ApplicationId, TagPath, MostNegativeIncrement, \
                MostPositiveIncrement, MinimumIncrement, SetpointHighLimit, \
                SetpointLowLimit, FeedbackMethod, IncrementalOutput) "\
                "values ('%s', %s, '%s', %s, %s, %s, %s, %s, '%s', %s)" % \
                (quantOutput, str(applicationId), tagPath, str(mostNegativeIncrement), 
                str(mostPositiveIncrement), str(minimumIncrement), str(setpointHighLimit),
                str(setpointLowLimit), feedbackMethod, str(incrementalOutput))
            print SQL
            Id=system.db.runUpdateQuery(SQL, getKey=True)
            ds=system.dataset.setValue(ds, row, "id", Id) 
            print "Insert %s and got id: %i" % (quantOutput, Id)                                                         
        else:
            print "Could not find application: <%s>" % (application)

    table.data=ds



def createFloatOutput(container):
    rootContainer=container.parent
    table=container.getComponent("Power Table")
    ds=table.data
    UDTType='Basic IO/OPC Output'
    site = rootContainer.getComponent("Site").text
    provider = rootContainer.getComponent("Tag Provider").text
    itemIdPrefix = system.tag.read("[" + provider + "]Configuration/DiagnosticToolkit/itemIdPrefix").value

    for row in range(ds.rowCount):
#        oldApplicationName = ds.getValueAt(row, "application")
        oldApplicationName = ds.getValueAt(row, 2)
        application = getApplicationName(rootContainer, oldApplicationName)
        outputName = ds.getValueAt(row, "name")
        names = ds.getValueAt(row, "names")
        itemId = ds.getValueAt(row, "item-id")
        itemId = itemIdPrefix + itemId
        gsiInterface = ds.getValueAt(row, "opc-server")
        serverName, scanClass = lookupOPCServerAndScanClass(site, gsiInterface)
        path = "DiagnosticToolkit/" + application
        
        print application, outputName, itemId, serverName
        
        parentPath = '[' + provider + ']' + path    
        tagPath = parentPath + "/" + outputName
        tagExists = system.tag.exists(tagPath)
    
        if tagExists:
#        print tagName, " already exists!"
            pass
        else:
            print "Creating a %s, Name: %s, Path: %s, Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, tagPath, itemId, scanClass, serverName)
            system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
                    attributes={"UDTParentType":UDTType}, 
                    parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "alternateNames": names})


def createPKSController(container):
    rootContainer=container.parent
    table=container.getComponent("Power Table")
    ds=table.data
    UDTType='Controllers/PKS Controller'
    site = rootContainer.getComponent("Site").text
    provider = rootContainer.getComponent("Tag Provider").text
    itemIdPrefix = system.tag.read("[" + provider + "]Configuration/DiagnosticToolkit/itemIdPrefix").value

    for row in range(ds.rowCount):
        oldApplicationName = ds.getValueAt(row, 2)
        application = getApplicationName(rootContainer, oldApplicationName)
        outputName = ds.getValueAt(row, "name")
        names = ds.getValueAt(row, "names")

        # For Vistalon diagnostic, the controllers are not configured for a PV because we are just writing, 
        # nobody cares what the inputs are.
        itemId=""
        opItemId=""
        spItemId = itemIdPrefix + ds.getValueAt(row, "item-id")
        
        permissiveItemId = itemIdPrefix + ds.getValueAt(row, "permissive-item-id")
        highClampItemId = itemIdPrefix + ds.getValueAt(row, "high-clamp-item-id")
        lowClampItemId = itemIdPrefix + ds.getValueAt(row, "low-clamp-item-id")
        windupItemId = itemIdPrefix + ds.getValueAt(row, "windup-item-id")
        modeItemId = itemIdPrefix + ds.getValueAt(row, "mode-item-id")

        gsiInterface = ds.getValueAt(row, "opc-server")
        serverName, scanClass = lookupOPCServerAndScanClass(site, gsiInterface)
        path = "DiagnosticToolkit/" + application
        
        parentPath = '[' + provider + ']' + path    
        tagPath = parentPath + "/" + outputName
        tagExists = system.tag.exists(tagPath)
    
        if not(tagExists):
            print "Creating a %s, Name: %s, Path: %s, SP Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, tagPath, spItemId, scanClass, serverName)
            # Because this generic controller definition is being used by the Diagnostic Toolkit it does not use the PV and OP attributes.  
            # There are OPC tags and just to make sure we don't wreak havoc with the OPC server, these should be disabled
            system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
                        attributes={"UDTParentType":UDTType}, 
                        parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "spItemId":spItemId,
                                "opItemId":opItemId, "modeItemId":modeItemId,
                                "highClampItemId": highClampItemId, "lowClampItemId":lowClampItemId, "windupItemId":windupItemId,
                                "alternateNames": names},
                        overrides={"value": {"Enabled":"false"}, "op": {"Enabled":"false"}})
            

def createPKSACEController(container):
    rootContainer=container.parent
    table=container.getComponent("Power Table")
    ds=table.data
    UDTType='Controllers/PKS ACE Controller'
    site = rootContainer.getComponent("Site").text
    provider = rootContainer.getComponent("Tag Provider").text
    itemIdPrefix = system.tag.read("[" + provider + "]Configuration/DiagnosticToolkit/itemIdPrefix").value

    for row in range(ds.rowCount):
        oldApplicationName = ds.getValueAt(row, 2)
        application = getApplicationName(rootContainer, oldApplicationName)
        outputName = ds.getValueAt(row, "name")
        names = ds.getValueAt(row, "names")

        # For Vistalon diagnostic, the controllers are not configured for a PV because we are just writing, 
        # nobody cares what the inputs are.
        itemId=""
        opItemId=""
        spItemId = itemIdPrefix + ds.getValueAt(row, "item-id")
        
        permissiveItemId = itemIdPrefix + ds.getValueAt(row, "permissive-item-id")
        highClampItemId = itemIdPrefix + ds.getValueAt(row, "high-clamp-item-id")
        lowClampItemId = itemIdPrefix + ds.getValueAt(row, "low-clamp-item-id")
        windupItemId = itemIdPrefix + ds.getValueAt(row, "windup-item-id")
        modeItemId = itemIdPrefix + ds.getValueAt(row, "mode-item-id")
        processingCommandItemId = itemIdPrefix + ds.getValueAt(row, "processing-cmd-item-id")
        
        gsiInterface = ds.getValueAt(row, "opc-server")
        serverName, scanClass = lookupOPCServerAndScanClass(site, gsiInterface)
        path = "DiagnosticToolkit/" + application
       
        parentPath = '[' + provider + ']' + path    
        tagPath = parentPath + "/" + outputName
        tagExists = system.tag.exists(tagPath)

        if not(tagExists):
            print "Creating a %s, Name: %s, Path: %s, SP Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, tagPath, spItemId, scanClass, serverName)
            system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
                        attributes={"UDTParentType":UDTType}, 
                        parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "spItemId":spItemId,
                            "opItemId":opItemId, "modeItemId":modeItemId, 
                            "highClampItemId": highClampItemId, "lowClampItemId":lowClampItemId, "windupItemId":windupItemId, 
                            "processingCommandItemId": processingCommandItemId, "alternateNames": names},
                        overrides={"value": {"Enabled":"false"}, "op": {"Enabled":"false"}})


# We could probably use the database for this lookup, but let's just follow the pattern
def getQuantOutputId(rootContainer, quantOutput):
    Id = -1
    ds=rootContainer.getComponent("Quant Output Container").getComponent("Power Table").data
    for row in range(ds.rowCount):
        if ds.getValueAt(row, 3) == quantOutput:
            return ds.getValueAt(row, "id")
    return Id

# We could probably use the database for this lookup, but let's just follow the pattern
def getFinalDiagnosisId(rootContainer, finalDiagnosis):
    Id = -1
    ds=rootContainer.getComponent("Final Diagnosis Container").getComponent("Power Table").data
    for row in range(ds.rowCount):
        if ds.getValueAt(row, 4) == finalDiagnosis:
            return ds.getValueAt(row, "id")
    return Id

def insertRecommendationDefinition(container):
    rootContainer=container.parent
    table=container.getComponent("Power Table")
    ds=table.data

    for row in range(ds.rowCount):
        quantOutput = ds.getValueAt(row, "quant-output")
        finalDiagnosis = ds.getValueAt(row, "final-diagnosis")
    
        quantOutputId=getQuantOutputId(rootContainer, quantOutput)
        finalDiagnosisId=getFinalDiagnosisId(rootContainer, finalDiagnosis)
        if quantOutputId < 0:
            print "Could not find Quant Output: <%s>" % (quantOutput)
        elif finalDiagnosisId < 0:
            print "Could not find Final Diagnosis: <%s>" % (finalDiagnosis)
        else:
            SQL = "insert into DtRecommendationDefinition (FinalDiagnosisId, QuantOutputId) values (%s, %s)" % \
                (str(finalDiagnosisId), str(quantOutputId))
            print SQL
            Id=system.db.runUpdateQuery(SQL, getKey=True)
            ds=system.dataset.setValue(ds, row, "id", Id) 
            print "Insert %s - %s and got id: %i" % (finalDiagnosis, quantOutput, Id)                                                         

    table.data=ds

    