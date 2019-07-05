'''
Created on Aug 2, 2015

@author: Pete

The grade tag must always be in a folder that is the name of the unit.  So we can get the unit out of the tagPath

'''

import system
log = system.util.getLogger("com.ils.common")

# Read the current grade for a unit.  The works because we adhere to the convention of a grade UDT inside 
# a unit folder in the site folder.
def getGradeForUnit(unitName, tagProvider):
    # Try to read the current grade
    tagPath="[%s]Site/%s/Grade/grade" % (tagProvider, unitName)

    exists=system.tag.exists(tagPath)
    if exists:
        grade=system.tag.read(tagPath)
        if grade.quality.isGood():
            grade=grade.value
        else:
            log.error("Grade tag (%s) quality is bad!" % (tagPath))
            grade=None
    else:
        log.error("Grade tag (%s) does not exist" % (tagPath))
        grade=None
    
    return grade

'''
'''
def handleGradeChange(tagPath, previousValue, currentValue, initialChange):
    log.infof( "Handling common grade change logic for  a change from %s to %s for %s...", str(previousValue.value), str(currentValue.value), tagPath)
    
    from ils.io.util import getProviderFromTagPath
    tagProvider = getProviderFromTagPath(tagPath)
    
    from ils.common.config import getTagProvider, getDatabase, getIsolationDatabase
    productionTagProvider = getTagProvider()
    
    if tagProvider == productionTagProvider:
        db = getDatabase()
    else:
        db = getIsolationDatabase()
        
    tagPathRoot = tagPath[:tagPath.rfind('/')+ 1]
        
    '''
    Get the unit out of the tagPath which points to the grade tag within the grade UDT
    '''
    unit = tagPath[tagPath.find('/')+1:]
    unit = unit[:unit.find('/')]
    log.infof("The Unit from the grade tag is <%s>", unit)
    
    logGradeChange(tagPath, previousValue, currentValue, initialChange, tagPathRoot, unit, tagProvider, db)
    resetCatInHours(tagPath, previousValue, currentValue, initialChange, tagPathRoot, unit, tagProvider, db)
    
    log.infof( "... done with common grade change logic for grade %s (%s)!", str(currentValue.value), tagPath)


'''
When the grade changes, we need to reset the total cat in hours for this grade.
'''
def resetCatInHours(tagPath, previousValue, currentValue, initialChange, tagPathRoot, unit, tagProvider, db):
    print "Resetting the Cat In hours for ", unit
    system.tag.write(tagPathRoot + "catInHours", 0.0)


'''
When the grade changes we log a whole bunch of stuff to the operator logbook
'''
def logGradeChange(tagPath, previousValue, currentValue, initialChange, tagPathRoot, unit, tagProvider, db):
    
    if initialChange:
        return
    
    try:
        log.infof("writing grade change information to the operator logbook for grade tag %s", tagPath)
        
        qvs = system.tag.readAll([tagPathRoot + "currentProduction", tagPathRoot + "catInHours", tagPathRoot + "timeOfMostRecentGradeChange"])
        
        if qvs[0].quality.isGood():
            production = qvs[0].value
        else:
            production = "BAD QUALITY"
        
        if qvs[1].quality.isGood():
            catInHours = qvs[1].value
        else:
            catInHours = "BAD QUALITY"
        
        if qvs[2].quality.isGood():
            gradeChangeTime = qvs[2].value
            gradeHours = system.date.hoursBetween(gradeChangeTime, system.date.now())
        else:
            gradeHours = "BAD QUALITY"
        
        msg = "Grade %s has just been downloaded for the %s unit.  A change from %s." % (str(currentValue.value), unit, str(previousValue.value))
        msg += "\nGrade %s accumulated %s cat-in run hours during %s total hours" % (str(previousValue.value), str(round(catInHours,2)), str(round(gradeHours, 2)))
        msg += "\nReactor production was %s klb for the run." % (str(production))
        
        from ils.diagToolkit.common import fetchPostForUnit
        post = fetchPostForUnit(unit, db)
        
        from ils.common.operatorLogbook import insertForPost
        insertForPost(post, msg, db)
    except:
        from ils.common.error import catchError
        txt = catchError(__name__+ ".logGradeChange()", "Grade Tag: " + tagPath + ", Grade: " + str(currentValue.value))
        log.error(txt)

'''
This runs pretty often and updates the total cat-in time by the amount of time since the last time this ran. 
'''
def updateCatInHours(tagPath, previousValue, currentValue, initialChange):
    
    if initialChange:
        return
    
    tagPathRoot = tagPath[:tagPath.rfind('/')+ 1]

    qv = system.tag.read(tagPathRoot + "catInHours")
    if qv.quality.isGood():
        catInHours = qv.value
        if catInHours == None:
            catInHours = 0.0
    else:
        catInHours = 0.0
    
    hoursBetween = system.date.secondsBetween(previousValue.value, currentValue.value) / 60.0 / 60.0
    catInHours = catInHours + hoursBetween 
    system.tag.write(tagPathRoot + "catInHours", catInHours)