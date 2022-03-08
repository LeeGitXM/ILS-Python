'''
Created on Sep 19, 2019

@author: phass
'''
from ils.log import getLogger
log =getLogger(__name__)

def glucoseAverage(dataDictionary):
    '''
    There must be exactly 3 values.  The trigger value and two related values.
    The formula is (R1 + R2 + T) / 3 
    This method does not care about the order of dictionaries or how much related data there is.
    '''
    log.infof("In %s.glucoseAverage() - a derived value callback - the data dictionary is: %s", __name__, str(dataDictionary))
    
    total = 0
    i = 0
    for tagDictionary in dataDictionary.values(): 
        log.tracef("   Tag dictionary: %s", str(tagDictionary))
        rawValue = tagDictionary.get("rawValue")
        total += float(rawValue)
        i += 1

    derivedVal = total / i
    log.tracef("   Calculated average glucose (from %d values) as: %f", i, derivedVal)
    return {"status": "success", "value":derivedVal}

def glucoseMin(dataDictionary):
    '''
    Calculate the the minimum value.  This method does not care which value is the minimum or how many values there are.
    The formula is min(values) 
    '''
    log.infof("In %s.glucoseMin() - a derived value callback - the data dictionary is: %s", __name__, str(dataDictionary))
    
    minValue = 1000000.0
    i = 0
    for tagDictionary in dataDictionary.values(): 
        log.tracef("   Tag dictionary: %s", str(tagDictionary))
        rawValue = float(tagDictionary.get("rawValue"))
        if rawValue < minValue:
            minValue = rawValue
            i += 1

    log.tracef("   Calculated glucose minimum as: %f from %d values", minValue, i)
    return {"status": "success", "value":minValue}

def glucoseRatio(dataDictionary):
    '''
    This derived data calculation method depends on the order of the related data.  
    There must be exactly 3 values.  The trigger value and two related values.
    The formula is average(R1 + R2) / T 
    '''
    log.infof("In %s.glucoseRatio() - a derived lab data callback - the data dictionary is: %s", __name__, str(dataDictionary))
    
    for tagDictionary in dataDictionary.values(): 
        log.trace("   Tag dictionary: %s" % (str(tagDictionary)))
        if tagDictionary.get("trigger"):
            T = tagDictionary.get("rawValue")
        else:
            if tagDictionary.get("order") == 0:
                R1 = tagDictionary.get("rawValue", 0.0)
            else:
                R2 = tagDictionary.get("rawValue", 0.0)

    derivedVal = ((R1 + R2) / 2.0) / T
    log.tracef("   Calculated c9InCrumb as: %f", derivedVal)
    return {"status": "success", "value":derivedVal}