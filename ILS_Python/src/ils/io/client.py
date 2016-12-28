'''
Created on Dec 26, 2016

This module defined that IO API that can be used from a client where the write will be performed in the gateway.
If these APIswill be used it is up to the client to poll te status tags of the write targets since these APIs send
messages to the gateway to perform the writes asynchronously.  There is no return status possible from the APIs.
Although this API layer is intended for calling from a Vision client, it works equally from gateway scope, whether
called from a tag change script or a SFC; thus the need to pass in the project.

@author: phass
'''

import system
log = system.util.getLogger("com.ils.client")


def writeWithNoCheck(tagPath, tagValue, project, valueType="value"):
    tagValues = [{"tagPath":tagPath, "tagValue":tagValue, "valueType":valueType}]
    log.trace("Sending writeWithNoCheck message to gateway for %s..." % (str(tagValues)))
    system.util.sendMessage(project, "tagWriter", {"command": "writeWithNoCheck", "tagList": tagValues}, scope="G")

def writeWithNoChecks(tagValues, project):
    log.trace("Sending writeWithNoCheck message to gateway for %s..." % (str(tagValues)))
    system.util.sendMessage(project, "tagWriter", {"command": "writeWithNoCheck", "tagList": tagValues}, scope="G")
    
def writeDatum(tagPath, tagValue, project, valueType="value"):
    tagValues = [{"tagPath":tagPath, "tagValue":tagValue, "valueType":valueType}]
    log.trace("Sending writeDatum message to gateway for %s..." % (str(tagValues)))
    system.util.sendMessage(project, "tagWriter", {"command": "writeDatum", "tagList": tagValues}, scope="G")

def writeDatums(tagValues, project):
    log.trace("Sending writeDatum message to gateway for %s..." % (str(tagValues)))
    system.util.sendMessage(project, "tagWriter", {"command": "writeDatum", "tagList": tagValues}, scope="G")

def writeRamp(tagPath, tagValue, valueType, rampTime, updateFrequency, writeConfirm, project):
    payload = {"tagPath":tagPath, "tagValue":tagValue, "valueType":valueType, "rampTime":rampTime, "updateFrequenct":updateFrequency, "writeConfirm":writeConfirm}
    tagValues=[payload]
    log.trace("Sending write message for %i tags..." % (len(tagValues)))
    system.util.sendMessage(project, "tagWriter", {"command": "writeRamp", "tagList": tagValues}, scope="G")

def writeRecipeDetail(tagPath, newHighLimit, newValue, newLowLimit, project):
    log.trace("Sending writeRecipeDetail message to gateway for %s - %s - %s - %s..." % (tagPath, str(newHighLimit), str(newValue), str(newLowLimit)))
    payload = {"tagPath":tagPath, "newHighLimit":newHighLimit, "newValue":newValue, "newLowLimit":newLowLimit}
    tagList=[payload]
    system.util.sendMessage(project, "tagWriter", {"command": "writeRecipeDetail", "tagList": tagList}, scope="G")

def writeRecipeDetails(tagList, project):
    log.trace("Sending writeRecipeDetail message to gateway for %s..." % (str(tagList)))
    system.util.sendMessage(project, "tagWriter", {"command": "writeRecipeDetail", "tagList": tagList}, scope="G")
    