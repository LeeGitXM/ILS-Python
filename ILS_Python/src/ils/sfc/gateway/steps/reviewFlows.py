'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties):    
    from ils.sfc.gateway.util import createWindowRecord, sendOpenWindow, getStepId, getControlPanelId,\
    getStepProperty, waitOnResponse, deleteAndSendClose
    from ils.sfc.gateway.api import s88Set, getDatabaseName, getProject
    from ils.sfc.common.util import isEmpty
    from system.ils.sfc import getReviewFlows, getReviewFlowsConfig
    from system.ils.sfc.common.Constants import BUTTON_KEY, BUTTON_KEY_LOCATION, BUTTON_LABEL,  VALUE, \
    AUTO_MODE, AUTOMATIC, OK, DATA, REVIEW_FLOWS, HEADING1, HEADING2, HEADING3, POSITION, SCALE, WINDOW_TITLE
    import system.db
    chartScope = scopeContext.getChartScope() 
    stepScope = scopeContext.getStepScope()
    autoMode = getStepProperty(stepProperties, AUTO_MODE) 
    if autoMode == AUTOMATIC:   
        # nothing to do? why even have autoMode ?
        return
    
    database = getDatabaseName(chartScope)
    controlPanelId = getControlPanelId(chartScope)
    buttonLabel = getStepProperty(stepProperties, BUTTON_LABEL) 
    if isEmpty(buttonLabel):
        buttonLabel = 'Flows'
    position = getStepProperty(stepProperties, POSITION) 
    scale = getStepProperty(stepProperties, SCALE) 
    title = getStepProperty(stepProperties, WINDOW_TITLE) 
    heading1 = getStepProperty(stepProperties, HEADING1) 
    heading2 = getStepProperty(stepProperties, HEADING2) 
    heading3 = getStepProperty(stepProperties, HEADING3) 
    windowId = createWindowRecord(controlPanelId, 'SFC/ReviewFlows', buttonLabel, position, scale, title, database)
    stepId = getStepId(stepProperties) 
    system.db.runUpdateQuery("insert into SfcReviewFlows (windowId, heading1, heading2, heading3) values ('%s', '%s', '%s', '%s')" % (windowId, heading1, heading2, heading3), database)

    # add table data
    configJson = getStepProperty(stepProperties, REVIEW_FLOWS) 
    configDataset = getReviewFlows(chartScope, stepScope, configJson)  
    for row in range(configDataset.rowCount):
        addData(windowId, configDataset, row, True, database)
 
    sendOpenWindow(chartScope, windowId, stepId, database)

    response = waitOnResponse(windowId, chartScope)
    responseButton = response[VALUE]
    recipeKey = getStepProperty(stepProperties, BUTTON_KEY)
    recipeLocation = getStepProperty(stepProperties, BUTTON_KEY_LOCATION)
    s88Set(chartScope, stepScope, recipeKey, responseButton, recipeLocation)
    
    if responseButton == OK:
        config = getReviewFlowsConfig(configJson) 
        responseDataset = response[DATA]
        for i in range(len(config.rows)):
            configRow = config.rows[i]
            responseFlow1 = responseDataset.getValueAt(i,2)
            s88Set(chartScope, stepScope, configRow.flow1Key, responseFlow1, configRow.destination )
            responseFlow2 = responseDataset.getValueAt(i,3)
            s88Set(chartScope, stepScope, configRow.flow2Key, responseFlow2, configRow.destination )
            sumFlows = configRow.flow3Key.lower() == 'sum'
            if not sumFlows:
                responseFlow3 = responseDataset.getValueAt(i,4)
                s88Set(chartScope, stepScope, configRow.flow3Key, responseFlow3, configRow.destination )

    system.db.runUpdateQuery("delete from SfcReviewFlowsTable where windowId = '%s'" % (windowId), database)
    system.db.runUpdateQuery("delete from SfcReviewFlows where windowId = '%s'" % (windowId), database)
    project = getProject(chartScope)
    deleteAndSendClose(project, windowId, database)

def addData(windowId, dataset, row, isPrimary, database):
    import system.db
    prompt = dataset.getValueAt(row, 0)
    advice = dataset.getValueAt(row, 1)
    flow1 = dataset.getValueAt(row, 2)
    flow2 = dataset.getValueAt(row, 3)
    flow3 = dataset.getValueAt(row, 4)
    units = dataset.getValueAt(row, 5)
    sumFlows = dataset.getValueAt(row, 6)
    if sumFlows:
        flow3 = flow1 + flow2
    system.db.runUpdateQuery("insert into SfcReviewFlowsTable (windowId, rowNum, prompt, advice, data1, data2, data3, units, sumFlows) values ('%s', %d, '%s', '%s', %f, %f, %f, '%s', %d)" % (windowId, row, prompt, advice, flow1, flow2, flow3, units, sumFlows), database)
