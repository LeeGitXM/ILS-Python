'''
Created on Jun 20, 2017

@author: phass
'''
import system

def hardReset(tagProvider):
    system.tag.writeToTag("%sConfiguration/Data Pump/simulationState" % (tagProvider), "Idle")
    system.tag.writeToTag("%sConfiguration/Data Pump/command" % (tagProvider), "Abort")
    system.tag.writeToTag("%sConfiguration/Data Pump/lineNumber" % (tagProvider), -1)