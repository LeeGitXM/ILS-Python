'''
Created on Jun 20, 2017

@author: phass
'''
import system
from ils.io.util import writeTag

def hardReset(tagProvider):
    writeTag("%sData Pump/simulationState" % (tagProvider), "Idle")
    writeTag("%sData Pump/command" % (tagProvider), "Abort")
    writeTag("%sData Pump/lineNumber" % (tagProvider), -1)