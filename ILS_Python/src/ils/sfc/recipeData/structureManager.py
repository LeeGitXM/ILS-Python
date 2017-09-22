'''
Created on Dec 29, 2016

@author: phass
'''

import system
from ils.common.util import formatDateTimeForDatabase
log = system.util.getLogger("com.ils.sfc.python.structureManager")
from ils.common.error import catchError
from ils.sfc.recipeData.core import fetchStepTypeIdFromFactoryId, fetchStepIdFromUUID, fetchChartIdFromChartPath
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
    
def deleteChart(resourceId, chartPath, db):
    log.infof("Deleting a chart: %d", resourceId)
    
    try:
        txId = getTxId(db)    

        SQL = "select chartId, chartPath from SfcChart where chartResourceId = %d" % resourceId
        pds = system.db.runQuery(SQL, tx=txId)
        
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
            pds = system.db.runQuery(SQL, tx=txId)
            
            if len(pds) == 0:
                log.infof("...cleaning up for a deleted chart...")
                SQL = "delete from SfcHierarchy where childChartId = %d" % chartId
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                log.tracef( "...deleted %d children from SfcChartHierarchy...", rows)
                            
                SQL = "delete from SfcHierarchy where ChartId = %d" % chartId
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                log.tracef( "...deleted %d parents from SfcChartHierarchy...", rows)
    
                SQL = "delete from SfcChart where chartResourceId = %d" % resourceId
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                log.tracef("...deleted %d rows from SfcChart...", rows)
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
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                if rows == 1:
                    log.trace("Successfully deleted the new chart")
                else:
                    log.errorf("Error deleting the new chart - %s", SQL)
                
                SQL = "update SfcChart set ChartResourceId = %d, ChartPath = '%s' where ChartId = %d" % (newResourceId, newChartPath, chartId)
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                if rows == 1:
                    log.trace("Successfully updated the old chart")
                else:
                    log.errorf("Error updating the old chart - %s", SQL)
                
            else:
                log.errorf("I can't handle multiple resource updates")
        else:
            log.warnf("The chart was not found in SfcChart")
        
        log.tracef("Committing and closing the transaction.")        
        system.db.commitTransaction(txId)
        system.db.closeTransaction(txId)

    except:
        errorTxt = catchError("deleting a chart - rolling back database transactions")
        log.errorf(errorTxt)
        system.db.rollbackTransaction(txId)
        system.db.closeTransaction(txId)


'''
This is only called by Java hook in designer when the user saves the project.  It is passed all of the resources that have been changed since the last time the 
project was saved.
'''
def updateChartHierarchy(parentChartPath, parentResourceId, stepNames, stepUUIDs, stepFactoryIds, childPaths, childNames, childUUIDs, childFactoryIds, db):
    log.infof("In %s.updateChartHierarcy() updating the steps and hierarchy with the parent: %s and children: %s - %s", __name__, parentResourceId, str(childNames), str(childFactoryIds))
    
    txId = getTxId(db)    
    
    log.tracef("Steps: %s", str(stepNames))
    log.tracef("Step UUIDs: %s", str(stepUUIDs))
    log.tracef("Factory Ids: %s", str(stepFactoryIds))
    
    try:
        # Fetch the chart id (the database id)
        SQL = "select * from SfcChart where ChartResourceId = %d" % (parentResourceId)
        pds =  system.db.runQuery(SQL, tx=txId)
        
    
        # There really shouldn't be a way that the chart is not already inserted...
        if len(pds) == 0:
            log.tracef("The chart did not already exist, creating a new one...")
            SQL = "insert into SfcChart (ChartPath, chartResourceId) values ('%s', %d)" % (parentChartPath, parentResourceId)
            chartId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
            log.tracef("...inserted chart with id: %d", chartId)
        else:
            record = pds[0]
            chartId = record["ChartId"]
            log.tracef("The id for chart %s is: %d", parentChartPath, chartId)
            chartPath = record["ChartPath"]
            if chartPath <> parentChartPath:
                log.tracef("Updating the chart path for a renamed chart...")
                SQL = "update SfcChart set ChartPath = '%s' where ChartId = %s" % (parentChartPath, str(chartId))
                rows = system.db.runUpdateQuery(SQL, tx=txId)
                log.tracef("...updated %d existing sfcChart", rows)
        
        '''
        Handle the step catalog - we need this so that we can have a recipe editor.
        '''
        log.tracef("------------------")
        log.tracef("Inserting steps...")
        log.tracef("------------------")
        
        databaseStepsPds = system.db.runQuery("select * from sfcStep where ChartId = %d" % (chartId), tx=txId)
        stepsInDatabase = []
        for record in databaseStepsPds:
            stepsInDatabase.append(record["StepUUID"])
        
        updateCntr = 0
        insertCntr = 0
        for i in range(0, len(stepNames)):
            # Skip connections, notes, etc.
            if str(stepFactoryIds[i]) <> "None":
                stepTypeId = fetchStepTypeIdFromFactoryId(stepFactoryIds[i], txId)
                
                if stepUUIDs[i] in stepsInDatabase:
                    log.tracef("Step already exists in database, checking if it needs to be updated...")
                    
                    for stepRecord in databaseStepsPds:
                        if stepUUIDs[i] == stepRecord["StepUUID"]:
                            log.tracef("...found the step in the database list...")
                            updateIt = False
                            if stepNames[i] <> stepRecord["StepName"]:
                                log.tracef("...the name has been changed from %s to %s", stepRecord["StepName"], stepNames[i])
                                updateIt = True
                            if chartId <> stepRecord["ChartId"]:
                                updateIt = True
                                log.tracef("...the chartId has been changed from %s to %s", str(stepRecord["ChartId"]), str(chartId))
                            if stepTypeId <> stepRecord["StepTypeId"]:
                                log.tracef("...the stepType has been changed from %s to %s", str(stepRecord["StepTypeId"]), str(stepTypeId))
                                updateIt = True

                            if updateIt:
                                SQL = "update SfcStep set StepName = '%s', StepTypeId = %d, ChartId = %d where StepUUID = '%s'" % (stepNames[i], stepTypeId, chartId, stepUUIDs[i])
                                rows = system.db.runUpdateQuery(SQL, tx=txId)
                                log.tracef("...updated %d existing steps", rows)
                                updateCntr = updateCntr + 1
                    
                    stepsInDatabase.remove(stepUUIDs[i])
                else:
                    log.tracef("Inserting a new step %s, a %s into the database...", stepNames[i], stepFactoryIds[i])
                    SQL = "insert into SfcStep (StepName, StepUUID, StepTypeId, ChartId) values ('%s', '%s', %d, %d)" % (stepNames[i], stepUUIDs[i], stepTypeId, chartId)
                    stepId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
                    log.tracef("...inserted a %s step with id: %d", stepFactoryIds[i], stepId)
                    insertCntr = insertCntr + 1

        log.tracef("...%d steps were inserted...", insertCntr)
        log.tracef("...%d steps were updated...", updateCntr)
                
        log.tracef("Checking for steps to delete from the database that have been deleted from the chart...")
        
        deleteCntr = 0
        for stepUUID in stepsInDatabase:
            SQL = "delete from SfcStep where StepUUID = '%s' and ChartId = %d" % (stepUUID, chartId)
            rows = system.db.runUpdateQuery(SQL, tx=txId)
            deleteCntr = deleteCntr + rows
            if rows <> 1:
                log.warnf("...error deleting step <%s> from SfcStep - %d rows were deleted", stepUUID, rows)
            else:
                log.infof("Step <%s> was successfully deleted", stepUUID)

        log.tracef("... %d steps were deleted!", deleteCntr)
        
        '''
        Now handle the chart hierarchy
        '''
        log.tracef("------------------")
        log.tracef("Updating the chart hierarchy...")
        log.tracef("------------------")
        
        # Fetch what is already in the database
        SQL = "Select * from SfcHierarchyView where ChartId = %d" % (chartId)
        childrenInDatabasePds = system.db.runQuery(SQL, tx=txId)
        from ils.common.database import toDictList
        chidrenInDatabaseList = toDictList(childrenInDatabasePds, [])
        log.tracef("...found %d children already in the database...", len(chidrenInDatabaseList))
        
        # Make a list of dictionaries from the lists that are currently in the chart
        children = []
        for i in range(0, len(childNames)):
            child = {"stepName": childNames[i], "childPath": childPaths[i], "uuid": childUUIDs[i], "factoryId": childFactoryIds[i]}
            children.append(child)
                
        log.tracef("The children from Designer are: %s", str(children))

        childInsertCntr = 0
        childUpdateCntr = 0
        for child in children:
            log.tracef("Checking stepName: %s, childPath: %s, stepUUID: %s, factoryId: %s...", child["stepName"], child["childPath"], child["uuid"], child["factoryId"])
            
            '''
            Compare the stepName and childPath from the Designer with what is already in the database
            '''
            insertChild = True
            for childDatabase in chidrenInDatabaseList:
                log.tracef("...comparing to %s - %s", childDatabase["StepName"], childDatabase["ChildChartPath"])
                if child["stepName"] == childDatabase["StepName"]:
                 
                    insertChild = False
                    if child["childPath"] == childDatabase["ChildChartPath"]:
                        log.tracef("...this child already exists...")
                    else:
                        log.tracef("...this child already exists but is calling a different chart...")
                        childChartId = fetchChartIdFromChartPath(child.get("childPath"), txId)
                        log.tracef("...the new child chart Id is: %s", str(childChartId))
                        if childChartId == None:
                            log.errorf("Id not found for child chart, it will be created later hopefully,  with path: %s", child.get("childPath"))
                        
                        else:
                            stepId = fetchStepIdFromUUID(child.get("uuid"), txId)
                            SQL = "Update SfcHierarchy set ChildChartId = %d where StepId = %d" % (childChartId, stepId)
                            system.db.runUpdateQuery(SQL, tx=txId)
                            log.tracef("...updated %d into sfcHierarchy", stepId) 
                            childUpdateCntr = childUpdateCntr + 1

                    break
                
            if insertChild:            
                log.tracef("--- Inserting a child into the hierarchy ---")

                stepTypeId = fetchStepTypeIdFromFactoryId(child.get("factoryId"), txId)
                if stepTypeId == None:
                    log.errorf("Id not found for step type: %s", child.get("factoryId"))
            
                '''
                In the normal workflow of creating SFCs, an encapsulation task cannot reference a chart until the referenced
                chart is created.  We will get into problems when migrating tasks where we import a whole set of charts.
                '''
                
                childChartId = fetchChartIdFromChartPath(child.get("childPath"), txId)
                log.tracef("...the child chart Id is: %s", str(childChartId))
                if childChartId == None:
                    log.errorf("Id not found for child chart, it will be created later hopefully,  with path: %s", child.get("childPath"))
                
                if stepTypeId <> None and childChartId <> None:
                    stepId = fetchStepIdFromUUID(child.get("uuid"), txId)
                    SQL = "Insert into SfcHierarchy (StepId, ChartId, ChildChartId) values (%d, %d, %d)" % (stepId, chartId, childChartId)
                    system.db.runUpdateQuery(SQL, tx=txId)
                    log.tracef("...inserted %d into sfcHierarchy", stepId) 
                    childInsertCntr = childInsertCntr + 1


        log.tracef("...inserted %d new children", childInsertCntr)
        log.tracef("...updated %d children", childUpdateCntr)
        
        '''
        Children will be automatically deleted because there is a cascade delete from the  children that are left in the list we fetched from the database.
        Steps that have been updated to point to a different child will be updated above.
        '''

        log.tracef("Committing and closing the transaction.")        
        system.db.commitTransaction(txId)
        system.db.closeTransaction(txId)

    except:
        errorTxt = catchError("Updating the Chart Hierarchy - rolling back database transactions")
        log.errorf(errorTxt)
        system.db.rollbackTransaction(txId)
        system.db.closeTransaction(txId)
