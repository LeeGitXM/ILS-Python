'''
Utilities for units of measure and conversion

Created on Sep 16, 2014

@author: rforbes
'''



class Unit(object):
    '''
    Represents a unit of measure, with reference to a base unit conversion
    '''
    unitsByName = dict()
    unitTypes = set()

    def __init__(self):
        '''
        Constructor
        '''
        self.name = ''
        self.type = ''
        self.description = ''
        self.isBaseUnit = False
        self.m = 0.
        self.b = 0.
  
    def toBaseUnits(self, y):
        '''convert the given number of this unit to the base unit'''
        if self.isBaseUnit:
            return y
        else:
            return (y - self.b) /self. m;
        
    def fromBaseUnits(self, x):
        '''convert the given number of base units to the this unit'''
        if self.isBaseUnit:
            return x
        else:
            return self.m * x + self.b;
    
    def convertTo(self, otherUnit, value):
        '''convert a value in my units to the given (other) units'''
        return otherUnit.fromBaseUnits(self.toBaseUnits(value))

    @staticmethod
    def convert(fromUnitName, toUnitName, value):
        fromUnit = Unit.getUnit(fromUnitName)
        toUnit = Unit.getUnit(toUnitName)
        return fromUnit.convertTo(toUnit, value)
        
    @staticmethod
    def addUnits(newUnitsByName):
        '''add some units to the global dictionary in addition to any already present.
           the input param is a dictionary; a unit that is indexed by a name different
           than its own in the dictionary represents an alias'''
        for key in newUnitsByName:
            newUnit = newUnitsByName[key]
            Unit.unitsByName[key] = newUnit
            Unit.unitTypes.add(newUnit.type)
        
    @staticmethod
    def clearUnits():
        '''clear all unit information'''
        Unit.unitsByName.clear()
        Unit.unitTypes.clear()
        
    @staticmethod
    def writeSql(filename):
        '''write a file that will insert all the unit info into a database,
           replacing whatever is there'''
        out = open(filename, 'w')
        out.write("delete from Units\nGO\n");
        out.write("delete from UnitAliases\nGO\n");
        for unit in Unit.unitsByName.values():
            out.write(unit.getInsertStatement())
        for key in Unit.unitsByName.keys():
            unit = Unit.unitsByName[key]
            if not key == unit.name:
                out.write(("insert into UnitAliases(alias, name) values(" + 
                    Unit.quoteSqlString(key) + ", " + 
                    Unit.quoteSqlString(unit.name)+ ")\nGO\n"))
        out.close()
    
    @staticmethod
    def getUnitTypes():
        '''Get all distinct unit types'''
        return Unit.unitTypes
    
    @staticmethod
    def getUnitsOfType(unitType):
        '''Get all the units of a particular type'''
        result = []
        for unit in Unit.unitsByName.values():
            if unit.type == unitType:
                result.append(unit.name)
        return result
    
    @staticmethod
    def getUnit(name):
        '''Get the unit with the given name (or alias)'''
        unit = Unit.unitsByName.get(name)
        if unit == None:
            print 'Failed to find unit: ' + name
        return unit

    def getInsertStatement(self):
        '''Get a sql statement that will insert this unit into a SQL Server database'''
        return ("insert into Units(name, description, type, m, b, isBaseUnit) values(" +
            Unit.quoteSqlString(self.name) + ", " +
            Unit.quoteSqlString(self.description) + ", " +
            Unit.quoteSqlString(self.type) + ", " +
            str(self.m) + ", " +
            str(self.b) + ", " +
            str(Unit.getBooleanInt(self.isBaseUnit)) + ")\nGO\n");

    @staticmethod
    def getBooleanInt(bval):
        if bval:
            return 1
        else:
            return 0
        
    @staticmethod
    def quoteSqlString(string):
        return "'" + string.replace("'", "''") + "'"

    @staticmethod
    def lazyInitialize(database):
        if len(Unit.unitsByName.keys()) == 0:
            Unit.readFromDb(database)
            
    @staticmethod
    def readFromDb(database):
        '''read unit info from the project's default database'''
        import system.db
        Unit.clearUnits()
        newUnits = dict()
        results = system.db.runQuery("select * from Units")
        # Read the units
        for row in results:
            unit = Unit()
            unit.name = row["name"]
            unit.description = row["description"];
            unit.type = row["type"]
            unit.m = row["m"]
            unit.b = row["b"]
            unit.isBaseUnit = row["isBaseUnit"]
            newUnits[unit.name] = unit
        Unit.addUnits(newUnits)
        print 'added units ', newUnits
        # Read the aliases
        newUnits = dict()
        results = system.db.runQuery("select * from UnitAliases")
        for row in results:
            realUnit = Unit.getUnit(row["name"])
            if realUnit != None:
                newUnits[row["alias"]] = realUnit
        Unit.addUnits(newUnits)
        
def unitsOfSameType(unitName):
    '''
    Get all units of the same type as the given one
    '''
    unit = Unit.getUnit(unitName)
    if unit != None:
        return Unit.getUnitsOfType(unit.type)
    else:
        print 'No unit named ', unitName
        return None