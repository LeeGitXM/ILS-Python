'''
Created on Apr 15, 2022

@author: ils
'''

import system
from ils.common.config import getDatabaseClient
from ils.diagToolkit.common import fetchApplicationId, \
    fetchOutputNamesForApplication,\
    fetchOutputNamesForFinalDiagnosisId

from ils.log import getLogger
log = getLogger(__name__)

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()", __name__)
    rootContainer = event.source.rootContainer
    refresh(rootContainer)
    
def refresh(rootContainer):
    log.infof("In %s.refresh()", __name__)
    db = getDatabaseClient()
    
    applicationName = rootContainer.applicationName
    applicationId = fetchApplicationId(applicationName, db)
    rootContainer.applicationId = applicationId
    
    finalDiagnosisId = rootContainer.finalDiagnosisId
    
    SQL = "select FinalDiagnosisName, FinalDiagnosisLabel, Comment, Explanation, TextRecommendation, CalculationMethod, FinalDiagnosisPriority, "\
        "RefreshRate, PostProcessingCallback, Constant, ShowExplanationWithRecommendation, TrapInsignificantRecommendations, PostTextRecommendation, "\
        "ManualMoveAllowed "\
        "FROM DtFinalDiagnosis "\
        "WHERE FinalDiagnosisId = %d" % (finalDiagnosisId)
    pds = system.db.runQuery(SQL, database=db)
    
    if len(pds) == 0:
        system.gui.messageBox("Error fetching details for final diagnosis with id = %s" % str(finalDiagnosisId))
        return 
    
    record = pds[0]
    
    rootContainer.finalDiagnosisName = record["FinalDiagnosisName"]
    rootContainer.finalDiagnosisLabel = record["FinalDiagnosisLabel"]
    rootContainer.comment = record["Comment"]
    rootContainer.explanation = record["Explanation"]
    rootContainer.textRecommendation = record["TextRecommendation"]
    rootContainer.calculationMethod = record["CalculationMethod"]
    rootContainer.finalDiagnosisPriority = record["FinalDiagnosisPriority"]
    rootContainer.refreshRate = record["RefreshRate"]
    rootContainer.postProcessingCallback = record["PostProcessingCallback"]
    rootContainer.constant = record["Constant"]
    rootContainer.showExplanationWithRecommendation = record["ShowExplanationWithRecommendation"]
    rootContainer.trapInsignificantRecommendations = record["TrapInsignificantRecommendations"]
    rootContainer.postTextRecommendation = record["PostTextRecommendation"]
    rootContainer.manualMoveAllowed = record["ManualMoveAllowed"]
    
    '''
    Fetch the quant outputs and update the lists
    '''
    availableOutputPds = fetchOutputNamesForApplication(applicationName, db)
    availableOutputDs = system.dataset.toDataSet(availableOutputPds)
    log.infof("Fetched %d outputs for this application.", len(availableOutputPds))
    
    selectedOutputPds = fetchOutputNamesForFinalDiagnosisId(finalDiagnosisId, db)
    selectedOutputDs = system.dataset.toDataSet(selectedOutputPds)
    log.infof( "Fetched %d outputs for this final diagnosis.", len(selectedOutputPds))
    
    ''' Remove the used outputs from the available outputs '''
    
    for row in range(selectedOutputDs.rowCount):
        outputName = selectedOutputDs.getValueAt(row, 0)
        
        for availableRow in range(availableOutputDs.rowCount):
            if outputName == availableOutputDs.getValueAt(availableRow, 0):
                log.infof("--- found the row to remove ---")
                availableOutputDs = system.dataset.deleteRow(availableOutputDs, availableRow)
                break

    rootContainer.availableOutputs = availableOutputDs
    rootContainer.selectedOutputs = selectedOutputDs

def saveCallback(event):
    log.infof("In %s.saveCallback()", __name__)
    save(event)
    system.nav.closeParentWindow(event)

def applyCallback(event):
    log.infof("In %s.applyCallback()", __name__)
    save(event)

def save(event):
    '''
    We can't create or delete Final Diagnosis in the Vision client, that can only be done in Designer in the 
    Symbolic Ai context.  We also cannot rename a Final Diagnosis - that also can only happen in Designer.
    '''
    log.infof("In %s.save()", __name__)
    db = getDatabaseClient()
    rootContainer = event.source.parent
    finalDiagnosisId = rootContainer.finalDiagnosisId
    
    log.infof("Updating DtFinalDiagnosis...")
    SQL = "update DtFinalDiagnosis set FinalDiagnosisLabel=?, FinalDiagnosisPriority=?, Comment=?, Explanation=?, TextRecommendation=?, "\
        " CalculationMethod=?, RefreshRate=?, PostProcessingCallback=?, Constant=?, ShowExplanationWithRecommendation=?, "\
        " TrapInsignificantRecommendations=?, PostTextRecommendation=?, ManualMoveAllowed=? "\
        "WHERE FinalDiagnosisId=?"

    values = [rootContainer.finalDiagnosisLabel, rootContainer.finalDiagnosisPriority, rootContainer.comment, rootContainer.explanation, 
              rootContainer.textRecommendation, rootContainer.calculationMethod, rootContainer.refreshRate, rootContainer.postProcessingCallback,
              rootContainer.constant, rootContainer.showExplanationWithRecommendation, rootContainer.trapInsignificantRecommendations,
              rootContainer.postTextRecommendation, rootContainer.manualMoveAllowed,
              finalDiagnosisId]

    rows = system.db.runPrepUpdate(SQL, values, database=db)
    log.infof("...updated %d rows!", rows)
    
    ''' 
    For the list of outputs, we only want to process changes.  So get the list of currently assigned outputs and then compare it to what 
    is defined in the editor.
    '''
    log.infof("Fetching outputs current assigned in the database...")
    SQL = "select upper(QO.QuantOutputName) QuantOutputName, RecommendationDefinitionId "\
        " from DtRecommendationDefinition RD, DtQuantOutput QO "\
        " where RD.QuantOutputId = QO.QuantOutputId "\
        " and RD.FinalDiagnosisId = %d "\
        " order by QuantOutputName"  % (finalDiagnosisId)
    
    pds = system.db.runQuery(SQL, database=db)
    log.tracef("...fetched %d outputs...", len(pds))
    outputList = []
    for record in pds:       
        outputList.append(str(record["QuantOutputName"]))
    
    log.infof("The existing outputs are: %s", str(outputList))
    
    ''' Check for newly added outputs '''
    selectedOutputDs = rootContainer.selectedOutputs
    newOutputList = []
    for row in range(selectedOutputDs.rowCount):
        outputName = str(selectedOutputDs.getValueAt(row, 0))
        newOutputList.append(outputName)   
        outputId = selectedOutputDs.getValueAt(row, 1)
        if outputName not in outputList:
            SQL = "Insert into DtRecommendationDefinition(FinalDiagnosisId, QuantOutputId) values (?,?)"
            system.db.runPrepUpdate(SQL, [finalDiagnosisId, outputId], database=db)
            log.infof("...inserted %s", outputName)
    
    ''' Check for deleted outputs '''
    for record in pds:
        outputName = record["QuantOutputName"]
        if outputName not in newOutputList:
            recommendationDefinitionId = record["RecommendationDefinitionId"]
            
            SQL = "Delete from DtRecommendation where RecommendationDefinitionId = ?"
            system.db.runPrepUpdate(SQL, [recommendationDefinitionId], database=db)
            
            SQL = "Delete from DtRecommendationDefinition where RecommendationDefinitionId = ?"
            system.db.runPrepUpdate(SQL, [recommendationDefinitionId], database=db)
            log.infof("...deleted %s", outputName)

    
def selectOutputCallback(event):
    ''' This is called when they press the RIGHT ARROW button to move the selected output from the left list to the right list '''
    log.infof("In %s.selectOutputCallback()", __name__)
    rootContainer = event.source.parent
    
    ''' Get info about the selected output in the available list and remove it from the list '''
    availableOutputDs = rootContainer.availableOutputs
    row = rootContainer.getComponent("Available Outputs List").selectedIndex
    outputName = availableOutputDs.getValueAt(row, 0)
    outputId = availableOutputDs.getValueAt(row, 1)
    availableOutputDs = system.dataset.deleteRow(availableOutputDs, row)
    rootContainer.availableOutputs = availableOutputDs
    
    ''' Add the selected row in the left list to the right list '''
    selectedOutputDs = rootContainer.selectedOutputs
    selectedOutputDs = system.dataset.addRow(selectedOutputDs, [outputName, outputId])
    selectedOutputDs = system.dataset.sort(selectedOutputDs, 0)
    rootContainer.selectedOutputs = selectedOutputDs

def unselectOutputCallback(event):
    ''' This is called when they press the LEFT ARROW button to move the selected output from the right list to the left list '''
    log.infof("In %s.unselectOutputCallback()", __name__)
    rootContainer = event.source.parent
    
    ''' Get info about the selected output in the selected list (the right one) and remove it from the list '''
    selectedOutputDs = rootContainer.selectedOutputs
    row = rootContainer.getComponent("Selected Outputs List").selectedIndex
    outputName = selectedOutputDs.getValueAt(row, 0)
    outputId = selectedOutputDs.getValueAt(row, 1)
    selectedOutputDs = system.dataset.deleteRow(selectedOutputDs, row)
    rootContainer.selectedOutputs = selectedOutputDs
    
    ''' Add the selected row in the right list to the leftt list '''
    availableOutputDs = rootContainer.availableOutputs
    availableOutputDs = system.dataset.addRow(availableOutputDs, [outputName, outputId])
    availableOutputDs = system.dataset.sort(availableOutputDs, 0)
    rootContainer.availableOutputs = availableOutputDs
    