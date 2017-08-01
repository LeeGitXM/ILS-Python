'''
Created on Dec 17, 2015

@author: rforbes
'''
from ils.common.error import catch
from ils.sfc.gateway.api import getChartLogger, getProviderName, handleUnexpectedGatewayError, standardDeviation, getTopLevelProperties, getStepProperty, getTopChartRunId
from ils.sfc.recipeData.api import s88Set
from ils.sfc.common.constants import COLLECT_DATA_CONFIG
from ils.sfc.common.util import substituteHistoryProvider
from system.util import jsonDecode
import system

def activate(scopeContext, stepProperties, state):

    try:
        chartScope = scopeContext.getChartScope()
        provider = getProviderName(chartScope)
        stepScope = scopeContext.getStepScope()
        logger = getChartLogger(chartScope)
        logger.trace("Executing a collect data block")
        configJson = getStepProperty(stepProperties, COLLECT_DATA_CONFIG)
        config = jsonDecode(configJson)
        logger.trace("Block Configuration: %s" % (str(config)))
    
        # config.errorHandling
        for row in config['rows']:
            valueType = row['valueType']
            
            if valueType == 'current':
                try:
                    tagPath = "[%s]%s" % (provider, row['tagPath'])
                    logger.trace("Collecting %s from %s" % (str(valueType), str(tagPath)))
                    tagReadResult = system.tag.read(tagPath)
                    tagValue = tagReadResult.value
                    readOk = tagReadResult.quality.isGood()
                except:
                    logger.error("Error reading the current value for %s" % (tagPath))
                    readOk = False
            else:
                tagPath = substituteHistoryProvider(chartScope, row['tagPath'])
                rangeMinutes = -1.0 * float(row['pastWindow'])
                logger.trace("Collecting %s from %s for %f minutes" % (str(valueType), str(tagPath), rangeMinutes))
                tagPaths = [tagPath]
                if valueType == 'stdDeviation':
                    logger.trace("   calling queryTagHistory() to fetch the dataset for calculating the standard deviation...") 
                    tagValues = system.tag.queryTagHistory(tagPaths, rangeMinutes=rangeMinutes, ignoreBadQuality=True)
                    logger.trace("   calculating the standard deviation from the raw dataset...")
                    tagValue = standardDeviation(tagValues, 1)
                    logger.trace("   ...the standard deviation is: %s" % (tagValue))
                    readOk = True
                else:
                    if valueType == 'average':
                        mode = 'Average'
                    elif valueType == 'minimum':
                        mode = 'Minimum'
                    elif valueType == 'maximum':
                        mode = 'Maximum'
                    else:
                        logger.error("Unknown value type" + valueType)
                        mode = 'Average'
                    try:
                        # This should return a dataset with a single row, but it seems to return two rows where
                        # the first row contains the value we are looking for.  I'm not sure what is in the second row.
                        tagValues = system.tag.queryTagHistory(tagPaths, returnSize=1, rangeMinutes=rangeMinutes, aggregationMode=mode, 
                                ignoreBadQuality=True, returnFormat='Wide')
                        
                        # ?? how do we tell if there was an error??
                        if tagValues.rowCount > 0:
                            tagValue = tagValues.getValueAt(0,1)
                            logger.trace("   ... returned: %s" % str(tagValue) )
                            readOk = True
                        else:
                            logger.warn("queryTagHistory did not return a value")
                            readOk = False
                    except:
                        txt=catch(__name__, "Error collecting data from %s for %s minutes using %s" % (tagPath, str(row['pastWindow']), mode))
                        logger.error(txt)
                        readOk = False
            if readOk:
                logger.info("Tag Path: %s, Mode: %s => %f " % (tagPath, valueType, tagValue))
                s88Set(chartScope, stepScope, row['recipeKey'], tagValue, row['location'])
            else:
                # ?? should we write a None value to recipe data for abort/timeout cases ??
                errorHandling = config['errorHandling']
                if errorHandling == 'abort':
                    topRunId = getTopChartRunId(chartScope)
                    system.sfc.cancelChart(topRunId)
                elif errorHandling == 'timeout':
                    topScope = getTopLevelProperties(chartScope)
                    topScope['timeout'] = True
                elif errorHandling == 'defaultValue':
                    s88Set(chartScope, stepScope, row['recipeKey'], row['defaultValue'], row['location'] )
    except:
        handleUnexpectedGatewayError(chartScope, stepProperties, 'Unexpected error in collectData.py', logger)
    finally:
        return True