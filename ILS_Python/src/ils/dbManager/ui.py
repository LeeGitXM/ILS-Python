'''
Created on Mar 21, 2017

@author: phass

This module contains a collection of scripts suitable
for common configuration of widgets in the UI.
'''

import system
from ils.common.util import getRootContainer
from ils.dbManager.userdefaults import get as getUserDefaults

log = system.util.getLogger("com.ils.recipe.ui")

# When the window is closed, make sure that any open transaction
# is cleaned up (rolled-back and closed). 
def handleWindowClosed(window):
    log.info("ui.handleWindowClosed ...")

# When the window is opened, look for a "clear" button on the screen.
# Fire its actionPerformed method
def handleWindowOpened(window):
    log.info("ui.handleWindowOpened ...")
    
# Populate  combo-box with a dataset of containing names
# of parameters available for a grade.
def populateParameterForGradeDropdown(dropdown):
    SQL = "Select Name from RtSQCParameters "
    pds = system.db.runQuery(SQL)
    # Create a new dataset using only the Name column
    header = ["Parameters"]
    names = []
    names.append(["ALL"])
    for row in pds:
        name = row['FamilyName']
        nl = []
        nl.append(name)
        names.append(nl)
        
    dropdown.data = system.dataset.toDataSet(header,names)
    # Select the current value. 
    current = getUserDefaults('UNIT')
    if len(current)>0:
        oldSelection = str(dropdown.selectedValue)
        dropdown.setSelectedStringValue(current)
        # Loose old edits if we select a different database
        if oldSelection!=current:
            log.info("ui.populateUnitDropdown: New selection %s ..." % (current))

#
# Populate combo-box with a dataset of containing names
# of grades available to a unit. Do not rollback on a change
def populateGradeForFamilyDropdown(dropdown):
    SQL = "SELECT DISTINCT Grade from RtGradeMaster"
    family = getUserDefaults("FAMILY")
    if not family=="ALL":
        SQL = SQL+" WHERE RecipeFamilyId = (SELECT RecipeFamilyId FROM RtRecipeFamily WHERE RecipeFamilyName='"+family+"')"
    pds = system.db.runQuery(SQL)
    
    # Create a new dataset using only the Name column
    header = ["Grade"]
    names = []
    names.append(["ALL"])
    for row in pds:
        name = row['Grade']
        nl = []
        nl.append(name)
        names.append(nl)
        
    dropdown.data = system.dataset.toDataSet(header,names)
    # Select the current value. We expect it to be in a custom property
    root = getRootContainer(dropdown)
    print "Setting selected grade to (populateGradeForFamilyDropdown): ", root.grade
    dropdown.setSelectedStringValue(root.grade)

# Populate  combo-box with a dataset of containing names
# of recipe Families, plus "ALL". Select the current UNIT
def populateRecipeFamilyDropdown(dropdown):
    SQL = "Select RecipeFamilyName from RtRecipeFamily order by RecipeFamilyName"
    pds = system.db.runQuery(SQL)
    
    # Create a new dataset using only the Name column
    header = ["Family"]
    names = []
    names.append(["ALL"])
    for row in pds:
        name = row['RecipeFamilyName']
        nl = []
        nl.append(name)
        names.append(nl)
    dropdown.data = system.dataset.toDataSet(header,names)
    
    # Select the current value. 
    current = getUserDefaults('FAMILY')
    if len(current)>0:
        oldSelection = str(dropdown.selectedStringValue)
        dropdown.setSelectedStringValue(current)
        # Loose old edits if we select a different database
        if oldSelection!=current:
            log.info("ui.populateFamilyDropdown: New family selection %s ..." % (current))

# Populate combo-box with a dataset of containing versions
# available for a grade on a unit. Custom grade component assumed.
def populateVersionForGradeDropdown(dropdown):
    SQL = "SELECT DISTINCT Version from RtGradeMaster "
    family = getUserDefaults("FAMILY")
    if not family=="ALL":
        SQL = SQL+" WHERE RecipeFamilyId = (SELECT RecipeFamilyId FROM RtRecipeFamily WHERE RecipeFamilyName='"+family+"')"
    
        root = getRootContainer(dropdown)
        grade = root.grade
        if not grade == None and not grade=="ALL":
            SQL = SQL+" AND Grade = '"+grade+"'"
    
    pds = system.db.runQuery(SQL)
    # Create a new dataset using only the Name column
    header = ["Grade"]
    versions = []
    versions.append(["ALL"])
    for row in pds:
        version = row['Version']
        nl = []
        nl.append(str(version))
        versions.append(nl)
        
    dropdown.data = system.dataset.toDataSet(header,versions)
    # Select the current value. We expect it to be in a custom property
    root = getRootContainer(dropdown)
    dropdown.setSelectedStringValue(str(root.version))
