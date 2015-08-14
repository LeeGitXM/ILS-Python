'''
Created on Mar 29, 2015

@author: Pete
'''
import system
log = system.util.getLogger("com.ils.labData.selector")

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
                
        
def updateItemIdCRAP(targetName, itemId, database=""):
    from ils.labData.common import fetchValueId
    targetId = fetchValueId(targetName, database)

    if targetId == None:
        print "Error: target %s was not defined" % targetName
    else:
        SQL = "update LtPHDValue set ItemId = '%s' where ValueId = %i " % (itemId, targetId)
        print SQL 
        system.db.runUpdateQuery(SQL, database)


def valueChanged(tagPath):
    log.trace("Detected a value change in: %s" % (tagPath))
    database = "XOM"
    
    tagRoot=tagPath.rstrip('/value')    
    enabled=system.tag.read(tagRoot + '/processingEnabled').value

    from ils.labData.scanner import storeSelector
    if enabled:
        storeSelector(tagPath, database)
    else:
        log.trace("Skipping the value change because processing is not enabled")
        

# Update the expression in the selector tag to get its values from a new source
# This operates entirely on tags and has no database transactions
def configureSelector(unitName, selectorName, sourceName):
    from ils.common.config import getTagProvider
    provider = getTagProvider()
    parentTagPath = '[' + provider + ']LabData/' + unitName + '/'
    tagPath = parentTagPath + selectorName
    log.trace("Configuring: %s" % (tagPath))

    # Determine the type of the UDT   
    UDTType = system.tag.getAttribute(tagPath, "UDTParentType")
    log.trace("UDT Type: %s" % (UDTType))

    if UDTType == "Lab Data/Lab Selector Value":
        badValueTag='{[.]../' + sourceName + '/badValue}'
        rawValueTag='{[.]../' + sourceName + '/rawValue}'
        sampleTimeTag='{[.]../' + sourceName + '/sampleTime}'
        rawSampleTimeTag='{[.]../' + sourceName + '/rawSampleTime}'
        valueTag='{[.]../' + sourceName + '/value}'
        statusTag='{[.]../' + sourceName + '/status}'
    
        parameters={
                    'badValueTag':badValueTag, 
                    'rawValueTag':rawValueTag, 
                    'sampleTimeTag':sampleTimeTag,
                    'rawSampleTimeTag':rawSampleTimeTag,
                    'valueTag':valueTag,
                    'statusTag':statusTag
                    }
    
        log.trace("%s - %s" % (tagPath, str(parameters)))
        system.tag.editTag(tagPath, parameters=parameters)
        
        # Update the LtSelector table to reflect the current active source
        valueId = system.db.runScalarQuery("select valueId from LtValue where ValueName = '%s'" % (selectorName))
        sourceValueId = system.db.runScalarQuery("select valueId from LtValue where ValueName = '%s'" % (sourceName))
        system.db.runUpdateQuery("update LtSelector set sourceValueId = %i where ValueId = %i" % (sourceValueId, valueId))
        
    elif UDTType == "Lab Data/Lab Selector Limit SQC":
        lowerSQCLimitTag='{[.]../' + sourceName + '/lowerSQCLimit}'
        lowerValidityLimitTag='{[.]../' + sourceName + '/lowerValidityLimit}'
        standardDeviationTag='{[.]../' + sourceName + '/standardDeviation}'
        targetTag='{[.]../' + sourceName + '/target}'
        upperSQCLimitTag='{[.]../' + sourceName + '/upperSQCLimit}'
        upperValidityLimitTag='{[.]../' + sourceName + '/upperValidityLimit}'
    
        parameters={
                    'lowerSQCLimitTag':lowerSQCLimitTag, 
                    'lowerValidityLimitTag':lowerValidityLimitTag, 
                    'standardDeviationTag':standardDeviationTag,
                    'targetTag':targetTag,
                    'upperSQCLimitTag':upperSQCLimitTag,
                    'upperValidityLimitTag':upperValidityLimitTag
                    }
    
        log.trace("%s - %s" % (tagPath, str(parameters)))
        system.tag.editTag(tagPath, parameters=parameters)
 
    elif UDTType == "Lab Data/Lab Selector Limit Validity":
        lowerValidityLimitTag='{[.]../' + sourceName + '/lowerValidityLimit}'
        upperValidityLimitTag='{[.]../' + sourceName + '/upperValidityLimit}'
    
        parameters={
                    'lowerValidityLimitTag':lowerValidityLimitTag, 
                    'upperValidityLimitTag':upperValidityLimitTag
                    }
    
        log.trace("%s - %s" % (tagPath, str(parameters)))
        system.tag.editTag(tagPath, parameters=parameters)
        
    elif UDTType == "Lab Data/Lab Selector Limit Release":
        lowerReleaseLimitTag='{[.]../' + sourceName + '/lowerReleaseLimit}'
        upperReleaseLimitTag='{[.]../' + sourceName + '/upperReleaseLimit}'
    
        parameters={
                    'lowerReleaseLimitTag':lowerReleaseLimitTag, 
                    'upperReleaseLimitTag':upperReleaseLimitTag
                    }
    
        log.trace("%s - %s" % (tagPath, str(parameters)))
        system.tag.editTag(tagPath, parameters=parameters)
    
    else:
        log.error("Unsupported UDT Type: %s" % (UDTType))     

# When a selector has a new source, the tags are configured above, but we also need to update the 
# description of the selector, which shows up in the display table.  For example, they don't want to see
# Mooney lab data (which doesn't tell them where it came from), they want to see Rx1-ML or Rx2-ML
def updateSelectorDisplayTableDescription(selectorName, sourceName):
    
    SQL = "update LtValue set Description = (select description from LtValue where ValueName = '%s') "\
        " where ValueName = '%s'" % (sourceName, selectorName)
    print SQL
    rows = system.db.runUpdateQuery(SQL)
    print "Updated %i rows" % (rows)