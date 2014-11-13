'''
Created on Sep 10, 2014

@author: Pete
'''

import system, string
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit.download")

# I Need to pass the table because in a project with multiple consoles I have two diffferent download tables
def logMaster(unitId, grade, version):
    log.trace("Inserting a DownloadMaster record for %s - %s - version %" % (str(unitId), str(grade), str(version)))
    SQL = "insert into RtDownloadMaster (UnitId, Grade, Version, DownloadStartTime) " \
        " values (?, ?, ?, getdate())"
    logId = system.db.runPrepUpdate(SQL, args=[unitId, grade, version], getKey=True)
    return logId

def updateLogMaster(logId, status, totalDownloads, passedDownloads, failedDownloads):
    log.trace("Updating the DownloadMaster record...")
    SQL = "update RtDownloadMaster set DownloadEndTime = getdate(), status = ?, TotalDownloads = ?, PassedDownloads = ?, FailedDownloads = ? " \
        " where Id = ?"
    system.db.runPrepUpdate(SQL, args=[status, totalDownloads, passedDownloads, failedDownloads, logId])

    
# Log the results of an individual write
def logDetail(downloadId, tag, outputVal, status, storeVal, compareVal, recommendVal, reason, errorMessage):
       
    if string.upper(status) == 'SUCCESS':
        success = True
    else:
        success = False

    if errorMessage == "":
        errorMessage = None
        
    print "Logging"
    
    SQL = "insert into RtDownloadDetail (DownloadId, Timestamp, Tag, OutputValue, Success, StoreValue, CompareValue, "\
        " RecommendedValue, Reason, Error) " \
        " values (?, getdate(), ?, ?, ?, ?, ?, ?, ?, ?)"
    
    print SQL
    
    system.db.runPrepUpdate(SQL, [downloadId, tag, outputVal, success, storeVal, compareVal, recommendVal, reason, errorMessage])
