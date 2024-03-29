'''
Created on Mar 25, 2015

@author: Pete
'''
import system
from ils.log import getLogger
log =getLogger(__name__)

'''
This runs in client scope and is called from a client message handler...
'''
def newLabDataMessageHandler(payload):
    log.tracef("In %s.newLabDataMessageHandler() - Handling a new lab data message...", __name__)
    
    windows = system.gui.getOpenedWindows()
    for window in windows:
        windowPath = window.getPath()
        if windowPath == "Lab Data/Lab Table Chooser":
            rootContainer = window.rootContainer
            log.tracef("-------------------")
            log.tracef("There is an open lab data chooser window ")
            
            populateRepeater(rootContainer)
            animatePageTabs(rootContainer)
    

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()", __name__)
    
    # Populate the list of all consoles - the selected console is passed from the console window and should be in the list
    SQL = "select post from TkPost order by post"
    pds = system.db.runQuery(SQL)
    rootContainer.posts=pds
    
    rootContainer.selectedPage = 1
    rootContainer.selectedPageName = 'Page 1'
    
    setNumberOfPages(rootContainer)

# update the list of display tables that are appropriate for the selected console
def internalFrameActivated(rootContainer):
    log.tracef("In %s.internalFrameActivated()", __name__)
    populateRepeater(rootContainer)
    animatePageTabs(rootContainer)

def newPostSelected(rootContainer):
    log.tracef("In %s.newPostSelected()", __name__)
    setNumberOfPages(rootContainer)
    populateRepeater(rootContainer)

def newPageSelected(rootContainer):
    log.tracef("In %s.newPageSelected()", __name__)
    populateRepeater(rootContainer)

# Fetch the number of pages of lab data tables for the console and set up the tab strip    
def setNumberOfPages(rootContainer):
    log.tracef("In %s.setNumberOfPages", __name__)
    selectedPost = rootContainer.selectedPost
    
    if selectedPost == "" or selectedPost == None:
        log.errorf("Error: Please select a post")
        return
    
    SQL = "Select max(DT.DisplayPage) "\
        "from LtDisplayTable DT, TkPost P "\
        "where DT.PostId = P.PostId "\
        " and P.Post = '%s' " % (selectedPost)
    numPages = system.db.runScalarQuery(SQL)
    rootContainer.numberOfPages = numPages
    
    log.tracef("The %s post has %s pages of lab data tables", selectedPost, str(numPages))
    configureTabStrip(rootContainer, numPages)
    rootContainer.selectedPage = 1

# Populate the template repeater with the table names for the selected post and page
def animatePageTabs(rootContainer):
    numberOfPages = rootContainer.numberOfPages
    tabStrip=rootContainer.getComponent("Tab Strip")
    tabDataDS=tabStrip.tabData
    
    if numberOfPages <= 1:
        return
    
    log.tracef("In In labData.tableChooser.animatePageTabs")
    selectedPost = rootContainer.selectedPost
    for selectedPage in range(1, numberOfPages+1):
        log.tracef("Checking Page %s", str(selectedPage))
        SQL = "Select DisplayTableTitle "\
            "from LtDisplayTable DT, TkPost P "\
            "where DT.PostId = P.PostId "\
            " and P.Post = '%s' "\
            " and DT.DisplayPage = %i "\
            " and DT.DisplayFlag = 1 "\
            "Order by DisplayOrder" % (selectedPost, selectedPage)        

        pds = system.db.runQuery(SQL)
        
        data = []
        tabNewData=False
        for record in pds:
            displayTableTitle = record['DisplayTableTitle']
            newData = checkForNewData(displayTableTitle)            
            data.append([displayTableTitle,newData])
            tabNewData = tabNewData or newData
        
        if tabNewData:
            unselectedGradientStartColor=system.gui.color(255,0,0)
            unselectedGradientEndColor=system.gui.color(217,0,0)
            selectedBackgroundColor=system.gui.color(255,0,0)
            log.tracef("  There is new data - Make it red")
        else:
            log.tracef("  There is NOT new data - Make it grey")
            unselectedGradientStartColor=system.gui.color(238,236,232)
            unselectedGradientEndColor=system.gui.color(170,170,170)
            selectedBackgroundColor=system.gui.color(238,236,232,255)
            
        tabDataDS=system.dataset.setValue(tabDataDS, selectedPage - 1, "UNSELECTED_GRADIENT_START_COLOR", unselectedGradientStartColor)
        tabDataDS=system.dataset.setValue(tabDataDS, selectedPage - 1, "UNSELECTED_GRADIENT_END_COLOR",   unselectedGradientEndColor)
        tabDataDS=system.dataset.setValue(tabDataDS, selectedPage - 1, "SELECTED_BACKGROUND_COLOR", selectedBackgroundColor)

    tabStrip.tabData=tabDataDS


# Populate the template repeater with the table names for the selected post and page
def populateRepeater(rootContainer):
    log.tracef("In %s.populateRepeater()", __name__)
    selectedPost = rootContainer.getPropertyValue("selectedPost")
    selectedPage = rootContainer.getPropertyValue("selectedPage")
    SQL = "Select DisplayTableTitle "\
        "from LtDisplayTable DT, TkPost P "\
        "where DT.PostId = P.PostId "\
        " and P.Post = '%s' "\
        " and DT.DisplayPage = %i "\
        " and DT.DisplayFlag = 1 "\
        "Order by DisplayOrder" % (selectedPost, selectedPage)        

    pds = system.db.runQuery(SQL)
    
    SQL = "select ValueName, V.ValueId, MAX(reportTime) maxTime "\
        " from LtHistory H, LtValue V "\
        " where H.ValueId = V.ValueId "\
        " group by V.ValueId, V.ValueName "\
        " order by maxTime desc"
    maxTimePds = system.db.runQuery(SQL)
    
    header = ['DisplayTableTitle', 'NewData']
    data = []
    for record in pds:
        displayTableTitle = record['DisplayTableTitle']
        newData = checkForNewData2(displayTableTitle, maxTimePds)          
        data.append([displayTableTitle,newData])
    
    ds = system.dataset.toDataSet(header, data)
    rootContainer.displayTableTitles = ds

def checkForNewData(displayTableTitle):
    log.tracef("In labData.tableChooser.checkForNewData()...")
    log.tracef(" ---- Checking Table: %s", displayTableTitle)
    newData = False

    username = system.security.getUsername()
    
    # Select the values in the table of interest
    SQL = "select V.ValueId, V.ValueName "\
        " from LtValue V, LtDisplayTable DT, LtDisplayTableDetails DTD "\
        " where DTD.displayTableId = DT.DisplayTableId "\
        " and DTD.ValueId = V.ValueId"\
        " and DT.DisplayTableTitle = '%s' "\
        " order by ValueName" % (displayTableTitle)
    pds = system.db.runQuery(SQL)
    
    # Now try to figure out it there is new data  
    for record in pds:
        valueId = record["ValueId"]
        valueName = record["ValueName"]
        
        # Fetch the newest report time
        SQL = "select max(ReportTime) "\
            " from LtHistory "\
            " where ValueId = %i " % (valueId)

        mostRecentReportTime = system.db.runScalarQuery(SQL)
        log.tracef("The most recent report time for %s is %s", valueName, str(mostRecentReportTime))
        
        if mostRecentReportTime != None:
            SQL = "select viewTime "\
                " from LtValueViewed "\
                " where ValueId = %i "\
                " and username = '%s' " % (valueId, username)

            lastViewedTime = system.db.runScalarQuery(SQL)
            log.tracef("   ...and the last Viewed time is: %s", str(lastViewedTime))
            if lastViewedTime == None or mostRecentReportTime > lastViewedTime:
                newData = True
                log.tracef("   ---There IS new data---")
        
    return newData

def checkForNewData2(displayTableTitle, maxTimePds):
    log.tracef("In %s.labData.tableChooser.checkForNewData2()...", __name__)
    log.tracef(" ---- Checking Table: %s", displayTableTitle)
    newData = False

    username = system.security.getUsername()
    
    # Select the values in the table of interest
    SQL = "select V.ValueId, V.ValueName "\
        " from LtValue V, LtDisplayTable DT, LtDisplayTableDetails DTD "\
        " where DTD.displayTableId = DT.DisplayTableId "\
        " and DTD.ValueId = V.ValueId"\
        " and DT.DisplayTableTitle = '%s' "\
        " order by ValueName" % (displayTableTitle)
    pds = system.db.runQuery(SQL)
    
    # Now try to figure out it there is new data  
    for record in pds:
        valueId = record["ValueId"]
        valueName = record["ValueName"]
        
        for rec in maxTimePds:
            if valueId == rec["ValueId"]:
                mostRecentReportTime = rec["maxTime"]
                log.tracef("Found max time of %s for %s", str(mostRecentReportTime), valueName)
        
        # Fetch the newest report time
        SQL = "select max(ReportTime) "\
            " from LtHistory "\
            " where ValueId = %i " % (valueId)

        mostRecentReportTime = system.db.runScalarQuery(SQL)
        log.tracef("The most recent report time for %s is %s", valueName, str(mostRecentReportTime))  
        
        if mostRecentReportTime != None:
            SQL = "select viewTime "\
                " from LtValueViewed "\
                " where ValueId = %i "\
                " and username = '%s' " % (valueId, username)
    
            lastViewedTime = system.db.runScalarQuery(SQL)
            log.tracef("   ...and the last Viewed time is: %s", str(lastViewedTime))
            if lastViewedTime == None or mostRecentReportTime > lastViewedTime:
                newData = True
                log.tracef("   ---There IS new data---")
        
    return newData


def configureTabStrip(rootContainer, numPages):
    log.tracef("In %s.configureTabStrip()...", __name__)
    tabStrip=rootContainer.getComponent("Tab Strip")

    header=["NAME","DISPLAY_NAME","HOVER_COLOR","SELECTED_IMAGE_PATH","SELECTED_IMAGE_HORIZONTAL_ALIGNMENT","SELECTED_IMAGE_VERTICAL_ALIGNMENT","SELECTED_FOREGROUND_COLOR","SELECTED_BACKGROUND_COLOR","SELECTED_FONT","SELECTED_GRADIENT_START_COLOR","SELECTED_GRADIENT_END_COLOR","UNSELECTED_IMAGE_PATH","UNSELECTED_IMAGE_HORIZONTAL_ALIGNMENT","UNSELECTED_IMAGE_VERTICAL_ALIGNMENT","UNSELECTED_FOREGROUND_COLOR","UNSELECTED_BACKGROUND_COLOR","UNSELECTED_FONT","UNSELECTED_GRADIENT_START_COLOR","UNSELECTED_GRADIENT_END_COLOR","USE_SELECTED_GRADIENT","USE_UNSELECTED_GRADIENT","MOUSEOVER_TEXT"]
    data=[]
    if numPages == 0 or numPages == None:
        ds = system.dataset.toDataSet(header, data)
        tabStrip.tabData=ds
        return
    
    for i in range(1, numPages + 1):
        pageTitle="Page %i" % (i)
        data.append([pageTitle,pageTitle,"color(250,214,138,255)","","-1","-1","color(0,0,0,255)","color(238,236,232,255)","font(Dialog,PLAIN,12)","color(238,236,232,255)","color(238,236,232,255)","","-1","-1","color(0,0,0,255)","color(238,236,232,255)","font(Dialog,PLAIN,12)","color(238,236,232,255)","color(170,170,170,255)","false","true",""])
    
    ds = system.dataset.toDataSet(header, data)
    tabStrip.tabData=ds