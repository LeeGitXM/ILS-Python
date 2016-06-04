'''
Created on Jun 4, 2016

@author: ils
'''

# This assumes a dataset that has the keys in the first (0) column.  
# The attr can be any subsequent column and is looked up by name
def lookup(ds, key, attr, defaultKey="default"):
    for row in range(ds.rowCount):
        if ds.getValueAt(row, 0) == key:
            return ds.getValueAt(row, attr)

    for row in range(ds.rowCount):
        if ds.getValueAt(row, 0) == defaultKey:
            print "Using the DEFAULT key"
            return ds.getValueAt(row, attr)
    
    return "ERROR"