'''
Created on Nov 30, 2016

@author: phassler
'''

import system, string
from ils.io.util import readTag
from ils.common.units import convert
from ils.common.cast import toBit, isFloat
from ils.common.util import formatDateTime, isText
from ils.common.util import substituteProvider
from ils.sfc.common.constants import DATABASE, START_TIMER, STOP_TIMER, PAUSE_TIMER, RESUME_TIMER, CLEAR_TIMER, \
    TAG_PROVIDER, TIMER_CLEARED, TIMER_STOPPED, TIMER_RUNNING, TIMER_PAUSED, GLOBAL_SCOPE, OPERATION_SCOPE, PHASE_SCOPE

from ils.sfc.recipeData.constants import ARRAY, INPUT, MATRIX, OUTPUT, OUTPUT_RAMP, SQC, RECIPE, \
    SIMPLE_VALUE, TIMER, ENCLOSING_STEP_SCOPE_KEY, PARENT, S88_LEVEL, STEP_NAME

from ils.log import getLogger
logger = getLogger(__name__)

def walkUpHieracrchy(chartProperties, stepType):
    logger.tracef("Walking up the hierarchy looking for %s", stepType)
    thisStepType = ""
    RECURSION_LIMIT = 100
    i = 1
    while thisStepType == None or string.upper(thisStepType) <> string.upper(stepType):
        i = i + 1
        if chartProperties.get(ENCLOSING_STEP_SCOPE_KEY, None) != None:
            enclosingStepScope = chartProperties.get(ENCLOSING_STEP_SCOPE_KEY, None) 
            logger.tracef("  The enclosing step scope is: %s", str(enclosingStepScope))
            superiorName = enclosingStepScope.get(STEP_NAME, None)
            thisStepType = enclosingStepScope.get(S88_LEVEL)
            
            chartProperties = chartProperties.get(PARENT)
            
            chartPath = chartProperties.get("chartPath", None)
            logger.tracef("  The superior step: %s - %s - %s", thisStepType, chartPath, superiorName)
        else:
            print "Throw an error here - we are at the top"
            return None, None
        
        if i > RECURSION_LIMIT:
            logger.error("***** HIT A RECURSION PROBLEM ****")
            return None, None
    
    return chartPath, superiorName
       

def getSuperiorStep(chartProperties):
    logger.tracef("Getting the superior step...")
    if chartProperties.get(ENCLOSING_STEP_SCOPE_KEY, None) != None:
        enclosingStepScope = chartProperties.get(ENCLOSING_STEP_SCOPE_KEY, None) 
        logger.tracef("  The enclosing step scope is: %s", str(enclosingStepScope))
        superiorName = enclosingStepScope.get(STEP_NAME, None)
        
        chartProperties = chartProperties.get(PARENT)
        chartPath = chartProperties.get("chartPath", None)
    else:
        print "Throw an error here - we are at the top"
        return None, None
    
    logger.tracef("  The superior step is %s - %s ", chartPath, superiorName)
    return chartPath, superiorName

'''
This is only called from a transition.  The SFC framework passes the PRIOR step's properties
in stepProperties.
'''
def getPriorStep(chartProperties, stepProperties):
    logger.tracef("Getting the chart path and prior step name...")
    chartPath = chartProperties.get("chartPath", None)
    priorName = stepProperties.get(STEP_NAME, None)  
    logger.tracef("...returning %s and %s", chartPath, priorName)
    return chartPath, priorName

# Get the S88 level of the step superior to this chart.  The chart that is encapsulated under an operation is operation scope.
def getEnclosingStepScope(chartScope):
    enclosingScope = "foo"
    
    if chartScope.get(ENCLOSING_STEP_SCOPE_KEY, None) != None:
        print "Found an enclosing step"
        parentChartScope = getSubScope(chartScope, PARENT)
        parentIsRoot = getSubScope(parentChartScope, PARENT) == None
        enclosingStepScope = getSubScope(chartScope, ENCLOSING_STEP_SCOPE_KEY)            
        scopeIdentifier = enclosingStepScope.get(S88_LEVEL)
        if scopeIdentifier <> None:
            enclosingScope = scopeIdentifier
        elif parentIsRoot:
            enclosingScope = "global"
    else:
        # There is no enclosing scope at the very top, scope only starts when we get under a unit procedure
        enclosingScope = None

    return enclosingScope   


def getStepInfoFromId(stepId, db):
    '''  Return the chartPath and stepName from the stepId. '''
    SQL = "select ChartPath, StepName from SfcStepView where StepId = %d" % (stepId)
    pds = system.db.runQuery(SQL, db)
    if len(pds) == 0:
        logger.errorf("Unable to find a step with step id: %d", stepId)
        return None, None
    
    if len(pds) > 1:
        logger.errorf("Multiple steps found for step id: %d", stepId)
        return None, None
    
    record = pds[0]
    return record["ChartPath"], record["StepName"]

def getStepInfoFromUUID(stepUUID, db):
    '''  Return the chartPath and stepName from the stepUUID. '''
    SQL = "select ChartPath, StepName from SfcStepView where StepUUID = %d" % (stepUUID)
    pds = system.db.runQuery(SQL, db)
    if len(pds) == 0:
        logger.errorf("Unable to find a step with step UUID: %s", stepUUID)
        return None, None
    
    if len(pds) > 1:
        logger.errorf("Multiple steps found for step UUID: %s", stepUUID)
        return None, None
    
    record = pds[0]
    return record["ChartPath"], record["StepName"]

def getSubScope(scope, key):
    print "Getting %s out of %s" % (scope, str(key))
    subScope = scope.get(key, None)
    print "The sub scope is: ", subScope
    return subScope

def fetchRecipeDataType(stepId, folder, key, attribute, db):
    logger.tracef("Fetching %s.%s.%s from %d", folder, key, attribute, stepId)
    chartPath, stepName = getStepInfoFromId(stepId, db)
    
    # Separate the key from the array index if there is an array index
    attribute, arrayIndex, rowIndex, columnIndex = checkForArrayOrMatrixReference(attribute)
    recipeDataId, recipeDataType, units = getRecipeDataId(stepName, stepId, folder + "." + key, db)
    return recipeDataType

def recipeGroupExists(stepId, key, parentKey, db):
    if parentKey == "":
        SQL = "select * from SfcRecipeDataFolderView "\
            " where stepId = %d and RecipeDataKey = '%s' and ParentRecipeDataFolderId is NULL" % (stepId, key) 
    else:
        logger.error("ERROR Support for nested folders has not been implemented!")
    
    pds = system.db.runQuery(SQL, db)
    
    if len(pds) == 1:
        logger.tracef("...it exists!")
        return True
    
    logger.tracef("...it does not exist!")
    return False

def recipeDataExists(stepId, folder, key, attribute, db):
    logger.tracef("Checking if %s.%s.%s from step id %d exists...", folder, key, attribute, stepId)
    
    # Separate the key from the array index if there is an array index
    attribute, arrayIndex, rowIndex, columnIndex = checkForArrayOrMatrixReference(attribute)
    
    '''
    I can't use the handy utility getRecieDataId() which does all of this work because it logs an error and throws an exception if the 
    recipe data doesn't exist.  The whole point of this is do a test to see if it exists ao that an error can be avoided!
    '''
    
    if folder == "":
        SQL = "select RECIPEDATAID, RECIPEDATATYPE, UNITS "\
            " from SfcRecipeDataView where stepId = %d and RecipeDataKey = '%s' and RecipeDataFolderId is NULL" % (stepId, key) 
    else:
        recipeDataFolderId = getFolderForStep(stepId, folder, db)
        
        if recipeDataFolderId == None:
            logger.tracef("...the folder does not exist!")
            return False
        
        SQL = "select RECIPEDATAID, RECIPEDATATYPE, UNITS "\
            " from SfcRecipeDataView where stepId = %d and RecipeDataKey = '%s' and RecipeDataFolderId = %s" % (stepId, key, str(recipeDataFolderId)) 

    pds = system.db.runQuery(SQL, db)
    
    if len(pds) == 1:
        logger.tracef("...it exists!")
        return True
    
    logger.tracef("...it does not exist!")
    return False

def recipeDataExistsForStepId(stepId, folderID, key, db):
    logger.tracef("Checking if %s.%s from %s exists...", folderID, key, stepId)
    
    '''
    I can't use the handy utility getRecieDataId() which does all of this work because it logs an error and throws an exception if the 
    recipe data doesn't exist.  The whole point of this is do a test to see if it exists ao that an error can be avoided!
    '''
    
    if folderID < 0:
        SQL = "select RECIPEDATAID, RECIPEDATATYPE, UNITS "\
            " from SfcRecipeDataView where stepId = %s and RecipeDataKey = '%s' and RecipeDataFolderId is NULL" % (str(stepId), key) 
    else:        
        SQL = "select RECIPEDATAID, RECIPEDATATYPE, UNITS "\
            " from SfcRecipeDataView where stepId = %s and RecipeDataKey = '%s' and RecipeDataFolderId = %s" % (str(stepId), key, str(folderID)) 

    pds = system.db.runQuery(SQL, db)
    
    if len(pds) == 1:
        logger.tracef("...it exists!")
        return True
    
    logger.tracef("...it does not exist!")
    return False

def getRecipeDataId(stepName, stepId, keyOriginal, db):
    logger.tracef("Fetching recipe data id for %s - %s", stepId, keyOriginal)
    
    ''' This utility requires a key and an attribute, so add a fake attribute and then ignore it  '''
    folder,key,attribute = splitKey(keyOriginal + ".value")

    if folder in ["", None, "NULL"]:
        logger.tracef("...there isn't a folder...")
        SQL = "select RECIPEDATAID, RECIPEDATATYPE, UNITS "\
            " from SfcRecipeDataView where stepId = %s and RecipeDataKey = '%s' and RecipeDataFolderId is NULL" % (str(stepId), key) 
    else:        
        recipeDataFolderId = getFolderForStep(stepId, folder, db)
        logger.tracef("...found folder Id :%s:", str(recipeDataFolderId))
        SQL = "select RECIPEDATAID, RECIPEDATATYPE, UNITS "\
            " from SfcRecipeDataView where stepId = %s and RecipeDataKey = '%s' and RecipeDataFolderId = %s" % (str(stepId), key, str(recipeDataFolderId)) 

    pds = system.db.runQuery(SQL, db)
    if len(pds) == 0:
        if folder == "":
            logger.errorf("Error the key <%s> was not found for step <%s> using db <%s>", key, stepName, db)
            raise RecipeException("Missing recipe data - Key <%s> was not found for step <%s> using db <%s> (id %d)" % (key, stepName, db, stepId))
        else:
            logger.errorf("Error the key <%s.%s> was not found for step <%s> using db <%s>", folder, key, stepName, db)
            raise RecipeException("Missing recipe data - Key <%s.%s> was not found for step <%s> using db <%s>(id %d)" % (folder, key, stepName, db, stepId))
    
    if len(pds) > 1:
        logger.errorf("Error multiple records were found")
        raise RecipeException("Multiple records were found for key <%s> for step %s (id %d))" % (keyOriginal, stepName, stepId))
    
    record = pds[0]
    recipeDataId = record["RECIPEDATAID"]
    recipeDataType = record["RECIPEDATATYPE"]
    units = record["UNITS"]
    logger.tracef("...the recipe data type is: %s for id: %d", recipeDataType, recipeDataId)
    
    return recipeDataId, recipeDataType, units

def fetchRecipeData(stepName, stepId, folder, key, attribute, db):
    logger.tracef("Fetching %s.%s.%s from step id: %d", folder, key, attribute, stepId)
 
    # Separate the key from the array index if there is an array index
    attribute, arrayIndex, rowIndex, columnIndex = checkForArrayOrMatrixReference(attribute)
    recipeDataId, recipeDataType, units = getRecipeDataId(stepName, stepId, folder + "." + key, db)
    
    # These attributes are common to all recipe data classes
    attribute = string.upper(attribute)
    if attribute == "UNITS":
        val = units
    elif attribute == "RECIPEDATATYPE":
        val = recipeDataType
    elif attribute in ["DESCRIPTION","LABEL","ADVICE"]:
        SQL = "select %s from SfcRecipeData where RecipeDataId = %d" % (attribute, recipeDataId)
        val = system.db.runScalarQuery(SQL, db)
    else:
        val = fetchRecipeDataFromId(recipeDataId, recipeDataType, attribute, units, arrayIndex, rowIndex, columnIndex, db)
    
    return val, units

def getFolderForStep(stepId, folder, db):
    logger.tracef("...getting the recipeId for folder <%s> for step <%d>", folder, stepId)
    SQL = "Select RecipeDataFolderId, RecipeDataKey, ParentRecipeDataFolderId "\
        "from SfcRecipeDataFolderView "\
        "where StepId = '%s'" % (str(stepId))
    folderPDS = system.db.runQuery(SQL, db)
    
    tokens = folder.split(".")
    recipeDataFolderId = None
    for token in tokens:
        for record in folderPDS:
            if string.lower(record["RecipeDataKey"]) == string.lower(token) and record["ParentRecipeDataFolderId"] == recipeDataFolderId:
                recipeDataFolderId = record["RecipeDataFolderId"]
                break

    return recipeDataFolderId

'''
This is designed to be called from private SFC block internals that are called over and over again.  The recipeId will be fetched the first time and 
can then be used for subsequent calls as the block evaluates every second.
'''
def fetchRecipeDataFromId(recipeDataId, recipeDataType, attribute, units, arrayIndex=0, rowIndex=0, columnIndex=0, db=""):
    attribute = string.upper(attribute)
    logger.tracef("Fetching recipe data using recipeDataId: %d of type %s, attribute: %s", recipeDataId, recipeDataType, attribute)
    
    if recipeDataType == SIMPLE_VALUE:
        SQL = "select RECIPEDATAKEY, VALUETYPE, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE from SfcRecipeDataSimpleValueView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        
        if attribute in ["VALUETYPE"]:
            val = record[attribute]
        elif attribute == "VALUE":
            valueType = record['VALUETYPE']
            val = record["%sVALUE" % string.upper(valueType)]
            logger.tracef("Fetched the value: %s", str(val))
        else:
            raise RecipeException("Unsupported attribute: %s for a simple value recipe data %s" % (attribute, record['RECIPEDATAKEY']))
    
    elif recipeDataType == TIMER:
        SQL = "select STARTTIME, STOPTIME, TIMERSTATE, CUMULATIVEMINUTES from SfcRecipeDataTimer where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        
        if attribute in ["CUMULATIVEMINUTES", "STARTTIME", "STOPTIME", "TIMERSTATE"]:
            val = record[attribute]
        elif attribute in ["RUNTIME", "ELAPSEDMINUTES"]:
            timerState = record["TIMERSTATE"]
            if timerState in ['NULL', None, 'Cleared']:
                val = 0
            elif timerState in [TIMER_STOPPED, TIMER_PAUSED]:
                startTime = record["STARTTIME"]
                stopTime = record['STOPTIME']
                cumulativeMinutes = record['CUMULATIVEMINUTES']
                runTimeMinutes = cumulativeMinutes
                val = runTimeMinutes
            elif timerState in [TIMER_RUNNING]:
                startTime = record["STARTTIME"]
                cumulativeMinutes = record['CUMULATIVEMINUTES']
                if cumulativeMinutes == None:
                    cumulativeMinutes = 0.0
                now = system.date.now()
                runTimeMinutes = cumulativeMinutes + system.date.secondsBetween(startTime, now) / 60.0
                val = runTimeMinutes
            elif timerState in [TIMER_CLEARED]:
                val = 0.0

        else:
            raise RecipeException("Unsupported attribute: %s for a timer recipe data" % attribute)
        
        logger.tracef("Fetched the value: %s", str(val))
        
    
    elif recipeDataType == RECIPE:
        SQL = "select RECIPEDATAKEY, PRESENTATIONORDER, STORETAG, COMPARETAG, MODEATTRIBUTE, MODEVALUE, CHANGELEVEL, RECOMMENDEDVALUE, "\
            "LOWLIMIT, HIGHLIMIT "\
            "from SfcRecipeDataRecipeView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        
        if attribute in ["PRESENTATIONORDER", "STORETAG", "COMPARETAG", "MODEATTRIBUTE", "MODEVALUE", "CHANGELEVEL", "RECOMMENDEDVALUE", "LOWLIMIT", "HIGHLIMIT"]:
            val = record[attribute]
        else:
            raise RecipeException("Unsupported attribute: %s for an input recipe data %s" % (attribute, record['RECIPEDATAKEY']))
    
    elif recipeDataType == SQC:
        SQL = "select RECIPEDATAKEY, LOWLIMIT, TARGETVALUE, HIGHLIMIT from SfcRecipeDataSQCView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        
        if attribute in ["LOWLIMIT", "TARGETVALUE", "HIGHLIMIT"]:
            val = record[attribute]
        else:
            raise RecipeException("Unsupported attribute: %s for an sqc recipe data %s" % (attribute, record['RECIPEDATAKEY']))
    
    elif recipeDataType == INPUT:
        SQL = "select TAG, RECIPEDATAKEY, VALUETYPE, ERRORCODE, ERRORTEXT, RECIPEDATATYPE, "\
            "TARGETFLOATVALUE, TARGETINTEGERVALUE, TARGETSTRINGVALUE, TARGETBOOLEANVALUE, "\
            "PVFLOATVALUE, PVINTEGERVALUE, PVSTRINGVALUE, PVBOOLEANVALUE, "\
            "PVMONITORACTIVE, PVMONITORSTATUS "\
            "from SfcRecipeDataInputView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueType = string.upper(record["VALUETYPE"])
        
        if attribute in ["TAG","VALUETYPE","ERRORCODE","ERRORTEXT","PVMONITORACTIVE","PVMONITORSTATUS"]:
            val = record[attribute]
        elif attribute == "TARGETVALUE":
            theAttribute = "TARGET%sVALUE" % (valueType)
            val = record[theAttribute]
        elif attribute == "PVVALUE":
            theAttribute = "PV%sVALUE" % (valueType)
            val = record[theAttribute]
        else:
            raise RecipeException("Unsupported attribute: %s for an input recipe data %s" % (attribute, record['RECIPEDATAKEY']))
    
    elif recipeDataType == OUTPUT:
        SQL = "select RECIPEDATAKEY, TAG, VALUETYPE, OUTPUTTYPE, DOWNLOAD, DOWNLOADSTATUS, ERRORCODE, ERRORTEXT, TIMING, RECIPEDATATYPE, "\
            "MAXTIMING, ACTUALTIMING, ACTUALDATETIME, OUTPUTFLOATVALUE, OUTPUTINTEGERVALUE, OUTPUTSTRINGVALUE, OUTPUTBOOLEANVALUE, "\
            "TARGETFLOATVALUE, TARGETINTEGERVALUE, TARGETSTRINGVALUE, TARGETBOOLEANVALUE, "\
            "PVFLOATVALUE, PVINTEGERVALUE, PVSTRINGVALUE, PVBOOLEANVALUE, "\
            "PVMONITORACTIVE, PVMONITORSTATUS, WRITECONFIRM, WRITECONFIRMED "\
            "from SfcRecipeDataOutputView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueType = string.upper(record["VALUETYPE"])
        
        if attribute in ["TAG","VALUETYPE","OUTPUTTYPE","DOWNLOAD","DOWNLOADSTATUS","ERRORCODE","ERRORTEXT","TIMING","MAXTIMING",\
                         "ACTUALTIMING","ACTUALDATETIME","PVMONITORACTIVE","PVMONITORSTATUS","WRITECONFIRM","WRITECONFIRMED"]:
            val = record[attribute]
        elif attribute == "OUTPUTVALUE":
            theAttribute = "OUTPUT%sVALUE" % (valueType)
            val = record[theAttribute]
        elif attribute == "TARGETVALUE":
            theAttribute = "TARGET%sVALUE" % (valueType)
            val = record[theAttribute]
        elif attribute == "PVVALUE":
            theAttribute = "PV%sVALUE" % (valueType)
            val = record[theAttribute]
        else:
            raise RecipeException("Unsupported attribute: %s for an output recipe data %s" % (attribute, record['RECIPEDATAKEY']))
    
    elif recipeDataType == OUTPUT_RAMP:
        SQL = "select RECIPEDATAKEY, TAG, VALUETYPE, OUTPUTTYPE, DOWNLOAD, DOWNLOADSTATUS, ERRORCODE, ERRORTEXT, TIMING, RECIPEDATATYPE, "\
            "MAXTIMING, ACTUALTIMING, ACTUALDATETIME, OUTPUTFLOATVALUE, OUTPUTINTEGERVALUE, OUTPUTSTRINGVALUE, OUTPUTBOOLEANVALUE, "\
            "TARGETFLOATVALUE, TARGETINTEGERVALUE, TARGETSTRINGVALUE, TARGETBOOLEANVALUE, "\
            "PVFLOATVALUE, PVINTEGERVALUE, PVSTRINGVALUE, PVBOOLEANVALUE, "\
            "PVMONITORACTIVE, PVMONITORSTATUS, WRITECONFIRM, WRITECONFIRMED, RAMPTIMEMINUTES, UPDATEFREQUENCYSECONDS "\
            "from SfcRecipeDataOutputRampView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueType = string.upper(record["VALUETYPE"])
        
        if attribute in ["TAG","VALUETYPE","OUTPUTTYPE","DOWNLOAD","DOWNLOADSTATUS","ERRORCODE","ERRORTEXT","TIMING","MAXTIMING",\
                         "ACTUALTIMING","ACTUALDATETIME","PVMONITORACTIVE","PVMONITORSTATUS","WRITECONFIRM","WRITECONFIRMED", \
                         "RAMPTIMEMINUTES", "UPDATEFREQUENCYSECONDS"]:
            val = record[attribute]
        elif attribute == "OUTPUTVALUE":
            theAttribute = "OUTPUT%sVALUE" % (valueType)
            val = record[theAttribute]
        elif attribute == "TARGETVALUE":
            theAttribute = "TARGET%sVALUE" % (valueType)
            val = record[theAttribute]
        elif attribute == "PVVALUE":
            theAttribute = "PV%sVALUE" % (valueType)
            val = record[theAttribute]
        else:
            raise RecipeException("Unsupported attribute: %s for an output ramp recipe data %s" % (attribute, record['RECIPEDATAKEY']))
    
    elif recipeDataType == ARRAY:
        if attribute == "VALUE":
            if arrayIndex == None:
                val = []
                SQL = "select VALUETYPE, ARRAYINDEX, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE "\
                    " from SfcRecipeDataArrayView A, SfcRecipeDataArrayElementView E where A.RecipeDataId = E.RecipeDataId "\
                    " and E.RecipeDataId = %d order by ARRAYINDEX" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
                for record in pds:
                    valueType = record['VALUETYPE']
                    aVal = record["%sVALUE" % string.upper(valueType)]
                    val.append(aVal)
                logger.tracef("Fetched the whole array: %s", str(val))
            else:
                '''
                If the array index is a string then it must be a keyed array, translate the string to an integer 
                '''
                if isText(arrayIndex):
                    SQL = "select indexKeyId from SfcRecipeDataArray where recipeDataId = %d" % (recipeDataId)
                    keyId = system.db.runScalarQuery(SQL, db)
                    arrayIndex = getIndexForKey(keyId, arrayIndex, db)
                    
                SQL = "select VALUETYPE, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE "\
                    " from SfcRecipeDataArrayView A, SfcRecipeDataArrayElementView E where A.RecipeDataId = E.RecipeDataId "\
                    " and E.RecipeDataId = %d and ArrayIndex = %d" % (recipeDataId, arrayIndex)
                pds = system.db.runQuery(SQL, db)
                record = pds[0]
                valueType = record['VALUETYPE']
                val = record["%sVALUE" % string.upper(valueType)]
                logger.tracef("Fetched the value: %s", str(val))
        else:
            raise RecipeException("Unsupported attribute: %s for array recipe data" % (attribute))
    
    elif recipeDataType == MATRIX:
        if attribute == "VALUE":
            if rowIndex == None:
                val = []
                SQL = "select VALUETYPE, RowIndex, ColumnIndex, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE "\
                    " from SfcRecipeDataMatrixView A, SfcRecipeDataMatrixElementView E where A.RecipeDataId = E.RecipeDataId "\
                    " and E.RecipeDataId = %d order by RowIndex, ColumnIndex" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
                lastRow = -1
                rowList = None
                for record in pds:
                    valueType = record['VALUETYPE']
                    rowIndex = record["RowIndex"]
                    columnIndex = record["ColumnIndex"]
                    aVal = record["%sVALUE" % string.upper(valueType)]
                    if rowIndex != lastRow:
                        if rowList != None:
                            val.append(rowList)
                        rowList = []
                    rowList.append(aVal)
                    lastRow = rowIndex
                val.append(rowList)
                logger.tracef("Fetched the whole array: %s", str(val))
            else:
                if isText(rowIndex):
                    SQL = "select rowIndexKeyId from SfcRecipeDataMatrix where recipeDataId = %d" % (recipeDataId)
                    keyId = system.db.runScalarQuery(SQL, db)
                    rowIndex = getIndexForKey(keyId, rowIndex, db)
                if isText(columnIndex):
                    SQL = "select columnIndexKeyId from SfcRecipeDataMatrix where recipeDataId = %d" % (recipeDataId)
                    keyId = system.db.runScalarQuery(SQL, db)
                    columnIndex = getIndexForKey(keyId, columnIndex, db)
                
                SQL = "select VALUETYPE, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE "\
                    " from SfcRecipeDataMatrixView A, SfcRecipeDataMatrixElementView E where A.RecipeDataId = E.RecipeDataId "\
                    " and E.RecipeDataId = %d and RowIndex = %s and ColumnIndex = %s" % (recipeDataId, str(rowIndex), str(columnIndex))
                
                print SQL
                pds = system.db.runQuery(SQL, db)
                if len(pds) == 0:
                    print "Error: No rows returned!"
                    
                record = pds[0]
                valueType = record['VALUETYPE']
                val = record["%sVALUE" % string.upper(valueType)]
                logger.tracef("Fetched the value: %s", str(val))

        else:
            raise RecipeException("Unsupported attribute: %s for matrix recipe data" % (attribute))
    
    else:
        raise RecipeException("Unsupported recipe data type: %s" % (recipeDataType))
    
    return val

def getIndexForKey(keyId, keyValue, db):
    SQL = "Select keyIndex "\
        "from SfcRecipeDataKeyView "\
        "where keyId = %d "\
        " and keyValue = '%s'" % (keyId, keyValue)
    keyIndex = system.db.runScalarQuery(SQL, db)
    return keyIndex 

def getKeyedIndex(keyName, keyValue, db):
    ''' Very similar to the one above but this uses the keyName rather than the Id '''
    SQL = "Select keyIndex "\
        "from SfcRecipeDataKeyView "\
        "where keyName = '%s' "\
        " and keyValue = '%s'" % (keyName, keyValue)
    keyIndex = system.db.runScalarQuery(SQL, db)
    return keyIndex 


def fetchRecipeDataRecord(stepName, stepId, folderId, key, db):
    logger.tracef("Fetching %s from %s", key, stepId)
    
    if folderId == None:
        SQL = "select RECIPEDATAID, STEPUUID, RECIPEDATAKEY, RECIPEDATATYPE, LABEL, DESCRIPTION, ADVICE, UNITS "\
            " from SfcRecipeDataView where stepId = %d and RecipeDataKey = '%s' and RecipeDataFolderId is NULL" % (stepId, key)
    else:
        SQL = "select RECIPEDATAID, STEPUUID, RECIPEDATAKEY, RECIPEDATATYPE, LABEL, DESCRIPTION, ADVICE, UNITS "\
            " from SfcRecipeDataView where stepId = %d and RecipeDataKey = '%s' and RecipeDataFolderId = %s" % (stepId, key, str(folderId))

    pds = system.db.runQuery(SQL, db)
    if len(pds) == 0:
        logger.errorf("Error: the key <%s> was not found for step <%s>", key, stepName)
        raise RecipeException("Missing recipe data - Key <%s> was not found for step <%s>" % (key, stepName))
    
    if len(pds) > 1:
        logger.errorf("Error: multiple records were found for key <%s> for step <%s>", key, stepName)
        raise RecipeException("Multiple records were found for key <%s> for step <%s>" % (key, stepName))
    
    record = pds[0]
    recipeDataId = record["RECIPEDATAID"]
    recipeDataType = record["RECIPEDATATYPE"]
    logger.tracef("...the recipe data type is: %s for id: %d", recipeDataType, recipeDataId)
    
    return fetchRecipeDataRecordFromRecipeDataId(recipeDataId, recipeDataType, db)

def fetchRecipeDataRecordsInFolder(stepId, folderId, db):
    logger.tracef("Fetching records from %s - %s", stepId, folderId)
    
    if folderId:     
        SQL = "select RECIPEDATAID, STEPUUID, RECIPEDATAKEY, RECIPEDATATYPE, LABEL, DESCRIPTION, ADVICE, UNITS "\
            " from SfcRecipeDataView where stepId = %s and RecipeDataFolderId = %s" % (stepId, folderId)
    else:
        SQL = "select RECIPEDATAID, STEPUUID, RECIPEDATAKEY, RECIPEDATATYPE, LABEL, DESCRIPTION, ADVICE, UNITS "\
            " from SfcRecipeDataView where stepId = %s and RecipeDataFolderId is NULL" % stepId
    pds = system.db.runQuery(SQL, db)
    
    return pds

def fetchRecipeDataRecordFromRecipeDataId(recipeDataId, recipeDataType, db):
    # These attributes are common to all recipe data classes
    if recipeDataType == SIMPLE_VALUE:
        SQL = "select RECIPEDATAID, DESCRIPTION, ADVICE, LABEL, UNITS, VALUETYPEID, VALUETYPE, RECIPEDATATYPE, VALUEID, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE "\
            "from SfcRecipeDataSimpleValueView where RecipeDataId = %s" % (recipeDataId)
    
    elif recipeDataType == TIMER:
        SQL = "select RECIPEDATAID, DESCRIPTION, ADVICE, LABEL, UNITS, RECIPEDATATYPE, STARTTIME, STOPTIME, TIMERSTATE, CUMULATIVEMINUTES "\
            "from SfcRecipeDataTimerView where RecipeDataId = %s" % (recipeDataId)
        
    elif recipeDataType == INPUT:
        SQL = "select RECIPEDATAID, DESCRIPTION, ADVICE, LABEL, UNITS, TAG, VALUETYPE, VALUETYPEID, ERRORCODE, ERRORTEXT, RECIPEDATATYPE, PVMONITORACTIVE, PVMONITORSTATUS, "\
            "TARGETVALUEID, TARGETFLOATVALUE, TARGETINTEGERVALUE, TARGETSTRINGVALUE, TARGETBOOLEANVALUE, "\
            "PVVALUEID, PVFLOATVALUE, PVINTEGERVALUE, PVSTRINGVALUE, PVBOOLEANVALUE "\
            "from SfcRecipeDataInputView where RecipeDataId = %s" % (recipeDataId)
    
    elif recipeDataType == OUTPUT:
        SQL = "select RECIPEDATAID, DESCRIPTION, ADVICE, LABEL, UNITS, TAG, VALUETYPE, VALUETYPEID, OUTPUTTYPE, OUTPUTTYPEID, DOWNLOAD, DOWNLOADSTATUS, ERRORCODE, ERRORTEXT, TIMING, RECIPEDATATYPE, "\
            "MAXTIMING, ACTUALTIMING, ACTUALDATETIME, PVMONITORACTIVE, PVMONITORSTATUS, SETPOINTSTATUS,  WRITECONFIRM, WRITECONFIRMED, "\
            "OUTPUTVALUEID, OUTPUTFLOATVALUE, OUTPUTINTEGERVALUE, OUTPUTSTRINGVALUE, OUTPUTBOOLEANVALUE, "\
            "TARGETVALUEID, TARGETFLOATVALUE, TARGETINTEGERVALUE, TARGETSTRINGVALUE, TARGETBOOLEANVALUE, "\
            "PVVALUEID, PVFLOATVALUE, PVINTEGERVALUE, PVSTRINGVALUE, PVBOOLEANVALUE "\
            "from SfcRecipeDataOutputView where RecipeDataId = %s" % (recipeDataId)
    
    elif recipeDataType == OUTPUT_RAMP:
        SQL = "select RECIPEDATAID, DESCRIPTION, ADVICE, LABEL, UNITS, TAG, VALUETYPE, VALUETYPEID, OUTPUTTYPE, OUTPUTTYPEID, DOWNLOAD, DOWNLOADSTATUS, ERRORCODE, ERRORTEXT, TIMING, RECIPEDATATYPE, "\
            "MAXTIMING, ACTUALTIMING, ACTUALDATETIME, PVMONITORACTIVE, PVMONITORSTATUS, SETPOINTSTATUS,  WRITECONFIRM, WRITECONFIRMED, "\
            "OUTPUTVALUEID, OUTPUTFLOATVALUE, OUTPUTINTEGERVALUE, OUTPUTSTRINGVALUE, OUTPUTBOOLEANVALUE, "\
            "TARGETVALUEID, TARGETFLOATVALUE, TARGETINTEGERVALUE, TARGETSTRINGVALUE, TARGETBOOLEANVALUE, "\
            "PVVALUEID, PVFLOATVALUE, PVINTEGERVALUE, PVSTRINGVALUE, PVBOOLEANVALUE "\
            "from SfcRecipeDataOutputRampView where RecipeDataId = %s" % (recipeDataId)
    
    elif recipeDataType == ARRAY:
        # This is pretty close, but it needs ValueId in the view- CJL
        valueType = 'Unset'
        valueIds = []
        val = []
        indices = []
        SQL = "select A.RECIPEDATAID, E.VALUEID, VALUETYPE, ARRAYINDEX, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE "\
            " from SfcRecipeDataArrayView A, SfcRecipeDataArrayElementView E where A.RecipeDataId = E.RecipeDataId "\
            " and E.RecipeDataId = %d order by ARRAYINDEX" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        for record in pds:
            valueType = record["VALUETYPE"]
            aVal = record["%sVALUE" % string.upper(valueType)]
            val.append(aVal)
            bVal = record["ARRAYINDEX"]
            indices.append(bVal)
            cVal = record["VALUEID"]
            valueIds.append(cVal)

        ''' This assumes all entries in the array are of the same type (should be a safe assumption)  ''' 
        ''' I'm not sure if arrayindex is always used and/or unique, so I'm not using key:value pairs '''
        val = {'RECIPEDATATYPE':ARRAY, 'VALUETYPE':valueType, 'INDEXVALUES':indices ,'ARRAYVALUES':val,'VALUEIDS':valueIds}
        
        logger.tracef("Fetched the whole array: %s", str(val))
        return val
    
    else:
        raise RecipeException("Unsupported recipe data type: %s" % (recipeDataType))

    pds = system.db.runQuery(SQL, db)
    if len(pds) <> 1:
        raise RecipeException("%d rows were returned when exactly 1 was expected" % (len(pds)))

    record = pds[0]
    return record

def setRecipeData(stepName, stepId, folder, key, attribute, val, db, units=""):
    logger.tracef("Setting recipe data value for step with stepId: %d, folder: %s, key: %s, attribute: %s, value: %s", stepId, folder, key, attribute, str(val))
    
    # Separate the key from the array index if there is an array index
    attribute, arrayIndex, rowIndex, columnIndex = checkForArrayOrMatrixReference(attribute)
    recipeDataId, recipeDataType, targetUnits = getRecipeDataId(stepName, stepId, folder + "." + key, db)
    
    setRecipeDataFromId(recipeDataId, recipeDataType, attribute, val, units, targetUnits, arrayIndex, rowIndex, columnIndex, db)

def setRecipeDataFromId(recipeDataId, recipeDataType, attribute, val, units, targetUnits, arrayIndex, rowIndex, columnIndex, db):
    attribute = string.upper(attribute).strip()
    
    if isFloat(val) and units <> "":
        oldVal = val
        val = convert(units, targetUnits, float(val), db)
        logger.tracef("...converted %s-%s to %s-%s...", str(oldVal), units, str(val), targetUnits)
    
    if str(val) in ["None", "NONE", "none", "NO-VALUE"]:
        val = None
    
    logger.tracef("...the recipe data type is: %s for id: %d", recipeDataType, recipeDataId)
    
    if attribute in ['DESCRIPTION', 'UNITS', 'LABEL', 'ADVICE']:
        SQL = "update SfcRecipeData set %s = '%s' where recipeDataId = %s" % (attribute, val, recipeDataId)
        rows = system.db.runUpdateQuery(SQL, db)
        logger.tracef('...updated %d records in SfcRecipeData', rows)
    
    elif recipeDataType == SIMPLE_VALUE:
        if attribute in ["VALUETYPE"]:
            valueTypeId = fetchValueTypeId(val, db)
            SQL = "update SfcRecipeDataSimpleValue set ValueTypeId=%d where recipeDataId = %s" % (valueTypeId, recipeDataId)
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef('...updated %d simple value recipe data records', rows)
        else:
            SQL = "select * from SfcRecipeDataSimpleValueView where RecipeDataId = %s" % (recipeDataId)
            pds = system.db.runQuery(SQL, db)
            record = pds[0]
            valueType = record['ValueType']
            valueId = record['ValueId']
            if valueType == "String":
                if val == None:
                    SQL = "update SfcRecipeDataValue set %sValue = NULL where ValueId = %s" % (valueType, valueId)
                else:
                    SQL = "update SfcRecipeDataValue set %sValue = '%s' where ValueId = %s" % (valueType, val, valueId)
            elif valueType == "Boolean":
                if val == None:
                    SQL = "update SfcRecipeDataValue set %sValue = NULL where ValueId = %s" % (valueType, valueId)
                else:
                    bitVal = toBit(val)
                    SQL = "update SfcRecipeDataValue set %sValue = %s where ValueId = %s" % (valueType, str(bitVal), valueId)
            else:
                if val == None:
                    SQL = "update SfcRecipeDataValue set %sValue = NULL where ValueId = %s" % (valueType, valueId)
                else:
                    SQL = "update SfcRecipeDataValue set %sValue = %s where ValueId = %s" % (valueType, str(val), valueId)
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef('...updated %d simple value recipe data records', rows)
            
    elif recipeDataType == RECIPE:
        SQL = "update SfcRecipeDataRecipe set %s = '%s' where recipeDataId = %s" % (attribute, val, recipeDataId)
        rows = system.db.runUpdateQuery(SQL, db)
        logger.tracef('...updated %d simple value recipe data records', rows)
    
    elif recipeDataType == SQC:
        SQL = "update SfcRecipeDataSQC set %s = %s where recipeDataId = %s" % (attribute, str(val), recipeDataId)
        rows = system.db.runUpdateQuery(SQL, db)
        logger.tracef('...updated %d SQC recipe data records', rows)
        
    elif recipeDataType == INPUT:
        if attribute in ['TAG', 'ERRORCODE', 'ERRORTEXT', 'PVMONITORSTATUS']:
            SQL = "update SfcRecipeDataInput set %s = '%s' where recipeDataId = %s" % (attribute, str(val), recipeDataId)
        elif attribute in ['PVMONITORACTIVE']:
            bitVal = toBit(val)
            SQL = "update SfcRecipeDataInput set %s = %s where recipeDataId = %s" % (attribute, bitVal, recipeDataId)
        elif attribute in ['PVVALUE','TARGETVALUE']:
            attrName="%sID" % (attribute)
            SQL = "select ValueType, %s from SfcRecipeDataInputView where RecipeDataId = %s" % (attrName, recipeDataId)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise RecipeException("Unable to find the value type for Input recipe data")
            record = pds[0]
            valueType = record["ValueType"]
            valueId = record[attrName]
            theAttribute = "%sValue" % (valueType)
    
            if valueType == 'String':
                SQL = "update SfcRecipeDataValue set %s = '%s' where valueId = %s" % (theAttribute, val, valueId)
            else:
                SQL = "update SfcRecipeDataValue set %s = %s where valueId = %s" % (theAttribute, val, valueId)
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef('...updated %d value records', rows)

        elif attribute in ['VALUETYPE']:
            valueTypeId = fetchValueTypeId(val, db)
            SQL = "update SfcRecipeDataInput set ValueTypeId = %i where recipeDataId = %s" % (valueTypeId, recipeDataId)
        else:
            txt = "Unsupported attribute <%s> for input recipe data" % (attribute)
            logger.errorf(txt)
            raise RecipeException(txt)
            
        rows = system.db.runUpdateQuery(SQL, db)
        logger.tracef('...updated %d input recipe data records', rows)

    
    elif recipeDataType in [OUTPUT, OUTPUT_RAMP]:
        if string.upper(str(val)) == "NULL" and attribute not in ['OUTPUTVALUE','PVVALUE','TARGETVALUE']:
            SQL = "update SfcRecipeDataOutput set %s = NULL where recipeDataId = %s" % (attribute, recipeDataId)
        elif attribute in ['TAG', 'DOWNLOADSTATUS', 'ERRORCODE', 'ERRORTEXT', 'PVMONITORSTATUS', 'ACTUALDATETIME', 'SETPOINTSTATUS']:
            SQL = "update SfcRecipeDataOutput set %s = '%s' where recipeDataId = %s" % (attribute, str(val), recipeDataId)
        elif attribute in ['DOWNLOAD', 'PVMONITORACTIVE', 'WRITECONFIRM', 'WRITECONFIRMED']:
            bitVal = toBit(val)
            SQL = "update SfcRecipeDataOutput set %s = %s where recipeDataId = %s" % (attribute, bitVal, recipeDataId)
        elif attribute in ['TIMING', 'MAXTIMING', 'ACTUALTIMING']:
            SQL = "update SfcRecipeDataOutput set %s = %s where recipeDataId = %s" % (attribute, val, recipeDataId)
        elif attribute in ['OUTPUTVALUE','PVVALUE','TARGETVALUE']:
            attrName="%sID" % (attribute)
            
            if recipeDataType == OUTPUT_RAMP:
                tableName = "SfcRecipeDataOutputRampView"
            else:
                tableName = "SfcRecipeDataOutputView"
                
            SQL = "select ValueType, %s from %s where RecipeDataId = %s" % (attrName, tableName, recipeDataId)
            logger.tracef(SQL)
            pds = system.db.runQuery(SQL, db)
            if len(pds) <> 1:
                raise RecipeException("Unable to find the value type for Output recipe data")
            record = pds[0]
            valueType = record["ValueType"]
            valueId = record[attrName]
            theAttribute = "%sValue" % (valueType)
    
            if valueType == 'String':
                if val == None:
                    SQL = "update SfcRecipeDataValue set %s = NULL where valueId = %s" % (theAttribute, valueId)
                else:
                    SQL = "update SfcRecipeDataValue set %s = '%s' where valueId = %s" % (theAttribute, val, valueId)
            else:
                if val == None:
                    SQL = "update SfcRecipeDataValue set %s = NULL where valueId = %s" % (theAttribute, valueId)
                else:
                    SQL = "update SfcRecipeDataValue set %s = %s where valueId = %s" % (theAttribute, val, valueId)

            logger.tracef(SQL)
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef('...updated %d value records', rows)

        elif attribute in ['VALUETYPE']:
            valueTypeId = fetchValueTypeId(val, db)
            SQL = "update SfcRecipeDataOutput set ValueTypeId = %i where recipeDataId = %s" % (valueTypeId, recipeDataId)
        elif attribute in ['OUTPUTTYPE']:
            outputTypeId = fetchOutputTypeId(val, db)
            SQL = "update SfcRecipeDataOutput set OutputTypeId = %i where recipeDataId = %s" % (outputTypeId, recipeDataId)
        elif recipeDataType == OUTPUT_RAMP and attribute in ['RAMPTIMEMINUTES', 'UPDATEFREQUENCYSECONDS']: 
            SQL = "update SfcRecipeDataOutputRamp set %s = %s where recipeDataId = %s" % (attribute, str(val), recipeDataId)
        else: 
            logger.errorf("Unsupported attribute <%s> for output recipe data", attribute)
            raise RecipeException("Unsupported attribute <%s> for %s recipe data" % (attribute, recipeDataType))
            
        rows = system.db.runUpdateQuery(SQL, db)
        logger.tracef('...updated %d output recipe data records', rows)

    
    elif recipeDataType == TIMER:
        if attribute in ['COMMAND']:
            now = system.date.now()
            now = formatDateTime(now, format='MM/dd/yy HH:mm:ss')
            val=val.upper()
            if val == PAUSE_TIMER.upper():
                logger.tracef("Pausing timer...")
                SQL = "select * from sfcRecipeDataTimerView where RecipeDataId = %d" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
                record = pds[0]
                cumulativeMinutes = record["CumulativeMinutes"]
                startTime = record['StartTime']
                timerState = record['TimerState']
                
                if timerState == "running":
                    cumulativeMinutes = cumulativeMinutes + system.date.secondsBetween(startTime, system.date.now()) / 60.0
                    SQL = "update SfcRecipeDataTimer set StopTime = '%s', TimerState = '%s', CumulativeMinutes = %f where RecipeDataId = %d" % (now, TIMER_PAUSED, cumulativeMinutes, recipeDataId)
                else:
                    logger.warnf("The timer cannot be paused because it is not running, the timer state is: %s", timerState)
                    return
                
            elif val == START_TIMER.upper():
                logger.tracef("Starting timer...")
                SQL = "update SfcRecipeDataTimer set StartTime = '%s', StopTime = NULL, TimerState = '%s', CumulativeMinutes = 0.0 where RecipeDataId = %d" % (now, TIMER_RUNNING, recipeDataId)
            
            elif val == RESUME_TIMER.upper():
                logger.tracef("Resuming timer...")
                SQL = "select * from sfcRecipeDataTimerView where RecipeDataId = %d" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
                record = pds[0]
                startTime = record['StartTime']
                
                SQL = "update SfcRecipeDataTimer set StartTime = '%s', StopTime = NULL, TimerState = '%s' where RecipeDataId = %d" % (now, TIMER_RUNNING, recipeDataId)
            
            elif val == CLEAR_TIMER.upper():
                logger.tracef("Clearing timer...")
                SQL = "update SfcRecipeDataTimer set StartTime = NULL, StopTime = NULL, TimerState = '%s', CumulativeMinutes = 0.0 where RecipeDataId = %d" % (TIMER_CLEARED, recipeDataId)
            
            elif val == STOP_TIMER.upper():
                logger.tracef("Stopping timer...")
                SQL = "select * from sfcRecipeDataTimerView where RecipeDataId = %d" % (recipeDataId)
                pds = system.db.runQuery(SQL, db)
                record = pds[0]
                cumulativeMinutes = record["CumulativeMinutes"]
                startTime = record['StartTime']
                timerState = record['TimerState']
                if timerState == "running":
                    cumulativeMinutes = cumulativeMinutes + system.date.secondsBetween(startTime, system.date.now()) / 60.0
                    SQL = "update SfcRecipeDataTimer set StopTime = '%s', TimerState = '%s', CumulativeMinutes = %f where RecipeDataId = %d" % (now, TIMER_PAUSED, cumulativeMinutes, recipeDataId)
                else:
                    SQL = "update SfcRecipeDataTimer set StopTime = '%s', TimerState = '%s' where RecipeDataId = %d" % (now, TIMER_PAUSED, recipeDataId)
  
            else:
                raise RecipeException("Unsupported timer command <%s> for timer recipe data" % (val))

            logger.tracef(SQL)
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef('...updated %d timer records', rows)
        
#            SQL = "update SfcRecipeDataTimer set StartTime = '%s' where recipeDataId = %s" % (val, recipeDataId)
#            rows = system.db.runUpdateQuery(SQL, db)
#            logger.tracef('...updated %d timer recipe data records', rows)
        else:
            logger.errorf("Unsupported attribute <%s> for timer recipe data", attribute)
            raise RecipeException("Unsupported attribute <%s> for timer recipe data" % (attribute))
        
    
    elif recipeDataType == ARRAY:
        # Get the value type from the SfcRecipeDataArray table.
        SQL = "select * from SfcRecipeDataArrayView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueType = record['ValueType']
        recipeDataId = record['RecipeDataId']
            
        if arrayIndex == None:
            logger.tracef("Setting an entire array...")
            
            logger.tracef("...deleting all existing elements...")
            SQL = "delete from SfcRecipeDataArrayElement where RecipeDataId = %s" % (str(recipeDataId))
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef("...deleted %d  rows...", rows)
            
            idx = 0
            for el in val:
                logger.tracef("idx: %d => %s", idx, str(el))
                    
                if valueType == 'String':
                    SQL = "insert into SfcRecipeDataValue (RecipeDataId, StringValue) values (%d, '%s')" % (recipeDataId, el)
                else:
                    valueColumnName = valueType + "Value"
                    if valueType == "Boolean":
                        el = toBit(el)
                    SQL = "insert into SfcRecipeDataValue (RecipeDataId, %s) values (%d, %s)" % (valueColumnName, recipeDataId, str(el))
                logger.tracef(SQL)
                valueId=system.db.runUpdateQuery(SQL, getKey=True, database=db)
                
                SQL = "insert into SfcRecipeDataArrayElement (RecipeDataId, ArrayIndex, ValueId) values (%d, %d, %d)" % (recipeDataId, idx, valueId)
                system.db.runUpdateQuery(SQL, db)

                idx = idx + 1
            
        else:
            '''
            If the arrayIndex is a text string, then assume that this is a keyed array and translate the string index to an integer
            '''
            if isText(arrayIndex):
                SQL = "select indexKeyId from SfcRecipeDataArray where recipeDataId = %d" % (recipeDataId)
                keyId = system.db.runScalarQuery(SQL, db)
                arrayIndex = getIndexForKey(keyId, arrayIndex, db)
            
            # Now fetch the Value Id of the specific element of the array
            SQL = "select valueId from SfcRecipeDataArrayElement where RecipeDataId = %s and ArrayIndex = %s" % (str(recipeDataId), str(arrayIndex))
            valueId = system.db.runScalarQuery(SQL, db)
            
            if valueType == "String":
                SQL = "update SfcRecipeDataValue set %sValue = '%s' where ValueId = %d" % (valueType, val, valueId)
            else:
                SQL = "update SfcRecipeDataValue set %sValue = %s where ValueId = %d" % (valueType, val, valueId)
    
            rows = system.db.runUpdateQuery(SQL, db)
            logger.tracef('...updated %d array value recipe data records', rows)
       
    elif recipeDataType == MATRIX:
        if rowIndex == None or columnIndex == None:
            raise RecipeException("Matrix Recipe data must specify a row and a column index")
        
        # Dereference array keys
        if isText(rowIndex):
            SQL = "select rowIndexKeyId from SfcRecipeDataMatrix where recipeDataId = %d" % (recipeDataId)
            keyId = system.db.runScalarQuery(SQL, db)
            rowIndex = getIndexForKey(keyId, rowIndex, db)
        if isText(columnIndex):
            SQL = "select columnIndexKeyId from SfcRecipeDataMatrix where recipeDataId = %d" % (recipeDataId)
            keyId = system.db.runScalarQuery(SQL, db)
            columnIndex = getIndexForKey(keyId, columnIndex, db)
        
        # Get the value type from the SfcRecipeDataArray table.
        SQL = "select * from SfcRecipeDataMatrixView where RecipeDataId = %s" % (recipeDataId)
        pds = system.db.runQuery(SQL, db)
        record = pds[0]
        valueType = record['ValueType']
        
        # Now fetch the Value Id of the specific element of the array
        SQL = "select valueId from SfcRecipeDataMatrixElement where RecipeDataId = %s and RowIndex = %s and columnIndex = %s" % (str(recipeDataId), str(rowIndex), str(columnIndex))
        valueId = system.db.runScalarQuery(SQL, db)
        
        if valueType == "String":
            SQL = "update SfcRecipeDataValue set %sValue = '%s' where ValueId = %d" % (valueType, val, valueId)
        else:
            SQL = "update SfcRecipeDataValue set %sValue = %s where ValueId = %d" % (valueType, val, valueId)

        rows = system.db.runUpdateQuery(SQL, db)
        logger.tracef('...updated %d matrix value recipe data records', rows)
        
    else:
        logger.errorf("Unsupported recipe data type: %s", record["RecipeDataType"])
        raise RecipeException("Unsupported recipe data type: %s" % (recipeDataType))


# Separate the key from the array index if there is an array index
def checkForArrayOrMatrixReference(attribute):
    arrayIndex = None
    rowIndex = None
    columnIndex = None
    
    if string.count(attribute, "[") == 1:
        logger.tracef("There is an array index...")
        arrayIndex = attribute[attribute.find("[")+1:len(attribute)-1]
        logger.tracef("...it is: %s", arrayIndex)
        
        if not(isText(arrayIndex)):
            arrayIndex = int(arrayIndex)
            
        attribute = attribute[:attribute.find("[")]
        
    elif string.count(attribute, "[") == 2:
        logger.tracef("There is an matrix reference...")
        
        rowIndex = attribute[attribute.find("[")+1:attribute.find("]")]
        if not(isText(rowIndex)):
            arrayIndex = int(rowIndex)
        
        columnIndex = attribute[attribute.rfind("[")+1:attribute.rfind("]")]
        if not(isText(columnIndex)):
            arrayIndex = int(columnIndex)
        
        attribute = attribute[:attribute.find("[")]
    
    return attribute, arrayIndex, rowIndex, columnIndex
        
def fetchOutputTypeId(val, db):
    SQL = "select OutputTypeId from SfcRecipeDataOutputType where OutputType = '%s'" % (val)
    outputTypeId = system.db.runScalarQuery(SQL, db)
    return outputTypeId

def fetchValueTypeId(val, db):
    SQL = "select ValueTypeId from SfcValueType where ValueType = '%s'" % (val)
    valueTypeId = system.db.runScalarQuery(SQL, db)
    return valueTypeId

def fetchRecipeDataTypeId(val, db):
    SQL = "select RecipeDataTypeId from SfcRecipeDataType where RecipeDataType = '%s'" % (val)
    recipeDataTypeId = system.db.runScalarQuery(SQL, db)
    return recipeDataTypeId

def getChartUUID(chartProperties):
    return chartProperties.get("chartUUID", "-1")

def getStepUUID(stepProperties):
    return stepProperties.get("id","-1")

def getStepName(stepProperties):
    return stepProperties.get(STEP_NAME, "")

def getStepIdFromUUID(stepUUID, db):
    SQL = "select stepId from SfcStep where stepUUID = '%s'" % (stepUUID) 
    stepId = system.db.runScalarQuery(SQL, db)
    return stepId

# This handles a simple "key.attribute" notation, but does not handle folder reference or arrays
def splitKey(keyAndAttribute):
    tokens = keyAndAttribute.split(".")
    if len(tokens) < 2:
        txt = "Recipe access failed while attempting to split the key and attribute because there were not enough tokens: <%s> " % (keyAndAttribute)
        raise RecipeException(txt)
    folder = ".".join(tokens[:len(tokens) - 2])
    key = string.upper(tokens[len(tokens) - 2])
    attribute = string.upper(tokens[len(tokens) - 1])
    logger.tracef("Folder: <%s>, Key: <%s>, Attribute: <%s>", folder, key, attribute)
    return folder, key, attribute

def fetchStepTypeIdFromFactoryId(factoryId, tx):
    SQL = "select StepTypeId from SfcStepType where FactoryId = '%s'" % (factoryId)
    stepTypeId = system.db.runScalarQuery(SQL, tx=tx)
    
    if stepTypeId < 0:
        print "Step %s does not exist, inserting it..." % (factoryId)
        SQL = "Insert into SfcStepType (StepType, FactoryId) values ('%s','%s')" % (factoryId, factoryId)
        stepTypeId = system.db.runUpdateQuery(SQL, tx=tx, getKey=True)
        print "...inserted into SfcSteptype with id: ", stepTypeId

    return stepTypeId

def fetchChartIdFromChartPath(chartPath, tx):
    chartPath = string.replace(chartPath,'\\','/')
    SQL = "select chartId from SfcChart where ChartPath = '%s'" % (chartPath)
    chartId = system.db.runScalarQuery(SQL, tx=tx)
    return chartId

def fetchChartPathFromChartId(chartId, tx=""):
    SQL = "select chartPath from SfcChart where ChartId = %d" % (chartId)
    chartPath = system.db.runScalarQuery(SQL, tx=tx)
    return chartPath

def getStepId(chartPath, stepName, db):
    logger.tracef("%s.getStepId with %s - %s (%s)", __name__, chartPath, stepName, db)
    chartPath = string.replace(chartPath,'\\','/')
    SQL = "select stepId from SfcStepView where ChartPath = '%s' and stepName = '%s' " % (chartPath, stepName)
    logger.tracef("SQL: %s", SQL)
    stepId = system.db.runScalarQuery(SQL, db)
    logger.tracef("...found step id: %s", str(stepId))
    return stepId

def fetchStepIdFromChartIdAndStepName(chartId, stepName, tx):
    SQL = "select stepId from SfcStep where ChartId = %s and stepName = '%s' " % (chartId, stepName)
    stepId = system.db.runScalarQuery(SQL, tx=tx)
    return stepId

def fetchStepIdFromUUID(stepUUID, tx):
    SQL = "select stepId from SfcStep where StepUUID = '%s'" % (stepUUID)
    stepId = system.db.runScalarQuery(SQL, tx=tx)
    return stepId

# Return a value only for a specific key, otherwise raise an exception.
def s88GetRecipeDataDS(stepId, recipeDataType, db):
    logger.tracef("%s.s88GetRecipeDataDS(): %s", __name__, recipeDataType)
    
    SQL = "select RecipeDataFolderId, RecipeDataKey, ParentRecipeDataFolderId, ParentFolderName "\
            "from SfcRecipeDataFolderView  "\
            "where stepId = %d "\
            "order by RecipeDataFolderId " % (stepId) 
    folderPDS = system.db.runQuery(SQL, db)
    logger.tracef("...fetched %d folders", len(folderPDS))

    if recipeDataType == SIMPLE_VALUE:
        SQL = "select RecipeDataKey, Units, ValueType, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE, folderId "\
            "from SfcRecipeDataSimpleValueView  "\
            "where stepId = %d "\
            "order by RecipeDataKey " % (stepId) 
            
        pds = system.db.runQuery(SQL, db)
        logger.tracef("...fetched %d rows pf %s", len(pds), recipeDataType)
        
        ''' Need to collapse the 4 value fields (I wish I knew how to do this in SQL) '''
        data = []
        header = ["KEY", "UNITS", "DATATYPE", "VALUE"]
        for record in pds:
            key = record["RecipeDataKey"]
            valueType = record["ValueType"]
            val = str(record[string.upper(valueType) + "VALUE"])
            folderId = record["folderId"]
            if folderId != None:
                folderPath = getFolderPath(folderId,folderPDS)
                key = folderPath + "/" + key
    
            data.append([key, record["Units"], valueType, val])
        ds = system.dataset.toDataSet(header, data)
    
    elif recipeDataType == OUTPUT:
        SQL = "select RecipeDataKey, Units, Tag, OutputType, Download, WriteConfirm, Timing, MaxTiming, ValueType, OUTPUTFLOATVALUE, OUTPUTINTEGERVALUE, OUTPUTSTRINGVALUE, OUTPUTBOOLEANVALUE, folderId "\
            "from SfcRecipeDataOutputView  "\
            "where stepId = %d "\
            "order by RecipeDataKey " % (stepId) 
            
        pds = system.db.runQuery(SQL, db)
        logger.tracef("...fetched %d rows of %s", len(pds), recipeDataType)
        
        ''' Need to collapse the 4 value fields (I wish I knew how to do this in SQL) '''
        data = []
        header = ["KEY", "UNITS", "TAG", "OUTPUTTYPE", "DOWNLOAD", "WRITECONFIRM", "TIMING", "MAXTIMING", "DATATYPE", "OUTPUTVALUE"]
        for record in pds:
            key = record["RecipeDataKey"]
            valueType = record["ValueType"]
            outputValue = str(record["OUTPUT" + string.upper(valueType) + "VALUE"])
            folderId = record["folderId"]
            if folderId != None:
                folderPath = getFolderPath(folderId,folderPDS)
                key = folderPath + "/" + key
                
            data.append([ key, record["Units"], record["Tag"],  record["OutputType"], record["Download"], record["WriteConfirm"], record["Timing"], record["MaxTiming"], valueType, outputValue])
        ds = system.dataset.toDataSet(header, data)
        
    elif recipeDataType == OUTPUT_RAMP:
        SQL = "select RecipeDataKey, Units, Tag, OutputType, Download, WriteConfirm, Timing, MaxTiming, RampTimeMinutes, UpdateFrequencySeconds, ValueType, OUTPUTFLOATVALUE, OUTPUTINTEGERVALUE, OUTPUTSTRINGVALUE, OUTPUTBOOLEANVALUE, folderId "\
            "from SfcRecipeDataOutputRampView  "\
            "where stepId = %d "\
            "order by RecipeDataKey " % (stepId) 
            
        pds = system.db.runQuery(SQL, db)
        logger.tracef("...fetched %d rows of %s", len(pds), recipeDataType)
        
        ''' Need to collapse the 4 value fields (I wish I knew how to do this in SQL) '''
        data = []
        header = ["KEY", "UNITS", "TAG", "OUTPUTTYPE", "DOWNLOAD", "WRITECONFIRM", "TIMING", "MAXTIMING", "RAMPTIME", "UPDATEFREQUENCY", "DATATYPE", "OUTPUTVALUE"]
        for record in pds:
            key = record["RecipeDataKey"]
            valueType = record["ValueType"]
            outputValue = str(record["OUTPUT" + string.upper(valueType) + "VALUE"])
            folderId = record["folderId"]
            if folderId != None:
                folderPath = getFolderPath(folderId,folderPDS)
                key = folderPath + "/" + key
                
            data.append([ key, record["Units"], record["Tag"],  record["OutputType"], record["Download"], record["WriteConfirm"], record["Timing"], record["MaxTiming"], record["RampTimeMinutes"], record["UpdateFrequencySeconds"], valueType, outputValue])
        ds = system.dataset.toDataSet(header, data)
        
    elif recipeDataType == INPUT:
        SQL = "select RecipeDataKey, Units, Tag, ValueType, PVFLOATVALUE, PVINTEGERVALUE, PVSTRINGVALUE, PVBOOLEANVALUE, TARGETFLOATVALUE, TARGETINTEGERVALUE, TARGETSTRINGVALUE, TARGETBOOLEANVALUE, folderId "\
            "from SfcRecipeDataInputView  "\
            "where stepId = %d "\
            "order by RecipeDataKey " % (stepId) 
            
        pds = system.db.runQuery(SQL, db)
        logger.tracef("...fetched %d rows of %s", len(pds), recipeDataType)
        
        ''' Need to collapse the 4 value fields (I wish I knew how to do this in SQL) '''
        data = []
        header = ["KEY", "UNITS", "TAG", "DATATYPE", "PVVALUE", "TARGETVALUE"]
        for record in pds:
            key = record["RecipeDataKey"]
            valueType = record["ValueType"]
            pvValue = str(record["PV" + string.upper(valueType) + "VALUE"])
            targetValue = str(record["TARGET" + string.upper(valueType) + "VALUE"])
            
            folderId = record["folderId"]
            if folderId != None:
                folderPath = getFolderPath(folderId,folderPDS)
                key = folderPath + "/" + key
                
            data.append([ key, record["Units"], record["Tag"], valueType, pvValue, targetValue])
        ds = system.dataset.toDataSet(header, data)
        
        
    elif recipeDataType == ARRAY:
        SQL = "select RecipeDataId, RecipeDataKey, Units, ValueType, KeyName, folderId "\
            "from SfcRecipeDataArrayView  "\
            "where stepId = %d "\
            "order by RecipeDataKey " % (stepId) 
            
        pds = system.db.runQuery(SQL, db)
        logger.tracef("...fetched %d rows of %s", len(pds), recipeDataType)
        
        ''' Need to collapse the 4 value fields (I wish I knew how to do this in SQL) '''
        data = []
        header = ["KEY", "UNITS", "DATATYPE", "VALS" ]

        for record in pds:
            recipeDataId = record["RecipeDataId"]
            key = record["RecipeDataKey"]
            valueType = record["ValueType"]
            
            folderId = record["folderId"]
            if folderId != None:
                folderPath = getFolderPath(folderId,folderPDS)
                key = folderPath + "/" + key
            
            data = []
            SQL = "select  ArrayIndex, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE "\
                "from SfcRecipeDataArrayElementView "\
                "where RecipeDataId = %d "\
                "order by ArrayIndex" % (recipeDataId)
            valuePDS = system.db.runQuery(SQL, db)

            vals = []
            for valueRecord in valuePDS:
                val = str(valueRecord[string.upper(valueType) + "VALUE"])
                vals.append(val)
                
            valString = "(" + ",".join(vals) + ")"
            data.append([ key, record["Units"], valueType, valString])
    
        ds = system.dataset.toDataSet(header, data)
        
    elif recipeDataType == MATRIX:
        SQL = "select RecipeDataId, RecipeDataKey, Units, ValueType, RowIndexKeyName, ColumnIndexKeyName, folderId "\
            "from SfcRecipeDataMatrixView  "\
            "where stepId = %d "\
            "order by RecipeDataKey " % (stepId) 
            
        pds = system.db.runQuery(SQL, db)
        logger.tracef("...fetched %d rows of %s", len(pds), recipeDataType)
        
        ''' Need to collapse the 4 value fields (I wish I knew how to do this in SQL) '''
        data = []
        header = ["KEY", "UNITS", "DATATYPE", "VALS" ]

        for record in pds:
            recipeDataId = record["RecipeDataId"]
            key = record["RecipeDataKey"]
            valueType = record["ValueType"]
            
            folderId = record["folderId"]
            if folderId != None:
                folderPath = getFolderPath(folderId,folderPDS)
                key = folderPath + "/" + key
            
            data = []
            SQL = "select  RowIndex, ColumnIndex, FLOATVALUE, INTEGERVALUE, STRINGVALUE, BOOLEANVALUE "\
                "from SfcRecipeDataMatrixElementView "\
                "where RecipeDataId = %d "\
                "order by RowIndex, ColumnIndex" % (recipeDataId)
            valuePDS = system.db.runQuery(SQL, db)

            vals = []
            for valueRecord in valuePDS:
                val = str(valueRecord[string.upper(valueType) + "VALUE"])
                vals.append(val)
                
            valString = "(" + ",".join(vals) + ")"
            data.append([ key, record["Units"], valueType, valString])
    
        ds = system.dataset.toDataSet(header, data)
        
    elif recipeDataType == RECIPE:
        SQL = "select RecipeDataKey, Units, PresentationOrder, StoreTag, CompareTag, ModeAttribute, ModeValue, ChangeLevel, RecommendedValue, LowLimit, HighLimit, folderId "\
            "from SfcRecipeDataRecipeView  "\
            "where stepId = %d "\
            "order by PresentationOrder " % (stepId) 
            
        pds = system.db.runQuery(SQL, db)
        logger.tracef("...fetched %d rows of %s", len(pds), recipeDataType)
        
        data = []
        header = ["Key", "Units", "PresentationOrder", "StoreTag", "CompareTag", "ModeAttribute", "ModeValue", "ChangeLevel", "RecommendedValue", "LowLimit", "HighLimit"]
        for record in pds:
            key = record["RecipeDataKey"]
            
            folderId = record["folderId"]
            if folderId != None:
                folderPath = getFolderPath(folderId,folderPDS)
                key = folderPath + "/" + key
                
            data.append([ key, record["Units"], record["PresentationOrder"], record["StoreTag"], record["CompareTag"], record["ModeAttribute"], record["ModeValue"], record["ChangeLevel"], record["RecommendedValue"], record["LowLimit"], record["HighLimit"] ])
        ds = system.dataset.toDataSet(header, data)
        
    elif recipeDataType == SQC:
        SQL = "select RecipeDataKey, Units, LowLimit, TargetValue, HighLimit, folderId "\
            "from SfcRecipeDataSQCView  "\
            "where stepId = %d "\
            "order by RecipeDataKey " % (stepId) 
            
        pds = system.db.runQuery(SQL, db)
        logger.tracef("...fetched %d rows of %s", len(pds), recipeDataType)
        
        data = []
        header = ["Key", "Units", "LowLimit", "TargetValue", "HighLimit"]
        for record in pds:
            key = record["RecipeDataKey"]
            
            folderId = record["folderId"]
            if folderId != None:
                folderPath = getFolderPath(folderId,folderPDS)
                key = folderPath + "/" + key
                
            data.append([ key, record["Units"], record["LowLimit"], record["TargetValue"], record["HighLimit"] ])
        ds = system.dataset.toDataSet(header, data)
        
    elif recipeDataType == TIMER:
        SQL = "select RecipeDataKey, StartTime, StopTime, TimerState, CumulativeMinutes, folderId "\
            "from SfcRecipeDataTimerView  "\
            "where stepId = %d "\
            "order by RecipeDataKey " % (stepId) 
            
        pds = system.db.runQuery(SQL, db)
        logger.tracef("...fetched %d rows of %s", len(pds), recipeDataType)
        
        data = []
        header = ["Key", "StartTime", "StopTime", "TimerState", "CumulativeMinutes"]
        for record in pds:
            key = record["RecipeDataKey"]
            
            folderId = record["folderId"]
            if folderId != None:
                folderPath = getFolderPath(folderId,folderPDS)
                key = folderPath + "/" + key
                
            data.append([ key, record["StartTime"], record["StopTime"], record["TimerState"], record["CumulativeMinutes"] ])
        ds = system.dataset.toDataSet(header, data)
    
    else:
        raise RecipeException("Unsupported recipe data type: %s" % (recipeDataType))
    
    return ds

def getFolderPath(folderId, pds):
    '''
    Given a folder Id, which presumably came from a recipe data record and is not None, use the supplied dataset
    of folder records to recusively put together the path of arbitrary depth.
    '''    
    #---------------------------------------------------------------
    def getFolderInfo(folderId, pds):
        for record in pds:
            if record["RecipeDataFolderId"] == folderId:
                return record["RecipeDataKey"], record["ParentRecipeDataFolderId"]
        return None, None
    #---------------------------------------------------------------
    
    logger.tracef("Looking for the folder path for: %s", str(folderId))
    key, parentId = getFolderInfo(folderId, pds)
    keys = []
    keys.append(key)
    
    while parentId != None:
        key, parentId = getFolderInfo(parentId, pds)
        if key != None:
            keys.insert(0, key)

    path = "/".join(keys)
    logger.tracef("The path is: %s", str(path))
    return path
        
        
def copyFolderValues(fromStepId, fromFolder, toStepId, toFolder, recursive, category, db):
    logger.tracef("Copying recipe data from %d-%s to %d-%s", fromStepId, fromFolder, toStepId, toFolder)
    
    # ------------------------------------------------------------------------------------
    def getKeys(pds):
        keys = []
        for record in pds:
            keys.append(record["RECIPEDATAKEY"])
        return keys
    # ------------------------------------------------------------------------------------

    fromFolderId = getFolderForStep(fromStepId, fromFolder, db)    
    toFolderId = getFolderForStep(toStepId, toFolder, db)
    logger.tracef("  From folder: %s", fromFolderId)
    logger.tracef("    To Folder: %s", toFolderId)
    
    ''' Get all of the FROM keys ''' 
    fromPds = fetchRecipeDataRecordsInFolder(fromStepId, fromFolderId, db)
    logger.tracef("Found %d recipe datums in %s (the source)", len(fromPds), fromFolder)
    fromKeys = getKeys(fromPds)
    
    ''' Get all of the TO keys '''
    toPds = fetchRecipeDataRecordsInFolder(toStepId, toFolderId, db)
    logger.tracef("Found %d recipe datums in %s (the destination)", len(toPds), toFolder)
    toKeys = getKeys(toPds)
    
    i = 0
    for fromKey in fromKeys:
        if fromKey in toKeys:
            logger.tracef("  Copying %s...", fromKey)
            fromRecord = fromPds[i]
            fromRecord = fetchRecipeDataRecordFromRecipeDataId(fromRecord["RECIPEDATAID"], fromRecord["RECIPEDATATYPE"], db)
            
            for toRecord in toPds:
                if toRecord["RECIPEDATAKEY"] == fromKey:
                    toRecord = fetchRecipeDataRecordFromRecipeDataId(toRecord["RECIPEDATAID"], toRecord["RECIPEDATATYPE"], db)
                    copySourceToTargetValues(fromRecord, toRecord, db)
            
        else:
            logger.tracef("Skipping %s because it is not in the destination", fromKey)
        i = i + 1
#    keys = s88GetKeysForNamedBlock(fromChartPath, fromStepName, "%", db)

def copyRecipeDatum(sourceUUID, sourceKey, targetUUID, targetKey, db):
    # 1) Ensure that the types of recipe data are the same.
    # 2) Call a copy method that knows which attributes of recipe data need to be copied
    
    tokens = sourceKey.split(".")
    if len(tokens) > 1:
        sourceFolder = sourceKey[:sourceKey.rfind(".")]
        sourceKey = sourceKey[sourceKey.rfind(".")+1:]
        sourceFolderId = getFolderForStep(sourceUUID, sourceFolder, db)
        logger.tracef("Source: <%s>.<%s>", sourceFolder, sourceKey)
    else:
        sourceFolderId = None
        
    tokens = targetKey.split(".")
    if len(tokens) > 1:
        targetFolder = targetKey[:targetKey.rfind(".")]
        targetKey = targetKey[targetKey.rfind(".")+1:]
        targetFolderId = getFolderForStep(targetUUID, targetFolder, db)
        logger.tracef("Target: <%s>.<%s>", targetFolder, targetKey)
    else:
        targetFolderId = None

    chartPath, stepName = getStepInfoFromUUID(sourceUUID, db)
    sourceRecord = fetchRecipeDataRecord(stepName, sourceUUID, sourceFolderId, sourceKey, db)
    
    chartPath, stepName = getStepInfoFromUUID(targetUUID, db)
    targetRecord = fetchRecipeDataRecord(stepName, targetUUID, targetFolderId, targetKey, db)
    
    copySourceToTarget(sourceRecord, targetRecord, db)
    
def copySourceToTargetValues(sourceRecord, targetRecord, db):
    '''
    This is used when copying the value of a recipe item only.  It allows copying from simple value to other recipe types
    '''
    
    def updateSfcRecipeDataValue(valueId, floatValue, integerValue, stringValue, booleanValue, db):
        SQL = "update SfcRecipeDataValue set FloatValue = ?, IntegerValue = ?, StringValue = ?, BooleanValue = ? where ValueId = ?"
        rows = system.db.runPrepUpdate(SQL, [floatValue, integerValue, stringValue, booleanValue, valueId], database=db)
        logger.tracef("      Updated %d rows in SfcRecipeDataValue", rows)
        
    def updateSfcRecipeDataValueWithType(valueId, value, valueType, db):
        SQL = "update SfcRecipeDataValue set %sValue = ? where ValueId = ?" % valueType
        rows = system.db.runPrepUpdate(SQL, [value, valueId], database=db)
        logger.tracef("      Updated %d rows in SfcRecipeDataValue", rows)
        
    ''' --------------------------------------------- End of Private Methods ------------------------------------------------- '''
    sourceRecipeDataType = sourceRecord["RECIPEDATATYPE"]
    targetRecipeDataType = targetRecord["RECIPEDATATYPE"]
        
#     if sourceRecipeDataType != targetRecipeDataType:
#         logger.errorf("EREIAM JH - Copying input recipe :%s: to :%s:" % (sourceRecipeDataType, targetRecipeDataType))

    if targetRecipeDataType == SIMPLE_VALUE:
        valueId = targetRecord["VALUEID"]
    elif targetRecipeDataType == OUTPUT:
        valueId = targetRecord["OUTPUTVALUEID"]
    elif targetRecipeDataType == OUTPUT_RAMP:
        valueId = targetRecord["OUTPUTVALUEID"]
    elif targetRecipeDataType == ARRAY:
        logger.tracef('Copying target array recipe!')
    elif targetRecipeDataType == INPUT:
        logger.errorf('Copying target input recipe data HAS NOT BEEN IMPLEMENTED...')
    elif targetRecipeDataType == TIMER:
        logger.errorf('Copying target timer recipe data HAS NOT BEEN IMPLEMENTED...')
    else:
        logger.errorf("Unsupported target recipe data type: %s", targetRecipeDataType)
        raise RecipeException("Unsupported target recipe data type: %s" % targetRecipeDataType)
        return
    
    if sourceRecipeDataType == SIMPLE_VALUE:
        logger.tracef('    Copying simple recipe data...')
        updateSfcRecipeDataValue(valueId, sourceRecord["FLOATVALUE"], sourceRecord["INTEGERVALUE"], sourceRecord["STRINGVALUE"], sourceRecord["BOOLEANVALUE"], db)
    elif sourceRecipeDataType == INPUT:
        logger.errorf("    Copying input recipe data HAS NOT BEEN IMPLEMENTED...")
    elif sourceRecipeDataType == OUTPUT:
        logger.tracef('    Copying output recipe data...')
        updateSfcRecipeDataValue(valueId, sourceRecord["OUTPUTFLOATVALUE"], sourceRecord["OUTPUTINTEGERVALUE"], sourceRecord["OUTPUTSTRINGVALUE"], sourceRecord["OUTPUTBOOLEANVALUE"], db)
    elif sourceRecipeDataType == OUTPUT_RAMP:
        logger.tracef('    Copying output recipe data...')
        updateSfcRecipeDataValue(valueId, sourceRecord["OUTPUTFLOATVALUE"], sourceRecord["OUTPUTINTEGERVALUE"], sourceRecord["OUTPUTSTRINGVALUE"], sourceRecord["OUTPUTBOOLEANVALUE"], db)
    elif sourceRecipeDataType == TIMER:
        logger.errorf("    Copying timer recipe data HAS NOT BEEN IMPLEMENTED...")
    elif sourceRecipeDataType == ARRAY:
        ''' Nested for loop is inefficient, but maybe OK since this is seldom used and arrays are generally small '''
        logger.tracef('    Copying an array one element at a time...')
        sourceValueType = sourceRecord["VALUETYPE"]
        sourceIndices = sourceRecord["INDEXVALUES"]
        sourceValues = sourceRecord["ARRAYVALUES"]
        sourceValueIds = sourceRecord["VALUEIDS"]
        targetValueType = targetRecord["VALUETYPE"]
        targetIndices = targetRecord["INDEXVALUES"]
        targetValues = targetRecord["ARRAYVALUES"]
        targetValueIds = targetRecord["VALUEIDS"]
        
        ''' Disassemble arrays and copy values '''
        for i in range(len(sourceValues)):
            for j in range(len(targetValues)):
                if sourceIndices[i] == targetIndices[j]:
                    updateSfcRecipeDataValueWithType(targetValueIds[j], sourceValues[i], sourceValueType, db)
            
    elif sourceRecipeDataType == MATRIX:
        logger.errorf('Copying matrix recipe data HAS NOT BEEN IMPLEMENTED...')
    else:
        logger.errorf("Unsupported recipe data type: %s", sourceRecipeDataType)
        raise RecipeException("Unsupported recipe data type: %s" % (sourceRecipeDataType))

def copySourceToTarget(sourceRecord, targetRecord, db):
    '''
    This is used when copying a single datum to another or when copying all of the datums in one folder to another folder
    '''
    
    ''' --------------------------------------------- Private Methods ------------------------------------------------- '''
    def updateSfcRecipeData(recipeDataId, label, description, advice, units, db):
        SQL = "update SfcRecipeData set Label = ?, Description = ?, Advice = ?, Units = ? where RecipeDataId = ?"
        rows = system.db.runPrepUpdate(SQL, [label, description, advice, units,recipeDataId], database=db)
        logger.tracef("Updated %d rows in SfcRecipeData", rows)
    
    def updateSfcRecipeDataValue(valueId, floatValue, integerValue, stringValue, booleanValue, db):
        SQL = "update SfcRecipeDataValue set FloatValue = ?, IntegerValue = ?, StringValue = ?, BooleanValue = ? where ValueId = ?"
        rows = system.db.runPrepUpdate(SQL, [floatValue, integerValue, stringValue, booleanValue, valueId], database=db)
        logger.tracef("Updated %d rows in SfcRecipeDataValue", rows)
        
    def updateSfcRecipeDataSimpleValue(recipeDataId, valueTypeId, db):
        SQL = "update SfcRecipeDataSimpleValue set ValueTypeId = ? where RecipeDataId = ?"
        rows = system.db.runPrepUpdate(SQL, [valueTypeId, recipeDataId], database=db)
        logger.tracef("Updated %d rows in SfcRecipeDataSimpleValue", rows)
    
    def updateSfcRecipeDataInput(recipeDataId, valueTypeId, tag, db):
        SQL = "update SfcRecipeDataInput set ValueTypeId = ?, tag = ? where RecipeDataId = ?"
        rows = system.db.runPrepUpdate(SQL, [valueTypeId, tag, recipeDataId], database=db)
        logger.tracef("Updated %d rows in updateSfcRecipeDataInput", rows)
    
    def updateSfcRecipeDataOutput(recipeDataId, valueTypeId, outputTypeId, tag, download, timing, maxTiming, writeConfirm, db):
        SQL = "update SfcRecipeDataOutput set ValueTypeId = ?, outputTypeId = ?, tag = ?, download = ?, timing = ?, maxTiming = ?, writeConfirm = ? where RecipeDataId = ?"
        rows = system.db.runPrepUpdate(SQL, [valueTypeId, outputTypeId, tag, download, timing, maxTiming, writeConfirm, recipeDataId], database=db)
        logger.tracef("Updated %d rows in updateSfcRecipeDataOutput", rows)
    
    ''' --------------------------------------------- End of Private Methods ------------------------------------------------- '''
    recipeDataType = sourceRecord["RECIPEDATATYPE"]
    targetRecipeDataType = targetRecord["RECIPEDATATYPE"]
        
        
    if recipeDataType != targetRecipeDataType:
        errorText = "Unable to copy recipe data of dissimilar type!  %s != %s" % (recipeDataType, targetRecipeDataType)
        raise RecipeException(errorText)
        return
    
    if recipeDataType == SIMPLE_VALUE:
        logger.tracef('Copying simple recipe data...')
        updateSfcRecipeData(targetRecord["RECIPEDATAID"], sourceRecord["LABEL"], sourceRecord["DESCRIPTION"], sourceRecord["ADVICE"], sourceRecord["UNITS"], db)
        updateSfcRecipeDataSimpleValue(targetRecord["RECIPEDATAID"], sourceRecord["VALUETYPEID"], db)
        updateSfcRecipeDataValue(targetRecord["VALUEID"], sourceRecord["FLOATVALUE"], sourceRecord["INTEGERVALUE"], sourceRecord["STRINGVALUE"], sourceRecord["BOOLEANVALUE"], db)
        
    elif recipeDataType == INPUT:
        logger.tracef('Copying input recipe data...')
        updateSfcRecipeData(targetRecord["RECIPEDATAID"], sourceRecord["LABEL"], sourceRecord["DESCRIPTION"], sourceRecord["ADVICE"], sourceRecord["UNITS"], db)
        updateSfcRecipeDataInput(targetRecord["RECIPEDATAID"], sourceRecord["VALUETYPEID"], sourceRecord["TAG"], db)
        updateSfcRecipeDataValue(targetRecord["TARGETVALUEID"], sourceRecord["TARGETFLOATVALUE"], sourceRecord["TARGETINTEGERVALUE"], sourceRecord["TARGETSTRINGVALUE"], sourceRecord["TARGETBOOLEANVALUE"], db)
        updateSfcRecipeDataValue(targetRecord["PVVALUEID"], sourceRecord["PVFLOATVALUE"], sourceRecord["PVINTEGERVALUE"], sourceRecord["PVSTRINGVALUE"], sourceRecord["PVBOOLEANVALUE"], db)
    
    elif recipeDataType == OUTPUT:
        logger.tracef('Copying output recipe data...')
        updateSfcRecipeData(targetRecord["RECIPEDATAID"], sourceRecord["LABEL"], sourceRecord["DESCRIPTION"], sourceRecord["ADVICE"], sourceRecord["UNITS"], db)
        updateSfcRecipeDataOutput(targetRecord["RECIPEDATAID"], sourceRecord["VALUETYPEID"], sourceRecord["OUTPUTTYPEID"], sourceRecord["TAG"], 
                                  sourceRecord["DOWNLOAD"], sourceRecord["TIMING"], sourceRecord["MAXTIMING"], sourceRecord["WRITECONFIRM"], db)
        updateSfcRecipeDataValue(targetRecord["OUTPUTVALUEID"], sourceRecord["OUTPUTFLOATVALUE"], sourceRecord["OUTPUTINTEGERVALUE"], sourceRecord["OUTPUTSTRINGVALUE"], sourceRecord["OUTPUTBOOLEANVALUE"], db)
        updateSfcRecipeDataValue(targetRecord["TARGETVALUEID"], sourceRecord["TARGETFLOATVALUE"], sourceRecord["TARGETINTEGERVALUE"], sourceRecord["TARGETSTRINGVALUE"], sourceRecord["TARGETBOOLEANVALUE"], db)
        updateSfcRecipeDataValue(targetRecord["PVVALUEID"], sourceRecord["PVFLOATVALUE"], sourceRecord["PVINTEGERVALUE"], sourceRecord["PVSTRINGVALUE"], sourceRecord["PVBOOLEANVALUE"], db)
    
    elif recipeDataType == TIMER:
        logger.errorf("Copying timer recipe data HAS NOT BEEN IMPLEMENTED...")
    
    elif recipeDataType == ARRAY:
        logger.errorf('Copying array recipe data HAS NOT BEEN IMPLEMENTED...')
       
    elif recipeDataType == MATRIX:
        logger.errorf('Copying matrix recipe data HAS NOT BEEN IMPLEMENTED...')

    elif recipeDataType == OUTPUT_RAMP:
        logger.errorf('Copying output ramp recipe data HAS NOT BEEN IMPLEMENTED...')
        
    else:
        logger.errorf("Unsupported recipe data type: %s", recipeDataType)
        raise ValueError, "Unsupported recipe data type: %s" % (recipeDataType)
    
def getDatabaseName(chartProperties):
    '''Get the name of the database this chart is using, we conveniently put this into the top properties '''
    topProperties = getTopLevelProperties(chartProperties)
    return topProperties[DATABASE]

def getIsolationMode(chartProperties):
    '''Returns true if the chart is running in isolation mode'''
    from ils.sfc.common.constants import ISOLATION_MODE
    topProperties = getTopLevelProperties(chartProperties)
    return topProperties[ISOLATION_MODE]

def getTopLevelProperties(chartProperties):
#    print "------------------"
#    print "In getTopLevelProperties..."
    from ils.sfc.common.constants import PARENT
#    print "Checking: ", chartProperties.get(PARENT, None)
#    print "   level: ", chartProperties.get("s88Level", None)
    while chartProperties.get(PARENT, None) != None:
#        print chartProperties
        chartProperties = chartProperties.get(PARENT)
#        print "Checking: ", chartProperties.get(PARENT, None)
#        print "   level: ", chartProperties.get("s88Level", None)
#    print " --- returning --- "
    return chartProperties

def readTag(chartScope, tagPath):
    '''  Read a tag substituting provider according to isolation mode.  '''
    provider = getProviderName(chartScope)
    fullPath = substituteProvider(tagPath, provider)
    qv = readTag(fullPath)
    return qv.value

def getProviderName(chartProperties):
    '''Get the name of the tag provider for this chart, taking isolation mode into account'''
    topProperties = getTopLevelProperties(chartProperties)
    provider = topProperties[TAG_PROVIDER]
    return provider

def getProvider(chartProperties):
    '''Like getProviderName(), but puts brackets around the provider name'''
    topProperties = getTopLevelProperties(chartProperties)
    provider = topProperties[TAG_PROVIDER]
    return "[" + provider + "]"

def getSuperiorAncestors(chartPath, db):
    ancestors=[]
    SQL = "select ChartPath from SfcHierarchyView where ChildChartPath = '%s'" % (chartPath)
    pds = system.db.runQuery(SQL, db)
    for record in pds:
        print record["ChartPath"]
        ancestors.append(record["ChartPath"])
    return ancestors

def getFirstEnclosingChart(chartPath, db):
    ''' "First" is a bit arbitrary, since a chart can be called by more than one parent.
    This is used when mocking up the call hierarchy when debugging from designer. '''
    SQL = "select chartPath, stepName, stepUUID, stepType, factoryId from SfcHierarchyView where ChildChartPath = '%s'" % (chartPath)    
    pds = system.db.runQuery(SQL, db)
    if len(pds) == 0:
        return None, None, None, None, None
    
    record = pds[0]
    chartPath = record["chartPath"]
    stepName = record["stepName"]
    stepUUID = record["stepUUID"]
    stepType = record["stepType"]
    factoryId = record["factoryId"]
    return chartPath, stepName, stepUUID, stepType, factoryId

def walkUpHierarchyLookingForStepType(chartPath, ancestorType, db):
    
    def fetchParents(chartPaths, ancestorType):
        terminals = []
        parents = []
        
        for cp in chartPaths:
            SQL = "select ChartPath, StepType from SfcHierarchyView where ChildChartPath = '%s'" % (cp)
            pds = system.db.runQuery(SQL, database=db)
            for record in pds:
                print record["ChartPath"], " - ", record["StepType"]
                if ancestorType == GLOBAL_SCOPE and record["StepType"] == "Unit Procedure":
                    terminals.append(record["ChartPath"])
                elif ancestorType == OPERATION_SCOPE and record["StepType"] == "Operation":
                    terminals.append(record["ChartPath"])
                else:
                    parents.append(record["ChartPath"])
        print "   returning %s - %s" % (str(terminals), str(parents)) 
        return terminals, parents
    
    ancestors=[]
    chartPaths = [chartPath]
    
    i = 0
    while len(chartPaths) > 0 and i < 5:
        print "(%d) Looking for <%s> ancestors for %s" % (i, ancestorType, str(chartPaths))
        terminals, chartPaths = fetchParents(chartPaths, ancestorType)
        ancestors = ancestors + terminals
        i = i + 1
        
    print "The <%s> ancestors of %s are %s" % (ancestorType, chartPath, str(ancestors))
    
    return ancestors

class RecipeException(Exception):
    def __init__(self, txt):
        self.txt = txt
    def __str__(self):
        return "S88 Recipe Error: " + self.txt