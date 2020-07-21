'''
Created on Feb 17, 2020

@author: phass
'''

import system
from ils.sfc.recipeData.internalize import splitChartXML
log=system.util.getLogger("com.ils.sfc.recipeData.initialize")

'''
This is called from the Tools menu and the designer hook
'''
def initialize(chartPath, chartXML):
    log.infof("***************  PYTHON  *******************")
    log.infof("In %s.initialize() for chart: %s", __name__, chartPath)
    log.tracef("The initial chart XML is: %s", chartXML)
    
    '''
    This already does all the work of eliminating the associated data.  This was done as part of the internalize method to provide a clean slate!
    '''
    preamble, postamble, steps = splitChartXML(chartXML, log)

    ''' All I have to do is paste the parts back together '''
    middle = ""
    for step in steps:
        middle = middle + step

    chartXML = preamble + middle + postamble
    log.tracef("The initialized chart XML is: %s", str(chartXML))
    
    return chartXML
