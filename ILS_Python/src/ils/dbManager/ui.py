'''
Created on Mar 21, 2017

@author: phass

This module contains a collection of scripts suitable
for common configuration of widgets in the UI.
'''

import system
from java.lang   import System
from java.io     import File
from javax.swing import JFileChooser
from javax.swing.filechooser import FileNameExtensionFilter
from ils.dbManager.sql import commitTransactionForComponent, getTransactionForComponent, rollbackTransactionForComponent, closeTransactionForComponent, getRootContainer
from ils.dbManager.userdefaults import get as getUserDefaults

log = system.util.getLogger("com.ils.recipe.ui")

#
# Action script for an "Apply" button.
def applyAction(event):
    window = system.gui.getParentWindow(event)
    commitTransactionForComponent(window.getRootContainer())
    
# Action script for a "Cancel" button.
# NOTE: The request for save confirmation is Designer-only
# NOTE: FPMIWindow is a JInternalFrame 
def cancelAction(event):
    window = system.gui.getParentWindow(event)
    rollbackTransactionForComponent(window.getRootContainer())
    closeTransactionForComponent(window.getRootContainer())
    #window.setCloser(None)
    #window.doDefaultCloseAction()
    system.nav.closeWindow(window)

#        
# Traverse the component tree until we get to the frame 
def findRootPane(component):
    while component!=None:
        # print component.getClass().getCanonicalName()
        if component.getClass().getCanonicalName() == 'javax.swing.JRootPane':
            return component
        component = component.getParent()
        
    return component
    

# When the window is closed, make sure that any open transaction
# is cleaned up (rolled-back and closed). 
def handleWindowClosed(window):
    log.info("ui.handleWindowClosed ...")
    rollbackTransactionForComponent(window.getRootContainer())
    closeTransactionForComponent(window.getRootContainer())

# When the window is opened, look for a "clear" button on the screen.
# Fire its actionPerformed method
def handleWindowOpened(window):
    log.info("ui.handleWindowOpened ...")
    button = window.getRootContainer().getComponent("ClearButton")
    if button!= None:
        button.visible = False
        button.doClick()
#
# Action script for an "OK" button.
# Commit any open transaction, then close the window
def okAction(event):
    window = system.gui.getParentWindow(event)
    commitTransactionForComponent(window.getRootContainer())
    closeTransactionForComponent(window.getRootContainer())
    system.nav.closeWindow(window)
    
# Populate  combo-box with a dataset of containing names
# of parameters available for a grade.
def populateParameterForGradeDropdown(dropdown):
    txn = getTransactionForComponent(dropdown)
    SQL = "Select Name from RtSQCParameters "
    pds = system.db.runQuery(SQL,tx=txn)
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
            rollbackTransactionForComponent(dropdown)

#
# Populate combo-box with a dataset of containing names
# of grades available to a unit. Do not rollback on a change
def populateGradeForFamilyDropdown(dropdown):
    txn = getTransactionForComponent(dropdown)
    SQL = "SELECT DISTINCT Grade from RtGradeMaster"
    family = getUserDefaults("FAMILY")
    if not family=="ALL":
        SQL = SQL+" WHERE RecipeFamilyId = (SELECT RecipeFamilyId FROM RtRecipeFamily WHERE RecipeFamilyName='"+family+"')"
    pds = system.db.runQuery(SQL,tx=txn)
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

#
# Populate  combo-box with a dataset of containing names
# of recipe Families, plus "ALL". Select the current UNIT
def populateRecipeFamilyDropdown(dropdown):
    txn = getTransactionForComponent(dropdown)
    SQL = "Select RecipeFamilyName from RtRecipeFamily order by RecipeFamilyName"
    pds = system.db.runQuery(SQL,tx=txn)
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
            rollbackTransactionForComponent(dropdown)

# Populate combo-box with a dataset of containing versions
# available for a grade on a unit. Custom grade component assumed.
def populateVersionForGradeDropdown(dropdown):
    txn = getTransactionForComponent(dropdown)
    SQL = "SELECT DISTINCT Version from RtGradeMaster "
    family = getUserDefaults("FAMILY")
    if not family=="ALL":
        SQL = SQL+" WHERE RecipeFamilyId = (SELECT RecipeFamilyId FROM RtRecipeFamily WHERE RecipeFamilyName='"+family+"')"
    
        root = getRootContainer(dropdown)
        grade = root.grade
        if not grade == None and not grade=="ALL":
            SQL = SQL+" AND Grade = '"+grade+"'"
    
    pds = system.db.runQuery(SQL,tx=txn)
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

# Display a file chooser. On return populate the subject
# text box. We are looking for SQL files.
# **** We don't use this anymore, but this is a really nice file chooser ****
def selectFile(textbox):
    root = findRootPane(textbox)
    
    fc = JFileChooser()
    # If the text box already has a value, then use it as the starting place
    currentPath = textbox.getText()
    print currentPath
    print System.getProperty("file.separator")
    if  currentPath != None and len(currentPath)>0 :
        # Strip off file portion
        separator = System.getProperty("file.separator")
        index = currentPath.rfind(separator)
        if index>0:
            currentPath = currentPath[0:index]
            file = File(currentPath)
            if file != None:
                fc.setCurrentDirectory(file)
    fc.setDialogTitle("Path for database creation script")
    filter = FileNameExtensionFilter("SQL files",["sql"])
    fc.addChoosableFileFilter(filter)
    fc.setApproveButtonToolTipText("Select the file system location for the database create script")
    fc.setDialogType(JFileChooser.CUSTOM_DIALOG)
    ret = fc.showDialog(root,"Select/Create")
    
    if ret == JFileChooser.APPROVE_OPTION:
        file = fc.getSelectedFile()
        path = file.getCanonicalPath()
        if not path.endswith(".sql"):
            path = path + ".sql"
        textbox.setText(path)