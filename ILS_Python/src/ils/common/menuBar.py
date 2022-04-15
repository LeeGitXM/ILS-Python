'''
Created on Mar 7, 2016

@author: ils
'''
import system
from javax.swing import JMenuItem
from ils.log import getLogger
log = getLogger(__name__)

# Collection of useful methods for menu configuration
class ConsoleMenus():
    '''
    An instance of this class is created from the client startup script.  The instance is stored in the menu somehow.
    The one instance lives as long as the client is connected.
    '''
    
    def __init__(self,bar):
        self.menus = {}
        '''
        Add appropriate consoles for this project
        '''
        log.infof("In %s.ConsoleMenus() - Adding consoles to main menu...", __name__)
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
                        log.infof("ConsoleMenus: Found the View->Console submenu...")
                        SQL = "select consoleName, windowName from TkConsole order by Priority, consoleName"
                        pds = system.db.runQuery(SQL)
                        log.infof("...fetched %d consoles from the database...", len(pds))
                        for record in pds:
                            consoleName = record["consoleName"]
                            windowName = record["windowName"]
                            self.menus[consoleName] = windowName
                            submenu.add(JMenuItem(consoleName, actionPerformed=self.menuAction))
                    viewIndex=viewIndex+1
            
            index=index+1
            
    def menuAction(self,event):
        '''
        This is called when the user selects one of the console choices from the pulldown menu.
        '''  
        console = event.getSource().getText()
        windowPath = self.menus[console]
        log.infof("In %s.menuAction() - opening %s for console %s", __name__, windowPath, console)
        system.nav.openWindow(windowPath)


def clearConsoles(bar): 
    '''
    Remove entries from the View->Console entry on the main menu.
    '''
    log.infof("...removing console menu entries...")
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
                    log.infof("...found the View->Console submenu...")
                    submenu.removeAll()
                viewIndex=viewIndex+1
            
        index=index+1


def removeNonOperatorMenus(bar):
    log.infof("Removing the menus which are not appropriate for operators.")

    count = bar.getMenuCount()
    index = 0
    while index < count:
        menu = bar.getMenu(index)
        name = menu.getText()

        if name == 'Admin':
            log.infof("Removing the Admin menu...")
            bar.remove(menu)
            count = count - 1
        
        elif name == 'View':
            # Find the console menu
            viewCount = menu.getItemCount()
            viewIndex = 0
            while viewIndex < viewCount:
                submenu = menu.getItem(viewIndex)
                submenuName = submenu.getText()
                log.infof("View Submenu: %s", submenuName)
                
                if submenuName == 'Consoles':
                    log.infof("Removing the Consoles menu...")
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
    
    log.infof("Removing unwanted menus for this application: %s", projectType)
    
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
        log.infof("Menu: %s", name)
        
        if name == 'View':    
            # Find the console menu
            viewCount = menu.getItemCount()
            viewIndex = 0
            while viewIndex < viewCount:
                submenu = menu.getItem(viewIndex)
                submenuName = submenu.getText()
                log.infof("View Submenu: %s", submenuName)
                if submenuName not in enabledViewMenus:
                    log.infof("  *** REMOVING ***")
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
                log.infof("Admin Submenu: %s", submenuName)
                if submenuName in disabledAdminMenus:
                    log.infof("  *** REMOVING ***")
                    menu.remove(submenu)
                    viewCount=viewCount-1
                else:
                    viewIndex=viewIndex+1

        index=index+1
