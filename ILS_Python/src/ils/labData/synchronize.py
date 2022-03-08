'''
Created on Jul 17, 2015

@author: Pete
'''

import system, string
from ils.common.config import getTagProviderClient
from ils.common.util import append
from ils.log import getLogger
log =getLogger(__name__)
LAB_DATA_ROOT = "LabData"

def createLabValue(unitName, valueName):
    tagProvider = getTagProviderClient()
    UDTType='Lab Data/Lab Value'
    path = LAB_DATA_ROOT + "/" + unitName
    parentPath = "[%s]%s" % (tagProvider, path)  
    tagPath = parentPath + "/" + valueName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        log.tracef("%s already exists!", tagPath)
    else:
        log.tracef("Creating a %s, Name: %s, Path: %s", UDTType, valueName, tagPath)
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
        log.tracef("%s already exists!", tagPath)
    else:
        log.tracef("Creating a %s, Name: %s, Path: %s", udtType, labDataName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=labDataName, tagType="UDT_INST", 
                      attributes={"UDTParentType":udtType})

def createDcsTag(unitName, valueName, interfaceName, itemId):
    tagProvider = getTagProviderClient()
    path = "LabData/%s/DCS-Lab-Values" % (unitName)
    parentPath = "[%s]%s" % (tagProvider, path)  
    tagPath = parentPath + "/" + valueName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        log.tracef("%s already exists!  ", tagPath)
    else:
        log.tracef("Creating an OPC tag for a DCS lab value named: %s, Path: %s", valueName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=valueName, tagType="OPC", dataType="Float8", 
                          attributes={"OPCServer": interfaceName, "OPCItemPath": itemId})

def createLabSelector(unitName, valueName):
    tagProvider = getTagProviderClient()
    UDTType='Lab Data/Lab Selector Value'
    path = LAB_DATA_ROOT + "/" + unitName
    parentPath = "[%s]%s" % (tagProvider, path)  
    tagPath = parentPath + "/" + valueName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        log.tracef("%s already exists!", tagPath)
    else:
        log.tracef("Creating a %s, Name: %s, Path: %s", UDTType, valueName, tagPath)
        system.tag.addTag(parentPath=parentPath, name=valueName, tagType="UDT_INST", 
                          attributes={"UDTParentType":UDTType})


def deleteLabValue(unitName, valueName):
    log.infof("Deleting lab data UDT for %s - %s", unitName, valueName)
    tagProvider = getTagProviderClient()
    tagPath = "[%s]%s/%s/%s" % (tagProvider, LAB_DATA_ROOT, unitName, valueName) 
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "Deleting tag %s, Path: %s" % (valueName, tagPath)
        system.tag.removeTag(tagPath)
    else:
        print "%s (%s) does not exist!" % (valueName, tagPath)
        
def deleteDcsLabValue(unitName, valueName):
    tagProvider = getTagProviderClient()
    path = "LabData/%s/DCS-Lab-Values" % (unitName)
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


def deleteLabSelector(unitName, valueName):
    tagProvider = getTagProviderClient()
    path = LAB_DATA_ROOT + "/" +  unitName
    parentPath = "[%s]%s" % (tagProvider, path) 
     
    tagPath = parentPath + "/" + valueName
    tagExists = system.tag.exists(tagPath)
    if tagExists:
        print "Deleting tag %s, Path: %s" % (valueName, tagPath)
        system.tag.removeTag(tagPath)
    else:
        print "%s (%s) does not exist!" % (valueName, tagPath)

    '''
    Delete the limit selector 
    '''
    for limitType in ["-SQC", "-RELEASE", "-VALIDITY"]:
        tagPath = parentPath + "/" + valueName +limitType
        tagExists = system.tag.exists(tagPath)
        if tagExists:
            print "Deleting tag %s, Path: %s" % (valueName, tagPath)
            system.tag.removeTag(tagPath)
        else:
            print "%s (%s) does not exist!" % (valueName, tagPath)


def synchronize(provider, unitName, repair):
    '''
    This synchronizes the Lab Data UDTs and the database.  This can be used on startup, after some tags have been edited or on demand.
    
    ---- THIS IS INCOMPLETE BUT IT IS A GREAT IDEA!!!  ALSO NEED TO VALIDATE THE DB - FINDING STRANDED DATA IN LTVALUE WITH NO CORRESPONDING RECORD IN PHD, DCS, OR LOCAL ---   
    '''

    def synchronizeLabValues(provider, unitName, repair, txt):
        log.infof("synchronizeLabValues")
        txt=append(txt, "     --- synchronizing lab value tags ---")
        
        # For values, it doesn't matter if it is PHD, DCS, or local.  They all use the same UDT
        SQL = "select V.ValueId, V.ValueName from LtValue V, TkUnit U where V.UnitId = U.UnitId and U.UnitName = '%s'" % (unitName)
        pds = system.db.runQuery(SQL)
        log.infof("fetched %d lab values from the DB...", len(pds))
        
        # Make a couple of lists to facilitate easy searches
        valueNames = []
        for record in pds:
            valueNames.append(record["ValueName"])
            
        parentPath="[" + provider + "]" + 'LabData/' + unitName
        udtType="Lab Data/Lab Value"
        log.tracef("Browsing %s for %s...", parentPath, udtType)
        tags = system.tag.browseTags(parentPath=parentPath, udtParentType=udtType, recursive=True)
        log.infof("...found %d UDTs...", len(tags))
        
        udtType="Lab Data/Lab Selector Value"
        log.tracef("Browsing %s for %s...", parentPath, udtType)
        selectors = system.tag.browseTags(parentPath=parentPath, udtParentType=udtType, recursive=True)
        log.infof("...found %d UDTs...", len(tags))
        
        # The database is the master list
        # The first phase is to look for UDTs that should be deleted because they do not exist in the database
        txt=append(txt, "Checking for tags to delete...")
        log.infof("Checking for tags to delete...")
        for tag in tags:
            log.tracef("...checking if UDT %s is needed...", tag.name)
            if tag.name not in valueNames:
                txt=append(txt, "   deleting %s" % (tag.fullPath))
                if repair:
                    system.tag.removeTag(tag.fullPath)
            else:
                valueNames.remove(tag.name)
        
        txt=append(txt,"Checking for selectors to delete...")
        log.infof("Checking for selectors to delete...")
        for tag in selectors:
            log.tracef("...checking if selector %s is needed...", tag.name)
            if tag.name not in valueNames:
                txt=append(txt,"   deleting %s" % (tag.fullPath))
                if repair:
                    system.tag.removeTag(tag.fullPath)
            else:
                valueNames.remove(tag.name)

        # The second phase is for UDTS that need to be created because a record exists in the database but not as a UDT
        
        txt=append(txt, "Checking for tags to create...")
        log.infof("Checking for tags to create...")
        #TODO somehow I need to figure out how to distinguish between a selector and a regular lab value here
        for valueName in valueNames:            
            UDTType='Lab Data/Lab Value'
            path = LAB_DATA_ROOT + "/" + unitName
            parentPath = "[" + provider + "]" + path  
            tagPath = parentPath + "/" + valueName
            tagExists = system.tag.exists(tagPath)
            if tagExists:
                print "  ", tagPath, " already exists!"
            else:
                txt=append(txt, "creating a %s, Name: %s, Path: %s" % (UDTType, valueName, tagPath))
                if repair:
                    system.tag.addTag(parentPath=parentPath, name=valueName, tagType="UDT_INST",  attributes={"UDTParentType":UDTType})
        
        return txt
                
    #----------------------------------------------------------
    def synchronizeLabLimits(provider, unitName, limitType, repair):

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
    
    log.infof("In %s.synchronize()", __name__)

    txt = ""
    txt = synchronizeLabValues(provider, unitName, repair, txt)
#    txt = synchronizeLabLimits(provider, unitName, "SQC", repair, txt)
#    txt = synchronizeLabLimits(provider, unitName, "Release", repair, txt)
#    txt = synchronizeLabLimits(provider, unitName, "Validity", repair, txt)

    log.infof("... leaving synchronize()")
    return txt

def updateLabValueUdt(unitName, dataType, labValueName, colName, newValue):
    log.infof("Updating lab value UDT for %s - %s, a %s", unitName, labValueName, dataType)
    tagProvider = getTagProviderClient()
    
    if colName == "ValueName":
        print "Renaming a Lab Data UDT"
        tagPath = "[%s]%s/%s/%s" % (tagProvider, LAB_DATA_ROOT, unitName, labValueName)
        if system.tag.exists(tagPath):
            system.tag.editTag(tagPath=tagPath, attributes={"Name": newValue})
        else:
            system.gui.warningBox("Error renaming Lab Data UDT <%s> for %s" % (tagPath, labValueName))

        if dataType == "DCS":
            tagPath = "[%s]%s/%s/DCS-Lab-Values/%s" % (tagProvider, LAB_DATA_ROOT, unitName, labValueName)
            if system.tag.exists(tagPath):
                system.tag.editTag(tagPath=tagPath, attributes={"Name": newValue})
            else:
                system.gui.warningBox("Error renaming Lab Data OPC tag for a DCS lab value <%s> for %s" % (tagPath, labValueName))
    
    elif colName == "ItemId":
        ''' Update the item id for the OPC tag for a DCS lab value '''
        if dataType == "DCS":
            tagPath = "[%s]%s/%s/DCS-Lab-Values/%s" % (tagProvider, LAB_DATA_ROOT, unitName, labValueName)
            if system.tag.exists(tagPath):
                system.tag.editTag(tagPath=tagPath, attributes={"OPCItemPath": newValue})
            else:
                system.gui.warningBox("Error updating the itemId for the OPC tag for a DCS lab value <%s> for %s" % (tagPath, labValueName))
                
    elif colName == "InterfaceName":
        ''' Update the OPC interface for the OPC tag for a DCS lab value '''
        if dataType == "DCS":
            tagPath = "[%s]%s/%s/DCS-Lab-Values/%s" % (tagProvider, LAB_DATA_ROOT, unitName, labValueName)
            if system.tag.exists(tagPath):
                system.tag.editTag(tagPath=tagPath, attributes={"OPCServer": newValue})
            else:
                system.gui.warningBox("Error updating the itemId for the OPC tag for a DCS lab value <%s> for %s" % (tagPath, labValueName))
    
    else:
        print "Unsupported column name: ", colName
            