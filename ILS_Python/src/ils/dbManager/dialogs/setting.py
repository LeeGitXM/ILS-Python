'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "Add Grade Setting" dialog
'''

import system
from ils.common.util import getRootContainer
from ils.dbManager.userdefaults import get as getUserDefaults
from ils.log import getLogger
log =getLogger(__name__)

# Refresh the text field and dropdowns
def refresh(component):
    container = getRootContainer(component)
    log.debug("setting.refresh ... ")
    field = container.getComponent("UnitField")
    unit = getUserDefaults("UNIT")
    if field!=None:
        field.setText(unit)
        field.setEnabled(False)
        
        
# When the screen is first displayed, set widgets for user defaults
def initialize(component):
    container = getRootContainer(component)
    dropdown = container.getComponent("DatabaseDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("DATABASE"))
    dropdown = container.getComponent("UnitDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("UNIT"))