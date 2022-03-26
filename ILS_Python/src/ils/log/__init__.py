from ils.log.LogRecorder import LogRecorder

'''
For system default settings, use:

def getLogger(name, levelName=None, enableTraceThread=False):
    return LogRecorder(name, levelName=levelName, enableTraceThread=enableTraceThread)
'''

logs = {}

def getLogger(name, levelName='INFO', enableTraceThread=True):
    logger = logs.get(name, None)
    if logger == None:
        logger = LogRecorder(name, levelName=levelName, enableTraceThread=enableTraceThread)
        logs[name] = logger
    return logger