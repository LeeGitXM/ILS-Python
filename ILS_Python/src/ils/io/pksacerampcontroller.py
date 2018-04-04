'''
Created on Mar 29, 2018

@author: phass
'''

import system, string, time
import ils.io.pksrampcontroller as pksrampcontroller
import ils.io.opcoutput as opcoutput
log = system.util.getLogger("com.ils.io")

class PKSACERampController(pksrampcontroller.PKSRampController):
    
    def __init__(self,path):
        pksrampcontroller.PKSRampController.__init__(self,path)
        
    '''
    For now this will inherit everything from the pks ramp controller
    '''
        