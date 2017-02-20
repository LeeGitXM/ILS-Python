'''
Created on Feb 17, 2017

@author: phass
'''

import system

def launch(window, component, tagProvider, tagPath):
    print "Launching the tag selector popup"
    header = ["window", "component"]
    rows = [[window, component]]
    args = system.dataset.toDataSet(header, rows)
    payload = {"args": args, "tagProvider": tagProvider, "tagPath": tagPath}
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
    
def save(event, rootContainer):
    print "Saving"
    args = rootContainer.args
    window = args.getValueAt(0, "window")
    component = args.getValueAt(0, "component")
    
    ds = rootContainer.getComponent("Tag Browse Tree").selectedPaths
    tagPath = ds.getValueAt(0,0)
    
    print "The guy selected: ", tagPath
    
    component.text = tagPath
    
    system.nav.closeParentWindow(event)