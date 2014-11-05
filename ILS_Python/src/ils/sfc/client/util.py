'''
Created on Oct 31, 2014

@author: rforbes
'''
import system.util 
from ils.sfc.common.constants import *
from ils.sfc.common.sessions import updateSessionStatus
from ils.sfc.client.controlPanel import ControlPanel

def sendResponse(request, response):
    ''' send a message to the Gateway in response to a previous request message''' 
    replyPayload = dict() 
    replyPayload[RESPONSE] = response
    messageId = request[MESSAGE_ID]
    replyPayload[MESSAGE_ID] = messageId    
    project = system.util.getProjectName()
    system.util.sendMessage(project, 'sfcResponse', replyPayload, "G")
    
def runChart(chartName):
    ''' Send a message to the gateway w. context info telling it to run an SFC'''
    from ils.sfc.common.sessions import createSession 
    from ils.sfc.common.util import getDatabaseFromSystem
    from ils.sfc.client.controlPanel import createControlPanel
    project = system.util.getProjectName()
    #TODO: remove this debug value:
    database = getDatabaseFromSystem()
    user = system.security.getUsername()
    initialChartProps = dict()
    initialChartProps[PROJECT] = project
    initialChartProps[CHART_NAME] = chartName
    initialChartProps[USER] = user
    initialChartProps[DATABASE] = database
    '''Run an SFC. At the moment, this could live on the client as well'''
    chartRunId = system.sfc.startChart(chartName, initialChartProps)
    # mimic what happens to the internal chart props: addition of instanceId
    initialChartProps[INSTANCE_ID] = chartRunId
    createSession(user, chartName, chartRunId, database)
    createControlPanel(initialChartProps)
   
def onStop(chartProperties):
    '''this should be called from every SFC chart's onStop hook'''
    updateSessionStatus(chartProperties, STOPPED)
    
def onAbort(chartProperties):
    '''this should be called from every SFC chart's onPause hook'''
    updateSessionStatus(chartProperties, ABORTED)
    
 