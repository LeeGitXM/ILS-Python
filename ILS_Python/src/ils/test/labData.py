'''
Created on Sep 19, 2019

@author: phass
'''

import system
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

'''
This derived data calculation method depends on the order of the related data.  
There must be exactly 3 values.  The trigger value and two related values.
The formula is R1 + R2 + T / 3 
'''
def glucoseDerived(dataDictionary):
    log.tracef("In derived value callback %s.glucoseDerived() - the data dictionary is: %s", __name__, str(dataDictionary))
    
    for tagDictionary in dataDictionary.values(): 
        log.trace("   Tag dictionary: %s" % (str(tagDictionary)))
        if tagDictionary.get("trigger"):
            T = tagDictionary.get("rawValue")
            print "Found the trigger: ", T
        else:
            if tagDictionary.get("order") == 0:
                R1 = tagDictionary.get("rawValue")
            else:
                R2 = tagDictionary.get("rawValue")

    derivedVal = (R1 + R2 + T) / 3.0
    log.trace("   Calculated glucoseDerived as: %f" % (derivedVal))

    return {"status": "success", "value":derivedVal}


'''
This derived data calculation method depends on the order of the related data.  
There must be exactly 3 values.  The trigger value and two related values.
The formula is R1 / R2 + T 
'''
def c9InCrumb(dataDictionary):
    log.tracef("In derived value callback %s.c9InCrumb() - the data dictionary is: %s", __name__, str(dataDictionary))
    
    for tagDictionary in dataDictionary.values(): 
        log.trace("   Tag dictionary: %s" % (str(tagDictionary)))
        if tagDictionary.get("trigger"):
            T = tagDictionary.get("rawValue")
            print "Found the trigger: ", T
        else:
            if tagDictionary.get("order") == 0:
                R1 = tagDictionary.get("rawValue")
            else:
                R2 = tagDictionary.get("rawValue")

    derivedVal = R1 / R2 + T
    log.trace("   Calculated c9InCrumb as: %f" % (derivedVal))

    return {"status": "success", "value":derivedVal}
