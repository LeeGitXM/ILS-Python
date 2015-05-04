'''
Created on Mar 31, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.labData")
sqlLog = LogUtil.getLogger("com.ils.labDataSQL")

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
        SQL = "select limitId from LtLimit where RecipeParameterName = '%s'" % (parameterName)
        sqlLog.trace(SQL)
        
        ldpds=system.db.runQuery(SQL, database)
        for labDataRecord in ldpds:
            limitId=labDataRecord['limitId']
            log.trace("   ... found a matching lab data limit with id: %i" % (limitId))
            updateSQCLimits(limitId, upperLimit, lowerLimit, database)
             

# This calculates the target, standard deviation, and validity limits from the SQC limits.  
# The SQC limits can come from anywhere, recipe, the DCS, or manually entered.
def updateSQCLimits(limitId, upperLimit, lowerLimit, database):
    
    # The default number of standard deviations from the target to the limits is 3
    # The old system would look at the SQC limit blocks that use this lab data and find the max standard deviation,
    # I'm not real sure how I am going to do this. 
    maxStandardDeviations = 3.0
    
    #TODO This needs to come from a configuration tag
    standardDeviationsToValidityLimits = 4.5
    
    if upperLimit == None or lowerLimit == None:
        log.error("Can't calculate target or standard deviation for limit id: %i, because one of the limits is NULL" % (limitId))
        return
    
    target = (upperLimit + lowerLimit) / 2.0
    standardDeviation = (upperLimit - lowerLimit) / (2.0 * maxStandardDeviations)
    upperValidityLimit = target + (standardDeviationsToValidityLimits * standardDeviation)
    lowerValidityLimit = target - (standardDeviationsToValidityLimits * standardDeviation)
    
    SQL = "Update LtLimit set " \
        " UpperSQCLimit = %s, "\
        " LowerSQCLimit = %s, "\
        " UpperValidityLimit = %s, "\
        " LowerValidityLimit = %s, "\
        " Target = %s, "\
        " StandardDeviation = %s "\
        " where limitId = %s" % (str(upperLimit), str(lowerLimit), str(upperValidityLimit), str(lowerValidityLimit), \
                               str(target), str(standardDeviation), str(limitId))
    sqlLog.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, database)
    log.trace("   ...updated %i rows" % (rows))