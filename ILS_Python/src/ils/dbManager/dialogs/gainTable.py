'''
Created on Apr 19, 2019

@author: phass
'''

import system
from ils.dbManager.ui import populateRecipeFamilyDropdown
from ils.dbManager.userdefaults import get as getUserDefaults
from ils.dbManager.sql import idForFamily, idForGain
from ils.common.error import notifyError
log = system.util.getLogger("com.ils.recipe.ui")

# Called from the client startup script: View menu
def showWindow():
    window = "DBManager/GainsTable"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)

# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameOpened(rootContainer):
    log.infof("In %s.InternalFrameOpened", __name__)
    dropdown = rootContainer.getComponent("FamilyDropdown")
    dropdown.setSelectedStringValue(getUserDefaults("FAMILY"))
    
# When the screen is first displayed, set widgets for user defaults
# The "active" dropdown is always initialized to "TRUE"
def internalFrameActivated(rootContainer):
    log.infof("In %s.InternalFrameActivated", __name__)
    requery(rootContainer)
    dropdown = rootContainer.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown, False)

def requery(rootContainer):
    log.infof("In %s.InternalFrameActivated", __name__)
    table = rootContainer.getComponent("Power Table")
    
    dropdown = rootContainer.getComponent("FamilyDropdown")
    recipeFamilyName = dropdown.selectedStringValue
    
    checkBox = rootContainer.getComponent("ActiveOnlyCheckBox")
    activeOnly = checkBox.selected
    
    columns = fetchColumns(recipeFamilyName)
    grades = fetchRows(recipeFamilyName, activeOnly)
    pds = fetchData(recipeFamilyName)
    ds = mergeData(rootContainer, grades, columns, pds)
    table.data = ds
    
    for col in range(ds.getColumnCount()):
        if col == 0:
            table.setColumnWidth(col, 70)
        else:
            table.setColumnWidth(col, 110)
    
def fetchColumns(recipeFamilyName):
    SQL = "select  G.Parameter "\
        "from RtGain G,  RtRecipeFamily F "\
        "where G.RecipeFamilyId = F.RecipeFamilyId "\
        " and F.RecipeFamilyName = '%s' order by Parameter" % (recipeFamilyName)
    pds = system.db.runQuery(SQL)
    
    columns = []
    for record in pds:
        columns.append(record["Parameter"])
        
    print "Columns: ", columns
    return columns
    
def fetchRows(recipeFamilyName, activeOnly):
    
    if activeOnly:
        SQL = "select distinct GM.Grade "\
            " from RtGradeMaster GM,  RtRecipeFamily RF "\
            " where RF.RecipeFamilyName = '%s' and GM.Active = 1 and GM.RecipeFamilyId = RF.RecipeFamilyId order by Grade" % (recipeFamilyName)
    else:
        SQL = "select distinct GM.Grade "\
            " from RtGradeMaster GM,  RtRecipeFamily RF "\
            " where RF.RecipeFamilyName = '%s' and GM.RecipeFamilyId = RF.RecipeFamilyId order by Grade" % (recipeFamilyName)
    
    print SQL
    pds = system.db.runQuery(SQL)
    
    rows = []
    for record in pds:
        rows.append(record["Grade"])

    print "Rows: ", rows    
    return rows

def fetchData(recipeFamilyName):
    SQL = "select Grade, Parameter, Gain "\
        " from RtGainView "\
        "where RecipeFamilyName = '%s' order by Grade, Parameter" % (recipeFamilyName)
    pds = system.db.runQuery(SQL)
    print "Fetched %d rows of data..." % (len(pds))
    return pds

def mergeData(rootContainer, grades, columns, pds):
    print "In %s.mergeData()" % (__name__)
    print "Grades: ", grades
    data = []
    for grade in grades:
        row = [None]*(len(columns) + 1)
        row[0] = str(grade)
        data.append(row)
    
    columns.insert(0, "Grade")
    ds = system.dataset.toDataSet(columns, data)
    
    for record in pds:
        grade = record["Grade"]
        if grade in grades:
            rowNum = grades.index(grade)
            column = record["Parameter"]
            gain = record["Gain"]
            ds = system.dataset.setValue(ds, rowNum, column, gain)
        else:
            log.errorf("Unknown grade: %s - this grade does not exist in the Grade Master table.", grade)

    return ds

def saveData(self, rowIndex, colIndex, colName, oldValue, newValue):
    print "Setting the new value to <%s>" % (newValue)
    rootContainer = self.parent
    familyName  = rootContainer.getComponent("FamilyDropdown").selectedStringValue
    familyId = idForFamily(familyName)
    
    ds = self.data
    grade = ds.getValueAt(rowIndex, 0)
    
    column = self.selectedColumn
    parameterName = ds.getColumnName(column)
    parameterId = idForGain(familyId, parameterName)
    
    if newValue == "":
        SQL ="update RtGainGrade set gain = NULL where ParameterId = %d and Grade = '%s'" % (parameterId, grade)
    else:
        SQL = "update RtGainGrade set gain = %s where ParameterId = %d and Grade = '%s'" % (str(newValue), parameterId, grade)
    print SQL
    system.db.runUpdateQuery(SQL)
    self.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)

def deleteColumn(event):
    print "In %s.deleteColumn()" % (__name__)
    rootContainer = event.source.parent
    familyName  = rootContainer.getComponent("FamilyDropdown").selectedStringValue
    recipeFamilyId = idForFamily(familyName)
    table = event.source.parent.getComponent("Power Table")
    ds = table.data
    column = table.selectedColumn
    if column < 0:
        system.gui.warningBox("Please select the column to delete.")
        return

    parameter = ds.getColumnName(column)
    print "Deleting Gain: <%s>" % (parameter)
    
    ''' Hopefully there is a cascade delete on the RtGainGrade table '''
    SQL = "delete from RtGain where Parameter = '%s' and RecipeFamilyId = %d" % (parameter, recipeFamilyId)
    system.db.runUpdateQuery(SQL)
    
    requery(rootContainer)


def addGainParameter(button, parameter):
    rootContainer = button.parent
    
    # Family
    family = rootContainer.getComponent("FamilyDropdown").selectedStringValue
    if family == "" or family == "All":
        system.gui.messageBox("Please select a specific family!")
        return
    
    familyId = idForFamily(getUserDefaults("FAMILY"))

    # Parameter
    if parameter!=None and len(parameter)>0:
        SQL = "INSERT INTO RtGain (RecipeFamilyId, Parameter) VALUES (%i, '%s')" % (familyId, parameter)
        log.trace(SQL)
        system.db.runUpdateQuery(SQL)            
    else:
        system.gui.messageBox("Please enter a parameter name!")
