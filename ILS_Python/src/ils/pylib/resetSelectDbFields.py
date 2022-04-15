# This module provided methods used to place the diagnostic toolkit problems in a null state 
# ready for automated testing.

import system
from ils.log import getLogger
log = getLogger(__name__)

def resetActiveProblems(common,db):
    ''' Turn off competing votes for most important problm to be worked. '''
    log.info("In resetActiveProblems ...")
   
    sqlDE = "update DtDiagnosisEntry set Status = 'Inactive' where Status = 'Active'"
    sqlQU = "update DtQuantOutput set Active = 0 where Active = 1"
    sqlFD = "update DtFinalDiagnosis set Active = 0 where Active = 1"
    
    rowsDE = system.db.runUpdateQuery(sqlDE,db)
    rowsQU = system.db.runUpdateQuery(sqlQU,db)
    rowsFD = system.db.runUpdateQuery(sqlFD,db)

    log.info("...cleared %i diagnosis entries" % (rowsDE))
    log.info("...cleared %i quantoutput entries" % (rowsQU))
    log.info("...cleared %i final diagnosis" % (rowsFD))

def initializeQuantOutputs(common,db):
    ''' Set quant output fields to zero '''
    log.info("In intiializeQuantOutputs ...")

    sql = "update DtQuantOutput set FeedbackOutput = 0.0, FeedbackOutputConditioned = 0.0"
    rows = system.db.runUpdateQuery(sql,db)

    log.info("... cleared %i output values" % (rows))

def resetQuantOutputsForFD(common,db,appName,qoName):
    ''' Set selected quantoutput to zero ''' 

    log.info("In resetQuantOutputsForFD ...")

    sql = "update DtQuantOutput set FeedbackOutput = 0.0, FeedbackOutputConditioned = 0.0" \
          " from DtQuantOutput QO, DtApplication A" \
          " where QO.ApplicationId = A.ApplicationId" \
          " and A.ApplicationName = '%s' "\
          " and QO.QuantOutputName = '%s' " % (appName, qoName)
    log.info("... query to be used is %s" %(sql))
    rows = system.db.runUpdateQuery(sql,db)

    log.info("... cleared %i rows for app %s" % (rows,appName))


