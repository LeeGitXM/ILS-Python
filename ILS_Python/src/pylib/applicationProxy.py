# Copyright 2015. ILS Automation. All rights reserved.

import system.ils.blt.diagram as script

def configureForTest(common,name):
	console = 'VFU'
	grade = '28'
	print "HEREEEE"

	handler = script.getHandler()
	db = handler.getDefaultDatabase(name)

	vfuConsoleId=getConsoleId(console,db)
	appId=insertOrUpdateApplication(name,vfuConsoleId,db)
	return appId

# Place a result of "true" in the common dictionary
# if the application is found in the default database.
# Argument is the application name
def exists(common,name):
	handler = script.getHandler()
	db = handler.getDefaultDatabase(name)
	SQL = "SELECT ApplicationId FROM DtApplication "\
          " WHERE Application = '%s';" % name
	val = system.db.runScalarQuery(SQL,db)
	if val != None:
		common['result'] = True
	else:
		common['result'] = False


#  This method refers to an application node in the Nav tree
def setState(common,name,state):
	print name,":",state
	script.setApplicationState(name,state)
# 
# =============================== Helper Methods =========================
# These are not directly callable from a test script
# 
# return the id of the named console. The console record is created 
#        if it does not currently exist.
def getConsoleId(console,db):
	SQL = "SELECT consoleId from DtConsole WHERE console='%s'" % (console)
	consoleId = system.db.runScalarQuery(SQL,db)
	if consoleId == None:
		SQL = "INSERT into DtConsole (console) values ('%s')" % (console)
		consoleId = system.db.runUpdateQuery(SQL,db, getKey=True)
	return consoleId
			
# Correlate a console with the named application.
# If the application does not exist, create it.
# Return the applicationId
def insertOrUpdateApplication(appName, consoleId,db):
	SQL = "SELECT from DtApplication where application='%s'" % (appName)
	applicationId = system.db.runScalarQuery(SQL,db)
	if applicationId == None:
		SQL = "INSERT into DtApplication (application, ConsoleId) values ('%s', %i)" % (appName, consoleId)
		applicationId = system.db.runUpdateQuery(SQL,db, getKey=True)
	else:
		SQL = "UPDATE DtApplication SET ConsoleId=%i WHERE applicationId =  %i" % (consoleId,applicationId)
		system.db.runUpdateQuery(SQL,db)

	return applicationId
