'''
Created on Dec 29, 2016

@author: phass
'''

import system
log = system.util.getLogger("com.ils.sfc.python.structureManager")
from ils.common.error import catch
from ils.sfc.recipeData.core import fetchStepTypeIdFromFactoryId, fetchStepIdFromUUID

def createChart(resourceId, chartPath, db):
    # Check if the chart already exists
    print "In createChart with %s-%s..."%(chartPath, resourceId)
    SQL = "select count(*) from SfcChart where chartResourceId = %d" % resourceId
    rows = system.db.runScalarQuery(SQL, db)
    if rows == 0:
        SQL = "insert into SfcChart (ChartPath, chartResourceId) values ('%s', %d)" % (chartPath, resourceId)
        chartId = system.db.runUpdateQuery(SQL, database=db, getKey=True)
        print "...inserted %s into SfcChart table and got id: %i" % (chartPath, chartId)
    else:
        print "...%s already exists" % (chartPath)
        SQL = "update SfcChart set ChartPath = '%s' where chartResourceId = %d" % (chartPath, resourceId)
        print SQL
        system.db.runUpdateQuery(SQL, database=db)
    
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
    
    tx = system.db.beginTransaction(database)
    try:
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

        log.infof("...done inserting steps!")
        
        '''
        Now handle the chart hierarchy
        '''
        log.infof("------------------")
        log.infof("Updating the chart hierarchy...")
        log.infof("------------------")
        # If there are no children, then delete from the database to match
        if len(childPaths) == 0:
            print "There are no children so make sure the database is clean..."
            SQL = "Delete from SfcHierarchy where ChartId = %d" % (chartId)
            rows = system.db.runUpdateQuery(SQL, tx=tx)
            print "...deleted %i children!" % (rows)
        
        else:
            # Make a list of dictionaries from the lists
            children = []
            for i in range(0, len(childNames)):
                child = {"path": childPaths[i], "name": childNames[i], "uuid": childUUIDs[i], "factoryId": factoryIds[i]}
                children.append(child)
                
            print "The children are: ", children
            
            # Now see what children are already in the database, if the current children are not in this list then insert one.
            SQL = "select * from SfcHierarchyView where ChartResourceId = %d" % (parentResourceId)
            pds = system.db.runQuery(SQL, tx=tx)
            
            for child in children:
                print child
                
                found = False
                for record in pds:
                    if child.get("name") == record["StepName"]:
                        found = True
                        # Update the Record
                        
                if not(found):
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
        