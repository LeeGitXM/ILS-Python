'''
Created on Sep 10, 2014

@author: Pete
'''
from __builtin__ import str

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

def isFloat(val):
    try:
        isFloat = True
        floatVal = float(val)
    except:
        isFloat = False
    return isFloat

'''
I think this is a general purpose routine to convert a json string that looks like a dictionary to an actual dictionary.
It is particularly useful for the SFC environment where we are going back and forth between Java and Python.  
The step configuration structures are generally in JSON.  I'm not sure if it is generic, but when a null value was in the JSON it
was not surrounded by double quites which caused eval to barf.
'''
def jsonToDict(json):
    import ast
    json = json.replace(':null',':"null"')
    dict=ast.literal_eval(str(json))
#    dict=eval(str(json))
    return dict