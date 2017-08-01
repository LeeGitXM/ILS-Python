'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, state):
    ''' Abort the chart execution'''
    from ils.sfc.common.constants import DEACTIVATED, CANCELLED
    from ils.sfc.gateway.api import cancelChart, addControlPanelMessage, getChartLogger,handleUnexpectedGatewayError

    try:
        print 'cancel.py', state
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        if not (state == DEACTIVATED or state == CANCELLED):
            cancelChart(chartScope)
            addControlPanelMessage(chartScope, "Chart canceled", "Error", False)
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in cancel.py', chartLogger)
    finally:
        return True
