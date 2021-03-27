# This module provided methods used to write lab data to lab history for the diagnostic toolkit problems.

import system
import system.ils.blt.diagram as blt
from java.util import Calendar
from java.util import Date

from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

def writeLabHistValues(common,db,labTagName,labTagVal,labTagTimeOffset):
    log.info("In writeLabHistoryTestValues ...")
    log.info("... now writing lab history for %s with value %s at offset %s" % (labTagName, str(labTagVal), str(labTagTimeOffset)))
    
    sql = "select ValueId from LtValue where ValueName = '%s'" % (labTagName)
    rtn = system.db.runQuery(sql, db)
    if len(rtn) == 1:
        labId = rtn[0]
        log.info("... found %s for lab tag %s" % (str(labId["ValueId"]), labTagName))
        labValId = labId["ValueId"]
    else:
        log.info("    found too many results")
#   calculate sample time from current time and labTagTimeOffset
    nowDate = Date()
    cal = Calendar.getInstance()
    cal.setTime(nowDate)
    cal.add(Calendar.MINUTE, int(labTagTimeOffset))
    labTagTime = cal.getTime()
#   calculate report time allowing 30 minutes of analysis time
    cal = Calendar.getInstance()
    cal.setTime(nowDate)
    cal.add(Calendar.MINUTE, int(labTagTimeOffset)+30)
    labReptTime = cal.getTime()

    log.info("... storing data for sample time %s and report time %s" % (str(labTagTime), str(labReptTime)))

    sql = "insert into LtHistory (RawValue, SampleTime, ReportTime, ValueId)" \
          "values (?, ?, ?, ?)"
	
    log.info("... query to be used is %s" % (sql))
    rows =  system.db.runPrepUpdate(sql, [float(labTagVal), labTagTime, labReptTime, labValId], db)

    log.info("... ending")

def clearHistValues(common,labTagName):

    log.info("In clearHistValues to delete test lab values...")
    sql = "select ValueId from LtValue where ValueName = '%s'" % (labTagName)
    database = blt.getToolkitProperty("SecondaryDatabase")
    labId = system.db.runScalarQuery(sql, str(database))
    log.info("...%s query with database %s returned %s" % (str(sql),str(database),str(labId)))
    sql = "delete from LtHistory where ValueId = '%s'" % (str(labId))
    rows = system.db.runUpdateQuery(sql,database)
    log.info("...%s rows deleted from history for %s" % (str(rows),labTagName))

