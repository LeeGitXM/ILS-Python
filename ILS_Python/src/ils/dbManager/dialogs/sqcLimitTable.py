'''
Created on Apr 19, 2019

@author: phass
'''

import system
from ils.dbManager.ui import populateRecipeFamilyDropdown
from ils.dbManager.userdefaults import get as getUserDefaults
from ils.dbManager.sql import idForFamily, idForParameter
from ils.common.error import notifyError
from ils.common.cast import toBit
log = system.util.getLogger("com.ils.recipe.ui")

# Called from the client startup script: View menu
def showWindow():
    window = "DBManager/SQCLimitsTable"
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
    SQL = "select  P.Parameter "\
        "from RtSQCParameter P,  RtRecipeFamily F "\
        "where P.RecipeFamilyId = F.RecipeFamilyId "\
        " and F.RecipeFamilyName = '%s' order by Parameter" % (recipeFamilyName)
    pds = system.db.runQuery(SQL)
    
    columns = []
    for record in pds:
        columns.append(record["Parameter"] + "_LL")
        columns.append(record["Parameter"] + "_UL")
        
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

    print "SQL: ", SQL
    pds = system.db.runQuery(SQL)
    print "Selected %d grades..." % (len(pds))
    
    grades = []
    for record in pds:
        grades.append(record["Grade"])

    print "Grades: ", grades    
    return grades

def fetchData(recipeFamilyName):
    SQL = "select Grade, Parameter, UpperLimit, LowerLimit "\
        " from RtSQCLimitView "\
        " where RecipeFamilyName = '%s' order by Grade, Parameter" % (recipeFamilyName)
    pds = system.db.runQuery(SQL)
    print "Fetched %d rows of data..." % (len(pds))
    return pds

def mergeData(rootContainer, grades, columns, pds):
    print "In %s.mergeData()" % (__name__)
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
            upperLimit = record["UpperLimit"]
            lowerLimit = record["LowerLimit"]
            ds = system.dataset.setValue(ds, rowNum, column + "_UL", upperLimit)
            ds = system.dataset.setValue(ds, rowNum, column + "_LL", lowerLimit)
    return ds

def saveData(self, rowIndex, colIndex, colName, oldValue, newValue):
    print "Setting the new value to <%s>" % (newValue)
    rootContainer = self.parent
    familyName  = rootContainer.getComponent("FamilyDropdown").selectedStringValue
    familyId = idForFamily(familyName)
    
    ds = self.data
    grade = ds.getValueAt(rowIndex, 0)
    
    column = self.selectedColumn
    columnName = ds.getColumnName(column)
    parameterName = columnName[:len(columnName)-3]
    parameterId = idForParameter(familyId, parameterName)
    
    limitType = columnName[len(columnName)-2:]
    if limitType == "LL":
        limitType = "LowerLimit"
    else:
        limitType = "UpperLimit"
    
    if newValue == "":
        SQL ="update RtSQCLimit set %s = NULL where ParameterId = %d and Grade = '%s'" % (limitType, parameterId, grade)
    else:
        SQL = "update RtSQCLimit set %s = %s where ParameterId = %d and Grade = '%s'" % (limitType, str(newValue), parameterId, grade)
    print SQL
    system.db.runUpdateQuery(SQL)
    self.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)

def deleteColumns(event):
    print "In %s.deleteColumns()" % (__name__)
    rootContainer = event.source.parent
    familyName  = rootContainer.getComponent("FamilyDropdown").selectedStringValue
    recipeFamilyId = idForFamily(familyName)
    table = event.source.parent.getComponent("Power Table")
    ds = table.data
    column = table.selectedColumn
    columnName = ds.getColumnName(column)
    parameter = columnName[:len(columnName)-3]
    print "Deleting SQC Parameter: <%s>" % (parameter)
    
    SQL = "delete from RtSQCParameter where Parameter = '%s' and RecipeFamilyId = %d" % (parameter, recipeFamilyId)
    system.db.runUpdateQuery(SQL)
    
    requery(rootContainer)