'''
Created on Feb 17, 2017

@author: phass
'''

import system

def launch(window, component, tagProvider, tagPath, stripTagProvider=True):
    print "Launching the tag selector popup"
    header = ["window", "component"]
    rows = [[window, component]]
    args = system.dataset.toDataSet(header, rows)
    payload = {"args": args, "tagProvider": tagProvider, "tagPath": tagPath, 'stripTagProvider': stripTagProvider}
    window = system.nav.openWindow("Common/Tag Selector Popup", payload)
    system.nav.centerWindow(window)

'''
This is called on a seperate thread from a timer, hopefully after the tree has been populated
'''
def setSelectedTag(rootContainer):
    print "In setSelectedTag..."
    tagPath = rootContainer.tagPath
    
    print "The tagPath is: ", tagPath 
    
    tagBrowser = rootContainer.getComponent("Tag Browse Tree")
    ds = tagBrowser.selectedPaths
    ds = system.dataset.setValue(ds, 0, 0, tagPath)
    tagBrowser.selectedPaths = ds

'''
This is tailored to work with the isolation / production tag provider where the tag provider is determined at run time.
Specifically this is used on the recipe data editors where we specify a tag for Input or Output recipe data.  The tag
browser selects a tag within a provider.  When they press save I will strip the tag provider off.
'''
def save(event, rootContainer):
    print "Saving"
    args = rootContainer.args
    stripTagProvider = rootContainer.stripTagProvider
    window = args.getValueAt(0, "window")
    component = args.getValueAt(0, "component")
    
    ds = rootContainer.getComponent("Tag Browse Tree").selectedPaths
    tagPath = ds.getValueAt(0,0)
    
    print "The guy selected: ", tagPath
    
    ''' Strip off the tag provider '''
    if stripTagProvider:
        tagPath = tagPath[tagPath.index("]")+1:]
    
    print "The adjusted tagpath is <%s>" % (tagPath)
    
    component.text = tagPath
    
    system.nav.closeParentWindow(event)