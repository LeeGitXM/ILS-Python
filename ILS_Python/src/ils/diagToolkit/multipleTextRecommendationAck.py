'''
Created on Nov 19, 2018

@author: phass
'''
import system
from ils.common.config import getDatabaseClient
from ils.diagToolkit.common import fetchActiveTextRecommendationsForPost
from ils.diagToolkit.setpointSpreadsheet import acknowledgeTextRecommendationProcessing

def internalFrameOpened(rootContainer):
    print "In %s.internalFrameOpened()" % (__name__)
    refresh(rootContainer)
    
def refresh(rootContainer):
    print "In %s.refresh()" % (__name__)
    database = getDatabaseClient()
    post = rootContainer.post
    pds = fetchActiveTextRecommendationsForPost(post, database)
    ackVals = [False] * len(pds)
    ds = system.dataset.toDataSet(pds)
    ds = system.dataset.addColumn(ds,ackVals, "Ackd", bool)
    table = rootContainer.getComponent("Power Table")
    table.data = ds
    
def ack(event):
    print "In %s.ack()" % (__name__)
    rootContainer = event.source.parent
    database = getDatabaseClient()
    post = rootContainer.post
    provider = rootContainer.provider

    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    ''' Count how many rows are marked for Ack '''
    rowsToAck = 0
    for row in range(ds.rowCount):
        if ds.getValueAt(row, "Ackd"):
            rowsToAck = rowsToAck + 1
            
    if ds.rowCount > 0 and rowsToAck == 0:
        ans = system.gui.confirm("You have not selected any recommendations to acknowledge, are you sure you want to exit?")
        if not(ans):
            return

    ackCnt = 0
    for row in range(ds.rowCount):
        if ds.getValueAt(row, "Ackd"):
            ackCnt = ackCnt + 1
            diagnosisEntryId = ds.getValueAt(row, "DiagnosisEntryId")
            applicationName = ds.getValueAt(row, "ApplicationName")
            if ackCnt == rowsToAck:
                recalc = True
            else:
                recalc = False
            acknowledgeTextRecommendationProcessing(post, applicationName, diagnosisEntryId, database, provider, recalc)
    
    system.nav.closeParentWindow(event)