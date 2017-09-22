'''
Created on Mar 21, 2017

@author: phass
'''

import system
from ils.dbManager.ui import populateRecipeFamilyDropdown
from ils.dbManager.sql import idForFamily
from ils.common.util import getRootContainer
from ils.dbManager.userdefaults import get as getUserDefaults
from ils.common.error import notifyError
log = system.util.getLogger("com.ils.recipe.ui")

# Called from the client startup script: View menu
# Note: No attempt is made at this point to reconcile with any tab strip
def showWindow():
    window = "DBManager/Events"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)
    
# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(rootContainer):
    log.info("event.requery ...")
    table = rootContainer.getComponent("DatabaseTable")
    whereExtension = getWhereExtension(rootContainer)
    SQL = "SELECT F.RecipeFamilyName, E.Grade, EP.Parameter, E.Value, EP.ParameterId " \
        " FROM RtRecipeFamily F, RtEvent E, RtEventParameter EP " \
        " WHERE EP.RecipeFamilyId = F.RecipeFamilyId  "\
        " and E.ParameterId = EP.ParameterId %s " \
        " ORDER BY RecipeFamilyName, Grade, Parameter" % (whereExtension)
    log.trace(SQL)
    try:
        pds = system.db.runQuery(SQL)
        table.data = pds
    except:
        notifyError(__name__, "Error fetching the event data")

# By deleting a row, we are deleting the parameter for every grade for the family.
def deleteRow(button):
    log.info("event.deleteRow ...")
    container = getRootContainer(button)
    table = container.getComponent("DatabaseTable")
    
    rownum = table.selectedRow
    ds = table.data
    pid = ds.getValueAt(rownum,'ParameterId')
    
    tx = system.db.beginTransaction()
    try:
        SQL = "DELETE FROM RtEvent WHERE ParameterId = %i" % (pid)
        log.trace(SQL)
        rows = system.db.runUpdateQuery(SQL,tx=tx)
        log.info("Deleted %i rows from RtEvent" % (rows))
            
        SQL = "DELETE FROM RtEventParameter WHERE ParameterId = %i" % (pid)
        log.trace(SQL)
        rows = system.db.runUpdateQuery(SQL,tx=tx)
        log.info("Deleted %i rows from RtEventParameter" % (rows))
    except:
        system.db.rollbackTransaction(tx)
        notifyError(__name__, "Deleting Events")
    else:
        system.db.commitTransaction(tx)
        ds = system.dataset.deleteRow(ds,rownum)
        table.data = ds
        table.selectedRow = -1
        
    system.db.closeTransaction(tx)

# Enhance the joining where clause with the selects from the dropdowns
def getWhereExtension(rootContainer):
    where = ""

    dropdown = rootContainer.getComponent("FamilyDropdown")
    family = dropdown.selectedLabel
    if family != "ALL" and family != "<Family>":
        where = " AND F.RecipeFamilyName = '"+family+"' "
    
    dropdown = rootContainer.getComponent("GradeDropdown")
    grade = dropdown.selectedLabel
    if grade != "ALL" and grade != "<Grade>":
        where = where+" AND E.Grade = '"+grade+"'"
                    
    return where

# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameOpened(rootContainer):
    log.trace("event.internalFrameOpened")

    dropdown = rootContainer.getComponent("FamilyDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("FAMILY"))

    dropdown = rootContainer.getComponent("GradeDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("GRADE"))
    
# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameActivated(rootContainer):
    log.trace("event.internalFrameActivated")
    requery(rootContainer)
    dropdown = rootContainer.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown)
                                
# Update database for a cell edit. We only allow edits of parameter name or limits.
def update(table,row,colname,value):
    log.info("event.update (%d:%s)=%s ..." %(row,colname,str(value)))
    ds = table.data
    #column is LowerLimit or UpperLimit. Others are not editable.
    paramid=ds.getValueAt(row,"ParameterId")
    grade=ds.getValueAt(row,"Grade")
    SQL = "UPDATE RtEvent SET value = %s WHERE ParameterId = %i and Grade = '%s'" % (str(value), paramid, grade)
    log.trace(SQL)
    system.db.runUpdateQuery(SQL)
    
# Add a new row to the RtEventParameters table and one row for each grade to the RtEvents table
# By adding a new parameter, we are adding a new parameter for every grade for the family
# Will get an error if the row exists.
def addParameter(button, parameter):
    rootContainer = getRootContainer(button)
    
    # Family
    family = rootContainer.getComponent("FamilyDropdown").selectedStringValue
    if family == "" or family == "All":
        system.gui.messageBox("Please select a specific family!")
        return
    familyId = idForFamily(getUserDefaults("FAMILY"))

    # Parameter
    if parameter!=None and len(parameter)>0:
        tx = system.db.beginTransaction()
        
        try:
            SQL = "INSERT INTO RtEventParameter (RecipeFamilyId, Parameter) VALUES (%i, '%s')" % (familyId, parameter)
            log.trace(SQL)
            parameterId = system.db.runUpdateQuery(SQL,tx=tx,getKey=True)
                
            # Now add a new limit row for each grade
            SQL = "INSERT INTO RtEvent (ParameterId, Grade) " \
                " SELECT DISTINCT %i, Grade FROM RtGradeMaster WHERE RecipeFamilyId = %i " % (parameterId, familyId)
            log.trace(SQL)
            rows=system.db.runUpdateQuery(SQL,tx=tx)
            log.info("Inserted %i rows into RtEvent" % (rows))
        except:
            system.db.rollbackTransaction(tx)
            notifyError(__name__, "Inserting an event")
            
        else:
            system.db.commitTransaction(tx)
        
        system.db.closeTransaction(tx)
    else:
        system.gui.messageBox("Please enter a parameter name!")
        return