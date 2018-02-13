'''
Created on Jul 17, 2015

@author: Pete
'''

import system, string
from ils.common.config import getTagProviderClient

def createLabValue(unitName, valueName):
    tagProvider = getTagProviderClient()
    UDTType='Lab Data/Lab Value'
    path = "LabData/" + unitName
    parentPath = "[%s]%s" % (tagProvider, path)  
    tagPath = parentPath + "/" + valueName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", tagPath, " already exists!"
    else:
        print "Creating a %s, Name: %s, Path: %s" % (UDTType, valueName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=valueName, tagType="UDT_INST", 
                          attributes={"UDTParentType":UDTType})

def createLabLimit(unitName, valueName, limitType):
    tagProvider = getTagProviderClient()
    parentPath = "[%s]LabData/%s" % (tagProvider, unitName)
    if string.upper(limitType) == 'SQC':
        udtType='Lab Data/Lab Limit SQC'
        suffix='-SQC'
    elif string.upper(limitType) == 'RELEASE':
        udtType='Lab Data/Lab Limit Release'
        suffix='-RELEASE'
    elif string.upper(limitType) == 'VALIDITY':
        udtType='Lab Data/Lab Limit Validity'
        suffix='-VALIDITY'

    labDataName=valueName+suffix
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "  ", tagPath, " already exists!"
    else:
        print "  creating a %s, Name: %s, Path: %s" % (udtType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
                      attributes={"UDTParentType":udtType})


def deleteLabValue(unitName, valueName):
    tagProvider = getTagProviderClient()
    path = "LabData/" + unitName
    parentPath = "[%s]%s" % (tagProvider, path)  
    tagPath = parentPath + "/" + valueName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "Deleting tag %s, Path: %s" % (valueName, tagPath)
        system.tag.removeTag(tagPath)
    else:
        print "%s (%s) does not exist!" % (valueName, tagPath)

def deleteLabLimit(unitName, valueName, limitType):
    tagProvider = getTagProviderClient()
    
    if string.upper(limitType) == 'SQC':
        suffix='-SQC'
    elif string.upper(limitType) == 'RELEASE':
        suffix='-RELEASE'
    elif string.upper(limitType) == 'VALIDITY':
        suffix='-VALIDITY'

    parentPath = "[%s]LabData/%s" % (tagProvider, unitName)
    labDataName=valueName+suffix
    tagPath = parentPath + "/" + labDataName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "Deleting tag %s, Path: %s" % (labDataName, tagPath)
        system.tag.removeTag(tagPath)
    else:
        print "%s (%s) does not exist!" % (labDataName, tagPath)

# This synchronizes the Lab Data UDTs and the database.  This can be used on startup, after some tags have been edited
# or on demand.   
def synchronize(provider, unitName):

    def synchronizeLabValues(provider, unitName):
        print ""
        print "     --- synchronizing lab value tags ---"
        print ""
        
        # For values, it doesn't matter if it is PHD, DCS, or local.  They all use the same UDT
        SQL = "select V.ValueId, V.ValueName from LtValue V, TkUnit U where V.UnitId = U.UnitId and U.UnitName = '%s'" % (unitName)
        pds = system.db.runQuery(SQL)
        
        # Make a couple of lists to facilitate easy searches
        valueNames = []
        for record in pds:
            valueNames.append(record["ValueName"])
            
        parentPath=provider+'LabData/'+unitName
        tags = system.tag.browseTags(parentPath=parentPath, udtParentType="Lab Data/Lab Value", recursive=True)
        selectors = system.tag.browseTags(parentPath=parentPath, udtParentType="Lab Data/Lab Selector Value", recursive=True)
        
        # The database is the master list
        # The first phase is to look for UDTs that should be deleted because they do not exist in the database
        print "Checking for tags to delete..."
        for tag in tags:
            if tag.name not in valueNames:
                print "   deleting ", tag.fullPath
                system.tag.removeTag(tag.fullPath)
            else:
                valueNames.remove(tag.name)
        
        print "Checking for selectors to delete..."
        for tag in selectors:
            if tag.name not in valueNames:
                print "   deleting ", tag.fullPath
                system.tag.removeTag(tag.fullPath)
            else:
                valueNames.remove(tag.name)

        # The second phase is for UDTS that need to be created because a record exists in the database but not as a UDT
        
        print "Checking for tags to create..."
        #TODO somehow I need to figure out how to distinguish between a selector and a regular lab value here
        for valueName in valueNames:
            print "Create ", valueName
            
            UDTType='Lab Data/Lab Value'
            path = "LabData/" + unitName
            parentPath = provider + path  
            tagPath = parentPath + "/" + valueName
            tagExists = system.tag.exists(tagPath)
            if tagExists:
                print "  ", tagPath, " already exists!"
            else:
                print "  creating a %s, Name: %s, Path: %s" % (UDTType, valueName, tagPath)
                system.tag.addTag(parentPath=parentPath, name=valueName, tagType="UDT_INST", 
                                  attributes={"UDTParentType":UDTType})
            
                
    #----------------------------------------------------------
    def synchronizeLabLimits(provider, unitName, limitType):

        print ""
        print "     --- synchronizing %s lab limits tags ---" % (limitType)
        print ""
        
        SQL = "select ValueId, ValueName, LimitType "\
            " from LtLimitView "\
            " where UnitName = '%s' and LimitType = '%s' order by ValueName" % (unitName, limitType)
        pds = system.db.runQuery(SQL)

        # Make a list to facilitate easy searches
        valueNames = []
        for record in pds:
            valueNames.append(record["ValueName"])
            
        parentPath=provider+'LabData/'+unitName
        if string.upper(limitType) == 'SQC':
            udtType='Lab Data/Lab Limit SQC'
            suffix='-SQC'
        elif string.upper(limitType) == 'RELEASE':
            udtType='Lab Data/Lab Limit Release'
            suffix='-RELEASE'
        elif string.upper(limitType) == 'VALIDITY':
            udtType='Lab Data/Lab Limit Validity'
            suffix='-VALIDITY'

        limits = system.tag.browseTags(parentPath=parentPath, udtParentType=udtType, recursive=True)

        print "Checking for %s limit tags to delete..." % (limitType)
        for tag in limits:
            tagName = tag.name
            end = tagName.rfind('-') #Strip off the limit type which conveniently comes at the end
            tagName = tagName[:end]
#            print "   Check if %s exists in the database %s - %s " % (tagName, tag.path, tag.fullPath)
            if tagName not in valueNames:
                print "   deleting ", tag.fullPath
                system.tag.removeTag(tag.fullPath)
            else:
                valueNames.remove(tagName)

        print "%s limits to create:" % (limitType)
        for tagName in valueNames:
            labDataName=tagName+suffix
            tagPath = parentPath + "/" + labDataName
            tagExists = system.tag.exists(tagPath)
            if tagExists:
                print "  ", tagPath, " already exists!"
            else:
                print "  creating a %s, Name: %s, Path: %s" % (udtType, labDataName, tagPath)
                system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
                              attributes={"UDTParentType":udtType})
    #----------------------------------------------------------

    synchronizeLabValues(provider, unitName)
    synchronizeLabLimits(provider, unitName, "SQC")
    synchronizeLabLimits(provider, unitName, "Release")
    synchronizeLabLimits(provider, unitName, "Validity")
