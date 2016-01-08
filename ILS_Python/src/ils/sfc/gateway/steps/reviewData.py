'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):    
    from ils.sfc.gateway.util import sendOpenWindow, getTimeoutTime, getStepId, createWindowRecord, \
        getControlPanelId, hasStepProperty, getStepProperty, waitOnResponse, deleteAndSendClose, \
        handleUnexpectedGatewayError
    from ils.sfc.gateway.api import s88Set, getDatabaseName, getProject, getChartLogger
    from ils.sfc.common.util import isEmpty 
    from system.ils.sfc.common.Constants import AUTO_MODE, AUTOMATIC, PRIMARY_REVIEW_DATA_WITH_ADVICE, SECONDARY_REVIEW_DATA_WITH_ADVICE, BUTTON_KEY, BUTTON_KEY_LOCATION 
    from ils.sfc.common.constants import PRIMARY_REVIEW_DATA, SECONDARY_REVIEW_DATA, BUTTON_LABEL, \
        POSITION, SCALE, WINDOW_TITLE
    from system.ils.sfc import getReviewData
    import system.db
    
    try:
        chartScope = scopeContext.getChartScope() 
        stepScope = scopeContext.getStepScope()
        chartLogger = getChartLogger(chartScope)
        autoMode = getStepProperty(stepProperties, AUTO_MODE) 
        if autoMode == AUTOMATIC:   
            # nothing to do? why even have autoMode ?
            return
        
        showAdvice = hasStepProperty(stepProperties, PRIMARY_REVIEW_DATA_WITH_ADVICE)
        if showAdvice:
            primaryConfigJson = getStepProperty(stepProperties, PRIMARY_REVIEW_DATA_WITH_ADVICE) 
            secondaryConfigJson = getStepProperty(stepProperties, SECONDARY_REVIEW_DATA_WITH_ADVICE) 
        else:
            primaryConfigJson = getStepProperty(stepProperties, PRIMARY_REVIEW_DATA)        
            secondaryConfigJson = getStepProperty(stepProperties, SECONDARY_REVIEW_DATA)        
    
        database = getDatabaseName(chartScope)
        controlPanelId = getControlPanelId(chartScope)
        buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
        if isEmpty(buttonLabel):
            buttonLabel = 'Review'
        position = getStepProperty(stepProperties, POSITION) 
        scale = getStepProperty(stepProperties, SCALE) 
        title = getStepProperty(stepProperties, WINDOW_TITLE) 
        windowId = createWindowRecord(controlPanelId, 'SFC/ReviewData', buttonLabel, position, scale, title, database)
        stepId = getStepId(stepProperties) 
        system.db.runUpdateQuery("insert into SfcReviewData (windowId, showAdvice) values ('%s', %d)" % (windowId, showAdvice), database)
        primaryDataset = getReviewData(chartScope, stepScope, primaryConfigJson, showAdvice)
        for row in range(primaryDataset.rowCount):
            addData(windowId, primaryDataset, row, True, showAdvice, database)
        secondaryDataset = getReviewData(chartScope, stepScope, secondaryConfigJson, showAdvice)
        for row in range(secondaryDataset.rowCount):
            addData(windowId, secondaryDataset, row, False, showAdvice, database)
        sendOpenWindow(chartScope, windowId, stepId, database)
        
        timeoutTime = getTimeoutTime(chartScope, stepProperties)
        responseValue = waitOnResponse(windowId, chartScope, timeoutTime)
        
        recipeKey = getStepProperty(stepProperties, BUTTON_KEY)
        recipeLocation = getStepProperty(stepProperties, BUTTON_KEY_LOCATION)
        s88Set(chartScope, stepScope, recipeKey, responseValue, recipeLocation )
    
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in cancel.py', chartLogger)
    finally:
        system.db.runUpdateQuery("delete from SfcReviewDataTable where windowId = '%s'" % (windowId), database)
        system.db.runUpdateQuery("delete from SfcReviewData where windowId = '%s'" % (windowId), database)
        project = getProject(chartScope)
        deleteAndSendClose(project, windowId, database)
         
def addData(windowId, dataset, row, isPrimary, showAdvice, database):
    import system.db
    from ils.sfc.gateway.util import dbStringForString, dbStringForFloat
    data = dataset.getValueAt(row, 0)
    if showAdvice:
        advice = dataset.getValueAt(row, 1)
        value = dataset.getValueAt(row, 2)
        units = dataset.getValueAt(row, 3)
    else:
        advice = ''
        value = dataset.getValueAt(row, 1)
        units = dataset.getValueAt(row, 2)
    system.db.runUpdateQuery("insert into SfcReviewDataTable (windowId, data, advice, value, units, isPrimary) values ('%s', %s, %s, %s, %s, %d)" % (windowId, dbStringForString(data), dbStringForString(advice), dbStringForFloat(value), dbStringForString(units), isPrimary), database)
