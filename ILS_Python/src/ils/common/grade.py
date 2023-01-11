'''
Created on Aug 2, 2015
@author: Pete
The grade tag must always be in a folder that is the name of the unit.  So we can get the unit out of the tagPath
'''

import system
from ils.io.util import readTag, writeTag
from ils.log import getLogger
log = getLogger(__name__)

# Read the current grade for a unit.  The works because we adhere to the convention of a grade UDT inside 
# a unit folder in the site folder.
def getGradeForUnit(unitName, tagProvider):
    # Try to read the current grade
    tagPath="[%s]Site/%s/Grade/grade" % (tagProvider, unitName)

    exists=system.tag.exists(tagPath)
    if exists:
        grade=readTag(tagPath)
        if grade.quality.isGood():
            grade=grade.value
        else:
            log.error("Grade tag (%s) quality is bad!" % (tagPath))
            grade=None
    else:
        log.error("Grade tag (%s) does not exist" % (tagPath))
        grade=None
    
    return grade


def handleGradeChange(tagPath, previousValue, currentValue, initialChange):
    '''
    Implement some really basic logic for a grade change.  
    All of this is internal to the grade change UDT, it doesn't do anything to diagtoolikt, recipe, or lab data.
    '''
    legit, status = gradeChangeIsLegit(tagPath, previousValue, currentValue, initialChange)
    
    if not(legit):
        log.tracef("Ignoring a grade change which is deemed to not be legit because: %s", status)
        return
    
    log.infof( "Handling common grade change logic for a change from %s to %s for %s...", str(previousValue.value), str(currentValue.value), tagPath)
    
    tagPathRoot = tagPath[:tagPath.rfind('/')+ 1]
    projectName = readTag(tagPathRoot + "/projectName").value
    if projectName == "":
        log.warnf("Unable to process the grade change because the project has not been set in the Grade UDT <%s>", tagPathRoot)
        return
    
    from ils.io.util import getProviderFromTagPath
    tagProvider = getProviderFromTagPath(tagPath)

    from ils.config.gateway import getTagProvider, getDatabase
    productionTagProvider = getTagProvider(projectName, False)

    if tagProvider == productionTagProvider:
        db = getDatabase(projectName, False)
    else:
        db = getDatabase(projectName, True)

    '''
    Get the unit out of the tagPath which points to the grade tag within the grade UDT
    '''
    unit = tagPath[tagPath.find('/')+1:]
    unit = unit[:unit.find('/')]
    log.infof("The Unit from the grade tag is <%s>", unit)
    
    logGradeChange(tagPath, previousValue, currentValue, initialChange, tagPathRoot, unit, tagProvider, db)
    resetCatInHours(tagPath, previousValue, currentValue, initialChange, tagPathRoot, unit, tagProvider, db)
    
    writeTag(tagPathRoot + "lastGradeProcessed", currentValue.value)
    
    log.infof( "... done with common grade change logic for grade %s (%s)!", str(currentValue.value), tagPath)


def gradeChangeIsLegit(tagPath, previousValue, currentValue, initialChange):
    legit = True
    
    ''' If the quality of the new value is bad then this can't be legit '''
    if not(currentValue.quality.isGood()):
        return False, "This grade change is not legit because the quality is bad."
    
    tagPathRoot = tagPath[:tagPath.rfind('/')+ 1]
    lastGrade = readTag(tagPathRoot + "lastGradeProcessed").value
    
    if currentValue.value == lastGrade:
        return False, "This grade <%s> has already been processed." % (str(lastGrade))
    
    return legit, ""


def resetCatInHours(tagPath, previousValue, currentValue, initialChange, tagPathRoot, unit, tagProvider, db):
    '''
    When the grade changes, we need to reset the total cat in hours for this grade.
    '''
    print "Resetting the Cat In hours for ", unit
    writeTag(tagPathRoot + "catInHours", 0.0)


'''
When the grade changes we log a whole bunch of stuff to the operator logbook
'''
def logGradeChange(tagPath, previousValue, currentValue, initialChange, tagPathRoot, unit, tagProvider, db):
    
    if initialChange:
        return
    
    try:
        log.infof("writing grade change information to the operator logbook for grade tag %s", tagPath)
        
        qvs = system.tag.readBlocking([tagPathRoot + "currentProduction", tagPathRoot + "catInHours", tagPathRoot + "timeOfMostRecentGradeChange"])
        
        if qvs[0].quality.isGood():
            production = qvs[0].value
        else:
            production = "BAD QUALITY"
        
        if qvs[1].quality.isGood():
            catInHours = qvs[1].value
            catInHours = str(round(catInHours,2))
        else:
            catInHours = "BAD QUALITY"
        
        if qvs[2].quality.isGood():
            gradeChangeTime = qvs[2].value
            gradeHours = system.date.hoursBetween(gradeChangeTime, system.date.now())
            gradeHours = str(round(gradeHours, 2))
        else:
            gradeHours = "BAD QUALITY"
        
        msg = "Grade %s has just been downloaded for the %s unit.  A change from %s." % (str(currentValue.value), unit, str(previousValue.value))
        msg += "\nGrade %s accumulated %s cat-in run hours during %s total hours" % (str(previousValue.value), catInHours, gradeHours)
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

    qv = readTag(tagPathRoot + "catInHours")
    if qv.quality.isGood():
        catInHours = qv.value
        if catInHours == None:
            catInHours = 0.0
    else:
        catInHours = 0.0
    
    hoursBetween = system.date.secondsBetween(previousValue.value, currentValue.value) / 60.0 / 60.0
    catInHours = catInHours + hoursBetween 
    writeTag(tagPathRoot + "catInHours", catInHours)