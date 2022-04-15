'''
Created on Jan 8, 2021

@author: phass
'''
import system, sys, traceback, time
from ils.io.util import getTagExpression, getTagSQL, getUDTType, getTagScript, readTag, writeTag, isFolder, stripProvider
from ils.common.cast import listToDataset 

COMMAND_TAG_PATH = "[Client]Replicate/Command"
DESTINATION_TAG_PROVIDER_TAG_PATH = "[Client]Replicate/Destination Tag Provider"
DUMP_TAGS_TAG_PATH = "[Client]Replicate/Dump Tags"
SELECTED_TAG_PATH_TAG_PATH = "[Client]Replicate/Selected Tag Path"
STATUS_TAG_PATH = "[Client]Replicate/Status"
TAG_COUNTER_TAG_PATH = "[Client]Replicate/Tag Counter"
TOTAL_TAG_COUNT_TAG_PATH = "[Client]Replicate/Total Tag Count"
REPLACE_EXPRESSION_TAGS_TAG_PATH = "[Client]Replicate/Replace Expression Tags"
REPLACE_QUERY_TAGS_TAG_PATH = "[Client]Replicate/Replace Query Tags"

ABORT_COMMAND = "Abort"
log = system.util.getLogger(__name__)

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()", __name__)
    projectName = system.util.getProjectName()
    messageHandler = "getTagProviders"
    tagProviders = system.util.sendRequest(projectName, messageHandler, scope = "G")
    tagProviders.remove("System")
    ds = listToDataset(tagProviders)
    ds = system.dataset.sort(ds, 0)
    rootContainer.TagProviders = ds
    rootContainer.ShowPreferences = False
    
    reset()
    
def abortCallback(event):
    writeTag(COMMAND_TAG_PATH, ABORT_COMMAND)

def resetCallback(event):
    reset()
    
def reset():
    log.infof("In %s.reset()", __name__)
    writeTag(COMMAND_TAG_PATH, "")
    writeTag(STATUS_TAG_PATH, "")
    writeTag(TOTAL_TAG_COUNT_TAG_PATH, 0)
    writeTag(TAG_COUNTER_TAG_PATH, 0)
    
def replicateCallback(event):
    rootContainer = event.source.parent
    
    okToProceed, sourceTagProvider, destinationTagProvider, sourceTagTree, selectedTagPath = checkSelections(rootContainer)
    if not(okToProceed):
        return
    
    writeTag(SELECTED_TAG_PATH_TAG_PATH, selectedTagPath)
    writeTag(DESTINATION_TAG_PROVIDER_TAG_PATH, destinationTagProvider)
    writeTag(COMMAND_TAG_PATH, "Replicate")
        
def copyDataCallback(event):
    rootContainer = event.source.parent
    
    okToProceed, sourceTagProvider, destinationTagProvider, sourceTagTree, selectedTagPath = checkSelections(rootContainer)
    if not(okToProceed):
        return
    
    writeTag(SELECTED_TAG_PATH_TAG_PATH, selectedTagPath)
    writeTag(DESTINATION_TAG_PROVIDER_TAG_PATH, destinationTagProvider)
    writeTag(COMMAND_TAG_PATH, "CopyValues")
    
def convertUdtCallback(event):
    '''
    This is a small utility function that can be used to help convert a production UDT to an isolation UDT.
    It replaces OPC tags with memory tags and leaves everything else intact.
    '''
    container = event.source.parent
    filename = container.getComponent("Filename Field").text
    if not(system.file.fileExists(filename)):
        system.gui.warningBox("File (%s) does not exist - please select another file." % (filename))
        return
    print "Converting ..."
    
    txt = system.file.readFileAsString(filename)
    txt = txt.replace('type="OPC"', 'type="DB"')
    newFilename = filename[:len(filename)-4] + "_isolation.xml"
    system.file.writeFile(newFilename, txt)
    
    system.gui.messageBox("<HTML>The modified UDT has been written to <b>%s</b><br>Using Designer, import it into the Data Types folder for the Isolation tag provider." % (newFilename))

def checkSelections(rootContainer):
    sourceTagProvider = rootContainer.getComponent("Source Container").getComponent("Tag Provider Dropdown").selectedStringValue
    if sourceTagProvider == "":
        system.gui.messageBox("<HTML>Please select a <b>SOURCE</b> tag provider from the dropdown.")
        return False, None, None, None, None
    
    destinationTagProvider = rootContainer.getComponent("Destination Container").getComponent("Tag Provider Dropdown").selectedStringValue
    if destinationTagProvider == "":
        system.gui.messageBox("<HTML>Please select a <b>DESTINATION</b> tag provider from the dropdown.")
        return False, None, None, None, None
    
    if sourceTagProvider == destinationTagProvider:
        system.gui.messageBox("<HTML>The source and destination tag providers must be different!")
        return False, None, None, None, None
    
    sourceTagTree = rootContainer.getComponent("Source Container").getComponent("Tag Browse Tree")
    ds = sourceTagTree.selectedPaths
    if ds.getRowCount() == 0:
        system.gui.messageBox("Please select a <b>SOURCE</b> tag/folder from the tree.")
        return False, None, None, None, None
    
    selectedTagPath = ds.getValueAt(0,0)
    if selectedTagPath in ["", None]:
        system.gui.messageBox("Please select a <b>SOURCE</b> tag/folder from the tree.")
        return False, None, None, None, None
        
    return True, sourceTagProvider, destinationTagProvider, sourceTagTree, selectedTagPath

def commandTagCallback(tagPath, previousValue, currentValue, initialChange, missedEvents):
    if initialChange:
        return
    
    try:
        if currentValue.value == "Replicate":
            writeTag(STATUS_TAG_PATH, "Starting to replicate...")
            replicator = Replicater()            
            replicator.replicate()
            replicator.copyValues()
            time.sleep(1)
            writeTag(STATUS_TAG_PATH, "Done - Successfully replicated tags and copied tag values!")
            
        if currentValue.value == "CopyValues":
            writeTag(STATUS_TAG_PATH, "Starting to copy values...")
            replicator = Replicater()
            replicator.copyValues()
            time.sleep(1)
            writeTag(STATUS_TAG_PATH, "Done - Successfully copied tag values!")
            
    except Exception, e:
        print sys.exc_info()[1]
        try:
            print traceback.format_exc()
        except:
            pass
        
        system.gui.messageBox(str(e))
        
def updateStatus(txt):
    writeTag(STATUS_TAG_PATH, txt)

class Replicater():
    selectedTagPath = None
    sourceTagProvider = None
    destinationTagProvider = None
    replaceExpressionTags = None
    replaceQueryTags = None
    myTags = None
    log = None
    
    def __init__(self):
        from ils.log import getLogger
        self.log = getLogger(__name__)
        self.log.infof("Initializing a Replicator")
        
        self.selectedTagPath = readTag(SELECTED_TAG_PATH_TAG_PATH).value
        self.destinationTagProvider = readTag(DESTINATION_TAG_PROVIDER_TAG_PATH).value
        self.replaceExpressionTags = readTag(REPLACE_EXPRESSION_TAGS_TAG_PATH).value
        self.replaceQueryTags = readTag(REPLACE_QUERY_TAGS_TAG_PATH).value

        ''' Derive the source tag provider from the selectedTagPath '''
        self.sourceTagProvider = self.selectedTagPath[1:self.selectedTagPath.find("]")]
        
        self.log.tracef("Replace Expression Tags: %s", str(self.replaceExpressionTags))
        self.log.tracef("Replace Query Tags: %s", str(self.replaceQueryTags))
        
        writeTag(STATUS_TAG_PATH, "Step #1 - Browsing tags...")
        self.myTags = self.getTags(self.selectedTagPath)
        
        ''' Count the number of tags and UDTs to drive the progress bar. '''
        i = 0
        for browseTag in self.myTags.getResults():
            if not(browseTag['tagType'] == "Folder"):
                i = i + 1
                
        writeTag(TOTAL_TAG_COUNT_TAG_PATH, i)
        self.log.infof("Found %d UDTs & Tags...", i)
        
        ''' There is a client tag that optionally turns on the tag dump. It can swamp the console log if it is turned on. '''
        dumpTags = readTag(DUMP_TAGS_TAG_PATH).value
        if dumpTags:
            self.dumpTags()
            
    def getTags(self, initPath):
        self.log.tracef("Browsing %s", initPath)
        
        '''
        Need to be able to handle selection of a single tag/udt, a folder, or the tag provider
        '''
        self.log.tracef("Determining what %s is...", initPath)
        if len(initPath) == initPath.rfind(']') + 1:
            self.log.tracef("Browsing the tag provider")
            tagSet = system.tag.browse(initPath, {"recursive": True})
        else:            
            isaFolder = isFolder(initPath)
            if isaFolder:
                self.log.tracef("Browsing a folder: %s", initPath)
                tagSet = system.tag.browse(initPath, {"recursive": True})
            else:
                self.log.tracef("%s is NOT a Folder", initPath)
                ''' A tag in the root directory is a little different than a tag in a folder '''
                if initPath.rfind('/') < 0:
                    parentPath = initPath[:initPath.rfind(']')+1]
                    tagName = '*' + initPath[initPath.rfind(']')+1:]
                else:
                    parentPath = initPath[:initPath.rfind('/')]
                    tagName = initPath[initPath.rfind('/')+1:]
                self.log.tracef("Browsing parent: %s, tag name: %s", parentPath, tagName)
                tagSet = system.tag.browse(parentPath, {"recursive": False, "name": tagName})
                
        return tagSet
        
    def replicate(self):
        '''
        Depending on how many tags are selected, this could take a looong time to run.  If this is run in the main UI thread it
        will freeze the UI.  It will work when run in the ui thread but is is designed to be called from an event script on a client tag.
        (Event scripts on client tags run in the client, not the gateway like other tag event scripts.)
        
        Create the tags, we don't need to explicitly create folders, they will be created automatically as we go 
        '''
        command = readTag(COMMAND_TAG_PATH).value
        if command == ABORT_COMMAND:
            return
        writeTag(STATUS_TAG_PATH, "Step #2 - Creating tags...")
        self.log.tracef("*******************")
        self.log.infof("Replicating tags...")
        self.log.tracef("*******************")
        i = 0
        
        for browseTag in self.myTags:
            log.tracef("Replicating %s...", browseTag['fullPath'])
            command = readTag(COMMAND_TAG_PATH).value
            if command == ABORT_COMMAND:
                updateStatus("Aborted tag replicate!")
                return
            
            tagType = str(browseTag['tagType'])
            if tagType != "Folder":
                i = i + 1
                writeTag(TAG_COUNTER_TAG_PATH, i)
                self.log.tracef("%s", browseTag['fullPath'])
                
                sourceTagPath = str(browseTag['fullPath'])
                tagName = str(browseTag['name'])
                
                ''' Strip off the provider '''
                tagPath = stripProvider(sourceTagPath)
                
                ''' Handle an atomic tag at the root level '''
                if tagPath.find("/") >= 0:
                    tagPath = tagPath[:tagPath.rfind("/")]
                else:
                    tagPath = ""
                    
                destinationTagPath = "[%s]%s" % (self.destinationTagProvider, tagPath)
                
                self.log.tracef("Checking if <%s/%s> already exists", destinationTagPath, tagName)
                if not(system.tag.exists(destinationTagPath + "/" + tagName)):
                    tagType = str(browseTag['tagType'])
                    self.log.tracef("%s is a %s (%s)!", sourceTagPath, tagType, str(browseTag))
                        
                    if tagType == "UdtInstance":
                        '''
                        Ignition is smart enough to use the Isolation UDT for the Isolation tag provider.  This will work as long as we have a parallel 
                        set of UDTs.  Note that the tag provider is not part of the UDT name anyway, so we don't need to replace the tag provider with 
                        the isolation tag provider in the UDT name. 
                        '''
                        udtType = str(browseTag['typeId'])
                        self.log.tracef("...creating a <%s> UDT for %s", udtType, sourceTagPath)
                        try:
                            tag = {
                                   "name": tagName,
                                   "typeId": udtType,
                                   "tagType": tagType
                                   }
                            system.tag.configure(destinationTagPath, [tag])
                        except:
                            print "Error: the <%s> UDT does not exist in the Destination tag provider."
                    
                    else:
                        dataType = browseTag['dataType']
                        valueSource = str(browseTag['valueSource'])
                        if valueSource == "expr":
                            if self.replaceExpressionTags:
                                self.log.tracef("...creating a memory tag %s in %s to replace an expression tag", tagName, destinationTagPath)
                                self.createMemoryTag(sourceTagPath, destinationTagPath, tagName, dataType)
                            else:
                                self.log.tracef("...creating an expression tag %s in %s", tagName, tagName)
                                self.createExpressionTag(sourceTagPath, destinationTagPath, tagName, dataType)
    
                        elif valueSource == "db":
                            if self.replaceQueryTags:
                                self.log.tracef("...creating a memory tag %s in %s to replace a query tag", tagName, destinationTagPath)
                                self.createMemoryTag(sourceTagPath, destinationTagPath, tagName, dataType)
                            else:
                                self.log.tracef("...creating a query tag %s in %s", tagName, destinationTagPath)
                                self.createQueryTag(sourceTagPath, destinationTagPath, tagName, dataType)
    
                        elif valueSource in ["opc", "memory"]:
                            self.log.tracef("...creating memory tag %s in %s", tagName, destinationTagPath)
                            self.createMemoryTag(sourceTagPath, destinationTagPath, tagName, dataType)
                        
                        elif valueSource in ["derived", "reference"]:
                            self.log.tracef("...creating a memory tag %s in %s to replace a %s tag!", tagName, browseTag.path, valueSource)
                            self.createMemoryTag(sourceTagPath, destinationTagPath, tagName, dataType)
            
                        else:
                            self.log.warnf("Unexpected tag type: %s for %s", valueSource, sourceTagPath)
                        
                else:
                    self.log.tracef("...already exists")
    
    def createMemoryTag(self, sourceTagPath, basePath, tagName, dataType):
        tagScript = getTagScript(sourceTagPath)
        tag = {'tagType': 'AtomicTag', 
            'name': tagName, 
            'dataType': dataType,
            'eventScripts': tagScript, 
            'valueSource': 'memory'
        }
        system.tag.configure(basePath, [tag])
        
    def createExpressionTag(self, sourceTagPath, basePath, tagName, dataType):
        tagScript = getTagScript(sourceTagPath)
        expression = getTagExpression(sourceTagPath)
        if expression != None:
            expression = expression.replace(self.sourceTagProvider, self.destinationTagProvider)
        tag = {'tagType': 'AtomicTag', 
            'name': tagName, 
            'dataType': dataType,
            'expression': expression,
            'eventScripts': tagScript, 
            'valueSource': 'memory'
        }
        system.tag.configure(basePath, [tag])
    
    def createQueryTag(self, sourceTagPath, basePath, tagName, dataType):
        ''' TODO I should switch the datasource here to teh isolation database, which assumes we are going from production to isolation '''
        tagScript = getTagScript(sourceTagPath)
        SQL = getTagSQL(sourceTagPath)

        tag = {'tagType': 'AtomicTag', 
            'name': tagName, 
            'dataType': dataType,
            'query': SQL,
            'eventScripts': tagScript, 
            'valueSource': 'memory'
        }
        system.tag.configure(basePath, [tag])

    def copyValues(self):
        ''' Copy tag values '''
        command = readTag(COMMAND_TAG_PATH).value
        if command == ABORT_COMMAND:
            return
        writeTag(STATUS_TAG_PATH, "Step #3 - Copying tag values...")
        self.log.tracef("*******************")
        self.log.infof("Copying tag values")
        self.log.tracef("*******************")
        i = 0
        for browseTag in self.myTags:
            command = readTag(COMMAND_TAG_PATH).value
            if command == ABORT_COMMAND:
                updateStatus("Aborted tag value copy!")
                return

            tagType = str(browseTag['tagType'])
            self.log.tracef("%s - %s - %s", browseTag['fullPath'], tagType, str(browseTag))
    
            if tagType != "Folder":
                i = i + 1
                writeTag(TAG_COUNTER_TAG_PATH, i)
 
                if tagType in ["AtomicTag"]:
                    self.log.tracef("Copying a tag...")
                    self.copyTagValues(browseTag, False)
                
                elif tagType in ["UdtInstance"]:
                    self.log.tracef("Copying a UDT...")
                    self.copyUdtProperties(browseTag['fullPath'], browseTag['name'])
                    self.copyUdtValues(str(browseTag['fullPath']))
                
                else:
                    self.log.warnf("Unexpected tag type for tag: %s, type: %s", browseTag['fullPath'], tagType)
                    
    def copyTagValues(self, browseTag, isUdtMember):
        '''
        This should only be called for atomic tags.  The target tag should already exist or we wouldn't have
        gotten this far. 
        '''
        sourceDataType = browseTag['dataType']
        valueSource = str(browseTag['valueSource'])
        sourceTagPath = str(browseTag['fullPath'])
        tagPath = stripProvider(str(browseTag['fullPath']))
        tagName = browseTag['name']
        targetTagPath = "[%s]%s" % (self.destinationTagProvider, tagPath)
        log.tracef("Copying values from %s to %s, a %s...", browseTag['fullPath'], targetTagPath, valueSource)
        
        ''' Get the value source and datatyoe of the target type '''
        configs = system.tag.getConfiguration(targetTagPath)
        tagDict = configs[0]
        
        targetDataType = tagDict.get("dataType", None)
        targetValueSource = tagDict.get("valueSource", None)
        self.log.tracef("Comparing %s (%s, %s) to %s (%s, %s)", str(browseTag['fullPath']), valueSource, sourceDataType, targetTagPath, targetValueSource, targetDataType)
        
        ''' It is a little different to change the data type of a stand alone tag versus a tag embedded in a UDT.
        I have noticed that when changing the datatype that the copy that happens a few lines down sometimes may not take.  
        Running copy a second time will fix it because the data type is only changed the first time through. '''
        if sourceDataType != targetDataType:
            self.log.infof("The source and target data type do not match...")
            if isUdtMember:
                self.log.infof("Converting %s (a member of a UDT) from %s to %s", targetTagPath, targetDataType, sourceDataType)
                config = system.tag.getConfiguration(targetTagPath)[0]
                config['dataType'] = sourceDataType
                basePath = targetTagPath[:targetTagPath.find(tagName)]
                system.tag.configure(basePath, [config])
            else:
                self.log.infof("Converting %s (a stand alone tag) from %s to %s", targetTagPath, targetDataType, sourceDataType)
                config = system.tag.getConfiguration(targetTagPath)[0]
                config['dataType'] = sourceDataType
                basePath = targetTagPath[:targetTagPath.find(tagName)]
                system.tag.configure(basePath, [config])
        
        ''' Now copy the values '''
        if valueSource == "expr" and not(self.replaceExpressionTags):
            self.log.tracef("--- Skipping an expression tag ---")
        elif valueSource == "db" and not(self.replaceQueryTags):
            self.log.tracef("--- Skipping a query tag ---")
        else:
            qv = readTag(sourceTagPath)
            if qv.quality.isGood():
                writeTag(targetTagPath, qv.value)
                    
    def copyUdtValues(self, tagPath):
        '''
        The browse function doesn't dig into UDTs, but when we copy values we need to recursively dig into the UDT.
        The original browse does navigate into folders so we don't need to treat them.
        '''
        self.log.tracef("Copy UDT values for %s", tagPath)
        
        results = system.tag.browse(tagPath, {"recursive": False})
    
        for browseTag in results.getResults():
            self.log.tracef("Path: %s", browseTag['fullPath'])
            self.log.tracef("Tag Type: %s", str(browseTag['tagType']))
            self.log.tracef("----------")
            
            if str(browseTag['tagType']) in ["UdtInstance"]:
                self.copyUdtValues(str(browseTag['fullPath']))
            else:
                self.copyTagValues(browseTag, True)
                    
        self.log.tracef("...done with the UDT copy!")
        
        
    def copyUdtProperties(self, sourceTagPath, tagName):
        '''
        The check has already been done, the tagPath IS a UDT instance.
        '''
        self.log.tracef("Copy properties for %s (tagName: %s)", sourceTagPath, tagName)
        tagPath = stripProvider(str(sourceTagPath))
        targetTagPath = "[%s]%s" % (self.destinationTagProvider, tagPath)
        
        ''' Read the UDT properties from the source tag'''
        sourceConfig = system.tag.getConfiguration(sourceTagPath)[0]
        udtProperties = sourceConfig.get("parameters", None)
        
        ''' Update the target UDT with the properties from the source UDT '''
        targetConfig = system.tag.getConfiguration(targetTagPath)[0]
        targetConfig["parameters"] = udtProperties
        baseTagPath = targetTagPath[:targetTagPath.find(tagName)]
        system.tag.configure(baseTagPath, targetConfig)
                     
        self.log.tracef("...done with the UDT property copy!")

    def dumpTags(self):        
        for browseTag in self.myTags:
            print "Name: ", browseTag.name
            print "Path: ", browseTag.path
            print "Fullpath: ", browseTag.fullPath
            print "UDT: ", browseTag.isUDT()
            if browseTag.isUDT():
                udtType = getUDTType(browseTag.fullPath)
                print "UDT Type: ", udtType
            print "Type: ", browseTag.type
            print "Datatype: ", browseTag.dataType
            print "-----------------"    