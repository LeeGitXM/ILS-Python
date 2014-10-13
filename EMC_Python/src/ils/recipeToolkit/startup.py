'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def gateway():
    from ils.recipeToolkit.version import version
    version = version()
    print "Starting Recipe Toolkit ", version

    from ils.common.config import getTagProvider
    provider = getTagProvider()
    createTags("[" + provider + "]")

#
def createTags(tagProvider):
    print "Creating global constant memory tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Recipe/Constants/"

    data.append([path, "localG2WriteAlias", "String", "LocalG2"])
    data.append([path, "recipeMinimumDifference", "Float8", "0.00001"])
    data.append([path, "recipeMinimumRelativeDifference", "Float8", "0.00001"])
    data.append([path, "recipeWriteEnabled", "Boolean", "True"])

    data.append([path, "backgroundColorReadOnly", "String", "lightblue"])  #'#ADD8E6'  light blue
    data.append([path, "backgroundColorReadWrite", "String", "lightcyan"]) #'#E0FFFF' light cyan
    data.append([path, "backgroundColorNoChange", "String", "lightblue"])  #'#ADD8E6'  light blue
    data.append([path, "backgroundColorMismatch", "String", "plum"])
    data.append([path, "backgroundColorError", "String", "pink"])
    
    data.append([path, "screenBackgroundColorInitializing", "String", "lightGrey"])
    data.append([path, "screenBackgroundColorDownloading", "String", "white"])
    data.append([path, "screenBackgroundColorSuccess", "String", "limegreen"])
    data.append([path, "screenBackgroundColorUnknown", "String", "magenta"])
    data.append([path, "screenBackgroundColorFail", "String", "red"])
    
   
    ds = system.dataset.toDataSet(headers, data)
    from ils.recipeToolkit.tagFactory import createConfigurationTags
    createConfigurationTags(ds)