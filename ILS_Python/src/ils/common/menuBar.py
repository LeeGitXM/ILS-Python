'''
Created on Mar 7, 2016

@author: ils
'''
import system

# Collection of useful methods for menu configuration


def removeUnwantedConsoles(bar): 
    '''
    Remove console menus that are not appropriate for this project.
    The common X-O-M ignition project is used by all sites.  The database used at each site uses 
    a common schema with site specific data.  The TkConsole table lists the consoles that are 
    appropriate for each site.  So this method removes menus that are not appropriate for this site.
    The argument is a menubar component.
    '''

    print "Removing unwanted consoles..."
    count = bar.getMenuCount()
    index = 0
    while index < count:
        menu = bar.getMenu(index)
        name = menu.getText()

        if name == 'View':            
            # Find the console menu
            viewCount = menu.getItemCount()
            viewIndex = 0
            while viewIndex < viewCount:
                submenu = menu.getItem(viewIndex)
                submenuName = submenu.getText()
                
                if submenuName == 'Consoles':
                    print "Found the View->Console submenu..."
                    consoleCount = submenu.getItemCount()
                    consoleIndex = 0
                    while consoleIndex < consoleCount:
                        console = submenu.getItem(consoleIndex)
                        consoleName = console.getText()
                        print "  Console menu: ", consoleName
                        SQL = "select count(*) from TkConsole where ConsoleName = '%s'" % (consoleName)
                        cnt=system.db.runScalarQuery(SQL)
                        if cnt == 0:
                            print "    *** REMOVE IT ***" 
                            submenu.remove(console)
                            consoleCount = consoleCount - 1
                        else:
                            consoleIndex = consoleIndex + 1

                viewIndex=viewIndex+1
            
        index=index+1


def removeNonOperatorMenus(bar):
    print " "
    print "Removing the menus which are not appropriate for operators."

    count = bar.getMenuCount()
    print "Count = ", count
    index = 0
    while index < count:
        menu = bar.getMenu(index)
        name = menu.getText()
        print "Menu:",name
        if name == 'Admin':
            print "Removing the Admin menu..."
            bar.remove(menu)
            count = count - 1
        
        elif name == 'View':
            # Find the console menu
            viewCount = menu.getItemCount()
            viewIndex = 0
            while viewIndex < viewCount:
                submenu = menu.getItem(viewIndex)
                submenuName = submenu.getText()
                print "View Submenu: ", submenuName
                
                if submenuName == 'Consoles':
                    print "Removing the Consoles menu..."
                    menu.remove(submenu)
                    viewCount = viewCount - 1
                else:
                    viewIndex = viewIndex + 1

            index=index+1

        else:
            index=index+1
    

# Given a component, traverse the hierarchy of its parents
# until we find a JFrame. Return it.
def getFrame(window):
    from javax.swing import SwingUtilities
    from javax.swing import JFrame
    
    return SwingUtilities.getAncestorOfClass(JFrame,window)
    
# Given a component, traverse the hierarchy of its parents
# until we find a JFrame. Return its menubar.
def getMenuBar(component):
    frame = getFrame(component)
    bar = None
    if frame!=None:
        bar = frame.getJMenuBar()
    return bar


def removeUnwantedMenus(bar, projectType): 
    '''
    Remove menus that are not appropriate for this project.
    The common ignition project X-O-M is used by all sites.  The database used at each site uses 
    a common schema with site specific data.  The TkMenuBar table lists the menus that are 
    appropriate for each site.  The 2nd argument, project type, is X-O-M or dbManager, it is not 
    the same as the project name.
    
    For some reason I decided to reverse the logic between the Admin and the View menus...
    '''
    
    print " "
    print "Removing unwanted menus for this application: ", projectType
    
    # Select the configuration of the menus for this site
    pds = system.db.runQuery("Select SubMenu, Enabled from TkMenuBar where Application = '%s' and Menu = 'View'" % (projectType))
    enabledViewMenus = []
    for record in pds:
        if record["Enabled"] == 1:
            enabledViewMenus.append(record["SubMenu"])
            
    # Select the configuration of the menus for this site
    pds = system.db.runQuery("Select SubMenu, Enabled from TkMenuBar where Application = '%s' and Menu = 'Admin'" % (projectType))
    disabledAdminMenus = []
    for record in pds:
        if record["Enabled"] == 0:
            disabledAdminMenus.append(record["SubMenu"])
    
    count = bar.getMenuCount()
    index = 0
    while index < count:
        menu = bar.getMenu(index)
        name = menu.getText()
        print "Menu:",name
        
        if name == 'View':    
            # Find the console menu
            viewCount = menu.getItemCount()
            viewIndex = 0
            while viewIndex < viewCount:
                submenu = menu.getItem(viewIndex)
                submenuName = submenu.getText()
                print "View Submenu: ", submenuName
                if submenuName not in enabledViewMenus:
                    print "  *** REMOVING ***"
                    menu.remove(submenu)
                    viewCount=viewCount-1
                else:
                    viewIndex=viewIndex+1
                    
        elif name == 'Admin':
            viewCount = menu.getItemCount()
            viewIndex = 0
            while viewIndex < viewCount:
                submenu = menu.getItem(viewIndex)
                submenuName = submenu.getText()
                print "Admin Submenu: ", submenuName
                if submenuName in disabledAdminMenus:
                    print "  *** REMOVING ***"
                    menu.remove(submenu)
                    viewCount=viewCount-1
                else:
                    viewIndex=viewIndex+1

        index=index+1
