'''
Utilities for units of measure and conversion

Created on Sep 16, 2014

@author: rforbes
'''
import system

FACTOR = 'FACtor'
ALIAS = 'ALIas'
BASEUNIT = 'BASEUNIT'

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
  
    def toBaseUnits(self, myUnits):
        '''convert the given number of this unit to the base unit'''
        if self.isBaseUnit:
            return myUnits
        else:
            return (myUnits - self.b) /self.m;
        
    def fromBaseUnits(self, baseUnits):
        '''convert the given number of base units to the this unit'''
        if self.isBaseUnit:
            return baseUnits
        else:
            return self.m * baseUnits + self.b;
     
    def convertTo(self, otherUnit, value):
        '''convert a value in my units to the given (other) units'''
        return otherUnit.fromBaseUnits(self.toBaseUnits(value))

    @staticmethod
    def convert(fromUnitName, toUnitName, value, database):
        fromUnit = Unit.getUnit(fromUnitName, database)
        toUnit = Unit.getUnit(toUnitName, database)
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
    def insertDB(database = None):
        '''This used to write a file that then had to somehow be inserted into 
           the database, it's much easier to just insert it here!'''
        tx=system.db.beginTransaction(database)
        system.db.runUpdateQuery("delete from Units", tx=tx)
        system.db.runUpdateQuery("delete from UnitAliases", tx=tx)
        for unit in Unit.unitsByName.values():
            system.db.runUpdateQuery(unit.getInsertStatement(), tx=tx)
        for key in Unit.unitsByName.keys():
            unit = Unit.unitsByName[key]
            if not key == unit.name:
                SQL = "insert into UnitAliases(alias, name) values('%s', '%s')" % (key, unit.name)
                system.db.runUpdateQuery(SQL, tx=tx)
        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx)
    
    @staticmethod
    def getUnitTypes(database = None):
        '''Get all distinct unit types'''
        Unit.lazyInitialize(database)
        return Unit.unitTypes
    
    @staticmethod
    def getUnitsOfType(unitType, database = None):
        '''Get all the units of a particular type'''
        Unit.lazyInitialize(database)
        result = []
        for unit in Unit.unitsByName.values():
            if unit.type == unitType:
                result.append(unit.name)
        return result
    
    @staticmethod
    def getUnit(name, database = None):
        '''Get the unit with the given name (or alias)'''
        Unit.lazyInitialize(database)
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
            str(Unit.getBooleanInt(self.isBaseUnit)) + ")");

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
    def lazyInitialize(database = None):
        from ils.sfc.common.util import getDatabaseFromSystem
        if database == None:
            database = getDatabaseFromSystem();
        if len(Unit.unitsByName.keys()) == 0:
            Unit.readFromDb(database)
            
    @staticmethod
    def readFromDb(database):
        '''read unit info from the project's default database'''
        import system.db
        import sys
        
        try:
        
            results = system.db.runQuery("select * from Units")
            # Read the units
            Unit.clearUnits()
            newUnits = dict()
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
            # Read the aliases
            newUnits = dict()
            results = system.db.runQuery("select * from UnitAliases")
            for row in results:
                realUnit = Unit.getUnit(row["name"])
                if realUnit != None:
                    newUnits[row["alias"]] = realUnit
            Unit.addUnits(newUnits)
        except:
            print "units.py: Exception reading units database: " + str(sys.exc_info()[0])+str(sys.exc_info()[1])

def getUnitTypes():
    return list(Unit.getUnitTypes())
 
def getUnitsOfType(unitType):
    return Unit.getUnitsOfType(unitType)

def getTypeOfUnit(unitName):
    unit = Unit.getUnit(unitName)
    if unit != None:
        return unit.type
    else:
        return None
        
def unitsOfSameType(unitName, database = None):
    '''
    Get all units of the same type as the given one
    '''
    unit = Unit.getUnit(unitName, database)
    if unit != None:
        return Unit.getUnitsOfType(unit.type)
    else:
        print 'No unit named ', unitName
        return None

# Read a unit file and convert it into Unit objects
def parseUnitFile(unitfile):
    import ils.common.units
    
    unitsByName = dict()

    for line in open(unitfile, 'r').xreadlines():
        isFactor = line.find(FACTOR) != -1
        isAlias = line.find(ALIAS) != -1
        isComment = line[0] == '*'
        
        if isComment or not(isFactor | isAlias):
            continue
        description = ''
        
        # extract the description, if there is one (ignore alias descriptions tho)
        exclamIndex = line.find('!')
        if exclamIndex != -1: # trailing description
            description = line[exclamIndex+1 : len(line)].strip()
            line = line[0 : exclamIndex]
        
        quotedToken = None
        tokens = []
        for token in line.split():
            if quotedToken != None:
                if token.endswith('"'):
                    quotedToken = quotedToken + token
                    tokens.append(quotedToken[1 : len(quotedToken)-1])
                    quotedToken = None
            elif token.startswith('"'):
                quotedToken = token
            else :
                tokens.append(token)
                
        name1 = tokens[1]
        name2 = tokens[2]
        if isFactor:
            unit = ils.common.units.Unit()
            unit.isBaseUnit = tokens[3] == BASEUNIT
            unit.name = name1
            unit.type = name2
            unit.description = description
            unitsByName[unit.name] = unit
            if not unit.isBaseUnit:
                unit.m = float(tokens[3].replace('D', 'E'))
                unit.b = float(tokens[4].replace('D', 'E'))
 
        elif isAlias:
            realUnit = unitsByName[name2]
            if realUnit != None:
                unitsByName[name1] = realUnit       
            else:
                errMsg = "unit " + name2 + " for alias " + name1 + " not found"
    
    return unitsByName
    
