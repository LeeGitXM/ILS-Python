'''
A concrete class for AbstractSfcIO that allows basic testing with memory tags in place 
of a real controller. The assumption is that tags will use the TestController datatype
which has sub-tags called currentValue and setpoint

apparently Python doesn't like circular dependencies in imports of classes. 
"from abstractSfcIIO import AbstractSfcIO" causes problems, but the more awkward
"import abstractSfcIO" and use of abstractSfcIO.AbstractSfcIO works !?

Created on Jun 18, 2015

@author: rforbes
'''

import system.tag
import abstractSfcIO

class TagIOCRAP:    
    name = ''
    
    def  __init__(self, _tagPath, isolationMode):
        from system.ils.sfc import getProviderName
        providerName = getProviderName(isolationMode) 
        self.name = _tagPath
        self.tagPath = '[' + providerName + ']' + _tagPath
    
    def getName(self):
        return self.name
    
    def set(self, attribute, value):
        system.tag.writeSynchronous(self.getPath(attribute), value)

    def getSetpoint(self):
        return self.get('setpoint')
    
    def setSetpoint(self, value):
        self.set('setpoint', value)
    
    def isSetpointDownloaded(self):
        setpoint = self.getSetpoint()
        pv = self.getCurrentValue()
        return setpoint != pv

    def getCurrentValue(self):
        return self.get('currentValue')
    
    def setCurrentValue(self, value):
        '''This may not be supported in the real world--it is at least handy for testing'''
        self.set('currentValue', value)
    
    def get(self, attribute):
        print "Reading ", attribute
        if attribute == 'tagPath':
            return self.tagPath
        else:
            qval = system.tag.read(self.getPath(attribute))
            #TODO: bad value handling
            return qval.value
        
    def getPath(self, attribute):
        return self.tagPath + '/' + attribute + '.value'
