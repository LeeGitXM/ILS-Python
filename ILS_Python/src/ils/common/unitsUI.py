'''
Created on Feb 13, 2015

@author: Pete
'''
import ils.common.units
import system
 
UNIT_TYPES = "unitTypes"
FROM_VALUE = "fromValue"
TO_VALUE = "toValue"
FROM_UNITS = "fromUnits"
TO_UNITS = "toUnits"

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
    ils.common.units.Unit.insertDB("")

def clearMemoryCallback(rootContainer):
    ils.common.units.Unit.clearUnits()
   
def resetUI(container):
    unitTypes = ils.common.units.Unit.getUnitTypes("")
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
