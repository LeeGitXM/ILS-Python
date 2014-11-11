'''
Created on Sep 10, 2014

@author: Pete
'''

import system

# Ignition does not behave well when "." are used in tag names.  This is unfortunate because we have the practice
# of naming I/O using the item-ids, which always have "." in them.  We need to continue to use the "." in the item-id
# but this script modified the recipe tag name to an Ignition compatible tag name by replacing "." with hyphens. 
def formatTagName(provider, recipeKey, tagName):
    tagName = updateTagName(tagName)
    tagName = '[%s]Recipe/%s/%s' % (provider, recipeKey, tagName)
    return tagName

# Format a tag name into the complete path for a "tag".  This is for a tag whose value is set by the recipe toolkit,
# is not used in the DCS, but is used by other toolkits.  Therefore, these entities are "local" to Ignition
# and are generally represented as memory tags.
def formatLocalTagName(provider, tagName):
    import string
    
    # If the tag name ends in ".VALUE" then trim it off
    if tagName.endswith('.VALUE'):
        tagName = tagName[:len(tagName) - 6]
    
    # Replace the "." with "/" which converts the folder structure
    tagName = string.replace(tagName, '.', '/')
    
    # Add the provider and root folder for site specific "Local" tags
    tagName = '[%s]Site/%s' % (provider, tagName)

    return tagName


# Format the path and name for local tags
def formatLocalTagPathAndName(provider, tagName):
    
    # Format the provider and root folder for site specific "Local" tags
    tagPath = '[%s]Site/' % (provider)    

    # If the tag name ends in ".VALUE" then trim it off
    if tagName.endswith('.VALUE'):
        tagName = tagName[:len(tagName) - 6]

    # Replace the "." with "/" which converts the folder structure
    tokens = tagName.split('.')

    for i in range(0, len(tokens) - 1):
        tagPath = tagPath + tokens[i] + '/'

    tagName = tokens[len(tokens) - 1]

    return tagPath, tagName


# Ignition does not behave well when "." are used in tag names.  This is unfortunate because we have the practice
# of naming I/O using the item-ids, which always have "." in them.  We need to continue to use the "." in the item-id
# but this script modified the recipe tag name to an Ignition compatible tag name by replacing "." with hyphens. 
def updateTagName(tagName):
    import string
    tagName = string.replace(tagName, '.', '-')
    return tagName

# I have designed a tree structure for tags used in the toolkits.  This will be assumed throughout and cannot be changed.
# This routing should be the only place where this is hard coded
def getTagPath(recipeKey, tagName):
    tagPath = "/Recipe/" + recipeKey + "/" + tagName
    return tagPath

# Animate the screen color based on the status of the download
def setBackgroundColor(rootContainer, colorTagName):
    color = system.tag.read("/Recipe/Constants/" + colorTagName)
    rootContainer.setPropertyValue("backgroundColor", color.value)
