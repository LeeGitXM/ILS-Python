'''
Created on Oct 5, 2014

@author: Pete
'''

import system

def callback(event):
    print "in ils.recipeToolkit.save.callbaclk()"
    rootContainer = event.source.parent
    recipeKey = rootContainer.recipeKey
    grade = rootContainer.grade
       
    from ils.recipeToolkit.fetch import fetchUnitId
    unitId = fetchUnitId(recipeKey)

    txId = system.db.beginTransaction()
    try:
        version = insertGradeMaster(unitId, grade, txId)
    
        table = event.source.parent.getComponent('Power Table')
        ds = table.data
        pds = system.dataset.toPyDataSet(ds)
        for record in pds:
            print record
            valueId = record['ValueId']
            pend = record['Pend']
            lowLimit = record['Low Limit']
            highLimit = record['High Limit']
            
            insertGradeDetail(unitId, grade, version, valueId, pend, lowLimit, highLimit, txId)
    
    except:
        print "Caught an exception - rolling back transactions"
        system.db.rollbackTransaction(txId)
    else:
        print "committing transactions"
        system.db.commitTransaction(txId)
    
    system.db.closeTransaction(txId)
    print "Closing the database transaction"

def insertGradeMaster(unitId, grade, txId):
    print "In insertGradeMaster()"
    
    SQL = "select max(version) from GradeMaster where UnitId = %i and Grade = %s" % (unitId, grade)
    version = system.db.runScalarQuery(SQL, tx=txId)
    version = version + 1

    SQL = "insert into GradeMaster (UnitId, Grade, Version, Timestamp, Active) " \
        "values (%i, '%s', %i, getdate(), 0)" % (unitId, grade, version)
         
    print SQL
    system.db.runUpdateQuery(SQL, tx=txId)
    
    return version

def insertGradeDetail(unitId, grade, version, valueId, pend, lowLimit, highLimit, txId):
    print "In insert Grade Detail"
    
# The problem with this version is the handling of NULL values.  It insert the text string
# 'none' where the special value of NULL is preferred.
#    SQL = "insert into GradeDetail (UnitId, Grade, Version, ValueId, RecommendedValue, LowLimit, HighLimit) " \
#        "values (%i, '%s', %i, %i, '%s', '%s', '%s' )" % (unitId, grade, version, valueId, str(pend), str(lowLimit), str(highLimit))
#    print SQL
#    system.db.runUpdateQuery(SQL, tx=txId)

    if pend == '':
        pend = None
        
    if lowLimit == '':
        lowLimit = None

    if highLimit == '':
        highLimit = None

    SQL = "insert into GradeDetail (UnitId, Grade, Version, ValueId, RecommendedValue, LowLimit, HighLimit) " \
        "values (?, ?, ?, ?, ?, ?, ?)"
    print SQL
    system.db.runPrepUpdate(SQL, args=[unitId, grade, version, valueId, pend, lowLimit, highLimit], tx=txId)
