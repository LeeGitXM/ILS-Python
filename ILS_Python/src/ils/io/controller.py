'''
Created on Nov 30, 2014

@author: Pete
'''

import ils.io.opctag as opctag
import system
log = system.util.getLogger("com.ils.io")

class Controller(opctag.OPCTag):
    def __init__(self,path):
        opctag.OPCTag.__init__(self,path)

    # Reset the UDT in preparation for a write 
    def reset(self):
        print "resetting a generic controller"
        log.trace('Resetting...')
        
        system.tag.write(self.path + '/writeConfirmed', False)
        system.tag.write(self.path + '/writeErrorMessage', '')
        system.tag.write(self.path + '/writeStatus', '')
        system.tag.write(self.path + '/command', '')
