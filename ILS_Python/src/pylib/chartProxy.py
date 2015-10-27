# Copyright 2015. ILS Automation. All rights reserved.
# Execute a chart from a client/
import system.ils.sfc as ilssfc
import ils.sfc.gateway.msgHandlers as msghandler

# Argument is the chart path
def start(common,project,user,isolation,name):
	# Assemble initial properties for the chart, the run it.
	from ils.sfc.common.constants import PROJECT, USER, ISOLATION_MODE, CHART_NAME

	properties = dict()
	properties[PROJECT] = project
	properties[USER]    = user
	# ISOLATION_MODE must be a true boolean
	properties[ISOLATION_MODE] = str2bool(isolation)
	properties[CHART_NAME] = name;
	chartid = msghandler.sfcStartChart(properties)
	ilssfc.watchChart(chartid,name)
	common['result'] = chartid

def getState(common,chart,name):
	state = ilssfc.stepState(chart,name)
	common['result'] = state

# --------------------------- private ------------------
def str2bool(val):
	return val.lower() in ("true","yes","t","1")
	
