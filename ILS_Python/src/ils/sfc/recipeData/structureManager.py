'''
Created on Dec 29, 2016

@author: phass
'''

import system
from ils.sfc.gateway import steps
log = system.util.getLogger("com.ils.sfc.python.structureManager")
from ils.common.error import catch
from ils.sfc.recipeData.core import fetchStepTypeIdFromFactoryId, fetchStepIdFromUUID
from ils.common.database import toList

def createChart(resourceId, chartPath, db):
    # Check if the chart already exists
    log.infof("In %s.createChart() with %s-%s...", __name__, chartPath, str(resourceId))
    
    try:
        log.tracef("...updating the chartPath <%s> for a record in sfcChart by resourceId: %d...", chartPath, resourceId)
        SQL = "update SfcChart set ChartPath = '%s' where chartResourceId = %d" % (chartPath, resourceId)
        log.tracef(SQL)
        rows = system.db.runUpdateQuery(SQL, database=db)
        
        if rows > 0:
            return 
        
        log.tracef("...updating the resourceId <%d> for a record in sfcChart by chartPath <%s>...", resourceId, chartPath)
        SQL = "update SfcChart set chartResourceId = %d where ChartPath = '%s'" % (resourceId, chartPath)
        log.tracef(SQL)
        rows = system.db.runUpdateQuery(SQL, database=db)
        
        if rows > 0:
            return
        
        log.tracef("Inserting a new record into SfcChart for %s - %d...", chartPath, resourceId)
        SQL = "insert into SfcChart (ChartPath, chartResourceId) values ('%s', %d)" % (chartPath, resourceId)
        log.tracef(SQL)
        chartId = system.db.runUpdateQuery(SQL, database=db, getKey=True)
        log.tracef("...inserted %s into SfcChart table and got id: %d", chartPath, chartId)

    except:
        errorTxt = catch("%s.createChart()")
        log.error(errorTxt)
    
def deleteChart(resourceId, chartPath, db):
    print "Deleting a chart: %d" % (resourceId)
    SQL = "delete from SfcChart where chartResourceId = %d" % resourceId
    rows = system.db.runUpdateQuery(SQL, db)
    print "Deleted %s rows from SfcChart for %s" % (rows, chartPath)

def updateChartHierarchy(parentChartPath, parentResourceId, stepNames, stepUUIDs, stepFactoryIds, childPaths, childNames, childUUIDs, factoryIds, database):
    log.infof("Updating the chart hierarchy with the parent: %s and children: %s - %s", parentResourceId, str(childNames), str(factoryIds))
    
    log.tracef("Steps: %s", str(stepNames))
    log.tracef("Step UUIDs: %s", str(stepUUIDs))
    log.tracef("Factory Ids: %s", str(stepFactoryIds))
    
    tx = ""
    try:
        tx = system.db.beginTransaction(database)
        # Fetch the chart id (the database id)
        SQL = "select chartId from SfcChart where ChartResourceId = %d" % (parentResourceId)
        chartId =  system.db.runScalarQuery(SQL, tx=tx)
        print "The id for chart %s is: %d" % (parentChartPath, chartId)
    
        # There really shouldn't be a way that the chart is not already inserted...
        if chartId < 0:
            print "Surprisingly the chart did not already exist..."
            SQL = "insert into SfcChart (ChartPath, chartResourceId) values ('%s', %d)" % (parentChartPath, parentResourceId)
            chartId = system.db.runUpdateQuery(SQL, tx=tx, getKey=True)
            print "...inserted chart with id: %d" % (chartId)
        
        '''
        Handle the step catalog - we need this so that we can have a recipe editor.
        '''
        log.infof("------------------")
        log.infof("Inserting steps...")
        log.infof("------------------")
        
        pds = system.db.runQuery("select StepUUID from sfcStep where ChartId = %d" % (chartId))
        stepsInDatabase = toList(pds)
        
        for i in range(0, len(stepNames)):
            # Skip connections, notes, etc.
            if str(stepFactoryIds[i]) <> "None":
                stepTypeId = fetchStepTypeIdFromFactoryId(stepFactoryIds[i], tx)
                
                log.tracef("Checking if the step %s exists...", stepUUIDs[i])
                SQL = "select count(*) from SfcStep where StepUUID = '%s'" % (stepUUIDs[i])
                cnt = system.db.runScalarQuery(SQL, tx=tx)
                
                if cnt == 0:
                    SQL = "insert into SfcStep (StepName, StepUUID, StepTypeId, ChartId) values ('%s', '%s', %d, %d)" % (stepNames[i], stepUUIDs[i], stepTypeId, chartId)
                    stepId = system.db.runUpdateQuery(SQL, tx=tx, getKey=True)
                    log.tracef("...inserted a %s step with id: %d", stepFactoryIds[i], stepId)
                else:
                    SQL = "update SfcStep set StepName = '%s', StepTypeId = %d, ChartId = %d where StepUUID = '%s'" % (stepNames[i], stepTypeId, chartId, stepUUIDs[i])
                    rows = system.db.runUpdateQuery(SQL, tx=tx)
                    log.tracef("...updated %d existing steps", rows)

                stepsInDatabase.remove(stepUUIDs[i])
            
        log.infof("...done inserting steps!")
        
        log.infof("Deleting steps from the database that have been deleted from the chart...")
        
        for stepUUID in stepsInDatabase:
            SQL = "delete from SfcStep where StepUUID = '%s' and ChartId = %d" % (stepUUID, chartId)
            rows = system.db.runUpdateQuery(SQL, tx=tx)
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
        rows = system.db.runUpdateQuery(SQL, tx=tx)
        print "...deleted %i children!" % (rows)
        

        # Make a list of dictionaries from the lists
        children = []
        for i in range(0, len(childNames)):
            child = {"path": childPaths[i], "name": childNames[i], "uuid": childUUIDs[i], "factoryId": factoryIds[i]}
            children.append(child)
                
            print "The children from Designer are: ", children

        for child in children:
            print "...Inserting a child into the hierarchy..."
            stepTypeId = fetchStepTypeIdFromFactoryId(child.get("factoryId"), tx)
            print "The step Type Id is: ", stepTypeId
            if stepTypeId == None:
                log.errorf("Id not found for step type: %s", child.get("factoryId"))
            
            '''
            In the normal workflow of creating SFCs, an encapsulation task cannot reference a chart until the referenced
            chart is created.  We will get into problems when migrating tasks where we import a whole set of charts.
            '''
            from ils.sfc.recipeData.core import fetchChartIdFromChartPath
            childChartId = fetchChartIdFromChartPath(child.get("path"), tx)
            print "The Child Chart Id is: ", childChartId
            if childChartId == None:
                print "The child chart <%s> does not exist in the chart catalog." % (child.get("path"))
                log.errorf("Id not found for child chart, it will be created later hopefully,  with path: %s", child.get("path"))
            
            if stepTypeId <> None and childChartId <> None:
                stepId = fetchStepIdFromUUID(child.get("uuid"), tx)
                SQL = "Insert into SfcHierarchy (StepId, ChartId, ChildChartId) values (%d, %d, %d)" % (stepId, chartId, childChartId)
                print SQL
                system.db.runUpdateQuery(SQL, tx=tx)
                print "...inserted %d into sfcHierarchy" % (stepId)

        log.infof("...committing and closing transaction!")
        system.db.commitTransaction(tx)
    except:
        errorTxt = catch("Updating the Chart Hierarchy - rolling back transactions")
        log.errorf(errorTxt)
        system.db.rollbackTransaction(tx)
    finally:
        system.db.closeTransaction(tx)
        