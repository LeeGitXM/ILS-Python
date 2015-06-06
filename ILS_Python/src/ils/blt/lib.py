#  Copyright 2015 ILS Automation
#
# This library is referenced by translated procedures that are part
# of the diagnosic toolkit. 
# 
from com.inductiveautomation.ignition.common.util import LogUtil
'''
Created on Jun 5, 2015
'''
# This is derived from the debug mode of the G2 procedure that we
# are translating. Simply return false and use the standard logging
# levels.
def getDebugMode(application):
    return False
 
# Originally called with the name of the procedure.                      
def getName(application):
    return str(application)
 
# We believe that the argument is simply a String.   
def getBlockName(block):
    return str(block)