'''
Created on Oct 5, 2014

@author: Pete
'''
import sys, traceback
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit.ui")

def callback(event):
    log.info("Saving the modified recipe (ils.recipeToolkit.save.callback)")
    rootContainer = event.source.parent
    recipeKey = rootContainer.recipeKey
    grade = rootContainer.grade
    version = rootContainer.version
     
    from ils.recipeToolkit.fetch import fetchUnitId
    unitId = fetchUnitId(recipeKey)
    
    txId = system.db.beginTransaction()
    
    try:
        newVersion = insertGradeMaster(unitId, grade, txId)

        # Make an exact copy of the current master recipe with a new version
        insertRecipe(unitId, grade, newVersion, version, txId)

        # Update the copy with whatever the user edited.
        updateRecipe(event, unitId, grade, newVersion, txId)

    except:
        errorType,value,trace = sys.exc_info()
        errorTxt = traceback.format_exception(errorType, value, trace, 500)
        log.error("Caught an exception... \n%s" % (errorTxt) )
        system.db.rollbackTransaction(txId)
       
    else:
        log.trace("committing transactions")
        system.db.commitTransaction(txId)
        system.gui.messageBox("Version %s was successfully stored to the recipe database.  Version %s will remain the active version." % (newVersion, version))

    system.db.closeTransaction(txId)
    log.trace("Closing the database transaction")


# Get the highest existing version number and then increment it 
# (The version that we are viewing may not be the highest version)
def insertGradeMaster(unitId, grade, txId):
    log.trace("In insertGradeMaster()")
    
    SQL = "select max(version) from RtGradeMaster where UnitId = %i and Grade = %s" % (unitId, grade)
    log.trace(SQL)
    version = system.db.runScalarQuery(SQL, tx=txId)
    version = version + 1
    log.trace("The new version is: %i" % (version))

    SQL = "insert into RtGradeMaster (UnitId, Grade, Version, Timestamp, Active) " \
        "values (%i, '%s', %i, getdate(), 0)" % (unitId, grade, version)         
    log.trace(SQL)
    system.db.runUpdateQuery(SQL, tx=txId)
    
    log.trace("A new record has been inserted into RtGradeMaster")
    return version


def insertRecipe(unitId, grade, newVersion, version, txId):
    # Now copy the existing recipe
    SQL="INSERT INTO RtGradeDetail(UnitId,Grade,ValueId,Version,RecommendedValue,LowLimit,HighLimit) " \
            "SELECT UnitId, Grade, ValueId, %i, RecommendedValue,LowLimit,HighLimit FROM RtGradeDetail " \
            " WHERE UnitID=%s and Grade='%s' and version=%i" % (newVersion, str(unitId), grade, version)
    log.trace(SQL)
    rows=system.db.runUpdateQuery(SQL, tx=txId)
    log.trace("Inserted %i rows into RtGradeDetail" % (rows))

    
def updateRecipe(event, unitId, grade, newVersion, txId):
    table = event.source.parent.getComponent('Power Table')
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    for record in pds:
        valueId = record['ValueId']
        pend = record['Pend']
        lowLimit = record['Low Limit']
        highLimit = record['High Limit']
            
        updateGradeDetail(unitId, grade, newVersion, valueId, pend, lowLimit, highLimit, txId)

        
def updateGradeDetail(unitId, grade, version, valueId, pend, lowLimit, highLimit, txId):   
    if pend == '':
        pend = None
        
    if lowLimit == '':
        lowLimit = None

    if highLimit == '':
        highLimit = None

    SQL = "update RtGradeDetail set RecommendedValue = ?, LowLimit = ?, HighLimit = ? " \
        "where UnitId = ? and Grade = ? and Version = ? and  ValueId = ?" 
    log.trace("SQL: %s Values: %s, %s, %s, %s, %s, %s, %s" % (SQL, str(pend), str(lowLimit), str(highLimit), str(unitId), str(grade), str(version), str(valueId)))
    system.db.runPrepUpdate(SQL, args=[pend, lowLimit, highLimit, unitId, grade, version, valueId], tx=txId)
