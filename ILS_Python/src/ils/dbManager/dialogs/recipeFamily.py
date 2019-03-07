'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "RecipeFamily" dialog
'''

import system
from ils.common.util import getRootContainer
from ils.dbManager.sql import idForPost
from ils.dbManager.userdefaults import get as getUserDefaults
from ils.common.error import notifyError
log = system.util.getLogger("com.ils.recipe.ui")


# Called only when the screen is first displayed
def internalFrameOpened(component):
    log.trace("InternalFrameOpened")

# Called whenever the screen is brought to the top
def internalFrameActivated(component):
    log.trace("InternalFrameActivated")
    requery(component)


# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(component):
    log.info("unit.requery ...")
    container = getRootContainer(component)
    table = container.getComponent("DatabaseTable")
    
    SQL = "SELECT F.RecipeFamilyId, F.RecipeFamilyName, P.Post, F.RecipeUnitPrefix, F.RecipeNameAlias, F.Comment "\
        " FROM RtRecipeFamily F, TkPost P "\
        " WHERE F.PostId = P.PostId ORDER by RecipeFamilyName"
    try:
        pds = system.db.runQuery(SQL)
        table.data = pds
    except:
        notifyError(__name__, "Fetching families")

# Delete the selected row.  The family is a primary key for many of the other recipe tables.  This delete works using cascade deletes.
def deleteRow(button):
    log.info("recipeFamily.deleteRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")

    rownum = table.selectedRow
    ds = table.data
    familyId = ds.getValueAt(rownum,'RecipeFamilyId')
    familyName = ds.getValueAt(rownum,'RecipeFamilyName')
    confirm = system.gui.confirm("Are you sure that you want to delete family <%s> and all of its associated recipes?" % (familyName))
    if confirm:
        SQL = "DELETE FROM RtRecipeFamily WHERE RecipeFamilyId="+str(familyId)
        system.db.runUpdateQuery(SQL)
        ds = system.dataset.deleteRow(ds,rownum)
        table.data = ds
        table.selectedRow = -1
        button.setEnabled(False)

            
# Called from the client startup script: View menu
def showWindow():
    window = "DBManager/RecipeFamily"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)
    
# Update database for a cell edit
def update(table,row,colname,value):
    log.info("recipeFamily.update (%d:%s)=%s ..." %(row,colname,str(value)))
    ds = table.data
    id = ds.getValueAt(row,0)
    
    if colname == "Post":
        postId = idForPost(str(value))
        SQL = "UPDATE RtRecipeFamily SET PostId = %s WHERE RecipeFamilyId =  %s" % (str(postId), str(id))
    else:
        SQL = "UPDATE RtRecipeFamily SET "+colname+" = '"+value+"' WHERE RecipeFamilyId="+str(id)
        
    system.db.runUpdateQuery(SQL)