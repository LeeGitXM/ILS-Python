# Copyright 2015. ILS Automation. All rights reserved.
# Execute a chart from a client/
import system
import system.ils.sfc as ilssfc
import system.ils.tf as testframe
from ils.sfc.recipeData.api import s88GetFromName, s88SetFromName

logger=system.util.getLogger("com.ils.pylib.chartProxy")


# SFC Testing requires:
#  1) [default]CurrentChartId
#  2) Database row for "scratch" 
def prepareForTest(common, isolationMode):
	tagPath="[default]CurrentChartId"
	if not(system.tag.exists(tagPath)):
		system.tag.addTag(parentPath="[default]",name="CurrentChartId",tagType="MEMORY",dataType="String")
	tagPath="[default]CurrentChartPath"
	if not(system.tag.exists(tagPath)):
		system.tag.addTag(parentPath="[default]",name="CurrentChartPath",tagType="MEMORY",dataType="String")
		
	db = ilssfc.getDatabaseName(isolationMode)  # Assume isolation
	try:
		SQL = "INSERT INTO SfcControlPanel(controlPanelId,controlPanelName,chartPath,isolationMode,enablePause,enableResume,enableCancel) VALUES(-42,'scratch','tbd',1,1,1,1)"
		system.db.runUpdateQuery(SQL,db)
	except:
		pass # Ignore error

# Update the standard console record for the given chart
def updateConsoleRecord(common,path,controlPanelName,isolationMode):
	db = ilssfc.getDatabaseName(isolationMode)  # Assume isolation
	SQL = "UPDATE SfcControlPanel set chartPath='%s' "\
		" WHERE controlPanelName='%s'" % (path, controlPanelName)
	system.db.runUpdateQuery(SQL,db)

def getRecipeData(common,path,stepName,keyAndAttribute,isolationMode):
	logger.infof("*************************************************** s88GetFromName():  %s * %s * %s", path, stepName, keyAndAttribute)
	db = ilssfc.getDatabaseName(isolationMode)
	data = s88GetFromName(path, stepName, keyAndAttribute, db)
	common['result'] = str(data)
	
def setRecipeData(common,path,stepName,keyAndAttribute,theValue,isolationMode):
	logger.infof("*************************************************** s88SetFromName():  %s * %s * %s : %s", path, stepName, keyAndAttribute, theValue)
	db = ilssfc.getDatabaseName(isolationMode)
	s88SetFromName(path, stepName, keyAndAttribute, theValue, db)

	
# Argument is the chart path
def start(common,path,isolationMode):
	project = testframe.getProjectName() 
	user = testframe.getUserName()
	try:
		chartid = ilssfc.debugChart(path,project,user,str2bool(isolationMode))
	except:
		chartid = "none"
	print "chartProxy.start:",path,chartid,project,user,isolationMode,str2bool(isolationMode)
	ilssfc.watchChart(str(chartid),path)
	common['result'] = str(chartid)

def getDatabaseName(common,isolationMode):
	name = ilssfc.getDatabaseName(str2bool(isolationMode))
	common['result'] = name
	
def getProviderName(common,isolationMode):
	name = ilssfc.getProviderName(str2bool(isolationMode))
	common['result'] = name

def getChartState(common,chartid):
	state = ilssfc.chartState(chartid)
	common['result'] = state

# --------------------------- private ------------------
def str2bool(val):
	return val.lower() in ("true","yes","t","1")
	
