'''
Created on Dec 29, 2016

@author: phass
'''

import system
from ils.common.util import formatDateTimeForDatabase
log = system.util.getLogger("com.ils.sfc.python.structureManager")
from ils.common.error import catch
from ils.sfc.recipeData.core import fetchStepTypeIdFromFactoryId, fetchStepIdFromUUID
from ils.common.database import toList

def getTxId(db):
    
    try:
        txId = system.util.getGlobals()['txId']
        if txId in ["", None, "foo"]:
            txId = system.db.beginTransaction(database=db, isolationLevel=system.db.READ_COMMITTED, timeout=86400000)    # timeout is one day
            system.util.getGlobals()['txId'] = txId
        print "The transactionId is: ", txId
    except:
        print "*** Getting a fresh transaction Id ***"
        txId = system.db.beginTransaction(database=db, isolationLevel=system.db.READ_COMMITTED, timeout=86400000)    # timeout is one day
        system.util.getGlobals()['txId'] = txId

    return txId

def createChart(resourceId, chartPath, db):
    # Check if the chart already exists 
    log.infof("In %s.createChart() with %s-%s...", __name__, chartPath, str(resourceId))

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
        errorTxt = catch("%s.createChart()")
        log.errorf(errorTxt)
    
def deleteChart(resourceId, chartPath, db):
    log.infof("Deleting a chart: %d", resourceId)
    
    txId = getTxId(db)    
    print "The transactionId is: ", txId
    
    try:
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
    except:
        errorTxt = catch("%s.createChart()" % (__name__))
        log.error(errorTxt)


def saveProject(project, db):
    # Check if the chart already exists
    log.infof("In %s.saveProject() with %s...", __name__, str(project))

    txId = getTxId(db)

    try:
        log.tracef("...committing database transactions using %s..." % (txId))
        system.db.commitTransaction(txId)
        system.db.closeTransaction(txId)
        system.util.getGlobals()['txId'] = None

    except:
        errorTxt = catch("%s.saveProject()")
        log.error(errorTxt)


def updateChartHierarchy(parentChartPath, parentResourceId, stepNames, stepUUIDs, stepFactoryIds, childPaths, childNames, childUUIDs, factoryIds, db):
    log.infof("Updating the chart hierarchy with the parent: %s and children: %s - %s", parentResourceId, str(childNames), str(factoryIds))
    
    txId = getTxId(db)    
    print "The transactionId is: ", txId
    
    log.tracef("Steps: %s", str(stepNames))
    log.tracef("Step UUIDs: %s", str(stepUUIDs))
    log.tracef("Factory Ids: %s", str(stepFactoryIds))
    
    try:
        # Fetch the chart id (the database id)
        SQL = "select chartId from SfcChart where ChartResourceId = %d" % (parentResourceId)
        chartId =  system.db.runScalarQuery(SQL, tx=txId)
        print "The id for chart %s is: %d" % (parentChartPath, chartId)
    
        # There really shouldn't be a way that the chart is not already inserted...
        if chartId < 0:
            print "Surprisingly the chart did not already exist..."
            SQL = "insert into SfcChart (ChartPath, chartResourceId) values ('%s', %d)" % (parentChartPath, parentResourceId)
            chartId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
            print "...inserted chart with id: %d" % (chartId)
        
        '''
        Handle the step catalog - we need this so that we can have a recipe editor.
        '''
        log.infof("------------------")
        log.infof("Inserting steps...")
        log.infof("------------------")
        
        pds = system.db.runQuery("select StepUUID from sfcStep where ChartId = %d" % (chartId), tx=txId)
        stepsInDatabase = toList(pds)
        
        for i in range(0, len(stepNames)):
            # Skip connections, notes, etc.
            if str(stepFactoryIds[i]) <> "None":
                stepTypeId = fetchStepTypeIdFromFactoryId(stepFactoryIds[i], txId)
                
                log.tracef("Checking if the step %s exists...", stepUUIDs[i])
                SQL = "select count(*) from SfcStep where StepUUID = '%s'" % (stepUUIDs[i])
                cnt = system.db.runScalarQuery(SQL, tx=txId)
                
                if cnt == 0:
                    SQL = "insert into SfcStep (StepName, StepUUID, StepTypeId, ChartId) values ('%s', '%s', %d, %d)" % (stepNames[i], stepUUIDs[i], stepTypeId, chartId)
                    stepId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
                    log.tracef("...inserted a %s step with id: %d", stepFactoryIds[i], stepId)
                else:
                    SQL = "update SfcStep set StepName = '%s', StepTypeId = %d, ChartId = %d where StepUUID = '%s'" % (stepNames[i], stepTypeId, chartId, stepUUIDs[i])
                    rows = system.db.runUpdateQuery(SQL, tx=txId)
                    log.tracef("...updated %d existing steps", rows)

                if stepUUIDs[i] in stepsInDatabase:
                    stepsInDatabase.remove(stepUUIDs[i])
            
        log.infof("...done inserting steps!")
        
        log.infof("Deleting steps from the database that have been deleted from the chart...")
        
        for stepUUID in stepsInDatabase:
            SQL = "delete from SfcStep where StepUUID = '%s' and ChartId = %d" % (stepUUID, chartId)
            rows = system.db.runUpdateQuery(SQL, tx=txId)
            if rows <> 1:
                log.warnf("...error deleting step <%s> from SfcStep - %d rows were deleted", stepUUID, rows)
            else:
                log.infof("Step <%s> was successfully deleted", stepUUID)

        log.infof("...done deleting steps!")
        
        '''
        Now handle the chart hierarchy
        '''
        log.infof("------------------")
        log.infof("Updating the chart hierarchy...")
        log.infof("------------------")
        
        # Start out with a clean hierarchy in the database

        print "Initializing the SFC Hierarchy for parent %d ..." % (chartId)
        SQL = "Delete from SfcHierarchy where ChartId = %d" % (chartId)
        rows = system.db.runUpdateQuery(SQL, tx=txId)
        print "...deleted %i children!" % (rows)
        

        # Make a list of dictionaries from the lists
        children = []
        for i in range(0, len(childNames)):
            child = {"path": childPaths[i], "name": childNames[i], "uuid": childUUIDs[i], "factoryId": factoryIds[i]}
            children.append(child)
                
            print "The children from Designer are: ", children

        for child in children:
            print "...Inserting a child into the hierarchy..."
            stepTypeId = fetchStepTypeIdFromFactoryId(child.get("factoryId"), txId)
            print "The step Type Id is: ", stepTypeId
            if stepTypeId == None:
                log.errorf("Id not found for step type: %s", child.get("factoryId"))
            
            '''
            In the normal workflow of creating SFCs, an encapsulation task cannot reference a chart until the referenced
            chart is created.  We will get into problems when migrating tasks where we import a whole set of charts.
            '''
            from ils.sfc.recipeData.core import fetchChartIdFromChartPath
            childChartId = fetchChartIdFromChartPath(child.get("path"), txId)
            print "The Child Chart Id is: ", childChartId
            if childChartId == None:
                print "The child chart <%s> does not exist in the chart catalog." % (child.get("path"))
                log.errorf("Id not found for child chart, it will be created later hopefully,  with path: %s", child.get("path"))
            
            if stepTypeId <> None and childChartId <> None:
                stepId = fetchStepIdFromUUID(child.get("uuid"), txId)
                SQL = "Insert into SfcHierarchy (StepId, ChartId, ChildChartId) values (%d, %d, %d)" % (stepId, chartId, childChartId)
                print SQL
                system.db.runUpdateQuery(SQL, tx=txId)
                print "...inserted %d into sfcHierarchy" % (stepId)

        log.infof("...completed adjusting the sfcHierarchy!")
    except:
        errorTxt = catch("Updating the Chart Hierarchy")
        log.errorf(errorTxt)

        