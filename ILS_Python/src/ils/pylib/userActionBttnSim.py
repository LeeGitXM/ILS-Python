# This module provided methods used to simulate parts of a No Douwnload action by the console operator.

import system

from ils.diagToolkit.setpointSpreadsheet import resetOutputs
from ils.diagToolkit.setpointSpreadsheet import resetRecommendations
from ils.diagToolkit.setpointSpreadsheet import resetFinalDiagnosis
from ils.diagToolkit.setpointSpreadsheet import resetDiagnosisEntry
from ils.diagToolkit.setpointSpreadsheet import resetDiagram
from ils.diagToolkit.setpointSpreadsheet import partialResetDiagram

from ils.log import getLogger
log = getLogger(__name__)

#### need to add call to def partialResetDiagram(finalDiagnosisIds, database): to perform a Wait for More Data action

def getQoIdVal(common, db, lst, qoName, init=""):
    log.info("In %s.getQoIdVal..." % (__name__))
    sql = "select QuantOutputId from DtQuantOutput where QuantOutputName = '%s'" % (qoName)
    qoId = system.db.runScalarQuery(sql, db)
    if init:
        lst = str(qoId)
    else:
        lst = lst + ", " + str(qoId)
    common['result'] = lst
    log.info("...quant output ids found and returned to testframework as %s" % (lst))

def getFdIdVal(common, db, lst, fdName, init=""):
    log.info("In %s.getFdIdVal..." % (__name__))
    sql = "select FinalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName = '%s'" % (fdName)
    fdId = system.db.runScalarQuery(sql, db)
    if init:
        lst = str(fdId)
    else:
        lst = lst + ", " + str(fdId)
    common['result'] = lst
    log.info("...final diagnosis ids found and returned to testframework as %s" % (lst))
	
def noDownAct(common, appName, fdIds, qoIds, provider, database):
    import string
    log.info("In %s.noDownAct" % (__name__))
# convert string returned by 'result' in the testframework to a list
    fdIds = fdIds.split(",")
    qoIds = qoIds.split(",")
# convert string values to integer
    fdIdsInt = []
    for fdId in fdIds:
        fdIdInt = int(fdId)
        fdIdsInt.append(fdIdInt)
    qoIdsInt = []
    for qoId in qoIds:
        qoIdInt = int(qoId)
        qoIdsInt.append(qoIdInt)
# perform no download actions
    resetOutputs(qoIdsInt, "No Download", log, database)
    resetRecommendations(qoIdsInt, "No Download", log, database)
    resetFinalDiagnosis(appName, "No Download", fdIdsInt, log, database, provider)
    resetDiagnosisEntry(appName, "No Download", fdIdsInt, "No Download by TF", log, database)
    resetDiagram(fdIdsInt, database)
    log.info("...no download actions completed")

def moreDataWaitAct (common, appName, fdIds, qoIds, provider, database):
    import string
    log.info("In %s.moreDataWaitAct" % (__name__))
# convert string returned by 'result' in the testframework to a list
    fdIds = fdIds.split(",")
    qoIds = qoIds.split(",")
# convert string values to integer
    fdIdsInt = []
    for fdId in fdIds:
        fdIdInt = int(fdId)
        fdIdsInt.append(fdIdInt)
    qoIdsInt = []
    for qoId in qoIds:
        qoIdInt = int(qoId)
        qoIdsInt.append(qoIdInt)
# perform wait actions
    resetOutputs(qoIdsInt, "WAIT_FOR_MORE_DATA", log, database)
    resetRecommendations(qoIdsInt, "WAIT_FOR_MORE_DATA", log, database)
    resetFinalDiagnosis(appName, "WAIT_FOR_MORE_DATA", fdIdsInt, log, database, provider)
    resetDiagnosisEntry(appName, "WAIT_FOR_MORE_DATA", fdIdsInt, "Wait for More Data by TF", log, database)
    partialResetDiagram(fdIdsInt, database)
    log.info("...wait actions completed")
      
def writeDownloadImpTime(common,fdName,database):

    log.info("In %s.writeDownloadImpTime" % (__name__))
    log.info ("...database is %s for final diagnosis %s" % (database,fdName))
	
    sql = "update DtFinalDiagnosis Set TimeOfMostRecentRecommendationImplementation = getDate() where FinalDiagnosisName = '%s'" % (fdName)
    log.info("...sql statement is %s" % (sql))
	
    system.db.runUpdateQuery(sql,database)

    log.info("...ended noDownlaodImpTime")

### the following methods are not currently in use
    
def makeInt(txt, char=","):
    import string
    log.info("In %s.makeInt...." % (__name__))
# convert input string to integer for use with the 'result' returned by the testframework
# initialize variables
    indx0 = 0
    indx1 = 0
    size = len(txt)
    val = []
# parse the inut txt using separator char
    while indx1 != -1:
        indx1 = string.find(txt, char, indx0, size)
        val.append(int(txt[indx0+1:indx1]))
        indx0 = indx1
    log.info("...received %s and returned %s" % (txt,str(val)))
    return val

def buildFdWorklist(common, db, *args):
    log.info("In %s.buildFdWorklist..." % (__name__))
    fdIds = []
    for arg in args:
        sql = "select FinalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName = '%s'" % (arg)
        fdId = system.db.runScalarQuery(sql, db)
        fdIds.append(fdId)
        log.info("...sql statement %s returned Id %s for %s" % (sql, str(fdId), arg))
    common['result'] = fdIds
    log.info("...final diagnosis ids found and returned to testframework")

def buildQoWorklist(common, db, *args):
    log.info("In %s.buildQoWorklist..." % (__name__))
    qoIds = []
    for arg in args:
        sql = "select QuantOutputId from DtQuantOutput where QuantOutputName = '%s'" % (arg)
        qoId = system.db.runScalarQuery(sql, db)
        qoIds.append(qoId)
        log.info("...sql statement %s returned Id %s for %s" % (sql, str(qoId), arg))
    common['result'] = qoIds
    log.info("...quant output ids found and returned to testframework")

