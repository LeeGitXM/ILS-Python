'''
Created on Feb 17, 2020

@author: phass
'''

from ils.log import getLogger
log =getLogger(__name__)

'''
This is called from the Tools menu and the designer hook
'''
def initialize(chartPath, chartXML):
    log.infof("In %s.initialize() for chart: %s", __name__, chartPath)
#    log.tracef("The initial chart XML is: %s", chartXML)    
    
    if str(chartPath) == "A/A":
        print "YOOOOOOOOOOOOOOO"
        chartXML = initializeRecipeDataForChart(chartPath, chartXML)
        print "Returning: ", chartXML
#    log.tracef("The initialized chart XML is: %s", chartXML)
    
    return chartXML

def initializeRecipeDataForChart(chartPath, chartXML):
    '''
    Clear the associated-data slot for each step. The chart XML is in XML, which is basically text.
    If I use XML tools to insert the recipe data into the chart XML then A) I have less control, and B) ET inserts all sort of 
    escape characters making it harder to read, which is the whole point of using XML.  So I am going to use text string
    manipulation to add things in. 
    '''
    log.tracef("=====================================")
    log.tracef("In %s.initializeRecipeDataForChart() - Processing recipe data for chart: %s", __name__, chartPath)
    log.tracef("=====================================")
    
    '''
    Split the XML for a chart into 3 parts: the preamble, the postamble, and the middle - which contains the steps.
    This makes it easy to put back together at the end.  We are going to insert recipe data into the steps part, but the pre and 
    post parts remain unchanged.
    '''

    newChartXML = ""
    txt = chartXML
    while len(txt) > 0:
        stepStart = txt.find("<step")
        if stepStart >= 0:
            stepEnd = txt.find("</step>") + 7
            stepTxt = txt[stepStart:stepEnd]
            txtEnd = len(txt)
            
            newStepTxt = processStep(chartPath, stepTxt)
            
            newChartXML = newChartXML + txt[0:stepStart] + newStepTxt
            txt = txt[stepEnd:txtEnd]
        else:
            newChartXML = newChartXML + txt
            txt = ""
        
    #log.tracef("----------------------------------------------------------")
    
    #log.tracef("Chart After: %s", str(newChartXML))
    return newChartXML


def processStep(chartPath, stepTxt):    
    stepName = stepTxt[stepTxt.find("name=")+6:]
    stepName = stepName[:stepName.find("\"")]
    
    associatedDataStart = stepTxt.find("<associated-data>")
    associatedDataEnd = stepTxt.rfind("</associated-data>") + 18
    
    if associatedDataStart > 0 and associatedDataEnd > 0:
        log.tracef("Found recipe data for step %s on chart %s", stepName, chartPath)
        log.tracef("   Step BEFORE removing associated data: %s", stepTxt)
        stepTxt = stepTxt[:associatedDataStart] + stepTxt[associatedDataEnd:]
        log.tracef("   Step AFTER removing associated data: %s", stepTxt)

    return stepTxt