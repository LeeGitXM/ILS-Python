'''
Created on Dec 17, 2015

@author: rforbes
'''
def activate(scopeContext, stepProperties):
    from ils.sfc.gateway.util import standardDeviation, getTopLevelProperties, getStepProperty, \
    getTopChartRunId, handleUnexpectedGatewayError
    from ils.sfc.gateway.api import getChartLogger, s88Set
    from system.ils.sfc.common.Constants import COLLECT_DATA_CONFIG
    from ils.sfc.common.util import substituteProvider
    from system.util import jsonDecode
    import system.tag
 
    try:
        chartScope = scopeContext.getChartScope()
        stepScope = scopeContext.getStepScope()
        logger = getChartLogger(chartScope)
        logger.trace("Executing a collect data block")
        configJson = getStepProperty(stepProperties, COLLECT_DATA_CONFIG)
        config = jsonDecode(configJson)
        logger.trace("Block Configuration: %s" % (str(config)))
    
        # config.errorHandling
        for row in config['rows']:
            tagPath = substituteProvider(chartScope, row['tagPath'])
            valueType = row['valueType']
            logger.info("Collecting %s from %s" % (str(valueType), str(tagPath)))
            if valueType == 'current':
                try:
                    tagReadResult = system.tag.read(tagPath)
                    tagValue = tagReadResult.value
                    readOk = tagReadResult.quality.isGood()
                except:
                    readOk = False
            else:
                tagPaths = [tagPath]
                if valueType == 'stdDeviation':
                    logger.trace("calling queryTagHistory() to fetch the dataset for calculating the standard deviation") 
                    tagValues = system.tag.queryTagHistory(tagPaths, rangeHours=row['pastWindow'], ignoreBadQuality=True)
                    logger.trace("Calculating the standard deviation...")
                    tagValue = standardDeviation(tagValues, 1)
                    logger.trace("The standard deviation is: %s" % (tagValue))
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
                        logger.trace("calling queryTagHistory() - rangeMinutes: %s, aggregationMode: %s" % (str(row['pastWindow']), mode))
                        tagValues = system.tag.queryTagHistory(tagPaths, returnSize=1, rangeMinutes=row['pastWindow'], aggregationMode=mode, ignoreBadQuality=True)
                        # ?? how do we tell if there was an error??
                        if tagValues.rowCount == 1:
                            tagValue = tagValues.getValueAt(0,1)
                            print 'mode', mode, 'value', tagValue
                            logger.trace("Successfully returned: %s" )
                            readOk = True
                        else:
                            readOk = False
                    except:
                        readOk = False
            if readOk:
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
        handleUnexpectedGatewayError(chartScope, 'Unexpected error in collectData.py', logger)
    finally:
        return True