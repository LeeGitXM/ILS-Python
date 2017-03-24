'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "RecipeFamily" dialog
'''

import sys, system
from ils.dbManager.ui import populateRecipeFamilyDropdown
from ils.dbManager.sql import getRootContainer, getTransactionForComponent, rollbackTransactionForComponent, closeTransactionForComponent, commitTransactionForComponent, idForFamily, idForPost, fetchAnyPost
from ils.dbManager.userdefaults import get as getUserDefaults
log = system.util.getLogger("com.ils.recipe.unit")

# When the screen is first displayed, set widgets for user defaults
def internalFrameOpened(component):
    log.trace("InternalFrameOpened")
    container = getRootContainer(component)

    # Make sure the transaction is alive.
    getTransactionForComponent(component)

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
    txn = getTransactionForComponent(table)
    try:
        pds = system.db.runQuery(SQL,tx=txn)
        table.data = pds
        refresh(table)
    except:
        # type,value,traceback
        type,value,trace = sys.exc_info()
        log.info("unit.requery: SQL Exception ...",value) 
        rollbackTransactionForComponent(table)
        system.gui.messageBox("Error fetching from RtUnitRoot")

# Given the current state of the table, make sure that other widgets
# on the screen are in-synch. Note, if we delete a row, then that row 
# remains selected in the model.
def refresh(component):
    container = getRootContainer(component)
    table = container.getComponent("DatabaseTable")
    log.debug("unit.refresh ... selected = %d of %d" % (table.selectedRow,table.data.getRowCount()))
    button = container.getComponent("DeleteButton")
    if button!=None:
        button.setEnabled(table.selectedRow>=0 and table.selectedRow<table.data.getRowCount())

# Delete the selected row
def deleteRow(button):
    log.info("recipeFamily.deleteRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    txn = getTransactionForComponent(button)
    rownum = table.selectedRow
    ds = table.data
    id = ds.getValueAt(rownum,'RecipeFamilyId')
    SQL = "DELETE FROM RtRecipeFamily WHERE RecipeFamilyId="+str(id)
    system.db.runUpdateQuery(SQL,tx=txn)
    ds = system.dataset.deleteRow(ds,rownum)
    table.data = ds
    table.selectedRow = -1
    button.setEnabled(False)
    
# Add a new row to the table. The data element is a DataSet (not python)
def insertRow(button):
    log.info("recipeFamily.insertRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    txn = getTransactionForComponent(button)
    postId, post = fetchAnyPost()
    SQL = "INSERT INTO RtRecipeFamily(RecipeFamilyName, PostId, RecipeUnitPrefix, RecipeNameAlias) "\
        " VALUES('<FamilyName>', %s, '<Unit Prefix>','<Recipe Alias>')" % (str(postId))
    id = system.db.runUpdateQuery(SQL,tx=txn,getKey=True)
    requery(button)

#    row = [-1,'<family>','<post>','<unit prefix>','<recipe alias>','<comment>']    
#    ds = table.data
#    project.recipe.misc.dumpDataset(ds)
#    ds = system.dataset.addRow(ds,row)
#    project.recipe.misc.dumpDataset(ds)
#    table.data = ds


            
# Called from the client startup script: View menu
def showWindow():
    window = "DBManager/RecipeFamily"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)
    
# Update database for a cell edit
def update(table,row,colname,value):
    log.info("recipeFamily.update (%d:%s)=%s ..." %(row,colname,str(value)))
    txn = getTransactionForComponent(table)
    ds = table.data
    id = ds.getValueAt(row,0)
    
    if colname == "Post":
        postId = idForPost(str(value), txn)
        SQL = "UPDATE RtRecipeFamily SET PostId = %s WHERE RecipeFamilyId =  %s" % (str(postId), str(id))
    else:
        SQL = "UPDATE RtRecipeFamily SET "+colname+" = '"+value+"' WHERE RecipeFamilyId="+str(id)
        
    system.db.runUpdateQuery(SQL,tx=txn)