'''
Created on Sep 10, 2014

@author: Pete
'''

import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit.download")


def logMaster(unitId, grade, version, type = "Manual", database = ""):
    log.trace("Inserting a DownloadMaster record for %s - %s - version %s" % (str(unitId), str(grade), str(version)))
    SQL = "insert into RtDownloadMaster (UnitId, Grade, Version, Type, DownloadStartTime) " \
        " values (?, ?, ?, ?, getdate())"
    log.trace(SQL)
    logId = system.db.runPrepUpdate(SQL, args=[unitId, grade, version, type], getKey=True, database=database)
    return logId


def updateLogMaster(logId, status, totalDownloads, passedDownloads, failedDownloads, database = ""):
    log.trace("Updating the DownloadMaster record...")
    SQL = "update RtDownloadMaster set DownloadEndTime = getdate(), status = ?, TotalDownloads = ?, PassedDownloads = ?, FailedDownloads = ? " \
        " where Id = ?"
    log.trace(SQL)
    system.db.runPrepUpdate(SQL, args=[status, totalDownloads, passedDownloads, failedDownloads, logId], database=database)


# Log the results of an individual write
def logDetail(downloadId, tag, outputVal, status, storeVal, compareVal, recommendVal, reason, errorMessage, database=""):

    if string.upper(status) == 'SUCCESS':
        success = True
    else:
        success = False

    if errorMessage == "":
        errorMessage = None
   
    SQL = "insert into RtDownloadDetail (DownloadId, Timestamp, Tag, OutputValue, Success, StoreValue, CompareValue, "\
        " RecommendedValue, Reason, Error) " \
        " values (?, getdate(), ?, ?, ?, ?, ?, ?, ?, ?)"
    
    log.trace(SQL)
    
    system.db.runPrepUpdate(SQL, [downloadId, tag, outputVal, success, storeVal, compareVal, recommendVal, reason, errorMessage], database)
