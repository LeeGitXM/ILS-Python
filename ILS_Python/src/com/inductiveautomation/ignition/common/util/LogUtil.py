'''
Created on Nov 5, 2014

@author: chuckc
'''
from com.inductiveautomation.ignition.common.util import LoggerEx

class LogUtil(object):
    # A static method ...
    def getLogger(self,name):
        logger = LoggerEx()
        return logger