'''
Created on Apr 19, 2019

@author: phass
'''

import system
from ils.dbManager.userdefaults import get as getUserDefaults
from ils.dbManager.sql import idForFamily, idForParameter
from ils.config.client import getDatabase
from ils.log import getLogger
log = getLogger(__name__)

POWER_TABLE_NAME = "SQC Table"

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
    family = getUserDefaults("FAMILY")
    if family == "<Family>":
        family = ""
    rootContainer.family = family
    
def internalFrameActivated(rootContainer):
    log.infof("In %s.internalFrameActivated", __name__)
    requery(rootContainer)

def requery(rootContainer):
    log.infof("In %s.requery", __name__)
    table = rootContainer.getComponent(POWER_TABLE_NAME)
    recipeFamilyName = rootContainer.family
    
    columns = fetchColumns(recipeFamilyName)
    grades = fetchRows(recipeFamilyName)
    pds = fetchData(recipeFamilyName)
    ds = mergeData(rootContainer, grades, columns, pds)
    table.data = ds
    
    gradeTable = rootContainer.getComponent("Grade Table")
    data = []
    for grade in grades:
        data.append([grade])
    ds = system.dataset.toDataSet(["Grade"], data)
    gradeTable.data = ds

    for col in range(ds.getColumnCount()):
        if col == 0:
            table.setColumnWidth(col, 70)
        else:
            table.setColumnWidth(col, 110)
    
def fetchColumns(recipeFamilyName):
    db = getDatabase()
    SQL = "select  P.Parameter "\
        "from RtSQCParameter P,  RtRecipeFamily F "\
        "where P.RecipeFamilyId = F.RecipeFamilyId "\
        " and F.RecipeFamilyName = '%s' order by Parameter" % (recipeFamilyName)
    pds = system.db.runQuery(SQL, database=db)
    
    columns = []
    for record in pds:
        columns.append(record["Parameter"] + "_LL")
        columns.append(record["Parameter"] + "_UL")
        
    print "Columns: ", columns
    return columns
    
def fetchRows(recipeFamilyName):
    db = getDatabase()
    SQL = "select distinct GM.Grade "\
        " from RtGradeMaster GM,  RtRecipeFamily RF "\
        " where RF.RecipeFamilyName = '%s' and GM.RecipeFamilyId = RF.RecipeFamilyId order by Grade" % (recipeFamilyName)

    print "SQL: ", SQL
    pds = system.db.runQuery(SQL, database=db)
    print "Selected %d grades..." % (len(pds))
    
    grades = []
    for record in pds:
        grades.append(record["Grade"])

    print "Grades: ", grades    
    return grades

def fetchData(recipeFamilyName):
    db = getDatabase()
    SQL = "select Grade, Parameter, UpperLimit, LowerLimit "\
        " from RtSQCLimitView "\
        " where RecipeFamilyName = '%s' order by Grade, Parameter" % (recipeFamilyName)
    pds = system.db.runQuery(SQL, database=db)
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
    db = getDatabase()
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
    
    rows = system.db.runUpdateQuery(SQL, database=db)
    
    if rows == 0:
        print "   --- no rows were updated, try to insert ---"
        if newValue == "":
            SQL = "INSERT INTO RtSQCLimit (ParameterId, Grade, %s) VALUES (%i, '%s')" % (limitType, parameterId, grade)
        else:
            SQL = "INSERT INTO RtSQCLimit (ParameterId, Grade, %s) VALUES (%i, '%s', %s)" % (limitType, parameterId, grade, str(newValue))
        print SQL
        rows = system.db.runUpdateQuery(SQL, database=db)
        if rows == 0:
            print "*** NO ROWS WERE ADDED ***"
    
    self.data = system.dataset.setValue(ds, rowIndex, colIndex, newValue)

def deleteColumns(event):
    print "In %s.deleteColumns()" % (__name__)
    db = getDatabase()
    rootContainer = event.source.parent
    familyName  = rootContainer.getComponent("FamilyDropdown").selectedStringValue
    recipeFamilyId = idForFamily(familyName)
    table = event.source.parent.getComponent(POWER_TABLE_NAME)
    ds = table.data
    column = table.selectedColumn
    columnName = ds.getColumnName(column)
    parameter = columnName[:len(columnName)-3]
    print "Deleting SQC Parameter: <%s>" % (parameter)
    
    SQL = "delete from RtSQCParameter where Parameter = '%s' and RecipeFamilyId = %d" % (parameter, recipeFamilyId)
    system.db.runUpdateQuery(SQL, database=db)

    requery(rootContainer)

def exportCallback(event):
    db = getDatabase()
    where = ""
    
    entireTable = system.gui.confirm("<HTML>You can export the entire table or just the selected family.  <br>Would you like to export the <b>entire</b> table?")
    if not(entireTable):
        family = getUserDefaults("FAMILY")
        if family not in ["ALL", "", "<Family>"]:
            where = " WHERE  RecipeFamilyName = '" + family+"'"
        
    SQL = "select RecipeFamilyName, Grade, Parameter, UpperLimit, LowerLimit "\
        " from RtSQCLimitView "\
        " %s order by RecipeFamilyName, Grade, Parameter" % (where)
    print SQL
        
    pds = system.db.runQuery(SQL, database=db)
    log.trace(SQL)
    print "Fetched %d rows of data..." % (len(pds))

    csv = system.dataset.toCSV(pds)
    filePath = system.file.saveFile("SqcLimits.csv", "csv", "Comma Separated Values")
    if filePath:
        system.file.writeFile(filePath, csv)