'''
Created on Dec 17, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, deactivate):    
    from ils.sfc.gateway.util import sendOpenWindow, getTimeoutTime, getStepId, createWindowRecord, \
        getControlPanelId, hasStepProperty, getStepProperty,  handleUnexpectedGatewayError
    from ils.sfc.gateway.api import s88Set, getDatabaseName, getChartLogger
    from ils.sfc.common.util import isEmpty 
    from system.ils.sfc.common.Constants import AUTO_MODE, AUTOMATIC, \
    PRIMARY_REVIEW_DATA_WITH_ADVICE, SECONDARY_REVIEW_DATA_WITH_ADVICE
    from ils.sfc.common.constants import PRIMARY_REVIEW_DATA, SECONDARY_REVIEW_DATA, BUTTON_LABEL, \
        POSITION, SCALE, WINDOW_TITLE, BUTTON_KEY_LOCATION, BUTTON_KEY
    from system.ils.sfc import getReviewData
    from ils.sfc.common.constants import WAITING_FOR_REPLY, TIMEOUT_TIME, TIMEOUT_RESPONSE, WINDOW_ID
    from ils.sfc.gateway.util import checkForResponse
    import system.db
    
    try:
        chartScope = scopeContext.getChartScope() 
        stepScope = scopeContext.getStepScope()
        chartLogger = getChartLogger(chartScope)
        
        
        workDone = False
        waitingForReply = stepScope.get(WAITING_FOR_REPLY, False);
        if not waitingForReply:
            autoMode = getStepProperty(stepProperties, AUTO_MODE) 
            if autoMode == AUTOMATIC:   
                # nothing to do? why even have autoMode ?
                return           
            stepScope[WAITING_FOR_REPLY] = True
            timeoutTime = getTimeoutTime(chartScope, stepProperties)
            stepScope[TIMEOUT_TIME] = timeoutTime
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
            stepScope[WINDOW_ID] = windowId
            stepId = getStepId(stepProperties) 
            system.db.runUpdateQuery("insert into SfcReviewData (windowId, showAdvice) values ('%s', %d)" % (windowId, showAdvice), database)
            primaryDataset = getReviewData(chartScope, stepScope, primaryConfigJson, showAdvice)
            for row in range(primaryDataset.rowCount):
                addData(windowId, primaryDataset, row, True, showAdvice, database)
            secondaryDataset = getReviewData(chartScope, stepScope, secondaryConfigJson, showAdvice)
            for row in range(secondaryDataset.rowCount):
                addData(windowId, secondaryDataset, row, False, showAdvice, database)
            sendOpenWindow(chartScope, windowId, stepId, database)
        else:
            response = checkForResponse(chartScope, stepScope, stepProperties, TIMEOUT_RESPONSE)                
            if response != None: 
                print 'getting location/key'
                recipeLocation = getStepProperty(stepProperties, BUTTON_KEY_LOCATION) 
                key = getStepProperty(stepProperties, BUTTON_KEY) 
                print 'b4 s88Set location', recipeLocation
                s88Set(chartScope, stepScope, key, response, recipeLocation)
                print 'after s88Set'
                workDone = True    
    except:
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in reviewData.py', chartLogger)
        workDone = True
    finally:
        if workDone:
            cleanup(chartScope, stepScope)
        return workDone
         
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
    system.db.runUpdateQuery("insert into SfcReviewDataTable (windowId, rowNum, data, advice, value, units, isPrimary) values ('%s', %d, %s, %s, %s, %s, %d)" % (windowId, row, dbStringForString(data), dbStringForString(advice), dbStringForFloat(value), dbStringForString(units), isPrimary), database)

def cleanup(chartScope, stepScope):
    import system.db
    from ils.sfc.gateway.util import deleteAndSendClose, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getDatabaseName, getProject, getChartLogger
    from ils.sfc.common.constants import WINDOW_ID
    try:
        database = getDatabaseName(chartScope)
        project = getProject(chartScope)
        windowId = stepScope.get(WINDOW_ID, '???')
        system.db.runUpdateQuery("delete from SfcReviewDataTable where windowId = '%s'" % (windowId), database)
        system.db.runUpdateQuery("delete from SfcReviewData where windowId = '%s'" % (windowId), database)
        project = getProject(chartScope)
        deleteAndSendClose(project, windowId, database)
    except:
        chartLogger = getChartLogger(chartScope)
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in cleanup in reviewData.py', chartLogger)
