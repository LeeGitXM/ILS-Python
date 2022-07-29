'''
Created on Jul 25, 2022

@author: ils
'''

import system
import xml.etree.ElementTree as ET
from ils.log import getLogger
log = getLogger(__name__)


def importUnitParameterCallback(event):
    log.infof("In %s.importUnitParameterCallback()...", __name__)

    filename = system.file.openFile("xml")
    
    log.infof("In %s.importUnitParameterCallback() with %s", __name__, filename)
    tree = ET.parse(filename)
    root = tree.getroot()
    
    for unitParameter in root.findall("unitParameter"):
        name = unitParameter.get("name")
        fullPath = unitParameter.get("fullPath")
        ignoreSampleTime = unitParameter.get("ignoreSampleTime")
        numberOfPoints = unitParameter.get("numberOfPoints")
        valueReference = unitParameter.get("valueReference")
        sampleTimeReference = unitParameter.get("sampleTimeReference")
        
        log.infof("%s - %s - %s - %s - %s - %s", name, fullPath, ignoreSampleTime, numberOfPoints, valueReference, sampleTimeReference)
        
        ''' Now create a new UDT instance '''
        
    log.infof("Done importing Unit Parameters!")
    