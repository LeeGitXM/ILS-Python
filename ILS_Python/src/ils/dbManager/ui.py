'''
Created on Mar 21, 2017

@author: phass

This module contains a collection of scripts suitable
for common configuration of widgets in the UI.
'''
import system
from ils.dbManager.userdefaults import get as getUserDefaults
from ils.common.cast import toBit

# When the window is closed, make sure that any open transaction
# is cleaned up (rolled-back and closed). 
def handleWindowClosed(window):
    print "In %s.handleWindowClosed()..." % (__name__)

# When the window is opened, look for a "clear" button on the screen.
# Fire its actionPerformed method
def handleWindowOpened(window):
    print "In %s..handleWindowOpened ..." % (__name__)
    
# Populate  combo-box with a dataset of containing names
# of parameters available for a grade.
def populateParameterForGradeDropdown(dropdown):
    SQL = "Select Name from RtSQCParameters "
    pds = system.db.runQuery(SQL)
    # Create a new dataset using only the Name column
    header = ["Parameters"]
    names = []
    names.append([""])
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
            print "New selection %s ..." % (current)

# Populate combo-box with a dataset of containing names
# of grades available to a unit. Do not rollback on a change
def populateGradeForFamilyDropdown(dropdown):
    print "In %s.populateGradeForFamilyDropdown()" % (__name__)
    family = getUserDefaults("FAMILY")
    active = getUserDefaults("ACTIVE")
    activeBit = toBit(str(active))
    
    if family in ["", "", "<Family>"]:
        SQL = "SELECT DISTINCT Grade from RtGradeMaster "
        if active:
            SQL = SQL +  " WHERE active = %s" % (str(activeBit))
    else:
        SQL = "SELECT DISTINCT Grade from RtGradeMaster WHERE RecipeFamilyId = (SELECT RecipeFamilyId FROM RtRecipeFamily WHERE RecipeFamilyName='%s') " % (family)
        if active:
            SQL = SQL +  " and active = %s" % (str(activeBit))
    
    print "     SQL: ", SQL
    pds = system.db.runQuery(SQL)
    print "     ...fetched %d unique grades" % (len(pds))
    
    # Create a new dataset using only the Name column
    header = ["Grade"]
    names = [["<Grade>"]]
    for row in pds:
        name = row['Grade']
        nl = []
        nl.append(name)
        names.append(nl)
        
    dropdown.data = system.dataset.toDataSet(header,names)
    
    # Select the current value. We expect it to be in a custom property
    print "     Setting selected grade to (populateGradeForFamilyDropdown): ", getUserDefaults("GRADE")
    dropdown.setSelectedStringValue(getUserDefaults("GRADE"))

# Populate  combo-box with a dataset of containing names
# of recipe Families, plus "". Select the current UNIT
def populateRecipeFamilyDropdown(dropdown, includeAll=True):
    print "In %s.populateRecipeFamilyDropdown()" % (__name__)
    SQL = "Select RecipeFamilyName from RtRecipeFamily order by RecipeFamilyName"
    pds = system.db.runQuery(SQL)
    
    # Create a new dataset using only the Name column
    header = ["Family"]
    names = []
    if includeAll:
        names.append(["<Family>"])
    
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
            print "...new family selection %s ..." % (current)

# Populate combo-box with a dataset of containing versions
# available for a grade on a unit. Custom grade component assumed.
def populateVersionForGradeDropdown(dropdown):
    print "In %s.populateVersionForGradeDropdown()" % (__name__)
    SQL = "SELECT DISTINCT Version from RtGradeMaster "
    family = getUserDefaults("FAMILY")
    grade = getUserDefaults("GRADE") 
    
    if family == "<Family>" or grade == "<Grade>":
        pds = system.db.runQuery(SQL)
        print "...fetched %d rows" % (len(pds))
    
    else:
        if not(family in ["", "<Family>"]):
            SQL = SQL+" WHERE RecipeFamilyId = (SELECT RecipeFamilyId FROM RtRecipeFamily WHERE RecipeFamilyName='"+family+"')"
        
            if not (grade in [None, "", "ALL", "<Grade>"]):
                SQL = SQL+" AND Grade = '"+grade+"'"
        
        print "    SQL: ", SQL
        pds = system.db.runQuery(SQL)
        print "...fetched %d rows" % (len(pds))
    
    header = ["Grade"]
    versions = [["<Version>"]]
    for row in pds:
        version = row['Version']
        nl = []
        nl.append(str(version))
        versions.append(nl)
        
    dropdown.data = system.dataset.toDataSet(header, versions)
    
    # Select the current value. We expect it to be in a custom property
    dropdown.setSelectedStringValue(str(getUserDefaults("VERSION")))
