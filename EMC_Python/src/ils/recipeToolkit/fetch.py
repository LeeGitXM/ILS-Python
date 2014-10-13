'''
Created on Sep 10, 2014

@author: Pete
'''

import system
 
def map(recipeKey):
    SQL = "select * from RecipeMap where RecipeKey = '%s'" % (recipeKey)
    print SQL
    pds = system.db.runQuery(SQL)
    
    if len(pds) == 1:
        record = pds[0]
    else:
        record = "Not Found"
    
    return record


def ids(familyName):
    SQL = "select Grade, Version, Timestamp from RtGradeMaster GM, RtUnitRoot UR where UR.UnitId = GM.UnitId "\
        " and UR.FamilyName = '%s' and GM.active = 1 order by Grade, Version" % (familyName)
    print SQL
    pds = system.db.runQuery(SQL)
    
    return pds


# Given a unit name, fetch the unitId from the recipe database.
# Note: If we consolidate the recipe database into the EMC database, then this will need to be updated and
# we could use the default database and wouldn't need to pass it.
def fetchUnitId(unitName):
    SQL = "select unitId from RtUnitRoot where FamilyName = '%s'" % (unitName)
    unitId = system.db.runScalarQuery(SQL)
    return unitId


def details(unitName, grade, version):
    
    print "Fetching the recipe for: %s - %s - %i" % (unitName, str(grade), version)
    
    unitId = fetchUnitId(unitName)
    
    SQL = "select VD.PresentationOrder, VD.Description, VD.ChangeLevel, VD.ModeAttribute, VD.ModeValue, VD.WriteLocation, "\
        " GD.RecommendedValue, GD.HighLimit, GD.LowLimit, VD.StoreTag, VD.CompareTag, VD.ValueId "\
        " from RtGradeDetail GD, RtValueDefinition VD "\
        " where GD.ValueId = VD.ValueId "\
        " and GD.UnitId = %i "\
        " and GD.Grade = %s" \
        " and GD.Version = %i" \
        " order by PresentationOrder" % (unitId, grade, version)
    
    print SQL
    pds = system.db.runQuery(SQL)

    return pds