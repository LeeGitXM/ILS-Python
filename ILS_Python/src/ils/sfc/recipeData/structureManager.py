'''
Created on Dec 29, 2016

@author: phass
'''

import system, string
from ils.common.config import getTagProvider, getDatabase
from ils.common.util import formatDateTimeForDatabase
log = system.util.getLogger("com.ils.sfc.structureManager.python")
parseLog = system.util.getLogger("com.ils.sfc.structureManager.xmlParser")
from ils.common.error import catchError
from ils.sfc.recipeData.core import fetchStepTypeIdFromFactoryId, fetchStepIdFromUUID, fetchChartIdFromChartPath, fetchStepIdFromChartIdAndStepName
from ils.common.database import toList

def getTxId(db):
    txId = system.db.beginTransaction(database=db, timeout=86400000)    # timeout is one day
    return txId

def createChart(resourceId, chartPath, db):
    # Check if the chart already exists 
    log.infof("In %s.createChart() with %s-%s...", __name__, chartPath, str(resourceId))
    
    print "*************************************************"
    print "** WHY AM I HERE????"
    print "*************************************************"
    return

    txId = getTxId(db)    
    print "The transactionId is: ", txId

    try:
        log.tracef("...updating the chartPath <%s> for a record in sfcChart by resourceId: %d...", chartPath, resourceId)
        SQL = "update SfcChart set ChartPath = '%s' where chartResourceId = %d" % (chartPath, resourceId)
        log.tracef(SQL)
        rows = system.db.runUpdateQuery(SQL, tx=txId)
        
        if rows > 0:
            return 
        
        log.tracef("...updating the resourceId <%d> for a record in sfcChart by chartPath <%s>...", resourceId, chartPath)
        SQL = "update SfcChart set chartResourceId = %d where ChartPath = '%s'" % (resourceId, chartPath)
        log.tracef(SQL)
        rows = system.db.runUpdateQuery(SQL, tx=txId)
        
        if rows > 0:
            return
        
        log.tracef("Inserting a new record into SfcChart for %s - %d...", chartPath, resourceId)
        SQL = "insert into SfcChart (ChartPath, chartResourceId, CreateTime) values ('%s', %d, getdate())" % (chartPath, resourceId)
        log.tracef(SQL)
        chartId = system.db.runUpdateQuery(SQL, tx=txId, getKey=True)
        log.tracef("...inserted %s into SfcChart table and got id: %d", chartPath, chartId)

    except:
        errorTxt = catchError("%s.createChart()")
        log.errorf(errorTxt)



    



