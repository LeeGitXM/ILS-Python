'''
Created on Mar 31, 2015

@author: Pete
'''
import system

def checkValidityLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit):
    print "Checking Validity limits"
    
    upperLimit=limit.get("UpperValidityLimit",None)
    lowerLimit=limit.get("LowerValidityLimit",None)
    print "The validity limits are %s < %s < %s" % (str(lowerLimit), str(rawValue), str(upperLimit))
    
    if upperLimit != None and rawValue > upperLimit:
        print "%s **Failed** the validity upper limit check..." % (valueName)        
        return False, upperLimit, lowerLimit
    elif lowerLimit != None and rawValue < lowerLimit:
        print "%s **Failed** the validity lower limit check..." % (valueName)
        return False, upperLimit, lowerLimit
    else:
        print "%s passed the validity limit check..." % (valueName)
    return True, upperLimit, lowerLimit

def checkSQCLimit(post, valueId, valueName, rawValue, sampleTime, database, tagProvider, limit):
    print "Checking SQC limits: ", limit
    return True

def checkReleaseLimit(valueId, valueName, rawValue, sampleTime, database, tagProvider, limit):
    print "Checking Release limits", limit
    return True

def fetchLimits(database = ""):
    limits=[]

    print "Fetching Limits..."
    SQL = "select * from LtLimitView order by ValueName"
    pds = system.db.runQuery(SQL, database)
    print "  ...fetched %i limits!" % (len(pds))
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

    print "Limits: ", limits
    return limits
    