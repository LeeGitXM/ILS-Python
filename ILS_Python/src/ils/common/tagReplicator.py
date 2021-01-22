'''
Created on Jan 8, 2021

@author: phass
'''
import system, sys, traceback, time
from ils.tag.client import typeForTagPath, dataTypeForTagPath
from ils.io.util import getTagExpression, getTagSQL, getUDTType, isExpressionTag, isQueryTag, getTagScript

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

def internalFrameOpened(rootContainer):
    projectName = system.util.getProjectName()
    messageHandler = "getTagProviders"
    tagProviders = system.util.sendRequest(projectName, messageHandler, scope = "G")
    data = []
    for tagProvider in tagProviders:
        if tagProvider != "System":
            data.append([tagProvider])
    ds = system.dataset.toDataSet(["TagProvider"], data)
    ds = system.dataset.sort(ds, 0)
    rootContainer.TagProviders = ds
    rootContainer.ShowPreferences = False
    reset()
    
def abortCallback(event):
    system.tag.write(COMMAND_TAG_PATH, ABORT_COMMAND)

def resetCallback(event):
    reset()
    
def reset():
    system.tag.write(COMMAND_TAG_PATH, "")
    system.tag.write(STATUS_TAG_PATH, "")
    system.tag.write(TOTAL_TAG_COUNT_TAG_PATH, 0)
    system.tag.write(TAG_COUNTER_TAG_PATH, 0)
    
def replicateCallback(event):
    rootContainer = event.source.parent
    
    okToProceed, sourceTagProvider, destinationTagProvider, sourceTagTree, selectedTagPath = checkSelections(rootContainer)
    if not(okToProceed):
        return
    
    system.tag.write(SELECTED_TAG_PATH_TAG_PATH, selectedTagPath)
    system.tag.write(DESTINATION_TAG_PROVIDER_TAG_PATH, destinationTagProvider)
    system.tag.write(COMMAND_TAG_PATH, "Replicate")
        
def copyDataCallback(event):
    rootContainer = event.source.parent
    
    okToProceed, sourceTagProvider, destinationTagProvider, sourceTagTree, selectedTagPath = checkSelections(rootContainer)
    if not(okToProceed):
        return
    
    system.tag.write(SELECTED_TAG_PATH_TAG_PATH, selectedTagPath)
    system.tag.write(DESTINATION_TAG_PROVIDER_TAG_PATH, destinationTagProvider)
    system.tag.write(COMMAND_TAG_PATH, "CopyValues")
    
def convertUdtCallback(event):
    '''
    This is a small utility function that can be used to heklp convert a production UDT to an isolation UDT.
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
        return False, None, None, None
    
    destinationTagProvider = rootContainer.getComponent("Destination Container").getComponent("Tag Provider Dropdown").selectedStringValue
    if destinationTagProvider == "":
        system.gui.messageBox("<HTML>Please select a <b>DESTINATION</b> tag provider from the dropdown.")
        return False, None, None, None
    
    if sourceTagProvider == destinationTagProvider:
        system.gui.messageBox("<HTML>The source and destination tag providers must be different!")
        return False, None, None, None
    
    sourceTagTree = rootContainer.getComponent("Source Container").getComponent("Tag Browse Tree")
    ds = sourceTagTree.selectedPaths
    if ds.getRowCount() == 0:
        system.gui.messageBox("Please select a tag/folder from the tree.")
        return False, None, None, None
    
    selectedTagPath = ds.getValueAt(0,0)
    if selectedTagPath in ["", None]:
        system.gui.messageBox("Please select a tag/folder from the tree.")
        return False, None, None, None
        
    return True, sourceTagProvider, destinationTagProvider, sourceTagTree, selectedTagPath

def commandTagCallback(tagPath, previousValue, currentValue, initialChange, missedEvents):
    if initialChange:
        return
    
    try:
        if currentValue.value == "Replicate":
            system.tag.write(STATUS_TAG_PATH, "Starting to replicate...")
            replicator = Replicater()            
            replicator.replicate()
            replicator.copyValues()
            time.sleep(1)
            system.tag.write(STATUS_TAG_PATH, "Done - Successfully replicated tags and copied tag values!")
            
        if currentValue.value == "CopyValues":
            system.tag.write(STATUS_TAG_PATH, "Starting to copy values...")
            replicator = Replicater()
            replicator.copyValues()
            time.sleep(1)
            system.tag.write(STATUS_TAG_PATH, "Done - Successfully copied tag values!")
            
    except Exception, e:
        print sys.exc_info()[1]
        try:
            print traceback.format_exc()
        except:
            pass
        
        system.gui.messageBox(str(e))
        
def updateStatus(txt):
    system.tag.write(STATUS_TAG_PATH, txt)

class Replicater():
    selectedTagPath = None
    sourceTagProvider = None
    destinationTagProvider = None
    replaceExpressionTags = None
    replaceQueryTags = None
    myTags = None
    log = None
    
    def __init__(self):
        self.log = system.util.getLogger(__name__)
        self.log.infof("Initializing a Replicator")
        
        self.selectedTagPath = system.tag.read(SELECTED_TAG_PATH_TAG_PATH).value
        self.destinationTagProvider = system.tag.read(DESTINATION_TAG_PROVIDER_TAG_PATH).value
        self.replaceExpressionTags = system.tag.read(REPLACE_EXPRESSION_TAGS_TAG_PATH).value
        self.replaceQueryTags = system.tag.read(REPLACE_QUERY_TAGS_TAG_PATH).value

        ''' Derive the source tag provider from the selectedTagPath '''
        self.sourceTagProvider = self.selectedTagPath[1:self.selectedTagPath.find("]")]
        print "The source tag provider is <%s>" % (self.sourceTagProvider)
        print "The destination tag provider is <%s>" % (self.destinationTagProvider)
        
        
        self.log.tracef("Replace Expression Tags: %s", str(self.replaceExpressionTags))
        self.log.tracef("Replace Query Tags: %s", str(self.replaceQueryTags))
        
        system.tag.write(STATUS_TAG_PATH, "Step #1 - Browsing tags...")
        self.myTags = self.getTags(self.selectedTagPath)
        
        ''' Count the number of tags and UDTs to drive the progress bar. '''
        i = 0
        for browseTag in self.myTags:
            if not(browseTag.isFolder()):
                i = i + 1
        system.tag.write(TOTAL_TAG_COUNT_TAG_PATH, i)
        self.log.infof("Found %d UDTs & Tags...", i)
        
        ''' There is a client tag that optionally turns on the tag dump. It can swamp the console log if it is turned on. '''
        dumpTags = system.tag.read(DUMP_TAGS_TAG_PATH).value
        if dumpTags:
            self.dumpTags()
            
    def getTags(self, initPath):
        '''
        We do not want to use the built in recursive flag because it will treat UDTs as folders.
        The idea here is that we have a parallel set of UDTs
        '''
        self.log.tracef("Browsing %s", initPath)
        
        '''
        Need to be able to handle selection of a single tag/udt, a folder, or the tag provider
        '''
        self.log.tracef("Determining what %s is...", initPath)
        if len(initPath) == initPath.rfind(']') + 1:
            self.log.tracef("Browsing the tag provider")
            tagSet = self.myBrowse(initPath)
        else:
            tagType = typeForTagPath(initPath)
            self.log.tracef("%s is a %s", initPath, tagType)
            if tagType == 'Folder':
                tagSet = self.myBrowse(initPath)
            else:
                ''' A tag in the root directory is a little different than a tag in a folder '''
                if initPath.rfind('/') < 0:
                    parentPath = initPath[:initPath.rfind(']')+1]
                    tagName = '*' + initPath[initPath.rfind(']')+1:]
                else:
                    parentPath = initPath[:initPath.rfind('/')]
                    tagName = '*' + initPath[initPath.rfind('/')+1:]
                tagSet = system.tag.browseTags(parentPath=parentPath, tagPath=tagName, recursive=False)
                
        return tagSet
        
    def myBrowse(self, initPath):
        '''
        We do not want to use the built in recursive flag because it will treat UDTs as folders.
        The idea here is that we have a parallel set of UDTs
        '''
        self.log.tracef("Browsing %s", initPath)

        tagSet = system.tag.browseTags(parentPath=initPath, recursive=False)
        folderSet = system.tag.browseTags(parentPath=initPath, tagType = 'Folder', recursive=False)
    
        for folder in folderSet:
            command = system.tag.read(COMMAND_TAG_PATH).value
            if command == ABORT_COMMAND:
                updateStatus("Aborted tag browse!")
                return tagSet
            tagSet+=self.myBrowse(folder.fullPath)
        
        return tagSet
    
    def replicate(self):
        '''
        Depending on how many tags are selected, this could take a looong time to run.  If this is run in the main UI thread it
        will freeze the UI.  It will work when run in the ui thread but is is designed to be called from an event script on a client tag.
        (Event scripts on client tags run in the client, not the gateway like other tag event scripts.)
        
        Create the tags, we don't need to explicitly create folders, they will be created automatically as we go 
        '''
        command = system.tag.read(COMMAND_TAG_PATH).value
        if command == ABORT_COMMAND:
            return
        system.tag.write(STATUS_TAG_PATH, "Step #2 - Creating tags...")
        self.log.tracef("*******************")
        self.log.infof("Replicating tags...")
        self.log.tracef("*******************")
        i = 0
        
        for browseTag in self.myTags:
            command = system.tag.read(COMMAND_TAG_PATH).value
            if command == ABORT_COMMAND:
                updateStatus("Aborted tag replicate!")
                return
            
            if not(browseTag.isFolder()):
                i = i + 1
                system.tag.write(TAG_COUNTER_TAG_PATH, i)
                self.log.tracef(browseTag.fullPath)
                
                tagpath = browseTag.path
                if tagpath.find("/") >= 0:
                    tagpath = tagpath[:tagpath.rfind("/")]
                else:
                    tagpath = tagpath[:tagpath.rfind("]")+1]
                tagpath = "[%s]%s" % (self.destinationTagProvider, tagpath)
                
                self.log.tracef("Checking if <%s/%s> already exists", tagpath, browseTag.name)
                if not(system.tag.exists(tagpath + "/" + browseTag.name)):
                    
                    tagType = typeForTagPath(browseTag.fullPath)
                    self.log.tracef("%s is a %s", browseTag.fullPath, tagType)
                    
                    tagScript = getTagScript(browseTag.fullPath)
                        
                    if isExpressionTag(browseTag.fullPath):
                        if self.replaceExpressionTags:
                            self.log.tracef("...creating a memory tag %s in %s to replace an expression tag", browseTag.name, browseTag.path)
                            system.tag.addTag(parentPath=tagpath, name=browseTag.name, tagType="MEMORY", dataType=browseTag.dataType,
                                              attributes={"EventScripts":tagScript})
                        else:
                            expression = getTagExpression(browseTag.fullPath)
                            expression = expression.replace(self.sourceTagProvider, self.destinationTagProvider)
                            print "The updated expression is: ", expression
                            self.log.tracef("...creating an expression tag %s in %s with expression: %s", browseTag.name, browseTag.path, expression)
                            system.tag.addTag(parentPath=tagpath, name=browseTag.name, tagType="EXPRESSION", dataType=browseTag.dataType,
                                              attributes={"Expression": expression, "EventScripts":tagScript})

                    elif isQueryTag(browseTag.fullPath):
                        if self.replaceQueryTags:
                            self.log.tracef("...creating a memory tag %s in %s to replace a query tag", browseTag.name, browseTag.path)
                            system.tag.addTag(parentPath=tagpath, name=browseTag.name, tagType="MEMORY", dataType=browseTag.dataType,
                                            attributes={"EventScripts":tagScript})
                        else:
                            SQL = getTagSQL(browseTag.fullPath)
                            self.log.tracef("...creating a query tag %s in %s with SQL: %s", browseTag.name, browseTag.path, SQL)
                            system.tag.addTag(parentPath=tagpath, name=browseTag.name, tagType="QUERY", dataType=browseTag.dataType,
                                              attributes={"Expression": SQL, "EventScripts":tagScript})

                    elif str(browseTag.type) in ["OPC", "DB"]:
                        self.log.tracef("...creating memory tag %s in %s", browseTag.name, browseTag.path)
                        system.tag.addTag(parentPath=tagpath, name=browseTag.name, tagType="MEMORY", dataType=browseTag.dataType,
                                          attributes={"EventScripts":tagScript})
                    
                    elif str(browseTag.type) in ["DERIVED"]:
                        '''
                        self.log.tracef("...creating a derived tag %s in %s", browseTag.name, browseTag.path)
                        expression = getTagExpression(browseTag.fullPath)
                        print "...derived expression: ", expression
                        system.tag.addTag(parentPath=tagpath, name=browseTag.name, tagType="DERIVED", dataType=browseTag.dataType,
                                          attributes={"EventScripts":tagScript})
                        '''
                        self.log.tracef("...creating a memory tag %s in %s to replace a derived tag!", browseTag.name, browseTag.path)
                        system.tag.addTag(parentPath=tagpath, name=browseTag.name, tagType="MEMORY", dataType=browseTag.dataType,
                                          attributes={"EventScripts":tagScript})
        
                    elif str(browseTag.type) == "UDT_INST":
                        '''
                        Ignition is smart enough too use the Isolation UDT for the Isolation tag provider.  This will work as long as we have a parallel 
                        set of UDTs.  Note that the tag provider is not part of the UDT name anyway, so we don't need to replace the tag provider with 
                        the isolation tag provider in the UDT name. 
                        '''
                        udtType = getUDTType(browseTag.fullPath)
                        self.log.tracef("...creating a %s UDT for %s", udtType, browseTag.fullPath)
                        try:
                            system.tag.addTag(parentPath=tagpath, name=browseTag.name, tagType="UDT_INST", attributes={"UDTParentType":udtType})
                        except:
                            print "Error: the <%s> UDT does not exist in the Destination tag provider."
        
                    else:
                        self.log.warnf("Unexpected tag type: %s for %s", browseTag.type, browseTag.fullPath)
                        
                else:
                    self.log.tracef("...already exists")
                
    def copyValues(self):
        ''' Copy tag values '''
        command = system.tag.read(COMMAND_TAG_PATH).value
        if command == ABORT_COMMAND:
            return
        system.tag.write(STATUS_TAG_PATH, "Step #3 - Copying tag values...")
        self.log.tracef("*******************")
        self.log.infof("Copying tag values")
        self.log.tracef("*******************")
        i = 0
        for browseTag in self.myTags:
            command = system.tag.read(COMMAND_TAG_PATH).value
            if command == ABORT_COMMAND:
                updateStatus("Aborted tag value copy!")
                return

            self.log.tracef(browseTag.fullPath)
            if not(browseTag.isFolder()):
                i = i + 1
                system.tag.write(TAG_COUNTER_TAG_PATH, i)
                
                if str(browseTag.type) in ["OPC", "DB", "DERIVED"]:
                    self.log.tracef("Copying a tag...")
                    self.copyTagValues(browseTag, False)
                
                elif str(browseTag.type) in ["UDT_INST"]:
                    self.log.tracef("Copying a UDT...")
                    self.copyUdtValues(browseTag.fullPath)
                
                else:
                    self.log.warnf("Unhandled tag: %s, type: %s", browseTag.fullPath, browseTag.type)
                    
    def copyTagValues(self, browseTag, isUdtMember):
        dataType = dataTypeForTagPath(browseTag.fullPath)
        targetTagPath = "[%s]%s" % (self.destinationTagProvider, browseTag.path)
        targetDataType = dataTypeForTagPath(targetTagPath)
        self.log.tracef("Comparing %s (%s) to %s (%s)", browseTag.fullPath, dataType, targetTagPath, targetDataType)
        
        ''' It is a little different to change the data type of a stand alone tag versus a tag embedded in a UDT.
        I have noticed that when changing the datatype that the copy that happens a few lines down sometimes may not take.  
        Running copy a second time will fix it because the data type is only changed the first time through. '''
        if dataType != targetDataType:
            if isUdtMember:
                self.log.infof("Converting %s (a member of a UDT) from %s to %s", targetTagPath, targetDataType, dataType)
                tagPath = targetTagPath[:targetTagPath.rfind("/")]
                tagName =targetTagPath[targetTagPath.rfind("/")+1:]
                system.tag.editTag(tagPath=tagPath, overrides={tagName: {"DataType": dataType}})    
            else:
                self.log.infof("Converting %s (a stand alone tag) from %s to %s", targetTagPath, targetDataType, dataType)
                system.tag.editTag(targetTagPath, attributes={"DataType": dataType})    
        
        ''' Now copy the values '''
        if browseTag.isExpression() and not(self.replaceExpressionTags):
            self.log.tracef("--- Skipping an expression tag ---")
        elif browseTag.isQuery() and not(self.replaceQueryTags):
            self.log.tracef("--- Skipping a query tag ---")
        else:
            qv = system.tag.read(browseTag.fullPath)
            if qv.quality.isGood():
                system.tag.write("[%s]%s" % (self.destinationTagProvider, browseTag.path), qv.value)
                    
    def copyUdtValues(self, tagpath):
        '''
        The browse function doesn't dig into UDTs, but when we copy values we need to recursively dig into the UDT.
        The original browse does navigate into folders so we don't need to treat them.
        '''
        self.log.tracef("Copy values for %s", tagpath)
        
        tagSet = system.tag.browseTags(parentPath=tagpath, recursive=False)
    
        for browseTag in tagSet:
            self.log.tracef("Path: %s", browseTag.path)
            self.log.tracef("Type: %s", str(browseTag.type))
            self.log.tracef("Tag Type: %s", str(browseTag.tagType))
            self.log.tracef("----------")
            if str(browseTag.type) in ["UDT_INST"]:
                self.copyUdtValues(browseTag.fullPath)
            else:
                self.copyTagValues(browseTag, True)
        
        self.log.tracef("...done with the UDT copy!")

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