# Copyright 2015. ILS Automation. All rights reserved.

import system.ils.blt.diagram as script

# 
# We assume that the application record has already been inserted
def configureForTest(common,appName,famName):
	handler = script.getHandler()
	db = handler.getDefaultDatabase(name)

	appId=insertApplication(name,vfuConsoleId,db)
	return appId

# Place a result of "true" in the common dictionary
# if the family is found in the default database.
# Argument is the family name
def family(common,app,family):
	handler = script.getHandler()
	db = handler.getDefaultDatabase(name)
	SQL = "SELECT FamilyId FROM DtFamily "\
          " WHERE Application = '%s' "\
		  "  AND  Family = '%s';" % app,family
	val = system.db.runScalarQuery(SQL,db)
	if val != None:
		common['result'] = True
	else:
		common['result'] = False



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
def insertConsole(console,db):
	SQL = "delete from DtConsole where console='%s'" % (console)
	system.db.runUpdateQuery(SQL,db)
	SQL = "insert into DtConsole (console) values ('%s')" % (console)
	consoleId = system.db.runUpdateQuery(SQL,db, getKey=True)
	return consoleId
			
# Define an application
def insertApplication(appName, consoleId,db):
	SQL = "delete from DtApplication where application='%s'" % (appName)
	system.db.runUpdateQuery(SQL,db)
	SQL = "insert into DtApplication (application, ConsoleId) values ('%s', %i)" % (appName, consoleId)
	applicationId = system.db.runUpdateQuery(SQL,db getKey=True)
	return applicationId
