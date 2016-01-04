'''
Created on Feb 5, 2015

@author: Pete
'''
import sys, system, string, traceback
from ils.migration.common import lookupOPCServerAndScanClass
from ils.migration.common import lookupMessageQueue
from ils.common.database import lookup
#from xom.extensions import family

def load(rootContainer, stripGDA):
    filename=rootContainer.getComponent("File Field").text
    if not(system.file.fileExists(filename)):
        system.gui.messageBox("Error - the requested file does not exist!")
        return
    
    print "Stripping: ", stripGDA
    
    contents = system.file.readFileAsString(filename, "US-ASCII")
    records = contents.split('\n')
    
    ds=parseRecords(records,"INTERFACE", stripGDA)
    table=rootContainer.getComponent("Interface Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"APPLICATION", stripGDA)
    table=rootContainer.getComponent("Application Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"FAMILY", stripGDA)
    table=rootContainer.getComponent("Family Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"FINAL-DIAGNOSIS", stripGDA)
    ds=morphCalculationMethodName(rootContainer, ds)
    table=rootContainer.getComponent("Final Diagnosis Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"SQC-DIAGNOSIS", stripGDA)
    table=rootContainer.getComponent("SQC Diagnosis Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"QUANT-OUTPUT", stripGDA)
    table=rootContainer.getComponent("Quant Output Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"QUANT-RECOMMENDATION-DEF", stripGDA)
    table=rootContainer.getComponent("Quant Recommendation Def Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"OPC-FLOAT-OUTPUT", stripGDA)
    table=rootContainer.getComponent("Float Output Container").getComponent("Power Table")
    table.data=ds

    ds=parseRecords(records,"OPC-TEXT-COND-CNTRL-ACE-OUTPUT", stripGDA)
    table=rootContainer.getComponent("Text Cond Cntrl ACE Output Container").getComponent("Power Table")
    table.data=ds
    
    ds=parseRecords(records,"OPC-TEXT-COND-CNTRL-PKS-OUTPUT", stripGDA)
    table=rootContainer.getComponent("Text Cond Cntrl PKS Output Container").getComponent("Power Table")
    table.data=ds
        
    print "Done Loading!"

def parseRecords(records, recordType, stripGDA=True):
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
                
                if recordType == 'FINAL-DIAGNOSIS':
                    header.append('new-recommendation-calculation-method')
                
                numTokens=len(header)
                print "Header: ", header
            else:
                line="-1,%s" % (line)
                tokens = line.split(',')
                if stripGDA:
                    tokens = stripTokens(tokens)
                
                if recordType == 'APPLICATION':
                    tokens[2]=changeCase(tokens[2])
                elif recordType == 'FAMILY':
                    tokens[2]=changeCase(tokens[2])
                    tokens[3]=changeCase(tokens[3])
                elif recordType == 'FINAL-DIAGNOSIS':
                    tokens[2]=changeCase(tokens[2])
                    tokens[3]=changeCase(tokens[3])
                    tokens[4]=changeCase(tokens[4])
                    
                    # Copy the calculation method to the end - we are going to morph this name
                    tokens.append(tokens[8])
                elif recordType == 'SQC-DIAGNOSIS':
                    tokens[2]=changeCase(tokens[2])
                    tokens[3]=changeCase(tokens[3])
                    tokens[4]=changeCase(tokens[4])
                elif recordType == 'QUANT-OUTPUT':
                    tokens[2]=changeCase(tokens[2])
                elif recordType == 'QUANT-RECOMMENDATION-DEF':
                    tokens[2]=changeCase(tokens[2])
                    tokens[6]=changeCase(tokens[6])

                data.append(tokens[:numTokens])
            i = i + 1

    print "Data: ", data
    
    ds = system.dataset.toDataSet(header, data)
    print "   ...parsed %i %s records!" % (len(data), recordType)
    return ds

def morphCalculationMethodName(rootContainer, ds):
    #-----------------------------------------
    def mapApplication(oldName):
        oldName = string.upper(oldName)
        
        #
        # Vistalon Applications
        #
        
        if oldName == 'CSTRPRODUCTQUALITY':
            newName = "cstr"
        elif oldName == 'CRXPRODUCTQUALITY':
            newName = 'crx'
        elif oldName == 'VFUPRODUCTQUALITY':
            newName = 'vfu'
        elif oldName == 'POLYRATECHANGESYSTEM':
            newName = 'rateChange'
        elif oldName == 'POLYFLYINGSWITCHSYSTEM':
            newName = 'flyingSwitch'

        #
        # Put next application here
        #
        
        else:
            print "Mapping not found for application: ", oldName
            newName = oldName
        return newName
    #-------------------------------------------
    calculationMethodRoot=rootContainer.getComponent("Calculation Method Root Field").text

    for row in range(ds.rowCount):
        application=ds.getValueAt(row, "application")
        applicationNickName=mapApplication(application)
        
        oldCalculationMethod=ds.getValueAt(row, "recommendation-calculation-method")
        if string.upper(oldCalculationMethod) == 'CONSTANT':
            newCalculationMethod='CONSTANT'
        else:
            newCalculationMethod=oldCalculationMethod
#            print "Morphing ", newCalculationMethod
            
            if newCalculationMethod.startswith("CALC-"):
                newCalculationMethod=newCalculationMethod[5:]
#                print "   <%s>" % (newCalculationMethod)
            
            if newCalculationMethod.endswith("_PROBLEM-OUTPUT"):
                newCalculationMethod=newCalculationMethod[:len(newCalculationMethod)-15]
#                print "   <%s>" % (newCalculationMethod)
            
            newCalculationMethod=changeCase(newCalculationMethod)
#            print "   <%s>" % (newCalculationMethod)
            
            newCalculationMethod=calculationMethodRoot + applicationNickName + "." + newCalculationMethod + '.calculate'
 
        ds = system.dataset.setValue(ds, row, 'new-recommendation-calculation-method', newCalculationMethod)
    return ds

def changeCase(txt):
    t1=txt
    t1=t1.title()
    t1=string.replace(t1,"_","")
    t1=string.replace(t1,"-","")
    
    print "Converted <%s> to <%s>" % (txt, t1)
    return t1

def stripTokens(tokens):
    strippedTokens=[]
    for token in tokens:
        if token.endswith('-GDA'):
            strippedToken=token.rstrip('-GDA')
            strippedTokens.append(strippedToken)
        else:
            strippedTokens.append(token)
    return strippedTokens


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

def initializeSQCDiagnosis(container):
    SQL="delete from DtSQCDiagnosis"
    rows=system.db.runUpdateQuery(SQL)
    print "Delete %i rows from DtSQCDiagnosis" % (rows)    
    
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

    for row in range(ds.rowCount):
        #There are two columns named application so use idx here
        #I used to use column 4 (mixed case), but Chuck was using column 2 (ugly G2 name, all caps with "-GDA")
        application = ds.getValueAt(row, 2) 
        unit = ds.getValueAt(row, "unit")
        messageQueue = ds.getValueAt(row, "msg-queue-name")
        includeInMainMenu = ds.getValueAt(row, "include-in-main-menu")
        if includeInMainMenu == "TRUE":
            includeInMainMenu=1
        else:
            includeInMainMenu=0
        groupRampMethod = ds.getValueAt(row, "group-ramp-method")
        groupRampMethod = string.capitalize(groupRampMethod)
        groupRampMethodId = lookup("GroupRampMethod", groupRampMethod)
        
        from ils.common.database import getUnitId
        unitId = getUnitId(unit)
        
        newMessageQueue, messageQueueId = lookupMessageQueue(messageQueue)
        
        print 
        print "Application   : ", application
        print "Unit          : ", unit
        print "Unit Id       : ", unitId
        print "Queue (old)   : ", messageQueue
        print "Queue (new)   : ", newMessageQueue
        print "Queue Id      : ", messageQueueId
        print "Ramp Method   : ", groupRampMethod
        print "Ramp Method Id: ", groupRampMethodId
    
        if unitId >= 0 and messageQueueId >= 0:
            SQL = "insert into DtApplication (ApplicationName, MessageQueueId, UnitId, IncludeInMainMenu, GroupRampMethodId) "\
                " values ('%s', %i, %i, %i, %i)" % \
                (application, messageQueueId, unitId, includeInMainMenu, groupRampMethodId)
            applicationId=system.db.runUpdateQuery(SQL, getKey=True)
            ds=system.dataset.setValue(ds, row, "id", applicationId) 
            print "Insert %s and got id: %i" % (application, applicationId)                               
        else:
            if unitId < 0:
                print "   *** Could not find unit: <%s>" % (unit)
            if messageQueueId < 0:
                print "   *** Could not find queue: <%s>" % (messageQueue)

        table.data=ds

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

    for row in range(ds.rowCount):
        application = ds.getValueAt(row, "Application")
        applicationId=getApplicationId(rootContainer, application)
        family = ds.getValueAt(row, "name")  # I used to use the label as the name, but Chuck is using the name
        description = ds.getValueAt(row, "description")
        priority = ds.getValueAt(row, "priority")

        print ""
        print "Application   : ", application
        print "Application Id: ", applicationId
        print "Family        : ", family
        print "Priority      : ", priority
        
        if applicationId >= 0:
            SQL = "insert into DtFamily (FamilyName, ApplicationId, FamilyPriority, Description) "\
                "values ('%s', %s, %s, '%s')" % \
                (family, str(applicationId), str(priority), description)
            print SQL
            familyId=system.db.runUpdateQuery(SQL, getKey=True)
            ds=system.dataset.setValue(ds, row, "id", familyId) 
            print "Insert %s and got id: %i" % (family, familyId)                                                         
        else:
            print "Could not find application: <%s>" % (application)


    table.data=ds


# We can't use the database to do this because the export contains the G2 name, but we inserted the 
# "label" attribute as the name of the family in the new platform
def getFamilyId(rootContainer, family):
    familyId = -1
    ds=rootContainer.getComponent("Family Container").getComponent("Power Table").data
    for row in range(ds.rowCount):
        if ds.getValueAt(row, "name") == family:
            return ds.getValueAt(row, "id")
    return familyId

# Lookup the id of the family in the DtFamily table
def fetchFamilyId(familyName):
    SQL = "select familyId from DtFamily where FamilyName = '%s'" % (familyName)
    familyId = system.db.runScalarQuery(SQL)
    print "Fetched id: <%s> for family <%s>" % (familyId, familyName)
    return familyId


def insertFinalDiagnosis(container):
    rootContainer=container.parent
    table=container.getComponent("Power Table")
    ds=table.data

    for row in range(ds.rowCount):
        family=ds.getValueAt(row, "family")
        finalDiagnosis=ds.getValueAt(row, 4)    # I used to use the label, but Chuck is using the name, so use the name
        explanation=ds.getValueAt(row, "explanation")
        priority=ds.getValueAt(row, "priority")
        calculationMethod=ds.getValueAt(row, "new-recommendation-calculation-method")
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
            SQL = "insert into DtFinalDiagnosis (FinalDiagnosisName, FamilyId, Explanation, "\
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

def insertSQCDiagnosis(container):
    rootContainer=container.parent
    table=container.getComponent("Power Table")
    ds=table.data

    for row in range(ds.rowCount):
        familyName=ds.getValueAt(row, "family")
        sqcDiagnosis=ds.getValueAt(row, 4)    # I used to use the label, but Chuck is using the name, so use the name
            
        familyId=fetchFamilyId(familyName)
            
        if familyId >= 0:
            SQL = "insert into DtSQCDiagnosis (SQCDiagnosisName, FamilyId, Status) "\
                "values ('%s', %s, 'Unknown')" % \
                 (sqcDiagnosis, str(familyId))
            print SQL
            sqcDiagnosisId=system.db.runUpdateQuery(SQL, getKey=True)
            ds=system.dataset.setValue(ds, row, "id", sqcDiagnosisId) 
            print "Inserted %s and got id: %i" % (sqcDiagnosis, sqcDiagnosisId)                                                         
        else:
            print "Could not find family: <%s>" % (familyName)

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
        print "Feedback Method: ", feedbackMethod
        from ils.migration.common import lookupFeedbackMethod
        newFeedbackMethod, feedbackMethodId = lookupFeedbackMethod(feedbackMethod)
        tagPath = ds.getValueAt(row, "connected-output-name")
    
        applicationId=getApplicationId(rootContainer, application)
        if applicationId >= 0:
            SQL = "insert into DtQuantOutput (QuantOutputName, ApplicationId, TagPath, MostNegativeIncrement, \
                MostPositiveIncrement, MinimumIncrement, SetpointHighLimit, \
                SetpointLowLimit, FeedbackMethodId, IncrementalOutput) "\
                "values ('%s', %s, '%s', %s, %s, %s, %s, %s, %s, %s)" % \
                (quantOutput, str(applicationId), tagPath, str(mostNegativeIncrement), 
                str(mostPositiveIncrement), str(minimumIncrement), str(setpointHighLimit),
                str(setpointLowLimit), str(feedbackMethodId), str(incrementalOutput))
            print SQL
            Id=system.db.runUpdateQuery(SQL, getKey=True)
            ds=system.dataset.setValue(ds, row, "id", Id) 
            print "Insert %s and got id: %i" % (quantOutput, Id)                                                         
        else:
            print "Could not find application: <%s>" % (application)

    table.data=ds

def updateQuantOutput(container):
    rootContainer=container.parent
    
    targetApplication=container.getComponent("Target Application").text
    applicationAlias=container.getComponent("Application Alias").text
    
    table=container.getComponent("Power Table")
    ds=table.data
    cnt = 0

    for row in range(ds.rowCount):
        quantOutputId = ds.getValueAt(row, "id")
        application = ds.getValueAt(row, "application")
        if application == targetApplication:
            tagName = ds.getValueAt(row, "connected-output-name")
            
            # If I could ever figure out how to determine the class of the UDT I could do something smarter here
            attr = 'sp/value'
            tagPath = 'DiagnosticToolkit/%s/%s/%s' % (applicationAlias, tagName, attr)
        
            SQL = "update DtQuantOutput set TagPath = '%s' where QuantOutputId = %s" % (tagPath, str(quantOutputId))
            print SQL
            rows=system.db.runUpdateQuery(SQL)
            cnt = cnt + rows                                                         

    print "Updated %i Quant Outputs" % (cnt)


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
        serverName, scanClass, writeLocationId = lookupOPCServerAndScanClass(site, gsiInterface)
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
        serverName, scanClass, writeLocationId = lookupOPCServerAndScanClass(site, gsiInterface)
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
                                "opItemId":opItemId, "modeItemId":modeItemId, "permissiveItemId":permissiveItemId,
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
        serverName, scanClass, writeLocationId = lookupOPCServerAndScanClass(site, gsiInterface)
        path = "DiagnosticToolkit/" + application
       
        parentPath = '[' + provider + ']' + path    
        tagPath = parentPath + "/" + outputName
        tagExists = system.tag.exists(tagPath)

        if not(tagExists):
            print "Creating a %s, Name: %s, Path: %s, SP Item Id: %s, Scan Class: %s, Server: %s" % (UDTType, outputName, tagPath, spItemId, scanClass, serverName)
            system.tag.addTag(parentPath=parentPath, name=outputName, tagType="UDT_INST", 
                        attributes={"UDTParentType":UDTType}, 
                        parameters={"itemId":itemId, "serverName":serverName, "scanClassName":scanClass, "spItemId":spItemId,
                            "opItemId":opItemId, "modeItemId":modeItemId, "permissiveItemId":permissiveItemId,
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
        if str(ds.getValueAt(row, 4)) == finalDiagnosis:
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

    