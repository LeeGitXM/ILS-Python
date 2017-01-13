# This module provided methods used to write lab data to lab history for the diagnostic toolkit problems.

import system
# import system.date as time
from java.util import Calendar
from java.util import Date

log = system.util.getLogger("project.vistalon.tf")

def writeLabHistValues(common,db,labTagName,labTagVal,labTagTimeOffset):
    labReptTimeOffset = int(labTagTimeOffset) + 30
    log.info("In writeLabHistoryTestValues ...")
    log.info("... now writing lab history for %s " % (labTagName))
    
    sql = "select ValueId from LtValue where ValueName = '%s'" % (labTagName)
    rtn = system.db.runQuery(sql, db)
    if len(rtn) == 1:
        labId = rtn[0]
        log.info("... found %s for lab tag %s" % (str(labId["ValueId"]), labTagName))
        labValId = labId["ValueId"]
    else:
        log.info("    found too many results")

    nowDate = Date()
    cal = Calendar.getInstance()
    cal.setTime(nowDate)
    cal.add(Calendar.MINUTE, int(labTagTimeOffset))
    labTagTime = cal.getTime()
    cal = Calendar.getInstance()
    cal.setTime(labTagTime)
    cal.add(Calendar.MINUTE, int(labReptTimeOffset))
    labReptTime = cal.getTime()
    log.info("... storing data for sample time %s and report time %s" % (str(labTagTime), str(labReptTime)))

    sql = "insert into LtHistory (RawValue, SampleTime, ReportTime, ValueId)" \
          "values (?, ?, ?, ?)"
	
    log.info("... query to be used is %s" % (sql))
    rows =  system.db.runPrepUpdate(sql, [float(labTagVal), labTagTime, labReptTime, labValId], db)

    log.info("... ending")

