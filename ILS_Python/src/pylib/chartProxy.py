# Copyright 2015. ILS Automation. All rights reserved.
# Execute a chart from a client/
import system
import system.ils.sfc as ilssfc
import system.ils.tf as testframe


# Argument is the chart path
def start(common,path,isolation):
	project = testframe.getProjectName() 
	user = testframe.getUserName()
	try:
		chartid = ilssfc.debugChart(path,project,user, str2bool(isolation))
	except:
		chartid = "none"
	print path,chartid,project,user,isolation,str2bool(isolation)
	ilssfc.watchChart(str(chartid),path)
	common['result'] = str(chartid)

def getProviderName(common,isIsolationMode):
	name = ilssfc.getProviderName(str2bool(isIsolationMode))
	common['result'] = name

def getChartState(common,chartid):
	state = ilssfc.chartState(chartid)
	common['result'] = state
		
def getStepState(common,chartid,name):
	state = ilssfc.stepState(chartid,name)
	common['result'] = state
	
def getStepCount(common,chartid,name):
	state = ilssfc.stepCount(chartid,name)
	common['result'] = state
	
def postResponse(common,chartPath,stepName,text):
	ilssfc.postResponse(chartPath,stepName,text)
# --------------------------- private ------------------
def str2bool(val):
	return val.lower() in ("true","yes","t","1")
	
