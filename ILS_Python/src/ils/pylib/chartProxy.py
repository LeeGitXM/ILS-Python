# Copyright 2015. ILS Automation. All rights reserved.
# Execute a chart from a client/
import system
import system.ils.sfc as ilssfc
import system.ils.tf as testframe
from ils.sfc.recipeData.api import s88GetFromName, s88SetFromName

from ils.log import getLogger
logger = getLogger(__name__)

'''
If we are starting a chart from the top then we don't need to call this.
'''
def prepareForTest(common, isolationMode):
	tagPath="[default]CurrentChartId"
	if not(system.tag.exists(tagPath)):
		system.tag.addTag(parentPath="[default]",name="CurrentChartId",tagType="MEMORY",dataType="String")
	tagPath="[default]CurrentChartPath"
	if not(system.tag.exists(tagPath)):
		system.tag.addTag(parentPath="[default]",name="CurrentChartPath",tagType="MEMORY",dataType="String")
		
	db = ilssfc.getDatabaseName(str2bool(isolationMode))  # Don't assume isolation
	try:
		SQL = "INSERT INTO SfcControlPanel(controlPanelId,controlPanelName,chartPath,isolationMode,enablePause,enableResume,enableCancel) VALUES(-42,'scratch','tbd',1,1,1,1)"
		system.db.runUpdateQuery(SQL,db)
	except:
		pass # Ignore error

'''
Update the standard console record for the given chart
'''
def updateConsoleRecord(common,path,controlPanelName,isolationMode):
	db = ilssfc.getDatabaseName(str2bool(isolationMode))  # Don't assume isolation
	SQL = "UPDATE SfcControlPanel set chartPath='%s' "\
		" WHERE controlPanelName='%s'" % (path, controlPanelName)
	system.db.runUpdateQuery(SQL,db)

def getRecipeData(common,path,stepName,keyAndAttribute,isolationMode):
	logger.tracef("s88GetFromName():  %s * %s * %s", path, stepName, keyAndAttribute)
	db = ilssfc.getDatabaseName(str2bool(isolationMode))
	data = s88GetFromName(path, stepName, keyAndAttribute, db)
	common['result'] = str(data)
	
def setRecipeData(common,path,stepName,keyAndAttribute,theValue,isolationMode):
	logger.tracef("s88SetFromName():  %s * %s * %s : %s", path, stepName, keyAndAttribute, theValue)
	if isolationMode in [True, "True"]:
		isolationMode = True
	else:
		isolationMode = False
	db = ilssfc.getDatabaseName(isolationMode)
	s88SetFromName(path, stepName, keyAndAttribute, theValue, db)
	
'''
Use this when starting a test at any chart other than the top.  This requires that the call stack be mocked up to simulate what is
built by the engine when running from the top.  This environment is necessary for the operation and global scope locators to work.
'''
def start(common,chartPath,isolationMode):
	project = testframe.getProjectName() 
	user = testframe.getUserName()
	try:
		chartid = ilssfc.debugChart(chartPath,project,user,str2bool(isolationMode))
	except:
		chartid = "none"
	print "chartProxy.start:",chartPath,chartid,project,user,isolationMode,str2bool(isolationMode)
	ilssfc.watchChart(str(chartid),chartPath)
	common['result'] = str(chartid)

'''
If starting from the top, i.e., the chart that has the Unit rocedure then use this.
This starts the chart in the exact same way as the console buttons start a chart, so the test framework is doing less, the hope being
that this will produce a more genuine test.
'''
def startFromTop(common, chartPath, controlPanelName, isolationMode):
	from ils.sfc.common.util import startChart
	project = testframe.getProjectName() 
	originator = testframe.getUserName()
	
	print "In startFromTop() - Isolation Mode: ", isolationMode
	if isolationMode in [True, "True"]:
		isolationMode = True
	else:
		isolationMode = False
		
	chartRunId = startChart(chartPath, controlPanelName, project, originator, isolationMode)
	common['result'] = str(chartRunId)

def getDatabaseName(common,isolationMode):
	name = ilssfc.getDatabaseName(str2bool(isolationMode))
	common['result'] = name
	
def getProviderName(common,isolationMode):
	name = ilssfc.getProviderName(str2bool(isolationMode))
	common['result'] = name

def getChartState(common,chartid):
	state = "NOT-FOUND"
	ds = system.sfc.getRunningCharts()
	for row in range(ds.rowCount):
		if ds.getValueAt(row, "instanceId") == chartid:
			state = ds.getValueAt(row, "chartState")
	common['result'] = state

# --------------------------- private ------------------
def str2bool(val):
	return val.lower() in ("true","yes","t","1")
	
