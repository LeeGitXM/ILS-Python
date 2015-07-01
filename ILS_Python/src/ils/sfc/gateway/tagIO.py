'''
Created on Jun 18, 2015

@author: rforbes
'''

import system.tag
import abstractSfcIO

class TagIO:    
    
    def  __init__(self, _tagPath, isolationMode):
        providerName = abstractSfcIO.getProviderName(isolationMode)
        self.tagPath = '[' + providerName + ']' + _tagPath
        
    def set(self, attribute, value):
        system.tag.writeSynchronous(self.getPath(attribute), value)

    def get(self, attribute):
        if attribute == 'tagPath':
            return self.tagPath
        else:
            qval = system.tag.read(self.getPath(attribute))
            #TODO: bad value handling
            return qval.value
        
    def getPath(self, attribute):
        return self.tagPath + '/' + attribute + '.value'
