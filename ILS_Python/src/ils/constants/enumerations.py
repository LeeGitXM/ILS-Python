'''
Enumerations are part of Python 3.4, but we're at 2.7.
Current implementation is from: http://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python
Created on Sep 11, 2014
Returns a lower-cased string given the enumeration key.
@author: chuckc
'''
class Enum(object):
    def __init__(self, names, separator=None):
        self.names = names.split(separator)
        for value, name in enumerate(self.names):
            setattr(self, name.upper(), name.lower())
    def tuples(self):
        return tuple(enumerate(self.names))
    
# Use these constants 
EMCConstants= Enum('critical')
S88Command  = Enum('abort')
S88Scope    = Enum('global operation superior previous')
S88State    = Enum('aborted complete error running stopped')