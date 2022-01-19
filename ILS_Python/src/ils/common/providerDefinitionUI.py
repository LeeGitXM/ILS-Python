'''
Created on Dec 21, 2021

@author: ils
'''

import system, string
from ils.common.config import getIsolationModeClient
log = system.util.getLogger(__name__)

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()...", __name__)
    refresh(rootContainer)
    

def refresh(rootContainer):
    log.infof("In %s.refresh()...", __name__)
    thisProject = system.project.getProjectName()
    projects = system.project.getProjectNames()
    log.tracef("The projects in this gateway are: %s", str(projects))
    rows = []
    for projectName in projects:
        log.tracef("Project: %s", projectName)
        isolationMode = False
        payload = {"project": projectName, "isolationMode": isolationMode}
        
        productionTagProvider = system.util.sendRequest(thisProject, "getTagProvider", payload)
        productionDatabase = system.util.sendRequest(thisProject, "getDatabase", payload)
        productionTimeFactor = system.util.sendRequest(thisProject, "getTimeFactor", payload)
        
        isolationMode = True
        payload = {"project": projectName, "isolationMode": isolationMode}
        
        isolationTagProvider = system.util.sendRequest(thisProject, "getTagProvider", payload)
        isolationDatabase = system.util.sendRequest(thisProject, "getDatabase", payload)
        isolationTimeFactor = system.util.sendRequest(thisProject, "getTimeFactor", payload)
        
        rows.append([projectName, productionDatabase, productionTagProvider, productionTimeFactor, 
                     isolationDatabase, isolationTagProvider, isolationTimeFactor])

    ds = system.dataset.toDataSet(["Project", "Production Database", "Production Tag Provider", "Production Time Factor", 
                                   "Isolation Database", "Isolation Tag Provider", "Isolation Time Factor"], rows)
    ds = system.dataset.sort(ds, "Project")
    table = rootContainer.getComponent("Power Table")
    table.data = ds

def cellEdited(table, rowIndex, colIndex, colName, oldValue, newValue):
    log.infof("Cell (%d, %d) edited..", rowIndex, colIndex)
    if oldValue == newValue:
        print "Nothing changed..."
        return
    
    thisProject = system.project.getProjectName()
    projectName = table.data.getValueAt(rowIndex, "Project")

    if colName == "Production Database":
        status = system.util.sendRequest(thisProject, "setDatabase", {"project": projectName, "isolationMode": False, "val": newValue})
    elif colName == "Production Tag Provider":
        status = system.util.sendRequest(thisProject, "setTagProvider", {"project": projectName, "isolationMode": False, "val": newValue})
    elif colName == "Production Time Factor":
        status = system.util.sendRequest(thisProject, "setTimeFactor", {"project": projectName, "isolationMode": False, "val": newValue})
    elif colName == "Isolation Database":
        status = system.util.sendRequest(thisProject, "setDatabase", {"project": projectName, "isolationMode": True, "val": newValue})
    elif colName == "Isolation Tag Provider":
        status = system.util.sendRequest(thisProject, "setTagProvider", {"project": projectName, "isolationMode": True, "val": newValue})
    elif colName == "Isolation Time Factor":
        status = system.util.sendRequest(thisProject, "setTimeFactor", {"project": projectName, "isolationMode": True, "val": newValue})
    else:
        status = "Unknown column: %s" % (colName)

    if string.lower(status) == "success":
        table.data = system.dataset.setValue(table.data, rowIndex, colIndex, newValue)
    else:
        log.errorf("Unable to update the internal database")
        system.gui.errorBox("Unable to update the internal database")