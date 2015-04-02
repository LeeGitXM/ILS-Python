'''
Created on Mar 31, 2015

@author: Pete
'''

def check(valueId, valueName, rawValue, database, tagProvider, limitpds):
    print "Checking limits"
    
    for record in limitpds:
        if record["ValueName"] == valueName:
            limitType = record["LimitTypeName"]
            if limitType == "Validity":
                checkValidityLimit(valueId, valueName, rawValue, database, tagProvider, record)
            elif limitType == "SQC":
                checkSQCLimit(valueId, valueName, rawValue, database, tagProvider, record)
            elif limitType == "Release":
                checkReleaseLimit(valueId, valueName, rawValue, database, tagProvider, record)

def checkValidityLimit(valueId, valueName, rawValue, database, tagProvider, record):
    print "Checking Validity limits"
    
    upperLimit=record["UpperLimit"]
    lowerLimit=record["LowerLimit"]
    if rawValue > upperLimit or rawValue < lowerLimit:
        print "%s **Failed** the validity limit check..." % (valueName)
    else:
        print "%s passed the validity limit check..." % (valueName)

def checkSQCLimit(valueId, valueName, rawValue, database, tagProvider, record):
    print "Checking SQC limits"

def checkReleaseLimit(valueId, valueName, rawValue, database, tagProvider, record):
    print "Checking Release limits"