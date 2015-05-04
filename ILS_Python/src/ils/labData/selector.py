'''
Created on Mar 29, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.labData.selector")

def select(selectorName, database = ""):
    print "Configuring lab data for %s..." % (selectorName)
    
    SQL = "select * from LtPHDSelectorView where selectorName = '%s'" % (selectorName)
    pds = system.db.runQuery(SQL, database)
    for record in pds:
        valueName = record["ValueName"]
        selectorTypeName = record["SelectorTypeName"]
        targetId = record["TargetId"]
        targetTextValue = record["TargetTextValue"]
        
        print "The selected value is: %s - %s - %i - %s" % (valueName, selectorTypeName, targetId, targetTextValue) 
        
        if selectorTypeName == "PHD Lab Value ItemId" or selectorTypeName == "PHD Lab Value Interface":
            if selectorTypeName == "PHD Lab Value ItemId":
                SQL = "update LtPHDValue set ItemId = '%s' where ValueId = %i " % (targetTextValue, targetId) 
            elif selectorTypeName == "PHD Lab Value Interface":
                import ils.labData.common.fetchInterfaceId as fetchInterfaceId
                interfaceId = fetchInterfaceId(targetTextValue, database)
                SQL = "update LtPHDValue set InterfaceId = %i where ValueId = %i " % (interfaceId, targetId) 
            
            rows = system.db.runUpdateQuery(SQL, database)
            if rows != 1:
                log.error("Error processing PHD Lab Value selector: %s - %s - %i - %s" % (valueName, selectorTypeName, targetId, targetTextValue))
            else:
                log.trace("Successfully processed PHD Lab Value selector: %s - %s - %i - %s" % (valueName, selectorTypeName, targetId, targetTextValue))
                
        
def updateItemId(targetName, itemId, database=""):
    from ils.labData.common import fetchValueId
    targetId = fetchValueId(targetName, database)

    if targetId == None:
        print "Error: target %s was not defined" % targetName
    else:
        SQL = "update LtPHDValue set ItemId = '%s' where ValueId = %i " % (itemId, targetId)
        print SQL 
        system.db.runUpdateQuery(SQL, database)

#
def configureSelector(selectorName, sourceName):
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    parentTagPath = '[' + provider + ']LabData/'
    tagPath = parentTagPath + selectorName
    print "Configuring: ", tagPath

    # Determine the type of the UDT   
    UDTType = system.tag.getAttribute(tagPath, "UDTParentType")
    print "UDT Type: ", UDTType

    if UDTType == "Lab Data/Lab Selector Value":
        badValueTag='{[.]../' + sourceName + '/badValue}'
        rawValueTag='{[.]../' + sourceName + '/rawValue}'
        sampleTimeTag='{[.]../' + sourceName + '/sampleTime}'
        updateFlagTag='{[.]../' + sourceName + '/updateFlag}'
        valueTag='{[.]../' + sourceName + '/value}'
    
        parameters={
                    'badValueTag':badValueTag, 
                    'rawValueTag':rawValueTag, 
                    'sampleTimeTag':sampleTimeTag,
                    'updateFlagTag':updateFlagTag,
                    'valueTag':valueTag
                    }
    
        print tagPath, parameters
        system.tag.editTag(tagPath, parameters=parameters)
        
    elif UDTType == "Lab Data/Lab Selector SQC":
        lowerLimitTag='{[.]../' + sourceName + '/lowerLimit}'
        lowerValidityLimitTag='{[.]../' + sourceName + '/lowerValidityLimit}'
        standardDeviationTag='{[.]../' + sourceName + '/standardDeviation}'
        targetTag='{[.]../' + sourceName + '/target}'
        upperLimitTag='{[.]../' + sourceName + '/upperLimit}'
        upperValidityLimitTag='{[.]../' + sourceName + '/upperValidityLimit}'
    
        parameters={
                    'lowerLimitTag':lowerLimitTag, 
                    'lowerValidityLimitTag':lowerValidityLimitTag, 
                    'standardDeviationTag':standardDeviationTag,
                    'targetTag':targetTag,
                    'upperLimitTag':upperLimitTag,
                    'upperValidityLimitTag':upperValidityLimitTag
                    }
    
        print tagPath, parameters
        system.tag.editTag(tagPath, parameters=parameters)
 
    elif UDTType == "Lab Data/Lab Selector Validity":
        lowerLimitTag='{[.]../' + sourceName + '/lowerLimit}'
        upperLimitTag='{[.]../' + sourceName + '/upperLimit}'
    
        parameters={
                    'lowerLimitTag':lowerLimitTag, 
                    'upperLimitTag':upperLimitTag
                    }
    
        print tagPath, parameters
        system.tag.editTag(tagPath, parameters=parameters)
    
    else:
        print "Unsupported UDT Type: ", UDTType     
                