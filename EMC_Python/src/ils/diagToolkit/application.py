'''
Created on Sep 12, 2014

@author: Pete
'''

import system

# This is called from the Java Diag Toolkit Engine whenever a DiagToolkit Application is saved.
# This will handle newly created applications and changed ones.  Java will just pass the application
# object, I'll have to figure out how to get what I want out of it
def update(application):
    applicationName = 'Foo'
    GUID = 'ABD123'
    
    updateDatabase(GUID, applicationName)

def updateDatabase(GUID, applicationName):
    SQL = "select * from Application where GUID = '%s'" % (GUID)
    pds = system.db.runScalarQuery(SQL)
    if len(pds) == 0:
        # Insert a record into the Application table to define this application
        SQL = "insert into Application (GUID, ApplicationName, DiagnosisQueueKey) values (%s, %s, %s)" % (GUID, applicationName, applicationName)
        applicationId = system.db.runUpdateQuery(SQL)
        print "Created application with id: ", applicationId
        
        # Create a Message Queue for the Application
        title = "%s Diagnosis Queue" % (applicationName)
        SQL = "insert into QueueMaster (QueueKey, Title) values (%s, %s)" % (applicationName, title)
        queueId = system.db.runUpdateQuery(SQL)
        print "Created queue with id: ", queueId
    else:
        record = pds[0]
        oldName = record["ApplicationName"]
        SQL = "update application set ApplicationName = '%s', DiagnosisQueueKey = '%s' where GUID = '%s'" % (applicationName, applicationName, GUID)
        system.db.runUpdateQuery(SQL)
        
        SQL = "update QueueMaster set QueueKey = '%s' where QueueKey = '%s'" % (applicationName, oldName)
        system.db.runUpdateQuery(SQL)
        
         