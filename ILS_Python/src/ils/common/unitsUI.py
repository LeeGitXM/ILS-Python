'''
Created on Feb 13, 2015

@author: Pete
'''
import ils.common.units
import system
from ils.common.util import clearDataset
 
UNIT_TYPES = "unitTypes"
FROM_VALUE = "fromValue"
TO_VALUE = "toValue"
FROM_UNITS = "fromUnits"
TO_UNITS = "toUnits"

def internalFrameActivated(event):
    tabStrip=event.source.rootContainer.getComponent("Tab Strip")
    tabStrip.selectedTab="Configure"
    
    # The main table is automatically updated, clear the 3 other tables / lists
    rootContainer = event.source.rootContainer
    
    container = rootContainer.getComponent("Configure Container")
    
    powerTable = container.getComponent("Base Unit Container").getComponent("Power Table")
    powerTable.selectedRow = -1
    baseUnitContainer = container.getComponent("Base Unit Container")
    baseUnitContainer.selectedName = ""
    baseUnitContainer.type = ""
    
    aliasList = container.getComponent("Base Unit Container").getComponent("List")
    ds = aliasList.data
    ds = clearDataset(ds)
    print "Rows: ", ds.rowCount
    aliasList.data = ds
    
    conversionContainer = container.getComponent("Conversion Container")
    conversionContainer.selectedName = ""
    
    powerTable = container.getComponent("Conversion Container").getComponent("Power Table")
    ds = powerTable.data
    ds = clearDataset(ds)
    print "Rows: ", ds.rowCount
    powerTable.data = ds
    
    aliasList = container.getComponent("Conversion Container").getComponent("List")
    ds = aliasList.data
    ds = clearDataset(ds)
    print "Rows: ", ds.rowCount
    aliasList.data = ds


def getUnitsCallback():
    ds=ils.common.units.getUnits()
    return ds

def loadUnitsFromDBCallback(container, db=""):
    ils.common.units.Unit.readFromDb(db)
    resetUI(container)

def clearDBCallback(container, db=""):
    ils.common.units.Unit.clearDBUnits(db)
    resetUI(container)
        
def loadUnitsFromFileCallback(container):
    fileName = system.file.openFile()
    if fileName != None:
        newUnits = ils.common.units.parseUnitFile(fileName)
        ils.common.units.Unit.addUnits(newUnits)    
        resetUI(container)

def insertIntoDatabaseCallback(rootContainer):
    ils.common.units.Unit.insertDB()

def clearMemoryCallback(rootContainer):
    ils.common.units.Unit.clearUnits()
   
def resetUI(container):
    unitTypes = ils.common.units.Unit.getUnitTypes()
    typesCombo = container.getComponent(UNIT_TYPES)
    setComboValues(typesCombo, unitTypes)
    fromUnitCombo = container.getComponent(FROM_UNITS)
    setComboValues(fromUnitCombo, [])
    toUnitCombo = container.getComponent(TO_UNITS)
    setComboValues(toUnitCombo, [])
 
def typeSelected(container):
    selectedType = container.getComponent(UNIT_TYPES).selectedStringValue
    print "The selected type is: ", selectedType
    if selectedType != None:
        unitsOfSelectedType = ils.common.units.Unit.getUnitsOfType(selectedType)
    else:
        unitsOfSelectedType = []
        
    print "The list of units is: ", unitsOfSelectedType
    fromUnitCombo = container.getComponent(FROM_UNITS)
    setComboValues(fromUnitCombo, unitsOfSelectedType)
    
    toUnitCombo = container.getComponent(TO_UNITS)
    setComboValues(toUnitCombo, unitsOfSelectedType)
    
def setComboValues(combo, values):
    rows = []
    for value in values:
        rows.append([value])
    dataset = system.dataset.toDataSet(["values"], rows)
    combo.data = dataset
    
def getComboSelection(combo):
    if combo.selectedIndex != -1:
        return combo.selectedStringValue
    else:
        return None
        
def doConversion(container):    
    fromValue = container.getComponent(FROM_VALUE).doubleValue
    fromUnitName = getComboSelection(container.getComponent(FROM_UNITS))
    toUnitName = getComboSelection(container.getComponent(TO_UNITS))
    if fromUnitName == None or toUnitName == None:
        return
    newToValue = ils.common.units.Unit.convert(fromUnitName, toUnitName, fromValue)
    container.getComponent(TO_VALUE).doubleValue = newToValue

'''
Methods for adding and deleting from the config UI
'''

def addBaseUnit(event):
    container = event.source.parent
    powerTable = container.getComponent("Power Table")
    unitType = system.gui.inputBox("Enter new unit type")
    if unitType == None:
        return
    
    unitName = system.gui.inputBox("Enter new base unit name for %s" % unitType)
    if unitName == None:
        return
    
    SQL = "Insert into Units (name, isBaseUnit, type) values ('%s', 1, '%s')" % (unitName, unitType)
    print SQL
    system.db.runUpdateQuery(SQL)
    system.db.refresh(powerTable, "data")
    
def updateBaseUnits(powerTable, rowIndex, colIndex, colName, oldValue, newValue):
    unitId = powerTable.data.getValueAt(rowIndex, 0)
    
    ''' The only thing they can update is description (a string) for a base unit '''
    SQL = "update Units set %s = '%s' where id = %d" % (colName, newValue, unitId)        
    print SQL
    rows = system.db.runUpdateQuery(SQL)
    print "%d rows were updated" % (rows)
    
    ''' 
    If I refresh the component from the databas ethen the current selection will be lost and if the user wants to tab across a row he will be frustrated!
    Instead I will directly update the dataset and hopefully the DB and table will be in sync 
    '''
    #system.db.refresh(powerTable, "data")
    powerTable.data = system.dataset.setValue(powerTable.data, rowIndex, colIndex, newValue)
        
def deleteBaseUnit(event):
    container = event.source.parent
    powerTable = container.getComponent("Power Table")
    unitType = powerTable.data.getValueAt(powerTable.selectedRow, 1)
    unitName = powerTable.data.getValueAt(powerTable.selectedRow, 2)
    
    ''' Delete aliases first '''
    aliasRows = 0
    SQL = "delete from UnitAliases where Name = '%s' " % (unitName)
    print SQL
    rows = system.db.runUpdateQuery(SQL)
    aliasRows = aliasRows + rows
    
    SQL = "select name from Units where type = '%s' " % unitType
    pds = system.db.runQuery(SQL)
    for record in pds:
        SQL = "Delete from UnitAliases where Name = '%s' " % (record["name"])
        print SQL
        rows = system.db.runUpdateQuery(SQL)
        aliasRows = aliasRows + rows
    print "%d aliases were deleted" % (aliasRows)
        
    ''' Now delete the unit definition - the name has a unique index, so I don't need the type here '''
    SQL = "delete from Units where Type = '%s' " % (unitType)
    print SQL
    rows = system.db.runUpdateQuery(SQL)
    print "%d base and related units were deleted" % (rows)
    
    system.db.refresh(powerTable, "data")
    powerTable.selectedRow = -1
    
    aliasList = container.getComponent("List")
    system.db.refresh(aliasList, "data")
    
    powerTable = event.source.parent.parent.getComponent("Conversion Container").getComponent("Power Table")
    system.db.refresh(powerTable, "data")
    powerTable.selectedRow = -1
    
    aliasList = event.source.parent.parent.getComponent("Conversion Container").getComponent("List")
    system.db.refresh(aliasList, "data")

def addBaseUnitAlias(event):
    container = event.source.parent
    powerTable = container.getComponent("Power Table")
    unitType = powerTable.data.getValueAt(powerTable.selectedRow, 1)
    unitName = powerTable.data.getValueAt(powerTable.selectedRow, 2)
    aliasList = container.getComponent("List")
    alias = system.gui.inputBox("Enter new alias for base unit %s (a %s)" % (unitName, unitType))
    if alias != None:
        SQL = "Insert into UnitAliases (alias, name) values ('%s', '%s')" % (alias, unitName)
        print SQL
        system.db.runUpdateQuery(SQL)
        system.db.refresh(aliasList, "data")

def deleteBaseUnitAlias(event):
    container = event.source.parent
    powerTable = container.getComponent("Power Table")
    unitName = powerTable.data.getValueAt(powerTable.selectedRow, 2)
    aliasList = container.getComponent("List")
    idx = aliasList.selectedIndex
    alias = aliasList.data.getValueAt(idx,0)
    print "Delete ", alias
    SQL = "delete from UnitAliases where alias = '%s' and name = '%s' " % (alias, unitName)
    print SQL
    rows = system.db.runUpdateQuery(SQL)
    print "%d rows were deleted" % (rows)
    system.db.refresh(aliasList, "data")

def addRelatedUnit(event):
    container = event.source.parent.parent
    powerTable = container.getComponent("Base Unit Container").getComponent("Power Table")
    unitType = powerTable.data.getValueAt(powerTable.selectedRow, 1)
    unitName = system.gui.inputBox("Enter new related unit for %s" % unitType)
    if unitName != None:
        SQL = "Insert into Units (name, isBaseUnit, type) values ('%s', 0, '%s')" % (unitName, unitType)
        print SQL
        system.db.runUpdateQuery(SQL)
        powerTable = container.getComponent("Conversion Container").getComponent("Power Table")
        system.db.refresh(powerTable, "data")

def updateRelatedUnits(powerTable, rowIndex, colIndex, colName, oldValue, newValue):
    unitId = powerTable.data.getValueAt(rowIndex, 0)
    
    if colName in ['description']:
        SQL = "update Units set %s = '%s' where id = %d" % (colName, newValue, unitId)
    else:
        SQL = "update Units set %s = %s where id = %d" % (colName, str(newValue), unitId)
        
    print SQL
    rows = system.db.runUpdateQuery(SQL)
    print "%d rows were updated" % (rows)
    
    ''' 
    If I refresh the component from the databas ethen the current selection will be lost and if the user wants to tab across a row he will be frustrated!
    Instead I will directly update the dataset and hopefully the DB and table will be in sync 
    '''
    #system.db.refresh(powerTable, "data")
    powerTable.data = system.dataset.setValue(powerTable.data, rowIndex, colIndex, newValue)
    
def deleteRelatedUnit(event):
    container = event.source.parent
    powerTable = container.getComponent("Power Table")
    aliasList = container.getComponent("List")
    unitName = powerTable.data.getValueAt(powerTable.selectedRow, 1)
    
    ''' Delete aliases first '''
    SQL = "delete from UnitAliases where Name = '%s' " % (unitName)
    print SQL
    rows = system.db.runUpdateQuery(SQL)
    print "%d aliases were deleted" % (rows)
    
    ''' Now delete the unit definition - the name has a unique index, so I don't need the type here '''
    SQL = "delete from Units where Name = '%s' " % (unitName)
    print SQL
    rows = system.db.runUpdateQuery(SQL)
    print "%d units were deleted" % (rows)
    
    system.db.refresh(powerTable, "data")
    system.db.refresh(aliasList, "data")
    powerTable.selectedRow = -1
    
    
def addUnitAlias(event):
    container = event.source.parent
    powerTable = container.getComponent("Power Table")
    unitName = powerTable.data.getValueAt(powerTable.selectedRow, 1)
    aliasList = container.getComponent("List")
    alias = system.gui.inputBox("Enter new alias for %s" % unitName)
    if alias != None:
        SQL = "Insert into UnitAliases (alias, name) values ('%s', '%s')" % (alias, unitName)
        print SQL
        system.db.runUpdateQuery(SQL)
        system.db.refresh(aliasList, "data")
    
def deleteUnitAlias(event):
    container = event.source.parent
    powerTable = container.getComponent("Power Table")
    unitName = powerTable.data.getValueAt(powerTable.selectedRow, 1)
    aliasList = container.getComponent("List")
    idx = aliasList.selectedIndex
    alias = aliasList.data.getValueAt(idx,0)
    print "Delete ", alias
    SQL = "delete from UnitAliases where alias = '%s' and name = '%s' " % (alias, unitName)
    print SQL
    rows = system.db.runUpdateQuery(SQL)
    print "%d rows were deleted" % (rows)
    system.db.refresh(aliasList, "data")