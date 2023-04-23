'''
Created on Sep 16, 2022

@author: ils
'''
import system
from ils.config.client import getTagProviders

def internalFrameOpened(rootContainer):
    print "In %s.internalFrameOpened()" % (__name__)
    
    tagProviders = getTagProviders()
    vals = []
    for tagProvider in tagProviders:
        vals.append([tagProvider])
    ds = system.dataset.toDataSet(["tagProvider"], vals)
    rootContainer.tagProviders = ds
    
    table = rootContainer.getComponent("Power Table")
    header = ["ItemId", "Tag", "Count"]
    data = []
    ds = system.dataset.toDataSet(header, data)
    table.data = ds

    
def refresh(event):
    print "Starting to browse tags..."
    rootContainer = event.source.parent
    dropdown = rootContainer.getComponent("Tag Provider Dropdown")
    if dropdown.selectedValue == -1:
        system.gui.messageBox("Select a Tag Provider from the dropdown!")
        return
    tagProvider = dropdown.selectedStringValue
    filters = {"valueSource":"opc", "recursive":True}
    results = system.tag.browse(path="[%s]" % (tagProvider), filter=filters)
    i = 0
    header = ["ItemId", "Tag", "Count"]
    tagDict = {}
    data = []
    for tag in results.getResults():
        fullPath = str(tag['fullPath'])
        tagType = str(tag['tagType'])
        #print "%s - %s" % (fullPath, tagType)
        if tagType == "AtomicTag":    
            itemId = system.tag.readBlocking([fullPath + ".OPCItemPath"])[0].value
            
            if itemId not in ["", None]:
                i = i + 1
                cnt = tagDict.get(itemId, -1)
                if cnt < 0:
                    tagDict[itemId] = 1
                else:
                    tagDict[itemId] = cnt + 1
                    
                data.append([itemId, fullPath, 1])
    
    print "Found ", i , " OPC tags!"
    
    ds = system.dataset.toDataSet(header, data)
    ds = system.dataset.sort(ds,"ItemId")
    
    '''
    Now merge the dictionary of item id usage with the list of item ids / tags
    '''
    cnt = 1
    for row in range(ds.rowCount):
        itemId = ds.getValueAt(row, "ItemId")
        cnt = tagDict.get(itemId, -1)    
        if cnt > 1:
            ds = system.dataset.setValue(ds, row, "Count", cnt)
    
    table = event.source.parent.getComponent("Power Table")
    columnSizing = table.defaultColumnView
    table.data = ds
    table.defaultColumnView = columnSizing