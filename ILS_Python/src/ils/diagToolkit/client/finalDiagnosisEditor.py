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
    print "Fetched %d outputs for this application." % (len(availableOutputPds))
    
    selectedOutputPds = fetchOutputNamesForFinalDiagnosisId(finalDiagnosisId, db)
    selectedOutputDs = system.dataset.toDataSet(selectedOutputPds)
    print "Fetched %d outputs for this final diagnosis." % (len(selectedOutputPds))
    
    ''' Remove the used outputs from the available outputs '''
    
    for row in range(selectedOutputDs.rowCount):
        outputName = selectedOutputDs.getValueAt(row, 0)
        
        for availableRow in range(availableOutputDs.rowCount):
            if outputName == availableOutputDs.getValueAt(availableRow, 0):
                print "--- found the row to remove ---"
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
    log.infof("In %s.selec()", __name__)
    db = getDatabaseClient()
    rootContainer = event.source.parent
    finalDiagnosisId = rootContainer.finalDiagnosisId
    
    SQL = "update DtFinalDiagnosis set FinalDiagnosisLabel=?, FinalDiagnosisPriority=?, Comment=?, Explanation=?, TextRecommendation=?, "\
        " CalculationMethod=?, RefreshRate=?, PostProcessingCallback=?, Constant=?, ShowExplanationWithRecommendation=?, "\
        " TrapInsignificantRecommendations=?, PostTextRecommendation=?, ManualMoveAllowed=? "\
        "WHERE FinalDiagnosisId=?"

    values = [rootContainer.finalDiagnosisLabel, rootContainer.finalDiagnosisPriority, rootContainer.comment, rootContainer.explanation, 
              rootContainer.explanation, rootContainer.calculationMethod, rootContainer.refreshRate, rootContainer.postProcessingCallback,
              rootContainer.constant, rootContainer.showExplanationWithRecommendation, rootContainer.trapInsignificantRecommendations,
              rootContainer.postTextRecommendation, rootContainer.manualMoveAllowed,
              finalDiagnosisId]

    rows = system.db.runPrepUpdate(SQL, values, database=db)
    print "Updated %d rows" % (rows) 
    
    SQL = "delete from DtRecommendationDefinition where FinalDiagnosisId = %d" % (finalDiagnosisId)
    rows = system.db.runUpdateQuery(SQL, database=db)
    print "...deleted %d existing recommendation definitions..." % (rows)
    
    selectedOutputDs = rootContainer.selectedOutputs
    for row in range(selectedOutputDs.rowCount):
        outputName = selectedOutputDs.getValueAt(row, 0)    
        outputId = selectedOutputDs.getValueAt(row, 1)
        SQL = "Insert into DtRecommendationDefinition(FinalDiagnosisId, QuantOutputId) values (?,?)"
        system.db.runPrepUpdate(SQL, [finalDiagnosisId, outputId], database=db)
        print "Inserted ", outputName
    log.infof("Inserted %d outputs", selectedOutputDs.rowCount)
    
    
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
    