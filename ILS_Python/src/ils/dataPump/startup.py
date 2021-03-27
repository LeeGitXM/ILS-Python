'''
Created on Jul 14, 2017

@author: phass

There is really nothing to create here.  At one time the data pump used tags in the configuration folder that were created here
but the command tag has a tag change script which I can't configure when I create tags in this way.  So now the data pump tags are 
created manually from a standard XML export.
'''

import system
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def gateway(tagProvider, isolationTagProvider):
    from ils.labFeedback.version import version
    version, revisionDate = version()
    log.info("---------------------------------------------------------")
    log.info("Starting Data Pump Toolkit ")
    log.info("---------------------------------------------------------")

    tagPaths = []
    tagPaths.append("[%s]Data Pump/command" % (tagProvider))
    tagPaths.append("[%s]Data Pump/command" % (tagProvider))
    tagPaths.append("[%s]Data Pump/simulationState" % (tagProvider))
    tagPaths.append("[%s]Data Pump/simulationState" % (tagProvider))
    tagPaths.append("[%s]Data Pump/lineNumber" % (tagProvider))
    tagPaths.append("[%s]Data Pump/lineNumber" % (tagProvider))
    
    tagValues = []
    tagValues.append("Stop")
    tagValues.append("Stop")
    tagValues.append("Idle")
    tagValues.append("Idle")
    tagValues.append(0)
    tagValues.append(0)
    
    system.tag.writeAll(tagPaths, tagValues)