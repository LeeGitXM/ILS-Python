'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "SQC Parameter" dialog
'''

import string, system
from ils.dbManager.ui import populateRecipeFamilyDropdown
from ils.dbManager.sql import idForFamily
from ils.common.util import getRootContainer
from ils.dbManager.userdefaults import get as getUserDefaults
from ils.common.error import notifyError
log = system.util.getLogger("com.ils.recipe.ui")

# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameActivated(rootContainer):
    log.trace("InternalFrameOpened")
    
    # Clear the name field
    field = rootContainer.getComponent("ParameterNameField")
    field.text = ""
    
    dropdown = rootContainer.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown)

# Refresh the text field and dropdowns
def refresh(component):
    log.debug("sqcparameter.refresh ... ")
    initialize(component)

# Add a new row to the limits table for a new parameter.
# By adding a new parameter, we are adding a new parameter for every grade for the family
# Will get an error if the row exists.
def insertRow(rootContainer):
    # Family
    family = rootContainer.getComponent("FamilyDropdown").selectedStringValue
    if family == "" or string.upper(family) == "ALL":
        system.gui.messageBox("Please select a specific family!")
        return False
    familyId = idForFamily(family)
    
    # Parameter
    parameter = rootContainer.getComponent("ParameterNameField").text
    if parameter!=None and len(parameter)>0:
        tx= system.db.beginTransaction()
        
        try:
            SQL = "INSERT INTO RtSQCParameter(RecipeFamilyId, Parameter) VALUES(%s, '%s')" % (str(familyId), parameter)
            log.trace(SQL)
            parameterId = system.db.runUpdateQuery(SQL,tx=tx, getKey=True)
    
            # Now add a new limit row for each grade
            SQL = "INSERT INTO RtSQCLimit(ParameterId,Grade) " \
                " SELECT DISTINCT %i, Grade FROM RtGradeMaster WHERE RecipeFamilyId = %i " % (parameterId, familyId)
            log.trace(SQL)
            rows=system.db.runUpdateQuery(SQL,tx=tx)
        except:
            system.db.rollbackTransaction(tx)
            notifyError(__name__, "Inserting a SQC Parameter")
        else:
            log.info("Inserted %i rows into RtSQCLimit" % (rows))
        system.db.closeTransaction(tx)
        
    else:
        system.gui.messageBox("Please enter a parameter name!")
        return False

    return True
#
# When the screen is first displayed, set widgets for user defaults
def initialize(component):
    container = getRootContainer(component)
    field = container.getComponent("familyField")
    field.setText(getUserDefaults("FIELD"))
    field = container.getComponent("GradeField")
    field.setText(container.grade)