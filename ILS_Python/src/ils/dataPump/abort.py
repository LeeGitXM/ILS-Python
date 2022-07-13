'''
Created on Jun 20, 2017

@author: phass
'''
from ils.io.util import writeTag

def abort(tagProvider):
    import system
    writeTag("%sData Pump/command" % (tagProvider), "Abort")