'''
Created on Sep 9, 2014

@author: ILS
'''
import system, string
from uuid import UUID
log = system.util.getLogger("com.ils.diagToolkit.recommendation,recommendationMap")

def build(rootContainer):
    applicationName=rootContainer.getPropertyValue("applicationName")
    quantOutputName=rootContainer.getPropertyValue("quantOutputName")
    log.infof("Building a recommendation map for Quant Output: %s/%s", applicationName, quantOutputName)

    # Get the production/isolation tag provider and database 
    db=system.tag.read("[Client]Database").value
    provider=system.tag.read("[Client]Tag Provider").value
    
    theMap = rootContainer.getComponent("TheMap")
    diagnoses = fetchDiagnosisForQuantOutput(applicationName, quantOutputName, db=db)
    diagnoses = updateSqcFlag(diagnoses)
    theMap.diagnoses=diagnoses
    
    outputs=fetchQuantOutput(applicationName, quantOutputName, db, provider)
    theMap.outputs=outputs
    
    recDefs=fetchRecDefs(diagnoses, outputs, db)
    
    recommendations, recDefs=fetchRecommendations(diagnoses, outputs, recDefs, db)
    theMap.connections=recDefs
    theMap.recommendations=recommendations    


def fetchQuantOutput(applicationName, quantOutputName, db, provider):
    log.tracef("Fetching the quant output...")
    SQL = "select QuantOutputName, TagPath, convert(decimal(10,4),CurrentSetpoint) as CurrentSetpoint, Active, "\
        " convert(decimal(10,4),FinalSetpoint) as FinalSetpoint, convert(decimal(10,4),DisplayedRecommendation) as DisplayedRecommendation "\
        " from DtQuantOutput QO, DtApplication A "\
        " where QO.QuantOutputName = '%s' "\
        " and QO.ApplicationId = A.ApplicationId"\
        " and A.ApplicationName = '%s' "\
        " order by QO.QuantOutputName" % (quantOutputName, applicationName)
    pds = system.db.runQuery(SQL, database=db)
    log.tracef("  ...fetched %d Quant Outputs...", len(pds))

    headers=["Name","CurrentSetpoint","FinalSetpoint","Recommendation","Target"]
    data = []
    for record in pds:
        log.tracef("Active: %s", str(record["Active"]))
        if record["Active"] in [1, True]:
            data.append([record["QuantOutputName"],record["CurrentSetpoint"],record["FinalSetpoint"],record["DisplayedRecommendation"],record["TagPath"]])
        else:
            log.tracef("Need to read current SP")
            tagPath = '[' + provider + ']' + record['TagPath']
            sp = system.tag.read(tagPath)
            if sp.quality.isGood():
                sp = sp.value
            else:
                sp = "Bad Value"
            data.append([record["QuantOutputName"],sp,record["FinalSetpoint"],record["DisplayedRecommendation"],record["TagPath"]])
            
    ds = system.dataset.toDataSet(headers, data)
    return ds

def fetchDiagnosisForQuantOutput(applicationName, quantOutputName, db=""):
    ''' '''
    log.tracef("Fetching Final Diagnosis that touch %s...", quantOutputName)
        
    SQL = "select distinct FD.FinalDiagnosisId, FD.FinalDiagnosisName, FD.FinalDiagnosisUUID, FD.DiagramUUID "\
        " from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO, DtFamily F, DtApplication A "\
        " where F.ApplicationId = A.ApplicationId "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and FD.FamilyId = F.FamilyId "\
        " and QO.ApplicationId = A.ApplicationId "\
        " and QO.QuantOutputName = '%s' "\
        " and A.ApplicationName = '%s'"\
        " order by FD.FinalDiagnosisName" % (quantOutputName, applicationName)

    log.tracef(SQL)
    pds = system.db.runQuery(SQL, database=db)
    log.tracef("  ...fetched %d Final Diagnoses...", len(pds))
    
    headers=["Name","Problem","Multiplier", "hasSQC", "UUID", "DiagramUUID", "SqcUUID", "SqcName"]
    data = []
    for record in pds:
        log.tracef("Looking for the multiplier for %s...", record["FinalDiagnosisName"])
        SQL = "select Multiplier from DtDiagnosisEntry where FinalDiagnosisId = %d and Status = 'Active'" % (record["FinalDiagnosisId"]) 
        multiplier = system.db.runScalarQuery(SQL)
        log.tracef( "The multiplier is: %s", str(multiplier))
        data.append([record["FinalDiagnosisName"], record["FinalDiagnosisName"], multiplier, False, record["FinalDiagnosisUUID"], record["DiagramUUID"], None, None])
    
    ds = system.dataset.toDataSet(headers, data)
    return ds

# Given a dataset of final diagnoses, for each diagnosis, interrogate the diagram and determine if there is a SQC diagnosis
# upstream of the final diagnosis. (This runs in the client)
def updateSqcFlag(diagnoses):
    import system.ils.blt.diagram as diagram
    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
    log.tracef( "Now updating the hasSQC flag for each final diagnosis...")
    for row in range(diagnoses.rowCount):
        finalDiagnosisName = diagnoses.getValueAt(row, "Name")
        log.tracef("  FD Name: %s:", finalDiagnosisName)
        diagramUUID = diagnoses.getValueAt(row, "DiagramUUID")
        log.tracef("  Diagram UUID: %s", str(diagramUUID))
        
        if diagramUUID != None: 
            # Get the upstream blocks, make sure to jump connections
            blocks=diagram.listBlocksGloballyUpstreamOf(diagramUUID, finalDiagnosisName)
            
            log.tracef("...found %i upstream blocks...", len(blocks))
    
            for block in blocks:
                if not(string.find(block.getClassName(),"sqcdiagnosis.SQCDiagnosis") == 0):
                    log.tracef("   ... found a SQC diagnosis...")
                    blockId=block.getIdString()
                    blockName=block.getName()
                    diagnoses=system.dataset.setValue(diagnoses, row, "hasSQC", True)
                    diagnoses=system.dataset.setValue(diagnoses, row, "SqcUUID", blockId)
                    diagnoses=system.dataset.setValue(diagnoses, row, "SqcName", blockName)

    return diagnoses

def fetchQuantOutputForDiagnosis(finalDiagnosisName, db=""):
    log.tracef( "Fetching all of the quant outputs for Final Diagnosis %s ...", finalDiagnosisName)
    
    SQL = "select QO.QuantOutputName, QO.TagPath, convert(decimal(10,4),CurrentSetpoint) as CurrentSetpoint, "\
        " convert(decimal(10,4),FinalSetpoint) as FinalSetpoint, convert(decimal(10,4),DisplayedRecommendation) as DisplayedRecommendation "\
        " from DtQuantOutput QO, DtRecommendationDefinition RD, DtFinalDiagnosis FD "\
        " where FD.FinalDiagnosisName = '%s' "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " order by QuantOutputName" % (finalDiagnosisName)

    log.tracef(SQL)
    pds = system.db.runQuery(SQL, database=db)
    log.tracef("  ...fetched %d Quant Outputs ...", len(pds))
    return pds


def fetchRecDefs(diagnoses, outputs, db):
    print "Fetching QuantRecDefs..."
    
    fdNames=[]
    for row in range(diagnoses.rowCount):
        fdNames.append(diagnoses.getValueAt(row, "Name"))
    fdNames="','".join(map(str,fdNames))
    
    outputNames=[]
    for row in range(outputs.rowCount):
        outputNames.append(outputs.getValueAt(row, "Name"))
    outputNames="','".join(map(str,outputNames))

    SQL = "select FD.FinalDiagnosisName, QO.QuantOutputName, RD.RecommendationDefinitionId "\
        " from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO "\
        " where FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId" \
        " and FD.FinalDiagnosisName in ('%s')" \
        " and QO.QuantOutputName in ('%s')" % (fdNames, outputNames)
    print SQL
    pds = system.db.runQuery(SQL, database=db)
    print "  ...fetched %i QuantRecDefs!" % (len(pds))
    
    headers=["DiagnosisId","OutputId","Active"]
    data = []
    for record in pds:
        finalDiagnosisName = record["FinalDiagnosisName"]
        quantOutputName = record["QuantOutputName"]
        
        diagnosisIdx=lookupIdx(diagnoses, "Name", finalDiagnosisName)
        outputIdx=lookupIdx(outputs, "Name", quantOutputName)
        data.append([diagnosisIdx, outputIdx, False])
        
    ds = system.dataset.toDataSet(headers, data)
    return ds

def fetchRecommendations(diagnoses, outputs, recDefs, db):
    print "Fetching Recommendations..."
    
    fdNames=[]
    for row in range(diagnoses.rowCount):
        fdNames.append(diagnoses.getValueAt(row, "Name"))
    fdNames="','".join(map(str,fdNames))
    
    outputNames=[]
    for row in range(outputs.rowCount):
        outputNames.append(outputs.getValueAt(row, "Name"))
    outputNames="','".join(map(str,outputNames))

    SQL = "select FD.FinalDiagnosisName, QO.QuantOutputName, RD.RecommendationDefinitionId, R.AutoOrManual, R.RecommendationId, "\
        " convert(decimal(10,4), R.Recommendation) as Recommendation, "\
        " convert(decimal(10,4), R.AutoRecommendation) as AutoRecommendation, "\
        " convert(decimal(10,4), R.ManualRecommendation) as ManualRecommendation "\
        " from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO, DtRecommendation R "\
        " where FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId" \
        " and RD.RecommendationDefinitionId = R.RecommendationDefinitionId "\
        " and FD.FinalDiagnosisName in ('%s')" \
        " and QO.QuantOutputName in ('%s')" % (fdNames, outputNames)
    
    print SQL
    pds = system.db.runQuery(SQL, database=db)
    print "  ...fetched %i recommendations!" % (len(pds))
    
    headers=["DiagnosisId","OutputId","Auto", "Manual", "AutoOrManual", "RecommendationId"]
    data = []
    for record in pds:
        finalDiagnosisName = record["FinalDiagnosisName"]
        quantOutputName = record["QuantOutputName"]
        recommendation = record["AutoRecommendation"]
        manual = record["ManualRecommendation"]
        autoOrManual = record["AutoOrManual"]
        recommendationId = record["RecommendationId"]
        
        diagnosisIdx=lookupIdx(diagnoses, "Name", finalDiagnosisName)
        outputIdx=lookupIdx(outputs, "Name", quantOutputName)
        data.append([diagnosisIdx, outputIdx, recommendation, manual, autoOrManual, recommendationId])
        
        recDefs=setActiveRecDef(recDefs,diagnosisIdx, outputIdx)
        
    recommendations = system.dataset.toDataSet(headers, data)
    return recommendations, recDefs

def lookupIdx(ds, attr, val):
    for row in range(ds.rowCount):
        if ds.getValueAt(row, attr) == val:
            return row
    return -1

def setActiveRecDef(recDefs,diagnosisIdx, outputIdx):
    for row in range(recDefs.rowCount):
        if recDefs.getValueAt(row, "DiagnosisId") == diagnosisIdx and recDefs.getValueAt(row, "OutputId") == outputIdx:
            recDefs = system.dataset.setValue(recDefs, row, "Active", True)
            return recDefs
    return recDefs

'''
Final Diagnosis callbacks
'''
def hideFinalDiagnosis(theMap, diagnosisIdx):
    print "In hideFinalDiagnosis..."
    diagnosesDs = theMap.diagnoses
    diagnosesDs = system.dataset.deleteRow(diagnosesDs, diagnosisIdx)
    theMap.diagnoses = diagnosesDs 
    
    ds = theMap.connections
    ds = removeIdx(ds, "DiagnosisId", diagnosisIdx)
    theMap.connections = ds

    ds = theMap.recommendations 
    ds = removeIdx(ds, "DiagnosisId", diagnosisIdx)
    theMap.recommendations = ds
    
#    outputs = theMap.outputs

def expandFinalDiagnosis(theMap, diagnosisIdx):
    print "In expandFinalDiagnosis..."
    # Get the production/isolation tag provider and database 
    db=system.tag.read("[Client]Database").value
    finalDiagnosisName = getFinalDiagnosisName(theMap, diagnosisIdx)
    
    ds = theMap.outputs
    
    pds = fetchQuantOutputForDiagnosis(finalDiagnosisName)
    print "Fetched %i outputs" % (len(pds))
    
    # Merge the fetched dataset with the datset that is in the widget
    addedOutput = False
    for record in pds:
        outputName = record["QuantOutputName"]
        
        foundOutput = False
        for row in range(0, ds.rowCount, 1):
            print "checking row: ", row
            if outputName == ds.getValueAt(row, "Name"):
                foundOutput = True
        
        # If this output wasn't found, then add it atthe end 
        if not(foundOutput):
            addedOutput = True
            ds=system.dataset.addRow(ds,[record["QuantOutputName"],record["CurrentSetpoint"],record["FinalSetpoint"],record["DisplayedRecommendation"],record["TagPath"]])

    if addedOutput:
        print "at least one output was added..."
        outputs = system.dataset.sort(ds, "Name")
        theMap.outputs = outputs
        recDefs=fetchRecDefs(theMap.diagnoses, outputs, db)
    
        recommendations, recDefs=fetchRecommendations(theMap.diagnoses, outputs, recDefs, db)
        theMap.connections=recDefs
        theMap.recommendations=recommendations


# This should only be called IF there is an SQC diagnosis for the final Diagnosis, but that is a little tricky, so be defensive.
def sqcPlot(theMap, finalDiagnosisIdx):
    print "In sqcPlot..."
    
    # Get the upstream blocks, look for a SQC diagnosis.
    diagnoses = theMap.diagnoses
    hasSQC=diagnoses.getValueAt(finalDiagnosisIdx, "hasSQC")
    if not(hasSQC):
        system.gui.warningBox("This final diagnosis does not have a corresponding SQC plot")
        return
    
    sqcBlockId = diagnoses.getValueAt(finalDiagnosisIdx, "SqcUUID")
    sqcDiagnosisName = diagnoses.getValueAt(finalDiagnosisIdx, "SqcName")
    
    from ils.sqc.menuUI import openSQCPlotForSQCDiagnosis
    openSQCPlotForSQCDiagnosis(sqcDiagnosisName, sqcBlockId)

def changeMultiplier(theMap, finalDiagnosisIdx):
    print "In changeMultiplier..."
    project = system.util.getProjectName()
    rootContainer = theMap.parent
        
    # Get the production/isolation database 
    db=system.tag.read("[Client]Database").value
    provider=system.tag.read("[Client]Tag Provider").value
    
    ds = theMap.diagnoses
    multiplier = ds.getValueAt(finalDiagnosisIdx, "Multiplier")
    finalDiagnosisName = ds.getValueAt(finalDiagnosisIdx, "Name")
    
    # Final Diagnosis may be displayed on the map even when there are no recommendations, when this happens the multiplier will be None
    if multiplier == None:
        system.gui.messageBox("There are no recommendations for this final diagnosis, unable to enter a multiplier.")
        return
    
    newMultiplier = system.gui.inputBox("The current Multiplier is (%f), enter a new multiplier:" % (multiplier), "%f" % (multiplier))
    print "The new multiplier is: ", newMultiplier
    
    if newMultiplier == None or float(newMultiplier) == float(multiplier):
        print "Returning because the user pressed cancel or the recommendation was not changed"
        return 

    try:
        # First  update the database
        SQL = "Update DtDiagnosisEntry set Multiplier = %s where Status = 'Active' and FinalDiagnosisId = "\
            "(select FinalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName = '%s')" % (newMultiplier, finalDiagnosisName)
        print SQL
        rows = system.db.runUpdateQuery(SQL, db)
        print "Updated %i Final Diagnosis Entries" % (rows)
        
        # Update each recommendation connected to the final diagnosis
        if float(newMultiplier) == 1.0:
            print "Updating the recommendations to 'AUTO' because a multiplier of 1.0 was entered!"
            SQL = "Update DtRecommendation set AutoOrManual = 'Auto', ManualRecommendation = NULL, "\
                " Recommendation = AutoRecommendation "\
                " where RecommendationDefinitionId in (select RecommendationDefinitionId "\
                " from DtRecommendationDefinition RD, DtFinalDiagnosis FD "\
                "where RD.FinalDiagnosisId = FD.FinalDiagnosisId and FD.FinalDiagnosisName = '%s')" % (finalDiagnosisName)
        else: 
            print "Updating the recommendations to a user specified multiplier of %s..." % (str(newMultiplier))
            SQL = "Update DtRecommendation set AutoOrManual = 'Manual', ManualRecommendation = AutoRecommendation * %s, "\
                " Recommendation = AutoRecommendation * %s "\
                " where RecommendationDefinitionId in (select RecommendationDefinitionId "\
                " from DtRecommendationDefinition RD, DtFinalDiagnosis FD "\
                "where RD.FinalDiagnosisId = FD.FinalDiagnosisId and FD.FinalDiagnosisName = '%s')" % (newMultiplier, newMultiplier, finalDiagnosisName)
        print SQL
        rows = system.db.runUpdateQuery(SQL, db)
        print "Updated %i recommendations" % (rows)
        
        # If there are no current recommendations then why did the user change the multiplier?  It doesn't make any sense, but 
        # regardless the outputs don't need to be updated.
        print "Now updating quantoutputs..."
        numOutputs = 0
        if rows > 0:
            # Update the Total change for the quant output - remember that the output may be affected my multiple FDs
            # By involving DtRecommendation in this query, I will only get Outputs that have a recommendation.  A FD may have more
            # outputs than recommendations, a calculation method does not always need to manipulate all of the possible outputs.
            SQL = "select QuantOutputId from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtRecommendation R "\
                " where FD.FinalDiagnosisId = RD.FinalDiagnosisId and RD.RecommendationDefinitionId = R.RecommendationDefinitionId "\
                " and FinalDiagnosisName = '%s'" % finalDiagnosisName
            pds = system.db.runQuery(SQL, db)
            numOutputs = 0
            for record in pds:
                numOutputs = numOutputs + 1
                print "Processing QuantOutput: ", record["QuantOutputId"]
                SQL = "select sum(Recommendation) from DtRecommendation R, DtRecommendationDefinition RD "\
                    " where RD.RecommendationDefinitionId = R.RecommendationDefinitionId "\
                    " and RD.QuantOutputId = %s " % (record["QuantOutputId"])
                recommendation = system.db.runScalarQuery(SQL)
                print "The total recommendation is: ", recommendation
                
                if float(newMultiplier) == 1.0:
                    SQL = "Update DtQuantOutput set ManualOverride = 0, FeedbackOutputManual = 0, DisplayedRecommendation = %s, "\
                        " finalSetpoint = CurrentSetpoint + %s "\
                        " where QuantOutputId = %s" % (recommendation, recommendation, record["QuantOutputId"])
                else:
                    SQL = "Update DtQuantOutput set ManualOverride = 1, FeedbackOutputManual = %s, DisplayedRecommendation = %s, "\
                        " finalSetpoint = CurrentSetpoint + %s "\
                        " where QuantOutputId = %s" % (recommendation, recommendation, recommendation, record["QuantOutputId"])
                print SQL
                rows = system.db.runUpdateQuery(SQL, db)
                print "Updated %i quant outputs" % (rows)

        # Update the recommendation map on this client
        update(rootContainer)
        
        # Notify clients to update their setpoint spreadsheeta and recommendation maps
        post = rootContainer.getPropertyValue('post')
        clientId = system.util.getClientId()
        
        from ils.diagToolkit.finalDiagnosis import notifyClients
        notifyClients(project, post, clientId=clientId, notificationText="", notificationMode="quiet", numOutputs=numOutputs, database=db, provider=provider)
        print "Done"

    except:
        print "Caught an exception"
        from ils.common.error import catchError
        catchError()

# Send a message to clients to update any open recommendation maps.
def notifyRecommendationMapClients(project, post, clientId):
    print "Notifying %s-%s client to update their recommendation map..." % (project, post)
    system.util.sendMessage(project=project, messageHandler="consoleManager", 
                            payload={'type':'recommendationMap', 'post':post, 'clientId':clientId}, scope="C")


def handleNotification(payload):
    print "In %s handling a Recommendation Map u pdate message (%s)" % (__name__, str(payload))

    clientId=payload.get('clientId', -1)
    
    # If the client that received the message is the same on ethat sent the message then ignore it
    if clientId == system.util.getClientId():
        print "Ignoring a update recommendation map message because I am the client that sent it!"
        return
    
    windows = system.gui.getOpenedWindows()
    
    # check if the recommendation map is already open.
    print "Checking to see if there is an open recommendation map..."
    for window in windows:
        windowPath=window.getPath()
        
        pos = windowPath.find('Recommendation Map')
        if pos >= 0:
            print "...found an open recommendation map"
            rootContainer=window.rootContainer
            update(rootContainer)


'''
This is called in response to something being updated, either a recalc happened (possibly on a different client,
or a new diagnosis was made.
''' 
def update(rootContainer):
    print "Updating a recommendation map..."
    theMap = rootContainer.getComponent("TheMap")
    db=system.tag.read("[Client]Database").value
    
    # Update the recommendations Dataset
    '''
    ds = theMap.recommendations
    for row in range(ds.rowCount):
        recommendationId = ds.getValueAt(row, "RecommendationId")
        print "Row: %i, RecommendationId: %s" % (row, str(recommendationId))
        SQL = "select AutoRecommendation, ManualRecommendation, AutoOrManual from DtRecommendation "\
            "where RecommendationId = %s" % (recommendationId)
        pds = system.db.runQuery(SQL, db)
        if len(pds) == 1:
            record = pds[0]
            auto = record["AutoRecommendation"]
            manual = record["ManualRecommendation"]
            autoOrManual = record["AutoOrManual"]
            print "Updating recommendation - id: %s, Auto: %s, Manual: %s, A/M: %s" % (str(recommendationId), str(auto), str(manual), str(autoOrManual))
            ds = system.dataset.setValue(ds, row, "Auto", auto)
            ds = system.dataset.setValue(ds, row, "Manual", manual)
            ds = system.dataset.setValue(ds, row, "AutoOrManual", autoOrManual)
    theMap.recommendations = ds
    '''
    
    
    # Update the Outputs Dataset
    ds = theMap.outputs
    print "...updating the outputs dataset..."
    for row in range(ds.rowCount):
        quantOutputName = ds.getValueAt(row, "Name")

        SQL = "select convert(decimal(10,4), CurrentSetpoint) as CurrentSetpoint, "\
            "convert(decimal(10,4), FinalSetpoint) as FinalSetpoint, "\
            "convert(decimal(10,4), DisplayedRecommendation) as DisplayedRecommendation from DtQuantOutput "\
            "where QuantOutputName = '%s' " % (quantOutputName)
        pds = system.db.runQuery(SQL, db)
        if len(pds) == 1:
            record = pds[0]
            currentSetpoint = record["CurrentSetpoint"]
            finalSetpoint = record["FinalSetpoint"]
            recommendation = record["DisplayedRecommendation"]
            ds = system.dataset.setValue(ds, row, "CurrentSetpoint", currentSetpoint)
            ds = system.dataset.setValue(ds, row, "FinalSetpoint", finalSetpoint)
            ds = system.dataset.setValue(ds, row, "Recommendation", recommendation)
    theMap.outputs = ds
    
    # Update the Final Diagnosis Dataset
    print "...updating the final diagnosis dataset..."
    ds = theMap.diagnoses
    for row in range(ds.rowCount):
        finalDiagnosisName = ds.getValueAt(row, "Name")
        print "  ...updating multiplier for %s..." % (finalDiagnosisName)

        SQL = "select DE.Multiplier from DtDiagnosisEntry DE, DtFinalDiagnosis FD "\
            " where FD.FinalDiagnosisName = '%s' "\
            " and FD.FinalDiagnosisId = DE.FinalDiagnosisId "\
            " and DE.Status = 'Active'" % (finalDiagnosisName)
        pds = system.db.runQuery(SQL, db)
        if len(pds) == 1:
            record = pds[0]
            multiplier = record["Multiplier"]
            ds = system.dataset.setValue(ds, row, "Multiplier", multiplier)
            print "  ...updated %i rows with %s" % (len(pds), str(multiplier))
        else:
            print "  WARNING: Unexpected number of final diagnosis records: %i" % (len(pds))

    theMap.diagnoses = ds
    
    recDefs=theMap.connections
    recommendations, recDefs=fetchRecommendations(theMap.diagnoses, theMap.outputs, recDefs, db)
    theMap.connections=recDefs
    theMap.recommendations=recommendations
    
'''
Recommendation callbacks
'''
def manualRecommendation(theMap, recommendationIdx):
    print "In changeRecommendation..."
    # Get the production/isolation database 
    db=system.tag.read("[Client]Database").value
    ds = theMap.recommendations
    manualRecommendation = ds.getValueAt(recommendationIdx, "Manual")
    autoRecommendation = ds.getValueAt(recommendationIdx, "Auto")
#    diagnosisIdx = ds.getValueAt(recommendationIdx, "DiagnosisId")
#    outputIdx = ds.getValueAt(recommendationIdx, "OutputId")
#    autoOrManual = ds.getValueAt(recommendationIdx, "AutoOrManual")
    recommendationId = ds.getValueAt(recommendationIdx, "RecommendationId")
    
    if manualRecommendation == None or manualRecommendation == ""  or manualRecommendation == "0.0":
        currentRecommendation = autoRecommendation
    else:
        currentRecommendation = manualRecommendation
        
    txt = "The current recommendation is (%f), enter a new recommendation:" % (currentRecommendation)
    print txt
    newManualRecommendation = system.gui.inputBox(txt, "%f" % (currentRecommendation))
    print "The new multiplier is: ", newManualRecommendation
    
    if newManualRecommendation == None or float(newManualRecommendation) == float(currentRecommendation):
        print "Returning because the user pressed cancel or the recommendation was not changed"
        return 

    # Process the multiplier - first update the map widget
    ds = system.dataset.setValue(ds, recommendationIdx, "Manual", newManualRecommendation)
    ds = system.dataset.setValue(ds, recommendationIdx, "AutoOrManual", "Manual")
    theMap.recommendations = ds

    # Now update the database
    SQL = "Update DtRecommendation set ManualRecommendation = %s, AutoOrManual = 'Manual' where RecommendationId = %s" % (newManualRecommendation, recommendationId)
    print SQL
    rows = system.db.runUpdateQuery(SQL, db)
    print "Updated %i rows in Final Diagnosis" % (rows)

'''
Quant Output callbacks
'''
def hideOutput(theMap, outputIdx):
    print "In hideOutput, the index is %i..." % (outputIdx)

    outputDs = theMap.outputs
    outputDs = system.dataset.deleteRow(outputDs, outputIdx)
    theMap.outputs = outputDs 
    
    ds = theMap.connections
    ds = removeIdx(ds, "OutputId", outputIdx)
    theMap.connections = ds

    ds = theMap.recommendations 
    ds = removeIdx(ds, "OutputId", outputIdx)
    theMap.recommendations = ds

def expandOutput(theMap, outputIdx):
    print "In expandOutput, the index is %i..." % (outputIdx)
    # Get the production/isolation database 
    db=system.tag.read("[Client]Database").value
    rootContainer = theMap.parent
    applicationName=rootContainer.getPropertyValue("applicationName")
    quantOutputName = getOutputName(theMap, outputIdx)
    print "...expanding %s..." % (quantOutputName) 
    
    diagnosesDS = fetchDiagnosisForQuantOutput(applicationName, quantOutputName, db=db)
    ds = theMap.diagnoses
    
    addedDiagnosis = False
    for diagnosisRow in range(0, diagnosesDS.rowCount):
        print "Checking diagnosis idx: ", diagnosisRow
        finalDiagnosisName = diagnosesDS.getValueAt(diagnosisRow, "Name")
        print "  ...fetched %s (record %i)..." % (finalDiagnosisName, diagnosisRow)
        
        foundFinalDiagnosis = False
        for row in range(0, ds.rowCount):
            print "checking row: ", row
            if finalDiagnosisName == ds.getValueAt(row, "Name"):
                foundFinalDiagnosis = True
                print "     --- found an existing diagnosis ---"
        
        # If this output wasn't found, then add it at the end 
        if not(foundFinalDiagnosis):
            print "     adding a new final diagnosis"
            addedDiagnosis = True
            multiplier = diagnosesDS.getValueAt(diagnosisRow, "Multiplier")
            blockUUID = diagnosesDS.getValueAt(diagnosisRow, "UUID")
            diagramUUID = diagnosesDS.getValueAt(diagnosisRow, "DiagramUUID")
            hasSQC = False
            sqcUUID = None
            sqcName = None
            print "Adding"
            ds=system.dataset.addRow(ds,[finalDiagnosisName, finalDiagnosisName, multiplier, hasSQC, blockUUID, diagramUUID, sqcUUID, sqcName])
            print "Done Adding"
            
    if addedDiagnosis:
        print "at least one Final Diagnosis was added..."
        diagnoses = system.dataset.sort(ds, "Name")
        diagnosis = updateSqcFlag(diagnoses)
        theMap.diagnoses = diagnoses
        outputs=theMap.outputs
        recDefs=fetchRecDefs(diagnoses, outputs, db)
    
        recommendations, recDefs=fetchRecommendations(diagnoses, outputs, recDefs, db)
        theMap.connections=recDefs
        theMap.recommendations=recommendations


'''
Callback Helpers
'''
def removeIdx(ds, attr, IDX):
    # Need to do this in reverse
    for row in range(ds.rowCount - 1, -1, -1):
        print "checking row: ", row
        idx=ds.getValueAt(row, attr)
        if idx == IDX:
            ds=system.dataset.deleteRow(ds, row)
        elif idx > IDX:
            ds=system.dataset.setValue(ds, row, attr, idx - 1)
    return ds

def getFinalDiagnosisName(theMap, diagnosisIdx):
    ds = theMap.diagnoses
    finalDiagnosisName = ds.getValueAt(diagnosisIdx, "Name")
    return finalDiagnosisName

def getOutputName(theMap, outputIdx):
    ds = theMap.outputs
    outputName = ds.getValueAt(outputIdx, "Name")
    return outputName

# Purely for testing Chuck's widget
def test(rootContainer):
    #
    # Programmatically create datasets for the recommendation map
    #
    theMap = rootContainer.getComponent("TheMap")
    print "PopulateMap ..."
    # Create a dataset for diagnoses
    headers=["Name","Problem","Multiplier"]
    data = []
    data.append(["Diag1", "ProblemForDiag1",1.1])
    data.append(["Diag2", "ProblemForDiag2",1.2])
    data.append(["Diag3", "ProblemForDiag3",1.3])
    data.append(["Diag4", "ProblemForDiag4",1.4])
    data.append(["Diag5", "ProblemForDiag5",0.4])
    diagnoses = system.dataset.toDataSet(headers, data)
    theMap.setDiagnoses(diagnoses)
    print "PopulateMap: set diagnoses."
    
    # Create a dataset for quant outputs
    headers=["Name","CurrentSetpoint","FinalSetpoint","Recommendation","Target"]
    data = []
    data.append(["Out1", 21.1,33.1,12.6,22.5])
    data.append(["Out2", 22.1,33.2,12.6,23.5])
    data.append(["Out3", 23.1,33.3,12.6,24.5])
    data.append(["Out4", 24.1,33.4,12.6,25.5])
    data.append(["Out5", 25.1,33.5,12.6,26.5])
    outputs = system.dataset.toDataSet(headers, data)
    theMap.setOutputs(outputs)
    print "PopulateMap: set outputs."
    
    # Create a dataset for connections
    # The diagnosisId is the diagnosis dataset row number
    # The outputId is the output dataset row number
    headers=["DiagnosisId","OutputId","Active"]
    data = []
    data.append([0, 0,False])
    data.append([0, 1,False])
    data.append([2, 2,True])
    data.append([3, 2,True])
    data.append([4, 0,False])
    connections = system.dataset.toDataSet(headers, data)
    theMap.setConnections(connections)
    print "PopulateMap: set connections."
    
    # Create a dataset for recommendations
    # Recommendations only exist for active connections
    headers=["DiagnosisId","OutputId","Auto"]
    data = []
    data.append([2, 2,"0.5"])
    data.append([3, 2,"1.6"])
    recommends = system.dataset.toDataSet(headers, data)
    theMap.setRecommendations(recommends)
    print "PopulateMap: set recommendations."
    
    