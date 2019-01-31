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
    rootContainer.data = ds
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
    
    for row in range(ds.rowCount):
        print "Acking row ", row
        diagnosisEntryId = ds.getValueAt(row, "DiagnosisEntryId")
        applicationName = ds.getValueAt(row, "ApplicationName")
        acknowledgeTextRecommendationProcessing(post, applicationName, diagnosisEntryId, database, provider)
    
    system.nav.closeParentWindow(event)