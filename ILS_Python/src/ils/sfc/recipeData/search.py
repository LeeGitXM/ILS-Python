'''
Created on Feb 12, 2020

@author: phass
'''

import system, string
from ils.common.config import getDatabaseClient
from ils.sfc.recipeData.hierarchyWithBrowser import deleteRecipeData, deleteRecipeDataGroup
from ils.common.util import clearDataset

log = system.util.getLogger("ils.client.ui")

def internalFrameOpened(rootContainer):
    '''
    TODO - the clearDataset call is new to 7.9.7.  Once all of the systems reach this point then uncomment.
    '''
    log.infof("In %s.internalFrameOpened", __name__)
    
    ''' Clear all of the fields and tables and select the Search By Key tab '''
    container = rootContainer.getComponent("Search By Key Container")
    container.getComponent("Key Field").text = ""
    table = container.getComponent("Power Table")

    ds = table.data
    #ds = system.dataset.clearDataset(ds)
    table.data = ds
    
    container = rootContainer.getComponent("List Container")
    table = container.getComponent("Power Table")
    ds = table.data
    #ds = system.dataset.clearDataset(ds)
    table.data = ds
    
    tabStrip = rootContainer.getComponent("Tab Strip")
    tabStrip.selectedTab = "Search by Key"

    
def searchForKeyCallback(container):
    log.infof("In %s.searchForKeyCallback", __name__)
    db = getDatabaseClient()
    key = container.getComponent("Key Field").text
    
    SQL = "select RecipeDataId, StepId, RecipeDataFolderId, RecipeDataKey, ChartPath, StepName, RecipeDataType from SfcRecipeDataView "\
        "where RecipeDataKey like '%s' "\
        "order by RecipeDataKey " % (key)

    pds = system.db.runQuery(SQL, db)
    
    table = container.getComponent("Power Table")
    table.data = pds
    
    system.gui.messageBox("Found %d references" % (len(pds)))
    
    
def refreshRecipeDataListCallback(event):
    log.infof("In %s.listRecipeDataCallback", __name__)
    
    container = event.source.parent
    table = container.getComponent("Power Table")
    system.db.refresh(table, "data")
    
# chartIds are resource Ids of charts to consider
def getSearchResults(chartIds):
    print "Fetching recipe data to be used for searching" 
    recipeData = []
    return recipeData

    
def editCallback(event):
    log.infof("In %s.editCallback()...", __name__)
    stepId, recipeDataType, recipeDataId, recipeDataKey, recipeDataFolderId = getSelectedInfo(event)
    window = system.nav.openWindowInstance('SFC/RecipeDataEditor', {'stepId':stepId, 'recipeDataType':recipeDataType, 'recipeDataId':recipeDataId, 'recipeDataKey':recipeDataKey, "recipeDataFolderId":recipeDataFolderId})
    system.nav.centerWindow(window)

    
def deleteCallback(event):
    log.infof("In %s.deleteCallback()...", __name__)
    db = getDatabaseClient()
    
    stepId, recipeDataType, recipeDataId, recipeDataKey, recipeDataFolderId = getSelectedInfo(event)
    deleteRecipeData(recipeDataType, recipeDataId, db)
    refreshRecipeDataListCallback(event)


def deleteFolderCallback(event):
    log.infof("In %s.deleteFolderCallback()...", __name__)
    db = getDatabaseClient()
    
    container = event.source.parent
    table = container.getComponent("Power Table")
    selectedRow = table.selectedRow
    ds = table.data
    recipeDataFolderId = ds.getValueAt(selectedRow,"RecipeDataFolderId")
    
    deleteRecipeDataGroup(recipeDataFolderId, db)
    refreshRecipeDataListCallback(event)


def clearCallback(event):
    log.infof("In %s.clearCallback()...", __name__)    
    container = event.source.parent
    table = container.getComponent("Power Table")
    ds = table.data
    ds = clearDataset(ds)
    table.data = ds


def getSelectedInfo(event):
    container = event.source.parent
    table = container.getComponent("Power Table")
    selectedRow = table.selectedRow
    ds = table.data
    
    stepId = ds.getValueAt(selectedRow,"StepId")
    recipeDataType = ds.getValueAt(selectedRow,"RecipeDataType")
    recipeDataId = ds.getValueAt(selectedRow,"RecipeDataId")
    recipeDataKey = ds.getValueAt(selectedRow,"RecipeDataKey")
    recipeDataFolderId = ds.getValueAt(selectedRow,"RecipeDataFolderId")
    
    log.infof("    %s %s, %s %s %s", str(stepId), recipeDataType, str(recipeDataId), recipeDataKey, str(recipeDataFolderId))
    
    return stepId, recipeDataType, recipeDataId, recipeDataKey, recipeDataFolderId


def searchForReferenceCallback(container):
    TEST_MODE = False
    log.infof("In %s.searchForReferenceCallback", __name__)
    db = getDatabaseClient()
    key = container.getComponent("Key Field").text
    log.tracef("Searching for: %s", key)
    
    if TEST_MODE:
        log.tracef("Using a list of TEST chart paths...")
        chartPaths = ["A/A", "A/AA", "A/AB", "A/ABA", "A/ABB"]
    else:
        log.tracef("Searching ALL chart paths...")
        chartPaths = ['%']
        
    searchCandidates = []
    for chartPath in chartPaths:
        searchCandidates = getSearchCandidates(chartPath, searchCandidates, db)
        
    log.tracef("There are %d search candidates", len(searchCandidates))
    
    matches = []
    for searchCandidate in searchCandidates:
        txt = string.upper(searchCandidate.get("TEXT", ""))
        log.tracef("Search candidate: %s",  str(searchCandidate))
        if txt.find(string.upper(key)) > 0:
            log.tracef( "*** FOUND ****")
            matches.append(searchCandidate)
             
    from ils.dataset.util import listOfDictionariesToDataset
    log.infof("Found %d matches", len(matches))
    ds = listOfDictionariesToDataset(matches)
    container.getComponent("Power Table").data = ds


def getSearchResults(chartPath):
    '''
    This is called by the Ignition Find and Replace utility.  Chuck has extended it through Java to support SFCs and this is called if they elect to search for recipe data.
    This needs to return the recipe data for the selected chart as a big text string.
    '''
    log.tracef("In %s.getSearchResults() - searching Chart Path: %s", __name__, chartPath)
    
    ignitionGlobals  = system.util.getGlobals()
    searchResults = ignitionGlobals.get('searchResults', None)
    
    if searchResults == None:
        queryTime = None
    else:
        queryTime = searchResults.get("queryTime", None)

    if queryTime == None or (system.date.secondsBetween(queryTime, system.date.now()) > 60 ):
        
        searchCandidates = []
        searchCandidates = getSearchCandidates("%", searchCandidates)
        log.tracef("Fetched %d **FRESH** search candidates...", len(searchCandidates))
        searchResults = {"queryTime": system.date.now(), "searchCandidates": searchCandidates}
        system.util.getGlobals()['searchResults'] = searchResults
    else:
        searchCandidates = searchResults.get("searchCandidates", None)
        log.tracef("... using %d cached searchCandidates...", len(searchCandidates))
        
    searchCandidatesForThisChart = []
    for searchCandidate in searchCandidates:
        if chartPath == searchCandidate.get("PATH", ""):
            searchCandidatesForThisChart.append(searchCandidate)
    
    log.tracef("Returning: %s", str(searchCandidatesForThisChart))
    return searchCandidatesForThisChart


def getSearchCandidates(chartPath, searchCandidates = [], db=""):
    
    ''' Simple Values '''
    SQL = "select ChartPath, StepName, RecipeDataKey, RecipeDataId, RecipeDataType, Label, Description, Units, ValueType, FolderKey "\
        " from SfcRecipeDataSimpleValueView where ChartPath like '%s' " % (chartPath)
    searchCandidates = sqlRunner(SQL, chartPath,  searchCandidates, db)
    
    ''' Timers '''
    SQL = "select ChartPath, StepName, RecipeDataKey, RecipeDataId, RecipeDataType, Label, Description, Units, TimerState, CumulativeMinutes "\
        " from SfcRecipeDataTimerView where ChartPath like '%s' " % (chartPath)
    searchCandidates = sqlRunner(SQL, chartPath,  searchCandidates, db)
    
    ''' Outputs '''
    SQL = "select ChartPath, StepName, RecipeDataKey, RecipeDataId, RecipeDataType, Label, Description, Tag, Units, ValueType, OutputType, Download,  "\
        " DownloadStatus, ErrorCode, ErrorText, Timing, MaxTiming, ActualTiming, PVMonitorActive, WriteConfirm, FolderKey "\
        " from SfcRecipeDataOutputView where ChartPath like '%s' " % (chartPath)
    searchCandidates = sqlRunner(SQL, chartPath, searchCandidates, db)
    
    ''' Output Ramps '''
    SQL = "select ChartPath, StepName, RecipeDataKey, RecipeDataId, RecipeDataType, Label, Description, Tag, Units, ValueType, OutputType, Download,  "\
        " DownloadStatus, ErrorCode, ErrorText, Timing, MaxTiming, ActualTiming, PVMonitorActive, WriteConfirm, RampTimeMinutes, UpdateFrequencySeconds, FolderKey "\
        " from SfcRecipeDataOutputRampView where ChartPath like '%s' " % (chartPath)
    searchCandidates = sqlRunner(SQL, chartPath, searchCandidates, db)
    
    '''  Inputs '''
    SQL = "select ChartPath, StepName, RecipeDataKey, RecipeDataId, RecipeDataType, Label, Description, Tag, Units, ValueType, PVMonitorActive, FolderKey "\
        " from SfcRecipeDataInputView where ChartPath like '%s' " % (chartPath)
    searchCandidates = sqlRunner(SQL, chartPath, searchCandidates, db)
    
    '''  Arrays '''
    SQL = "select ChartPath, StepName, RecipeDataKey, RecipeDataId, RecipeDataType, Label, Description, Units, ValueType, KeyName, FolderKey "\
        " from SfcRecipeDataArrayView where ChartPath like '%s' " % (chartPath)
    searchCandidates = sqlRunner(SQL, chartPath, searchCandidates, db)
    
    '''  Matrix '''
    SQL = "select ChartPath, StepName, RecipeDataKey, RecipeDataId, RecipeDataType, Label, Description, Units, ValueType, RowIndexKeyName, ColumnIndexKeyName, FolderKey "\
        " from SfcRecipeDataMatrixView where ChartPath like '%s' " % (chartPath)
    searchCandidates = sqlRunner(SQL, chartPath, searchCandidates, db)
    
    '''  Recipe '''
    SQL = "select ChartPath, StepName, RecipeDataKey, RecipeDataId, RecipeDataType, Label, Description, Units, PresentationOrder, StoreTag, CompareTag, "\
        " ModeAttribute, ModeValue, ChangeLevel, RecommendedValue, LowLimit, HighLimit, FolderKey "\
        " from SfcRecipeDataRecipeView where ChartPath like '%s' " % (chartPath)
    searchCandidates = sqlRunner(SQL, chartPath, searchCandidates, db)
    
    '''  SQC '''
    SQL = "select ChartPath, StepName, RecipeDataKey, RecipeDataId, RecipeDataType, Label, Description, Units, LowLimit, "\
        " TargetValue, HighLimit, FolderKey "\
        " from SfcRecipeDataSQCView where ChartPath like '%s' " % (chartPath)
    searchCandidates = sqlRunner(SQL, chartPath, searchCandidates, db)

    return searchCandidates
    

def sqlRunner(SQL, chartPath, searchCandidates, db):
    def dsToTextWithColumnName(ds, row, delimiter):
        txt = ""
        columns = ds.getColumnNames()
        for col in range(ds.getColumnCount()):
            if col > 0:
                txt = txt + delimiter
            txt = str(txt) + columns[col] + "=" + str(ds.getValueAt(row, col))
        return txt
    
    pds = system.db.runQuery(SQL, database=db)
    ds = system.dataset.toDataSet(pds)
    for row in range(ds.getRowCount()):
        txt = dsToTextWithColumnName(ds, row, ",")
        searchCandidate = {"PATH": ds.getValueAt(row,"ChartPath"), "STEP": ds.getValueAt(row,"StepName"), "KEY": ds.getValueAt(row,"RecipeDataKey"), "TEXT": txt}
        searchCandidates.append(searchCandidate)
    
    return searchCandidates
