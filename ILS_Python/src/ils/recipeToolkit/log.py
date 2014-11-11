'''
Created on Sep 10, 2014

@author: Pete
'''

import system, string

# I Need to pass the table because in a project with multiple consoles I have two diffferent download tables
def logMaster(unitId, grade, version):

    print "Logging"
    SQL = "insert into RtDownloadMaster (UnitId, Grade, Version, DownloadStartTime) " \
        " values (?, ?, ?, getdate())"
    print SQL
    logId = system.db.runPrepUpdate(SQL, args=[unitId, grade, version], getKey=True)
    return logId

def updateLogMaster(logId, status, totalDownloads, passedDownloads, failedDownloads):
    print "Updating the Master Log record"

    SQL = "update RtDownloadMaster set DownloadEndTime = getdate(), status = ?, TotalDownloads = ?, PassedDownloads = ?, FailedDownloads = ? " \
        " where Id = ?"

    print SQL
    system.db.runPrepUpdate(SQL, args=[status, totalDownloads, passedDownloads, failedDownloads, logId])

    
# Log the results of an individual write
def logDetail(downloadId, tag, outputVal, status, storeVal, compareVal, recommendVal, reason, errorMessage):
    
    #TODO need a NAN
    if outputVal == None:
        outputVal = -99
    if storeVal == None:
        storeVal = -99
    if compareVal== None:
        compareVal = -99
    if recommendVal== None:
        recommendVal = -99
        
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
