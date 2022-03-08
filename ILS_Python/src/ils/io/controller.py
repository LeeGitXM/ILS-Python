'''
Created on Nov 30, 2014

@author: Pete
'''

import ils.io.opctag as opctag
import ils.io.opcmodeoutput as opcmodeoutput
import system
from ils.log import getLogger
log =getLogger(__name__)

class Controller(opctag.OPCTag):
    
    modeTag = None
    
    def __init__(self,path):
        opctag.OPCTag.__init__(self,path)
        self.modeTag = opcmodeoutput.OPCModeOutput(path + '/mode')
        
        
    # Reset the UDT in preparation for a write 
    def reset(self):
        print "resetting a generic controller"
        log.trace('Resetting...')
        
        system.tag.write(self.path + '/writeConfirmed', False)
        system.tag.write(self.path + '/writeErrorMessage', '')
        system.tag.write(self.path + '/writeStatus', '')
