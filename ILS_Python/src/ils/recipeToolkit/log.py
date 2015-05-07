'''
Created on Sep 10, 2014

@author: Pete
'''

import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit.download")


def logMaster(familyId, grade, version, downloadType = "Manual", database = ""):
    log.trace("Inserting a DownloadMaster record for %s - %s - version %s" % (str(familyId), str(grade), str(version)))
    SQL = "insert into RtDownloadMaster (RecipeFamilyId, Grade, Version, Type, DownloadStartTime) " \
        " values (?, ?, ?, ?, getdate())"
    log.trace(SQL)
    logId = system.db.runPrepUpdate(SQL, args=[familyId, grade, version, downloadType], getKey=True, database=database)
    return logId


def updateLogMaster(masterId, status, totalDownloads, passedDownloads, failedDownloads, database = ""):
    log.trace("Updating the DownloadMaster record...")
    SQL = "update RtDownloadMaster set DownloadEndTime = getdate(), status = ?, TotalDownloads = ?, PassedDownloads = ?, FailedDownloads = ? " \
        " where MasterId = ?"
    log.trace(SQL)
    system.db.runPrepUpdate(SQL, args=[status, totalDownloads, passedDownloads, failedDownloads, masterId], database=database)


# Log the results of an individual write
def logDetail(masterId, tag, outputVal, status, storeVal, compareVal, recommendVal, reason, errorMessage, database=""):

    if string.upper(status) == 'SUCCESS':
        success = True
    else:
        success = False

    if errorMessage == "":
        errorMessage = None
   
    SQL = "insert into RtDownloadDetail (MasterId, Timestamp, Tag, OutputValue, Success, StoreValue, CompareValue, "\
        " RecommendedValue, Reason, Error) " \
        " values (?, getdate(), ?, ?, ?, ?, ?, ?, ?, ?)"
    
    log.trace(SQL)
    
    system.db.runPrepUpdate(SQL, [masterId, tag, outputVal, success, storeVal, compareVal, recommendVal, reason, errorMessage], database)
