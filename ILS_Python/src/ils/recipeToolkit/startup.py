'''
Created on Sep 10, 2014

@author: Pete
'''

import system

import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit")

def gateway():
    from ils.recipeToolkit.version import version
    version = version()
    log.info("Starting Recipe Toolkit version %s" % (version))

    from ils.common.config import getTagProvider
    provider = getTagProvider()
    createTags("[" + provider + "]")

def client():
    print "In recipeToolkit.startup.client()"
    log = LogUtil.getLogger("com.ils.recipeToolkit.download")
    log.info("Initializing the recipe toolkit")

def createTags(tagProvider):
    print "Creating global constant memory tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Recipe/Constants/"

    data.append([path, "localG2WriteAlias", "String", "LocalG2"])
    data.append([path, "itemIdPrefix", "String", ""])
    data.append([path, "recipeMinimumDifference", "Float8", "0.00001"])
    data.append([path, "recipeMinimumRelativeDifference", "Float8", "0.00001"])
    data.append([path, "recipeWriteEnabled", "Boolean", "True"])
    data.append([path, "downloadTimeout", "Int4", "120"])

    data.append([path, "backgroundColorReadOnly", "String", "lightblue"])  #'#ADD8E6'  light blue
    data.append([path, "backgroundColorReadWrite", "String", "lightcyan"]) #'#E0FFFF' light cyan
    data.append([path, "backgroundColorNoChange", "String", "lightblue"])  #'#ADD8E6'  light blue
    data.append([path, "backgroundColorMismatch", "String", "plum"])
    data.append([path, "backgroundColorError", "String", "pink"])
    data.append([path, "backgroundColorWritePending", "String", "yellow"])
    data.append([path, "backgroundColorWriteError", "String", "red"])
    data.append([path, "backgroundColorWriteSuccess", "String", "lime"])
    
    data.append([path, "screenBackgroundColorInitializing", "String", "lightGrey"])
    data.append([path, "screenBackgroundColorDownloading", "String", "white"])
    data.append([path, "screenBackgroundColorSuccess", "String", "limegreen"])
    data.append([path, "screenBackgroundColorUnknown", "String", "magenta"])
    data.append([path, "screenBackgroundColorFail", "String", "red"])
       
    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
    
    # Now make two additional tags that are used to test how long the system has been RUNNING
    # First, make the tag that records when the gateway was restarted
    name = "startTime"
    fullName = path + name
    if not(system.tag.exists(fullName)):
        print "Creating the start time tag" 
        system.tag.addTag(parentPath = path, name = name, tagType = "MEMORY", dataType = "DateTime")
    
    # Unlike the configuration tags where we do not overwrite the value once it has been set, this needs to 
    # be reset EVERY time we restart
    import ils.common.util as util
    now = util.getDate()
    system.tag.write(fullName, now)
    
    # Now make an expression tag that calculates how many seconds the gateway has been running
    name = "runningSeconds"
    fullName = path + name
    if not(system.tag.exists(fullName)):
        print "Creating the running time tag" 
        expr = "dateDiff({[.]startTime}, now(0), 'sec')"
        system.tag.addTag(parentPath=path, name=name, tagType="EXPRESSION", dataType="Int8", attributes={"Expression":expr})

