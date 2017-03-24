'''
Created on Mar 21, 2017

@author: phass
'''

import system

# Dump the contents of a python dataset
def dumpPyDataset(pds):
    ds = system.dataset.toDataSet(pds)
    print '\t'.join(system.dataset.getColumnHeaders(ds))
    for row in pds:
        fields=[]
        for value in row:
            fields.append(str(value))
        print '\t'.join(fields)
            
        
#
# Dump the contents of a python dataset
def dumpDataset(ds):
    print '\t'.join(system.dataset.getColumnHeaders(ds))
    pds = system.dataset.toPyDataSet(ds)
    for row in pds:
        fields=[]
        for value in row:
            fields.append(str(value))
        print '\t'.join(fields)
        
# Print the dataset headers
def dumpDatasetHeaders(ds):
    print '\t'.join(system.dataset.getColumnHeaders(ds))
