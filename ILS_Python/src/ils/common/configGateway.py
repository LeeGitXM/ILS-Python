'''
Created on Jan 25, 2022

@author: phass
'''

def getUserLibDirHandler(payload):
    userLibDir = getUserLibPath()
    return userLibDir

def getUserLibPath():
    ''' This only works in gateway scope '''
    from com.inductiveautomation.ignition.gateway import SRContext
    context = SRContext.get()
    homeDir = context.getUserlibDir().getAbsolutePath()
    return homeDir