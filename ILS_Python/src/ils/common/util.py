'''
Created on Sep 10, 2014

@author: Pete
'''

import system, string, time
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from java.util import Date
 
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


def getDate(database = ""):
    SQL = "select getdate()"
    theDate = system.db.runScalarQuery(SQL, database)
    return theDate


def formatDate(theDate, format = 'MM/dd/yy'):
    theDate = system.db.dateFormat(theDate, format)
    return theDate

    
def formatDateTime(theDate, format = 'MM/dd/yy hh:mm'):
    theDate = system.db.dateFormat(theDate, format)
    return theDate


# Returns the m and b constants from the equation y = mx + b
def equationOfLine(x1, y1, x2, y2):
    
    # Found a horizontal line
    if (y2 - y1) == 0:
        return 0.0, y1
    
    # Found a vertical line which isn't handled very well
    if (x2 - x1) == 0:
        return 999999.0, 0.0
    
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1
    
    return m, b

# Calculate the Y value for a line given an X value and the slope and y-Intercept
def calculateYFromEquationOfLine(x, m, b):
    y = x * m + b
    return y

# Calculate the Y value for a line given an X value and the slope and y-Intercept
def calculateXFromEquationOfLine(y, m, b):
    x = (y - b) / m
    return x

