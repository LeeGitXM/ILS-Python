'''
Created on Mar 27, 2017

@author: phass
'''

import system

# Remove menus that are not appropriate for this project.
# The common ignition project is used by all sites.  The database used at each site uses 
# a common schema with site specific data.  The TkMenuBar table lists the menus that are 
# appropriate for each site.  
def removeUnwantedMenus(bar): 
    
    # Select the configuration of the menus for this site
    pds = system.db.runQuery("Select SubMenu, Enabled from TkMenuBar where Application = 'dbManager' and Menu = 'View'")
    enabledMenus = []
    for record in pds:
        if record["Enabled"] == 1:
            enabledMenus.append(record["SubMenu"])
    
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
                if submenuName not in enabledMenus:
                    print "  *** REMOVING ***"
                    menu.remove(submenu)
                    viewCount=viewCount-1
                else:
                    viewIndex=viewIndex+1

        index=index+1
