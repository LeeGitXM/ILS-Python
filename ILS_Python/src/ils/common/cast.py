'''
Created on Sep 10, 2014

@author: Pete
'''

def toBool(txt):

    if txt == "true" or txt == "True" or txt == "TRUE" or txt == True or txt == '1' or txt == 1:
        val = True
    else:
        val = False

    return val

def toBit(txt):

    if txt == "true" or txt == "True" or txt == "TRUE" or txt == True or txt == '1' or txt == 1:
        val = 1
    else:
        val = 0

    return val

def tagHistoryDatasetToList(ds, idx):
    aList=[]
    for row in range(ds.rowCount):
        aList.append(ds.getValueAt(row,idx))
    return aList