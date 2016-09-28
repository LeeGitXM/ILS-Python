'''
Created on Apr 8, 2016

@author: ils
'''

import system, time

def showLogbookCallback(event):
    print "In showLogbookCallback()"
    button = event.source
    template = button.parent

    from java.util import Calendar
    cal = Calendar.getInstance()
    cal.set(Calendar.HOUR_OF_DAY, 0)
    cal.set(Calendar.MINUTE, 0)
    cal.set(Calendar.SECOND, 0)
    cal.set(Calendar.MILLISECOND, 0)
    startDate = cal.getTime()
    
    cal.set(Calendar.HOUR_OF_DAY, 23)
    cal.set(Calendar.MINUTE, 59)
    endDate = cal.getTime()
    
    logbookName = template.logbookName
    print "Opening logbook: ", logbookName 
    win = system.nav.openWindowInstance('Logbook/Logbook Viewer', {"logbook": logbookName, "startDate": startDate, "endDate": endDate})
    system.nav.centerWindow(win)
    
def getLogbookForPost(post):
    SQL = "select LogbookName from TkPost P, TkLogbook L "\
        " where P.logbookId = L.logbookId "\
        " and P.Post = '%s'" % (post)
    logbook = system.db.runScalarQuery(SQL)
    return logbook

def initializeView(rootContainer):
    print "Initializing..."
    dropdown = rootContainer.getComponent("Logbook Dropdown")
    dropdown.selectedStringValue = ""
    selectedStringValue =rootContainer.logbook
    ds = system.db.runQuery("select LogbookId, LogbookName from TkLogbook order by logbookName")
    dropdown.data = ds
    
    def setSelectedValue(dropdown=dropdown, selectedStringValue=selectedStringValue):
        print "Setting the selected Value to: ", selectedStringValue
#        time.sleep(5)
        dropdown.selectedStringValue=selectedStringValue

    system.util.invokeLater(setSelectedValue)

    print "Done initializing"