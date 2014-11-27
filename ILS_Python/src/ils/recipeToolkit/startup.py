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
    from ils.recipeToolkit.tagFactory import createConfigurationTags
    createConfigurationTags(ds)