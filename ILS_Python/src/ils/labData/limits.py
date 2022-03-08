'''
Created on Mar 31, 2015

@author: Pete
'''
import system, string

from ils.log import getLogger
log =getLogger(__name__)
sqllog =getLogger(__name__ + ".sql")

'''
This is a memory resident dictionary of limit dictionaries that survives from scan to scan.  
The key is the valueId.  It gets validated each cycle with new limits from the LtValueView database table.
The main purpose of the cache is so optimize writing out to the Lab Limit UDTs, rather than just blast out to 
the UDTs every cycle, I only write if a new or changed limit is detected.
5/31/21 - Redesigned to handle multiple limits record.  Previously the last record found won.
'''
limits={}

def checkValidityLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit):
    inhibitValidity = system.tag.read("[%s]Configuration/LabData/inhibitValidity" % (tagProvider)).value
    if inhibitValidity:
        log.tracef("Skipping validity checking for %s - validity checking is inhibited.", valueName)
        return True, None, None

    log.tracef("Checking Validity limits for %s - %s...", valueName, str(limit))
    validityLimit = limit.get("VALIDITY", None)
    log.tracef("...the validity limit is %s...", str(validityLimit))
    
    if validityLimit == None:
        log.tracef(" -- no validity limit found --")
        return True, None, None
    
    upperLimit=validityLimit.get("UpperValidityLimit", None)
    lowerLimit=validityLimit.get("LowerValidityLimit", None)
    log.tracef("   ...the validity limits are %s < %s < %s", str(lowerLimit), str(rawValue), str(upperLimit))
    
    if upperLimit != None and rawValue > upperLimit:
        log.tracef("%s **Failed** the validity upper limit check...", valueName)        
        return False, upperLimit, lowerLimit
    elif lowerLimit != None and rawValue < lowerLimit:
        log.tracef("%s **Failed** the validity lower limit check...", valueName)
        return False, upperLimit, lowerLimit
    else:
        log.tracef("%s passed the validity limit check...", valueName)
    
    return True, upperLimit, lowerLimit

def checkSQCLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit):
    inhibitValidity = system.tag.read("[%s]Configuration/LabData/inhibitValidity" % (tagProvider)).value
    if inhibitValidity:
        log.tracef("Skipping validity checking for %s - validity checking is inhibited.", valueName)
        return True, None, None
    
    log.tracef("Checking SQC - Validity limits for %s - %s", valueName, str(limit))
    sqcLimit = limit.get("SQC", None)
    log.tracef("...the SQC limit is %s...", str(sqcLimit))
    
    if sqcLimit == None:
        log.tracef(" -- no validity limit found --")
        return True, None, None
    
    upperLimit=sqcLimit.get("UpperValidityLimit", None)
    lowerLimit=sqcLimit.get("LowerValidityLimit", None)
    log.tracef("   ...the validity limits are %s < %s < %s", str(lowerLimit), str(rawValue), str(upperLimit))
    
    if upperLimit != None and rawValue > upperLimit:
        log.tracef("%s **Failed** the SQC - validity upper limit check...", valueName)        
        return False, upperLimit, lowerLimit
    elif lowerLimit != None and rawValue < lowerLimit:
        log.tracef("%s **Failed** the SQC - validity lower limit check...", valueName)
        return False, upperLimit, lowerLimit
    else:
        log.tracef("%s passed the SQC - validity limit check...", valueName)

    return True, upperLimit, lowerLimit

# Release limit checking is exactly like validity limit checking, the difference is what happens if they fail.  It appears that
# the main difference is that the notification screen gives the operator the chance to start a UIR.
# One concern is that the G2 code for release limits absolutely uses the limits in the validity limit slot - it was unclear if 
# they just put the release limits into the validity limits so they could use some common processing logic or what - but I am going 
# to use the limits in the release limits 
def checkReleaseLimit(valueId, valueName, rawValue, sampleTime, database, tagProvider, limit):
    log.tracef("Checking Release limits for %s - %s...", valueName, str(limit))
    releaseLimit = limit.get("RELEASE", None)
    log.tracef("...the RELEASE limit is %s...", str(releaseLimit))
    if releaseLimit == None:
        log.tracef("%s There aren't any release limits", valueName)
        return True, None, None
    
    upperLimit=releaseLimit.get("UpperReleaseLimit", None)
    lowerLimit=releaseLimit.get("LowerReleaseLimit", None)
    log.tracef("   ...the release limits are %s < %s < %s", str(lowerLimit), str(rawValue), str(upperLimit))
    
    if upperLimit != None and rawValue > upperLimit:
        log.tracef("%s **Failed** the release upper limit check...", valueName)
        return False, upperLimit, lowerLimit
    elif lowerLimit != None and rawValue < lowerLimit:
        log.tracef("%s **Failed** the release lower limit check...", valueName)
        return False, upperLimit, lowerLimit
    else:
        log.tracef("%s passed the release limit check...", valueName)

    return True, upperLimit, lowerLimit
    

def fetchLimits(tagProvider, database):
    '''
    This fetches the currently active limits that are the Lab Data Toolkit tables regardless of where they came from.
    There are three sources: Recipe, DCS, and Constant.  If the source is Recipe then some other mechanism needs to push
    them from recipe into Lab Data.  If the source is DCS, then they are read each cycle.  If they are constant, then the value in 
    Lab Data is the master and whatever updates them is outside the scope of this logic.
    '''
    def calculateSQCLimits(record, oldLimit, tagProvider):
        '''
        When SQC limits are loaded from the recipe toolkit, the target, standard deviation and validity limits are calculated and then 
        stored in the database so no further calculations are necessary.
        '''
        limitSource=record["LimitSource"]
        
        log.tracef("Getting SQC limits from %s", limitSource)
        if limitSource=="DCS":
            upperSQCLimit, lowerSQCLimit=readSQCLimitsFromDCS(record)
            print "**** oldLimit: ", oldLimit
            
            if oldLimit == None:
                log.trace("***********    A DCS SQC limit has been added...  ******************")
                target, standardDeviation, lowerValidityLimit, upperValidityLimit = updateLabLimits(record["ValueName"], record["UnitName"], "SQC", record["LimitId"], upperSQCLimit, lowerSQCLimit, tagProvider, database)
            
            else:
                
                if oldLimit["UpperSQCLimit"] != upperSQCLimit or oldLimit["LowerSQCLimit"] != lowerSQCLimit:
                    log.trace("A DCS SQC limit has changed - recalculate the target & standard deviation")
                    target, standardDeviation, lowerValidityLimit, upperValidityLimit = updateLabLimits(record["ValueName"], record["UnitName"], "SQC", record["LimitId"], upperSQCLimit, lowerSQCLimit, tagProvider, database)

                else:
                    target=0.0
                    standardDeviation=0.0
                    lowerValidityLimit=0.0
                    upperValidityLimit=0.0

        else:
            upperValidityLimit=record["UpperValidityLimit"]
            lowerValidityLimit=record["LowerValidityLimit"]
            upperSQCLimit=record["UpperSQCLimit"]
            lowerSQCLimit=record["LowerSQCLimit"]
            target=record["Target"]
            standardDeviation=record["StandardDeviation"]
        return upperSQCLimit, lowerSQCLimit, upperValidityLimit, lowerValidityLimit, target, standardDeviation
    #----
    def getValidityLimits(record):
        limitSource=record["LimitSource"]
        
        log.tracef("Getting Validity limits from %s", limitSource)
        if limitSource=="DCS":
            upperValidityLimit, lowerValidityLimit=readSQCLimitsFromDCS(record)
        else:
            upperValidityLimit=record["UpperValidityLimit"]
            lowerValidityLimit=record["LowerValidityLimit"]
        return upperValidityLimit, lowerValidityLimit
    #----
    def getReleaseLimits(record):
        limitSource=record["LimitSource"]
        
        log.tracef("Getting Release limits from %s", limitSource)
        if limitSource=="DCS":
            upperReleaseLimit, lowerReleaseLimit=readSQCLimitsFromDCS(record)
        else:
            upperReleaseLimit=record["UpperReleaseLimit"]
            lowerReleaseLimit=record["LowerReleaseLimit"]
        return upperReleaseLimit, lowerReleaseLimit
    #-------------------------------------
    def packLimit(record, tagProvider, new=False):
        valueName=record["ValueName"]
        limitType=record["LimitType"]
        log.tracef("Packing a %s limit for %s", limitType, valueName)
        
        d={}

        if limitType == "SQC":
            upperSQCLimit, lowerSQCLimit, upperValidityLimit, lowerValidityLimit, target, standardDeviation = calculateSQCLimits(record, None, tagProvider)
            d["UpperValidityLimit"]=upperValidityLimit
            d["LowerValidityLimit"]=lowerValidityLimit
            d["UpperSQCLimit"]=upperSQCLimit
            d["LowerSQCLimit"]=lowerSQCLimit
            d["Target"]=target
            d["StandardDeviation"]=standardDeviation
        elif limitType == "Release":
            d["UpperReleaseLimit"]=record["UpperReleaseLimit"]
            d["LowerReleaseLimit"]=record["LowerReleaseLimit"]
        elif limitType == "Validity":
            upperValidityLimit, lowerValidityLimit = getValidityLimits(record)
            d["UpperValidityLimit"]=upperValidityLimit
            d["LowerValidityLimit"]=lowerValidityLimit
        else:
            log.error("Unexpected limit type while packing: <%s> for %s" % (limitType, valueName))
            
        log.trace("Packed a dictionary for %s - %s: " % (valueName, str(d)))
        return d
    
    def packNewLimit(record, tagProvider):
        valueName=record["ValueName"]
        limitType=record["LimitType"]
        log.tracef("Packing a *NEW* %s limit for %s", limitType, valueName)
        
        limitDict = packLimit(record, tagProvider)
        limitType=string.upper(limitType)
        d={
           "ValueName":record["ValueName"],
           "UnitName":record["UnitName"],
           "Post":record["Post"],
           "ValidationProcedure":record["ValidationProcedure"],
           limitType: limitDict
           }
        return d
    #-----------------------------------------------------
    # Update the limit UDT (tags) with the new limits 
    def updateLimitTags(limit, tagProvider):   
        #-------------
        def writeLimit(tagProvider, unitName, valueName, limitType, limitValue):
            if limitValue != None:
                tagName="[%s]LabData/%s/%s/%s" % (tagProvider, unitName, valueName, limitType)
                log.tracef("Writing Limit <%s> to %s", limitValue, tagName)
                result=system.tag.write(tagName, limitValue)
                if result == 0:
                    log.error("Writing new limit value of <%s> to <%s> failed" % (str(limitValue), tagName))
        #-------------
        unitName=limit.get("UnitName","")
        valueName=limit.get("ValueName", None)
        log.tracef("Updating limit tags for %s - %s", valueName, str(limit))
        for limitTypeKey in ["SQC", "VALIDITY", "RELEASE"]:
            limitType=limit.get(limitTypeKey, None)
            if limitType <> None and limitTypeKey == "SQC":
                writeLimit(tagProvider, unitName, valueName + '-SQC', "upperValidityLimit", limitType.get("UpperValidityLimit", None))
                writeLimit(tagProvider, unitName, valueName + '-SQC', "lowerValidityLimit", limitType.get("LowerValidityLimit", None))
                writeLimit(tagProvider, unitName, valueName + '-SQC', "upperSQCLimit", limitType.get("UpperSQCLimit", None))
                writeLimit(tagProvider, unitName, valueName + '-SQC', "lowerSQCLimit", limitType.get("LowerSQCLimit", None))
                writeLimit(tagProvider, unitName, valueName + '-SQC', "target", limitType.get("Target", None))
                writeLimit(tagProvider, unitName, valueName + '-SQC', "standardDeviation", limitType.get("StandardDeviation", None))
            elif limitType <> None and limitTypeKey == "RELEASE":
                writeLimit(tagProvider, unitName, valueName + '-RELEASE', "upperReleaseLimit", limitType.get("UpperReleaseLimit", None))
                writeLimit(tagProvider, unitName, valueName + '-RELEASE', "lowerReleaseLimit", limitType.get("LowerReleaseLimit", None))
            elif limitType <> None and limitTypeKey == "VALIDITY":
                writeLimit(tagProvider, unitName, valueName + '-VALIDITY', "upperValidityLimit", limitType.get("UpperValidityLimit", None))
                writeLimit(tagProvider, unitName, valueName + '-VALIDITY', "lowerValidityLimit", limitType.get("LowerValidityLimit", None))

    #-----------------------------------------------------------
    def readSQCLimitsFromDCS(record):
        valueName=record["ValueName"]
        serverName=record["InterfaceName"]
        upperItemId=record["OPCUpperItemId"]
        lowerItemId=record["OPCLowerItemId"]
        log.trace("Fetching DCS limits for %s from %s (upper: %s, lower: %s)" % (valueName, serverName, upperItemId, lowerItemId))
        vals=system.opc.readValues(serverName, [upperItemId, lowerItemId] )
        log.trace("Read SQC limit values from the DCS: %s" % (str(vals)))
                
        qv=vals[0]
        if qv.quality.isGood():
            upperSQCLimit=qv.value
        else:
            upperSQCLimit=None
                
        qv=vals[1]
        if qv.quality.isGood():
            lowerSQCLimit=qv.value
        else:
            lowerSQCLimit=None
        
        return upperSQCLimit, lowerSQCLimit
    #------------------------------------------

    log.trace("Fetching new Limits...")
    log.trace("The old limits are: %s" % (str(limits)))
    SQL = "select * from LtLimitView"
    sqlLog.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    log.trace("  ...fetched %i limits!" % (len(pds)))
    
    for record in pds:
        valueId=record["ValueId"]
        unitName=record["UnitName"]
        
        ''' Check if there is any limits already defined for this lab value ''' 
        if valueId in limits:
            oldLimit=limits[valueId]
            
            limitType=record["LimitType"]
            limitSource=record["LimitSource"]
            log.tracef("Processing a %s - %s  limit for an existing lab value: %s", limitType, limitSource, str(valueId))
            
            ''' Get the old limit details for the limit type of the new limit '''
            oldLimitDetails = oldLimit.get(limitType, None)
            if oldLimitDetails == None:
                log.tracef("Adding a new %s limit to a structure with other limits", limitType)

                ''' Found a new limit '''
                d = packNewLimit(record, tagProvider)
                oldLimit[string.upper(limitType)] = d
                updateLimitTags(oldLimit, tagProvider)

            else:
                log.tracef("**** there IS an existing limit: %s ****", str(oldLimit))
                if limitType == "SQC":
                    
                    if limitSource == "DCS":
                        upperSQCLimit, lowerSQCLimit=readSQCLimitsFromDCS(record)
                        target, standardDeviation, lowerValidityLimit, upperValidityLimit = updateLabLimits(record["ValueName"], record["UnitName"], "SQC", record["LimitId"], upperSQCLimit, lowerSQCLimit, tagProvider, database)
                    else:
                        upperSQCLimit = record["UpperSQCLimit"]
                        lowerSQCLimit = record["LowerSQCLimit"]
                        upperValidityLimit = record["UpperValidityLimit"]
                        lowerValidityLimit = record["LowerValidityLimit"]
                        target = record["Target"]
                        standardDeviation = record["StandardDeviation"] 
    
                    ''' compare the old to the new '''
                    if oldLimitDetails.get("UpperSQCLimit", None) != upperSQCLimit or \
                        oldLimitDetails.get("LowerSQCLimit", None) != lowerSQCLimit or \
                        oldLimitDetails.get("UpperValidityLimit", None) != upperValidityLimit or \
                        oldLimitDetails.get("LowerValidityLimit", None) != lowerValidityLimit:
                        
                        log.trace("An existing SQC limit has changed")
                        log.trace("Old: %s" % (str(oldLimitDetails)))
    
                        oldLimitDetails["UpperValidityLimit"]=upperValidityLimit
                        oldLimitDetails["LowerValidityLimit"]=lowerValidityLimit
                        oldLimitDetails["UpperSQCLimit"]=upperSQCLimit
                        oldLimitDetails["LowerSQCLimit"]=lowerSQCLimit
                        oldLimitDetails["Target"]=target
                        oldLimitDetails["StandardDeviation"]=standardDeviation
                        updateLimitTags(oldLimit, tagProvider)
                        oldLimit["SQC"] = oldLimitDetails
                        limits[valueId]=oldLimit
                    else:
                        log.trace("No change to an existing SQC limit")

                        
                elif string.upper(limitType) == "VALIDITY":
                    upperValidityLimit, lowerValidityLimit = getValidityLimits(record)
                    if "VALIDITY" in oldLimit:
                        oldValidityLimit = oldLimit["VALIDITY"]
    
                        if oldValidityLimit.get("UpperValidityLimit", None) != upperValidityLimit or \
                            oldValidityLimit.get("LowerValidityLimit", None) != lowerValidityLimit:
                            
                            log.trace("An existing Validity limit has changed")
                            log.trace("Old: %s" % (str(oldValidityLimit)))
                            
                            oldValidityLimit["UpperValidityLimit"]=upperValidityLimit
                            oldValidityLimit["LowerValidityLimit"]=lowerValidityLimit
                            
                            oldLimit["VALIDITY"] = oldValidityLimit
                            limits[valueId]=oldLimit
                        else:
                            log.trace("No change to an existing Validity limit")
                
                elif string.upper(limitType) == "RELEASE":
                    upperReleaseLimit, lowerReleaseLimit = getReleaseLimits(record)
                    if "RELEASE" in oldLimit:
                        oldReleaseLimit = oldLimit["RELEASE"]
    
                        if oldReleaseLimit.get("UpperReleaseLimit", None) != upperReleaseLimit or \
                            oldReleaseLimit.get("LowerReleaseLimit", None) != lowerReleaseLimit:
                            
                            log.trace("An existing Release limit has changed")
                            log.trace("Old: %s" % (str(oldReleaseLimit)))
                            
                            oldReleaseLimit["UpperReleaseLimit"]=upperReleaseLimit
                            oldReleaseLimit["LowerReleaseLimit"]=lowerReleaseLimit
                            
                            oldLimit["RELEASE"] = oldReleaseLimit
                            limits[valueId]=oldLimit
                        else:
                            log.trace("No change to an existing Release limit")

    
        else:
            log.infof("Adding a new limit to the limit data structure for %s", str(valueId))
            d=packNewLimit(record, tagProvider)
            updateLimitTags(d, tagProvider)

            # Now add the dictionary to the big permanent dictionary
            limits[valueId]=d

    log.trace("The new Limit dictionary is: %s" % (str(limits)))
    return limits

#
def parseRecipeFamilyFromGradeTagPath(tagPath):
    print "In %s.parseRecipeFamilyFromGradeTagPath() with %s" % (__name__, tagPath)
    i=tagPath.find("Site/") + 5
    recipeFamily=tagPath[i:]
    
    i=recipeFamily.find("/")
    recipeFamily=recipeFamily[:i]
    print "...the recipe family is ", recipeFamily
    return recipeFamily


# This is called in response to a grade change (and also maybe on restart).  It fetches the grade specific SQC limits from recipe and 
# updates the lab data database tables.
def updateLabLimitsFromRecipe(recipeFamily, grade, tagProvider, database):
    log.infof("In %s.updateLabLimitsFromRecipe(): Loading SQC limits from recipe for family: %s, grade: %s, tagProvider: %s", __name__, recipeFamily, str(grade), tagProvider)
    
    if grade == None:
        log.warn("Unable to load SQC limits for an unknown grade.")
        return
    
    ''' 
    Strip off any decimal portion of the grade 
    (Some sites treat grade as a number, others as a text string.  Lab data treats it as a string.)
    '''
    grade = str(grade)
    if grade.rfind(".") > 0:
        grade = grade[:grade.rfind(".")]
        log.infof("   modified grade <%s>", grade)
    
    # I could do this all in one SQL but then I might miss some limits if the parameter names do not match
    # If there is something in recipe that does not exist in lab data then I want to notify someone.
    SQL = "select P.Parameter, L.UpperLimit, L.LowerLimit "\
        " from RtSQCParameter P, RtSQCLimit L, RtRecipeFamily F "\
        " where P.ParameterId = L.ParameterID "\
        " and P.RecipeFamilyId = F.RecipeFamilyId "\
        " and L.Grade = '%s' and F.RecipeFamilyName = '%s'" % (grade, recipeFamily)
    sqlLog.trace(SQL)

    pds = system.db.runQuery(SQL, database)
    log.infof("...fetched %d SQC parameters for this grade...", len(pds))
    for record in pds:
        parameterName=record["Parameter"]
        upperLimit=record["UpperLimit"]
        lowerLimit=record["LowerLimit"]
        log.trace("Loaded limit for %s: %s -> %s" % (parameterName, str(lowerLimit), str(upperLimit)))
        SQL = "select V.ValueName, L.limitId, U.UnitName, LU.LookupName LimitType "\
            "from LtValue V, LtLimit L, TkUnit U, Lookup LU "\
            "where L.RecipeParameterName = '%s'"\
            " and V.ValueId = L.ValueId "\
            " and L.LimitTypeId = LU.LookupId"\
            " and V.UnitId = U.UnitId" % (parameterName)
        sqlLog.trace(SQL)
        
        ldpds=system.db.runQuery(SQL, database)
        if len(ldpds) == 0:
            log.warnf("WARNING - Unable to locate any Lab Data for recipe parameter: %s", parameterName)
        
        for labDataRecord in ldpds:
            valueName=labDataRecord['ValueName']
            limitId=labDataRecord['limitId']
            unitName=labDataRecord['UnitName']
            limitType=labDataRecord['LimitType']
            log.trace("   ... found a matching lab data named %s (%s) with limit id: %i (unit=%s)" % (valueName, limitType, limitId, unitName))
            updateLabLimits(valueName, unitName, limitType, limitId, upperLimit, lowerLimit, tagProvider, database)
             

# 
def updateLabLimits(valueName, unitName, limitType, limitId, upperSQCLimit, lowerSQCLimit, tagProvider, database):
    '''
    Calculate the target, standard deviation, and validity limits from the SQC limits and updates the LtLimit table.  
    The SQC limits can come from anywhere: recipe, the DCS, or manually entered.
    '''
    target=float("NaN")
    standardDeviation=float("NaN")
    lowerValidityLimit=float("NaN")
    upperValidityLimit=float("NaN")
            
    '''
    The default number of standard deviations from the target to the limits is 3
    The old system would look at the SQC limit blocks that use this lab data and find the max standard deviation,
    I'm not real sure how I am going to do this. 
    '''
    standardDeviationsToSQCLimits = system.tag.read("[%s]Configuration/LabData/standardDeviationsToSQCLimits" % (tagProvider)).value
    standardDeviationsToValidityLimits = system.tag.read("[%s]Configuration/LabData/standardDeviationsToValidityLimits" % (tagProvider)).value
    log.trace("Using %s standard deviations to the SQC limits and %s standard deviations to the validity limits" % (str(standardDeviationsToSQCLimits), str(standardDeviationsToValidityLimits)))

    if limitType == "Release":
        if upperSQCLimit == None:
            SQL = "Update LtLimit set upperReleaseLimit = NULL where limitId = %s" % (str(limitId))
            upperSQCLimit=float("NaN")
        else:
            SQL = "Update LtLimit set upperReleaseLimit = %s where limitId = %s" % (str(upperSQCLimit), str(limitId))

        sqlLog.trace(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        sqlLog.trace("   ...updated %i rows" % (rows))
        
        if lowerSQCLimit == None:
            SQL = "Update LtLimit set lowerReleaseLimit = NULL where limitId = %s" % (str(limitId))
            lowerSQCLimit=float("NaN")
        else:
            SQL = "Update LtLimit set lowerReleaseLimit = %s where limitId = %s" % (str(lowerSQCLimit), str(limitId))

        sqlLog.trace(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        sqlLog.trace("   ...updated %i rows" % (rows))
        
        # Now write the fetched limits to the Lab Data UDT tags
        path = '[' + tagProvider + ']LabData/' + unitName + '/' + valueName + '-RELEASE'
        tags = [path+'/lowerReleaseLimit', path+'/upperReleaseLimit']
        vals = [lowerSQCLimit, upperSQCLimit]
    
    elif limitType == "Validity":
        if upperSQCLimit == None:
            SQL = "Update LtLimit set upperValidityLimit = NULL where limitId = %s" % (str(limitId))
            upperSQCLimit=float("NaN")
        else:
            SQL = "Update LtLimit set upperValidityLimit = %s where limitId = %s" % (str(upperSQCLimit), str(limitId))

        sqlLog.trace(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        sqlLog.trace("   ...updated %i rows" % (rows))
        
        if lowerSQCLimit == None:
            SQL = "Update LtLimit set lowerValidityLimit = NULL where limitId = %s" % (str(limitId))
            lowerSQCLimit=float("NaN")
        else:
            SQL = "Update LtLimit set lowerValidityLimit = %s where limitId = %s" % (str(lowerSQCLimit), str(limitId))

        sqlLog.trace(SQL)
        rows=system.db.runUpdateQuery(SQL, database)
        sqlLog.trace("   ...updated %i rows" % (rows))
        
        # Now write the fetched limits to the Lab Data UDT tags
        path = '[' + tagProvider + ']LabData/' + unitName + '/' + valueName + '-VALIDITY'
        tags = [path+'/lowerValidityLimit', path+'/upperValidityLimit']
        vals = [lowerSQCLimit, upperSQCLimit]
    
    else:
        # It must be an SQC limit - SQC limits must be two-sided
        #TODO SHould NULL values clear out any previous values?

        if upperSQCLimit == None or lowerSQCLimit == None:
            log.error("Can't calculate SQC target or standard deviation for %s, because one of the limits is NULL" % (valueName))
            lowerSQCLimit=float("NaN")
            upperSQCLimit=float("NaN")
            target=float("NaN")
            standardDeviation=float("NaN")
            lowerValidityLimit=float("NaN")
            upperValidityLimit=float("NaN")
            SQL = "Update LtLimit set " \
                " UpperSQCLimit = NULL, "\
                " LowerSQCLimit = NULL, "\
                " UpperValidityLimit = NULL, "\
                " LowerValidityLimit = NULL, "\
                " Target = NULL, "\
                " StandardDeviation = NULL "\
                " where limitId = %s" % (str(limitId))
            sqlLog.trace(SQL)
            rows=system.db.runUpdateQuery(SQL, database)
            sqlLog.trace("   ...updated %i rows" % (rows))
        
        else: 
            log.infof("Loading new SQC limits for %s: %s to %s", valueName, str(lowerSQCLimit), str(upperSQCLimit))
            try:
                target, standardDeviation, lowerValidityLimit, upperValidityLimit = calcSQCLimits(lowerSQCLimit, upperSQCLimit, standardDeviationsToSQCLimits, standardDeviationsToValidityLimits)
    
                SQL = "Update LtLimit set " \
                    " UpperSQCLimit = %s, "\
                    " LowerSQCLimit = %s, "\
                    " UpperValidityLimit = %s, "\
                    " LowerValidityLimit = %s, "\
                    " Target = %s, "\
                    " StandardDeviation = %s "\
                    " where limitId = %s" % (str(upperSQCLimit), str(lowerSQCLimit), str(upperValidityLimit), str(lowerValidityLimit), \
                               str(target), str(standardDeviation), str(limitId))
                sqlLog.trace(SQL)
                rows=system.db.runUpdateQuery(SQL, database)
                sqlLog.trace("   ...updated %i rows" % (rows))
            except:
                log.errorf("Caught error calculating SQC limits for %s: %s to %s (%s - %s)", valueName, str(lowerSQCLimit), str(upperSQCLimit), str(standardDeviationsToSQCLimits), str(standardDeviationsToValidityLimits))
                target=float("NaN")
                standardDeviation=float("NaN")
                lowerValidityLimit=float("NaN")
                upperValidityLimit=float("NaN")
    
        # Now write the fetched and calculated limits to the Lab Data UDT tags
    
        path = '[' + tagProvider + ']LabData/' + unitName + '/' + valueName + '-SQC'
    
        tags = [path+'/lowerSQCLimit', path+'/lowerValidityLimit', path+'/standardDeviation', path+'/target', path+'/upperSQCLimit', path+'/upperValidityLimit']
        vals = [lowerSQCLimit, lowerValidityLimit, standardDeviation, target, upperSQCLimit, upperValidityLimit]

    
    # Now perform the write and feedback any errors
    status=system.tag.writeAll(tags, vals)

    i = 0
    for stat in status:
        if stat == 0:
            log.error("   ERROR writing %s to %s" % (str(vals[i]), tags[i]))
        elif stat == 1:
            log.trace("   successfully wrote %s to %s" % (str(vals[i]), tags[i]))
        else:
            log.trace("   write pending %s to %s" % (str(vals[i]), tags[i]))
        i = i + 1
    
    return target, standardDeviation, lowerValidityLimit, upperValidityLimit

def calcSQCLimits(lowerSQCLimit, upperSQCLimit, standardDeviationsToSQCLimits, standardDeviationsToValidityLimits):
    '''
    This doesn't really calculate SQC limits, it calculates limparameters from the SQC limits.
    '''
    target = (upperSQCLimit + lowerSQCLimit) / 2.0
    standardDeviation = (upperSQCLimit - lowerSQCLimit) / (2.0 * standardDeviationsToSQCLimits)
    upperValidityLimit = target + (standardDeviationsToValidityLimits * standardDeviation)
    lowerValidityLimit = target - (standardDeviationsToValidityLimits * standardDeviation)
    
    return target, standardDeviation, lowerValidityLimit, upperValidityLimit