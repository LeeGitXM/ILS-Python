'''
Created on Mar 25, 2015

@author: Pete
'''
import system

def internalFrameActivated(rootContainer):
    print "In internalFrameActivated()"
    
    # Populate the list of all consoles - the selected console is passed from the console window and should be in the list
    SQL = "select post from DtConsole order by post"
    pds = system.db.runQuery(SQL)
    rootContainer.posts=pds
    
    rootContainer.selectedPage = 1
    rootContainer.selectedPageName = 'Page 1'
    
    setNumberOfPages(rootContainer)
    
    # Now update the list of display tables that are appropriate for the selected console
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
    
    SQL = "Select max(DT.DisplayPage) "\
        "from LtDisplayTable DT, DtConsole C "\
        "where DT.ConsoleId = C.ConsoleId "\
        " and C.Post = '%s' " % (selectedPost)
    numPages = system.db.runScalarQuery(SQL)
    rootContainer.numberOfPages = numPages
    
    print "The %s console has %i pages of lab data tables" % (selectedPost, numPages)

# Populate the template repeater with the table names for the selected console and page
def populateRepeater(rootContainer):
    print "In populateTablesForConsole"
    selectedPost = rootContainer.selectedPost
    selectedPage = rootContainer.selectedPage
    SQL = "Select DisplayTableTitle "\
        "from LtDisplayTable DT, DtConsole C "\
        "where DT.ConsoleId = C.ConsoleId "\
        " and C.Post = '%s' "\
        " and DT.DisplayPage = %i "\
        "Order by DisplayOrder" % (selectedPost, selectedPage)
    
    print SQL
    pds = system.db.runQuery(SQL)
    for record in pds:
        print record['DisplayTableTitle']

    repeater=rootContainer.getComponent("Template Repeater")
    rootContainer.displayTableTitles = pds
    

# This is called from the arrow button on the Lab Table selector screen.
# It selects the next post in the circular list of posts
def nextPost(rootContainer):
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