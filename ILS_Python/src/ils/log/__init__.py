from ils.log.LogRecorder import LogRecorder

'''
For system default settings, use:

def getLogger(name, levelName=None, enableTraceThread=False):
    return LogRecorder(name, levelName=levelName, enableTraceThread=enableTraceThread)
'''

''' Whenever this module is reloaded (which I think happens on every Python save) this dictionary is initialized so all logging levels are reset '''
logs = {}
import system

def getLogger(loggerName, levelName='INFO', enableTraceThread=True):
    systemName = system.tag.readBlocking(["[System]Gateway/SystemName"])[0].value
    
    ''' This is hack to disable customized logging during development on Pete's server '''
    if systemName == "ILSDEV4-Dev-8.1.10":
        ''' Avoid using the local logs dictionary to preserve logging levels '''
        logger = system.util.getLogger(loggerName)
        return logger
    
    logger = logs.get(loggerName, None)
    if logger == None:
        logger = LogRecorder(loggerName, levelName=levelName, enableTraceThread=enableTraceThread)
        logs[loggerName] = logger
    return logger