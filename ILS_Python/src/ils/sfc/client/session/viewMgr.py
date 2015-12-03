'''
Created on Nov 25, 2015

@author: rforbes
'''
sessionNamesById = dict()
controlPanelViewsById = dict()

def getControlPanelView(cpid):
    return controlPanelViewsById[cpid]

def addControlPanelView(controlPanelView):
    controlPanelViewsById[controlPanelView.model.sessionId] = controlPanelView

def removeControlPanelView(cpid):
    controlPanelViewsById.remove(cpid)