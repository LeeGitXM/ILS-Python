'''
Created on Aug 16, 2017

@author: phass
'''

import system

def load(rootContainer):
    filename=rootContainer.getComponent("File Field").text
    if not(system.file.fileExists(filename)):
        system.gui.messageBox("Error - the requested file does not exist!")
        return
    
    contents = system.file.readFileAsString(filename, "US-ASCII")
    records = contents.split('\n')
    
    header = ["Name", "Baler", "Property", "Item Id"]
    data = []
    
    print "Loaded %d records... " % (len(records))
    i = 0
    for line in records:
        line=line[:len(line)-1] #Strip off the last character which is some sort of CRLF
        print "Line: <%s>" % (line)
        tokens = line.split(',')
        
   
        if (i == 0):
            print "Header: ", line
        elif line <> "":
            baler = tokens[0]
            balerProperty = tokens[1]
            name = tokens[3]
            itemId = tokens[6]
            data.append([name, baler, balerProperty, itemId])
            print "Baler: %s, Property: %s, Item-Id: %s, Name: %s " % (baler, balerProperty, itemId, name)
        
        i = i + 1
    
    print "...done parsing data..."
    
    ds = system.dataset.toDataSet(header, data)
    
    table = rootContainer.getComponent("Baler Container").getComponent("Power Table")
    table.data = ds
    
    print "...done updating table!"


def configureBalers(container):
    print "Configuring Baler UDTs..."
    table = container.getComponent("Power Table")
    ds = table.data
    
    for i in range(ds.rowCount):
        print "Configuring line ", i
        baler = ds.getValueAt(i, "Baler")
        balerProperty = ds.getValueAt(i, "Property")
        name = ds.getValueAt(i, "Name")
        itemId = ds.getValueAt(i, "Item Id")
        
        tagPath = "[XOM]Site/Balers/Baler%s" % baler
        
        system.tag.editTag(
            tagPath=tagPath, 
            overrides={balerProperty: {"OPCItemPath":itemId}})
        
        