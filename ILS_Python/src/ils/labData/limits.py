'''
Created on Mar 31, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from cookielib import vals_sorted_by_key
log = LogUtil.getLogger("com.ils.labData.limits")
sqlLog = LogUtil.getLogger("com.ils.SQL.labData.limits")

# This is a memory resident dictionary of limit dictionaries that survives from scan to scan.  
# The key is the valueId. It gets updated each cycle.  The main purpose of this cache is so that we can determine
# 
limits={}


def checkValidityLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit):
    log.trace("Checking Validity limits for %s..." % (valueName))
    
    upperLimit=limit.get("UpperValidityLimit",None)
    lowerLimit=limit.get("LowerValidityLimit",None)
    log.trace("   ...the validity limits are %s < %s < %s" % (str(lowerLimit), str(rawValue), str(upperLimit)))
    
    if upperLimit != None and rawValue > upperLimit:
        log.trace("%s **Failed** the validity upper limit check..." % (valueName))        
        return False, upperLimit, lowerLimit
    elif lowerLimit != None and rawValue < lowerLimit:
        log.trace("%s **Failed** the validity lower limit check..." % (valueName))
        return False, upperLimit, lowerLimit
    else:
        log.trace("%s passed the validity limit check..." % (valueName))
    return True, upperLimit, lowerLimit

def checkSQCLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit):
    log.trace("Checking SQC limits...")
    return True

# Release limit checking is exactly like validity limit checking, the difference is what happens if they fail.  It appears that
# the main difference is that the notification screen gives the operator the chance to start a UIR.
# One concern is that the G2 code for release limits absolutely uses the limits in the validity limit slot - it was unclear if 
# they just put the release limits into the validity limits so they could use some common processing logic or what - but I am going 
# to use the limits in the release limits 
def checkReleaseLimit(valueId, valueName, rawValue, sampleTime, database, tagProvider, limit):
    log.trace("Checking Release limits for %s..." % (valueName))
    
    upperLimit=limit.get("UpperReleaseLimit",None)
    lowerLimit=limit.get("LowerReleaseLimit",None)
    log.trace("   ...the release limits are %s < %s < %s" % (str(lowerLimit), str(rawValue), str(upperLimit)))
    
    if upperLimit != None and rawValue > upperLimit:
        log.trace("%s **Failed** the release upper limit check..." % (valueName))        
        return False, upperLimit, lowerLimit
    elif lowerLimit != None and rawValue < lowerLimit:
        log.trace("%s **Failed** the release lower limit check..." % (valueName))
        return False, upperLimit, lowerLimit
    else:
        log.trace("%s passed the release limit check..." % (valueName))
    return True, upperLimit, lowerLimit
    



# This fetches the currently active limits that are the Lab Data Toolkit tables regardless of where the
# values came from.
def fetchLimits(database = ""):
    #-------------------------------------
    # When SQC limits are loaded from recipe, the target, standard deviation and validity limits are calculated and then 
    # stored in the XOM database so no further calculations are necessary.
    def getSQCLimits(record):
        limitSource=record["LimitSource"]
        if limitSource=="DCS":
            upperSQCLimit, lowerSQCLimit=readSQCLimitsFromDCS(record)
            upperValidityLimit=-1
            lowerValidityLimit=-1
            target=-1
            standardDeviation=-1
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
        if limitSource=="DCS":
            upperValidityLimit, lowerValidityLimit=readSQCLimitsFromDCS(record)
        else:
            upperValidityLimit=record["UpperValidityLimit"]
            lowerValidityLimit=record["LowerValidityLimit"]
        return upperValidityLimit, lowerValidityLimit
    #----
    def getReleaseLimits(record):
        limitSource=record["LimitSource"]
        if limitSource=="DCS":
            upperReleaseLimit, lowerReleaseLimit=readSQCLimitsFromDCS(record)
        else:
            upperReleaseLimit=record["UpperReleaseLimit"]
            lowerReleaseLimit=record["LowerReleaseLimit"]
        return upperReleaseLimit, lowerReleaseLimit
    #-------------------------------------
    def packLimit(record):
        valueName=record["ValueName"]
        limitType=record["LimitType"]
        
        d={
           "ValueName":record["ValueName"],
           "LimitType":record["LimitType"],
           "UnitName":record["UnitName"],
           "Post":record["Post"],
           "ValidationProcedure":record["ValidationProcedure"]
           }

        if limitType == "SQC":
            upperSQCLimit, lowerSQCLimit, upperValidityLimit, lowerValidityLimit, target, standardDeviation = getSQCLimits(record)
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
            log.error("Unexpected limit type: <%s> for %s" % (limitType, valueName))

        print "Packed a dictionary for %s - %s: " % (valueName, str(d))
        return d
    #-----------------------------------------------------
    # Update the limit UDT (tags) with the new limits 
    def updateLimitTags(limit):   
        #-------------
        def writeLimit(providerName, unitName, valueName, limitType, limitValue):
            if limitValue != None:
                tagName="[%s]LabData/%s/%s/%s" % (providerName, unitName, valueName, limitType)
                print "Writing <%s> to %s" % (limitValue, tagName)
                system.tag.writeSynchronous(tagName, limitValue)
#                if result == 0:
#                    log.error("Writing new limit value of <%s> to <%s> failed" % (str(limitValue), tagName))
        #-------------
        providerName="XOM"
        unitName=limit.get("UnitName","")
        valueName=limit.get("ValueName", None)
        limitType=limit.get("LimitType", None)
        if limitType == "SQC":
            writeLimit(providerName, unitName, valueName + '-SQC', "upperValidityLimit", limit.get("UpperValidityLimit", None))
            writeLimit(providerName, unitName, valueName + '-SQC', "lowerValidityLimit", limit.get("LowerValidityLimit", None))
            writeLimit(providerName, unitName, valueName + '-SQC', "upperSQCLimit", limit.get("UpperSQCLimit", None))
            writeLimit(providerName, unitName, valueName + '-SQC', "lowerSQCLimit", limit.get("LowerSQCLimit", None))
            writeLimit(providerName, unitName, valueName + '-SQC', "target", limit.get("Target", None))
            writeLimit(providerName, unitName, valueName + '-SQC', "standardDeviation", limit.get("StandardDeviation", None))
        elif limitType == "Release":
            writeLimit(providerName, unitName, valueName + '-RELEASE', "upperReleaseLimit", limit.get("UpperReleaseLimit", None))
            writeLimit(providerName, unitName, valueName + '-RELEASE', "lowerReleaseLimit", limit.get("LowerReleaseLimit", None))
        elif limitType == "Validity":
            writeLimit(providerName, unitName, valueName + '-VALIDITY', "upperValidityLimit", limit.get("UpperValidityLimit", None))
            writeLimit(providerName, unitName, valueName + '-VALIDITY', "lowerValidityLimit", limit.get("LowerValidityLimit", None))
        else:
            log.error("Unexpected limit type: <%s> for %s" % (limitType, valueName))
    #-----------------------------------------------------------
    def readSQCLimitsFromDCS(record):
        valueName=record["ValueName"]
        serverName=record["WriteLocation"]
        upperItemId=record["OPCUpperItemId"]
        lowerItemId=record["OPCLowerItemId"]
        log.trace("Fetching DCS limits for %s from %s (upper: %s, lower: %s)" % (valueName, serverName, upperItemId, lowerItemId))
        vals=system.opc.readValues(serverName, [upperItemId, lowerItemId] )
        print "Read values: ", vals
                
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
        
    print "The old limits are:", limits
    log.trace("Fetching new Limits...")
    SQL = "select * from LtLimitView"
    sqlLog.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    log.trace("  ...fetched %i limits!" % (len(pds)))
    for record in pds:
        valueId=record["ValueId"]
        unitName=record["UnitName"]
        if valueId in limits:
            limitType=record["LimitType"]
            
            oldLimit=limits[valueId]
            if limitType == "SQC":
                upperSQCLimit, lowerSQCLimit, upperValidityLimit, lowerValidityLimit, target, standardDeviation=getSQCLimits(record)

                if oldLimit["UpperValidityLimit"] != upperValidityLimit or \
                    oldLimit["LowerValidityLimit"] != lowerValidityLimit or \
                    oldLimit["UpperSQCLimit"] != upperSQCLimit or \
                    oldLimit["LowerSQCLimit"] != lowerSQCLimit:
                    print "An existing SQC limit has changed"
                    print "Old:", oldLimit
                    oldLimit["UpperValidityLimit"]=upperValidityLimit
                    oldLimit["LowerValidityLimit"]=lowerValidityLimit
                    oldLimit["UpperSQCLimit"]=upperSQCLimit
                    oldLimit["LowerSQCLimit"]=lowerSQCLimit
                    oldLimit["Target"]=target
                    oldLimit["StandardDeviation"]=standardDeviation
                    updateLimitTags(oldLimit)
                    limits[valueId]=oldLimit
                else:
                    print "No change to an existing SQC limit"
        else:
            print "Adding a new limit to the limit data structure"
            d=packLimit(record)
            updateLimitTags(d)

            # Now add the dictionary to the big permanent dictionary
            limits[valueId]=d

    print "The new Limit dictionary is: ", limits
    return limits
    
# This is called in response to a grade change (and also maybe on restart).  It fetches the grade specific SQC limits from recipe and 
# updates the lab data database tables.
def updateSQCLimitsFromRecipe(grade, database=""):
    log.info("Loading SQC limits from recipe for grade: %s" % (str(grade)))
    
    # I could do this all in one SQL but then I might miss some limits if the parameter names do not match
    # If there is something in recipe that does not exist in lab data then I want to notify someone.
    SQL = "select P.Parameter, L.UpperLimit, L.LowerLimit "\
        " from RtSQCParameter P, RtSQCLimit L "\
        " where P.ParameterId = L.ParameterID "\
        " and Grade = %s" % (grade)
    sqlLog.trace(SQL)

    pds = system.db.runQuery(SQL, database)
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
        for labDataRecord in ldpds:
            valueName=labDataRecord['ValueName']
            limitId=labDataRecord['limitId']
            unitName=labDataRecord['UnitName']
            limitType=labDataRecord['LimitType']
            log.trace("   ... found a matching lab data named %s (%s) with limit id: %i (unit=%s)" % (valueName, limitType, limitId, unitName))
            updateSQCLimits(valueName, unitName, limitType, limitId, upperLimit, lowerLimit, database)
             

# This calculates the target, standard deviation, and validity limits from the SQC limits.  
# The SQC limits can come from anywhere, recipe, the DCS, or manually entered.
def updateSQCLimits(valueName, unitName, limitType, limitId, upperSQCLimit, lowerSQCLimit, database):
    
    # The default number of standard deviations from the target to the limits is 3
    # The old system would look at the SQC limit blocks that use this lab data and find the max standard deviation,
    # I'm not real sure how I am going to do this. 
    #TODO
    maxStandardDeviations = 3.0
    standardDeviationsToValidityLimits = system.tag.read("Configuration/LabData/standardDeviationsToValidityLimits").value
    
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
        path = '[XOM]LabData/' + unitName + '/' + valueName + '-RELEASE'
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
        path = '[XOM]LabData/' + unitName + '/' + valueName + '-VALIDITY'
        tags = [path+'/lowerValidityLimit', path+'/upperValidityLimit']
        vals = [lowerSQCLimit, upperSQCLimit]
    
    else:
        # It must be an SQC limit - SQC limits must be two-sided
        #TODO SHould NULL values clear out any previous values?
        if upperSQCLimit == None or lowerSQCLimit == None:
            log.error("Can't calculate target or standard deviation for %s, because one of the limits is NULL" % (valueName))
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
        else: 
            log.trace("Loading new limits for %s: %f to %f" % (valueName, lowerSQCLimit, upperSQCLimit))
            target = (upperSQCLimit + lowerSQCLimit) / 2.0
            standardDeviation = (upperSQCLimit - lowerSQCLimit) / (2.0 * maxStandardDeviations)
            upperValidityLimit = target + (standardDeviationsToValidityLimits * standardDeviation)
            lowerValidityLimit = target - (standardDeviationsToValidityLimits * standardDeviation)
    
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
    
        # Now write the fetched and calculated limits to the Lab Data UDT tags
    
        path = '[XOM]LabData/' + unitName + '/' + valueName + '-SQC'
    
        tags = [path+'/lowerSQCLimit', path+'/lowerValidityLimit', path+'/standardDeviation', path+'/target', path+'/upperSQCLimit', path+'/upperValidityLimit']
        vals = [lowerSQCLimit, lowerValidityLimit, standardDeviation, target, upperSQCLimit, upperValidityLimit]
    
    # Now perform the write and feedback any errors (Make this a synchronous write so we know what passed and what failed).
    system.tag.writeAllSynchronous(tags, vals)
    
#    i = 0
#    for stat in status:
#        if stat == 0:
#            log.error("   ERROR writing %s to %s" % (str(vals[i]), tags[i]))
#        elif stat == 1:
#            log.trace("   successfully wrote %s to %s" % (str(vals[i]), tags[i]))
#        else:
#            log.trace("   write pending %s to %s" % (str(vals[i]), tags[i]))
#        i = i + 1