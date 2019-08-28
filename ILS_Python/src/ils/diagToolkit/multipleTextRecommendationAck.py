'''
Created on Nov 19, 2018

@author: phass
'''
import system
from ils.common.config import getDatabaseClient
from ils.common.util import stripHTML
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
    ds = system.dataset.addColumn(ds,ackVals, "SpecialActions", bool)
    ds = system.dataset.addColumn(ds,ackVals, "Ackd", bool)
    
    
    for row in range(ds.getRowCount()):
        textRec = stripHTML(ds.getValueAt(row, "TextRecommendation"))
        ds = system.dataset.setValue(ds, row, "TextRecommendation", textRec)
        postProcessingCallback = ds.getValueAt(row, "postProcessingCallback")
        if postProcessingCallback not in [None, ""]:
            ds = system.dataset.setValue(ds, row, "SpecialActions", True)
    
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
        if ans:
            system.nav.closeParentWindow(event)
            return

    ackCnt = 0
    skipCnt = 0
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
        else:
            skipCnt = skipCnt + 1
    
    if skipCnt == 0:
        system.nav.closeParentWindow(event)


def selectAll(event):
    print "In %s.selectAll()" % (__name__)
    rootContainer = event.source.parent

    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    for row in range(ds.rowCount):
        ds = system.dataset.setValue(ds, row, "Ackd", True)

    table.data = ds


def unselectAll(event):
    print "In %s.unselectAll()" % (__name__)
    rootContainer = event.source.parent

    table = rootContainer.getComponent("Power Table")
    ds = table.data
    
    for row in range(ds.rowCount):
        ds = system.dataset.setValue(ds, row, "Ackd", False)

    table.data = ds