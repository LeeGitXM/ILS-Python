'''
Created on Jul 13, 2022

@author: ils

This module provides an interface for all of the blt functions that can be called from Python.
Unless noted otherwise, all of these functions run from a client
'''

import system
import system.ils.blt.diagram as diagram

from com.inductiveautomation.ignition.common.project.resource import ResourceType
from com.inductiveautomation.ignition.common.project.resource import ProjectResourceId

from ils.log import getLogger
log = getLogger(__name__)

def listBlocksGloballyUpstreamOf(diagramName, finalDiagnosisName):
    log.infof("In %s.listBlocksGloballyUpstreamOf() with %s on %s", __name__, finalDiagnosisName, diagramName)
    projectResourceId = getProjectResourceId(diagramName)
    blocks=diagram.listBlocksGloballyUpstreamOf(projectResourceId, finalDiagnosisName)
    log.infof("...returned %s", str(blocks))
    return blocks

def getProjectResourceId(diagramName):
    log.infof("In %s.getProjectResourceId()...", __name__)

    resourceType = ResourceType("block", "blt.diagram")
    print "   Resource Type: ", str(resourceType)

    print "Getting project resource id..."
    projectName = system.util.getProjectName()
    projectResourceId = ProjectResourceId(projectName, resourceType, diagramName)
    print "   Project Resource Id: ", str(projectResourceId)
    return projectResourceId