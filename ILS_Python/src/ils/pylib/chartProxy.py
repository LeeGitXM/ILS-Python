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
def prepareForTest(common):
	tagPath="[default]CurrentChartId"
	if not(system.tag.exists(tagPath)):
		system.tag.addTag(parentPath="[default]",name="CurrentChartId",tagType="MEMORY",dataType="String")
	tagPath="[default]CurrentChartPath"
	if not(system.tag.exists(tagPath)):
		system.tag.addTag(parentPath="[default]",name="CurrentChartPath",tagType="MEMORY",dataType="String")
		
	db = ilssfc.getDatabaseName(True)  # Assume isolation
	try:
		SQL = "INSERT INTO SfcControlPanel(controlPanelId,controlPanelName,chartPath,isolationMode,enablePause,enableResume,enableCancel) VALUES(-42,'scratch','tbd',1,1,1,1)"
		system.db.runUpdateQuery(SQL,db)
	except:
		pass # Ignore error

# Update the standard console record for the given chart
def updateConsoleRecord(common,path):
	db = ilssfc.getDatabaseName(True)  # Assume isolation
	SQL = "UPDATE SfcControlPanel set chartPath='%s' "% (path)
	SQL = SQL + " WHERE controlPanelName='scratch'"
	system.db.runUpdateQuery(SQL,db)

def getRecipeData(common,path,stepName,keyAndAttribute):
	logger.infof("*************************************************** s88GetFromName():  %s * %s * %s", path, stepName, keyAndAttribute)
	db = ilssfc.getDatabaseName(False)
	data = s88GetFromName(path, stepName, keyAndAttribute, db)
	common['result'] = str(data)
	
def setRecipeData(common,path,stepName,keyAndAttribute,theValue):
	logger.infof("*************************************************** s88SetFromName():  %s * %s * %s : %s", path, stepName, keyAndAttribute, theValue)
	db = ilssfc.getDatabaseName(False)
	s88SetFromName(path, stepName, keyAndAttribute, theValue, db)

	
# Argument is the chart path
def start(common,path,isolation):
	project = testframe.getProjectName() 
	user = testframe.getUserName()
	try:
		chartid = ilssfc.debugChart(path,project,user,str2bool(isolation))
	except:
		chartid = "none"
	print "chartProxy.start:",path,chartid,project,user,isolation,str2bool(isolation)
	ilssfc.watchChart(str(chartid),path)
	common['result'] = str(chartid)

def getDatabaseName(common,isIsolationMode):
	name = ilssfc.getDatabaseName(str2bool(isIsolationMode))
	common['result'] = name
	
def getProviderName(common,isIsolationMode):
	name = ilssfc.getProviderName(str2bool(isIsolationMode))
	common['result'] = name

def getChartState(common,chartid):
	state = ilssfc.chartState(chartid)
	common['result'] = state

		
# --------------------------- private ------------------
def str2bool(val):
	return val.lower() in ("true","yes","t","1")
	
