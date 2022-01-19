'''
Created on Sep 10, 2014

@author: Pete
'''

import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit.sql")
 
def recipeFamily(familyName, db=""):
    SQL = "select F.RecipeFamilyId, P.Post, F.RecipeFamilyName, F.RecipeUnitPrefix, F.RecipeNameAlias, ConfirmDownload, "\
        " CurrentGrade, CurrentVersion, Status, Timestamp "\
        " from RtRecipeFamily F, TkPost P where F.PostId = P.PostId and F.RecipeFamilyName = '%s'" % (familyName)
    log.trace(SQL)
    
    pds = system.db.runQuery(SQL, database=db)
    log.trace("Fetched %i rows" % (len(pds)))
    
    if len(pds) == 1:
        record = pds[0]
    else:
        record = "Not Found"
    
    return record


def ids(familyName, db=""):
    SQL = "select GM.Grade, GM.Version, GM.Timestamp "\
        " from RtGradeMaster GM, RtRecipeFamily F "\
        " where F.RecipeFamilyId = GM.RecipeFamilyId "\
        " and F.RecipeFamilyName = '%s' and GM.active = 1 order by Grade, Version" % (familyName)
    log.trace(SQL)
    
    pds = system.db.runQuery(SQL, database=db)
    log.trace("Fetched %i rows" % (len(pds)))
    
    return pds

# Given a recipe family name and a grade, fetch the highest active version.
def fetchHighestVersion(familyName, grade, db=""):
    familyId = fetchFamilyId(familyName, db)
    log.trace("Fetching the highest ACTIVE version for family: %s (%s) - grade: %s" % (str(familyName), str(familyId), str(grade)))
    if familyId == None:
        return -1
    
    SQL = "select max(Version) from RtGradeMaster where RecipeFamilyId = %s and grade = '%s' and Active = 1" % (str(familyId), grade)
    log.trace(SQL)
    
    version = system.db.runScalarQuery(SQL, db)
    log.trace("Fetched version: %s" % (str(version)))

    return version


# Given a unit name, fetch the unitId from the recipe database.
# Note: If we consolidate the recipe database into the EMC database, then this will need to be updated and
# we could use the default database and wouldn't need to pass it.
def fetchFamilyId(familyName, db=""):
    SQL = "select RecipeFamilyId from RtRecipeFamily where RecipeFamilyName = '%s'" % (familyName)
    log.trace(SQL)
    
    familyId = system.db.runScalarQuery(SQL, database=db)
    log.trace("Fetched Family Id: %s" % (str(familyId)))

    return familyId


def details(familyName, grade, version, db=""): 
    print "Fetching the recipe for: %s - %s - %i" % (familyName, str(grade), version)
    
    familyId = fetchFamilyId(familyName, db)
       
    SQL = "select VD.PresentationOrder, VD.Description, VD.ChangeLevel, VD.ModeAttribute, VD.ModeValue, WL.Alias as WriteLocation, "\
        " GD.RecommendedValue, GD.HighLimit, GD.LowLimit, VD.StoreTag, VD.CompareTag, VD.ValueId, VT.ValueType "\
        " from  RtValueDefinition VD INNER JOIN RtValueType VT ON VD.ValueTypeId = VT.ValueTypeId "\
        " INNER JOIN RtGradeDetail GD ON VD.RecipeFamilyId = GD.RecipeFamilyId "\
        " AND VD.ValueId = GD.ValueId LEFT OUTER JOIN TkWriteLocation  WL ON VD.WriteLocationId = WL.WriteLocationId "\
        " where GD.RecipeFamilyId = %s "\
        " and GD.Grade = '%s'" \
        " and GD.Version = %s" \
        " and GD.RowActive = 1" \
        " order by PresentationOrder" % (str(familyId), grade, str(version))
    
    log.trace(SQL)

    pds = system.db.runQuery(SQL, database=db)
    log.trace("Fetched %i rows" % (len(pds)))
    
    '''
    Filter the data as a safety measure.  If there is a tagpath then there MUST be a value!
    Replace empty strings with NaN
    '''
    ds = system.dataset.toDataSet(pds)
    for row in range(ds.getRowCount()):
        description = ds.getValueAt(row, "Description")
        value = ds.getValueAt(row, "RecommendedValue")
        tag = ds.getValueAt(row, "StoreTag")
        
        if value in ["", None] and tag != None:
            log.infof("Found an NULL value for %s - %s that will be replaced with a NaN", description, tag)
            ds = system.dataset.setValue(ds, row, "RecommendedValue", "NaN")
    
    pds = system.dataset.toPyDataSet(ds)
    return pds