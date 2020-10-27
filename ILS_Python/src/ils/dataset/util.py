'''
Created on Sep 26, 2020

@author: phass
'''

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