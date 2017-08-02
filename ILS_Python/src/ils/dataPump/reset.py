'''
Created on Jun 20, 2017

@author: phass
'''
import system

def hardReset(tagProvider):
    system.tag.writeToTag("%sData Pump/simulationState" % (tagProvider), "Idle")
    system.tag.writeToTag("%sData Pump/command" % (tagProvider), "Abort")
    system.tag.writeToTag("%sData Pump/lineNumber" % (tagProvider), -1)