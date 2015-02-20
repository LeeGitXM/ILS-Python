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
conversionPanel = None

def internalFrameOpened(rootContainer):
    ils.common.unitsUI.conversionPanel = rootContainer.getComponent("conversion")
    
def loadUnitsFromFileCallback(rootContainer):
    fileName = system.file.openFile()
    if fileName != None:
        newUnits = ils.common.units.parseUnitFile(fileName)
        ils.common.units.Unit.addUnits(newUnits)    
        resetUnits()

def insertIntoDatabaseCallback(rootContainer):
    ils.common.units.Unit.insertDB("")

def clearMemoryCallback(rootContainer):
    ils.common.units.Unit.clearUnits()
    resetUnits()

def getComponent(name):
    return conversionPanel.getComponent(name)
    
def resetUnits():
    unitTypes = ils.common.units.Unit.getUnitTypes("")
    typesCombo = getComponent(UNIT_TYPES)
    setComboValues(typesCombo, unitTypes)
    fromUnitCombo = getComponent(FROM_UNITS)
    setComboValues(fromUnitCombo, [])
    toUnitCombo = getComponent(TO_UNITS)
    setComboValues(toUnitCombo, [])
 
def typeSelected():
    selectedType = getComponent(UNIT_TYPES).selectedStringValue
    if selectedType != None:
        unitsOfSelectedType = ils.common.units.Unit.getUnitsOfType(selectedType, "")
    else:
        unitsOfSelectedType = []
    fromUnitCombo = getComponent(FROM_UNITS)
    setComboValues(fromUnitCombo, unitsOfSelectedType)
    toUnitCombo = getComponent(TO_UNITS)
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
        
def doConversion():
    
    fromValue = getComponent(FROM_VALUE).doubleValue
    fromUnitName = getComboSelection(getComponent(FROM_UNITS))
    toUnitName = getComboSelection(getComponent(TO_UNITS))
    if fromUnitName == None or toUnitName == None:
        return        
    fromUnit = ils.common.units.Unit.getUnit(fromUnitName, "")
    toUnit = ils.common.units.Unit.getUnit(toUnitName, "")
    newToValue = toUnit.fromBaseUnits(fromUnit.toBaseUnits(fromValue))
    getComponent(TO_VALUE).doubleValue = newToValue
