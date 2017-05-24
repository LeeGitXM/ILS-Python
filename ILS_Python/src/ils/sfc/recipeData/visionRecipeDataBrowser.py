'''
Created on Feb 1, 2017

@author: phass
'''

import system
from ils.common.cast import toBit
from ils.common.error import catch
from ils.sfc.recipeData.core import fetchRecipeDataTypeId
log=system.util.getLogger("com.ils.sfc.visionEditor")

# The chart path is passed as a property when the window is opened.  Look up the chartId, refresh the Steps table and clear the RecipeData Table
def internalFrameOpened(rootContainer, db=""):
    print "In internalFrameOpened"
    chartId = rootContainer.getPropertyValue("chartId")
    print "Chart Id: ", chartId
    updateSteps(rootContainer, chartId, db)
    recipeDataTable = rootContainer.getComponent("Recipe Data")
    clearRecipeDataTable(recipeDataTable)

# Refresh the recipe data table, we could be coming back from one of the editors.
def internalFrameActivated(rootContainer, db=""):
    print "In internalFrameActivated"
    stepTable = rootContainer.getComponent("Steps")
    recieDataTable = rootContainer.getComponent("Recipe Data")
    if stepTable.selectedRow >= 0:
        print "...updating the recipe data table..."
        updateRecipeData(rootContainer, db)
    
def updateSteps(rootContainer, chartId, db=""):
    print "Updating the list of steps..."
    
    SQL = "select StepName, StepType, StepId from SfcStepView where ChartId = %s order by stepName" % (str(chartId))
    
    SQL = " select S.StepName, T.StepType, S.StepId, "\
        "(select COUNT(*) from SfcRecipeData D where D.StepId = S.StepId) as myRefs "\
        " from SfcStep S, SfcStepType T "\
        " where S.StepTypeId = T.StepTypeId "\
        " and S.ChartId = %s order by stepName" % (str(chartId))
    
    pds = system.db.runQuery(SQL, db)
    
    stepList = rootContainer.getComponent("Steps")
    stepList.data = pds

def updateRecipeData(rootContainer, db=""):
    print "**Updating the recipe data table**..."
    stepTable = rootContainer.getComponent("Steps")
    recipeDataTable = rootContainer.getComponent("Recipe Data")
    
    if stepTable.selectedRow < 0:
        clearRecipeDataTable(recipeDataTable)
    else:
        ds = stepTable.data
        stepId = ds.getValueAt(stepTable.selectedRow, "StepId")
        
        SQL = "select * from SfcRecipeDataView where StepId = %s order by RecipeDataKey" % (str(stepId))
        print SQL
        pds = system.db.runQuery(SQL, db)
        
        ds = pds
        row = 0
        for record in pds:
            recipeDataId = record["RecipeDataId"]
            recipeDataType = record["RecipeDataType"]
            print "Looking at %s - %s" % (recipeDataId, recipeDataType)
            
            if recipeDataType == "Simple Value":
                SQL = "select * from SfcRecipeDataSimpleValueView"
                valuePDS = system.db.runQuery(SQL, db)
                if len(valuePDS) == 1:
                    valueRecord = valuePDS[0]
                    desc = getDescriptionFromRecord(valueRecord)
                    ds = system.dataset.setValue(ds, row, "Description", desc)    
            row = row + 1
            
        recipeDataTable.data = ds

def getDescriptionFromRecord(record):
    desc = record["Description"]
    valueType = record["ValueType"]
    
    if valueType == "String":
        val = record["StringValue"]
    elif valueType == "Float":
        val = record["FloatValue"]
    elif valueType == "Integer":
        val = record["IntegerValue"]
    elif valueType == "Boolean":
        val = record["BooleanValue"]
        if val == 1:
            val = "True"
        else:
            val = "False"
    
    if desc == "":
        desc = "%s" % (str(val))
    else:
        desc = "%s, %s" % (desc, str(val))

    print "Returning description: ", desc
    return desc
    
def clearRecipeDataTable(recipeDataTable):
    print "Clearing table"
    ds = recipeDataTable.data
    rows=[]
    for i in range(0, ds.rowCount):
        rows.append(i)
    ds = system.dataset.deleteRows(ds, rows)
    recipeDataTable.data = ds
    
def deleteRecipeData(rootContainer, db=""):
    print "Deleting a recipe data..."

    recipeDataTable = rootContainer.getComponent("Recipe Data")
    
    if recipeDataTable.selectedRow < 0:
        system.gui.messageBox("Please select a row from the Recie Data table.")
        return
    
    ds = recipeDataTable.data
    recipeDataId = ds.getValueAt(recipeDataTable.selectedRow, "RecipeDataId")
    
    # The recipe data tables all have cascade delete foreign keys so we just need to delete from the main table
    SQL = "delete from SfcRecipeData where RecipeDataId = %d" % (recipeDataId)
    print SQL
    system.db.runUpdateQuery(SQL, db)
    
    # Update the table
    updateRecipeData(rootContainer, db)