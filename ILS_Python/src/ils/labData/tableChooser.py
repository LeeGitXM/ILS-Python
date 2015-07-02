'''
Created on Mar 25, 2015

@author: Pete
'''
import system

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()"
    
    # Populate the list of all consoles - the selected console is passed from the console window and should be in the list
    SQL = "select post from TkPost order by post"
    pds = system.db.runQuery(SQL)
    rootContainer.posts=pds
    
    rootContainer.selectedPage = 1
    rootContainer.selectedPageName = 'Page 1'
    
    setNumberOfPages(rootContainer)

# update the list of display tables that are appropriate for the selected console
def internalFrameActivated(rootContainer):
    print "In internalFrameActivated()"
    populateRepeater(rootContainer)

def newPostSelected(rootContainer):
    print "In newPostSelected()"
    setNumberOfPages(rootContainer)
    populateRepeater(rootContainer)

def newPageSelected(rootContainer):
    print "In newConsoleSelected()"
    populateRepeater(rootContainer)

# Fetch the number of pages of lab data tables for the console and set up the tab strip    
def setNumberOfPages(rootContainer):
    print "In setNumberOfPages"
    selectedPost = rootContainer.selectedPost
    
    if selectedPost == "" or selectedPost == None:
        print "Error: Please select a post"
        return
    
    SQL = "Select max(DT.DisplayPage) "\
        "from LtDisplayTable DT, TkPost P "\
        "where DT.PostId = P.PostId "\
        " and P.Post = '%s' " % (selectedPost)
    numPages = system.db.runScalarQuery(SQL)
    rootContainer.numberOfPages = numPages
    
    print "The %s post has %s pages of lab data tables" % (selectedPost, str(numPages))
    configureTabStrip(rootContainer, numPages)
    rootContainer.selectedPage = 1

# Populate the template repeater with the table names for the selected post and page
def populateRepeater(rootContainer):
    print "In populateTablesForConsole"
    selectedPost = rootContainer.selectedPost
    selectedPage = rootContainer.selectedPage
    SQL = "Select DisplayTableTitle "\
        "from LtDisplayTable DT, TkPost P "\
        "where DT.PostId = P.PostId "\
        " and P.Post = '%s' "\
        " and DT.DisplayPage = %i "\
        " and DT.DisplayFlag = 1 "\
        "Order by DisplayOrder" % (selectedPost, selectedPage)        
    
    print SQL
    pds = system.db.runQuery(SQL)
    
    header = ['DisplayTableTitle', 'NewData']
    data = []
    for record in pds:
        displayTableTitle = record['DisplayTableTitle']
        print "Checking if %s has new data..." % (displayTableTitle)
        newData = checkForNewData(displayTableTitle)            
        data.append([displayTableTitle,newData])
    
    ds = system.dataset.toDataSet(header, data)
    repeater=rootContainer.getComponent("Template Repeater")
    rootContainer.displayTableTitles = ds

def checkForNewData(displayTableTitle):
    print "Checking ", displayTableTitle
    newData = False
    username = system.security.getUsername()
    SQL = "select V.ValueId "\
        " from LtValue V, LtDisplayTable T "\
        " where V.displayTableId = T.DisplayTableId "\
        " and T.DisplayTableTitle = '%s' "\
        " order by ValueName" % (displayTableTitle)
    pds = system.db.runQuery(SQL)
    
    for record in pds:
        valueId = record["ValueId"]
        SQL = "select H.SampleTime, VV.Username "\
            " from LtHistory  H LEFT OUTER JOIN "\
            " LtValueViewed VV ON H.HistoryId = VV.HistoryId "\
            " where ValueId = %i "\
            " and (VV.username = '%s' or VV.username is NULL)"\
            " order by SampleTime desc" % (valueId, username)

        vpds = system.db.runQuery(SQL)
        for vrecord in vpds:
            if vrecord["Username"] == None:
                print "There IS new data..."
                newData = True

    return newData

def configureTabStrip(rootContainer, numPages):
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


# This is called from the arrow button on the Lab Table selector screen.
# It selects the next post in the circular list of posts
def nextPostOBSOLETE(rootContainer):
    selectedPost = rootContainer.selectedPost
    posts = rootContainer.posts
    
    pds = system.dataset.toPyDataSet(posts)
    if len(pds) < 1:
        print "There are no posts in the post list"
        return
    
    if len(pds) == 1:
        print "There is only one post in the post list so there is nothing to scroll"
        return
    
    for row in range(len(pds)):
        post = pds[row][0]
        if post == selectedPost:
            if row == len(pds) - 1:
                selectedPost = pds[0][0]
            else:
                selectedPost = pds[row + 1][0]

            rootContainer.selectedPost = selectedPost
            # Now update the list of display tables that are appropriate for the newly selected console
            populateRepeater(rootContainer)
            return
