'''
Created on Nov 13, 2016

@author: Pete
'''

import system, time

# Delete all of the models and results in Python and Java.  Also delete all of the real-time tables in the database
def initialize(rootContainer):       
    print "Initializing the engine and the database..."
    projectKey =rootContainer.key
    initializeDatabase()
    initializeEngine(projectKey)


# Initialize the real-time tables in the A E D database that keep track of Alerts and Suppression.
# This gives us a known starting point for the tests.  The test system should not be running other
# ad-hoc or automated testing.

def initializeDatabase():    
    print "   ...initializing the database..."
    system.tag.write("[]FT/Control/TestingStatus","Initializing")
    
    for table in ['CommentLog', 'ConditionLog', 'EventLog', 'Events', 'Suppressors', 'EvaluationNotes']:
        SQL = "delete from %s" % (table)
        rows = system.db.runUpdateQuery(SQL)
        print "Deleted %i rows from %s" % (rows, table)

# The final test suite requires a controlled environment.  Remove all running models from the engine.
# Rather than directly deleting them from the engine, use theRuleModelEditStatus table which will
# promote a consistent cleanup from the Java and the Python
def initializeEngine(project):
    import system.ils.aed.model as model
    
    print "   ...initializing the engine..."
    
    results = model.getExecutionResults(project)

        # Stop execution of this project
#        print "   ...stopping " + project
#        model.stopModelExecution(project)
        
#        print ""
#        print "*** Project %s Results ***" % (project)
#        print results
    for result in results:
#            print ""
#            print result
        id = result.get('id', -1)
        if id > 0:
            print "   ...deleting %s - %s" % (project, id)
            SQL = "insert into RuleModelEditStatus (RuleId, Action) values (%s, 'delete')" % (id)
            system.db.runUpdateQuery(SQL)

    # Wait until the running engine picks up the ids to be deleted and deletes them...
    waiting = True
    while waiting:
        time.sleep(5.0)    
        results = model.getExecutionResults(project)
        # There is always a header
        print "There are ", len(results) - 1, " models still in the engine..."
        print "  ", results
        if len(results) < 2:
            waiting = False
            
    # Stop execution of this project
    print "Stopping execution..."
    model.stopModelExecution(project)
#    system.gui.messageBox("The results have been written to the console log")