'''
Created on Mar 31, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.labData")
sqlLog = LogUtil.getLogger("com.ils.SQL.labData")

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
    print "Checking SQC limits: ", limit
    return True

def checkReleaseLimit(valueId, valueName, rawValue, sampleTime, database, tagProvider, limit):
    print "Checking Release limits", limit
    return True

# This fetches the currently active limits that are the Lab Data Toolkit tables regardless of where the
# values came from.
def fetchLimits(database = ""):
    limits=[]

    log.trace("Fetching Limits...")
    SQL = "select * from LtLimitView order by ValueName"
    sqlLog.trace(SQL)
    pds = system.db.runQuery(SQL, database)
    log.trace("  ...fetched %i limits!" % (len(pds)))
    for record in pds:
        d={
           "ValueName":record["ValueName"],
           "Post":record["Post"],
           "UpperValidityLimit":record["UpperValidityLimit"],
           "LowerValidityLimit":record["LowerValidityLimit"],
           "UpperSQCLimit":record["UpperSQCLimit"],
           "LowerSQCLimit":record["LowerSQCLimit"],
           "UpperReleaseLimit":record["UpperReleaseLimit"],
           "LowerReleaseLimit":record["LowerReleaseLimit"],
           "Target":record["Target"],
           "StandardDeviation":record["StandardDeviation"],
        }
        limits.append(d)

    log.trace("Limits: %s" % (str(limits)))
    return limits

# This is called in response to a grade change (and also maybe on restart).  It fetches the grade specific SQC limits from recipe and 
# updates the lab data database tables.
def updateSQCLimitsFromRecipe(grade, database=""):
    log.trace("Loading SQC limits from recipe for grade: %s" % (str(grade)))
    
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
    
    # Now perform the write and feedback any errors
    status = system.tag.writeAll(tags, vals)
    
    i = 0
    for stat in status:
        if stat == 1:
            log.trace("   successfully wrote %s to %s" % (str(vals[i]), tags[i]))
        else:
            log.error("Error writing %s to %s (Status=%i)" % (str(vals[i]), tags[i], stat))
        i = i + 1