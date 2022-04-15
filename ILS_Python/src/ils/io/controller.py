'''
Created on Nov 30, 2014

@author: Pete
'''

import system
import ils.io.opctag as opctag
import ils.io.opcmodeoutput as opcmodeoutput
from ils.io.util import readTag, writeTag
from ils.log import getLogger
log = getLogger(__name__)

class Controller(opctag.OPCTag):
    modeTag = None
    PERMISSIVE_LATENCY_TIME = 0.0
    
    def __init__(self,path):
        opctag.OPCTag.__init__(self,path)
        self.modeTag = opcmodeoutput.OPCModeOutput(path + '/mode')
        self.PERMISSIVE_LATENCY_TIME = readTag("[%s]Configuration/Common/opcPermissiveLatencySeconds" % (self.tagProvider)).value
        
    # Reset the UDT in preparation for a write 
    def reset(self):
        print "resetting a generic controller"
        log.trace('Resetting...')
        
        system.tag.writeBlocking(
            [self.path + '/writeConfirmed', self.path + '/writeErrorMessage', self.path + '/writeStatus'],
            [False, '', '']
            )
