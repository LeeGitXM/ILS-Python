'''
Created on Oct 5, 2014

@author: Pete
'''
import sys, traceback, system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
from ils.recipeToolkit.fetch import fetchFamilyId
from ils.recipeToolkit.common import checkForUncommentedChanges
from ils.common.error import catchError
log = LogUtil.getLogger("com.ils.recipeToolkit.ui")

def callback(event):
    log.info("Saving the modified recipe (ils.recipeToolkit.save.callback)")
    rootContainer = event.source.parent
    familyName = rootContainer.familyName
    grade = rootContainer.grade
    version = rootContainer.version
    
    provider = rootContainer.getPropertyValue("provider")
    requireComments = system.tag.read("[" + provider + "]/Configuration/RecipeToolkit/requireCommentsForChangedValues").value
    if requireComments:
        uncommentedChanges = checkForUncommentedChanges(rootContainer)
        if uncommentedChanges:
            system.gui.messageBox("Please enter comments for any changed values before saving recipe!")
            return
    
    recipeFamilyId = fetchFamilyId(familyName)
    
    txId = system.db.beginTransaction()
    
    try:
        newVersion = insertGradeMaster(recipeFamilyId, grade, txId)

        # Make an exact copy of the current master recipe with a new version
        insertRecipe(recipeFamilyId, grade, newVersion, version, txId)

        # Update the copy with whatever the user edited.
        updateRecipe(event, recipeFamilyId, grade, newVersion, txId)

    except:
        txt = catchError("%s.callback" % (__name__), "Caught error while saving a new version of the recipe")
        log.error(txt )
        system.db.rollbackTransaction(txId)
       
    else:
        log.trace("committing transactions")
        system.db.commitTransaction(txId)
        system.gui.messageBox("Version %s was successfully stored to the recipe database.  Version %s will remain the active version." % (newVersion, version))

    system.db.closeTransaction(txId)
    log.trace("Closing the database transaction")


# Get the highest existing version number and then increment it 
# (The version that we are viewing may not be the highest version)
def insertGradeMaster(recipeFamilyId, grade, txId):
    log.trace("In insertGradeMaster()")
    
    SQL = "select max(version) from RtGradeMaster where RecipeFamilyId = %i and Grade = '%s'" % (recipeFamilyId, grade)
    log.trace(SQL)
    version = system.db.runScalarQuery(SQL, tx=txId)
    version = version + 1
    log.trace("The new version is: %i" % (version))

    SQL = "insert into RtGradeMaster (RecipeFamilyId, Grade, Version, Timestamp, Active) " \
        "values (%i, '%s', %i, getdate(), 0)" % (recipeFamilyId, grade, version)         
    log.trace(SQL)
    system.db.runUpdateQuery(SQL, tx=txId)
    
    log.trace("A new record has been inserted into RtGradeMaster")
    return version


def insertRecipe(recipeFamilyId, grade, newVersion, version, txId):
    # Now copy the existing recipe
    SQL="INSERT INTO RtGradeDetail(RecipeFamilyId,Grade,ValueId,Version,RecommendedValue,LowLimit,HighLimit) " \
            "SELECT RecipeFamilyId, Grade, ValueId, %i, RecommendedValue,LowLimit,HighLimit FROM RtGradeDetail " \
            " WHERE RecipeFamilyId=%s and Grade='%s' and version=%i" % (newVersion, str(recipeFamilyId), grade, version)
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, tx=txId)
    log.trace("Inserted %i rows into RtGradeDetail" % (rows))


def updateRecipe(event, recipeFamilyId, grade, newVersion, txId):
    table = event.source.parent.getComponent('Power Table')
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    for record in pds:
        valueId = record['ValueId']
        pend = record['Pend']
        lowLimit = record['Low Limit']
        highLimit = record['High Limit']

        updateGradeDetail(recipeFamilyId, grade, newVersion, valueId, pend, lowLimit, highLimit, txId)

        
def updateGradeDetail(recipeFamilyId, grade, version, valueId, pend, lowLimit, highLimit, txId):   
    if pend == '':
        pend = None

    if lowLimit == '':
        lowLimit = None

    if highLimit == '':
        highLimit = None

    SQL = "update RtGradeDetail set RecommendedValue = ?, LowLimit = ?, HighLimit = ? " \
        "where RecipeFamilyId = ? and Grade = ? and Version = ? and  ValueId = ?" 

    log.trace("SQL: %s Values: %s, %s, %s, %s, %s, %s, %s" % (SQL, str(pend), str(lowLimit), str(highLimit), str(recipeFamilyId), str(grade), str(version), str(valueId)))
    system.db.runPrepUpdate(SQL, args=[pend, lowLimit, highLimit, recipeFamilyId, grade, version, valueId], tx=txId)
