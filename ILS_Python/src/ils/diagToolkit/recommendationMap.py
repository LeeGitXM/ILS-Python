'''
Created on Sep 9, 2014

@author: ILS
'''
import system
from uuid import UUID

def build(rootContainer, db=""):
    quantOutputName=rootContainer.quantOutputName
    print "Building a recommendation map for Quant Output: ", quantOutputName

    theMap = rootContainer.getComponent("TheMap")
    diagnoses = fetchDiagnosisForQuantOutput(quantOutputName, db)
    diagnoses = updateSqcFlag(diagnoses)
    theMap.diagnoses=diagnoses
    
    outputs=fetchQuantOutput(quantOutputName, db)
    theMap.outputs=outputs
    
    recDefs=fetchRecDefs(diagnoses, outputs, db)
    
    recommendations, recDefs=fetchRecommendations(diagnoses, outputs, recDefs, db)
    theMap.connections=recDefs
    theMap.recommendations=recommendations    


def fetchQuantOutput(quantOutputName, db=""):
    print "Fetching the quant output..."
    SQL = "select QuantOutputName, TagPath, convert(decimal(10,4),CurrentSetpoint) as CurrentSetpoint, "\
        " convert(decimal(10,4),FinalSetpoint) as FinalSetpoint, convert(decimal(10,4),DisplayedRecommendation) as DisplayedRecommendation "\
        " from DtQuantOutput "\
        " where QuantOutputName = '%s' "\
        " order by QuantOutputName" % (quantOutputName)
    print SQL
    pds = system.db.runQuery(SQL, database=db)
    print "  ...fetched %i Quant Outputs..." % (len(pds))
    
    headers=["Name","CurrentSetpoint","FinalSetpoint","Recommendation","Target"]
    data = []
    for record in pds:
        data.append([record["QuantOutputName"],record["CurrentSetpoint"],record["FinalSetpoint"],record["DisplayedRecommendation"],record["TagPath"]])
    ds = system.dataset.toDataSet(headers, data)
    return ds

def fetchDiagnosisForQuantOutput(quantOutputName, db=""):
    print "Fetching Final Diagnosis..."
    SQL = "select FD.FinalDiagnosisName, convert(decimal(10,2),FD.Multiplier) as Multiplier, FD.UUID, FD.DiagramUUID "\
        " from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO "\
        " where FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and QO.QuantOutputName = '%s' "\
        " order by FinalDiagnosisName" % (quantOutputName)
    print SQL
    pds = system.db.runQuery(SQL, database=db)
    print "  ...fetched %i Final Diagnoses..." % (len(pds))
    
    headers=["Name","Problem","Multiplier", "hasSQC", "UUID", "DiagramUUID", "SqcUUID", "SqcName"]
    data = []
    for record in pds:
        data.append([record["FinalDiagnosisName"],record["FinalDiagnosisName"],record["Multiplier"], False, record["UUID"], record["DiagramUUID"], None, None])
    ds = system.dataset.toDataSet(headers, data)
    return ds

# Given a dataset of final diagnoses, for each diagnosis, interrogate the diagram and determine if there is a SQC diagnosis
# upstream of the final diagnosis.
def updateSqcFlag(diagnoses):
    import system.ils.blt.diagram as diagram
    import com.ils.blt.common.serializable.SerializableBlockStateDescriptor
    print "Now updating the hasSQC flag for each final diagnosis..."
    for row in range(diagnoses.rowCount):
        finalDiagnosisName = diagnoses.getValueAt(row, "Name")
        print " "
        print "  FD Name: %s:" % (finalDiagnosisName)
        diagramUUID = diagnoses.getValueAt(row, "DiagramUUID")
        print "  Diagram UUID: %s" % (str(diagramUUID))
        
        if diagramUUID != None: 
            # Get the upstream blocks, make sure to jump connections
            blocks=diagram.listBlocksGloballyUpstreamOf(diagramUUID, finalDiagnosisName)
            
            print "Found upstream blocks: ", str(blocks)
            print "...found %i upstream blocks..." % (len(blocks))
    
            for block in blocks:
                print "Found a %s block..." % (block.getClassName())
                if block.getClassName() == "xom.block.sqcdiagnosis.SQCDiagnosis":
                    print "   ... found a SQC diagnosis..."
                    blockId=block.getIdString()
                    blockName=block.getName()
                    diagnoses=system.dataset.setValue(diagnoses, row, "hasSQC", True)
                    diagnoses=system.dataset.setValue(diagnoses, row, "SqcUUID", blockId)
                    diagnoses=system.dataset.setValue(diagnoses, row, "SqcName", blockName)

    return diagnoses

def fetchQuantOutputForDiagnosis(finalDiagnosisName, db=""):
    print "Fetching all of the quant outputs for Final Diagnosis %s ..." % (finalDiagnosisName)
    
    SQL = "select QO.QuantOutputName, QO.TagPath, convert(decimal(10,4),CurrentSetpoint) as CurrentSetpoint, "\
        " convert(decimal(10,4),FinalSetpoint) as FinalSetpoint, convert(decimal(10,4),DisplayedRecommendation) as DisplayedRecommendation "\
        " from DtQuantOutput QO, DtRecommendationDefinition RD, DtFinalDiagnosis FD "\
        " where FD.FinalDiagnosisName = '%s' "\
        " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " order by QuantOutputName" % (finalDiagnosisName)

    print SQL
    pds = system.db.runQuery(SQL, database=db)
    print "  ...fetched %i Quant Outputs ..." % (len(pds))
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
    print "  ...fetched %i recommendations!"
    
    headers=["DiagnosisId","OutputId","Auto", "Manual", "AutoOrManual", "RecommendationId"]
    data = []
    for record in pds:
        finalDiagnosisName = record["FinalDiagnosisName"]
        quantOutputName = record["QuantOutputName"]
        recommendation = record["Recommendation"]
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

#---------------------------
# Final Diagnosis callbacks
#---------------------------
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
    db = ""
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
    db = ""
    print "In changeMultiplier..."
    
    ds = theMap.diagnoses
    multiplier = ds.getValueAt(finalDiagnosisIdx, "Multiplier")
    finalDiagnosisName = ds.getValueAt(finalDiagnosisIdx, "Name")
    
    newMultiplier = system.gui.inputBox("The current Multiplier is (%f), enter a new multiplier:" % (multiplier), "%f" % (multiplier))
    print "The new multiplier is: ", newMultiplier
    
    if newMultiplier == None or float(newMultiplier) == float(multiplier):
        print "Returning because the user pressed cancel or the recommendation was not changed"
        return 

    # Process the multiplier - first update the map widget
    ds = system.dataset.setValue(ds, finalDiagnosisIdx, "Multiplier", newMultiplier)
    theMap.diagnoses = ds

    SQL = "Update DtFinalDiagnosis set Multiplier = %s where FinalDiagnosisName = '%s'" % (newMultiplier, finalDiagnosisName)
    print SQL
    rows = system.db.runUpdateQuery(SQL, db)
    print "Updated %i rows in Final Diagnosis" % (rows)


#--------------------------
# Recommendation callbacks
#--------------------------
def manualRecommendation(theMap, recommendationIdx):
    db = ""
    print "In changeRecommendation..."
    
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


#--------------------------
# Quant Output callbacks
#--------------------------
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
    db = ""
    print "In expandOutput, the index is %i..." % (outputIdx)

    quantOutputName = getOutputName(theMap, outputIdx)    
    diagnosesDS = fetchDiagnosisForQuantOutput(quantOutputName, db)
    
    ds = theMap.diagnoses
    
    addedDiagnosis = False
    for diagnosisRow in range(0, diagnosesDS.rowCount, 1):
        finalDiagnosisName = diagnosesDS.getValueAt(diagnosisRow, "Name")
        
        foundFinalDiagnosis = False
        for row in range(0, ds.rowCount, 1):
            print "checking row: ", row
            if finalDiagnosisName == ds.getValueAt(row, "Name"):
                foundFinalDiagnosis = True
        
        # If this output wasn't found, then add it at the end 
        if not(foundFinalDiagnosis):
            addedDiagnosis = True
            multiplier = diagnosesDS.getValueAt(diagnosisRow, "Multiplier")
            blockUUID = diagnosesDS.getValueAt(diagnosisRow, "UUID")
            diagramUUID = diagnosesDS.getValueAt(diagnosisRow, "DiagramUUID")
            sqcUUID = None
            sqcName = None
            ds=system.dataset.addRow(ds,[finalDiagnosisName, finalDiagnosisName, multiplier, blockUUID, diagramUUID, sqcUUID, sqcName])

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


#-------------------
# Callback Helpers
#-------------------
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
    
    