'''
Created on Jun 22, 2015

@author: rforbes
'''

from tagIO import TagIO

# These are "universal" attribute names that can be given to setValue and getValue. These
# will be internally translated into the actual names for a given controller
SETPOINT = 'setpoint'
VALUE = 'value'

class AbstractSfcIO:    
    '''An abstract superclass that encapsulates basic IO access for all controller types
    behind a uniform interface. The implementation is expected to handle the isolation mode
    flag by using the appropriate provider internally. '''
    def  __init__(self, _ioId, isolationMode):
        pass
            
    def set(self, attribute, value):
        '''Set an attribute. The attribute name may be controller-specific.'''
        pass

    def get(self, attribute):
        '''Get an attribute. The attribute name may be controller-specific.'''
        pass
    
def getIO(ioId, isolationMode):
    '''Get an IO instance of the proper type for the given id'''
    # TODO: support other controller types
    return TagIO(ioId, isolationMode)

def getProviderName(isolationMode):
    '''Get the name of the IO provider depending on whether we are in isolation mode'''
    from system.ils.sfc import getProviderName
    return getProviderName(isolationMode)

