'''
Created on Oct 12, 2020

@author: phass
'''

import system, string
from ils.sfc.recipeData.core import fetchStepTypeIdFromFactoryId, fetchChartIdFromChartPath, fetchStepIdFromChartIdAndStepName
from ils.common.util import formatDateTimeForDatabase
from ils.common.error import catchError

from ils.log import getLogger
log = getLogger(__name__)
parseLog = getLogger(__name__ + ".xmlParser")

def compileCharts(deletedResources, addedResources, changedResources, db):
    '''
    This is called from the Designer Hook when the global project is saved.
    
    There will be an entry in changedResources for every chart that is open in Designer, even if nothing changed.
    '''
    if len(deletedResources) == 0 and len(addedResources) == 0 and len(changedResources) == 0:
        log.infof( "Exiting %s.compileCharts() because there is nothing to do!", __name__)
        return
     
    log.infof( "In %s.compileCharts()", __name__)
    compiler = Compiler(deletedResources, addedResources, changedResources, db)
    compiler.compile()

    
class Compiler():
    deletedResources = None
    addedResources = None
    changedResources = None
    db = None
    txId = None
    PHASE_1 = 1
    PHASE_2 = 2
    charts = None
    stepsToDelete = []      # List used to collect steps that will be deleted at the very end

    def __init__(self, deletedResources, addedResources, changedResources, db):
        log.tracef("Creating a new compiler")
        self.deletedResources = deletedResources
        self.addedResources = addedResources
        self.changedResources = changedResources
        self.db = db
        self.getTxId()
        self.charts = []
        
    def getTxId(self):
        txId = system.db.beginTransaction(database=self.db, timeout=86400000)    # timeout is one day
        log.tracef("Created a new transaction id: %s", txId)
        self.txId = txId

    def compile(self):
        self.dumpLists("Initial lists")  # Before we do anything, print out all of the incoming data
        self.handleMovedCharts()
        self.dumpLists("After handling moved resources")
        
        '''
        Remove deleted resources from the update list.  It is common that a deleted chart will also appear in the update list. 
        In the deleted data structure, the chart path will probably be n/a so we will delete using the resource id.
        There is no point updating a chart if it is going to be deleted.
        '''
        self.handleDeletedCharts(self.PHASE_1)
        
        '''
        Add a record to the chart table for all new charts.  There should also be an update record for the chart that has 
        the step details for the chart 
        '''
        self.handleAddedResources()
        
        '''
        Handle changed resources
        '''
        self.setupCharts()        
        self.handleChangedCharts()

        '''
        Now that everything has been updated, delete the charts in the database that we determined need to be deleted
        '''
        self.handleDeletedCharts(self.PHASE_2)
        
        
        '''
        We are all done, close the database transaction, which should delete it
        '''
        log.tracef("Closing the transaction.")
        system.db.closeTransaction(self.txId)


    def dumpLists(self, title):
        ''' Dump the resources to help debug '''
        
        log.tracef("--------------------------------")
        log.tracef("Dumping resources: %s", title)
    
        log.tracef("Deleted Resources:")
        #print "addedResources is a ", deletedResources.__class__
        for resourceId in self.deletedResources:
            log.tracef("        resource id: %s", str(resourceId))
        
        ''' addedResources is a map where the key is the resourceId and the value is the chartPath '''
        log.tracef("Added Resources:") 
        #print "addedResources is a ", addedResources.__class__
        for resourceId in self.addedResources.keys():
            chartPath = self.addedResources[resourceId]
            log.tracef("        resource Id: %s, path: %s", resourceId, chartPath)
        
        ''' changedResources is a dictionary where the key is the resourceId and it has values chartPath and chartXml '''
        log.tracef("Changed Resources:")
        for k in self.changedResources.keys():
            res = self.changedResources[k]
            log.tracef("        resource Id: %s, path: %s", k, res["chartPath"])
            log.tracef("        xml: %s", res["chartXml"])
            log.tracef("")

            
    def handleMovedCharts(self):
        '''
        The key to determining a moved resource is if it has an entry in the deleted and the added lists.  The challenge
        is that the entry in the deleted list doesn't have a chartPath, so I query the database to get the old chartPath
        and then compare the chart NAME to the NAME of every added chart.
        
        The reason that we want to reserve the record in SfcChart and SfcSteps is so that recipe data is preserved.
        '''
        log.tracef("Handling moved resources, (resources that are marked for deletion: %s)", str(self.deletedResources))
        
        ''' I need to make a local copy of the list because I am removing members of the list as I go which throws off the iteration '''
        deletedResourceIds = []
        for deletedResourceId in self.deletedResources:
            deletedResourceIds.append(deletedResourceId)
        
        cntr = 0
        for deletedResourceId in deletedResourceIds:
            log.tracef("    Checking deleted resource %s", str(deletedResourceId))
            deletedChartPath, deletedChartName, deletedChartId = self.fetchChartForResourceId(deletedResourceId)
            
            if deletedChartPath <> None:
            
                ''' Look for a entry in the added list with the same chart NAME - not the entire path '''
        
                for addedResourceId in self.addedResources.keys():
                    addedChartPath = self.addedResources[addedResourceId]
                    addedChartName = addedChartPath[addedChartPath.rfind("/")+1:]
                    log.tracef("        looking at added resource Id: %s, path: %s <%s>", addedResourceId, addedChartPath, addedChartName)
                    if addedChartName == deletedChartName:
                        log.tracef("           --- found a match, this must be a moved chart ---")
                        cntr = cntr + 1
                        
                        ''' Found a match, update the resourceId and the chartPath '''
                        SQL = "update sfcChart set ChartResourceId = %s, chartPath = '%s' where ChartResourceId = %s"  % (addedResourceId, addedChartPath, deletedResourceId)
                        rows = system.db.runUpdateQuery(SQL, tx=self.txId)
                        log.tracef("      Updated %d rows in sfcChart!", rows)
                        
                        ''' update the lists and remove the charts from everywhere '''
                        del self.addedResources[addedResourceId]
                        self.deletedResources.remove(deletedResourceId)
                        
                        ''' 
                        When a chart is moved, all of the callers to that chart are broken (because IA uses absolute path references). 
                        Presumably, the engineer will go and fix the references, but when they do I will receive and updated dictionary.
                        '''
                        self.deleteChartFromDatabaseHierarchy(deletedChartId)
                        
                        '''
                        Update the updateList that references the old resourceId with the new resourceId.
                        We can't change the key of a dictionary, so we need to delete the old one and add a new one
                         '''
                        res = self.changedResources.get(deletedResourceId, None)
                        if res <> None:
                            log.tracef("      ...updating a dictionary in the changedResource list...")
                            del self.changedResources[deletedResourceId]
                            res["chartPath"]  = addedChartPath
                            self.changedResources[addedResourceId] = res
        
        log.tracef("...done with moved resources, moved %d charts", cntr)
            
                            
    def fetchChartForResourceId(self, resourceId):
        SQL = "select ChartPath, ChartId from SfcChart where ChartResourceId = %s" % (str(resourceId))
        pds = system.db.runQuery(SQL, tx=self.txId)
        
        if len(pds) == 0:
            log.tracef("No charts were found for resource: %s", resourceId)
            return None,None,None
        
        if len(pds) > 1:
            log.tracef("Multiple charts were found for resource: %s, which cannot be processed!", resourceId)
            return None,None,None
        
        record = pds[0]
        chartPath = record["ChartPath"]
        chartId = record["ChartId"]
        
        ''' 
        There is a problem here where a deleted chart is named "n/a".  
        The problem is that the "/" is also a path delimiter
        '''
        chartName = chartPath[chartPath.rfind("/")+1:]
        log.tracef("     Found <%s> <%s>", chartPath, chartName)
        return chartPath, chartName, chartId


    def handleAddedResources(self):
        '''
        When they add a new chart, it will appear in the added resource list and in the modified resource list.
        This routine needs to just create a record in the SfcChart table.
        '''
        log.tracef("Handling added resources:")
        for resourceId in self.addedResources.keys():
            chartPath = self.addedResources[resourceId]
            log.tracef("        resource Id: %s, path: %s", resourceId, chartPath)

            SQL = "select * from SfcChart where ChartPath = '%s' or chartResourceId = %s" % (chartPath, resourceId)
            pds =  system.db.runQuery(SQL, tx=self.txId)
            
            if len(pds) == 0:
                log.tracef("...neither the chart resource id <%s> nor the chart path <%s> exist, so add the new chart...", resourceId, chartPath)
        
                SQL = "insert into SfcChart (ChartPath, chartResourceId) values ('%s', %s)" % (chartPath, resourceId)
                chartId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
                log.tracef("...inserted chart with id: %d", chartId)
        
            else:
                log.warnf("WARNING: the chart path or resource id already exist!")
        log.tracef("...done with added resources!")

                            
    def handleDeletedCharts(self, phase):
        if phase == self.PHASE_1:
            log.tracef("Removing deleted resources from the update list (Phase 1):")
            i = 0
            j = 0
            for resourceId in self.deletedResources:
                ''''
                It is common that a deleted chart will also appear in the update list.  
                In the deleted data structure, the chart path will probably be n/a so we will delete using the resource id. 
                '''
                log.tracef("    %s", str(resourceId))
                i = i + 1
                if self.changedResources.has_key(resourceId):
                    log.tracef("Deleting %s from the list of changed resources...", str(resourceId))
                    del self.changedResources[resourceId]
                    j = j + 1
                '''
                Do not delete the chart from the database now.  This is now done at the end in order to support a moved step (and the recipe data on it)  
                '''
                #deleteChart(resourceId, db)
                log.tracef("...done with deleted resources (Phase 1) - handled %d deleted charts and removed %d from the update list", i, j)
                
        elif phase == self.PHASE_2:    
            try:
                log.tracef("Deleting %d charts and %d steps (Phase 2)..", len(self.deletedResources), len(self.stepsToDelete))
        
                ''' First delete steps '''
                
                deletedStepCntr = 0
                for stepDict in self.stepsToDelete:
                    stepName = stepDict.get("stepName", None)
                    chartId = stepDict.get("chartId", None)
                    stepUUID = stepDict.get("stepUUID", None)
                    SQL = "delete from SfcStep where StepName = '%s' and ChartId = %d and stepUUID = '%s'" % (stepName, chartId, stepUUID)
                    rows = system.db.runUpdateQuery(SQL, tx=self.txId)
                    deletedStepCntr = deletedStepCntr + rows
                    if rows <> 1:
                        log.warnf("...error deleting step <%s> from SfcStep - %d rows were deleted", stepName, rows)
                    else:
                        log.infof("Step <%s> was successfully deleted", stepName)
                        
                ''' Now delete charts '''
                        
                log.tracef("Deleting charts...")
                for resourceId in self.deletedResources:
                    ''''
                    It is common that a deleted chart will also appear in the update list.  
                    In the deleted data structure, the chart path will probably be n/a so we will delete using the resource id. 
                    '''
                    log.tracef("    %s", str(resourceId))                
                    self.deleteChart(resourceId)
                        
                log.tracef("Committing the transaction.")        
                system.db.commitTransaction(self.txId)
                
            except:
                log.errorf("Caught an error updating the Chart Hierarchy - rolling back database transactions")
                errorTxt = catchError("Updating the Chart Hierarchy - rolling back database transactions")
                print errorTxt
                system.db.rollbackTransaction(self.txId)
                system.db.closeTransaction(self.txId)
                raise Exception(errorTxt)
        
            log.tracef("... %d steps were deleted!", deletedStepCntr)

        else:
            print "I shouldn't ever get here!"
            
            
    def deleteChart(self, resourceId):
        '''
        Completely delete a chart from the database.
        Moved charts should have been handled before this is called.
        '''
        log.tracef("Deleting a chart with resourceId: %s", str(resourceId) )
    
        try:
            SQL = "select chartId, chartPath from SfcChart where chartResourceId = %s" % str(resourceId)
            pds = system.db.runQuery(SQL, tx=self.txId)
            
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
                pds = system.db.runQuery(SQL, tx=self.txId)
                
                if len(pds) == 0:
                    log.infof("...deleting chart Id: %d", chartId)
                    self.deleteChartFromDatabase(chartId)
                
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
                    rows = system.db.runUpdateQuery(SQL, tx=self.txId)
                    if rows == 1:
                        log.trace("Successfully deleted the new chart")
                    else:
                        log.errorf("Error deleting the new chart - %s", SQL)
                    
                    SQL = "update SfcChart set ChartResourceId = %d, ChartPath = '%s' where ChartId = %d" % (newResourceId, newChartPath, chartId)
                    rows = system.db.runUpdateQuery(SQL, tx=self.txId)
                    if rows == 1:
                        log.trace("Successfully updated the old chart")
                    else:
                        log.errorf("Error updating the old chart - %s", SQL)
                    
                else:
                    log.errorf("I can't handle multiple resource updates")
    
            elif len(pds) == 0:
                ''' When charts are deleted via the designer, the chartPath doesn't exist so if we can't find it by the resource id then we are screwed!'''
                log.warnf("...unable to find the chart by resource id (%s), this chart will need to be manually deleted from SQL*Server...", str(resourceId))
            
            elif len(pds) > 1:
                log.warnf("Multiple charts were found for the same resourceId")
                for record in pds:
                    chartId = record["chartId"]
                    log.infof("...deleting chart Id: %d", chartId)
                    self.deleteChartFromDatabase(chartId)
    
        except:
            ''' This will catch the error and then go on to the next chart '''
            txt = "deleting a chart - this chart will need to be manually deleted from SQL*Server (resourceId = %s)" % (str(resourceId))
            errorTxt = str(catchError(txt))
            log.errorf(errorTxt)
        
        else:
            log.tracef("Deleted charts!")


    def deleteChartFromDatabase(self, chartId):
        
        self.deleteChartFromDatabaseHierarchy(chartId)

        SQL = "delete from SfcChart where chartId = %d" % chartId
        rows = system.db.runUpdateQuery(SQL, tx=self.txId)
        log.tracef("...deleted %d rows from SfcChart...", rows)
        
        SQL = "delete from SfcHierarchyHandler where chartId = %d" % chartId
        rows = system.db.runUpdateQuery(SQL, tx=self.txId)
        log.tracef("...deleted %d caller rows from SfcHierarchyHandler...", rows)
        
        SQL = "delete from SfcHierarchyHandler where HandlerChartId = %d" % chartId
        rows = system.db.runUpdateQuery(SQL, tx=self.txId)
        log.tracef("...deleted %d handler rows from SfcHierarchyHandler...", rows)
        
    def deleteChartFromDatabaseHierarchy(self, chartId):
        SQL = "delete from SfcHierarchy where childChartId = %d" % chartId
        rows = system.db.runUpdateQuery(SQL, tx=self.txId)
        log.tracef( "...deleted %d children from SfcChartHierarchy...", rows)
                    
        SQL = "delete from SfcHierarchy where ChartId = %d" % chartId
        rows = system.db.runUpdateQuery(SQL, tx=self.txId)
        log.tracef( "...deleted %d parents from SfcChartHierarchy...", rows)
    

    def setupCharts(self):
        for resourceId in self.changedResources.keys():
            res = self.changedResources[resourceId]
            chart = Chart(res, resourceId, self, self.txId)
            chart.parseXml()
            self.charts.append(chart)

    def handleChangedCharts(self):
        log.infof("***********************************************")
        log.infof("Analyzing changed resources for the chart hierarchy")
        log.infof("***********************************************")

        for chart in self.charts:
            chart.updateChartHierarchy()

        log.infof("***********************************************")
        log.infof("Analyzing changed resources for the new, moved, deleted steps...")
        log.infof("***********************************************")
        
        stepsToDelete = []            
        for chart in self.charts:
            log.tracef("Processing steps for chart %s", chart.chartPath)
            stepsToDelete = chart.updateChartSteps(stepsToDelete)
        self.stepsToDelete = stepsToDelete


class Chart():
    resource = None
    chartPath = None
    chartXml = None
    txId = None
    resourceId = None
    steps = None
    children = None
    root = None
    compiler = None

    def __init__(self, resource, resourceId, compiler, txId):
        log.tracef("In %s.Cart.__init__() Creating a new Chart object to hold the chart and step data (using txId: %s)...", __name__, txId)
        self.resource = resource
        self.resourceId = resourceId
        self.txId = txId
        self.chartPath = resource["chartPath"]
        self.chartXml = resource["chartXml"]
        self.compiler = compiler
        log.tracef("...processing a chart <%s>...", self.chartPath)
        
    def parseXml(self):
        parseLog.infof("In %s.parseXml()", __name__)
        steps = []
        children = []
        
        parseLog.tracef("The chart XML is: %s", str(self.chartXml))
        
        import xml.etree.ElementTree as ET
        self.root = ET.fromstring(self.chartXml)
        
        for step in self.root.findall("step"):
            steps, children = self.parseStep(step, steps, children)
                
        for parallel in self.root.findall("parallel"):
            parseLog.tracef( "Found a parallel...")
            for step in parallel.findall("step"):
                steps, children = self.parseStep(step, steps, children)
    
        parseLog.tracef("========================")
        parseLog.tracef( "Python found in XML: ")
        parseLog.tracef( "     steps: %s", str(steps))
        parseLog.tracef( "  children: %s", str(children))
        parseLog.tracef( "========================")

        self.steps = steps
        self.children = children

    def parseStep(self, step, steps, children):
        parseLog.tracef( "===================")
        stepId = step.get("id")
        stepName = step.get("name")
        stepType = step.get("factory-id")
        
        stepDict = {"id": stepId, "name": stepName, "type": stepType}
        steps.append(stepDict)
        parseLog.tracef("Found a step in XML: %s", str(stepDict))
    
        childChartPath = step.get("chart-path")
        if (childChartPath != None):
            parseLog.tracef("Found an encapsulation in XML that calls %s", childChartPath)
            childDict = {"childPath": childChartPath, "id": stepId, "name": stepName, "type": stepType}
            children.append(childDict)
        
        if stepType in ['com.ils.procedureStep', 'com.ils.operationStep', 'com.ils.phaseStep']:
            for chartPath in step.findall("chart-path"):
                childChartPath = chartPath.text
                if (childChartPath != None):
                    parseLog.tracef("Found an %s named %s that calls %s", stepType, stepName, childChartPath)
                    childDict = {"childPath": childChartPath, "id": stepId, "name": stepName, "type": stepType}
                    children.append(childDict)
            
        return steps, children
        
    def updateChartHierarchy(self):
        '''
        This is the first pass of updating the database for an updated resource.  In this pass, I update the chartPath table,
        I use two passes because I can't depend on the order of dictionaries in the update list and so I might not be able to update the hierarchy correct
        if a child chart happens to come before the parent in the list..
        '''
        log.infof("Updating the chart hierarchy for chart: %s (%s)", self.chartPath, self.resourceId)
        warnings = []
    
        try:
            '''
            Determine if the chart exists using the resource Id.  
            If a chart path is changed, the resourceId does not change so update the path.
            '''
            SQL = "select * from SfcChart where ChartResourceId = %s" % (self.resourceId)
            pds =  system.db.runQuery(SQL, tx=self.txId)
            
            ''' There really shouldn't be a way that the chart is not already inserted... '''
            if len(pds) == 0:
                log.tracef("The chart resource id <%s> did not exist, checking the chart path...", self.resourceId)
                
                SQL = "select * from SfcChart where ChartPath = '%s'" % (self.chartPath)
                pds =  system.db.runQuery(SQL, tx=self.txId)
                
                if len(pds) == 0:
                    log.tracef("...Neither the chart resource id <%s> nor the chart path <%s> exist, the chart must be new...", self.resourceId, self.chartPath)
    
                    SQL = "insert into SfcChart (ChartPath, chartResourceId) values ('%s', %s)" % (self.chartPath, self.resourceId)
                    chartId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
                    log.tracef("...inserted chart with id: %d", chartId)
    
                else:
                    ''' Update the resource Id '''
                    record = pds[0]
                    chartId = record["ChartId"]
                    log.tracef("Updating the resource id...")
                    SQL = "update SfcChart set ChartResourceId = '%s' where ChartPath = '%s'" % (self.resourceId, self.chartPath)
                    rows = system.db.runUpdateQuery(SQL, tx=self.txId)
                    log.tracef("...updated %d existing sfcChart by chartPath", rows)
            else:
                record = pds[0]
                chartId = record["ChartId"]
                chartPath = record["ChartPath"]
                log.tracef("...the chart already exists (by resourceId) - path: %s, chart id: %d", chartPath, chartId)

                if chartPath <> self.chartPath:
                    log.tracef("Updating the chart path for a renamed chart...")
                    
                    ''' 
                    We found a resource id but it is associated with a different chartPath, before we assign the new chartPath to this resourceId, make sure it isn't already 
                    associated with another resourceId.
                    '''
                    self.compiler.deleteChart(chartId)

                    SQL = "update SfcChart set ChartPath = '%s' where ChartId = %s" % (self.chartPath, str(chartId))
                    print SQL
                    rows = system.db.runUpdateQuery(SQL, tx=self.txId)
                    log.tracef("...updated %d existing sfcChart", rows)
    
            log.tracef("Committing the transaction.")        
            system.db.commitTransaction(self.txId)
    
        except:
            log.errorf("Caught an error updating the Chart Hierarchy - rolling back database transactions")
            errorTxt = catchError("Updating the Chart Hierarchy - rolling back database transactions")
            print errorTxt
            system.db.rollbackTransaction(self.txId)
            system.db.closeTransaction(self.txId)
            raise Exception(errorTxt)
        
        if len(warnings) > 0:
            print "The save completed with the following warnings: %s" % (str(warnings))
    
        log.infof("...done with updateChartHierarchy()!")


    def checkForUniqueStepNames(self):
        '''
        Verify step name uniqueness. 
        '''
        log.tracef("******************************************************")
        log.infof("Checking for unique step names on chart: %s (%s)", self.chartPath, self.resourceId)
        log.tracef("******************************************************")
    
        parseLog.tracef("The chart XML is: %s", str(self.chartXML))
        
        SQL = "select * from SfcChart where ChartResourceId = %s" % (self.resourceId)
        pds =  system.db.runQuery(SQL, tx=self.txId)

        record = pds[0]
        chartId = record["ChartId"]
        chartPath = record["ChartPath"]
        log.tracef("ChartId: %d", chartId)
        
        warnings = []
            
        ''' Iterate over steps in the chart '''
        stepNames = []
        for step in self.steps:
            stepName = string.upper(step["name"])
            if stepName in stepNames:
                warnings.append("There are two or more steps named: %s on chart %s" % (stepName, chartPath))
 
            stepNames.append(stepName)
        
    def updateChartSteps(self, stepsToDelete):
        '''
        This is the second pass of updating the database for an updated resource.  In this pass, I update the step catalog and the chart hierarchy. 
        '''
        SQL = "select * from SfcChart where ChartResourceId = %s" % (self.resourceId)
        pds =  system.db.runQuery(SQL, tx=self.txId)
        
        if len(pds) == 0:
            log.warnf("Unable to update chart steps for resource id: %s", self.resourceId)
            return stepsToDelete
        
        record = pds[0]
        chartId = record["ChartId"]
        
        warnings = []
    
        try:
            '''
            Handle the step catalog - we need this so that we can have a recipe editor.
            '''
            log.tracef("------------------")
            log.infof("Updating steps for chart: %s, resource id: %s, chartId: %d", self.chartPath, self.resourceId, chartId)
            log.tracef("------------------")
            
            pds = system.db.runQuery("select * from sfcStepView where ChartId = %d" % (chartId), tx=self.txId)
            self.databaseStepsDataset = system.dataset.toDataSet(pds)

            log.tracef("Existing steps in the database:")
            for row in range(self.databaseStepsDataset.getRowCount()):
                log.tracef("  %s, %s, a %s", self.databaseStepsDataset.getValueAt(row, "StepName"), self.databaseStepsDataset.getValueAt(row, "StepUUID"), self.databaseStepsDataset.getValueAt(row, "StepType"))

            updateCntr = 0
            insertCntr = 0
            renameCntr = 0
            moveCntr = 0
            
            ''' Iterate over steps in the chart '''
            for step in self.steps:
                stepTypeId = fetchStepTypeIdFromFactoryId(step["type"], self.txId)
                stepUUID = step["id"]
                stepName = step["name"]
                stepType = step["type"]
                log.tracef("Looking at chart step %s - %s - a %s...", stepName, stepUUID, stepType)
            
                stepIsInDatabase, idx = self.checkIfStepIsInDatabase(stepName, stepUUID)
                if stepIsInDatabase:
                    log.tracef("   ...step already exists in database, checking if it needs to be updated...")

                    if string.upper(stepName) == self.databaseStepsDataset.getValueAt(idx, "StepName") \
                        and stepUUID == self.databaseStepsDataset.getValueAt(idx,"StepUUID"):
                        log.tracef("...found the step (name: %s, step type: %s-%s) in the database list...", stepName, stepType, str(stepTypeId))
                        updateIt = False
                        if chartId <> self.databaseStepsDataset.getValueAt(idx,"ChartId"):
                            updateIt = True
                            log.tracef("...the chartId has been changed from %s to %s", str(self.databaseStepsDataset.getValueAt(idx,"ChartId")), str(chartId))
                        if stepTypeId <> self.databaseStepsDataset.getValueAt(idx,"StepTypeId"):
                            log.tracef("...the stepType has been changed from %s to %s", str(self.databaseStepsDataset.getValueAt(idx,"StepTypeId")), str(stepTypeId))
                            updateIt = True
                        if stepName <> str(self.databaseStepsDataset.getValueAt(idx,"StepName")):
                            ''' I don't think that this will ever be reached.  If we get through checkIfStepIsInDatabase90 then the stepNames match. '''
                            log.tracef("...the step has been renamed from %s to %s", stepName, str(self.databaseStepsDataset.getValueAt(idx,"StepName") ))
                            updateIt = True
    
                        if updateIt:
                            SQL = "update SfcStep set StepName = '%s', StepTypeId = %d, ChartId = %d where StepUUID = '%s'" % (stepName, stepTypeId, chartId, stepUUID)
                            rows = system.db.runUpdateQuery(SQL, tx=self.txId)
                            log.tracef("...updated %d existing steps", rows)
                            updateCntr = updateCntr + 1
                    
                    self.databaseStepsDataset = system.dataset.deleteRow(self.databaseStepsDataset, idx)
                else:
                    ''' Before we insert a new step, see if they renamed a step (on the same chart) by using the id '''
                    stepWasRenamed, idx = self.checkForRenamedStep(stepName, stepUUID)
                    if stepWasRenamed:
                        log.tracef("-- found a step <%s> that needs to be renamed --", stepName)
                        SQL = "update SfcStep set StepName = '%s', StepTypeId = %d, ChartId = %d where StepUUID = '%s'" % (stepName, stepTypeId, chartId, stepUUID)
                        rows = system.db.runUpdateQuery(SQL, tx=self.txId)
                        log.tracef("...updated %d existing steps", rows)
                        renameCntr = renameCntr + 1
                        self.databaseStepsDataset = system.dataset.deleteRow(self.databaseStepsDataset, idx)
        
                    else:
                        ''' 
                        Before we insert a step, check for a step that was cut and pasted in which case it will have the same name but a different UUID.
                        Search for a step with the same name but a different UUID on the same chart. The whole point of this is to maintain / copy
                        recipe data.  If they cut (or copied) a step, pasted it on the same diagram, and then renamed it BEFORE SAVING then they 
                        are screwed.  A common use case is to move a step into a parallel transition due to refactoring.  The only way to do this 
                        is by cutting and pasting the step.  To us, it looks like a new step.  
                        '''
                        log.tracef("...checking if step has been cut and pasted...")
                        SQL = "select * from SfcStep where StepName = '%s' "\
                            "and StepUUID != '%s' and StepTypeId = %d and chartId = %d" % (stepName, stepUUID, stepTypeId, chartId)
                        log.tracef(SQL)
                        pds = system.db.runQuery(SQL, tx=self.txId)
                        log.tracef("...%d step records were found...", len(pds))
                        
                        if len(pds) == 0 or len(pds) > 1:     
                            log.tracef("...inserting a new step <%s>, a %s with UUID %s into the database...", stepName, stepType, stepUUID)
                            SQL = "insert into SfcStep (StepName, StepUUID, StepTypeId, ChartId) values ('%s', '%s', %d, %d)" % (stepName, stepUUID, stepTypeId, chartId)
                            stepId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
                            log.tracef("...inserted a %s step with id: %d", stepType, stepId)
                            insertCntr = insertCntr + 1
                        else:
                            log.tracef("...the step has been cut and pasted!")
                            SQL = "insert into SfcStep (StepName, StepUUID, StepTypeId, ChartId) values ('%s', '%s', %d, %d)" % (stepName, stepUUID, stepTypeId, chartId)
                            stepId = system.db.runUpdateQuery(SQL, tx=self.txId, getKey=True)
                            log.tracef("...inserted a %s step with id: %d", stepType, stepId)
                            
                            record = pds[0]
                            oldStepId = record["StepId"]
                            oldChartId = record["ChartId"]

                            log.infof("******* NEED TO COPY RECIPE DATA HERE ********")                            
                            log.tracef("...copy recipe data from step id: %d to step id: %d", oldStepId, stepId)
                            from ils.sfc.recipeData.api import s88CopyRecipeData
                            s88CopyRecipeData(oldStepId, stepId, self.chartPath, stepName, txId=self.txId)
#                            SQL = "update SfcStep set StepName = '%s', ChartId = %d where StepId = %d" % (stepName, chartId, stepId)
#                            rows = system.db.runUpdateQuery(SQL, tx=self.txId)
#                            log.tracef("...updated %d existing steps", rows)
                            moveCntr = moveCntr + 1
            
            log.tracef("...%d steps were inserted...", insertCntr)
            log.tracef("...%d steps were renamed...", renameCntr)
            log.tracef("...%d steps were updated...", updateCntr)
            log.tracef("...%d steps were moved...", moveCntr)
            
            '''
            Anything that is left in the list of steps that we originally fetched from the database should be deleted from the database because as we found the step in the chart XML we removed
            it from this dataset.  Defer the delete of steps so that we have a chance of supporting a moved step from one chart to another.  If we delete the step before we move the step then
            we will automatically lose the recipe data.
            '''
            log.tracef("Checking for steps to delete from the database that have been deleted from the chart...")
            for row in range(self.databaseStepsDataset.getRowCount()):
                stepDict = {"chartId": chartId, "stepName": self.databaseStepsDataset.getValueAt(row, "stepName"), "stepUUID": self.databaseStepsDataset.getValueAt(row, "stepUUID")}
                stepsToDelete.append(stepDict)
                log.tracef("...adding %s to the step to delete list", str(stepDict))
    
            '''
            Now handle the chart hierarchy
            '''
            log.tracef("------------------")
            log.tracef("Updating the chart hierarchy with children...")
            log.tracef("the children from parsing the chart XML is: %s", str(self.children))
            log.tracef("------------------")
            
            # Fetch what is already in the database
            SQL = "Select * from SfcHierarchyView where ChartId = %d" % (chartId)
            childrenInDatabasePds = system.db.runQuery(SQL, tx=self.txId)
            from ils.common.database import toDictList
            chidrenInDatabaseList = toDictList(childrenInDatabasePds, [])
            log.tracef("...found %d children already in the database...", len(chidrenInDatabaseList))
    
            childInsertCntr = 0
            childUpdateCntr = 0
            for child in self.children:
                stepName = child.get("name")
                #childPath = child.get("childPath")
                stepUUID = child.get("id") 
                stepType = child.get("type")
                log.tracef("----------------------------")
                log.tracef("Checking stepName: %s, childPath: %s, stepUUID: %s, step type: %s...", stepName, child.get("childPath"), stepUUID, stepType)
                
                '''
                If the path of the called chart begins with a "." then it is a relative chart path and we need to concatenat the
                parent's path to the called chart path
                '''
                child["childPath"] = self.convertRelativeChartPath(child.get("childPath"))

                '''
                Compare the stepName and childPath from the Designer with what is already in the database
                '''
                insertChild = True
                for childDatabase in chidrenInDatabaseList:
                    log.tracef("...comparing to %s - %s", childDatabase["StepName"], childDatabase["ChildChartPath"])
                    if stepName == childDatabase["StepName"]:
                     
                        insertChild = False
                        if child.get("childPath") == childDatabase["ChildChartPath"]:
                            log.tracef("...this child already exists...")
                        else:
                            log.tracef("...this child already exists but is calling a different chart...")
                            childChartId = fetchChartIdFromChartPath(child.get("childPath"), self.txId)
                            log.tracef("...the new child chart Id is: %s", str(childChartId))
                            if childChartId == None:
                                log.errorf("Id not found for child chart, it will be created later hopefully,  with path: %s", child.get("childPath"))
                            
                            else:
                                stepId = fetchStepIdFromChartIdAndStepName(chartId, stepName, self.txId)
                                log.tracef("The step id of the child step named %s on chart %s is: %s", stepName, str(chartId), str(stepId))
    
                                SQL = "Update SfcHierarchy set ChildChartId = %d where StepId = %d" % (childChartId, stepId)
                                log.tracef("SQL: %s", SQL)
                                system.db.runUpdateQuery(SQL, tx=self.txId)
                                log.tracef("...updated %d calls %d into sfcHierarchy", stepId, childChartId) 
                                childUpdateCntr = childUpdateCntr + 1
    
                        break
                    
                if insertChild:            
                    log.tracef("--- Inserting a child into the hierarchy ---")
    
                    stepTypeId = fetchStepTypeIdFromFactoryId(child.get("type"), self.txId)
                    if stepTypeId == None:
                        log.errorf("Id not found for step type: %s", child.get("type"))
                
                    '''
                    In the normal workflow of creating SFCs, an encapsulation task cannot reference a chart until the referenced
                    chart is created.  We will get into problems when migrating tasks where we import a whole set of charts.
                    '''
                    
                    childChartId = fetchChartIdFromChartPath(child.get("childPath"), self.txId)
                    log.tracef("...the child chart Id is: %s", str(childChartId))
                    if childChartId == None:
                        log.errorf("Id not found for child chart, it will be created later hopefully,  with path: %s", child.get("childPath"))
                    
                    if stepTypeId <> None and childChartId <> None:
                        stepId = fetchStepIdFromChartIdAndStepName(chartId, stepName, self.txId)
                        log.tracef("The step id of the child step named %s on chart %s is: %s", stepName, str(chartId), str(stepId))
                                
                        SQL = "Insert into SfcHierarchy (StepId, ChartId, ChildChartId) values (%d, %d, %d)" % (stepId, chartId, childChartId)
                        system.db.runUpdateQuery(SQL, tx=self.txId)
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
            pds = system.db.runQuery(SQL, tx=self.txId)
            
            log.tracef("------------------")
            log.tracef("Updating the chart hierarchy with End Handlers...")
            log.tracef("------------------")
            
            onStopChartPath = parseHandlerXML(self.root, "onstop")
            updateHandler(pds, chartId, onStopChartPath, "onStop", self.txId)
    
            onCancelChartPath = parseHandlerXML(self.root, "oncancel")
            updateHandler(pds, chartId, onCancelChartPath, "onCancel", self.txId)
    
            onAbortChartPath = parseHandlerXML(self.root, "onabort")
            updateHandler(pds, chartId, onAbortChartPath, "onAbort", self.txId)
    
            '''
            Children will be automatically deleted because there is a cascade delete from the  children that are left in the list we fetched from the database.
            Steps that have been updated to point to a different child will be updated above.
            '''
            log.tracef("Committing the transaction.")        
            system.db.commitTransaction(self.txId)
    
        except:
            log.errorf("Caught an error updating the Chart Hierarchy in updateChartSteps() - rolling back database transactions")
            errorTxt = str(catchError("Updating the Chart Hierarchy - rolling back database transactions"))
            print errorTxt   # I don't know what it is about this string but whenever I send it through a logger I get another error 
            system.db.rollbackTransaction(self.txId)
            system.db.closeTransaction(self.txId)
            raise Exception(errorTxt)
        
        if len(warnings) > 0:
            print "The save completed with the following warnings: %s" % (str(warnings))
    
        log.infof("...done with updateChartHierarchy()!")
        return stepsToDelete
    
    def checkIfStepIsInDatabase(self, stepName, stepUUID):
        '''
        This checks if a stepname and step UUID from a chart resource is already in the database.
        '''
        log.tracef("   Checking if %s - %s is in the database...", stepName, stepUUID)
        for row in range(self.databaseStepsDataset.getRowCount()):
            log.tracef("        comparing to %s - %s", self.databaseStepsDataset.getValueAt(row, "StepName"),  self.databaseStepsDataset.getValueAt(row, "StepUUID"))
            if stepName == self.databaseStepsDataset.getValueAt(row, "StepName") \
                and stepUUID == self.databaseStepsDataset.getValueAt(row, "StepUUID"):
                log.tracef("        *** FOUND IT ****")
                return True, row

        log.tracef("      --- step is not in the database ---")
        return False, None
    
    def convertRelativeChartPath(self, childPath):
        '''
        The child's chart path is w.r.t the folder containing the calling chart, so immediately pop off the chart name
        '''
        tokens = childPath.split("/")
        if tokens[0] not in [".", ".."]:
            log.tracef("The child path is absolute!")
            return childPath
        
        log.infof("...converting a relative chart path <%s> <%s>...", self.chartPath, childPath)
        
        # Split the parent path into folders and drop the last token which is the chart name
        parentFolders = self.chartPath.split("/")
        del parentFolders[len(parentFolders)-1]
        
        for token in tokens:
            if token == ".":
                log.tracef("...starting at current folder...")
                childPath = childPath[1:]
                log.tracef("   <%s> <%s>", str(parentFolders), childPath)
            elif token == "..":
                log.tracef("...going up a level...")
                del parentFolders[len(parentFolders)-1]
                childPath = childPath[3:]
                log.tracef("   <%s> <%s>", '/'.join(parentFolders), childPath)
        
        parentPath = '/'.join(parentFolders)
        
        if childPath[0] == "/":
            childPath = childPath[1:]
        
        childPath = parentPath + "/" + childPath
        log.infof("...absolute chart path: <%s>", childPath)
        return childPath
    
    def checkForRenamedStep(self, stepName, stepUUID):
        '''
        This checks if a step UUID from a chart resource is already in the database, it is specifically for renamed steps where the name will not match but the UUID will.
        '''
        log.tracef("   Checking if %s - %s has been renamed...", stepName, stepUUID)
        for row in range(self.databaseStepsDataset.getRowCount()):
            log.tracef("     comparing to %s - %s", self.databaseStepsDataset.getValueAt(row, "StepName"),  self.databaseStepsDataset.getValueAt(row, "StepUUID"))
            if stepUUID == self.databaseStepsDataset.getValueAt(row, "StepUUID"):
                log.tracef("     *** STEP HAS BEEN RENAMED ****")
                return True, row

        log.tracef("      --- step has NOT been renamed ---")
        return False, None
    



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
