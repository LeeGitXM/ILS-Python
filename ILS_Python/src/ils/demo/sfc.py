'''
Created on Jul 16, 2021

@author: phass
'''
import system, time
from ils.common.config import getTagProviderClient, getTagProvider

def start(operation):
    '''
    This is called from a client
    This doesn't really start running the chart, rather it opens the SFC control panel and if the startImmediately is True
    then the chart starts.
    '''
    print "Request to start: ", operation
    
    chartPath = "Demo\Main"
    controlPanelName = "Demo"
    tagProvider = getTagProviderClient()
    
    # Write the desired operation to the tag that the SFCF will check
    tagPath = "[%s]SFC/Demo/Operation" % (tagProvider)
    print "Writing <%s> to <%s>" % (operation, tagPath)
    system.tag.write(tagPath, operation)
    time.sleep(1)
    
    print "Starting the chart..."
    startImmediately = True
    from ils.sfc.client.windows.controlPanel import openDynamicControlPanel
    openDynamicControlPanel(chartPath, startImmediately, controlPanelName, "LOWER-RIGHT")