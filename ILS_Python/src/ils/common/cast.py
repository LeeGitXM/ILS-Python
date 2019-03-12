'''
Created on Sep 10, 2014

@author: Pete
'''

import system, string
from __builtin__ import str

def toDateTime(txt):
    mm = txt[:txt.find("/")]
    txt = txt[txt.find("/")+1:]
    
    dd = txt[:txt.find("/")]
    txt = txt[txt.find("/")+1:]
    yy = txt[:txt.find(" ")]
    txt = txt[txt.find(" ")+1:]
    
    hh = txt[:txt.find(":")]
    mi = txt[txt.find(":")+1:]
    
    theDate = system.date.getDate(int(yy), int(mm) - 1, int(dd))
    theDateTime = system.date.setTime(theDate, int(hh), int(mi), 0)
    return theDateTime

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

def isInteger(value):
    try:
        int(value)
        return True
    except:
        return False

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


def determineType(val):
    '''
    If they supplied the value None then make a completely arbitrary decision to create a Float.
    '''
    if val == None:
        return "Float", 0.0
    
    if val in [True, 'TRUE', 'True', 'true']:
        return "Boolean", True
    elif val in [False, 'FALSE', 'False', 'false']:
        return "Boolean", False
    elif isInteger(val):
        return "Integer", int(val)
    elif isFloat(val):
        return "Float", float(val)
    
    return "String", val