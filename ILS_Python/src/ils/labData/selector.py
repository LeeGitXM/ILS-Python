'''
Created on Mar 29, 2015

@author: Pete
'''
import system
from ils.common.error import catchError
from ils.common.config import getDatabase, getDatabaseClient
from ils.log import getLogger
log =getLogger(__name__)

def valueChanged(tagPath):
    import time
    try:
        log.trace("Detected a value change in: %s" % (tagPath))
        database = getDatabase()
     
        # Find the root of the tag by stripping off the /value or /sampleTime   
        tagRoot=tagPath.rstrip('/trigger') 
        enabled=system.tag.read(tagRoot + '/processingEnabled').value
    
        if enabled:
            # Because the value and the sampleTime tags both update nearly simultaneously, wait here 
            # to allow them to both complete and keep the data consistent
            time.sleep(5)
            from ils.labData.scanner import storeSelector
            storeSelector(tagRoot, database)
        else:
            log.trace("Skipping the value change because processing is not enabled")
    except:
        catchError("%s.valueChanged" % (__name__))
        
    # Reset the trigger
    system.tag.write(tagRoot + "/trigger", False)


def configureSelector(unitName, selectorName, sourceName, tagProvider, database):
    '''
    Update the expression in the selector tag to get its values from a new source
    This operates entirely on tags and has no database transactions
    '''
    parentTagPath = '[' + tagProvider + ']LabData/' + unitName + '/'
    tagPath = parentTagPath + selectorName
    log.infof("...configuring selector <%s> for source <%s>...", tagPath, sourceName)

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
        valueId = system.db.runScalarQuery("select valueId from LtValue where ValueName = '%s'" % (selectorName), database)
        sourceValueId = system.db.runScalarQuery("select valueId from LtValue where ValueName = '%s'" % (sourceName), database)
        system.db.runUpdateQuery("update LtSelector set sourceValueId = %i where ValueId = %i" % (sourceValueId, valueId), database)
        
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
def updateSelectorDisplayTableDescription(selectorName, sourceName, database):
    SQL = "update LtValue set Description = (select description from LtValue where ValueName = '%s') "\
        " where ValueName = '%s'" % (sourceName, selectorName)
    rows = system.db.runUpdateQuery(SQL, database)
    log.trace("Updated %i rows in LtValue" % (rows))