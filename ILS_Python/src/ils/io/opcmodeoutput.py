'''
Created on Apr 9, 2021

@author: phass
'''

import ils
import ils.io
import ils.io.opcoutput as opcoutput
import system, string

from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

class OPCModeOutput(opcoutput.OPCOutput):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
    
    def writeDatum(self, val, valueType="", confirmTagPath=""):
        log.tracef("%s.writeDatum() - Writing <%s>, <%s> to %s, an OPCModeOutput", __name__, str(val), str(valueType), self.path)
        
        return True, ""