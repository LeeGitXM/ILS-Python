'''
Created on Sep 9, 2014

@author: ILS
'''
import system

def build(rootContainer, db=""):
    quantOutputName=rootContainer.quantOutputName
    print "Building a recommendation map for Quant Output: ", quantOutputName

    theMap = rootContainer.getComponent("TheMap")
    diagnoses = fetchDiagnosisForQuantOutput(quantOutputName, db)
    theMap.diagnoses=diagnoses
    
    outputs=fetchQuantOutput(quantOutputName, db)
    theMap.outputs=outputs
    
    recDefs=fetchRecDefs(diagnoses, outputs, db)
    
    recommendations, recDefs=fetchRecommendations(diagnoses, outputs, recDefs, db)
    theMap.connections=recDefs
    theMap.recommendations=recommendations    

def fetchQuantOutput(quantOutputName, db=""):
    print "Fetching the quant output..."
    SQL = "select QuantOutputName, TagPath, CurrentSetpoint, FinalSetpoint, DisplayedRecommendation "\
        " from DtQuantOutput "\
        " where QuantOutputName = '%s' "\
        " order by QuantOutputName" % (quantOutputName)
    print SQL
    pds = system.db.runQuery(SQL, database=db)
    print "  ...fetched %i Quant Outputs..." % (len(pds))
    
    headers=["Name","CurrentSetpoint","FinalSetpoint","Recommendation","Target"]
    data = []
    for record in pds:
        #TODO Target should be the tagPath - wait for Chuck to change to a string
        data.append([record["QuantOutputName"],record["CurrentSetpoint"],record["FinalSetpoint"],record["DisplayedRecommendation"],record["DisplayedRecommendation"]])
    ds = system.dataset.toDataSet(headers, data)
    return ds

def fetchDiagnosisForQuantOutput(quantOutputName, db=""):
    print "Fetching Final Diagnosis..."
    SQL = "select FD.FinalDiagnosisName, FD.Multiplier "\
        " from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO "\
        " where FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and QO.QuantOutputName = '%s' "\
        " order by FinalDiagnosisName" % (quantOutputName)
    print SQL
    pds = system.db.runQuery(SQL, database=db)
    print "  ...fetched %i Final Diagnoses..." % (len(pds))
    
    headers=["Name","Problem","Multiplier"]
    data = []
    for record in pds:
        data.append([record["FinalDiagnosisName"],record["FinalDiagnosisName"],record["Multiplier"]])
    ds = system.dataset.toDataSet(headers, data)
    return ds

def fetchQuantOutputForDiagnosis(FinalDiagnosisName, db=""):
    print "Fetching Final Diagnosis..."
    SQL = "select FD.FinalDiagnosisName, FD.Multiplier "\
        " from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO "\
        " where FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId "\
        " and QO.QuantOutputName = '%s' "\
        " order by FinalDiagnosisName" % (FinalDiagnosisName)
    print SQL
    pds = system.db.runQuery(SQL, database=db)
    print "  ...fetched %i Final Diagnoses..." % (len(pds))
    
    headers=["Name","Problem","Multiplier"]
    data = []
    for record in pds:
        data.append([record["FinalDiagnosisName"],record["FinalDiagnosisName"],record["Multiplier"]])
    ds = system.dataset.toDataSet(headers, data)
    return ds


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

    SQL = "select FD.FinalDiagnosisName, QO.QuantOutputName, RD.RecommendationDefinitionId, R.Recommendation, "\
        " R.AutoRecommendation, R.ManualRecommendation, R.AutoOrManual "\
        " from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO, DtRecommendation R "\
        " where FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
        " and RD.QuantOutputId = QO.QuantOutputId" \
        " and RD.RecommendationDefinitionId = R.RecommendationDefinitionId "\
        " and FD.FinalDiagnosisName in ('%s')" \
        " and QO.QuantOutputName in ('%s')" % (fdNames, outputNames)
    
    print SQL
    pds = system.db.runQuery(SQL, database=db)
    print "  ...fetched %i recommendations!"
    
    headers=["DiagnosisId","OutputId","Auto"]
    data = []
    for record in pds:
        finalDiagnosisName = record["FinalDiagnosisName"]
        quantOutputName = record["QuantOutputName"]
        recommendation = record["Recommendation"]
        
        diagnosisIdx=lookupIdx(diagnoses, "Name", finalDiagnosisName)
        outputIdx=lookupIdx(outputs, "Name", quantOutputName)
        data.append([diagnosisIdx, outputIdx, recommendation])
        
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

# Final Diagnosis callbacks
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

def sqcPlot(theMap, finalDiagnosisIdx):
    print "In sqcPlot..."

def changeMultiplier(theMap, finalDiagnosisIdx):
    print "In changeMultiplier..."

# Quant Output callbacks
def hideOutput(theMap, outputIdx):
    print "In hideOutput..."

def expandOutput(theMap, outputIdx):
    print "In expandOutput..."

# Recommendation callbacks
def manualRecommendation(theMap, diagnosisIdx, outputIdx):
    print "In manualRecommendation..."

# Callback Helpers
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
    
    