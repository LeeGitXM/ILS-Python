'''
Created on Dec 29, 2016

@author: phass
'''

import system, string
from ils.common.config import getTagProvider, getDatabase
from ils.common.util import formatDateTimeForDatabase
log = system.util.getLogger("com.ils.sfc.structureManager.python")
parseLog = system.util.getLogger("com.ils.sfc.structureManager.xmlParser")
from ils.common.error import catchError
from ils.sfc.recipeData.core import fetchStepTypeIdFromFactoryId, fetchStepIdFromUUID, fetchChartIdFromChartPath, fetchStepIdFromChartIdAndStepName
from ils.common.database import toList

def getTxId(db):
    txId = system.db.beginTransaction(database=db, timeout=86400000)    # timeout is one day
    return txId

def createChart(resourceId, chartPath, db):
    # Check if the chart already exists 
    log.infof("In %s.createChart() with %s-%s...", __name__, chartPath, str(resourceId))
    
    print "*************************************************"
    print "** WHY AM I HERE????"
    print "*************************************************"
    return

    txId = getTxId(db)    
    print "The transactionId is: ", txId

    try:
        log.tracef("...updating the chartPath <%s> for a record in sfcChart by resourceId: %d...", chartPath, resourceId)
        SQL = "update SfcChart set ChartPath = '%s' where chartResourceId = %d" % (chartPath, resourceId)
        log.tracef(SQL)
        rows = system.db.runUpdateQuery(SQL, tx=txId)
        
        if rows > 0:
            return 
        
        log.tracef("...updating the resourceId <%d> for a record in sfcChart by chartPath <%s>...", resourceId, chartPath)
        SQL = "update SfcChart set chartResourceId = %d where ChartPath = '%s'" % (resourceId, chartPath)
        log.tracef(SQL)
        rows = system.db.runUpdateQuery(SQL, tx=txId)
        
        if rows > 0:
            return
        
        log.tracef("Inserting a new record into SfcChart for %s - %d...", chartPath, resourceId)
        SQL = "insert into SfcChart (ChartPath, chartResourceId, CreateTime) values ('%s', %d, getdate())" % (chartPath, resourceId)
        log.tracef(SQL)
        chartId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
        log.tracef("...inserted %s into SfcChart table and got id: %d", chartPath, chartId)

    except:
        errorTxt = catchError("%s.createChart()")
        log.errorf(errorTxt)

def deleteCharts(resourceMap, db):
    log.infof("Deleting %d charts with database %s...", len(resourceMap), db) 
    
    i = 0
    for resourceId in resourceMap.keySet():
        chartPath = resourceMap.get(resourceId)
        log.infof("Deleting a chart (%s) with resourceId: %d", chartPath, resourceId) 
    
        try:
            SQL = "select chartId, chartPath from SfcChart where chartResourceId = %d" % resourceId
            pds = system.db.runQuery(SQL, database=db)
            
            if len(pds) == 1:
                record = pds[0]
                chartId = record["chartId"]
                chartPath = record["chartPath"]
                log.tracef("...the corresponding chart id / path is: %s / %s", str(chartId), chartPath)

                '''
                If a chart is moved in the project tree then we get a create message for a new resource and then a delete message for the original resource.
                I'd like to update the original record in the database for the new path and resource Id to keep the step catalog intact.  Since there is no connection
                between the create and delete messages, I am going to look for a chart that was just created.  (If a whole folder is moved then there will be n creates 
                followed by n deletes - I am not going to address this.
                '''
                aBit = -15
                aBitAgo = system.date.addSeconds(system.date.now(), aBit)
                dateTimeString = formatDateTimeForDatabase(aBitAgo)
                SQL = "select * from SfcChart where CreateTime > '%s'" % (dateTimeString)
                pds = system.db.runQuery(SQL, database=db)
                
                if len(pds) == 0:
                    i = i + 1
                    log.infof("...deleting chart Id: %d", chartId)
                    
                    SQL = "delete from SfcHierarchy where childChartId = %d" % chartId
                    rows = system.db.runUpdateQuery(SQL, database=db)
                    log.tracef( "...deleted %d children from SfcChartHierarchy...", rows)
                                
                    SQL = "delete from SfcHierarchy where ChartId = %d" % chartId
                    rows = system.db.runUpdateQuery(SQL, database=db)
                    log.tracef( "...deleted %d parents from SfcChartHierarchy...", rows)
        
                    SQL = "delete from SfcChart where chartId = %d" % chartId
                    rows = system.db.runUpdateQuery(SQL, database=db)
                    log.tracef("...deleted %d rows from SfcChart...", rows)
                    
                    SQL = "delete from SfcHierarchyHandler where chartId = %d" % chartId
                    rows = system.db.runUpdateQuery(SQL, database=db)
                    log.tracef("...deleted %d caller rows from SfcHierarchyHandler...", rows)
                    
                    SQL = "delete from SfcHierarchyHandler where HandlerChartId = %d" % chartId
                    rows = system.db.runUpdateQuery(SQL, database=db)
                    log.tracef("...deleted %d handler rows from SfcHierarchyHandler...", rows)
                elif len(pds) == 1:
                    log.infof("...handling a moved / renamed chart...")
                    record = pds[0]
                    newChartPath = record["ChartPath"]
                    newResourceId = record["ChartResourceId"]
                    newChartId = record["ChartId"]
                    print "The New info for this chart is: %s - %s - %s" % (str(newChartId), newChartPath, str(newResourceId))
                    
                    '''
                    Instead of deleting the old record, update it and delete the new one.
                    Need to delete first to avoid a duplicate key error
                    '''
                    
                    SQL = "delete from sfcChart where ChartId = %d" % (newChartId)
                    rows = system.db.runUpdateQuery(SQL, database=db)
                    if rows == 1:
                        log.trace("Successfully deleted the new chart")
                    else:
                        log.errorf("Error deleting the new chart - %s", SQL)
                    
                    SQL = "update SfcChart set ChartResourceId = %d, ChartPath = '%s' where ChartId = %d" % (newResourceId, newChartPath, chartId)
                    rows = system.db.runUpdateQuery(SQL, database=db)
                    if rows == 1:
                        log.trace("Successfully updated the old chart")
                    else:
                        log.errorf("Error updating the old chart - %s", SQL)
                    
                else:
                    log.errorf("I can't handle multiple resource updates")
    
            else:
                '''
                When charts are deleted via the designer, the chartPath doesn't exist so if we can't find it by the resource id then we are screwed!
                '''
                log.errorf("...unable to find the chart by resource id, this chart will need to be manually deleted from SQL*Server...")

        except:
            ''' This will catch the error and then go on to the next chart '''
            txt = "deleting a chart - this chart will need to be manually deleted from SQL*Server (resourceId = %d)" % (resourceId)
            errorTxt = catchError(txt)
            log.errorf(errorTxt)

    log.infof("Done - deleted %d charts!", i)

    
'''
This is only called by Java hook in designer when the user saves the project.  It is passed all of the resources that have been changed since the last time the 
project was saved.
'''
def updateChartHierarchy(parentChartPath, parentResourceId, chartXML):
    log.infof("In %s.updateChartHierarcy() updating the steps and hierarchy for parent: %s", __name__, parentResourceId)
    
    db = getDatabase()
    log.infof("...using production database instance: %s...", db)
    
    log.tracef("The chart XML is: %s", str(chartXML))
    txId = getTxId(db)

    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(chartXML)
        
        steps, children = parseXML(root)
        
        '''
        Determine if the chart exists using the resource Id.  
        If a chart path is changed, the resourceId does not change so update the path.
        '''
        SQL = "select * from SfcChart where ChartResourceId = %d" % (parentResourceId)
        pds =  system.db.runQuery(SQL, tx=txId)
        
        ''' There really shouldn't be a way that the chart is not already inserted... '''
        if len(pds) == 0:
            log.tracef("The chart resource id <%s> did not exist, checking the chart path...", parentResourceId)
            
            SQL = "select * from SfcChart where ChartPath = '%s'" % (parentChartPath)
            pds =  system.db.runQuery(SQL, tx=txId)
            
            if len(pds) == 0:
                log.tracef("...Neither the chart resource id <%s> nor the chart path <%s> exist, the chart must be new...", parentResourceId, parentChartPath)

                SQL = "insert into SfcChart (ChartPath, chartResourceId) values ('%s', %d)" % (parentChartPath, parentResourceId)
                chartId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
                log.tracef("...inserted chart with id: %d", chartId)

            else:
                ''' Update the resource Id '''
                record = pds[0]
                chartId = record["ChartId"]
                log.tracef("Updating the resource id...")
                SQL = "update SfcChart set ChartResourceId = '%s' where ChartPath = '%s'" % (parentResourceId, parentChartPath)
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                log.tracef("...updated %d existing sfcChart by chartPath", rows)
        else:
            record = pds[0]
            chartId = record["ChartId"]
            log.tracef("The chart already exists - path: %s, chart id: %d", parentChartPath, chartId)
            chartPath = record["ChartPath"]
            if chartPath <> parentChartPath:
                log.tracef("Updating the chart path for a renamed chart...")
                SQL = "update SfcChart set ChartPath = '%s' where ChartId = %s" % (parentChartPath, str(chartId))
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                log.tracef("...updated %d existing sfcChart", rows)
        
        '''
        Verify step name uniqueness.
        '''
        log.tracef("------------------")
        log.tracef("Checking that step names are unique...")
        log.tracef("------------------")
        
        ''' Iterate over steps in the chart '''
        stepNames = []
        for step in steps:
            stepTypeId = fetchStepTypeIdFromFactoryId(step["type"], txId)
            stepName = string.upper(step["name"])
            if stepName in stepNames:
                errorTxt = "Error on chart %s - there are two or more steps named: %s" % (chartPath, stepName)
                print errorTxt
                print "RAISING AN EXCEPTION"
                raise Exception(errorTxt)
 
            stepNames.append(stepName)        
        
        '''
        Handle the step catalog - we need this so that we can have a recipe editor.
        '''
        log.tracef("------------------")
        log.tracef("Inserting steps for chart id %d...", chartId)
        log.tracef("------------------")
        
        databaseStepsPds = system.db.runQuery("select * from sfcStep where ChartId = %d" % (chartId), tx=txId)
        stepsInDatabase = []
        stepUUIDsInDatabase = []
        log.tracef("Existing steps:")
        for record in databaseStepsPds:
            log.tracef("  %s", record["StepName"])
            stepsInDatabase.append(string.upper(record["StepName"]))
            stepUUIDsInDatabase.append(str(record["StepUUID"]))
        
        log.tracef("...the UUIDs in the database are: %s", str(stepUUIDsInDatabase))
        
        updateCntr = 0
        insertCntr = 0
        renameCntr = 0
        ''' Iterate over steps in the chart '''
        for step in steps:
            stepTypeId = fetchStepTypeIdFromFactoryId(step["type"], txId)
            stepUUID = step["id"]
            stepName = step["name"]
            stepType = step["type"]
            
            if string.upper(stepName) in stepsInDatabase:
                log.tracef("Step <%s> already exists in database, checking if it needs to be updated...", stepName)
                
                for stepRecord in databaseStepsPds:
                    if string.upper(stepName) == stepRecord["StepName"]:
                        log.tracef("...found the step (name: %s, step type: %s-%s) in the database list...", stepName, stepType, str(stepTypeId))
                        updateIt = False
                        if chartId <> stepRecord["ChartId"]:
                            updateIt = True
                            log.tracef("...the chartId has been changed from %s to %s", str(stepRecord["ChartId"]), str(chartId))
                        if stepTypeId <> stepRecord["StepTypeId"]:
                            log.tracef("...the stepType has been changed from %s to %s", str(stepRecord["StepTypeId"]), str(stepTypeId))
                            updateIt = True
                        if stepName <> stepRecord["StepName"]:
                            log.tracef("...the step has been renamed slightly from %s to %s", stepName, str(stepRecord["StepName"]) )
                            updateIt = True

                        if updateIt:
                            SQL = "update SfcStep set StepName = '%s', StepTypeId = %d, ChartId = %d where StepUUID = '%s'" % (stepName, stepTypeId, chartId, stepUUID)
                            rows = system.db.runUpdateQuery(SQL, tx=txId)
                            log.tracef("...updated %d existing steps", rows)
                            updateCntr = updateCntr + 1
                
                stepsInDatabase.remove(string.upper(step["name"]))
            else:
                ''' Before we insert a new step, see if they renamed a step by using the id '''
                if stepUUID in stepUUIDsInDatabase:
                    log.tracef("-- found a step <%s> that needs to be renamed --", stepName)
                    SQL = "update SfcStep set StepName = '%s', StepTypeId = %d, ChartId = %d where StepUUID = '%s'" % (stepName, stepTypeId, chartId, stepUUID)
                    rows = system.db.runUpdateQuery(SQL, tx=txId)
                    log.tracef("...updated %d existing steps", rows)
                    renameCntr = renameCntr + 1
    
                    if stepName in stepsInDatabase:
                        stepsInDatabase.remove(string.upper(stepName))
                else:
                    log.tracef("Inserting a new step <%s>, a %s with UUID %s into the database...", stepName, stepType, stepUUID)
                    SQL = "insert into SfcStep (StepName, StepUUID, StepTypeId, ChartId) values ('%s', '%s', %d, %d)" % (stepName, stepUUID, stepTypeId, chartId)
                    stepId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
                    log.tracef("...inserted a %s step with id: %d", stepType, stepId)
                    insertCntr = insertCntr + 1

        log.tracef("...%d steps were inserted...", insertCntr)
        log.tracef("...%d steps were renamed...", renameCntr)
        log.tracef("...%d steps were updated...", updateCntr)
                
        log.tracef("Checking for steps to delete from the database that have been deleted from the chart...")
        
        deleteCntr = 0
        for stepName in stepsInDatabase:
            SQL = "delete from SfcStep where StepName = '%s' and ChartId = %d" % (stepName, chartId)
            rows = system.db.runUpdateQuery(SQL, tx=txId)
            deleteCntr = deleteCntr + rows
            if rows <> 1:
                log.warnf("...error deleting step <%s> from SfcStep - %d rows were deleted", stepName, rows)
            else:
                log.infof("Step <%s> was successfully deleted", stepName)

        log.tracef("... %d steps were deleted!", deleteCntr)
        
        '''
        Now handle the chart hierarchy
        '''
        log.tracef("------------------")
        log.tracef("Updating the chart hierarchy with children...")
        log.tracef("the children from parsing the chart XML is: %s", str(children))
        log.tracef("------------------")
        
        # Fetch what is already in the database
        SQL = "Select * from SfcHierarchyView where ChartId = %d" % (chartId)
        childrenInDatabasePds = system.db.runQuery(SQL, tx=txId)
        from ils.common.database import toDictList
        chidrenInDatabaseList = toDictList(childrenInDatabasePds, [])
        log.tracef("...found %d children already in the database...", len(chidrenInDatabaseList))

        childInsertCntr = 0
        childUpdateCntr = 0
        for child in children:
            stepName = child.get("name")
            childPath = child.get("childPath")
            stepUUID = child.get("id") 
            stepType = child.get("type")
            log.tracef("----------------------------")
            log.tracef("Checking stepName: %s, childPath: %s, stepUUID: %s, step type: %s...", stepName, childPath, stepUUID, stepType)
            
            '''
            Compare the stepName and childPath from the Designer with what is already in the database
            '''
            insertChild = True
            for childDatabase in chidrenInDatabaseList:
                log.tracef("...comparing to %s - %s", childDatabase["StepName"], childDatabase["ChildChartPath"])
                if stepName == childDatabase["StepName"]:
                 
                    insertChild = False
                    if childPath == childDatabase["ChildChartPath"]:
                        log.tracef("...this child already exists...")
                    else:
                        log.tracef("...this child already exists but is calling a different chart...")
                        childChartId = fetchChartIdFromChartPath(child.get("childPath"), txId)
                        log.tracef("...the new child chart Id is: %s", str(childChartId))
                        if childChartId == None:
                            log.errorf("Id not found for child chart, it will be created later hopefully,  with path: %s", child.get("childPath"))
                        
                        else:
                            stepId = fetchStepIdFromChartIdAndStepName(chartId, stepName, txId)
                            log.tracef("The step id of the child step named %s on chart %s is: %s", stepName, str(chartId), str(stepId))

                            SQL = "Update SfcHierarchy set ChildChartId = %d where StepId = %d" % (childChartId, stepId)
                            log.tracef("SQL: %s", SQL)
                            system.db.runUpdateQuery(SQL, tx=txId)
                            log.tracef("...updated %d calls %d into sfcHierarchy", stepId, childChartId) 
                            childUpdateCntr = childUpdateCntr + 1

                    break
                
            if insertChild:            
                log.tracef("--- Inserting a child into the hierarchy ---")

                stepTypeId = fetchStepTypeIdFromFactoryId(child.get("type"), txId)
                if stepTypeId == None:
                    log.errorf("Id not found for step type: %s", child.get("type"))
            
                '''
                In the normal workflow of creating SFCs, an encapsulation task cannot reference a chart until the referenced
                chart is created.  We will get into problems when migrating tasks where we import a whole set of charts.
                '''
                
                childChartId = fetchChartIdFromChartPath(child.get("childPath"), txId)
                log.tracef("...the child chart Id is: %s", str(childChartId))
                if childChartId == None:
                    log.errorf("Id not found for child chart, it will be created later hopefully,  with path: %s", child.get("childPath"))
                
                if stepTypeId <> None and childChartId <> None:
                    stepId = fetchStepIdFromChartIdAndStepName(chartId, stepName, txId)
                    log.tracef("The step id of the child step named %s on chart %s is: %s", stepName, str(chartId), str(stepId))
                            
                    SQL = "Insert into SfcHierarchy (StepId, ChartId, ChildChartId) values (%d, %d, %d)" % (stepId, chartId, childChartId)
                    system.db.runUpdateQuery(SQL, tx=txId)
                    log.tracef("...inserted %d into sfcHierarchy", stepId) 
                    childInsertCntr = childInsertCntr + 1


        log.tracef("...inserted %d new children", childInsertCntr)
        log.tracef("...updated %d children", childUpdateCntr)
        
        '''
        Parse the chart properties to determine if there are onStop, onCancel, and onAbort handlers to see if they call a chart using the new 
        chart abort handler paradigm
        '''
        SQL = "Select CH.ChartId, CH.Handler, CH.HandlerChartId, C.ChartPath as HandlerChartPath"\
            " from SfcHierarchyHandler CH, SfcChart C "\
            " where CH.HandlerChartId = C.ChartId "\
            " and CH.ChartId = %d" % (chartId)
        pds = system.db.runQuery(SQL, tx=txId)
        
        log.tracef("------------------")
        log.tracef("Updating the chart hierarchy with End Handlers...")
        log.tracef("------------------")
        
        onStopChartPath = parseHandlerXML(root, "onstop")
        updateHandler(pds, chartId, onStopChartPath, "onStop", txId)

        onCancelChartPath = parseHandlerXML(root, "oncancel")
        updateHandler(pds, chartId, onCancelChartPath, "onCancel", txId)

        onAbortChartPath = parseHandlerXML(root, "onabort")
        updateHandler(pds, chartId, onAbortChartPath, "onAbort", txId)

        '''
        Children will be automatically deleted because there is a cascade delete from the  children that are left in the list we fetched from the database.
        Steps that have been updated to point to a different child will be updated above.
        '''

        log.tracef("Committing and closing the transaction.")        
        system.db.commitTransaction(txId)
        system.db.closeTransaction(txId)

    except:
        print "CAUGHT AN EXCEPTION"
        errorTxt = catchError("Updating the Chart Hierarchy - rolling back database transactions")
        log.errorf(errorTxt)
        system.db.rollbackTransaction(txId)
        system.db.closeTransaction(txId)
        raise Exception("Database Update Exception in structureManager. %s" % (errorTxt))
    
    log.infof("...done with updateChartHierarchy()!")

'''
Update the SfcHierarchyHandler table.  If there is a record in the table but it is no longer needed, then delete the record.
'''
def updateHandler(pds, chartId, handlerChartPath, handler, txId):
    log.tracef("In updateHandler with a %s <%s>", handler, handlerChartPath)

    if handlerChartPath == None:
        '''
        If the chart doesn't have a handler, then make sure there isn't one in the database!
        '''
        log.tracef("The chart does not have an %s handler, checking to make sure there isn't one in the database...", handler)
        for record in pds:
            if record["Handler"] == handler:
                ''' Delete the chart in the database '''
                SQL = "delete from SfcHierarchyHandler where ChartId = %s and Handler = '%s'" % (chartId, handler)
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                log.tracef("Deleted %d unused %s handler", rows, handler)

    else:
        '''
        The chart does have a handler, make sure the database is in sync.  Insert if it is new, update if it is changed, 
        '''
        handlerChartId = fetchChartIdFromChartPath(handlerChartPath, txId) 
        if handlerChartId == None:
            log.errorf("Error attemting to update the SfcHierarchyHandler.  The specified handler chart path <%s> does not exist!", handlerChartPath)
            return
        
        for record in pds:
            log.tracef("This chart already has a %s handler...", handler)
            if record["Handler"] == handler:
                ''' There is already a handler in the database, if it is the same then we are done, if it isn't then update it '''
                if record["HandlerChartPath"] == handlerChartPath:
                    log.tracef("...the handler has not changed!")
                    return
                else:
                    log.tracef("...updating an existing handler...")
                    return

        ''' If we got this far then we need to insert a new record '''
        log.tracef("Inserting a new %s handler <%s> into SfcHierarchyHandler...", handler, handlerChartPath)
        SQL = "Insert into SfcHierarchyHandler (ChartId, Handler, HandlerChartId) values (%d, '%s', %d)" % (chartId, handler, handlerChartId)
        system.db.runUpdateQuery(SQL, tx=txId)

def parseHandlerXML(root, handlerName):
    
    chartPath = None
    for handler in root.findall(handlerName):
        parseLog.infof("Found an %s handler...", handlerName)
        
        ''' 
        Look for a call to endHandlerRunner, then look for the first argument.  If it is a chartVariable then look for it, if it isn't a chart variable
        then it must be the chart path.
        '''
        txt = handler.text
        key = "endHandlerRunner("
        idx = txt.find(key)
        if idx  >= 0:
            startPos = idx + len(key)
            endPos = txt[startPos:].find(",")
            chartPath = txt[startPos: startPos + endPos]
            parseLog.tracef("The local variable or chart path is: <%s>", chartPath)
            
            '''
            chartPath is either a chartPath or a local variable that contains the chartPath.  If it is a local variable, then search the text for
            an occurence before this reference.
            '''
            idx = txt.find(chartPath)
            if idx < startPos:
                ''' The reference is a local variable, which must be defined before this reference.  Look from the beginning for the local variable '''
                parseLog.tracef("...it is a local variable...")
                startPos = txt[idx:].find('"')
                chartPath = txt[idx + startPos + 1:]
                endPos = chartPath.find('"')
                chartPath = chartPath[:endPos]
            else:
                ''' The reference is a chartPath, we are done, strip off the Double or single quotes '''
                parseLog.tracef("...the chartpath is specified in-line")
                chartPath = chartPath.lstrip('"')
                chartPath = chartPath.rstrip('"')
            
            parseLog.infof("The handler calls chart <%s>", chartPath)
        else:
            parseLog.infof("This handler does not appear to call another chart!") 

    return chartPath

def parseXML(root):
    parseLog.infof("In %s.parseXML()", __name__)
    steps = []
    children = []
    
    for step in root.findall("step"):
        steps, children = parseStep(step, steps, children)
            
    for parallel in root.findall("parallel"):
        parseLog.tracef( "Found a parallel...")
        for step in parallel.findall("step"):
            steps, children = parseStep(step, steps, children)

    parseLog.tracef("========================")
    parseLog.tracef( "Python Found: ")
    parseLog.tracef( "     steps: %s", str(steps))
    parseLog.tracef( "  children: %s", str(children))
    parseLog.tracef( "========================")
    return steps, children

def parseStep(step, steps, children):
    parseLog.tracef( "===================")
    stepId = step.get("id")
    stepName = step.get("name")
    stepType = step.get("factory-id")
    
    stepDict = {"id": stepId, "name": stepName, "type": stepType}
    steps.append(stepDict)
    parseLog.tracef("Found a step: %s", str(stepDict))

    childChartPath = step.get("chart-path")
    if (childChartPath != None):
        log.tracef("Found an encapsulation that calls %s", childChartPath)
        childDict = {"childPath": childChartPath, "id": stepId, "name": stepName, "type": stepType}
        children.append(childDict)
    
    if stepType in ['com.ils.procedureStep', 'com.ils.operationStep', 'com.ils.phaseStep']:
        for chartPath in step.findall("chart-path"):
            childChartPath = chartPath.text
            if (childChartPath != None):
                log.tracef("Found an %s named %s that calls %s", stepType, stepName, childChartPath)
                childDict = {"childPath": childChartPath, "id": stepId, "name": stepName, "type": stepType}
                children.append(childDict)
        
    return steps, children