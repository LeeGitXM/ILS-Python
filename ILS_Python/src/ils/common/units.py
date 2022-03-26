'''
Utilities for units of measure and conversion

Created on Sep 16, 2014

@author: rforbes
'''
import system, sys, string
from ils.common.error import catchError
from ils.log import getLogger
logger = getLogger(__name__)

FACTOR = 'FACTOR'
ALIAS = 'ALIAS'
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
    def convert(fromUnitName, toUnitName, value):
        if fromUnitName == toUnitName:
            return value;
        else:
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
    def clearDBUnits(db):
        '''clear all unit information in the '''
        system.db.runUpdateQuery("delete from UnitAliases", db)
        system.db.runUpdateQuery("delete from Units", db)
        
    @staticmethod
    def insertDB():
        '''This used to write a file that then had to somehow be inserted into 
           the , it's much easier to just insert it here!'''
        Unit.clearDBUnits("")
        for unit in Unit.unitsByName.values():
            SQL=unit.getInsertStatement()
            try:
                system.db.runUpdateQuery(SQL, )
            except:
                logger.errorf("Unit insert failed: %s", SQL)
                
        for key in Unit.unitsByName.keys():
            unit = Unit.unitsByName[key]
            if not key == unit.name:
                try:
                    SQL = "insert into UnitAliases(alias, name) values('%s', '%s')" % (key, unit.name)
                    system.db.runUpdateQuery(SQL, )
                except:
                    logger.errorf("Failed Alias insert: %s", SQL)
    
    @staticmethod
    def getUnitTypes():
        '''Get all distinct unit types'''
        return Unit.unitTypes
    
    @staticmethod
    def getUnits():
        '''Get all the units that are loaded in memory (in the callers scope)'''
        header=["Name", "Type","Description","Base","Slope","Y-Intercept"]
        vals=[]
        for key in Unit.unitsByName.keys():
            val=[]
            unit = Unit.unitsByName[key]
            val.append(key)
            val.append(unit.type)
            val.append(unit.description)
            val.append(unit.isBaseUnit)
            val.append(unit.m)
            val.append(unit.b)
            vals.append(val)
        ds = system.dataset.toDataSet(header, vals)
        return ds
    
    @staticmethod
    def getUnitsOfType(unitType):
        '''Get all the units of a particular type'''
        result = []
        for unit in Unit.unitsByName.values():
            if unit.type == unitType:
                result.append(unit.name)
        print "Unsorted: ", result
        result.sort()
        print "Sorted: ", result
        return result
    
    @staticmethod
    def getUnit(name):
        if name == None:
            return None
        '''Get the unit with the given name (or alias)'''
        unit = Unit.unitsByName.get(name)
        if unit == None:
            # should use a logger here
            logger.errorf('Failed to find unit: %s', name)
        return unit

    def getInsertStatement(self):
        '''Get a sql statement that will insert this unit into a SQL Server '''
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
    def lazyInitialize(db):
        if len(Unit.unitsByName.keys()) == 0:
            logger.info("Initializing the units object...")
            Unit.readFromDb(db)
            
    @staticmethod
    def readFromDb(db):
        '''read unit info from the project's default '''

        try:
            logger.info("Loading units...")
            results = system.db.runQuery("select * from Units", database=db)
            logger.infof("...read %d units...", len(results))
            # Read the units
            Unit.clearUnits()
            newUnits = dict()
            for row in results:
                unit = Unit()
                unit.name = string.upper(row["name"])
                unit.description = row["description"];
                unit.type = row["type"]
                unit.m = row["m"]
                unit.b = row["b"]
                unit.isBaseUnit = row["isBaseUnit"]
                newUnits[unit.name] = unit
                
            Unit.addUnits(newUnits)
            # Read the aliases
            newUnits = dict()
            results = system.db.runQuery("select * from UnitAliases", database=db)
            logger.infof("...read %d aliases...", len(results))
            for row in results:
                realUnit = Unit.getUnit(string.upper(row["name"]))
                if realUnit != None:
                    newUnits[string.upper(row["alias"])] = realUnit
            Unit.addUnits(newUnits)
            logger.infof("...done loading units!")
        except:
            errorTxt = catchError("Error fetching Units")
            logger.errorf(errorTxt)

def getUnits():
    return Unit.getUnits()

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
        
def unitsOfSameType(unitName):
    '''
    Get all units of the same type as the given one
    '''
    unit = Unit.getUnit(unitName, )
    if unit != None:
        return Unit.getUnitsOfType(unit.type)
    else:
        logger.warnf('No unit named %s', unitName)
        return None

# Read a unit file and convert it into Unit objects
def parseUnitFile(unitfile):
    import ils.common.units
    
    unitsByName = dict()
    unitsByName = Unit.unitsByName
    print "There are currently %d units in memory..." % (len(list(unitsByName.keys())))
    i = 0
    j = 0

    for line in open(unitfile, 'r').xreadlines():
        isFactor = string.upper(line).find(FACTOR) != -1
        isAlias = string.upper(line).find(ALIAS) != -1
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
            i = i + 1
            unit = ils.common.units.Unit()
            unit.isBaseUnit = tokens[3] == BASEUNIT
            unit.name = name1
            unit.type = name2
            print "Loading a new factor: %s of type %s" % (name1, name2)
            unit.description = description
            unitsByName[unit.name] = unit
            if not unit.isBaseUnit:
                unit.m = float(tokens[3].replace('D', 'E'))
                unit.b = float(tokens[4].replace('D', 'E'))
 
        elif isAlias:
            j = j + 1
            print "Loading a new alias: %s which is equivalent to %s" % (name1, name2)
            realUnit = unitsByName[name2]
            if realUnit != None:
                unitsByName[name1] = realUnit       
            else:
                errMsg = "unit " + name2 + " for alias " + name1 + " not found"
    
    print "Loaded %d unit definitions" % (i)
    print "Loaded %d unit aliases" % (j)

    return unitsByName
    
# If this is run from a client or the designer, then we probably don't need a db string
def convert(fromUnitName, toUnitName, value, db=""):
    logger.tracef("Converting %s from %s to %s", str(value), fromUnitName, toUnitName)
    lazyInitialize(db)
    return Unit.convert(string.upper(fromUnitName), string.upper(toUnitName), value)

def lazyInitialize(db):
    Unit.lazyInitialize(db)