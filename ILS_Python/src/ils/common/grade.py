'''
Created on Aug 2, 2015

@author: Pete
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