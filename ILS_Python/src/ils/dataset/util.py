'''
Created on Sep 26, 2020

@author: phass
'''

from ils.io.util import readTag, writeTag
import system

def listOfDictionariesToDataset(theList):
    if len(theList) == 0:
        return None
    
    header = theList[0].keys()
        
    records = []
    for aDict in theList: 
        record = []
        for col in header:
            record.append(aDict.get(col))
        records.append(record)
        
    ds = system.dataset.toDataSet(header, records)
    return ds

def tagToList(tagPath):
    ds = readTag(tagPath).value
    theList = toList(ds)
    return theList

def toList(ds):
    theList = []
    for row in range(ds.rowCount):
        val = ds.getValueAt(row, 0)
        theList.append(val)
    return theList

def listToTag(tagPath, list):
    ds = fromList(list)
    writeTag(tagPath, ds)
    
def fromList(aList):
    header = ["vals"]
    data = []
    for val in aList:
        data.append([val])
        
    ds = system.dataset.toDataSet(header, data)
    return ds

def swapRows(ds, rowA, rowB):
    for col in range(ds.getColumnCount()):
        valA = ds.getValueAt(rowA, col)
        valB = ds.getValueAt(rowB, col)
        ds = system.dataset.setValue(ds, rowA, col, valB)
        ds = system.dataset.setValue(ds, rowB, col, valA)
    return ds