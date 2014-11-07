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
    
def lazyInitializeClientEnvironment(database):  
    '''ensure that any required initialization of the client environment
       has been done, but don't re-initialize'''
    from ils.common.units import Unit
    Unit.lazyInitialize(database)
       
def runChart(chartName):
    from ils.sfc.common.sessions import createSession 
    from ils.sfc.common.util import getDatabaseFromSystem
    from ils.sfc.client.controlPanel import createControlPanel
    project = system.util.getProjectName()
    database = getDatabaseFromSystem()
    lazyInitializeClientEnvironment(database)
    user = system.security.getUsername()
    initialChartProps = dict()
    initialChartProps[PROJECT] = project
    initialChartProps[CHART_NAME] = chartName
    initialChartProps[USER] = user
    initialChartProps[DATABASE] = database
    system.util.sendMessage(project, 'sfcStartChart', initialChartProps, "G")
   
def onStop(chartProperties):
    '''this should be called from every SFC chart's onStop hook'''
    updateSessionStatus(chartProperties, STOPPED)
    
def onAbort(chartProperties):
    '''this should be called from every SFC chart's onPause hook'''
    updateSessionStatus(chartProperties, ABORTED)
    
 