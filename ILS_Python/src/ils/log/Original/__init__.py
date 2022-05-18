'''
Use this version if u just want pure IA standard logging.
'''

import system

def getLogger(name, levelName='INFO', enableTraceThread=True):
    logger = system.util.getLogger(name)
    return logger