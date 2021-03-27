'''
Created on Sep 20, 2017

@author: phass
'''

import system
from ils.common.error import notifyError
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def internalFrameOpened(rootContainer):
    log.trace("InternalFrameOpened")

def internalFrameActivated(rootContainer):
    log.trace("InternalFrameActivated")

def createFamily(rootContainer):
    print "In createGrade..."
    family = rootContainer.getComponent("Family").text
    post = rootContainer.getComponent("Post").selectedStringValue
    postId = rootContainer.getComponent("Post").selectedValue
    unitPrefix = rootContainer.getComponent("Unit Prefix").text
    recipeAlias = rootContainer.getComponent("Recipe Alias").text
    comment = rootContainer.getComponent("Comment").text
    hasSQC = rootContainer.getComponent("HasSQC").selected
    hasGains = rootContainer.getComponent("HasGains").selected
    
    if family == None:
        system.gui.messageBox("Family is required.")
        return False
    
    if post == None or postId == -1:
        system.gui.messageBox("Post is required.")
        return False
    
    if unitPrefix == None:
        system.gui.messageBox("Unit Prefix is required.")
        return False
    
    if recipeAlias == None:
        system.gui.messageBox("RecipeAlias is required.")
        return False
    
    if len(comment) >= 2000:
        system.gui.messageBox("Maximum comment length is 200 characters, comment will be truncated.")
        comment = comment[:2000]
        
    print "Creating a new family..."

    # Insert row into RtRecipeFamily
    SQL="INSERT INTO RtRecipeFamily(RecipeFamilyName, RecipeUnitPrefix, RecipeNameAlias, PostId, HasSQC, HasGains, Comment) VALUES(?,?,?,?,?,?,?)"
    
    try:
        system.db.runPrepUpdate(SQL,[family, unitPrefix, recipeAlias, postId, hasSQC, hasGains, comment])
    except:
        notifyError(__name__, "Inserting a new family")
        
    return True