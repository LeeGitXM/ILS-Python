'''
Created on Dec 29, 2016

@author: phass
'''

import system
log = system.util.getLogger("com.ils.sfc.python.structureManager")

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

def updateChartHierarchy(parentChartPath, parentResourceId, childPaths, childNames, childUUIDs, factoryIds, database):
    print "Updating the chart hierarchy with the parent: %s and children: %s - %s" % (parentResourceId, str(childNames), str(factoryIds))
    
    # Fetch the chart id (the database id)
    SQL = "select chartId from SfcChart where ChartResourceId = %d" % (parentResourceId)
    chartId =  system.db.runScalarQuery(SQL, db=database)
    print "The id for %s is: %d" % (parentChartPath, chartId)
    
    # If there are no children, then delete from the database to match
    if len(childPaths) == 0:
        print "There are no children so make sure the database is clean..."
        SQL = "Delete from SfcHierarchy where ChartId = %d" % (chartId)
        rows = system.db.runUpdateQuery(SQL, db=database)
        print "...deleted %i children!" % (rows)
        return
    
    # Make a list of dictionaries from the lists
    children = []
    for i in range(0, len(childNames)):
        child = {"path": childPaths[i], "name": childNames[i], "uuid": childUUIDs[i], "factoryId": factoryIds[i]}
        children.append(child)
        
    print "The children are: ", children
    
    SQL = "select * from SfcHierarchyView where ChartResourceId = %d" % (parentResourceId)
    pds = system.db.runQuery(SQL, db=database)
    
    for child in children:
        print child
        
        found = False
        for record in pds:
            if child.get("name") == record["StepName"]:
                found = True
                # Update the Record
                
        if not(found):
            print "...Inserting a child into the hierarchy..."
            from ils.sfc.recipeData.core import fetchStepTypeIdFromFactoryId
            stepTypeId = fetchStepTypeIdFromFactoryId(child.get("factoryId"), database)
            print "The step Type Id is: ", stepTypeId
            if stepTypeId == None:
                log.errorf("Id not found for step type: %s", child.get("factoryId"))
            
            from ils.sfc.recipeData.core import fetchChartIdFromChartPath
            childChartId = fetchChartIdFromChartPath(child.get("path"), database)
            print "The Child Chart Id is: ", childChartId
            if childChartId == None:
                print "Hey It is None"
                log.errorf("Id not found for child chart with path: %s", child.get("path"))
            
            if stepTypeId <> None and childChartId <> None:
                SQL = "Insert into SfcHierarchy (StepUUID, StepName, StepTypeId, ChartId, ChildChartId) values ('%s', '%s', %d, %d, %d)" % \
                    (child.get("uuid"), child.get('name'), stepTypeId, chartId, childChartId)
                stepId = system.db.runUpdateQuery(SQL, db=database, getKey = True)
                print "...inserted %d into sfcHierarchy" % (stepId)