'''
Created on Sep 10, 2014

@author: Pete
'''

import system, string
from __builtin__ import str

def toDateTime(txt, dateDelimiter="/", timeDelimiter=":"):
    ''' The date time string may contain a decimal portion of seconds, we are not interested in it if it exists '''
    if txt.find(".") > -1:
        txt = txt[:txt.find(".")]
        
    mm = txt[:txt.find(dateDelimiter)]
    txt = txt[txt.find(dateDelimiter)+1:]
    
    dd = txt[:txt.find(dateDelimiter)]
    txt = txt[txt.find(dateDelimiter)+1:]
    yy = txt[:txt.find(" ")]
    txt = txt[txt.find(" ")+1:]
    
    tokens = txt.split(timeDelimiter)
    hh = tokens[0]
    mi = tokens[1]
    if len(tokens) == 3:
        sec = tokens[2]
    else:
        sec = 0
    
    theDate = system.date.getDate(int(yy), int(mm) - 1, int(dd))
    theDateTime = system.date.setTime(theDate, int(hh), int(mi), int(sec))
    return theDateTime

def toBool(txt):

    if txt in ["true", "True", "TRUE", True, '1', 1, "1.0"]:
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
    I wish I would have used the Python type constants rather than my names for Integer, Float, String, etc
    '''
    if val == None:
        return "Float", 0.0
    
    ''' This isn't typical Python behavior ''' 
    if val in ['TRUE', 'True', 'true']:
        val = True
    if val in ['FALSE', 'False', 'false']:
        val = False
    
    ''' This very carefully distinguishes between 1 / True and 0 / False '''
    if val is True or val is False:
        return "Boolean", val
    
    if isinstance(val, int):
        return "Integer", int(val)
    elif isinstance(val, float):
        return "Float", float(val)
    elif isinstance(val, str):
        return "String", val

    return "String", val

def listToDataset(valueList):
    vals = []
    for val in valueList:
        vals.append([val])
    ds = system.dataset.toDataSet(["val"], vals)
    return ds

def extendedPropertiesToDictionary(extendedProperties):
    dict = {}
    
    if extendedProperties is not None:
        for prop in extendedProperties:
            propName = str(prop.getProperty().name)
            propValue = prop.value
            dict[propName] = propValue
    
    print "Dict: ", dict
    
    return dict