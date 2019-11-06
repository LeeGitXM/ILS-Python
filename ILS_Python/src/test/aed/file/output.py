'''
Created on Jan 7, 2017

@author: phass
'''

import string, system
from xom.emre.test.file.sql import getValue as getSqlValue
log = system.util.getLogger("com.ils.aed.python.test")

# 04/19/2013
#  Write the first line of the regression test output file.  
# This runs on the client, writing the actual results happens in the gateway, so if the test is 
# being run from a client that is not the same computer as the gateway, then the header will
# be in a different file from the data.

def writeHeader(path,format,params,sqlparams) :
    lineList = [format,params,sqlparams]
    line = ",".join(lineList)
    line += "\n"
    system.file.writeFile(path,line)
    
def writeLine(results) :
    # The first dictionary in the list contains all we 
    # need to know about the required output.
    if len(results) > 0 :
        properties = results[0]
        log.tracef("The properties are: %s", str(properties))
        path = properties.get('DataOutputPath','unknown')
        format = properties.get('TimeFormat','unknown')
        params = properties.get('OutputParameters','unknown')
        sqlparams = properties.get('SQLParameters','unknown')
        tagparams = properties.get('Tags','')
        
        # If the path isn't defined, then do nothing
        if path!='unknown' :
            # Search the results list for results of the desired model
            
            if len(results) > 1:
                # The first field in the results file is the timestamp, each model result
                # contains a timestamp, they should all be the same, so get the timestamp 
                # out of the first result
                resultDictionary = results[1]
                log.tracef("The results dictionary is: %s", str(resultDictionary))
                timestamp = getTimestamp(resultDictionary,format)
                fields = []
                fields.append(timestamp)
                parameters = params.split(",")
                log.tracef("The parameters are: %s", parameters)

                # Parameter may take two forms.  It can be the same form that was used in all 
                # of the unit testing, i.e., the name of a parameter in the result dictionary. or it can
                # be the enhanced form where it takes the form "parameter:modelId".  If the regression 
                # test involves multiple models, then the second form is highly recommended. 
                for parameter in parameters :
                    log.tracef("-----")
                    log.tracef("Processing parameter: %s", parameter)
                    tokens = parameter.split(":")
                    if len(tokens) == 1:
                        val = getValue(parameter,results[1])
                        val = string.upper(str(val))
                        fields.append(val)    
                    else:
                        modelId = tokens[1]
                        resultDictionary = dictionaryForModelId(modelId,results)
                        val = getValue(tokens[0],resultDictionary)
                        fields.append(val) 

                parameters = sqlparams.split(",")
                for parameter in parameters :
                    tokens = parameter.split(":")
                    modelId = tokens[1]
                    val = getSqlValue(tokens[0], modelId)
                    fields.append( str(val) ) 
                    
                tags = tagparams.split(",")
                for tag in tags :
                    tagPath = "[AED]AED/" + tag
                    log.tracef("Reading %s", tagPath)
                    qv = system.tag.read(tagPath)
                    log.tracef("   ...read %s", qv)
                    fields.append( str(qv.value) ) 

                # Make a comma delimited text string out of the fields        
                line = ",".join(fields)
                line += "\n"
                
                # Append the line to the output file
                log.tracef("Writing: %s", line)
                system.file.writeFile(path,line,True)  

# Search the list of results for the requested model's results
def dictionaryForModelId(modelId, results):
    for d in results[1:] :
        if d.get('id','error') == modelId :
            return d
    return None

# Use the data collection time, if it exists
def getTimestamp(resultDictionary, format) :
#    import system.ils.test.date as date
    if resultDictionary == None :
        return ''

    ts = resultDictionary.get('timestamp', None)
    if ts == None :
        return ''

#    timestamp = date.convertDateString(ts,TSFormat,format)
    return ts

# We should have some try/except blocks here...
def getValue(param, resultDictionary) :
    log.tracef("Getting %s...", param)
    if param == None :
        return ''
    
    if resultDictionary == None :
        return ''
    
    params = param.split(".")
    if len(params) == 1 :
        val = resultDictionary.get(param,"")
        val = roundFloatValue(val)
        val = string.upper(str(val))
        log.tracef("   ...found %s", str(val))
        return val
    elif len(params) == 2 :
        log.tracef("Getting embedded results...")
        resultDictionary = resultDictionary.get(params[0], {})
        log.tracef("   the embedded results are: %s", str(resultDictionary))
        val = resultDictionary.get(params[1],"CRAP")
        val = roundFloatValue(val)
        val = string.upper(str(val))
        log.tracef("   ...found %s", str(val))
        return val
    else:
        log.error("Whoa I didn't expect a third level of nesting!")
        return "SHIT"

def roundFloatValue(val):
    
    try:
        floatVal = float(val)
        floatVal = round(floatVal, 4)
        log.tracef("...it was a float: converted %s to %s", val, str(floatVal))
        return str(floatVal)
    except:
        log.tracef("It must not have been a float...")
        return val 