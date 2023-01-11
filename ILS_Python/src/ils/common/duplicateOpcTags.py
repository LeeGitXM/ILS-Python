'''
Created on Sep 16, 2022

@author: ils
'''
import system

def internalFrameOpened(rootContainer):
    print "In %s.internalFrameOpened()" % (__name__)
    table = rootContainer.getComponent("Power Table")
    header = ["ItemId", "Tag", "Count"]
    data = []
    ds = system.dataset.toDataSet(header, data)
    table.data = ds
    
def refresh(event):
    print "Starting to browse tags..."
    filters = {"valueSource":"opc", "recursive":True}
    results = system.tag.browse(path="[*]", filter=filters)
    i = 0
    header = ["ItemId", "Tag", "Count"]
    tagDict = {}
    data = []
    for tag in results.getResults():
        fullPath = str(tag['fullPath'])
        tagType = str(tag['tagType'])
        if tagType == "AtomicTag":    
            itemId = system.tag.readBlocking([fullPath + ".OPCItemPath"])[0].value
            
            if itemId not in ["", None]:
                i = i + 1
                cnt = dict.get(itemId, -1)
                if cnt < 0:
                    tagDict[itemId] = 1
                else:
                    tagDict[itemId] = cnt + 1
                    
                data.append([itemId, fullPath, 1])
    
    print "Found ", i , " OPC tags!"
    
    ds = system.dataset.toDataSet(header, data)
    ds = system.dataset.sort(ds,"ItemId")
    
    '''
    Now merge the dicttionary of item id usage with the list of item ids / tags
    '''
    cnt = 1
    for row in range(ds.rowCount):
        itemId = ds.getValueAt(row, "ItemId")
        cnt = dict.get(itemId, -1)    
        if cnt > 1:
            ds = system.dataset.setValue(ds, row, "Count", cnt)
    
    table = event.source.parent.getComponent("Power Table")
    columnSizing = table.defaultColumnView
    table.data = ds
    table.defaultColumnView = columnSizing