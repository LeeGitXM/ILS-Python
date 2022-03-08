'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "SQC Parameter" dialog
'''

import string, system
from ils.dbManager.sql import idForFamily
from ils.common.error import notifyError
from ils.log import getLogger
from ils.common.config import getDatabaseClient
log =getLogger(__name__)

# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameActivated(rootContainer):
    log.trace("InternalFrameOpened")
    
    # Clear the name field
    field = rootContainer.getComponent("ParameterNameField")
    field.text = ""

# Add a new row to the limits table for a new parameter.
# By adding a new parameter, we are adding a new parameter for every grade for the family
# Will get an error if the row exists.
def insertRow(rootContainer):
    db = getDatabaseClient()
    # Family
    family = rootContainer.family
    if family == "" or string.upper(family) == "ALL":
        system.gui.messageBox("Please select a specific family!")
        return False
    familyId = idForFamily(family)
    
    # Parameter
    parameter = rootContainer.getComponent("ParameterNameField").text
    if parameter!=None and len(parameter)>0:
        
        try:
            SQL = "INSERT INTO RtSQCParameter(RecipeFamilyId, Parameter) VALUES(%s, '%s')" % (str(familyId), parameter)
            log.trace(SQL)
            system.db.runUpdateQuery(SQL, database=db)
        except:
            notifyError(__name__, "Inserting a SQC Parameter")
        else:
            log.info("Inserted a new row into RtSQCParameter")
        
    else:
        system.gui.messageBox("Please enter a parameter name!")
        return False

    return True