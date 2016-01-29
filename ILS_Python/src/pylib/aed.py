# Copyright 2016. ILS Automation. All rights reserved.
# 
# Scripts used for AED testing with the test framework
import datetime,time
import random
import system
import system.ils.tf as testframe
import xom.emre.simulation.setup as setup

#
# Create and populate the table for holding expression
# test data. This method creates 4 data columns.
# Tags in order are: constant,ramp,random,sawtooth.
def createExpressionTable(common,database,tableName,tag1,tag2,tag3,tag4):
	header=["TagPath","ColumnName","DataType"]
	ds = []
	ds.append([tag1,columnName(tag1),"float"])
	ds.append([tag2,columnName(tag2),"float"])
	ds.append([tag3,columnName(tag3),"float"])
	ds.append([tag4,columnName(tag4),"float"])
	mapping = system.dataset.toDataSet(header,ds)
	testframe.populateColumnTagMap(database, tableName, mapping)
	# Time column is tstamp 
	setup.createDataTable(database, tableName)
	setup.addIndex(database, tableName)
	
	populateTestTable(database,tableName,columnName(tag1),columnName(tag2),columnName(tag3),columnName(tag4))

# Create a single expression.
def createExpression(common,provider,path,text):
	testframe.createExpression(provider,path,"Float8",text)
			
# Create a set of expressions. The actual expression
# will be set later. Use the root name plus index.
def createExpressions(common,provider,root,count):
	for index in range(int(count)):
		testframe.createExpression(provider,root+str(index),"Float8","0.")
		
# Create a float tag.
def createTag(common,provider,path):
	testframe.createTag(provider,path,"Float8")


# Delete a tag or expression
def deleteTag(common,provider,path):
	testframe.deleteTag(provider,path);
	
def defineTablebasedTest(common,provider,database,table,timecol,mintime,maxtime,timefact):
	testframe.defineTablebasedTest(provider, database, table, timecol, mintime, maxtime, timefact)
	
def setExpressions(common,provider,root,count,expr):
	for index in range(int(count)):
		testframe.createExpression(provider,root+str(index),"Float8",expr)
	
# ==================================== Helper Functions ===============================
# Generate a column name from a tag name
def columnName(tagname):
	segments=tagname.split('/')
	return segments[-1]

# Fill a database table with sample data: constant,ramp,random,sawtooth
# Time column is: tstamp
# Time range is: 2000/01/01 00:00:00 for 100 minutes
def populateTestTable(database,table,col1,col2,col3,col4):
	date  = datetime.datetime(2000,01,01,00,00,00)
	system.db.runUpdateQuery("DELETE FROM "+table,database)
	
	# End of range is exclusive
	sql = "INSERT INTO "+table+"(tstamp,"+col1+","+col2+","+col3+","+col4+") VALUES(?,?,?,?,?)"
	
	minutes = 0
	stepspan = 10
	maxrandom = 10.
	for index in range(0,100):
		saw = index%stepspan
		r = random.random()*maxrandom
		system.db.runPrepUpdate(sql,[date,5,index,saw,r],database)
		date += datetime.timedelta(minutes=1)