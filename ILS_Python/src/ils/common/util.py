'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def isText(val):

    try:
        val = float(val)
        isText = False
    except:
        isText = True

    return isText


# The input to this is expected to be a string.  It tests to see if the string is a float.  I treats
# the text string NaN as a float.
def isFloattOrSpecialValue(val):
    
    if val in ['NaN', 'NAN']:
        return True

    try:
        val = float(val)
        isFloat = True
    except:
        isFloat = False
    
    return isFloat

def getDate():
    SQL = "select getdate()"
    theDate = system.db.runScalarQuery(SQL)
    return theDate


def formatDate(theDate, format = 'MM/dd/YY'):
    theDate = system.db.dateFormat(theDate, format)
    return theDate

    
def formatDateTime(theDate, format = 'MM/dd/YY hh:ss'):
    theDate = system.db.dateFormat(theDate, format)
    return theDate


# Compare two tag values taking into account that a float may be disguised as a text string and also
# calling two floats the same if they are almost the same.
def equalityCheck(val1, val2, recipeMinimumDifference, recipeMinimumRelativeDifference):
    val1IsText = isText(val1)
    val2IsText = isText(val2)

    if val1IsText and val2IsText:
        if val1 == val2:
            return True
        else:
            return False
    else:
        # They aren't both text, so if only one is text, then they don't match 
        if val1IsText or val2IsText:
            return False
        else:
            minThreshold = abs(recipeMinimumRelativeDifference * float(val1))
            if minThreshold < recipeMinimumDifference:
                minThreshold = recipeMinimumDifference

            if abs(float(val1) - float(val2)) < minThreshold:
                return True
            else:
                return False

# Verify that val2 is the same data type as val1.  Make sure to treat special values such as NaN as a float
def dataTypeMatch(val1, val2):
    val1IsFloat = isText(val1)
    val2IsFloat = isText(val2)
    
    if val1IsFloat != val2IsFloat:
        return False
    
    return True