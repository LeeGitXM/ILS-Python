'''
Created on Dec 16, 2015

@author: rforbes
'''

def activate(scopeContext, stepProperties, state):
    ''' Abort the chart execution'''
    from ils.sfc.common.constants import DEACTIVATED, CANCELLED
    from ils.sfc.gateway.api import cancelChart, addControlPanelMessage, getChartLogger,handleUnexpectedGatewayError

    try:
        chartScope = scopeContext.getChartScope()
        chartLogger = getChartLogger(chartScope)
        if not (state == DEACTIVATED or state == CANCELLED):
            cancelChart(chartScope)
            addControlPanelMessage(chartScope, stepProperties, "Chart canceled", "Error", False)
    except SystemExit:
        chartLogger.info("The chart has been cancelled!")
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in cancel.py', chartLogger)
    finally:
        return True
