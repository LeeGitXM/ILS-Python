'''
Created on May 9, 2018

@author: phass
'''

import system
from ils.io.util import readTag
from ils.common.config import getDatabaseClient, getTagProviderClient

def internalFrameOpened(rootContainer):
    print "In %s.internalFrameOpened" % (__name__)
    database = getDatabaseClient()
    tagProvider = getTagProviderClient()
    
    browseTags = system.tag.browseTags(
        parentPath="[%s]Site" % (tagProvider), 
        tagPath="*", 
        tagType="UDT_INST", 
        udtParentType="Grade", 
        recursive=True
        )

    print "...found %d grade tags..." % (len(browseTags))
    header = ["name"]
    data = []
    for browseTag in browseTags:
        print "<%s>" % (browseTag.path)
        unitName = browseTag.path[5:]
        print "<%s>" % (unitName)
        
        # I'm not exactly sure what I am doing here.  Maybe it has to do with how EM names these things.
        if unitName.find('/') > 0:
            unitName = unitName[:unitName.find('/')]
        
        print "<%s>" % (unitName)
        data.append([unitName])
        print "   ", unitName
    ds = system.dataset.toDataSet(header, data)
    
    familyDropdown = rootContainer.getComponent("Recipe Family Dropdown")
    familyDropdown.data = ds
    familyDropdown.selectedValue = -1
    
    gradeField = rootContainer.getComponent("Grade Field")
    gradeField.text = ""


def refreshGrade(rootContainer):
    '''
    This is called when the user selects a recipe family from the recipe family dropdown.  
    This goes out and reads the current grade for the family that was selected.
    '''
    tagProvider = getTagProviderClient()
    familyDropdown = rootContainer.getComponent("Recipe Family Dropdown")
    gradeField = rootContainer.getComponent("Grade Field")
    
    recipeFamilyName = familyDropdown.selectedStringValue
    if recipeFamilyName == "":
        print "Skipping the grade refresh!"
        return
    
    tagPath = "[%s]Site/%s/Grade/grade" % (tagProvider, recipeFamilyName)
    print "Refreshing grade for family %s from %s " % (recipeFamilyName, tagPath)
    qv = readTag(tagPath)
    grade = qv.value
    print "Read grade: ", grade
    gradeField.text = str(grade)


def updateCallback(rootContainer):
    '''
    This is called when the user presses the button on the "Update Lab Limits From Recipe"
    '''
    tagProvider = getTagProviderClient()
    database = getDatabaseClient()
    
    familyDropdown = rootContainer.getComponent("Recipe Family Dropdown")
    gradeField = rootContainer.getComponent("Grade Field")
    
    family = familyDropdown.selectedStringValue
    grade = gradeField.text
    
    from ils.labData.limits import updateLabLimitsFromRecipe
    updateLabLimitsFromRecipe(family, grade, tagProvider, database)
    
    