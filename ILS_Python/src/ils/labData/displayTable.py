'''
Created on Jun 10, 2019

@author: phass
'''

import system
from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def updateLabDataVisibility(displayTableTitle, visible, db):
    SQL = "update LtDisplayTable set DisplayFlag = %d where DisplayTableTitle = '%s' " % (visible, displayTableTitle)
    rows = system.db.runUpdateQuery(SQL, db)
    if rows <> 1:
        log.errorf("Error in %s.updateLabDataVisibility() updating LtDisplayTable - %d rows were updated, exactly one was expected (%s)", __name__, rows, SQL)